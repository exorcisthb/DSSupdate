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
                    thumbnail=str(row.get('thumbnail', ''))
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
                # Map columns based on platform
                if platform == "Lazada":
                    product = ProductExternal(
                        platform=platform,
                        external_id=str(row.get('ID', '')),
                        product_name=str(row.get('Tên sản phẩm', '')),
                        category_l1=str(row.get('category_l1', '')),
                        category_l2=str(row.get('category_l2', '')),
                        price=float(row.get('Giá (VND)', 0)),
                        sold_count=int(row.get('Số lượng đã bán', 0)),
                        rating=float(row.get('Điểm đánh giá', 0)),
                        review_count=int(row.get('Tổng lượt đánh giá', 0)),
                        discount_rate=float(row.get('Phần trăm giảm', 0)),
                        origin=str(row.get('Xuất xứ', '')),
                        url=str(row.get('Link', '')),
                        thumbnail=str(row.get('Thumbnail', '')),
                        date_collected=date_collected
                    )
                elif platform == "Shopee":
                    product = ProductExternal(
                        platform=platform,
                        external_id=str(row.get('id', '')),
                        product_name=str(row.get('title', '')),
                        category_l1=str(row.get('category_l1', '')),
                        category_l2=str(row.get('category_l2', '')),
                        price=float(row.get('final_price', 0)),
                        sold_count=int(row.get('sold', 0)),
                        rating=float(row.get('rating', 0)),
                        review_count=int(row.get('reviews', 0)),
                        discount_rate=0.0,  # Calculate if needed
                        origin="",
                        url=str(row.get('url', '')),
                        thumbnail=str(row.get('image_url', '')),
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
