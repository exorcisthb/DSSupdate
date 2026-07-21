"""
Data processor for ingesting data into database.
Handles Tiki, Lazada, and Shopee data processing.
"""

import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            ingested_at=datetime.utcnow()
        )
        self.db.add(log_entry)
        self.db.commit()
    
    def ingest_tiki_clean(self, df: pd.DataFrame, source_identifier: str) -> int:
        """Ingest Tiki clean data (current snapshot)."""
        print(f"📊 Processing {len(df)} Tiki products...")
        
        # Clear existing data
        self.db.query(ProductTiki).delete()
        
        records_added = 0
        for _, row in df.iterrows():
            try:
                product = ProductTiki(
                    product_id=str(row.get('product_id', '')),
                    product_name=str(row.get('product_name', '')),
                    category_l1=str(row.get('category_l1', '')),
                    category_l2=str(row.get('category_l2', '')),
                    price=float(row.get('price', 0)),
                    sold_count=int(row.get('sold_count', 0)),
                    estimated_revenue=float(row.get('estimated_revenue', 0)),
                    rating=float(row.get('rating', 0)),
                    review_count=int(row.get('review_count', 0)),
                    discount_rate=float(row.get('discount_rate', 0)),
                    url=str(row.get('url', '')),
                    thumbnail=str(row.get('thumbnail', '')),
                    is_authentic=bool(row.get('is_authentic', False)),
                    delivery_estimate_days=float(row.get('delivery_estimate_days', 3.0))
                )
                self.db.add(product)
                records_added += 1
            except Exception as e:
                print(f"⚠️  Error processing product {row.get('product_id')}: {e}")
                continue
        
        self.db.commit()
        print(f"✅ Ingested {records_added} Tiki products")
        return records_added
    
    def ingest_tiki_historical(self, df: pd.DataFrame, source_identifier: str) -> int:
        """Ingest Tiki historical data."""
        print(f"📊 Processing {len(df)} Tiki historical records...")
        
        records_added = 0
        for _, row in df.iterrows():
            try:
                # Parse date
                date_collected = row.get('date_collected')
                if pd.isna(date_collected):
                    continue
                
                if isinstance(date_collected, str):
                    date_collected = pd.to_datetime(date_collected)
                
                # Check if record already exists
                existing = self.db.query(ProductTikiHistory).filter(
                    and_(
                        ProductTikiHistory.product_id == str(row.get('product_id', '')),
                        ProductTikiHistory.date_collected == date_collected
                    )
                ).first()
                
                if existing:
                    continue
                
                history = ProductTikiHistory(
                    product_id=str(row.get('product_id', '')),
                    product_name=str(row.get('product_name', '')),
                    category_l1=str(row.get('category_l1', '')),
                    category_l2=str(row.get('category_l2', '')),
                    price=float(row.get('price', 0)),
                    sold_count=int(row.get('sold_count', 0)),
                    estimated_revenue=float(row.get('estimated_revenue', 0)),
                    rating=float(row.get('rating', 0)),
                    review_count=int(row.get('review_count', 0)),
                    discount_rate=float(row.get('discount_rate', 0)),
                    url=str(row.get('url', '')),
                    thumbnail=str(row.get('thumbnail', '')),
                    is_authentic=bool(row.get('is_authentic', False)),
                    delivery_estimate_days=float(row.get('delivery_estimate_days', 3.0)),
                    date_collected=date_collected
                )
                self.db.add(history)
                records_added += 1
            except Exception as e:
                print(f"⚠️  Error processing historical record: {e}")
                continue
        
        self.db.commit()
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
        
        self.db.commit()
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
        date_collected = datetime.utcnow()
        
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
