"""
Flask API for DSS Visual backend.
Provides endpoints for data upload and retrieval.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import SessionLocal, init_database
from data_fetcher.data_processor import DataProcessor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload external platform data file (Lazada or Shopee).
    
    Form data:
        - file: Excel file
        - platform: 'lazada' or 'shopee'
    """
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    platform = request.form.get('platform', '').lower()
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if platform not in ['lazada', 'shopee']:
        return jsonify({'error': 'Invalid platform. Must be lazada or shopee'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .xlsx and .xls allowed'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{platform}_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)
        
        # Read and process file
        df = pd.read_excel(filepath)
        
        # Apply classification if needed
        if 'category_l1' not in df.columns or 'category_l2' not in df.columns:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from process_data import classify_product
            
            if platform == 'lazada':
                classified = df['Tên sản phẩm'].apply(classify_product)
            else:  # shopee
                classified = df['title'].apply(classify_product)
            
            df['category_l1'] = [x[0] for x in classified]
            df['category_l2'] = [x[1] for x in classified]
        
        # Ingest to database
        db = SessionLocal()
        processor = DataProcessor(db)
        
        source_identifier = f"api_upload_{saved_filename}"
        count = processor.ingest_external_products(
            df,
            platform.capitalize(),
            source_identifier
        )
        
        # Log ingestion
        processor.log_ingest(
            source='api_upload',
            identifier=source_identifier,
            platform=platform,
            records_count=count,
            status='success'
        )
        
        db.close()
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded and processed {count} {platform} products',
            'records_count': count,
            'filename': saved_filename
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error processing file: {str(e)}'
        }), 500


@app.route('/api/ingest/github', methods=['POST'])
def trigger_github_ingest():
    """
    Trigger GitHub data ingestion.
    """
    try:
        from data_fetcher.github_fetcher import GitHubDataFetcher
        
        db = SessionLocal()
        processor = DataProcessor(db)
        
        fetcher = GitHubDataFetcher()
        commit_info = fetcher.get_latest_commit_info(fetcher.data_path)
        
        if commit_info:
            source_identifier = f"github_commit_{commit_info['sha'][:8]}"
            
            # Check if already ingested
            if processor.check_already_ingested('github', source_identifier):
                return jsonify({
                    'success': False,
                    'message': f"Data from commit {commit_info['sha'][:8]} already ingested"
                }), 400
        else:
            source_identifier = f"github_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Fetch and ingest data
        clean_df, historical_df, changes_df = fetcher.fetch_latest_data()
        
        total_records = 0
        
        if clean_df is not None:
            count = processor.ingest_tiki_clean(clean_df, source_identifier)
            total_records += count
        
        if historical_df is not None:
            count = processor.ingest_tiki_historical(historical_df, source_identifier)
            total_records += count
        
        if changes_df is not None:
            count = processor.ingest_tiki_changes(changes_df, source_identifier)
            total_records += count
        
        # Log ingestion
        processor.log_ingest(
            source='github',
            identifier=source_identifier,
            platform='tiki',
            records_count=total_records,
            status='success'
        )
        
        db.close()
        
        return jsonify({
            'success': True,
            'message': f'Successfully ingested {total_records} records from GitHub',
            'records_count': total_records,
            'commit_sha': commit_info['sha'][:8] if commit_info else None
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error during GitHub ingestion: {str(e)}'
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    try:
        db = SessionLocal()
        
        from database.schema import ProductTiki, ProductExternal, IngestLog
        
        tiki_count = db.query(ProductTiki).count()
        lazada_count = db.query(ProductExternal).filter(
            ProductExternal.platform == 'Lazada'
        ).count()
        shopee_count = db.query(ProductExternal).filter(
            ProductExternal.platform == 'Shopee'
        ).count()
        
        last_ingest = db.query(IngestLog).order_by(
            IngestLog.ingested_at.desc()
        ).first()
        
        db.close()
        
        return jsonify({
            'tiki_products': tiki_count,
            'lazada_products': lazada_count,
            'shopee_products': shopee_count,
            'last_ingest': {
                'source': last_ingest.source if last_ingest else None,
                'platform': last_ingest.platform if last_ingest else None,
                'timestamp': last_ingest.ingested_at.isoformat() if last_ingest else None,
                'records': last_ingest.records_processed if last_ingest else 0
            }
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error fetching stats: {str(e)}'
        }), 500


@app.route('/api/decision/evaluate', methods=['GET', 'POST'])
def evaluate_decision_endpoint():
    """
    Evaluate best product and decision score for selected category.
    Query params / JSON body:
        - category: category_l2 name (e.g., 'Đồ lót nam', 'Quần short nam')
    """
    try:
        category_l2 = request.args.get('category')
        if not category_l2 and request.is_json and request.get_json():
            category_l2 = request.json.get('category')
            
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from dashboard_generator import DashboardGenerator
        
        generator = DashboardGenerator()
        res = generator.evaluate_decision(category_l2)
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/all', methods=['GET'])
def get_dashboard_all():
    """
    Get all dashboard data from database.
    This replaces the need for dashboard_data.json file.
    """
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from dashboard_generator import DashboardGenerator
        
        generator = DashboardGenerator()
        data = generator.generate_all()
        
        return jsonify(data)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Error generating dashboard data: {str(e)}'
        }), 500


@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    """
    Get predictive forecasts for top categories.
    Query params:
        - top_n: Number of categories (default 5)
        - days: Days to forecast (default 30)
    """
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from analytics.predictive_model import PredictiveModel
        
        top_n = int(request.args.get('top_n', 5))
        days = int(request.args.get('days', 30))
        
        model = PredictiveModel()
        forecasts = model.forecast_top_categories(top_n=top_n, days_ahead=days)
        
        return jsonify({
            'forecasts': forecasts,
            'parameters': {
                'top_n': top_n,
                'days_ahead': days
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Error generating forecast: {str(e)}'
        }), 500


@app.route('/api/regression/insights', methods=['GET'])
def get_regression_insights():
    """Q2: Regression model insights — predict sold from price, authentic, delivery."""
    try:
        category = request.args.get('category')
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from regression_model import get_category_regression_insights, get_all_categories_optimal_price
        if category:
            data = get_category_regression_insights(category)
        else:
            data = get_category_regression_insights()
        optimal = get_all_categories_optimal_price()
        return jsonify({"product_predictions": data[:50], "optimal_prices": optimal})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/threshold/check', methods=['GET'])
def check_thresholds():
    """Q3: Check which competitor products meet the 4 success thresholds."""
    try:
        category = request.args.get('category')
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database.schema import ProductExternal, SessionLocal

        THRESHOLD_PRICE_DISCOUNT = 15.2
        THRESHOLD_RATING = 4.3
        THRESHOLD_REVIEWS = 14
        THRESHOLD_DELIVERY = 2.6

        db = SessionLocal()
        query = db.query(ProductExternal)
        if category:
            query = query.filter(ProductExternal.category_l2 == category)
        products = query.all()

        results = []
        for p in products:
            price_discount = p.discount_rate or 0
            passes_price = price_discount >= THRESHOLD_PRICE_DISCOUNT
            passes_rating = (p.rating or 0) >= THRESHOLD_RATING
            passes_reviews = (p.review_count or 0) >= THRESHOLD_REVIEWS
            passes_delivery = (p.delivery_estimate_days or 10) <= THRESHOLD_DELIVERY
            passes_count = sum([passes_price, passes_rating, passes_reviews, passes_delivery])
            results.append({
                "id": p.id,
                "product_name": p.product_name,
                "category_l2": p.category_l2,
                "platform": p.source,
                "price": p.price,
                "discount_rate": price_discount,
                "rating": p.rating,
                "review_count": p.review_count,
                "delivery_estimate_days": p.delivery_estimate_days,
                "is_authentic": p.is_authentic,
                "thresholds": {
                    "price_discount_15.2": passes_price,
                    "rating_4.3": passes_rating,
                    "reviews_14": passes_reviews,
                    "delivery_2.6": passes_delivery,
                    "pass_count": passes_count,
                    "pass_rate": f"{passes_count}/4",
                },
                "meets_all": passes_count == 4,
                "meets_most": passes_count >= 3,
            })
        db.close()
        return jsonify({
            "thresholds": {
                "price_discount_pct": THRESHOLD_PRICE_DISCOUNT,
                "min_rating": THRESHOLD_RATING,
                "min_reviews": THRESHOLD_REVIEWS,
                "max_delivery_days": THRESHOLD_DELIVERY,
            },
            "total_products": len(results),
            "pass_all_count": sum(1 for r in results if r["meets_all"]),
            "pass_most_count": sum(1 for r in results if r["meets_most"]),
            "products": results,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/whatif', methods=['GET'])
def get_whatif_scenarios():
    """
    Get what-if scenario analysis.
    """
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from analytics.whatif_scenarios import WhatIfAnalyzer
        
        analyzer = WhatIfAnalyzer()
        results = analyzer.generate_all_scenarios()
        
        return jsonify(results)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Error generating what-if scenarios: {str(e)}'
        }), 500


@app.route('/api/products/tiki', methods=['GET'])
def get_tiki_products():
    """
    Get raw Tiki products data with pagination and filtering.
    Query params:
        - page: Page number (default 1)
        - per_page: Items per page (default 50, max 200)
        - category_l1: Filter by L1 category
        - category_l2: Filter by L2 category
        - search: Search in product name
    """
    try:
        from database.schema import ProductTiki
        
        db = SessionLocal()
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)
        
        # Filters
        category_l1 = request.args.get('category_l1')
        category_l2 = request.args.get('category_l2')
        search = request.args.get('search')
        
        # Build query
        query = db.query(ProductTiki)
        
        if category_l1:
            query = query.filter(ProductTiki.category_l1 == category_l1)
        if category_l2:
            query = query.filter(ProductTiki.category_l2 == category_l2)
        if search:
            query = query.filter(ProductTiki.product_name.like(f'%{search}%'))
        
        # Order by sold count descending
        query = query.order_by(ProductTiki.sold_count.desc())
        
        # Get total count
        total = query.count()
        
        # Paginate
        products = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to dict
        products_data = [{
            'product_id': p.product_id,
            'product_name': p.product_name,
            'category_l1': p.category_l1,
            'category_l2': p.category_l2,
            'price': float(p.price),
            'sold_count': p.sold_count,
            'estimated_revenue': float(p.estimated_revenue),
            'rating': float(p.rating),
            'review_count': p.review_count,
            'discount_rate': float(p.discount_rate),
            'is_authentic': bool(p.is_authentic),
            'url': p.url,
            'thumbnail': p.thumbnail,
            'last_updated': p.last_updated.isoformat() if p.last_updated else None
        } for p in products]
        
        db.close()
        
        return jsonify({
            'products': products_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Error fetching Tiki products: {str(e)}'
        }), 500


@app.route('/api/products/tiki/top', methods=['GET'])
def get_top_tiki_products():
    """
    Get top Tiki products by various metrics.
    Query params:
        - metric: 'sold', 'revenue', 'rating' (default 'sold')
        - category_l1: Filter by L1 category
        - category_l2: Filter by L2 category
        - limit: Number of products (default 50, max 200)
    """
    try:
        from database.schema import ProductTiki
        
        db = SessionLocal()
        
        # Parameters
        metric = request.args.get('metric', 'sold')
        category_l1 = request.args.get('category_l1')
        category_l2 = request.args.get('category_l2')
        limit = min(int(request.args.get('limit', 50)), 200)
        
        # Build query
        query = db.query(ProductTiki)
        
        if category_l1:
            query = query.filter(ProductTiki.category_l1 == category_l1)
        if category_l2:
            query = query.filter(ProductTiki.category_l2 == category_l2)
        
        # Order by metric
        if metric == 'revenue':
            query = query.order_by(ProductTiki.estimated_revenue.desc())
        elif metric == 'rating':
            query = query.filter(ProductTiki.review_count > 10).order_by(
                ProductTiki.rating.desc(),
                ProductTiki.sold_count.desc()
            )
        else:  # sold (default)
            query = query.order_by(ProductTiki.sold_count.desc())
        
        # Get products
        products = query.limit(limit).all()
        
        # Convert to dict
        products_data = [{
            'product_id': p.product_id,
            'product_name': p.product_name,
            'category_l1': p.category_l1,
            'category_l2': p.category_l2,
            'price': float(p.price),
            'sold_count': p.sold_count,
            'estimated_revenue': float(p.estimated_revenue),
            'rating': float(p.rating),
            'review_count': p.review_count,
            'discount_rate': float(p.discount_rate),
            'is_authentic': bool(p.is_authentic),
            'url': p.url,
            'thumbnail': p.thumbnail,
            'badge': _get_product_badge(p, metric)
        } for p in products]
        
        db.close()
        
        return jsonify({
            'products': products_data,
            'metric': metric,
            'total': len(products_data)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Error fetching top Tiki products: {str(e)}'
        }), 500


def _get_product_badge(product, metric):
    """Determine badge for product based on metric."""
    if metric == 'sold' and product.sold_count > 1000:
        return 'HOT'
    elif metric == 'revenue' and product.estimated_revenue > 100000000:
        return 'HIGH_REVENUE'
    elif metric == 'rating' and product.rating >= 4.5 and product.review_count > 50:
        return 'BEST_RATED'
    return None


@app.route('/api/products/external', methods=['GET'])
def get_external_products():
    """
    Get raw external (Lazada/Shopee) products data with pagination and filtering.
    Query params:
        - platform: 'Lazada' or 'Shopee' (required)
        - page: Page number (default 1)
        - per_page: Items per page (default 50, max 200)
        - category_l1: Filter by L1 category
        - category_l2: Filter by L2 category
        - search: Search in product name
    """
    try:
        from database.schema import ProductExternal
        
        platform = request.args.get('platform')
        if not platform or platform not in ['Lazada', 'Shopee']:
            return jsonify({'error': 'Invalid or missing platform parameter'}), 400
        
        db = SessionLocal()
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)
        
        # Filters
        category_l1 = request.args.get('category_l1')
        category_l2 = request.args.get('category_l2')
        search = request.args.get('search')
        
        # Build query
        query = db.query(ProductExternal).filter(ProductExternal.platform == platform)
        
        if category_l1:
            query = query.filter(ProductExternal.category_l1 == category_l1)
        if category_l2:
            query = query.filter(ProductExternal.category_l2 == category_l2)
        if search:
            query = query.filter(ProductExternal.product_name.like(f'%{search}%'))
        
        # Order by price descending (since sold_count is 0)
        query = query.order_by(ProductExternal.price.desc())
        
        # Get total count
        total = query.count()
        
        # Paginate
        products = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to dict
        products_data = [{
            'external_id': p.external_id,
            'product_name': p.product_name,
            'platform': p.platform,
            'category_l1': p.category_l1,
            'category_l2': p.category_l2,
            'price': float(p.price),
            'sold_count': p.sold_count,
            'rating': float(p.rating),
            'review_count': p.review_count,
            'discount_rate': float(p.discount_rate),
            'is_authentic': bool(p.is_authentic),
            'origin': p.origin,
            'url': p.url,
            'thumbnail': p.thumbnail,
            'date_collected': p.date_collected.isoformat() if p.date_collected else None
        } for p in products]
        
        db.close()
        
        return jsonify({
            'products': products_data,
            'platform': platform,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Error fetching external products: {str(e)}'
        }), 500


@app.route('/api/category/insights', methods=['GET'])
def get_category_insights():
    """Phân tích tăng trưởng, rủi ro, lợi nhuận cho mỗi L2 category."""
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from dashboard_generator import DashboardGenerator
        gen = DashboardGenerator()
        data = gen.generate_category_insights()
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    try:
        print(f"Starting DSS API Server on {host}:{port}")
    except UnicodeEncodeError:
        print(f"[STARTUP] DSS API Server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
