"""
What-if Scenario Analysis
Simulate different business decisions and their impact on KPIs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import ProductTiki, ProductExternal, SessionLocal
import pandas as pd
import numpy as np
from sqlalchemy import func


class WhatIfAnalyzer:
    """Scenario-based decision support."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        self.db.close()
    
    def get_baseline_metrics(self):
        """Get current baseline KPIs."""
        
        # Tiki metrics
        tiki_total_sold = self.db.query(
            func.sum(ProductTiki.sold_count)
        ).scalar() or 0
        
        tiki_total_revenue = self.db.query(
            func.sum(ProductTiki.estimated_revenue)
        ).scalar() or 0
        
        tiki_sku_count = self.db.query(ProductTiki).count()
        
        # Competitor metrics
        comp_total_sold = self.db.query(
            func.sum(ProductExternal.sold_count)
        ).scalar() or 0
        
        # Market share
        total_market = tiki_total_sold + comp_total_sold
        market_share = (tiki_total_sold / total_market * 100) if total_market > 0 else 0
        
        return {
            'tiki_sold': int(tiki_total_sold),
            'tiki_revenue': int(tiki_total_revenue),
            'tiki_sku': int(tiki_sku_count),
            'competitor_sold': int(comp_total_sold),
            'market_share_pct': round(market_share, 2),
            'avg_revenue_per_sku': int(tiki_total_revenue / tiki_sku_count) if tiki_sku_count > 0 else 0
        }
    
    def scenario_1_increase_sku(self, sku_increase_pct: float = 20):
        """
        Scenario 1: Tăng số lượng SKU
        Assumption: Mỗi SKU mới có avg performance của SKU hiện tại
        """
        baseline = self.get_baseline_metrics()
        
        # Calculate new SKU count
        current_sku = baseline['tiki_sku']
        new_sku = int(current_sku * (1 + sku_increase_pct / 100))
        sku_added = new_sku - current_sku
        
        # Estimate revenue per SKU
        avg_revenue_per_sku = baseline['avg_revenue_per_sku']
        avg_sold_per_sku = baseline['tiki_sold'] / current_sku if current_sku > 0 else 0
        
        # New metrics
        additional_revenue = sku_added * avg_revenue_per_sku
        additional_sold = int(sku_added * avg_sold_per_sku)
        
        new_total_sold = baseline['tiki_sold'] + additional_sold
        new_total_revenue = baseline['tiki_revenue'] + additional_revenue
        
        # Recalculate market share
        new_market_total = new_total_sold + baseline['competitor_sold']
        new_market_share = (new_total_sold / new_market_total * 100) if new_market_total > 0 else 0
        
        return {
            'scenario_name': f'Tăng {sku_increase_pct}% SKU',
            'scenario_id': 'increase_sku',
            'parameters': {
                'sku_increase_pct': sku_increase_pct,
                'sku_added': sku_added
            },
            'baseline': baseline,
            'predicted': {
                'tiki_sold': int(new_total_sold),
                'tiki_revenue': int(new_total_revenue),
                'tiki_sku': new_sku,
                'market_share_pct': round(new_market_share, 2)
            },
            'impact': {
                'sold_increase': additional_sold,
                'sold_increase_pct': round((additional_sold / baseline['tiki_sold'] * 100), 2),
                'revenue_increase': int(additional_revenue),
                'revenue_increase_pct': round((additional_revenue / baseline['tiki_revenue'] * 100), 2),
                'market_share_gain': round((new_market_share - baseline['market_share_pct']), 2)
            }
        }
    
    def scenario_2_focus_top_gaps(self, top_n: int = 5):
        """
        Scenario 2: Focus vào top gap categories
        Assumption: Fill 50% gap trong 3 tháng
        """
        baseline = self.get_baseline_metrics()
        
        # Get top gap categories
        from api.dashboard_generator import DashboardGenerator
        generator = DashboardGenerator()
        gap_data = generator.generate_gap_opportunity()
        
        # Sort by priority and get top N
        top_gaps = sorted(gap_data, key=lambda x: x['priority_score'], reverse=True)[:top_n]
        
        # Calculate potential from filling 50% of gaps
        total_potential_sold = 0
        total_potential_revenue = 0
        
        for gap in top_gaps:
            # Fill 50% of supply gap
            filled_gap = gap['supply_gap'] * 0.5
            potential_revenue = filled_gap * gap['competitor_avg_price']
            
            total_potential_sold += filled_gap
            total_potential_revenue += potential_revenue
        
        new_total_sold = baseline['tiki_sold'] + int(total_potential_sold)
        new_total_revenue = baseline['tiki_revenue'] + int(total_potential_revenue)
        
        # Market share
        new_market_total = new_total_sold + baseline['competitor_sold']
        new_market_share = (new_total_sold / new_market_total * 100) if new_market_total > 0 else 0
        
        return {
            'scenario_name': f'Focus Top {top_n} Gap Categories',
            'scenario_id': 'focus_gaps',
            'parameters': {
                'top_n_categories': top_n,
                'gap_fill_rate': 0.5,
                'categories': [g['category_l2'] for g in top_gaps]
            },
            'baseline': baseline,
            'predicted': {
                'tiki_sold': int(new_total_sold),
                'tiki_revenue': int(new_total_revenue),
                'market_share_pct': round(new_market_share, 2)
            },
            'impact': {
                'sold_increase': int(total_potential_sold),
                'sold_increase_pct': round((total_potential_sold / baseline['tiki_sold'] * 100), 2),
                'revenue_increase': int(total_potential_revenue),
                'revenue_increase_pct': round((total_potential_revenue / baseline['tiki_revenue'] * 100), 2),
                'market_share_gain': round((new_market_share - baseline['market_share_pct']), 2)
            }
        }
    
    def scenario_3_pricing_strategy(self, discount_pct: float = 10, elasticity: float = 1.5):
        """
        Scenario 3: Chiến lược giảm giá
        Assumption: Price elasticity of demand
        elasticity = % change in quantity / % change in price
        """
        baseline = self.get_baseline_metrics()
        
        # Calculate expected volume increase from price decrease
        # If price down 10%, and elasticity = 1.5, then volume up 15%
        quantity_increase_pct = discount_pct * elasticity
        
        # New sold count
        additional_sold = int(baseline['tiki_sold'] * (quantity_increase_pct / 100))
        new_total_sold = baseline['tiki_sold'] + additional_sold
        
        # Revenue impact = volume gain - price reduction
        # New revenue = (current_revenue * (1 - discount%)) * (1 + volume_increase%)
        revenue_multiplier = (1 - discount_pct/100) * (1 + quantity_increase_pct/100)
        new_total_revenue = int(baseline['tiki_revenue'] * revenue_multiplier)
        revenue_change = new_total_revenue - baseline['tiki_revenue']
        
        # Market share
        new_market_total = new_total_sold + baseline['competitor_sold']
        new_market_share = (new_total_sold / new_market_total * 100) if new_market_total > 0 else 0
        
        return {
            'scenario_name': f'Giảm giá {discount_pct}% (Elasticity {elasticity})',
            'scenario_id': 'pricing_strategy',
            'parameters': {
                'discount_pct': discount_pct,
                'elasticity': elasticity,
                'expected_volume_increase_pct': round(quantity_increase_pct, 2)
            },
            'baseline': baseline,
            'predicted': {
                'tiki_sold': int(new_total_sold),
                'tiki_revenue': int(new_total_revenue),
                'market_share_pct': round(new_market_share, 2)
            },
            'impact': {
                'sold_increase': additional_sold,
                'sold_increase_pct': round((additional_sold / baseline['tiki_sold'] * 100), 2),
                'revenue_increase': int(revenue_change),
                'revenue_increase_pct': round((revenue_change / baseline['tiki_revenue'] * 100), 2),
                'market_share_gain': round((new_market_share - baseline['market_share_pct']), 2)
            }
        }
    
    def scenario_4_combo_strategy(self):
        """
        Scenario 4: Combined Strategy
        - Tăng 15% SKU
        - Focus top 3 gaps
        - Giảm giá 5%
        """
        baseline = self.get_baseline_metrics()
        
        # Calculate cumulative impact
        # Step 1: SKU increase
        s1 = self.scenario_1_increase_sku(15)
        after_s1_sold = s1['predicted']['tiki_sold']
        after_s1_revenue = s1['predicted']['tiki_revenue']
        
        # Step 2: Gap focus (on new baseline)
        s2 = self.scenario_2_focus_top_gaps(3)
        gap_sold_impact = s2['impact']['sold_increase']
        gap_revenue_impact = s2['impact']['revenue_increase']
        
        after_s2_sold = after_s1_sold + gap_sold_impact
        after_s2_revenue = after_s1_revenue + gap_revenue_impact
        
        # Step 3: Pricing (on new baseline)
        discount = 5
        elasticity = 1.5
        volume_increase = discount * elasticity
        
        additional_sold = int(after_s2_sold * (volume_increase / 100))
        final_sold = after_s2_sold + additional_sold
        
        # Revenue after discount
        revenue_multiplier = (1 - discount/100) * (1 + volume_increase/100)
        final_revenue = int(after_s2_revenue * revenue_multiplier)
        
        # Market share
        new_market_total = final_sold + baseline['competitor_sold']
        new_market_share = (final_sold / new_market_total * 100) if new_market_total > 0 else 0
        
        return {
            'scenario_name': 'Combined Strategy (SKU + Gap + Price)',
            'scenario_id': 'combo_strategy',
            'parameters': {
                'sku_increase': '15%',
                'gap_focus': 'Top 3',
                'discount': '5%'
            },
            'baseline': baseline,
            'predicted': {
                'tiki_sold': int(final_sold),
                'tiki_revenue': int(final_revenue),
                'market_share_pct': round(new_market_share, 2)
            },
            'impact': {
                'sold_increase': int(final_sold - baseline['tiki_sold']),
                'sold_increase_pct': round(((final_sold - baseline['tiki_sold']) / baseline['tiki_sold'] * 100), 2),
                'revenue_increase': int(final_revenue - baseline['tiki_revenue']),
                'revenue_increase_pct': round(((final_revenue - baseline['tiki_revenue']) / baseline['tiki_revenue'] * 100), 2),
                'market_share_gain': round((new_market_share - baseline['market_share_pct']), 2)
            }
        }
    
    def generate_all_scenarios(self):
        """Generate all predefined scenarios."""
        
        scenarios = [
            self.scenario_1_increase_sku(20),
            self.scenario_2_focus_top_gaps(5),
            self.scenario_3_pricing_strategy(10, 1.5),
            self.scenario_4_combo_strategy()
        ]
        
        # Add comparison summary
        best_revenue = max(scenarios, key=lambda x: x['impact']['revenue_increase'])
        best_market_share = max(scenarios, key=lambda x: x['impact']['market_share_gain'])
        
        return {
            'scenarios': scenarios,
            'comparison': {
                'best_for_revenue': best_revenue['scenario_name'],
                'best_for_market_share': best_market_share['scenario_name']
            }
        }


if __name__ == "__main__":
    # Test what-if scenarios
    print("🎯 Testing What-if Scenarios...")
    
    analyzer = WhatIfAnalyzer()
    
    results = analyzer.generate_all_scenarios()
    
    print(f"\n✅ Generated {len(results['scenarios'])} scenarios:\n")
    
    for s in results['scenarios']:
        print(f"📊 {s['scenario_name']}")
        print(f"   Revenue Impact: +{s['impact']['revenue_increase']:,} VND (+{s['impact']['revenue_increase_pct']}%)")
        print(f"   Market Share Gain: +{s['impact']['market_share_gain']}%")
        print()
    
    print(f"🏆 Best for Revenue: {results['comparison']['best_for_revenue']}")
    print(f"🏆 Best for Market Share: {results['comparison']['best_for_market_share']}")
