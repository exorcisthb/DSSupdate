import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import ast

# ============================================================
# CẤU HÌNH HỆ THỐNG FILE (3 TẦNG ĐÚNG YÊU CẦU)
# ============================================================
FILE_RAW        = "tiki_raw_data.xlsx"         # Ghi đè dữ liệu thô hôm nay
FILE_CLEAN      = "tiki_clean_data.xlsx"       # Ghi đè dữ liệu làm sạch hôm nay
FILE_HISTORICAL = "tiki_historical_data.xlsx"  # Gom dữ liệu sạch cũ (Tối đa 5 ngày)

MAX_PAGES   = 10
PAGE_SIZE   = 40
DELAY       = 1.2

CATEGORIES = {
    "Thời trang nữ":         915,
    "Thời trang nam":        931,
    "Giày dép nữ":           1686,
    "Giày dép nam":          1685,
    "Túi xách & Ví":         27498,
    "Phụ kiện thời trang":   4246,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    "Referer": "https://tiki.vn/",
}

def fetch_products(category_id: int, page: int) -> dict:
    url = "https://tiki.vn/api/personalish/v1/blocks/listings"
    params = {
        "limit": PAGE_SIZE,
        "page": page,
        "category": category_id,
        "sort": "top_seller",
        "urlKey": "thoi-trang-phu-kien",
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ⚠️ Lỗi request trang {page}: {e}")
        return {}

def safe_eval_list(val):
    if not val or pd.isna(val):
        return []
    if isinstance(val, list):
        return val
    try:
        return ast.literal_eval(str(val))
    except:
        return []

# ============================================================
# TIẾN TRÌNH XỬ LÝ CHÍNH
# ============================================================
def main():
    # Khởi tạo thời gian chuẩn múi giờ Việt Nam (ICT = UTC + 7)
    time_vn = datetime.utcnow() + timedelta(hours=7)
    ngay_hom_nay = time_vn.strftime("%Y-%m-%d")
    gio_hom_nay  = "07:00:00" # Đồng bộ mốc cố định giống file mẫu của bạn
    
    raw_records = []
    seen_ids = set()
    
    print(f"🤖 Bắt đầu cào dữ liệu (Giờ VN: {ngay_hom_nay} {time_vn.strftime('%H:%M:%S')})...")
    
    for cat_name, cat_id in CATEGORIES.items():
        print(f"-> Đang quét ngành hàng: {cat_name}")
        for page in range(1, MAX_PAGES + 1):
            data = fetch_products(cat_id, page)
            if not data:
                break
            items = data.get("data", [])
            if not items:
                break
                
            for item in items:
                pid = item.get("id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    
                    item_raw = item.copy()
                    item_raw["category_main"] = cat_name
                    item_raw["date_collected"] = ngay_hom_nay
                    item_raw["time_collected"] = gio_hom_nay
                    raw_records.append(item_raw)
            
            paging = data.get("paging", {})
            if page * PAGE_SIZE >= paging.get("total", 0):
                break
            time.sleep(DELAY)
            
    if not raw_records:
        print("❌ Không lấy được dữ liệu mới từ API!")
        return

    # --------------------------------------------------------
    # BƯỚC 1: GHI ĐÈ FILE RAW DATA (Đầy đủ tất cả các cột gốc)
    # --------------------------------------------------------
    processed_raw = []
    for item in raw_records:
        rec = {}
        for k, v in item.items():
            if isinstance(v, (dict, list)):
                rec[k] = str(v)
            else:
                rec[k] = v
        processed_raw.append(rec)
        
    df_raw_today = pd.DataFrame(processed_raw)
    df_raw_today.to_excel(FILE_RAW, index=False)
    print(f"💾 1. Đã ghi đè thành công file thô '{FILE_RAW}'.")

    # --------------------------------------------------------
    # BƯỚC 2: CHUYỂN DỮ LIỆU CŨ TRONG CLEAN SANG FILE HISTORY
    # --------------------------------------------------------
    df_clean_old = pd.DataFrame()
    if os.path.exists(FILE_CLEAN):
        try:
            df_clean_old = pd.read_excel(FILE_CLEAN)
            print("📦 Tìm thấy dữ liệu cũ trong file Clean, tiến hành chuyển sang History...")
        except Exception:
            pass

    if not df_clean_old.empty:
        df_history_old = pd.DataFrame()
        if os.path.exists(FILE_HISTORICAL):
            try:
                df_history_old = pd.read_excel(FILE_HISTORICAL)
            except Exception:
                pass
                
        # Gộp dữ liệu sạch cũ lại với nhau
        df_history_combined = pd.concat([df_history_old, df_clean_old], ignore_index=True)
        
        # Làm sạch định dạng ngày tháng và loại bỏ trùng lặp sản phẩm trong cùng một ngày
        df_history_combined["date_collected"] = pd.to_datetime(df_history_combined["date_collected"], errors="coerce")
        df_history_combined = df_history_combined.dropna(subset=
