#!/usr/bin/env python
"""Export external data from database back to Excel files for git storage"""

import pandas as pd
from database.schema import SessionLocal, ProductExternal
from datetime import datetime

db = SessionLocal()

print("=" * 60)
print("EXPORTING EXTERNAL DATA TO EXCEL")
print("=" * 60)

# Export Lazada data
print("\n📊 Exporting Lazada data...")
lazada_products = db.query(ProductExternal).filter(
    ProductExternal.platform == "Lazada"
).all()

if lazada_products:
    lazada_data = []
    for p in lazada_products:
        lazada_data.append({
            'external_id': p.external_id,
            'platform': p.platform,
            'product_name': p.product_name,
            'price': p.price,
            'discount_rate': p.discount_rate,
            'rating': p.rating,
            'review_count': p.review_count,
            'sold_count': p.sold_count,
            'thumbnail': p.thumbnail,
            'url': p.url,
            'origin': p.origin,
            'category_l1': p.category_l1,
            'category_l2': p.category_l2,
            'date_collected': p.date_collected
        })
    
    lazada_df = pd.DataFrame(lazada_data)
    filename = 'lazada_history_20260702_clean.xlsx'
    lazada_df.to_excel(filename, index=False)
    print(f"✅ Exported {len(lazada_data)} Lazada products to {filename}")
else:
    print("⚠️  No Lazada data found in database")

# Export Shopee data
print("\n📊 Exporting Shopee data...")
shopee_products = db.query(ProductExternal).filter(
    ProductExternal.platform == "Shopee"
).all()

if shopee_products:
    shopee_data = []
    for p in shopee_products:
        shopee_data.append({
            'external_id': p.external_id,
            'platform': p.platform,
            'product_name': p.product_name,
            'price': p.price,
            'discount_rate': p.discount_rate,
            'rating': p.rating,
            'review_count': p.review_count,
            'sold_count': p.sold_count,
            'thumbnail': p.thumbnail,
            'url': p.url,
            'origin': p.origin,
            'category_l1': p.category_l1,
            'category_l2': p.category_l2,
            'date_collected': p.date_collected
        })
    
    shopee_df = pd.DataFrame(shopee_data)
    filename = 'Shopee Data Cleaned From Scraper.xlsx'
    shopee_df.to_excel(filename, index=False)
    print(f"✅ Exported {len(shopee_data)} Shopee products to {filename}")
else:
    print("⚠️  No Shopee data found in database")

db.close()

print("\n" + "=" * 60)
print("✅ EXPORT COMPLETED")
print("=" * 60)
print("\nThese files are now ready to be added to git.")
print("They will NOT be auto-updated (manual uploads only).")
