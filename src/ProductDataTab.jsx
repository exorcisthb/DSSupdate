import React, { useState, useEffect } from 'react';
import { Search, ExternalLink, Star, Filter, ChevronLeft, ChevronRight, ShoppingBag } from 'lucide-react';

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

export default function ProductDataTab({ platform, selectedL1: globalL1, selectedL2: globalL2, searchQuery: globalSearchQuery, priceRange: globalPriceRange, minRating: globalMinRating }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [localSearchQuery, setLocalSearchQuery] = useState('');
  const [perPage] = useState(50);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      let url = '';
      let params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString()
      });

      // Apply global filters
      if (globalSearchQuery) {
        params.append('search', globalSearchQuery);
      }
      if (globalL1 && globalL1 !== 'All') {
        params.append('category_l1', globalL1);
      }
      if (globalL2 && globalL2 !== 'All') {
        params.append('category_l2', globalL2);
      }

      if (platform === 'Tiki') {
        url = `${API_BASE_URL}/api/products/tiki?${params}`;
      } else {
        params.append('platform', platform);
        url = `${API_BASE_URL}/api/products/external?${params}`;
      }

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      
      // Apply client-side filters for price and rating
      let filteredProducts = data.products.filter(p => {
        if (p.price > globalPriceRange) return false;
        if (p.rating < globalMinRating) return false;
        if (localSearchQuery && !p.product_name.toLowerCase().includes(localSearchQuery.toLowerCase())) return false;
        return true;
      });
      
      setProducts(filteredProducts);
      setTotal(data.pagination.total);
      setTotalPages(data.pagination.total_pages);
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
  }, [page, platform, globalL1, globalL2, globalSearchQuery, globalPriceRange, globalMinRating]);

  const handleSearch = () => {
    setPage(1);
    fetchProducts();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const platformColors = {
    Tiki: 'emerald',
    Lazada: 'blue',
    Shopee: 'orange'
  };

  const color = platformColors[platform] || 'gray';

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
      {/* Header with stats and search */}
      <div className={`bg-${color}-50 border border-${color}-200 rounded-xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4`}>
        <div>
          <h2 className={`text-xl font-bold text-${color}-900 font-mono`}>
            DỮ LIỆU {platform.toUpperCase()}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Tổng số: <strong className="text-gray-900">{formatNumber(total)}</strong> sản phẩm
          </p>
        </div>

        <div className="flex gap-2 w-full sm:w-auto">
          <div className="relative flex-grow sm:w-80">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Tìm kiếm thêm trong tab này..."
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <button
            onClick={handleSearch}
            className={`px-4 py-2 bg-${color}-500 hover:bg-${color}-600 text-white rounded-lg font-semibold text-sm transition`}
          >
            Tìm
          </button>
        </div>
      </div>

      {/* Global filter indicator */}
      {(globalSearchQuery || globalL1 !== 'All' || globalPriceRange < 1500000 || globalMinRating > 0) && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-700">
          <Filter className="w-4 h-4 inline mr-2" />
          <strong>Filter global đang áp dụng:</strong>
          {globalL1 !== 'All' && ` Ngành hàng: ${globalL1}`}
          {globalSearchQuery && ` | Tìm kiếm: "${globalSearchQuery}"`}
          {globalPriceRange < 1500000 && ` | Giá ≤ ${(globalPriceRange/1000).toFixed(0)}k`}
          {globalMinRating > 0 && ` | Rating ≥ ${globalMinRating}`}
        </div>
      )}

      {/* Products Table */}
      <div className="bg-white rounded-xl border border-emerald-200 shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-emerald-50 border-b border-emerald-200">
              <tr className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                <th className="py-4 px-4 text-left">Hình ảnh</th>
                  <th className="py-4 px-4 text-left">Tên sản phẩm</th>
                  <th className="py-4 px-4 text-center">Xác thực</th>
                  <th className="py-4 px-4 text-left">Danh mục</th>
                <th className="py-4 px-4 text-right">Giá</th>
                {platform === 'Tiki' && (
                  <>
                    <th className="py-4 px-4 text-right">Đã bán</th>
                    <th className="py-4 px-4 text-right">Doanh thu</th>
                  </>
                )}
                <th className="py-4 px-4 text-center">Đánh giá</th>
                <th className="py-4 px-4 text-center">Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {products.map((product, idx) => (
                <tr key={idx} className="hover:bg-emerald-50/50 transition">
                  {/* Thumbnail */}
                  <td className="py-3 px-4">
                    {product.thumbnail && !product.thumbnail.includes('nan') && product.thumbnail.trim().length > 3 ? (
                      <img
                        src={product.thumbnail}
                        alt={product.product_name}
                        className="w-16 h-16 object-cover rounded border border-gray-200"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="w-16 h-16 bg-gradient-to-br from-teal-600 to-emerald-800 rounded flex items-center justify-center text-white text-xs shadow-inner">
                        <ShoppingBag className="w-6 h-6 opacity-70" />
                      </div>
                    )}
                  </td>

                  {/* Product Name */}
                  <td className="py-3 px-4 max-w-md">
                    <p className="text-sm font-semibold text-gray-800 line-clamp-2">
                      {product.product_name}
                    </p>
                    {platform !== 'Tiki' && product.origin && (
                      <p className="text-xs text-gray-500 mt-1">Xuất xứ: {product.origin}</p>
                    )}
                  </td>

                  {/* Authentic Badge */}
                  <td className="py-3 px-4 text-center">
                    {product.is_authentic ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-bold rounded border border-emerald-300">
                        ✓ Chính hãng
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-500 text-[10px] font-bold rounded border border-gray-200">
                        Thường
                      </span>
                    )}
                  </td>

                  {/* Category */}
                  <td className="py-3 px-4">
                    <div className="text-xs">
                      <p className="font-semibold text-gray-700">{product.category_l2}</p>
                      <p className="text-gray-500">{product.category_l1}</p>
                    </div>
                  </td>

                  {/* Price */}
                  <td className="py-3 px-4 text-right">
                    <span className={`text-sm font-bold text-${color}-600 font-mono`}>
                      {formatCurrency(product.price)}
                    </span>
                    {product.discount_rate > 0 && (
                      <span className="block text-xs text-red-500 font-semibold">
                        -{product.discount_rate}%
                      </span>
                    )}
                  </td>

                  {/* Tiki-specific columns */}
                  {platform === 'Tiki' && (
                    <>
                      <td className="py-3 px-4 text-right">
                        <span className="text-sm font-mono text-gray-800">
                          {formatNumber(product.sold_count)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="text-sm font-mono text-emerald-600 font-semibold">
                          {formatCurrency(product.estimated_revenue)}
                        </span>
                      </td>
                    </>
                  )}

                  {/* Rating */}
                  <td className="py-3 px-4 text-center">
                    <div className="inline-flex items-center gap-1 bg-yellow-50 px-2 py-1 rounded border border-yellow-200">
                      <span className="text-sm font-bold text-yellow-700">{product.rating}</span>
                      <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400" />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatNumber(product.review_count)} review
                    </p>
                  </td>

                  {/* Link */}
                  <td className="py-3 px-4 text-center">
                    {product.url && (
                      <a
                        href={product.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`inline-flex items-center gap-1 px-3 py-1.5 bg-${color}-100 hover:bg-${color}-200 text-${color}-700 rounded-lg text-xs font-semibold transition border border-${color}-200`}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Xem
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="bg-emerald-50 border-t border-emerald-200 px-6 py-4 flex justify-between items-center">
          <p className="text-sm text-gray-600">
            Hiển thị trang {page} / {totalPages} (Tổng: {formatNumber(total)} sản phẩm)
          </p>

          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 bg-white border border-emerald-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-emerald-50 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" />
              Trước
            </button>

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 bg-white border border-emerald-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-emerald-50 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-1"
            >
              Sau
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
