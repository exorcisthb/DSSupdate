"""
Debug category matching between Tiki and External products.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.schema import ProductTiki, ProductExternal, SessionLocal
from sqlalchemy import func

def debug_categories():
    db = SessionLocal()
    
    print("=" * 70)
    print("🔍 DEBUGGING CATEGORY MATCHING")
    print("=" * 70)
    
    # Get Tiki categories
    tiki_categories = db.query(
        ProductTiki.category_l2,
        func.count(ProductTiki.id).label('count')
    ).filter(
        ProductTiki.category_l2.isnot(None)
    ).group_by(
        ProductTiki.category_l2
    ).order_by(
        func.count(ProductTiki.id).desc()
    ).all()
    
    print(f"\n📊 TIKI CATEGORIES (Top 15):")
    print("-" * 70)
    for cat, count in tiki_categories[:15]:
        print(f"   {cat}: {count} products")
    
    # Get External categories
    external_categories = db.query(
        ProductExternal.category_l2,
        func.count(ProductExternal.id).label('count'),
        func.avg(ProductExternal.price).label('avg_price')
    ).filter(
        ProductExternal.category_l2.isnot(None)
    ).group_by(
        ProductExternal.category_l2
    ).order_by(
        func.count(ProductExternal.id).desc()
    ).all()
    
    print(f"\n📊 EXTERNAL CATEGORIES (All):")
    print("-" * 70)
    for cat, count, avg_price in external_categories:
        avg_price_val = avg_price or 0
        print(f"   {cat}: {count} products, avg price: {avg_price_val:,.0f} đ")
    
    # Find matching categories
    tiki_cat_set = {cat for cat, _ in tiki_categories}
    external_cat_set = {cat for cat, _, _ in external_categories}
    
    matching_cats = tiki_cat_set.intersection(external_cat_set)
    
    print(f"\n✅ MATCHING CATEGORIES ({len(matching_cats)}):")
    print("-" * 70)
    for cat in sorted(matching_cats):
        tiki_count = db.query(ProductTiki).filter(ProductTiki.category_l2 == cat).count()
        external_count = db.query(ProductExternal).filter(ProductExternal.category_l2 == cat).count()
        
        external_avg_price = db.query(func.avg(ProductExternal.price)).filter(
            ProductExternal.category_l2 == cat,
            ProductExternal.price > 0
        ).scalar() or 0
        
        print(f"   {cat}:")
        print(f"      Tiki: {tiki_count} products")
        print(f"      External: {external_count} products (avg: {external_avg_price:,.0f} đ)")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ DEBUG COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    debug_categories()
