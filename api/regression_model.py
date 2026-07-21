"""
ASG2 Q2 Regression Model — Interaction Effect of Price, Authentic, Delivery on Sales
ln(sold+1) = 2.4146 - 1.3132e-6*Price + 0.7983*is_authentic + 1.4037e-4*delivery_days + 3.5816e-7*(Price × is_authentic)
"""
import math
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import ProductTiki, SessionLocal
from sqlalchemy import func

COEF_INTERCEPT = 2.4146
COEF_PRICE = -1.3132e-6
COEF_AUTHENTIC = 0.7983
COEF_DELIVERY = 1.4037e-4
COEF_PRICE_AUTH = 3.5816e-7

def predict_ln_sold(price, is_authentic, delivery_days):
    return (
        COEF_INTERCEPT
        + COEF_PRICE * price
        + COEF_AUTHENTIC * is_authentic
        + COEF_DELIVERY * delivery_days
        + COEF_PRICE_AUTH * (price * is_authentic)
    )

def predict_sold(price, is_authentic, delivery_days):
    ln_sold = predict_ln_sold(price, is_authentic, delivery_days)
    return max(0, math.exp(ln_sold) - 1)

def predict_revenue(price, is_authentic, delivery_days):
    return price * predict_sold(price, is_authentic, delivery_days)

def find_optimal_price(is_authentic, delivery_days, price_range=(10000, 1000000, 5000)):
    """Grid search for price that maximizes revenue."""
    best_revenue = 0
    best_price = price_range[0]
    p = price_range[0]
    while p <= price_range[1]:
        rev = predict_revenue(p, is_authentic, delivery_days)
        if rev > best_revenue:
            best_revenue = rev
            best_price = p
        p += price_range[2]
    return best_price, best_revenue

def get_category_regression_insights(category_l2=None):
    """Get regression insights for a specific category or all Tiki products."""
    db = SessionLocal()
    query = db.query(ProductTiki)
    if category_l2:
        query = query.filter(ProductTiki.category_l2 == category_l2)
    products = query.all()

    results = []
    for p in products:
        price = p.price or 0
        authentic = 1 if p.is_authentic else 0
        delivery = p.delivery_estimate_days or 3.0
        pred_sold = predict_sold(price, authentic, delivery)
        pred_rev = predict_revenue(price, authentic, delivery)
        authentic_advantage = 1.0
        if not p.is_authentic:
            pred_sold_auth = predict_sold(price, 1, delivery)
            authentic_advantage = pred_sold_auth / max(pred_sold, 1)
        results.append({
            "product_id": p.product_id,
            "product_name": p.product_name,
            "category_l2": p.category_l2,
            "price": price,
            "is_authentic": p.is_authentic,
            "delivery_days": delivery,
            "actual_sold": p.sold_count or 0,
            "predicted_sold": round(pred_sold, 1),
            "predicted_revenue": round(pred_rev, 0),
            "authentic_advantage_x": round(authentic_advantage, 2),
        })

    db.close()
    return results

def get_all_categories_optimal_price():
    """Find optimal price for each L2 category."""
    db = SessionLocal()
    cats = db.query(ProductTiki.category_l2).distinct().all()
    results = []
    for (cat,) in cats:
        prods = db.query(ProductTiki).filter(ProductTiki.category_l2 == cat).all()
        avg_delivery = sum(p.delivery_estimate_days or 3.0 for p in prods) / max(len(prods), 1)
        avg_price = sum(p.price or 0 for p in prods) / max(len(prods), 1)
        opt_price, opt_rev = find_optimal_price(0, avg_delivery)
        results.append({
            "category_l2": cat,
            "avg_price": int(avg_price),
            "avg_delivery_days": round(avg_delivery, 1),
            "optimal_price": opt_price,
            "optimal_revenue": int(opt_rev),
            "price_change_pct": round((opt_price - avg_price) / max(avg_price, 1) * 100, 1),
        })
    db.close()
    return results
