# 🎯 Tiki Fashion Decision Support System (DSS)

**Hệ thống phân tích khoảng trống sản phẩm thời trang** - So sánh Tiki với Shopee & Lazada

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.x-green)
![React](https://img.shields.io/badge/react-18-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## 📋 Tổng quan

**DSS Visual** là hệ thống hỗ trợ quyết định (Decision Support System) cho Seller thời trang trên Tiki. Hệ thống phân tích:
- ✅ **Top sản phẩm Tiki bán chạy** - Giúp seller chọn sản phẩm tiềm năng
- ✅ **Gap Analysis** - So sánh khoảng trống với đối thủ (Lazada, Shopee)
- ✅ **Predictive Forecasting** - Dự báo xu hướng 30 ngày
- ✅ **What-If Scenarios** - Mô phỏng kịch bản kinh doanh
- ✅ **Real-time Dashboard** - Giao diện trực quan, filter toàn cục

---

## 🚀 Tính năng chính

### 1. **Top Tiki Products** 🔥
- Hiển thị TOP sản phẩm Tiki theo 3 metrics:
  - 📈 **Bán chạy nhất** (sold_count)
  - 💰 **Doanh thu cao** (revenue)
  - ⭐ **Đánh giá tốt** (rating + reviews)
- Badge: 🔥 HOT, 💰 HIGH REVENUE, ⭐ BEST RATED
- Filter global: Category, Price, Rating, Search

### 2. **Gap Analysis**
- So sánh Tiki vs Competitor theo category
- Priority Score (0-100): SKU availability + Price + Rating
- Revenue potential estimation
- 10/41 categories có competitor data

### 3. **Predictive Forecast**
- Linear Regression time series
- 30-day forecast với confidence intervals
- Top 5 categories
- Historical vs Predicted charts

### 4. **What-If Scenarios**
- 4 kịch bản:
  - S1: Tăng 20% SKU
  - S2: Focus top gaps
  - S3: Pricing strategy
  - S4: Combined approach
- ROI analysis & recommendations

### 5. **Raw Data Tables**
- ✅ Data Tiki (1,925 products)
- ✅ Data Lazada (1,000 products)
- ✅ Data Shopee (98 products)
- Pagination, search, filter

---

## 🛠️ Tech Stack

### Backend
- **Python 3.x**
- **Flask** - REST API
- **SQLAlchemy** - ORM
- **pandas** - Data processing
- **scikit-learn** - Machine Learning
- **SQLite** - Database (dev)

### Frontend
- **React 18**
- **Vite** - Build tool
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Data Pipeline
- **GitHub API** - Auto-fetch Tiki data
- **NLP Classification** - 2-level category taxonomy
- **ETL** - pandas + SQLAlchemy

---

## 📦 Installation

### Prerequisites
```bash
- Python 3.8+
- Node.js 16+
- npm or yarn
```

### 1. Clone repository
```bash
git clone <your-repo-url>
cd "DSS Visual"
```


### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your GitHub credentials (optional)

# Initialize database
python database/schema.py

# Ingest data
python ingest.py
```

### 3. Frontend Setup

```bash
# Install dependencies
npm install

# Setup environment
cp .env.frontend .env
# Edit if needed
```

### 4. Run Application

**Option 1: Manual (2 terminals)**
```bash
# Terminal 1 - Backend
python api/app.py

# Terminal 2 - Frontend
npm run dev
```

**Option 2: Batch file (Windows)**
```bash
RUN_DSS.bat
```

Access: `http://localhost:5173`

---

## 📊 Database Schema

```sql
1. products_tiki (1,925 records)
   - Current Tiki products snapshot
   
2. products_tiki_history (9,626 records)
   - Historical snapshots for time series

3. products_changes (variable)
   - Week-over-week changes detection

4. products_external (1,098 records)
   - Lazada (1,000) + Shopee (98)

5. ingest_log
   - Data ingestion tracking
```

---

## 🎯 Usage Guide

### For Sellers

1. **Mở tab "Top Tiki Products"**
   - Chọn metric: Bán chạy / Doanh thu / Rating
   - Filter theo category, giá, rating
   - Xem sản phẩm có badge HOT 🔥

2. **So sánh với đối thủ** (Optional)
   - Tab "Gap Analysis": Category nào có cơ hội
   - Tab "So sánh Competitor": Sản phẩm external

3. **Dự báo xu hướng**
   - Tab "Predictive Forecast": 30-day forecast
   - Tab "What-If": Mô phỏng kịch bản

### For Analysts

1. **Raw Data**
   - Tabs "Data Tiki/Lazada/Shopee"
   - Export data cho analysis ngoài

2. **API Endpoints**
   - `/api/dashboard/all` - Full dashboard data
   - `/api/products/tiki/top` - Top Tiki products
   - `/api/products/tiki` - Tiki products with pagination
   - `/api/products/external` - External products
   - `/api/forecast` - Predictive forecasts
   - `/api/whatif` - Scenario analysis

---

## 📈 Analytics Models

### 1. Gap Analysis
```python
Priority Score = SKU Availability (40%) + 
                 Price Competitiveness (40%) + 
                 Rating Quality (20%)
```

### 2. Predictive Model
- **Algorithm**: Linear Regression
- **Input**: Historical time series (5 days)
- **Output**: 30-day forecast + confidence intervals
- **Limitations**: Assumes linear trend, no external factors

### 3. What-If Scenarios
- **S1**: SKU expansion (linear scaling)
- **S2**: Gap filling (50% rate assumption)
- **S3**: Pricing (elasticity = 1.5)
- **S4**: Combined (sequential application)

---

## 🔄 Data Pipeline

```
GitHub (Auto-fetch daily)
    ↓
data_fetcher/github_fetcher.py
    ↓
data_fetcher/data_processor.py (ETL)
    ↓
database/schema.py (SQLite)
    ↓
api/dashboard_generator.py (Analytics)
    ↓
api/app.py (REST API)
    ↓
React Dashboard (UI)
```

---

## 📁 Project Structure

```
DSS Visual/
├── analytics/
│   ├── predictive_model.py      # Forecasting
│   └── whatif_scenarios.py      # Scenario analysis
├── api/
│   ├── app.py                   # Flask API
│   └── dashboard_generator.py   # Data aggregation
├── database/
│   └── schema.py                # Database models
├── data_fetcher/
│   ├── github_fetcher.py        # Auto-fetch
│   └── data_processor.py        # ETL
├── src/                         # React frontend
│   ├── App.jsx                  # Main dashboard
│   ├── TopTikiProducts.jsx      # Top products tab
│   ├── ForecastTab.jsx          # Forecast view
│   ├── WhatIfTab.jsx            # Scenarios view
│   └── ProductDataTab.jsx       # Raw data tables
├── .env                         # Environment config
├── requirements.txt             # Python deps
├── package.json                 # Node deps
├── ASG2.md                      # Assignment 2 report
└── README.md                    # This file
```

---

## 📝 Assignment Deliverables

This project fulfills **Assignment 2 - Analytics & Model-Based DSS**:

✅ **Step 1 - EDA**: 10 gap categories identified  
✅ **Step 2 - Diagnostic Analytics**: 3 hypotheses tested  
✅ **Step 3 - Predictive Analytics**: Linear Regression models  
✅ **Step 4 - What-If Analysis**: 4 scenarios evaluated  
✅ **Step 5 - Recommendations**: 3-phase execution plan  

See **[ASG2.md](ASG2.md)** for full report (38KB, 700+ lines).

---

## 🚀 Deployment

### Development
- Backend: `http://127.0.0.1:5000`
- Frontend: `http://localhost:5173`

### Production (TODO)
- Docker containers
- PostgreSQL database
- Nginx reverse proxy
- Daily cron job for data refresh

---

## 🤝 Contributing

This is an academic project for DSS course. Contributions welcome!

1. Fork the repo
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Authors

**DSS Visual Analytics Team**  
Course: Decision Support Systems  
Date: July 2026

---

## 📞 Support

For issues or questions:
- 📧 Email: [your-email]
- 🐛 Issues: [GitHub Issues]
- 📖 Docs: [ASG2.md](ASG2.md)

---

## 🙏 Acknowledgments

- **Tiki.vn** - Data source
- **Lazada & Shopee** - Competitor data
- **scikit-learn** - ML library
- **React & Recharts** - Visualization
- Course instructors & TAs

---

**⭐ Star this repo if you find it useful!**

---

*Built with ❤️ for Decision Support Systems course*
