"""
Dashboard data generator - Query from database and calculate metrics.
This replaces the need for static dashboard_data.json file.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import (
    ProductTiki, ProductTikiHistory, ProductChange, 
    ProductExternal, SessionLocal
)
from sqlalchemy import func
import pandas as pd
from datetime import datetime


class DashboardGenerator:
    """Generate dashboard data from database."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        self.db.close()
    
    def generate_overview(self):
        """Generate overview statistics."""
        
        # Total Tiki SKUs
        total_tiki_sku = self.db.query(ProductTiki).count()
        
        # Total Tiki revenue
        total_tiki_revenue = self.db.query(
            func.sum(ProductTiki.estimated_revenue)
        ).scalar() or 0
        
        # New products count (from changes table with status containing '🆕')
        new_products_count = self.db.query(ProductChange).filter(
            ProductChange.status.like('%🆕%')
        ).count()
        
        # Potential gaps count (categories where competitor sold > tiki sold significantly)
        # This is a simplified calculation - proper one needs gap_opportunity data
        potential_gaps_count = 15  # Placeholder - will be calculated properly below
        
        return {
            "total_tiki_sku": int(total_tiki_sku),
            "total_tiki_revenue": int(total_tiki_revenue),
            "new_products_count": int(new_products_count),
            "potential_gaps_count": int(potential_gaps_count),
            "tiki_revenue_growth_pct": 5.4,  # Mock - needs historical comparison
            "new_sku_growth_pct": 3.5  # Mock - needs historical comparison
        }
    
    def generate_gap_opportunity(self):
        """Generate gap opportunity analysis by category."""
        
        # Get all unique category_l2 from Tiki
        categories_query = self.db.query(
            ProductTiki.category_l1,
            ProductTiki.category_l2
        ).distinct().all()
        
        gap_data = []
        
        for cat_l1, cat_l2 in categories_query:
            if not cat_l2:
                continue
            
            # Tiki metrics
            tiki_products = self.db.query(ProductTiki).filter(
                ProductTiki.category_l2 == cat_l2
            ).all()
            
            tiki_sold = sum(p.sold_count for p in tiki_products)
            tiki_revenue = sum(p.estimated_revenue for p in tiki_products)
            tiki_rating_sum = sum(p.rating * p.sold_count for p in tiki_products if p.sold_count > 0)
            tiki_rating_avg = tiki_rating_sum / tiki_sold if tiki_sold > 0 else 0
            tiki_sku = len(tiki_products)
            
            # Competitor metrics (Lazada + Shopee)
            comp_products = self.db.query(ProductExternal).filter(
                ProductExternal.category_l2 == cat_l2
            ).all()
            
            comp_sku = len(comp_products)
            comp_sold = sum(p.sold_count for p in comp_products)
            
            # Rating calculation: use simple average if sold_count is 0
            if comp_sold > 0:
                comp_rating_sum = sum(p.rating * p.sold_count for p in comp_products if p.sold_count > 0)
                comp_rating_avg = comp_rating_sum / comp_sold
            else:
                # Fallback: simple average of all ratings
                comp_ratings = [p.rating for p in comp_products if p.rating > 0]
                comp_rating_avg = sum(comp_ratings) / len(comp_ratings) if comp_ratings else 0
            
            comp_prices = [p.price for p in comp_products if p.price > 0]
            comp_avg_price = sum(comp_prices) / len(comp_prices) if comp_prices else 0
            
            # Calculate gaps
            # Since external products don't have sold_count, use SKU gap as proxy
            sku_gap = max(0, comp_sku - tiki_sku)
            
            # If competitor has more SKUs, estimate revenue potential
            # Assume each gap SKU could sell like average Tiki SKU in this category
            avg_tiki_sold_per_sku = tiki_sold / tiki_sku if tiki_sku > 0 else 100
            
            # Revenue potential = SKU gap * estimated sales per SKU * competitor avg price
            if sku_gap > 0:
                estimated_gap_sales = sku_gap * avg_tiki_sold_per_sku
                revenue_potential = estimated_gap_sales * comp_avg_price
            else:
                # Even if SKU count is similar, if competitor has products, there's opportunity
                # Use 20% of Tiki sales as conservative estimate
                revenue_potential = (tiki_sold * 0.2) * comp_avg_price if comp_sku > 0 else 0
            
            # Priority score (0-100)
            # Since comp_sold is 0, use alternative metrics:
            # 1. SKU availability (40 points): more external SKUs = higher priority
            sku_availability_score = min(40, (comp_sku / 100.0) * 40)
            
            # 2. Price competitiveness (40 points): higher prices = bigger opportunity
            price_score = min(40, (comp_avg_price / 500000.0) * 40) if comp_avg_price > 0 else 0
            
            # 3. Rating score (20 points): higher ratings = better opportunity
            rating_score = (comp_rating_avg / 5.0) * 20
            
            priority_score = sku_availability_score + price_score + rating_score
            
            gap_data.append({
                "category_l1": cat_l1,
                "category_l2": cat_l2,
                "tiki_sku": tiki_sku,
                "tiki_sold": int(tiki_sold),
                "tiki_revenue": int(tiki_revenue),
                "tiki_rating": round(tiki_rating_avg, 1),
                "competitor_sku": comp_sku,
                "competitor_sold": int(comp_sold),
                "competitor_rating": round(comp_rating_avg, 1),
                "competitor_avg_price": int(comp_avg_price),
                "sku_gap": int(sku_gap),
                "revenue_potential": int(revenue_potential),
                "priority_score": round(priority_score, 1)
            })
        
        # Sort by priority score
        gap_data.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return gap_data
    
    def generate_market_share(self):
        """Generate market share comparison by category."""
        
        categories_query = self.db.query(
            ProductTiki.category_l1,
            ProductTiki.category_l2
        ).distinct().all()
        
        market_share = []
        
        for cat_l1, cat_l2 in categories_query:
            if not cat_l2:
                continue
            
            # Tiki sold
            tiki_sold = self.db.query(
                func.sum(ProductTiki.sold_count)
            ).filter(
                ProductTiki.category_l2 == cat_l2
            ).scalar() or 0
            
            # Lazada sold
            lazada_sold = self.db.query(
                func.sum(ProductExternal.sold_count)
            ).filter(
                ProductExternal.category_l2 == cat_l2,
                ProductExternal.platform == 'Lazada'
            ).scalar() or 0
            
            # Shopee sold
            shopee_sold = self.db.query(
                func.sum(ProductExternal.sold_count)
            ).filter(
                ProductExternal.category_l2 == cat_l2,
                ProductExternal.platform == 'Shopee'
            ).scalar() or 0
            
            total = tiki_sold + lazada_sold + shopee_sold
            
            market_share.append({
                "category_l1": cat_l1,
                "category_l2": cat_l2,
                "Tiki": int(tiki_sold),
                "Lazada": int(lazada_sold),
                "Shopee": int(shopee_sold),
                "total": int(total)
            })
        
        return market_share
    
    def generate_tiki_trends(self):
        """Generate Tiki trends (category and product level)."""
        
        # Category trends by date
        dates_query = self.db.query(
            ProductTikiHistory.date_collected
        ).distinct().order_by(
            ProductTikiHistory.date_collected
        ).all()
        
        dates = [str(d[0]) for d in dates_query]
        
        # Category L1 trends
        category_trends = []
        categories_l1 = ["Thời trang nam", "Thời trang nữ", "Giày - Dép nam", "Phụ kiện thời trang"]
        
        for date in dates:
            trend_point = {"date": date}
            
            for cat_l1 in categories_l1:
                sold_sum = self.db.query(
                    func.sum(ProductTikiHistory.sold_count)
                ).filter(
                    ProductTikiHistory.date_collected == date,
                    ProductTikiHistory.category_l1 == cat_l1
                ).scalar() or 0
                
                trend_point[cat_l1] = int(sold_sum)
            
            category_trends.append(trend_point)
        
        # Top 5 trending products
        top_changes = self.db.query(ProductChange).order_by(
            ProductChange.sold_increase.desc()
        ).limit(5).all()
        
        # Product trends for top 5
        product_trends = []
        product_names = {}
        
        for change in top_changes:
            short_name = change.product_name[:30] + "..." if len(change.product_name) > 30 else change.product_name
            product_names[change.product_id] = short_name
        
        for date in dates:
            trend_point = {"date": date}
            
            for change in top_changes:
                sold = self.db.query(
                    ProductTikiHistory.sold_count
                ).filter(
                    ProductTikiHistory.product_id == change.product_id,
                    ProductTikiHistory.date_collected == date
                ).scalar() or 0
                
                trend_point[product_names[change.product_id]] = int(sold)
            
            product_trends.append(trend_point)
        
        return {
            "category_trends": category_trends,
            "product_trends": product_trends
        }
    
    def generate_competitor_recommendations(self):
        """Generate top competitor product recommendations."""
        
        # Get top categories by priority
        gap_data = self.generate_gap_opportunity()
        top_categories = [g['category_l2'] for g in gap_data[:6]]
        
        recommendations = []
        
        for cat_l2 in top_categories:
            # Top Lazada products
            lazada_products = self.db.query(ProductExternal).filter(
                ProductExternal.category_l2 == cat_l2,
                ProductExternal.platform == 'Lazada'
            ).order_by(
                ProductExternal.sold_count.desc()
            ).limit(4).all()
            
            for p in lazada_products:
                recommendations.append({
                    "id": f"lazada_{p.external_id}",
                    "name": p.product_name,
                    "price": int(p.price),
                    "discount_percent": int(p.discount_rate),
                    "sold": int(p.sold_count),
                    "rating": float(p.rating),
                    "reviews": int(p.review_count),
                    "origin": p.origin or "Không rõ",
                    "link": p.url,
                    "thumbnail": p.thumbnail or "",
                    "platform": "Lazada",
                    "category_l1": p.category_l1,
                    "category_l2": p.category_l2
                })
            
            # Top Shopee products
            shopee_products = self.db.query(ProductExternal).filter(
                ProductExternal.category_l2 == cat_l2,
                ProductExternal.platform == 'Shopee'
            ).order_by(
                ProductExternal.sold_count.desc()
            ).limit(4).all()
            
            for p in shopee_products:
                recommendations.append({
                    "id": f"shopee_{p.external_id}",
                    "name": p.product_name,
                    "price": int(p.price),
                    "discount_percent": 0,  # Shopee data doesn't have this
                    "sold": int(p.sold_count),
                    "rating": float(p.rating),
                    "reviews": int(p.review_count),
                    "origin": "Không rõ",
                    "link": p.url,
                    "thumbnail": p.thumbnail or "",
                    "platform": "Shopee",
                    "category_l1": p.category_l1,
                    "category_l2": p.category_l2
                })
        
        # Sort by sold count
        recommendations.sort(key=lambda x: x['sold'], reverse=True)
        
        return recommendations
    
    def generate_all(self):
        """Generate all dashboard data."""
        
        print("🔄 Generating dashboard data from database...")
        
        overview = self.generate_overview()
        print(f"✅ Overview: {overview['total_tiki_sku']} SKUs")
        
        gap_opportunity = self.generate_gap_opportunity()
        print(f"✅ Gap Analysis: {len(gap_opportunity)} categories")
        
        market_share = self.generate_market_share()
        print(f"✅ Market Share: {len(market_share)} categories")
        
        trends = self.generate_tiki_trends()
        print(f"✅ Trends: {len(trends['category_trends'])} time points")
        
        recommendations = self.generate_competitor_recommendations()
        print(f"✅ Recommendations: {len(recommendations)} products")
        
        # Update overview with actual gaps count
        overview['potential_gaps_count'] = sum(1 for g in gap_opportunity if g['priority_score'] > 40)
        
        return {
            "overview": overview,
            "gap_opportunity": gap_opportunity,
            "market_share": market_share,
            "tiki_category_trends": trends['category_trends'],
            "tiki_product_trends": trends['product_trends'],
            "competitor_recommendations": recommendations
        }


if __name__ == "__main__":
    # Test generator
    generator = DashboardGenerator()
    data = generator.generate_all()
    
    print("\n" + "="*60)
    print("✅ Dashboard data generated successfully!")
    print("="*60)
    
    import json
    print("\nSample data:")
    print(json.dumps({
        "overview": data['overview'],
        "gap_categories_count": len(data['gap_opportunity']),
        "market_categories_count": len(data['market_share']),
        "trend_points": len(data['tiki_category_trends']),
        "recommendations_count": len(data['competitor_recommendations'])
    }, indent=2, ensure_ascii=False))
