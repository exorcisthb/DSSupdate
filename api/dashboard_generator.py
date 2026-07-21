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
        
        # Get date range from ProductTikiHistory
        dates = self.db.query(ProductTikiHistory.date_collected).distinct().all()
        if dates:
            dates_list = sorted([pd.to_datetime(d[0]) for d in dates])
            min_date_str = dates_list[0].strftime('%d/%m')
            max_date_str = dates_list[-1].strftime('%d/%m/%Y')
            date_range_str = f"{min_date_str} - {max_date_str}"
            latest_date_str = dates_list[-1].strftime('%d/%m/%Y')
        else:
            date_range_str = "16/07 - 21/07/2026"
            latest_date_str = "21/07/2026"

        return {
            "total_tiki_sku": int(total_tiki_sku),
            "total_tiki_revenue": int(total_tiki_revenue),
            "new_products_count": int(new_products_count),
            "potential_gaps_count": int(potential_gaps_count),
            "tiki_revenue_growth_pct": 5.4,
            "new_sku_growth_pct": 3.5,
            "date_collected_range": date_range_str,
            "latest_date": latest_date_str
        }
    
    def generate_gap_opportunity(self):
        """
        Generate gap opportunity analysis by category.
        Implements ASG2 Q1 Opportunity Score formula:
            Score = 0.4 * (RevSKU / max_RevSKU) + 0.3 * SoldShare + 0.3 * (1 - OfficialDomRatio)
        Also annotates ASG2 Q4 Portfolio Matrix action (Divest / Watch / Invest).
        """

        # ── ASG2 Q4 Portfolio Matrix (hardcoded from report analysis) ──────────
        PORTFOLIO_ACTIONS = {
            # Divest: low sales, low rating, below cost
            "Men's Hoodies":  {"action": "Divest", "reason": "Sales <10 units, Rev/SKU <100K, extreme low rating"},
            "Men's Outfits":  {"action": "Divest", "reason": "0 sold, no traction"},
            "Women's Tops":   {"action": "Divest", "reason": "0 sold, outside core category"},
            # Watch / Hold
            "Men's T-Shirts": {"action": "Watch", "reason": "Large SKU count but avg rating 1.70 — quality audit needed"},
            "Men's Shirts":   {"action": "Watch", "reason": "Low avg rating — conduct factory audit"},
            # Invest / Expand
            "Men's Underwear": {"action": "Invest", "reason": "Total sold >23K, ROI 2.10x, high rating stability"},
            "Men's Shorts":    {"action": "Invest", "reason": "Total sold >28K, ROI 1.95x"},
            "Men's Swimwear":  {"action": "Invest", "reason": "Low barrier to entry, Opportunity Score 47.1"},
        }

        # Get all unique category_l2 from Tiki
        categories_query = self.db.query(
            ProductTiki.category_l1,
            ProductTiki.category_l2
        ).distinct().all()

        gap_data = []

        # Pre-compute totals for normalisation
        total_tiki_sold = self.db.query(
            func.sum(ProductTiki.sold_count)
        ).scalar() or 1

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

            # Official domination ratio for this category
            authentic_products = self.db.query(ProductTiki).filter(
                ProductTiki.category_l2 == cat_l2,
                ProductTiki.is_authentic == True
            ).all()
            authentic_sold = sum(p.sold_count for p in authentic_products)
            official_dom_ratio = (authentic_sold / tiki_sold) if tiki_sold > 0 else 0.0

            # Competitor metrics (Lazada + Shopee)
            comp_products = self.db.query(ProductExternal).filter(
                ProductExternal.category_l2 == cat_l2
            ).all()

            comp_sku = len(comp_products)
            comp_sold = sum(p.sold_count for p in comp_products)

            if comp_sold > 0:
                comp_rating_sum = sum(p.rating * p.sold_count for p in comp_products if p.sold_count > 0)
                comp_rating_avg = comp_rating_sum / comp_sold
            else:
                comp_ratings = [p.rating for p in comp_products if p.rating > 0]
                comp_rating_avg = sum(comp_ratings) / len(comp_ratings) if comp_ratings else 0

            comp_prices = [p.price for p in comp_products if p.price > 0]
            if comp_prices:
                comp_avg_price = sum(comp_prices) / len(comp_prices)
            else:
                # Fallback to Tiki average price for this category if no competitor data exists
                tiki_prices = [p.price for p in tiki_products if p.price > 0]
                comp_avg_price = sum(tiki_prices) / len(tiki_prices) if tiki_prices else 0

            # ── ASG2 Q1 Opportunity Score Formula ──────────────────────────────
            # Score = 0.4 * (RevSKU_norm) + 0.3 * SoldShare + 0.3 * (1 - OfficialDomRatio)
            rev_per_sku = (tiki_revenue / tiki_sku) if tiki_sku > 0 else 0
            sold_share = (tiki_sold / total_tiki_sold) if total_tiki_sold > 0 else 0
            # Normalise RevSKU by dividing by 100M reference (top category)
            rev_sku_norm = min(1.0, rev_per_sku / 100_000_000)

            opportunity_score = (
                0.4 * rev_sku_norm
                + 0.3 * sold_share
                + 0.3 * (1.0 - official_dom_ratio)
            ) * 100  # scale to 0-100

            # Fallback priority using competitor data if Opportunity Score is 0
            if opportunity_score < 1 and comp_sku > 0:
                sku_score = min(40, (comp_sku / 100.0) * 40)
                price_score = min(40, (comp_avg_price / 500_000.0) * 40) if comp_avg_price > 0 else 0
                rating_score = (comp_rating_avg / 5.0) * 20
                opportunity_score = sku_score + price_score + rating_score

            # Revenue potential calculation
            sku_gap = max(0, comp_sku - tiki_sku)
            avg_tiki_sold_per_sku = tiki_sold / tiki_sku if tiki_sku > 0 else 100
            if sku_gap > 0:
                revenue_potential = sku_gap * avg_tiki_sold_per_sku * comp_avg_price
            else:
                # Conservative 20% growth potential if no SKU gap
                revenue_potential = (tiki_sold * 0.2) * comp_avg_price if comp_avg_price > 0 else 0

            # Portfolio action from Q4
            portfolio = PORTFOLIO_ACTIONS.get(cat_l2, {"action": "Monitor", "reason": "Insufficient data for classification"})

            gap_data.append({
                "category_l1": cat_l1,
                "category_l2": cat_l2,
                "tiki_sku": tiki_sku,
                "tiki_sold": int(tiki_sold),
                "tiki_revenue": int(tiki_revenue),
                "tiki_rating": round(tiki_rating_avg, 1),
                "official_dom_ratio": round(official_dom_ratio * 100, 1),
                "competitor_sku": comp_sku,
                "competitor_sold": int(comp_sold),
                "competitor_rating": round(comp_rating_avg, 1),
                "competitor_avg_price": int(comp_avg_price),
                "sku_gap": int(sku_gap),
                "revenue_potential": int(revenue_potential),
                "priority_score": round(opportunity_score, 1),
                "opportunity_score": round(opportunity_score, 1),  # same, explicit alias
                "portfolio_action": portfolio["action"],
                "portfolio_reason": portfolio["reason"],
            })

        # Sort by opportunity_score descending
        gap_data.sort(key=lambda x: x['opportunity_score'], reverse=True)

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
                ProductExternal.review_count.desc()
            ).limit(4).all()
            
            for p in lazada_products:
                est_sold = int(p.sold_count) if p.sold_count > 0 else int((p.review_count or 0) * 5.24)
                recommendations.append({
                    "id": f"lazada_{p.external_id}",
                    "name": p.product_name,
                    "price": int(p.price),
                    "discount_percent": int(p.discount_rate or 0),
                    "sold": est_sold,
                    "rating": float(p.rating or 0),
                    "reviews": int(p.review_count or 0),
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
                ProductExternal.review_count.desc()
            ).limit(4).all()
            
            for p in shopee_products:
                est_sold = int(p.sold_count) if p.sold_count > 0 else int((p.review_count or 0) * 5.24)
                recommendations.append({
                    "id": f"shopee_{p.external_id}",
                    "name": p.product_name,
                    "price": int(p.price),
                    "discount_percent": 0,  # Shopee data doesn't have this
                    "sold": est_sold,
                    "rating": float(p.rating or 0),
                    "reviews": int(p.review_count or 0),
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
    
    def generate_portfolio_matrix(self):
        """
        Generate ASG2 Q4 Portfolio Divestment Matrix.
        Returns categorized list: Divest / Watch / Invest.
        """
        MATRIX = [
            {
                "category": "Men's Underwear",
                "action": "Invest",
                "total_sold": 23143,
                "revenue_per_sku": 59117755,
                "avg_rating": 3.5,
                "official_dom_pct": 92.3,
                "reason": "Total sold >23K, ROI 2.10×, high rating stability (>3.0). Allocate 90% of capital.",
            },
            {
                "category": "Men's Shorts",
                "action": "Invest",
                "total_sold": 28691,
                "revenue_per_sku": 89507090,
                "avg_rating": 3.2,
                "official_dom_pct": 99.5,
                "reason": "Total sold >28K, ROI 1.95×. Use bundle pricing to maximize volume.",
            },
            {
                "category": "Men's Swimwear",
                "action": "Invest",
                "total_sold": 605,
                "revenue_per_sku": 9520571,
                "avg_rating": 3.8,
                "official_dom_pct": 28.6,
                "reason": "Low barrier to entry (28.6% official dom), Opportunity Score 47.1. Enter NOW.",
            },
            {
                "category": "Men's T-Shirts",
                "action": "Watch",
                "total_sold": 12668,
                "revenue_per_sku": 4781804,
                "avg_rating": 1.70,
                "official_dom_pct": 96.8,
                "reason": "Large SKU count (440) but avg rating 1.70 — suspend new SKUs, conduct factory audit.",
            },
            {
                "category": "Men's Shirts",
                "action": "Watch",
                "total_sold": 446,
                "revenue_per_sku": 6760708,
                "avg_rating": 2.1,
                "official_dom_pct": 65.0,
                "reason": "Low avg rating — conduct quality/sizing audits, target rating 4.0+ before expanding.",
            },
            {
                "category": "Men's Hoodies",
                "action": "Divest",
                "total_sold": 1,
                "revenue_per_sku": 63083,
                "avg_rating": 0.0,
                "official_dom_pct": 0.0,
                "reason": "Sales <10 units, Rev/SKU <100K, no rating data. Clear below cost, do not reorder.",
            },
            {
                "category": "Men's Outfits",
                "action": "Divest",
                "total_sold": 0,
                "revenue_per_sku": 0,
                "avg_rating": 0.0,
                "official_dom_pct": 0.0,
                "reason": "0 units sold. Exit immediately to preserve working capital.",
            },
            {
                "category": "Women's Tops",
                "action": "Divest",
                "total_sold": 0,
                "revenue_per_sku": 0,
                "avg_rating": 0.0,
                "official_dom_pct": 0.0,
                "reason": "0 units sold, outside core men's fashion focus. Exit immediately.",
            },
        ]
        return MATRIX

    def generate_all(self):
        """Generate all dashboard data."""

        print("Generating dashboard data from database...")

        overview = self.generate_overview()
        print(f"Overview: {overview['total_tiki_sku']} SKUs")

        gap_opportunity = self.generate_gap_opportunity()
        print(f"Gap Analysis: {len(gap_opportunity)} categories")

        market_share = self.generate_market_share()
        print(f"Market Share: {len(market_share)} categories")

        trends = self.generate_tiki_trends()
        print(f"Trends: {len(trends['category_trends'])} time points")

        recommendations = self.generate_competitor_recommendations()
        print(f"Recommendations: {len(recommendations)} products")

        portfolio_matrix = self.generate_portfolio_matrix()
        print(f"Portfolio Matrix: {len(portfolio_matrix)} categories classified")

        # Update overview counts
        overview['potential_gaps_count'] = sum(
            1 for g in gap_opportunity if g['opportunity_score'] > 40
        )
        overview['invest_categories_count'] = sum(
            1 for p in portfolio_matrix if p['action'] == 'Invest'
        )

        return {
            "overview": overview,
            "gap_opportunity": gap_opportunity,
            "market_share": market_share,
            "tiki_category_trends": trends['category_trends'],
            "tiki_product_trends": trends['product_trends'],
            "competitor_recommendations": recommendations,
            "portfolio_matrix": portfolio_matrix,
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
