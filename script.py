import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import ast

# ============================================================
# CẤU HÌNH HỆ THỐNG FILE
# ============================================================
FILE_RAW        = "tiki_raw_data.xlsx"
FILE_CLEAN      = "tiki_clean_data.xlsx"
FILE_HISTORICAL = "tiki_historical_data.xlsx"

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

# Bảng ánh xạ hỗ trợ phân loại Danh mục cấp 2 dựa trên ID danh mục của Tiki
CATEGORY_L2_MAP = {
    917: "Áo nữ", 921: "Đầm nữ", 929: "Quần nữ", 933: "Áo khoác nữ", 930: "Chân váy",
    932: "Áo nam", 934: "Quần nam", 938: "Áo khoác nam", 5351: "Đồ lót nam",
    1688: "Giày cao gót", 1694: "Giày sandals nữ", 6010: "Giày thể thao nữ",
    1691: "Giày tây nam", 1693: "Giày lười nam", 6012: "Giày thể thao nam",
    7529: "Túi xách nữ", 7533: "Ví nữ", 7531: "Balo nam/nữ", 7535: "Ví nam",
    4247: "Mắt kính", 4250: "Trang sức", 8479: "Đồng hồ"
}

# ============================================================
# TIẾN TRÌNH XỬ LÝ CHÍNH
# ============================================================
def main():
    time_vn = datetime.utcnow() + timedelta(hours=7)
    ngay_hom_nay = time_vn.strftime("%Y-%m-%d")
    gio_hom_nay  = "07:00:00" 
    
    raw_records = []
    seen_ids = set()
    
    print(f"🤖 Bắt đầu thu thập dữ liệu (Múi giờ VN: {ngay_hom_nay} {time_vn.strftime('%H:%M:%S')})...")
    
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
        print("❌ Không thu được dữ liệu mới từ API.")
        return

    # --------------------------------------------------------
    # BƯỚC 1: GHI ĐÈ FILE RAW DATA
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
    print(f"💾 1. Đã cập nhật ghi đè file thô gốc '{FILE_RAW}'.")

    # --------------------------------------------------------
    # BƯỚC 2: CHUYỂN DỮ LIỆU CŨ TRONG CLEAN SANG FILE HISTORY
    # --------------------------------------------------------
    df_clean_old = pd.DataFrame()
    if os.path.exists(FILE_CLEAN):
        try:
            df_clean_old = pd.read_excel(FILE_CLEAN)
            print("📦 Đang chuyển dữ liệu sạch của ngày hôm trước vào kho lịch sử...")
        except Exception:
            pass

    if not df_clean_old.empty:
        df_history_old = pd.DataFrame()
        if os.path.exists(FILE_HISTORICAL):
            try:
                df_history_old = pd.read_excel(FILE_HISTORICAL)
            except Exception:
                pass
                
        df_history_combined = pd.concat([df_history_old, df_clean_old], ignore_index=True)
        
        df_history_combined["date_collected"] = pd.to_datetime(df_history_combined["date_collected"], errors="coerce")
        df_history_combined = df_history_combined.dropna(subset=["date_collected"])
        df_history_combined["date_collected"] = df_history_combined["date_collected"].dt.strftime('%Y-%m-%d')
        df_history_combined = df_history_combined.drop_duplicates(subset=["date_collected", "product_id"]).reset_index(drop=True)
        
        unique_days = sorted(df_history_combined["date_collected"].unique(), reverse=True)
        top_5_days  = unique_days[:5]
        df_history_final = df_history_combined[df_history_combined["date_collected"].isin(top_5_days)]
        
        df_history_final.to_excel(FILE_HISTORICAL, index=False)
        print(f"💾 2. Đã đồng bộ dữ liệu vào file lịch sử '{FILE_HISTORICAL}' (Lưu trữ các ngày: {top_5_days})")

    # --------------------------------------------------------
    # BƯỚC 3: XỬ LÝ LÀM SẠCH VÀ GHI ĐÈ FILE CLEAN DATA
    # --------------------------------------------------------
    clean_records = []
    for item in raw_records:
        price = item.get("price", 0)
        original_price = item.get("original_price", price)
        discount_amount = original_price - price # Sửa lại logic: Giá gốc - Giá hiện tại = Số tiền được giảm
        
        # Bóc tách số lượng đã bán an toàn
        sold_count = item.get("order_count", 0)
        if item.get("quantity_sold_value"):
            try:
                sold_count = int(item.get("quantity_sold_value"))
            except:
                pass
        else:
            q_sold = item.get("quantity_sold")
            if isinstance(q_sold, dict):
                sold_count = q_sold.get("value", 0)
        
        estimated_revenue = price * sold_count
        
        # Phân loại cây danh mục từ primary_category_path
        cat_path = item.get("primary_category_path", "")
        cat_ids = [int(x) for x in cat_path.split("/") if x.isdigit()] if isinstance(cat_path, str) else []
        
        category_l2 = "Khác"
        for cid in cat_ids:
            if cid in CATEGORY_L2_MAP:
                category_l2 = CATEGORY_L2_MAP[cid]
                break
                
        # Phân tích Badges
        badges_list = safe_eval_list(item.get("badges_new")) + safe_eval_list(item.get("badges_v3"))
        badge_codes = [b.get("code") for b in badges_list if isinstance(b, dict) and b.get("code")]
        
        is_official = "official_store" in badge_codes or item.get("inventory_status") == "available" and "rẻ hơn hoàn tiền" in str(badges_list).lower()
        tiki_verified = "tiki_verified" in badge_codes or "chính hãng" in str(badges_list).lower()
        is_tiki_now = "tikinow" in badge_codes
        is_freeship = "freeship_xtra" in badge_codes or "freeship" in str(badges_list).lower()
        is_top_brand = "top_brand" in badge_codes
        
        clean_rec = {
            "product_id":             item.get("id"),
            "product_name":           item.get("name"),
            "brand_name":             item.get("brand_name", "OEM"),
            "category_l1":            item.get("category_main"),
            "category_l2":            category_l2,
            "category_l3":            category_l2,  # Dự phòng cấu trúc cột của bạn
            "primary_category":       item.get("category_main"),
            "price":                  price,
            "original_price":         original_price,
            "discount_amount":        discount_amount,
            "discount_percent":       item.get("discount_rate", 0),
            "rating":                 item.get("rating_average", 0),
            "review_count":           item.get("review_count", 0),
            "sold_count":             sold_count,
            "favourite_count":        item.get("favourite_count", 0),
            "estimated_revenue":      estimated_revenue,
            "seller_id":              item.get("seller_id", 0),
            "seller_type":            "OFFICIAL_STORE" if is_official else "NONE",
            "is_official_store":      is_official,
            "tiki_verified":          tiki_verified,
            "is_tiki_now":            is_tiki_now,
            "is_freeship":            is_freeship,
            "delivery_estimate_days": 1 if is_tiki_now else 3,
            "order_route":            "same_province",
            "origin":                 "Việt Nam",
            "is_imported":            False,
            "is_authentic":           True,
            "is_top_brand":           is_top_brand,
            "date_collected":         item.get("date_collected"),
            "time_collected":         item.get("time_collected")
        }
        clean_records.append(clean_rec)
        
    df_clean_today = pd.DataFrame(clean_records)
    df_clean_today.to_excel(FILE_CLEAN, index=False)
    print(f"🎯 3. Đã tính toán làm sạch và cập nhật file thành công vào '{FILE_CLEAN}'!")

if __name__ == "__main__":
    main()
