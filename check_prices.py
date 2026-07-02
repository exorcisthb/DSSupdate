"""
Check if external products have price data populated.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.schema import ProductExternal, SessionLocal
from sqlalchemy import func

def check_external_prices():
    db = SessionLocal()
    
    print("=" * 70)
    print("🔍 CHECKING EXTERNAL PRODUCT PRICES")
    print("=" * 70)
    
    # Total external products
    total_external = db.query(ProductExternal).count()
    print(f"\n📊 Total external products: {total_external}")
    
    # By platform
    lazada_count = db.query(ProductExternal).filter(ProductExternal.platform == 'Lazada').count()
    shopee_count = db.query(ProductExternal).filter(ProductExternal.platform == 'Shopee').count()
    print(f"   - Lazada: {lazada_count}")
    print(f"   - Shopee: {shopee_count}")
    
    # Check price data
    print(f"\n💰 PRICE DATA ANALYSIS:")
    print("-" * 70)
    
    # Products with price > 0
    with_price = db.query(ProductExternal).filter(ProductExternal.price > 0).count()
    without_price = total_external - with_price
    
    print(f"   ✅ Products with price > 0: {with_price} ({with_price/total_external*100:.1f}%)")
    print(f"   ❌ Products with price = 0: {without_price} ({without_price/total_external*100:.1f}%)")
    
    # By platform
    lazada_with_price = db.query(ProductExternal).filter(
        ProductExternal.platform == 'Lazada',
        ProductExternal.price > 0
    ).count()
    
    shopee_with_price = db.query(ProductExternal).filter(
        ProductExternal.platform == 'Shopee',
        ProductExternal.price > 0
    ).count()
    
    print(f"\n   Lazada: {lazada_with_price}/{lazada_count} có giá ({lazada_with_price/lazada_count*100:.1f}%)")
    print(f"   Shopee: {shopee_with_price}/{shopee_count} có giá ({shopee_with_price/shopee_count*100:.1f}%)")
    
    # Sample data from each platform
    print(f"\n📋 SAMPLE DATA:")
    print("-" * 70)
    
    print("\n🔵 Lazada samples (first 5 products):")
    lazada_samples = db.query(ProductExternal).filter(
        ProductExternal.platform == 'Lazada'
    ).limit(5).all()
    
    for p in lazada_samples:
        print(f"   - {p.product_name[:50]}...")
        print(f"     Category: {p.category_l2}")
        print(f"     Price: {p.price:,.0f} đ | Sold: {p.sold_count} | Rating: {p.rating}")
    
    print("\n🟠 Shopee samples (first 5 products):")
    shopee_samples = db.query(ProductExternal).filter(
        ProductExternal.platform == 'Shopee'
    ).limit(5).all()
    
    for p in shopee_samples:
        print(f"   - {p.product_name[:50]}...")
        print(f"     Category: {p.category_l2}")
        print(f"     Price: {p.price:,.0f} đ | Sold: {p.sold_count} | Rating: {p.rating}")
    
    # Category analysis
    print(f"\n📂 CATEGORY ANALYSIS:")
    print("-" * 70)
    
    # Categories with external data
    categories_with_external = db.query(
        ProductExternal.category_l2,
        func.count(ProductExternal.id).label('count'),
        func.avg(ProductExternal.price).label('avg_price'),
        func.sum(ProductExternal.sold_count).label('total_sold')
    ).filter(
        ProductExternal.category_l2.isnot(None)
    ).group_by(
        ProductExternal.category_l2
    ).order_by(
        func.count(ProductExternal.id).desc()
    ).limit(10).all()
    
    print(f"\n   Top 10 categories with external products:")
    for cat, count, avg_price, total_sold in categories_with_external:
        avg_price_val = avg_price or 0
        total_sold_val = total_sold or 0
        print(f"   - {cat}: {count} products, avg price: {avg_price_val:,.0f} đ, total sold: {total_sold_val:,}")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    check_external_prices()
