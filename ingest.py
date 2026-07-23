#!/usr/bin/env python
"""
CLI tool for ingesting data from GitHub or manual uploads.
Usage:
    python ingest.py --source github
    python ingest.py --source manual --file path/to/file.xlsx --platform lazada
"""

import click
import pandas as pd
from datetime import datetime
import sys
import os

from database.schema import SessionLocal, init_database
from data_fetcher.github_fetcher import GitHubDataFetcher
from data_fetcher.data_processor import DataProcessor


@click.group()
def cli():
    """DSS Data Ingestion Tool"""
    pass


@cli.command()
@click.option('--source', type=click.Choice(['github', 'manual']), required=True,
              help='Data source: github or manual upload')
@click.option('--file', type=click.Path(exists=True), 
              help='File path for manual upload')
@click.option('--platform', type=click.Choice(['tiki', 'lazada', 'shopee']),
              help='Platform for manual upload')
@click.option('--force', is_flag=True, 
              help='Force re-ingest even if already processed')
def run(source, file, platform, force):
    """Run data ingestion."""
    
    print("=" * 60)
    print("🚀 DSS Data Ingestion Tool")
    print("=" * 60)
    print()
    
    # Initialize database
    init_database()
    
    # Create database session
    db = SessionLocal()
    processor = DataProcessor(db)
    
    try:
        if source == 'github':
            ingest_from_github(processor, force)
        elif source == 'manual':
            if not file or not platform:
                click.echo("❌ Error: --file and --platform required for manual upload")
                sys.exit(1)
            ingest_manual(processor, file, platform, force)
    
    except Exception as e:
        click.echo(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()
    
    print()
    print("=" * 60)
    print("✅ Ingestion completed!")
    print("=" * 60)


def ingest_from_github(processor: DataProcessor, force: bool = False):
    """Ingest data from GitHub repository."""
    
    print("📡 Fetching data from GitHub...")
    print()
    
    fetcher = GitHubDataFetcher()
    
    # Get latest commit info
    commit_info = fetcher.get_latest_commit_info(fetcher.data_path)
    if commit_info:
        source_identifier = f"github_commit_{commit_info['sha'][:8]}"
        print(f"📌 Latest commit: {commit_info['sha'][:8]}")
        print(f"📅 Date: {commit_info['date']}")
        print(f"💬 Message: {commit_info['message']}")
        print()
        
        # Check if already ingested
        if not force and processor.check_already_ingested('github', source_identifier):
            print(f"⚠️  Data from commit {commit_info['sha'][:8]} already ingested")
            print("   Use --force to re-ingest")
            return
        elif force and processor.check_already_ingested('github', source_identifier):
            processor.delete_ingest_log('github', source_identifier)
    else:
        source_identifier = f"github_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Fetch data
    clean_df, historical_df, changes_df = fetcher.fetch_latest_data()
    
    if clean_df is None and historical_df is None and changes_df is None:
        print("❌ No data files found to ingest")
        return
    
    # Ingest data
    total_records = 0
    
    if clean_df is not None:
        count = processor.ingest_tiki_clean(clean_df, source_identifier)
        total_records += count
    
    if historical_df is not None:
        count = processor.ingest_tiki_historical(historical_df, source_identifier)
        total_records += count
    
    if changes_df is not None:
        count = processor.ingest_tiki_changes(changes_df, source_identifier)
        total_records += count
    
    # Log the ingestion
    processor.log_ingest(
        source='github',
        identifier=source_identifier,
        platform='tiki',
        records_count=total_records,
        status='success'
    )
    
    print()
    print(f"✅ Successfully ingested {total_records} total records from GitHub")


def ingest_manual(processor: DataProcessor, file_path: str, 
                  platform: str, force: bool = False):
    """Ingest data from manual file upload."""
    
    print(f"📁 Loading file: {file_path}")
    print(f"🏢 Platform: {platform.upper()}")
    print()
    
    # Create source identifier
    filename = os.path.basename(file_path)
    source_identifier = f"manual_{platform}_{filename}"
    
    # Check if already ingested
    if not force and processor.check_already_ingested('manual_upload', source_identifier):
        print(f"⚠️  File {filename} already ingested for {platform}")
        print("   Use --force to re-ingest")
        return
    
    # Read Excel file
    try:
        df = pd.read_excel(file_path)
        print(f"📊 Loaded {len(df)} rows from {filename}")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return
    
    # Process based on platform
    if platform in ['lazada', 'shopee']:
        # Apply classification if not already classified
        if 'category_l1' not in df.columns or 'category_l2' not in df.columns:
            print("⚙️  Classifying products...")
            from process_data import classify_product
            
            if platform == 'lazada':
                classified = df['Tên sản phẩm'].apply(classify_product)
            else:  # shopee
                classified = df['title'].apply(classify_product)
            
            df['category_l1'] = [x[0] for x in classified]
            df['category_l2'] = [x[1] for x in classified]
        
        # Ingest external products
        count = processor.ingest_external_products(
            df, 
            platform.capitalize(), 
            source_identifier
        )
        
    elif platform == 'tiki':
        # Determine which type of Tiki file
        if 'date_collected' in df.columns:
            count = processor.ingest_tiki_historical(df, source_identifier)
        elif 'sold_increase' in df.columns:
            count = processor.ingest_tiki_changes(df, source_identifier)
        else:
            count = processor.ingest_tiki_clean(df, source_identifier)
    else:
        print(f"❌ Unsupported platform: {platform}")
        return
    
    # Log the ingestion
    processor.log_ingest(
        source='manual_upload',
        identifier=source_identifier,
        platform=platform,
        records_count=count,
        status='success'
    )
    
    print()
    print(f"✅ Successfully ingested {count} records from {filename}")


@cli.command()
def init():
    """Initialize database tables."""
    print("🔧 Initializing database...")
    init_database()
    print("✅ Database initialized!")


@cli.command()
def status():
    """Show ingestion status and logs."""
    from database.schema import IngestLog
    
    db = SessionLocal()
    
    try:
        logs = db.query(IngestLog).order_by(
            IngestLog.ingested_at.desc()
        ).limit(10).all()
        
        if not logs:
            print("📋 No ingestion logs found")
            return
        
        print("=" * 80)
        print("📋 Recent Ingestion Logs (last 10)")
        print("=" * 80)
        print()
        
        for log in logs:
            status_emoji = "✅" if log.status == "success" else "❌"
            print(f"{status_emoji} {log.ingested_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Source: {log.source} | Platform: {log.platform}")
            print(f"   Identifier: {log.source_identifier}")
            print(f"   Records: {log.records_processed}")
            if log.error_message:
                print(f"   Error: {log.error_message}")
            print()
    
    finally:
        db.close()


if __name__ == '__main__':
    cli()
