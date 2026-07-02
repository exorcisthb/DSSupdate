from database.schema import SessionLocal, ProductTiki, ProductExternal

db = SessionLocal()

print("=== TIKI CATEGORIES (Sample 10) ===")
tiki_cats = db.query(ProductTiki.category_l2).distinct().limit(10).all()
for c in tiki_cats:
    count = db.query(ProductTiki).filter(ProductTiki.category_l2 == c[0]).count()
    print(f"  {c[0]:40s} ({count} products)")

print("\n=== LAZADA CATEGORIES (Sample 10) ===")
laz_cats = db.query(ProductExternal.category_l2).filter(
    ProductExternal.platform == 'Lazada'
).distinct().limit(10).all()
for c in laz_cats:
    count = db.query(ProductExternal).filter(
        ProductExternal.platform == 'Lazada',
        ProductExternal.category_l2 == c[0]
    ).count()
    print(f"  {c[0]:40s} ({count} products)")

print("\n=== SHOPEE CATEGORIES (Sample 10) ===")
shp_cats = db.query(ProductExternal.category_l2).filter(
    ProductExternal.platform == 'Shopee'
).distinct().limit(10).all()
for c in shp_cats:
    count = db.query(ProductExternal).filter(
        ProductExternal.platform == 'Shopee',
        ProductExternal.category_l2 == c[0]
    ).count()
    print(f"  {c[0]:40s} ({count} products)")

# Check overlap
print("\n=== CATEGORY OVERLAP CHECK ===")
tiki_cats_set = set([c[0] for c in db.query(ProductTiki.category_l2).distinct().all()])
external_cats_set = set([c[0] for c in db.query(ProductExternal.category_l2).distinct().all()])

overlap = tiki_cats_set & external_cats_set
print(f"Tiki unique categories: {len(tiki_cats_set)}")
print(f"External unique categories: {len(external_cats_set)}")
print(f"Categories in common: {len(overlap)}")
if overlap:
    print("\nOverlapping categories:")
    for cat in list(overlap)[:10]:
        print(f"  - {cat}")

db.close()
