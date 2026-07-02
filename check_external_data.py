#!/usr/bin/env python
"""Check external data sources in database"""

from database.schema import SessionLocal, ProductExternal, IngestLog

db = SessionLocal()

print("=" * 60)
print("EXTERNAL PRODUCTS IN DATABASE")
print("=" * 60)

lazada_count = db.query(ProductExternal).filter(ProductExternal.platform == "Lazada").count()
shopee_count = db.query(ProductExternal).filter(ProductExternal.platform == "Shopee").count()

print(f"Lazada products: {lazada_count}")
print(f"Shopee products: {shopee_count}")

print("\n" + "=" * 60)
print("INGEST LOGS FOR EXTERNAL DATA")
print("=" * 60)

logs = db.query(IngestLog).filter(
    IngestLog.platform.in_(['lazada', 'shopee'])
).order_by(IngestLog.ingested_at.desc()).all()

if logs:
    for log in logs:
        print(f"\n{log.platform.upper()}:")
        print(f"  Source: {log.source}")
        print(f"  Identifier: {log.source_identifier}")
        print(f"  Records: {log.records_processed}")
        print(f"  Date: {log.ingested_at}")
else:
    print("\nNo external ingest logs found!")

db.close()
