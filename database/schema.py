"""
Database schema definitions for DSS Visual platform.
Supports both SQLite (development) and PostgreSQL (production).
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

# Database engine
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dss_data.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ProductTiki(Base):
    """Current snapshot of Tiki products."""
    __tablename__ = "products_tiki"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), nullable=False, unique=True, index=True)
    product_name = Column(Text, nullable=False)
    category_l1 = Column(String(200), index=True)
    category_l2 = Column(String(200), index=True)
    price = Column(Float, default=0.0)
    sold_count = Column(Integer, default=0)
    estimated_revenue = Column(Float, default=0.0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    discount_rate = Column(Float, default=0.0)
    url = Column(Text)
    thumbnail = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_category_l1_l2', 'category_l1', 'category_l2'),
    )


class ProductTikiHistory(Base):
    """Historical snapshots of Tiki products."""
    __tablename__ = "products_tiki_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), nullable=False, index=True)
    product_name = Column(Text, nullable=False)
    category_l1 = Column(String(200), index=True)
    category_l2 = Column(String(200), index=True)
    price = Column(Float, default=0.0)
    sold_count = Column(Integer, default=0)
    estimated_revenue = Column(Float, default=0.0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    discount_rate = Column(Float, default=0.0)
    url = Column(Text)
    thumbnail = Column(Text)
    date_collected = Column(DateTime, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_product_date', 'product_id', 'date_collected'),
        Index('idx_category_date', 'category_l1', 'category_l2', 'date_collected'),
    )


class ProductChange(Base):
    """Product changes detected between snapshots."""
    __tablename__ = "products_changes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), nullable=False, index=True)
    product_name = Column(Text, nullable=False)
    category = Column(String(200), index=True)
    status = Column(String(50))  # "🆕 Sản phẩm mới", "📈 Tăng mạnh", etc.
    old_sold = Column(Integer, default=0)
    new_sold = Column(Integer, default=0)
    sold_increase = Column(Integer, default=0)
    sold_increase_pct = Column(Float, default=0.0)
    old_price = Column(Float, default=0.0)
    new_price = Column(Float, default=0.0)
    price_change = Column(Float, default=0.0)
    price_change_pct = Column(Float, default=0.0)
    url = Column(Text)
    thumbnail = Column(Text)
    date_detected = Column(DateTime, default=datetime.utcnow, index=True)


class ProductExternal(Base):
    """Products from external platforms (Lazada, Shopee)."""
    __tablename__ = "products_external"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)  # "Lazada" or "Shopee"
    external_id = Column(String(100), nullable=False)
    product_name = Column(Text, nullable=False)
    category_l1 = Column(String(200), index=True)
    category_l2 = Column(String(200), index=True)
    price = Column(Float, default=0.0)
    sold_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    discount_rate = Column(Float, default=0.0)
    origin = Column(String(200))
    url = Column(Text)
    thumbnail = Column(Text)
    date_collected = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_platform_category', 'platform', 'category_l1', 'category_l2'),
        Index('idx_platform_date', 'platform', 'date_collected'),
    )


class IngestLog(Base):
    """Track data ingestion to prevent duplicates."""
    __tablename__ = "ingest_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # "github", "manual_upload"
    source_identifier = Column(String(500), nullable=False)  # filename, commit SHA, etc.
    file_date = Column(DateTime)
    platform = Column(String(50))  # "tiki", "lazada", "shopee"
    records_processed = Column(Integer, default=0)
    status = Column(String(50), default="success")  # "success", "failed", "partial"
    error_message = Column(Text)
    ingested_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_source_identifier', 'source', 'source_identifier', unique=True),
    )


def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized successfully!")


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
