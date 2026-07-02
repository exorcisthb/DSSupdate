"""
Predictive Analytics Module - Time Series Forecasting
Dự đoán sold_count và revenue cho các categories trong tương lai
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import ProductTikiHistory, SessionLocal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


class PredictiveModel:
    """Time series forecasting for Tiki categories."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.models = {}  # Store trained models per category
        self.scalers = {}
    
    def __del__(self):
        self.db.close()
    
    def prepare_time_series_data(self, category_l2: str):
        """
        Prepare time series data for a specific category.
        Returns DataFrame with date and aggregated metrics.
        """
        # Query historical data
        records = self.db.query(ProductTikiHistory).filter(
            ProductTikiHistory.category_l2 == category_l2
        ).all()
        
        if not records:
            return None
        
        # Convert to DataFrame
        data = []
        for r in records:
            data.append({
                'date': r.date_collected,
                'sold_count': r.sold_count,
                'revenue': r.estimated_revenue,
                'price': r.price
            })
        
        df = pd.DataFrame(data)
        
        # Group by date and sum (multiple products per category per day)
        df_agg = df.groupby('date').agg({
            'sold_count': 'sum',
            'revenue': 'sum',
            'price': 'mean'
        }).reset_index()
        
        # Sort by date
        df_agg = df_agg.sort_values('date')
        
        return df_agg
    
    def train_linear_trend_model(self, df: pd.DataFrame, target_col: str):
        """
        Train simple linear regression on time series.
        X = days since start
        y = target metric (sold_count or revenue)
        """
        if df is None or len(df) < 2:
            return None, None
        
        # Convert dates to numeric (days since first date)
        df = df.copy()
        df['days'] = (df['date'] - df['date'].min()).dt.days
        
        X = df[['days']].values
        y = df[target_col].values
        
        # Scale for better numerical stability
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
        
        # Train model
        model = LinearRegression()
        model.fit(X_scaled, y_scaled)
        
        return model, (scaler_X, scaler_y, df['date'].min())
    
    def forecast_category(self, category_l2: str, days_ahead: int = 30):
        """
        Forecast sold_count and revenue for a category.
        
        Args:
            category_l2: Category to forecast
            days_ahead: Number of days to forecast
        
        Returns:
            Dict with forecast results
        """
        # Prepare data
        df = self.prepare_time_series_data(category_l2)
        
        if df is None or len(df) < 2:
            return {
                'category': category_l2,
                'error': 'Insufficient historical data',
                'forecast': []
            }
        
        # Train models for both sold_count and revenue
        model_sold, scalers_sold = self.train_linear_trend_model(df, 'sold_count')
        model_rev, scalers_rev = self.train_linear_trend_model(df, 'revenue')
        
        if model_sold is None:
            return {
                'category': category_l2,
                'error': 'Model training failed',
                'forecast': []
            }
        
        # Generate forecast dates
        last_date = df['date'].max()
        forecast_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]
        
        # Prepare future X values
        scaler_X_sold, scaler_y_sold, date_min_sold = scalers_sold
        scaler_X_rev, scaler_y_rev, date_min_rev = scalers_rev
        
        future_days = [(d - date_min_sold).days for d in forecast_dates]
        X_future = np.array(future_days).reshape(-1, 1)
        X_future_scaled = scaler_X_sold.transform(X_future)
        
        # Predict sold_count
        y_pred_sold_scaled = model_sold.predict(X_future_scaled)
        y_pred_sold = scaler_y_sold.inverse_transform(y_pred_sold_scaled.reshape(-1, 1)).ravel()
        y_pred_sold = np.maximum(y_pred_sold, 0)  # No negative predictions
        
        # Predict revenue
        y_pred_rev_scaled = model_rev.predict(X_future_scaled)
        y_pred_rev = scaler_y_rev.inverse_transform(y_pred_rev_scaled.reshape(-1, 1)).ravel()
        y_pred_rev = np.maximum(y_pred_rev, 0)
        
        # Calculate confidence intervals (simple ±20%)
        forecast_data = []
        for i, date in enumerate(forecast_dates):
            forecast_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'sold_count': int(y_pred_sold[i]),
                'sold_count_lower': int(y_pred_sold[i] * 0.8),
                'sold_count_upper': int(y_pred_sold[i] * 1.2),
                'revenue': int(y_pred_rev[i]),
                'revenue_lower': int(y_pred_rev[i] * 0.8),
                'revenue_upper': int(y_pred_rev[i] * 1.2)
            })
        
        # Historical data for chart
        historical_data = []
        for _, row in df.iterrows():
            historical_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'sold_count': int(row['sold_count']),
                'revenue': int(row['revenue'])
            })
        
        # Calculate trend
        avg_daily_growth = (y_pred_sold[-1] - df['sold_count'].iloc[-1]) / days_ahead
        growth_rate = ((y_pred_sold[-1] / df['sold_count'].iloc[-1]) - 1) * 100 if df['sold_count'].iloc[-1] > 0 else 0
        
        return {
            'category': category_l2,
            'historical': historical_data,
            'forecast': forecast_data,
            'summary': {
                'avg_daily_growth': round(avg_daily_growth, 1),
                'growth_rate_pct': round(growth_rate, 1),
                'current_sold': int(df['sold_count'].iloc[-1]),
                'predicted_sold_30d': int(y_pred_sold[-1]),
                'current_revenue': int(df['revenue'].iloc[-1]),
                'predicted_revenue_30d': int(y_pred_rev[-1])
            }
        }
    
    def forecast_top_categories(self, top_n: int = 5, days_ahead: int = 30):
        """
        Forecast for top N categories by current sales.
        """
        # Get top categories
        from database.schema import ProductTiki
        from sqlalchemy import func, desc
        
        top_cats = self.db.query(
            ProductTiki.category_l2,
            func.sum(ProductTiki.sold_count).label('total_sold')
        ).group_by(
            ProductTiki.category_l2
        ).order_by(
            desc('total_sold')
        ).limit(top_n).all()
        
        results = []
        for cat, _ in top_cats:
            forecast = self.forecast_category(cat, days_ahead)
            if 'error' not in forecast:
                results.append(forecast)
        
        return results


if __name__ == "__main__":
    # Test forecasting
    print("🔮 Testing Predictive Model...")
    
    model = PredictiveModel()
    
    # Forecast top 3 categories
    forecasts = model.forecast_top_categories(top_n=3, days_ahead=30)
    
    print(f"\n✅ Generated forecasts for {len(forecasts)} categories:\n")
    
    for f in forecasts:
        print(f"📊 {f['category']}")
        print(f"   Current sold: {f['summary']['current_sold']:,}")
        print(f"   Predicted (30d): {f['summary']['predicted_sold_30d']:,}")
        print(f"   Growth: {f['summary']['growth_rate_pct']:+.1f}%")
        print()
