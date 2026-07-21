import React, { useState, useMemo, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, 
  LineChart, Line, AreaChart, Area 
} from 'recharts';
import { 
  TrendingUp, ShoppingBag, AlertCircle, Filter, Search, ExternalLink, 
  Star, Percent, Award, Info, Calendar, DollarSign, Layers, CheckCircle2, XCircle, Zap, Activity, Database
} from 'lucide-react';
import ForecastTab from './ForecastTab';
import WhatIfTab from './WhatIfTab';
import ProductDataTab from './ProductDataTab';
import TopTikiProducts from './TopTikiProducts';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

// Utility helper to format currency
const formatCurrency = (val) => {
  if (val >= 1000000000) {
    return (val / 1000000000).toFixed(2) + ' tỷ đ';
  }
  if (val >= 1000000) {
    return (val / 1000000).toFixed(1) + ' triệu đ';
  }
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val).replace('₫', 'đ');
};

// Utility helper to format large numbers
const formatNumber = (val) => {
  return new Intl.NumberFormat('vi-VN').format(val);
};

export default function App() {
  // Loading & Data States
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 1. States for filtering and search
  const [selectedL1, setSelectedL1] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [priceRange, setPriceRange] = useState(1500000); // Max price filter
  const [minRating, setMinRating] = useState(0); // Min rating filter
  const [selectedPlatforms, setSelectedPlatforms] = useState({
    Lazada: true,
    Shopee: true
  });
  
  // States for toggles
  const [trendType, setTrendType] = useState('category'); // 'category' or 'product'
  const [activeTab, setActiveTab] = useState('top-tiki'); // 'gaps', 'top-tiki', 'recommendations', 'forecast', 'whatif', 'tiki-data', 'lazada-data', 'shopee-data'

  // Fetch dashboard data from API on component mount
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/dashboard/all`);
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        setDashboardData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    
    // Optional: Refresh data every 5 minutes
    const interval = setInterval(fetchDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Extract unique L1 categories
  const l1Categories = useMemo(() => {
    if (!dashboardData) return ['All'];
    const cats = new Set(dashboardData.gap_opportunity.map(item => item.category_l1));
    return ['All', ...Array.from(cats)];
  }, [dashboardData]);

  // 2. Filtered Gap Opportunities
  const filteredGaps = useMemo(() => {
    if (!dashboardData) return [];
    return dashboardData.gap_opportunity.filter(item => {
      // L1 filter
      if (selectedL1 !== 'All' && item.category_l1 !== selectedL1) return false;
      // Search filter
      if (searchQuery && !item.category_l2.toLowerCase().includes(searchQuery.toLowerCase()) && !item.category_l1.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      // Price filter (based on competitor average price)
      if (item.competitor_avg_price > priceRange) return false;
      // Rating filter
      if (item.competitor_rating < minRating) return false;
      
      return true;
    });
  }, [dashboardData, selectedL1, searchQuery, priceRange, minRating]);

  // Dynamic Gaps Count based on filtered items
  const dynamicGapsCount = useMemo(() => {
    return filteredGaps.filter(g => g.priority_score > 40).length;
  }, [filteredGaps]);

  // 3. Filtered Competitor Recommendations
  const filteredRecommendations = useMemo(() => {
    if (!dashboardData) return [];
    return dashboardData.competitor_recommendations.filter(item => {
      // L1 filter
      if (selectedL1 !== 'All' && item.category_l1 !== selectedL1) return false;
      // Search filter
      if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase()) && !item.category_l2.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      // Platform filter
      if (!selectedPlatforms[item.platform]) return false;
      // Price filter
      if (item.price > priceRange) return false;
      // Rating filter
      if (item.rating < minRating) return false;

      return true;
    });
  }, [dashboardData, selectedL1, searchQuery, selectedPlatforms, priceRange, minRating]);

  // 4. Market Share Chart Data (Top 10 sorted by total sales)
  const marketShareChartData = useMemo(() => {
    if (!dashboardData) return [];
    const data = dashboardData.market_share.filter(item => {
      if (selectedL1 !== 'All' && item.category_l1 !== selectedL1) return false;
      return item.total > 0;
    });
    // Sort and limit to top 8 to keep chart readable
    return data.sort((a, b) => b.total - a.total).slice(0, 8);
  }, [dashboardData, selectedL1]);

  // 5. Custom Recharts Tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-panel p-3 rounded-lg shadow-xl border border-emerald-200 bg-white/95 text-sm">
          <p className="font-semibold text-gray-800 mb-1.5">{label}</p>
          <div className="space-y-1">
            {payload.map((entry, idx) => (
              <div key={idx} className="flex items-center justify-between gap-4">
                <span className="flex items-center gap-1.5 text-xs text-gray-600">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                  {entry.name}:
                </span>
                <span className="font-mono text-gray-900 font-medium">{formatNumber(entry.value)} sản phẩm</span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  // Render priority score badge with GREEN/YELLOW/RED
  const renderPriorityBadge = (score) => {
    let colorClass = "bg-gray-100 text-gray-600 border-gray-200";
    let text = "Thấp";
    
    if (score >= 80) {
      colorClass = "bg-emerald-50 text-emerald-700 border-emerald-200 font-bold";
      text = "Cực tốt";
    } else if (score >= 60) {
      colorClass = "bg-yellow-50 text-yellow-700 border-yellow-200 font-semibold";
      text = "Tốt";
    } else if (score >= 40) {
      colorClass = "bg-orange-50 text-orange-700 border-orange-200";
      text = "Trung bình";
    } else {
      colorClass = "bg-red-50 text-red-700 border-red-200";
      text = "Thấp";
    }
    
    return (
      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${colorClass}`}>
          {text}
        </span>
        <span className="text-xs font-mono text-gray-500">({score} pts)</span>
      </div>
    );
  };

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-slate-400 font-mono">Đang tải dữ liệu từ database...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Lỗi kết nối API</h2>
          <p className="text-slate-400 mb-4">{error}</p>
          <p className="text-sm text-slate-500 mb-4">
            Đảm bảo API server đang chạy tại: {API_BASE_URL}
          </p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-orange-500 hover:bg-orange-600 rounded-lg font-medium transition"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  // No data state
  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p className="text-slate-400">Không có dữ liệu</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-sky-50 text-gray-800 flex flex-col selection:bg-emerald-500 selection:text-white pb-12">
      
      {/* HEADER SECTION */}
      <header className="border-b border-emerald-100 bg-white/80 backdrop-blur sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white p-2 rounded-lg font-bold text-xs tracking-wider font-mono shadow-md">DSS</span>
              <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent font-mono">TIKI FASHION DECISION SUPPORT SYSTEM</h1>
            </div>
            <p className="text-gray-600 text-sm mt-0.5">
              Hệ thống phân tích khoảng trống sản phẩm thời trang so sánh với Shopee & Lazada
            </p>
          </div>
          
          <div className="flex items-center gap-4 text-xs text-gray-600 self-start md:self-auto bg-white/80 px-4 py-2 rounded-lg border border-emerald-100 shadow-sm">
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-emerald-500" />
              Thu thập ngày: <strong className="text-gray-800">{dashboardData?.overview?.date_collected_range || '16/07 - 21/07/2026'}</strong>
            </span>
            <span className="w-px h-3 bg-emerald-200" />
            <span className="flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-sky-500" />
              Tình trạng: <span className="text-emerald-600 flex items-center gap-1 font-medium">Ổn định <span className="relative flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span></span></span>
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 mt-8 flex-grow w-full space-y-8">
        
        {/* FILTERS & SEARCH ROW */}
        <section className="glass-panel p-5 rounded-2xl border border-emerald-100 shadow-lg flex flex-col lg:flex-row gap-6 items-stretch justify-between">
          
          {/* Category Filter */}
          <div className="flex flex-col gap-2 flex-grow">
            <label className="text-xs font-semibold uppercase tracking-wider text-gray-600 flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-emerald-500" /> Ngành hàng lớn (Category L1)
            </label>
            <div className="flex flex-wrap gap-1.5">
              {l1Categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedL1(cat)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    selectedL1 === cat
                      ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/30 font-semibold'
                      : 'bg-white hover:bg-emerald-50 text-gray-700 border border-emerald-100'
                  }`}
                >
                  {cat === 'All' ? 'Tất cả ngành hàng' : cat}
                </button>
              ))}
            </div>
          </div>

          {/* Sliders and query filter */}
          <div className="flex flex-col sm:flex-row gap-4 lg:w-3/5">
            {/* Search Input */}
            <div className="flex flex-col gap-2 flex-grow">
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-600">Tìm kiếm từ khóa</label>
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Nhập tên sản phẩm, danh mục..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-lg text-xs custom-input font-medium placeholder:text-gray-400"
                />
              </div>
            </div>

            {/* Price Filter Slider */}
            <div className="flex flex-col gap-2 min-w-[150px]">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-600">Giá tối đa</label>
                <span className="text-xs font-mono font-semibold text-emerald-600">{formatCurrency(priceRange)}</span>
              </div>
              <input
                type="range"
                min="50000"
                max="1500000"
                step="50000"
                value={priceRange}
                onChange={(e) => setPriceRange(Number(e.target.value))}
                className="w-full accent-emerald-500 bg-emerald-100 rounded-lg cursor-pointer h-1.5 mt-2"
              />
            </div>

            {/* Rating Filter Slider */}
            <div className="flex flex-col gap-2 min-w-[130px]">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-600">Đánh giá tối thiểu</label>
                <span className="text-xs font-mono font-semibold text-emerald-600 flex items-center gap-0.5">
                  {minRating} <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400 inline" />
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="5"
                step="0.5"
                value={minRating}
                onChange={(e) => setMinRating(Number(e.target.value))}
                className="w-full accent-yellow-500 bg-yellow-100 rounded-lg cursor-pointer h-1.5 mt-2"
              />
            </div>
          </div>

        </section>

        {/* OVERVIEW CARDS GRID */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Card 1: Tiki SKU */}
          <div className="glass-panel p-5 rounded-2xl border border-emerald-100 relative overflow-hidden group hover:border-emerald-200 transition-all duration-300 hover:shadow-lg">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:scale-110 transition-transform duration-300">
              <Layers className="w-24 h-24 text-emerald-500" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 text-xs font-semibold uppercase tracking-wider">Tổng sản phẩm Tiki (SKU)</span>
              <div className="w-7 h-7 rounded-lg bg-sky-100 flex items-center justify-center text-sky-600 border border-sky-200">
                <Layers className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight font-mono text-gray-900 tabular-nums">
                {formatNumber(dashboardData.overview.total_tiki_sku)}
              </span>
              <span className="text-gray-500 text-xs font-mono">SKUs</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 text-xs">
              <span className="text-emerald-600 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded flex items-center gap-0.5 border border-emerald-200">
                <TrendingUp className="w-3 h-3" /> {dashboardData.overview.new_sku_growth_pct}%
              </span>
              <span className="text-gray-500">tăng trưởng tuần</span>
            </div>
          </div>

          {/* Card 2: Tiki Revenue */}
          <div className="glass-panel p-5 rounded-2xl border border-emerald-100 relative overflow-hidden group hover:border-emerald-200 transition-all duration-300 hover:shadow-lg">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:scale-110 transition-transform duration-300">
              <DollarSign className="w-24 h-24 text-emerald-500" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 text-xs font-semibold uppercase tracking-wider">Doanh thu ước tính Tiki</span>
              <div className="w-7 h-7 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600 border border-emerald-200">
                <DollarSign className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight font-mono text-gray-900 tabular-nums">
                {formatCurrency(dashboardData.overview.total_tiki_revenue)}
              </span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 text-xs">
              <span className="text-emerald-600 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded flex items-center gap-0.5 border border-emerald-200">
                <TrendingUp className="w-3 h-3" /> {dashboardData.overview.tiki_revenue_growth_pct}%
              </span>
              <span className="text-gray-500">so với kỳ trước</span>
            </div>
          </div>

          {/* Card 3: New Products Weekly */}
          <div className="glass-panel p-5 rounded-2xl border border-yellow-100 relative overflow-hidden group hover:border-yellow-200 transition-all duration-300 hover:shadow-lg">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:scale-110 transition-transform duration-300">
              <ShoppingBag className="w-24 h-24 text-yellow-500" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 text-xs font-semibold uppercase tracking-wider">Sản phẩm mới tuần qua</span>
              <div className="w-7 h-7 rounded-lg bg-yellow-100 flex items-center justify-center text-yellow-600 border border-yellow-200">
                <ShoppingBag className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight font-mono text-gray-900 tabular-nums">
                {formatNumber(dashboardData.overview.new_products_count)}
              </span>
              <span className="text-gray-500 text-xs font-mono">mã mới</span>
            </div>
            <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-yellow-500" /> Báo cáo biến động từ Changes Report
            </div>
          </div>

          {/* Card 4: Invest Categories — ASG2 Q4 */}
          <div className="glass-panel p-5 rounded-2xl border border-emerald-100 relative overflow-hidden group hover:border-emerald-300 transition-all duration-300 hover:shadow-lg">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:scale-110 transition-transform duration-300">
              <CheckCircle2 className="w-24 h-24 text-emerald-500" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 text-xs font-semibold uppercase tracking-wider">Ngành hàng nên đầu tư</span>
              <div className="w-7 h-7 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600 border border-emerald-200">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight font-mono text-gray-900 tabular-nums">
                {dashboardData.portfolio_matrix
                  ? dashboardData.portfolio_matrix.filter(p => p.action === 'Invest').length
                  : 3}
              </span>
              <span className="text-gray-500 text-xs font-mono">ngành INVEST</span>
            </div>
            <div className="mt-2 text-xs text-emerald-600 flex items-center gap-1 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              Underwear · Shorts · Swimwear
            </div>
          </div>

        </section>

        {/* TABS NAVIGATION */}
        <section className="flex overflow-x-auto border-b border-emerald-100 bg-white/50">
          <button
            onClick={() => setActiveTab('top-tiki')}
            className={`px-6 py-3 font-mono text-xs uppercase tracking-wider font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'top-tiki'
                ? 'border-emerald-500 text-emerald-700 bg-emerald-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/80'
            }`}
          >
            <TrendingUp className="w-4 h-4" /> 🔥 Top Tiki Products
          </button>
          <button
            onClick={() => setActiveTab('gaps')}
            className={`px-6 py-3 font-mono text-xs uppercase tracking-wider font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'gaps'
                ? 'border-emerald-500 text-emerald-700 bg-emerald-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/80'
            }`}
          >
            <AlertCircle className="w-4 h-4" /> Gap Analysis
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`px-6 py-3 font-mono text-xs uppercase tracking-wider font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'recommendations'
                ? 'border-emerald-500 text-emerald-700 bg-emerald-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/80'
            }`}
          >
            <Award className="w-4 h-4" /> So sánh Competitor
          </button>
          <button
            onClick={() => setActiveTab('forecast')}
            className={`px-6 py-3 font-mono text-xs uppercase tracking-wider font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'forecast'
                ? 'border-emerald-500 text-emerald-700 bg-emerald-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/80'
            }`}
          >
            <Activity className="w-4 h-4" /> Predictive Forecast
          </button>
          <button
            onClick={() => setActiveTab('whatif')}
            className={`px-6 py-3 font-mono text-xs uppercase tracking-wider font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'whatif'
                ? 'border-emerald-500 text-emerald-700 bg-emerald-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/80'
            }`}
          >
            <Zap className="w-4 h-4" /> What-If Scenarios
          </button>
          
          {/* Divider */}
          <div className="w-px bg-emerald-200 mx-2 my-2"></div>
          
          {/* Raw Data Tabs */}
          <button
            onClick={() => setActiveTab('tiki-data')}
            className={`px-6 py-3 font-mono text-xs uppercase tracking-wider font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'tiki-data'
                ? 'border-emerald-500 text-emerald-700 bg-emerald-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/80'
            }`}
          >
            <Database className="w-4 h-4" /> Data Tiki
          </button>
          <button
            onClick={() => setActiveTab('lazada-data')}
            className={`px-6 py-3 font-mono text-xs uppercase tracking-wider font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'lazada-data'
                ? 'border-blue-500 text-blue-700 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/80'
            }`}
          >
            <Database className="w-4 h-4" /> Data Lazada
          </button>
          <button
            onClick={() => setActiveTab('shopee-data')}
            className={`px-6 py-3 font-mono text-xs uppercase tracking-wider font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'shopee-data'
                ? 'border-orange-500 text-orange-700 bg-orange-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/80'
            }`}
          >
            <Database className="w-4 h-4" /> Data Shopee
          </button>
        </section>

        {/* TAB CONTENTS */}
        {activeTab === 'top-tiki' ? (
          <TopTikiProducts 
            selectedL1={selectedL1}
            searchQuery={searchQuery}
            priceRange={priceRange}
            minRating={minRating}
          />
        ) : activeTab === 'forecast' ? (
          <ForecastTab />
        ) : activeTab === 'whatif' ? (
          <WhatIfTab />
        ) : activeTab === 'tiki-data' ? (
          <ProductDataTab 
            platform="Tiki" 
            selectedL1={selectedL1}
            searchQuery={searchQuery}
            priceRange={priceRange}
            minRating={minRating}
          />
        ) : activeTab === 'lazada-data' ? (
          <ProductDataTab 
            platform="Lazada"
            selectedL1={selectedL1}
            searchQuery={searchQuery}
            priceRange={priceRange}
            minRating={minRating}
          />
        ) : activeTab === 'shopee-data' ? (
          <ProductDataTab 
            platform="Shopee"
            selectedL1={selectedL1}
            searchQuery={searchQuery}
            priceRange={priceRange}
            minRating={minRating}
          />
        ) : activeTab === 'gaps' ? (
          /* TAB 2: GAP & OPPORTUNITY ANALYSIS — ASG2 Q1 + Q4 */
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* MAIN DATA TABLE */}
            <div className="lg:col-span-2 glass-panel rounded-2xl border border-emerald-200 shadow-xl overflow-hidden flex flex-col justify-between bg-white">
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-emerald-200 bg-emerald-50 text-[10px] uppercase font-bold tracking-wider text-gray-700 font-mono">
                      <th className="py-4 px-5">Ngành hàng (L2)</th>
                      <th className="py-4 px-4 text-right">SKU Tiki</th>
                      <th className="py-4 px-4 text-right">SKU Đối thủ</th>
                      <th className="py-4 px-4 text-right">Giá TB đối thủ</th>
                      <th className="py-4 px-4 text-center">Rating</th>
                      <th className="py-4 px-4 text-right">Revenue tiềm năng</th>
                      <th className="py-4 px-5">Mức độ ưu tiên</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-emerald-100 text-xs font-medium">
                    {filteredGaps.length > 0 ? (
                      filteredGaps.map((item, idx) => (
                        <tr key={idx} className="hover:bg-emerald-50/50 transition duration-150 group">
                          {/* Category name */}
                          <td className="py-3 px-5">
                            <span className="font-semibold text-gray-800 block">{item.category_l2}</span>
                            <span className="text-[10px] text-gray-500 font-mono">{item.category_l1}</span>
                          </td>
                          
                          {/* Tiki SKU */}
                          <td className="py-3 px-4 text-right font-mono text-gray-700 tabular-nums">
                            {formatNumber(item.tiki_sku)}
                          </td>
                          
                          {/* Competitor SKU */}
                          <td className="py-3 px-4 text-right font-mono text-teal-600 font-semibold tabular-nums">
                            {formatNumber(item.competitor_sku || 0)}
                          </td>
                          
                          {/* Competitor Avg Price */}
                          <td className="py-3 px-4 text-right font-mono text-blue-600 font-semibold tabular-nums">
                            {item.competitor_avg_price > 0 ? formatCurrency(item.competitor_avg_price) : '—'}
                          </td>
                          
                          {/* Competitor Rating */}
                          <td className="py-3 px-4 text-center">
                            <span className="inline-flex items-center gap-0.5 bg-yellow-50 px-2 py-0.5 rounded text-yellow-700 font-mono font-bold border border-yellow-200">
                              {item.competitor_rating > 0 ? item.competitor_rating : '—'} 
                              {item.competitor_rating > 0 && <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />}
                            </span>
                          </td>
                          
                          {/* Revenue Opportunity */}
                          <td className="py-3 px-4 text-right font-mono text-emerald-600 font-bold tabular-nums">
                            {formatCurrency(item.revenue_potential)}
                          </td>
                          
                          {/* Priority Score badge */}
                          <td className="py-3 px-5">
                            {renderPriorityBadge(item.priority_score)}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="7" className="py-12 text-center text-gray-500">
                          <AlertCircle className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                          Không tìm thấy dữ liệu nào thỏa mãn các bộ lọc thiết lập.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              
              <div className="bg-emerald-50 px-5 py-4 border-t border-emerald-200 flex justify-between items-center text-xs text-gray-600 font-mono">
                <span>Hiển thị {filteredGaps.length}/{dashboardData.gap_opportunity.length} ngách — sắp xếp theo Opportunity Score (ASG2 Q1)</span>
                <span className="text-teal-600 font-semibold">Score = 0.4×RevSKU + 0.3×SoldShare + 0.3×(1−OfficialDom)</span>
              </div>

            </div>

            {/* SIDEBAR: Portfolio Matrix + Charts */}
            <div className="space-y-6 flex flex-col">

              {/* ASG2 Q4 PORTFOLIO MATRIX */}
              {dashboardData.portfolio_matrix && (
                <div className="glass-panel rounded-2xl border border-emerald-200 shadow-xl bg-white overflow-hidden">
                  <div className="px-5 py-3 border-b border-emerald-100 bg-emerald-50 flex items-center justify-between">
                    <h3 className="text-xs font-bold font-mono uppercase text-gray-700">Portfolio Matrix — ASG2 Q4</h3>
                    <span className="text-[10px] text-gray-500 italic">Divest / Watch / Invest</span>
                  </div>
                  <div className="divide-y divide-gray-50">
                    {dashboardData.portfolio_matrix.map((item, idx) => {
                      const actionConfig = {
                        Invest: { bg: 'bg-emerald-50', text: 'text-emerald-700', badge: 'bg-emerald-100 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500' },
                        Watch:  { bg: 'bg-yellow-50',  text: 'text-yellow-700',  badge: 'bg-yellow-100 text-yellow-700 border-yellow-200',  dot: 'bg-yellow-500' },
                        Divest: { bg: 'bg-red-50',     text: 'text-red-700',     badge: 'bg-red-100 text-red-700 border-red-200',           dot: 'bg-red-500'   },
                      };
                      const cfg = actionConfig[item.action] || actionConfig.Watch;
                      return (
                        <div key={idx} className={`px-4 py-2.5 flex items-center justify-between gap-3 ${cfg.bg}`}>
                          <div className="flex items-center gap-2 min-w-0">
                            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot}`} />
                            <div>
                              <div className="text-xs font-semibold text-gray-800">{item.category}</div>
                              <div className="text-[10px] text-gray-500 truncate max-w-[130px]" title={item.reason}>{item.reason.slice(0, 50)}…</div>
                            </div>
                          </div>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border flex-shrink-0 ${cfg.badge}`}>
                            {item.action}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              
              {/* MARKET SHARE CHART */}
              <div className="glass-panel p-5 rounded-2xl border border-emerald-200 shadow-xl flex-grow flex flex-col justify-between bg-white">
                <div>
                  <h3 className="text-sm font-bold font-mono tracking-wider uppercase text-gray-800">
                    Phân tích Sản lượng tiêu thụ
                  </h3>
                  <p className="text-gray-600 text-xs mt-0.5 mb-4">
                    Thị phần lượng bán (sold count) 8 ngách hàng lớn nhất
                  </p>
                </div>
                
                <div className="h-64 w-full text-xs">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={marketShareChartData}
                      layout="vertical"
                      margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#d1fae5" horizontal={true} vertical={false} />
                      <XAxis type="number" stroke="#6b7280" fontSize={10} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(0)}k` : val} />
                      <YAxis dataKey="category_l2" type="category" stroke="#6b7280" width={90} fontSize={10} />
                      <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(209, 250, 229, 0.3)' }} />
                      <Legend 
                        iconSize={8}
                        iconType="circle"
                        wrapperStyle={{ fontSize: '10px', paddingTop: '10px', borderTop: '1px solid #d1fae5' }}
                      />
                      {/* Bar stacks mapping: Tiki (emerald), Lazada (blue), Shopee (orange) */}
                      <Bar dataKey="Tiki" stackId="a" fill="#10b981" name="Tiki (nội bộ)" radius={[0, 0, 0, 0]} />
                      <Bar dataKey="Lazada" stackId="a" fill="#3b82f6" name="Lazada" radius={[0, 0, 0, 0]} />
                      <Bar dataKey="Shopee" stackId="a" fill="#f97316" name="Shopee" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                <div className="mt-4 pt-3 border-t border-emerald-100 text-[10px] text-gray-500 italic">
                  * Biểu thị sản lượng phân bổ giữa các nền tảng thương mại điện tử
                </div>
              </div>

              {/* TIKI HISTORICAL TRENDS CHART */}
              <div className="glass-panel p-5 rounded-2xl border border-emerald-200 shadow-xl flex-grow flex flex-col justify-between bg-white">
                <div className="flex justify-between items-start gap-4 mb-4">
                  <div>
                    <h3 className="text-sm font-bold font-mono tracking-wider uppercase text-gray-800">
                      Xu hướng tăng trưởng Tiki
                    </h3>
                    <p className="text-gray-600 text-xs mt-0.5">
                      Trực quan snapshot lượng bán tích lũy 5 ngày gần nhất
                    </p>
                  </div>
                  <div className="flex bg-emerald-100 p-0.5 rounded-lg border border-emerald-200 text-[10px] font-mono">
                    <button 
                      onClick={() => setTrendType('category')}
                      className={`px-2.5 py-1 rounded-md transition ${trendType === 'category' ? 'bg-emerald-500 text-white font-semibold' : 'text-gray-600 hover:text-gray-800'}`}
                    >
                      Ngành hàng L1
                    </button>
                    <button 
                      onClick={() => setTrendType('product')}
                      className={`px-2.5 py-1 rounded-md transition ${trendType === 'product' ? 'bg-emerald-500 text-white font-semibold' : 'text-gray-600 hover:text-gray-800'}`}
                    >
                      Mã Hot
                    </button>
                  </div>
                </div>

                <div className="h-56 w-full text-xs">
                  {trendType === 'category' ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={dashboardData.tiki_category_trends}
                        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                      >
                        <defs>
                          <linearGradient id="colorNam" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorNu" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ec4899" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#ec4899" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorGiay" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorPhuKien" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#d1fae5" />
                        <XAxis dataKey="date" stroke="#6b7280" fontSize={9} tickFormatter={(str) => str.slice(-5)} />
                        <YAxis stroke="#6b7280" fontSize={9} />
                        <Tooltip />
                        <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: '9px', paddingTop: '10px' }} />
                        <Area type="monotone" dataKey="Thời trang nam" stroke="#10b981" fillOpacity={1} fill="url(#colorNam)" strokeWidth={2} />
                        <Area type="monotone" dataKey="Thời trang nữ" stroke="#ec4899" fillOpacity={1} fill="url(#colorNu)" strokeWidth={2} />
                        <Area type="monotone" dataKey="Giày - Dép nam" stroke="#3b82f6" fillOpacity={1} fill="url(#colorGiay)" strokeWidth={2} />
                        <Area type="monotone" dataKey="Phụ kiện thời trang" stroke="#f59e0b" fillOpacity={1} fill="url(#colorPhuKien)" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={dashboardData.tiki_product_trends}
                        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#d1fae5" />
                        <XAxis dataKey="date" stroke="#6b7280" fontSize={9} tickFormatter={(str) => str.slice(-5)} />
                        <YAxis stroke="#6b7280" fontSize={9} />
                        <Tooltip />
                        <Legend iconSize={8} iconType="plainline" wrapperStyle={{ fontSize: '9px', paddingTop: '10px' }} />
                        {Object.keys(dashboardData.tiki_product_trends[0] || {})
                          .filter(k => k !== 'date')
                          .map((key, idx) => {
                            const colors = ['#10b981', '#3b82f6', '#f59e0b', '#a855f7', '#ec4899'];
                            return (
                              <Line 
                                key={key}
                                type="monotone" 
                                dataKey={key} 
                                stroke={colors[idx % colors.length]} 
                                strokeWidth={2}
                                dot={{ r: 2 }}
                              />
                            );
                          })
                        }
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>

            </div>

          </section>
        ) : (
          /* TAB 3: COMPETITOR RECOMMENDATIONS — ASG2 Q3 Thresholds */
          <section className="space-y-6">

            {/* ASG2 Q3 THRESHOLD BANNER */}
            <div className="rounded-2xl border-2 border-teal-300 bg-gradient-to-r from-teal-50 to-emerald-50 p-5 shadow-md">
              <div className="flex items-start gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center flex-shrink-0">
                  <Award className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-teal-800 font-mono">Ngưỡng thắng cuộc — Regular Seller vs Official Store (ASG2 Q3)</h3>
                  <p className="text-xs text-teal-700 mt-0.5">Từ mô hình Logistic — đây là tiêu chí tối thiểu để regular seller cạnh tranh thành công với Official Store trên Tiki</p>
                </div>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="bg-white rounded-xl p-3 border border-teal-200 shadow-sm">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-teal-600 mb-1">Chiết khấu giá</div>
                  <div className="text-xl font-bold font-mono text-gray-900">≥ 15.2%</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">So với Official Store</div>
                </div>
                <div className="bg-white rounded-xl p-3 border border-teal-200 shadow-sm">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-teal-600 mb-1">Rating tối thiểu</div>
                  <div className="text-xl font-bold font-mono text-gray-900">≥ 4.3 ★</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Điểm đánh giá trung bình</div>
                </div>
                <div className="bg-white rounded-xl p-3 border border-teal-200 shadow-sm">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-teal-600 mb-1">Lượt review</div>
                  <div className="text-xl font-bold font-mono text-gray-900">≥ 14</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Social proof tối thiểu</div>
                </div>
                <div className="bg-white rounded-xl p-3 border border-teal-200 shadow-sm">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-teal-600 mb-1">Thời gian giao hàng</div>
                  <div className="text-xl font-bold font-mono text-gray-900">≤ 2.6 ngày</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">Dùng Tiki Fulfillment/FBT</div>
                </div>
              </div>
              <div className="mt-3 text-[10px] text-teal-600 italic flex items-center gap-1.5">
                <Info className="w-3 h-3" /> Nguồn: Mô hình Logistic Regression (ASG2 Q3) — trên 1,925 sản phẩm Tiki Fashion thực tế
              </div>
            </div>
            
            {/* Platform filter */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-amber-50 p-4 rounded-xl border border-amber-200">
              <div className="text-xs text-gray-700">
                <strong className="text-amber-700 font-bold">[EXTERNAL — ĐỐI THỦ]</strong> Sản phẩm Lazada &amp; Shopee để tham khảo so sánh với các ngưỡng trên.
                <br />Hãy kiểm tra xem sản phẩm đối thủ có đáp ứng <strong className="text-teal-700">đủ 4 ngưỡng ASG2 Q3</strong> hay không trước khi quyết định cạnh tranh.
              </div>
              
              {/* Platform Switcher */}
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-gray-700 font-mono uppercase">Lọc theo sàn:</span>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2 text-xs cursor-pointer select-none">
                    <input 
                      type="checkbox"
                      checked={selectedPlatforms.Lazada}
                      onChange={(e) => setSelectedPlatforms({...selectedPlatforms, Lazada: e.target.checked})}
                      className="rounded accent-blue-500 cursor-pointer w-4 h-4"
                    />
                    <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 font-semibold border border-blue-200">Lazada</span>
                  </label>
                  
                  <label className="flex items-center gap-2 text-xs cursor-pointer select-none">
                    <input 
                      type="checkbox"
                      checked={selectedPlatforms.Shopee}
                      onChange={(e) => setSelectedPlatforms({...selectedPlatforms, Shopee: e.target.checked})}
                    />
                    <span className="px-2 py-0.5 rounded bg-orange-100 text-orange-700 font-semibold border border-orange-200">Shopee</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Grid display */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {filteredRecommendations.length > 0 ? (
                filteredRecommendations.map((prod) => (
                  <div key={prod.id} className="glass-panel rounded-xl overflow-hidden border border-emerald-200 hover:border-emerald-300 hover:shadow-xl transition duration-300 flex flex-col justify-between group relative bg-white">
                    
                    {/* Thumbnail representation */}
                    <div className="h-44 w-full bg-gray-100 flex items-center justify-center relative overflow-hidden">
                      {prod.thumbnail ? (
                        <img 
                          src={prod.thumbnail} 
                          alt={prod.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          onError={(e) => { e.target.style.display = 'none'; }} // Fallback on error
                        />
                      ) : (
                        <div className="text-gray-400 flex flex-col items-center gap-2">
                          <ShoppingBag className="w-10 h-10 opacity-30" />
                          <span className="text-[10px] font-mono">Hình ảnh sản phẩm</span>
                        </div>
                      )}
                      
                      {/* Platform label overlay */}
                      <span className={`absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-bold border shadow-lg ${
                        prod.platform === 'Lazada' 
                          ? 'bg-blue-600 text-white border-blue-500' 
                          : 'bg-orange-600 text-white border-orange-500'
                      }`}>
                        {prod.platform}
                      </span>
                      
                      {/* Discount Badge */}
                      {prod.discount_percent > 0 && (
                        <span className="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-red-500 text-white text-[10px] font-bold font-mono">
                          -{prod.discount_percent}%
                        </span>
                      )}
                    </div>
                    
                    {/* Product details */}
                    <div className="p-4 flex-grow flex flex-col justify-between gap-3">
                      <div>
                        {/* L2 Category */}
                        <span className="text-[10px] text-gray-500 font-semibold font-mono uppercase tracking-wider block mb-1">
                          {prod.category_l2}
                        </span>
                        
                        {/* Title */}
                        <h4 className="text-xs font-semibold text-gray-800 line-clamp-2 h-8 leading-relaxed mb-2" title={prod.name}>
                          {prod.name}
                        </h4>
                      </div>
                      
                      <div className="space-y-2">
                        {/* Price */}
                        <div className="flex items-baseline justify-between">
                          <span className="text-sm font-bold text-emerald-600 font-mono">{formatCurrency(prod.price)}</span>
                          <span className="text-[10px] text-gray-500">Xuất xứ: {prod.origin}</span>
                        </div>

                        {/* Sold and rating statistics */}
                        <div className="flex justify-between items-center bg-emerald-50 p-2 rounded-lg border border-emerald-200 text-[10px] text-gray-600">
                          <span className="flex items-center gap-1">
                            Lượng bán quy đổi: <strong className="text-gray-900 font-mono">{formatNumber(prod.sold)}</strong>
                          </span>
                          <span className="flex items-center gap-0.5 font-bold text-yellow-600">
                            {prod.rating} <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                          </span>
                        </div>
                        
                        {/* Original Store Link */}
                        <a 
                          href={prod.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full mt-2 py-1.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold font-mono text-[10px] uppercase tracking-wider flex items-center justify-center gap-1.5 border-0 transition shadow-md hover:shadow-lg"
                        >
                          Xem chi tiết gốc <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>

                    </div>

                  </div>
                ))
              ) : (
                <div className="col-span-full py-16 text-center text-gray-500 glass-panel rounded-2xl border border-emerald-200 bg-white">
                  <AlertCircle className="w-10 h-10 mx-auto text-gray-400 mb-2" />
                  Không tìm thấy sản phẩm tham khảo nào thỏa mãn các bộ lọc.
                </div>
              )}
            </div>

          </section>
        )}

      </main>

      {/* FOOTER & DISCLAIMER */}
      <footer className="max-w-7xl mx-auto px-6 mt-16 pt-8 border-t border-slate-900 text-slate-500 text-[10px] space-y-4">
        
        {/* Methodologies */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-900/10 p-5 rounded-2xl border border-slate-900">
          <div>
            <h5 className="font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center gap-1.5 text-xs mb-2">
              <Info className="w-3.5 h-3.5 text-orange-500" /> VỀ DỮ LIỆU ĐỐI THỦ (LAZADA, SHOPEE)
            </h5>
            <p className="leading-relaxed">
              Các cột lượng bán (<span className="text-slate-400">Sold Lazada+Shopee</span>) của đối thủ được suy luận bằng thuật toán dựa trên tỷ lệ quy đổi bán/review của ngành thời trang.
              Hệ số bán/review trung bình: <strong className="text-slate-400">5.24</strong> (1 review ≈ 5.24 lượt mua).
            </p>
          </div>
          <div>
            <h5 className="font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center gap-1.5 text-xs mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-orange-500" /> OPPORTUNITY SCORE (ASG2 Q1)
            </h5>
            <p className="leading-relaxed">
              <strong className="text-slate-400">Score = 0.4 × (RevSKU_norm) + 0.3 × SoldShare + 0.3 × (1 − OfficialDomRatio)</strong>.
              Điểm cao = doanh thu/SKU lớn, thị phần bán nhiều nhưng tỷ lệ thống trị của Official Store thấp.
              <br />Điểm ≥ 40 = <span className="text-orange-500 font-semibold">Cơ hội tốt</span> để regular seller gia nhập.
            </p>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-slate-600 font-mono text-[9px] pt-2">
          <span>Tiki Fashion DSS v1.0.0 © 2026. Phân tích nội bộ dành riêng cho Seller Thời Trang.</span>
          <span>Chú ý: Đây là số liệu ước tính hỗ trợ quyết định (DSS), không đại diện cho doanh số chính thức của các sàn TMĐT.</span>
        </div>

      </footer>
    </div>
  );
}
