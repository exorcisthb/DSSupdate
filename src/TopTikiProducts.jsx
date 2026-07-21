import React, { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Star, Filter, Search, ExternalLink, Award, Zap, ShoppingBag } from 'lucide-react';

function ProductCardImage({ src, name, category, discount }) {
  const [imgError, setImgError] = useState(false);

  const gradients = [
    'from-emerald-600 to-teal-800',
    'from-blue-600 to-indigo-800',
    'from-purple-600 to-pink-800',
    'from-amber-600 to-orange-800',
    'from-cyan-600 to-blue-800',
  ];
  const charCode = (category || name || 'T').charCodeAt(0);
  const gradient = gradients[charCode % gradients.length];

  return (
    <div className="h-48 w-full bg-slate-100 flex items-center justify-center relative overflow-hidden group">
      {!imgError && src && !src.includes('nan') && src.trim().length > 5 ? (
        <img
          src={src}
          alt={name}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          onError={() => setImgError(true)}
        />
      ) : (
        <div className={`w-full h-full bg-gradient-to-br ${gradient} flex flex-col items-center justify-center p-4 text-white text-center shadow-inner`}>
          <ShoppingBag className="w-10 h-10 mb-2 opacity-80" />
          <span className="text-[11px] font-bold font-mono uppercase tracking-wider line-clamp-1 opacity-90">{category || 'Thời Trang Nam'}</span>
          <span className="text-[9px] opacity-75 mt-1 line-clamp-2 px-2 leading-tight">{name}</span>
        </div>
      )}
      
      {discount > 0 && (
        <span className="absolute bottom-2 right-2 px-2 py-0.5 bg-red-500 text-white text-[10px] font-bold rounded shadow font-mono">
          -{discount}%
        </span>
      )}
    </div>
  );
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

const formatCurrency = (val) => {
  if (val >= 1000000) {
    return (val / 1000000).toFixed(1) + ' triệu đ';
  }
  return new Intl.NumberFormat('vi-VN').format(val) + ' đ';
};

const formatNumber = (val) => {
  return new Intl.NumberFormat('vi-VN').format(val);
};

export default function TopTikiProducts({ selectedL1, searchQuery: globalSearchQuery, priceRange, minRating }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metric, setMetric] = useState('sold'); // 'sold', 'revenue', 'rating'
  const [localSearchQuery, setLocalSearchQuery] = useState('');

  const fetchProducts = async () => {
    setLoading(true);
    try {
      let params = new URLSearchParams({
        metric: metric,
        limit: '100'
      });

      // Apply global category filter
      if (selectedL1 && selectedL1 !== 'All') {
        params.append('category_l1', selectedL1);
      }

      const response = await fetch(`${API_BASE_URL}/api/products/tiki/top?${params}`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setProducts(data.products);
      setError(null);
    } catch (err) {
      console.error('Error fetching products:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [metric, selectedL1]);

  // Apply all global filters
  const filteredProducts = products.filter(p => {
    // Global search filter (from header)
    if (globalSearchQuery && !p.product_name.toLowerCase().includes(globalSearchQuery.toLowerCase())) {
      return false;
    }
    
    // Local search filter (from tab)
    if (localSearchQuery && !p.product_name.toLowerCase().includes(localSearchQuery.toLowerCase())) {
      return false;
    }
    
    // Price range filter
    if (p.price > priceRange) {
      return false;
    }
    
    // Min rating filter
    if (p.rating < minRating) {
      return false;
    }
    
    return true;
  });

  const getBadgeStyle = (badge) => {
    switch(badge) {
      case 'HOT':
        return 'bg-red-100 text-red-700 border-red-300';
      case 'HIGH_REVENUE':
        return 'bg-emerald-100 text-emerald-700 border-emerald-300';
      case 'BEST_RATED':
        return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      default:
        return '';
    }
  };

  const getBadgeIcon = (badge) => {
    switch(badge) {
      case 'HOT':
        return <Zap className="w-3.5 h-3.5" />;
      case 'HIGH_REVENUE':
        return <DollarSign className="w-3.5 h-3.5" />;
      case 'BEST_RATED':
        return <Award className="w-3.5 h-3.5" />;
      default:
        return null;
    }
  };

  if (loading && products.length === 0) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-700 font-semibold">Lỗi tải dữ liệu: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl p-6 shadow-xl">
        <h2 className="text-2xl font-bold font-mono flex items-center gap-2">
          <TrendingUp className="w-7 h-7" />
          TOP SẢN PHẨM TIKI BÁN CHẠY
        </h2>
        <p className="text-emerald-50 mt-2">
          Phân tích sản phẩm HOT nhất trên Tiki - Giúp seller chọn ngành hàng tiềm năng
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white border border-emerald-200 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          {/* Metric selector */}
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-gray-700">
              Xếp hạng theo:
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setMetric('sold')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 ${
                  metric === 'sold'
                    ? 'bg-emerald-500 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                Bán chạy nhất
              </button>
              <button
                onClick={() => setMetric('revenue')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 ${
                  metric === 'revenue'
                    ? 'bg-emerald-500 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <DollarSign className="w-4 h-4" />
                Doanh thu cao
              </button>
              <button
                onClick={() => setMetric('rating')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 ${
                  metric === 'rating'
                    ? 'bg-emerald-500 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Star className="w-4 h-4" />
                Đánh giá tốt
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="flex gap-2 w-full lg:w-auto">
            <div className="relative flex-grow lg:w-80">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Tìm kiếm thêm trong tab này..."
                value={localSearchQuery}
                onChange={(e) => setLocalSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <div className="text-sm text-gray-600 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
            <strong className="text-emerald-700">💡 Lưu ý:</strong> Đây là sản phẩm <strong className="text-emerald-700">[TIKI INTERNAL]</strong> đang bán trên Tiki. 
            Seller có thể chọn các sản phẩm này để bán (nhiều shop có thể bán cùng 1 sản phẩm).
          </div>
          
          {(globalSearchQuery || selectedL1 !== 'All' || priceRange < 1500000 || minRating > 0) && (
            <div className="text-xs text-blue-600 bg-blue-50 border border-blue-200 rounded-lg p-2 flex items-center gap-2">
              <Filter className="w-4 h-4" />
              <span>
                <strong>Đang áp dụng filter global:</strong>
                {selectedL1 !== 'All' && ` Ngành hàng: ${selectedL1}`}
                {globalSearchQuery && ` | Tìm kiếm: "${globalSearchQuery}"`}
                {priceRange < 1500000 && ` | Giá ≤ ${(priceRange/1000).toFixed(0)}k`}
                {minRating > 0 && ` | Rating ≥ ${minRating}`}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {filteredProducts.map((product, idx) => (
          <div
            key={idx}
            className="bg-white rounded-xl border border-emerald-200 hover:border-emerald-400 hover:shadow-2xl transition duration-300 flex flex-col group relative overflow-hidden"
          >
            {/* Platform badge */}
            <div className="absolute top-2 left-2 z-10">
              <span className="px-2 py-1 bg-emerald-600 text-white text-[10px] font-bold rounded border border-emerald-500 shadow-lg">
                TIKI
              </span>
            </div>

            {/* Performance badge */}
            {product.badge && (
              <div className="absolute top-2 right-2 z-10">
                <span className={`px-2 py-1 text-[10px] font-bold rounded border flex items-center gap-1 ${getBadgeStyle(product.badge)}`}>
                  {getBadgeIcon(product.badge)}
                  {product.badge === 'HOT' && '🔥 HOT'}
                  {product.badge === 'HIGH_REVENUE' && '💰 REVENUE'}
                  {product.badge === 'BEST_RATED' && '⭐ RATED'}
                </span>
              </div>
            )}

            {/* Thumbnail */}
            <ProductCardImage
              src={product.thumbnail}
              name={product.product_name}
              category={product.category_l2}
              discount={product.discount_rate}
            />

            {/* Product info */}
            <div className="p-4 flex-grow flex flex-col gap-3">
              <div>
                <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider block">
                  {product.category_l2}
                </span>
                <h4 className="text-sm font-semibold text-gray-800 line-clamp-2 mt-1 leading-relaxed">
                  {product.product_name}
                </h4>
              </div>

              {/* Metrics */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">Giá:</span>
                  <span className="text-sm font-bold text-emerald-600">{formatCurrency(product.price)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">Đã bán:</span>
                  <span className="text-sm font-bold text-orange-600">{formatNumber(product.sold_count)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">Doanh thu:</span>
                  <span className="text-sm font-bold text-purple-600">{formatCurrency(product.estimated_revenue)}</span>
                </div>
              </div>

              {/* Rating */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-2 flex justify-between items-center">
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span className="text-sm font-bold text-yellow-700">{product.rating}</span>
                </div>
                <span className="text-xs text-gray-600">{formatNumber(product.review_count)} review</span>
              </div>

              {/* Link */}
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-lg font-semibold text-xs flex items-center justify-center gap-2 transition shadow-md hover:shadow-lg"
              >
                Xem trên Tiki
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        ))}
      </div>

      {filteredProducts.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-12 text-center">
          <p className="text-gray-600">Không tìm thấy sản phẩm phù hợp</p>
        </div>
      )}

      {/* Footer stats */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
        <p className="text-sm text-gray-700">
          Hiển thị <strong className="text-emerald-700">{filteredProducts.length}</strong> sản phẩm HOT từ Tiki
        </p>
      </div>
    </div>
  );
}
