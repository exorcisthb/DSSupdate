"""
Data processor for ingesting data into database.
Handles Tiki, Lazada, and Shopee data processing.
"""

import pandas as pd
from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import OperationalError
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _db_retry(fn, max_attempts=5, base_delay=1):
    """Retry DB operation on OperationalError (locked) with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except OperationalError as e:
            if 'locked' in str(e) and attempt < max_attempts - 1:
                delay = base_delay * (2 ** attempt)
                print(f"  ⏳ DB locked, retrying in {delay}s (attempt {attempt+1}/{max_attempts})...")
                time.sleep(delay)
                continue
            raise

from database.schema import (
    ProductTiki, ProductTikiHistory, ProductChange, 
    ProductExternal, IngestLog, get_db
)


class DataProcessor:
    """Process and ingest data into database."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def check_already_ingested(self, source: str, identifier: str) -> bool:
        """Check if data has already been ingested."""
        existing = self.db.query(IngestLog).filter(
            and_(
                IngestLog.source == source,
                IngestLog.source_identifier == identifier
            )
        ).first()
        return existing is not None

    def delete_ingest_log(self, source: str, identifier: str):
        """Delete ingest log entry (used for force re-ingest)."""
        existing = self.db.query(IngestLog).filter(
            and_(
                IngestLog.source == source,
                IngestLog.source_identifier == identifier
            )
        ).first()
        if existing:
            self.db.delete(existing)
            _db_retry(lambda: self.db.commit())
    
    def log_ingest(self, source: str, identifier: str, platform: str,
                   records_count: int, status: str = "success", 
                   error_msg: Optional[str] = None):
        """Log data ingestion."""
        log_entry = IngestLog(
            source=source,
            source_identifier=identifier,
            platform=platform,
            records_processed=records_count,
            status=status,
            error_message=error_msg,
            ingested_at=datetime.now(timezone.utc)
        )
        self.db.add(log_entry)
        _db_retry(lambda: self.db.commit())
    
    @staticmethod
    def _fetch_tiki_thumbnails(product_ids, max_workers=10):
        """Fetch thumbnails from Tiki API in parallel."""
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        thumb_map = {}
        def fetch(pid):
            try:
                r = session.get(f'https://tiki.vn/api/v2/products/{pid}', timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    thumb = data.get('thumbnail_url', '')
                    return pid, thumb if thumb else None
            except:
                pass
            return pid, None
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            fut = {pool.submit(fetch, pid): pid for pid in product_ids}
            for f in as_completed(fut):
                pid, thumb = f.result()
                if thumb:
                    thumb_map[pid] = thumb
        print(f"  ✅ Fetched {len(thumb_map)}/{len(product_ids)} thumbnails from Tiki API")
        return thumb_map

    def ingest_tiki_clean(self, df: pd.DataFrame, source_identifier: str) -> int:
        """Ingest Tiki clean data (current snapshot)."""
        print(f"📊 Processing {len(df)} Tiki products...")

        # Preserve existing thumbnails before clearing
        existing_thumbs = _db_retry(
            lambda: {
                p[0]: p[1] for p in self.db.query(ProductTiki.product_id, ProductTiki.thumbnail).all()
                if p[1] and not p[1].startswith('https://salt.tikicdn.com/ts/product/')
            }
        )

        # Clear existing data
        _db_retry(lambda: self.db.query(ProductTiki).delete())

        # Parse date_collected from file (clean data has this column)
        file_date = None
        if 'date_collected' in df.columns:
            try:
                sample = df['date_collected'].dropna().iloc[0]
                file_date = pd.to_datetime(sample) if isinstance(sample, str) else sample
            except:
                pass
        if file_date is None:
            file_date = datetime.now(timezone.utc)

        # Check if df has real thumbnail data; if not, fetch from Tiki API
        has_thumb_col = 'thumbnail' in df.columns
        if has_thumb_col:
            sample_thumb = df['thumbnail'].dropna().apply(str).str.strip()
            sample_thumb = sample_thumb[~sample_thumb.str.lower().isin(['nan', '', 'none'])]
            has_thumb_col = len(sample_thumb) > 0
        thumb_map = {}
        if has_thumb_col:
            for _, row in df.iterrows():
                pid = str(row.get('product_id', '')).strip()
                if pid and pid not in ('', 'nan'):
                    t = str(row.get('thumbnail', ''))
                    if t and t.lower() not in ('nan', '', 'none'):
                        thumb_map[pid] = t
        else:
            all_pids = [str(row.get('product_id', '')).strip()
                        for _, row in df.iterrows()
                        if str(row.get('product_id', '')).strip() not in ('', 'nan')]
            # Use existing thumbnails from DB as cache (skip API for known products)
            need_fetch = [pid for pid in all_pids if pid not in existing_thumbs]
            thumb_map = {pid: existing_thumbs[pid] for pid in all_pids if pid in existing_thumbs}
            if need_fetch:
                print(f"  ⚠️  No thumbnail column — fetching {len(need_fetch)}/{len(all_pids)} from Tiki API...")
                fetched = self._fetch_tiki_thumbnails(need_fetch)
                thumb_map.update(fetched)
            else:
                print(f"  ✅ Using {len(thumb_map)} cached thumbnails from previous run")

        records_added = 0
        for _, row in df.iterrows():
            try:
                pid = str(row.get('product_id', '')).strip()
                if not pid or pid == 'nan':
                    continue

                # Support both old and new column names from the scraper
                url = str(row.get('url') or row.get('product_link') or '')
                thumbnail = thumb_map.get(pid, '')

                # Support both discount_rate and discount_percent column names
                discount = row.get('discount_rate') or row.get('discount_percent') or 0
                try:
                    discount_val = float(discount) if not pd.isna(discount) else 0.0
                except:
                    discount_val = 0.0

                # Support both is_authentic and is_official_store
                is_auth = row.get('is_authentic') or row.get('is_official_store') or False
                try:
                    is_auth_val = bool(is_auth) if not pd.isna(is_auth) else False
                except:
                    is_auth_val = False

                # delivery_estimate_days may not be in new data — default 3.0
                del_days = row.get('delivery_estimate_days')
                try:
                    del_days_val = float(del_days) if del_days is not None and not pd.isna(del_days) else 3.0
                except:
                    del_days_val = 3.0

                def safe_float(v, default=0.0):
                    try: return float(v) if v is not None and not pd.isna(v) else default
                    except: return default

                def safe_int(v, default=0):
                    try: return int(float(v)) if v is not None and not pd.isna(v) else default
                    except: return default

                product = ProductTiki(
                    product_id=pid,
                    product_name=str(row.get('product_name', '')),
                    category_l1=str(row.get('category_l1', '')),
                    category_l2=str(row.get('category_l2', '')),
                    price=safe_float(row.get('price')),
                    sold_count=safe_int(row.get('sold_count')),
                    estimated_revenue=safe_float(row.get('estimated_revenue')),
                    rating=safe_float(row.get('rating')),
                    review_count=safe_int(row.get('review_count')),
                    discount_rate=discount_val,
                    url=url,
                    thumbnail=thumbnail,
                    is_authentic=is_auth_val,
                    delivery_estimate_days=del_days_val
                )
                self.db.add(product)

                # Also write to ProductTikiHistory with today's date so dashboard shows latest day
                existing = self.db.query(ProductTikiHistory).filter(
                    and_(
                        ProductTikiHistory.product_id == pid,
                        ProductTikiHistory.date_collected == file_date
                    )
                ).first()
                if not existing:
                    history = ProductTikiHistory(
                        product_id=pid,
                        product_name=str(row.get('product_name', '')),
                        category_l1=str(row.get('category_l1', '')),
                        category_l2=str(row.get('category_l2', '')),
                        price=safe_float(row.get('price')),
                        sold_count=safe_int(row.get('sold_count')),
                        estimated_revenue=safe_float(row.get('estimated_revenue')),
                        rating=safe_float(row.get('rating')),
                        review_count=safe_int(row.get('review_count')),
                        discount_rate=discount_val,
                        url=url,
                        thumbnail=thumbnail,
                        is_authentic=is_auth_val,
                        delivery_estimate_days=del_days_val,
                        date_collected=file_date
                    )
                    self.db.add(history)

                records_added += 1
            except Exception as e:
                print(f"⚠️  Error processing product {row.get('product_id')}: {e}")
                continue

        _db_retry(lambda: self.db.commit())
        print(f"✅ Ingested {records_added} Tiki products")
        return records_added
    
    def ingest_tiki_historical(self, df: pd.DataFrame, source_identifier: str) -> int:
        """Ingest Tiki historical data."""
        print(f"📊 Processing {len(df)} Tiki historical records...")

        # Pre-cache existing ProductTiki IDs
        existing_tiki_ids = set(
            p[0] for p in self.db.query(ProductTiki.product_id).all()
        )

        records_added = 0
        for _, row in df.iterrows():
            try:
                # Parse date
                date_collected = row.get('date_collected')
                if pd.isna(date_collected):
                    continue

                if isinstance(date_collected, str):
                    date_collected = pd.to_datetime(date_collected)

                pid = str(row.get('product_id', '')).strip()
                if not pid or pid == 'nan':
                    continue

                # Ensure parent ProductTiki exists to satisfy Foreign Key constraint
                if pid not in existing_tiki_ids:
                    del_days = row.get('delivery_estimate_days')
                    del_days_val = 3.0 if pd.isna(del_days) else float(del_days)
                    stub_product = ProductTiki(
                        product_id=pid,
                        product_name=str(row.get('product_name', 'Sản phẩm Tiki')),
                        category_l1=str(row.get('category_l1', 'Thời trang nam')),
                        category_l2=str(row.get('category_l2', 'Khác')),
                        price=float(row.get('price', 0) if not pd.isna(row.get('price')) else 0),
                        sold_count=int(row.get('sold_count', 0) if not pd.isna(row.get('sold_count')) else 0),
                        estimated_revenue=float(row.get('estimated_revenue', 0) if not pd.isna(row.get('estimated_revenue')) else 0),
                        rating=float(row.get('rating', 0) if not pd.isna(row.get('rating')) else 0),
                        review_count=int(row.get('review_count', 0) if not pd.isna(row.get('review_count')) else 0),
                        discount_rate=float(row.get('discount_rate', 0) if not pd.isna(row.get('discount_rate')) else 0),
                        url=str(row.get('url', '')),
                        thumbnail=str(row.get('thumbnail', '')),
                        is_authentic=bool(row.get('is_authentic', False)),
                        delivery_estimate_days=del_days_val
                    )
                    self.db.add(stub_product)
                    self.db.flush()
                    existing_tiki_ids.add(pid)

                # Check if record already exists
                existing = self.db.query(ProductTikiHistory).filter(
                    and_(
                        ProductTikiHistory.product_id == pid,
                        ProductTikiHistory.date_collected == date_collected
                    )
                ).first()

                if existing:
                    continue

                del_days = row.get('delivery_estimate_days')
                del_days_val = 3.0 if pd.isna(del_days) else float(del_days)

                history = ProductTikiHistory(
                    product_id=pid,
                    product_name=str(row.get('product_name', '')),
                    category_l1=str(row.get('category_l1', '')),
                    category_l2=str(row.get('category_l2', '')),
                    price=float(row.get('price', 0) if not pd.isna(row.get('price')) else 0),
                    sold_count=int(row.get('sold_count', 0) if not pd.isna(row.get('sold_count')) else 0),
                    estimated_revenue=float(row.get('estimated_revenue', 0) if not pd.isna(row.get('estimated_revenue')) else 0),
                    rating=float(row.get('rating', 0) if not pd.isna(row.get('rating')) else 0),
                    review_count=int(row.get('review_count', 0) if not pd.isna(row.get('review_count')) else 0),
                    discount_rate=float(row.get('discount_rate', 0) if not pd.isna(row.get('discount_rate')) else 0),
                    url=str(row.get('url', '')),
                    thumbnail=str(row.get('thumbnail', '')),
                    is_authentic=bool(row.get('is_authentic', False)),
                    delivery_estimate_days=del_days_val,
                    date_collected=date_collected
                )
                self.db.add(history)
                records_added += 1
            except Exception as e:
                print(f"⚠️ Error processing historical record: {e}")
                continue

        _db_retry(lambda: self.db.commit())
        print(f"✅ Ingested {records_added} historical records")
        return records_added
    
    def ingest_tiki_changes(self, df: pd.DataFrame, source_identifier: str) -> int:
        """Ingest Tiki product changes."""
        print(f"📊 Processing {len(df)} product changes...")
        
        # Clear old changes (keep only recent ones)
        self.db.query(ProductChange).delete()
        
        records_added = 0
        for _, row in df.iterrows():
            try:
                change = ProductChange(
                    product_id=str(row.get('product_id', '')),
                    product_name=str(row.get('product_name', '')),
                    category=str(row.get('category', '')),
                    status=str(row.get('status', '')),
                    old_sold=int(row.get('old_sold', 0)),
                    new_sold=int(row.get('new_sold', 0)),
                    sold_increase=int(row.get('sold_increase', 0)),
                    sold_increase_pct=float(row.get('sold_increase_pct', 0)),
                    old_price=float(row.get('old_price', 0)),
                    new_price=float(row.get('new_price', 0)),
                    price_change=float(row.get('price_change', 0)),
                    price_change_pct=float(row.get('price_change_pct', 0)),
                    url=str(row.get('url', '')),
                    thumbnail=str(row.get('thumbnail', ''))
                )
                self.db.add(change)
                records_added += 1
            except Exception as e:
                print(f"⚠️  Error processing change record: {e}")
                continue
        
        _db_retry(lambda: self.db.commit())
        print(f"✅ Ingested {records_added} change records")
        return records_added
    
    def ingest_external_products(self, df: pd.DataFrame, platform: str, 
                                 source_identifier: str) -> int:
        """Ingest external platform products (Lazada, Shopee)."""
        print(f"📊 Processing {len(df)} {platform} products...")
        
        # Clear old data for this platform
        self.db.query(ProductExternal).filter(
            ProductExternal.platform == platform
        ).delete()
        
        records_added = 0
        date_collected = datetime.now(timezone.utc)
        
        for _, row in df.iterrows():
            try:
                # Getters with fallbacks
                ext_id = str(row.get('external_id') or row.get('ID') or row.get('id') or '')
                prod_name = str(row.get('product_name') or row.get('Tên sản phẩm') or row.get('title') or '')
                cat_l1 = str(row.get('category_l1', ''))
                cat_l2 = str(row.get('category_l2', ''))
                price = float(row.get('price') or row.get('Giá (VND)') or row.get('final_price') or 0.0)
                sold_count = int(row.get('sold_count') or row.get('Số lượng đã bán') or row.get('sold') or 0)
                rating = float(row.get('rating') or row.get('Điểm đánh giá') or 0.0)
                reviews = int(row.get('review_count') or row.get('Tổng lượt đánh giá') or row.get('reviews') or 0)
                discount = float(row.get('discount_rate') or row.get('Phần trăm giảm') or 0.0)
                origin = str(row.get('origin') or row.get('Xuất xứ') or '')
                url = str(row.get('url') or row.get('Link') or '')
                thumbnail = str(row.get('thumbnail') or row.get('Thumbnail') or row.get('image_url') or '')
                
                is_auth = bool(row.get('is_authentic', False)) or any(kw in prod_name.lower() for kw in ['chính hãng', 'official', 'mall'])
                del_days = float(row.get('delivery_estimate_days') or (2.2 if is_auth else 3.5))

                if platform in ["Lazada", "Shopee"]:
                    product = ProductExternal(
                        platform=platform,
                        external_id=ext_id,
                        product_name=prod_name,
                        category_l1=cat_l1,
                        category_l2=cat_l2,
                        price=price,
                        sold_count=sold_count,
                        rating=rating,
                        review_count=reviews,
                        discount_rate=discount,
                        origin=origin,
                        url=url,
                        thumbnail=thumbnail,
                        is_authentic=is_auth,
                        delivery_estimate_days=del_days,
                        date_collected=date_collected
                    )
                else:
                    continue
                
                self.db.add(product)
                records_added += 1
            except Exception as e:
                print(f"⚠️  Error processing {platform} product: {e}")
                continue
        
        self.db.commit()
        print(f"✅ Ingested {records_added} {platform} products")
        return records_added
