"""
Test the gap opportunity calculation to see actual values.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.dashboard_generator import DashboardGenerator

def test_gap_calculation():
    print("=" * 70)
    print("🧪 TESTING GAP OPPORTUNITY CALCULATION")
    print("=" * 70)
    
    generator = DashboardGenerator()
    gap_data = generator.generate_gap_opportunity()
    
    print(f"\n📊 Total categories analyzed: {len(gap_data)}")
    
    print(f"\n🔝 TOP 10 CATEGORIES BY PRIORITY SCORE:")
    print("-" * 70)
    
    for i, item in enumerate(gap_data[:10], 1):
        print(f"\n{i}. {item['category_l2']} ({item['category_l1']})")
        print(f"   Tiki: {item['tiki_sold']:,} sold | {item['tiki_sku']} SKU | Revenue: {item['tiki_revenue']:,} đ | Rating: {item['tiki_rating']}")
        print(f"   Competitor: {item['competitor_sold']:,} sold | {item['competitor_sku']} SKU | Avg Price: {item['competitor_avg_price']:,} đ | Rating: {item['competitor_rating']}")
        print(f"   SKU Gap: {item['sku_gap']:,} | Revenue Potential: {item['revenue_potential']:,} đ")
        print(f"   Priority Score: {item['priority_score']} points")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_gap_calculation()
