import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import ast

# ============================================================
# CẤU HÌNH HỆ THỐNG FILE (3 TẦNG CHUẨN ĐÚNG MẪU)
# ============================================================
FILE_RAW        = "tiki_raw_data.xlsx"         # Ghi đè dữ liệu thô hôm nay
FILE_CLEAN      = "tiki_clean_data.xlsx"       # Ghi đè dữ liệu sạch hôm nay
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

# Định nghĩa chuẩn xác danh sách 30 cột cần có cho file Clean và History
REQUIRED_COLUMNS = [
    "product_id", "product_name", "brand_name", "category_l1", "category_l2",
    "category_l3", "primary_category", "price", "original_price", "discount_amount",
    "discount_percent", "rating", "review_count", "sold_count", "favourite_count",
    "estimated_revenue", "seller_id", "seller_type", "is_official_store", "tiki_verified",
    "is_tiki_now", "is_freeship", "delivery_estimate_days", "order_route", "origin",
    "is_imported", "is_authentic", "is_top_brand", "date_collected", "time_collected"
]

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
    if val is None:
        return []
    try:
        if pd.isna(val):
            return []
    except (TypeError, ValueError):
        pass
    if isinstance(val, list):
        return val
    try:
        return ast.literal_eval(str(val))
    except:
        return []

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
    gio_hom_nay  = time_vn.strftime("%H:%M:%S") 
    
    raw_records = []
    seen_ids = set()
    
    print(f"🤖 Khởi chạy hệ thống pipeline dữ liệu (Giờ VN: {ngay_hom_nay} {time_vn.strftime('%H:%M:%S')})...")
    
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
        print("❌ Không lấy được dữ liệu thô mới từ API!")
        return

    # --------------------------------------------------------
    # BƯỚC 1: GHI ĐÈ FILE RAW DATA (Bảo toàn dữ liệu thô gốc)
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
    print(f"💾 1. Đã cập nhật ghi đè file thô gốc '{FILE_RAW}' thành công.")

    # --------------------------------------------------------
    # BƯỚC 2: TÍNH TOÁN LÀM SẠCH DỮ LIỆU CỦA NGÀY HÔM NAY (CLEAN DATA)
    # --------------------------------------------------------
    clean_records = []
    for item in raw_records:
        price = item.get("price", 0)
        original_price = item.get("original_price", price)
        discount_amount = original_price - price if original_price > price else 0
        
        sold_count = 0
        if item.get("quantity_sold_value") is not None:
            try:
                sold_count = int(item.get("quantity_sold_value"))
            except:
                pass
        else:
            q_sold = item.get("quantity_sold")
            if isinstance(q_sold, dict):
                sold_count = q_sold.get("value", 0)
            elif isinstance(q_sold, str) and "value" in q_sold:
                try:
                    sold_count = ast.literal_eval(q_sold).get("value", 0)
                except:
                    sold_count = item.get("order_count", 0)
            else:
                sold_count = item.get("order_count", 0)
        
        estimated_revenue = price * sold_count
        
        cat_path = item.get("primary_category_path", "")
        cat_ids = [int(x) for x in cat_path.split("/") if x.isdigit()] if isinstance(cat_path, str) else []
        
        category_l2 = "Khác"
        for cid in cat_ids:
            if cid in CATEGORY_L2_MAP:
                category_l2 = CATEGORY_L2_MAP[cid]
                break
                
        badges_list = safe_eval_list(item.get("badges_new")) + safe_eval_list(item.get("badges_v3"))
        badge_codes = [b.get("code") for b in badges_list if isinstance(b, dict) and b.get("code")]
        
        is_official = "official_store" in badge_codes or item.get("inventory_status") == "available" and "rẻ hơn hoàn tiền" in str(badges_list).lower()
        tiki_verified = "tiki_verified" in badge_codes or "chính hãng" in str(badges_list).lower()
        is_tiki_now = "tikinow" in badge_codes
        is_freeship = "freeship_xtra" in badge_codes or "freeship" in str(badges_list).lower()
        is_top_brand = "top_brand" in badge_codes
        
        # Tạo dữ liệu bằng DataFrame từ đầu để loại trừ tuyệt đối lỗi lệch chiều dài mảng
        clean_rec = {col: None for col in REQUIRED_COLUMNS}
        clean_rec["product_id"]             = item.get("id")
        clean_rec["product_name"]           = item.get("name", "")
        clean_rec["brand_name"]             = item.get("brand_name", "OEM")
        clean_rec["category_l1"]            = item.get("category_main")
        clean_rec["category_l2"]            = category_l2
        clean_rec["category_l3"]            = category_l2
        clean_rec["primary_category"]       = item.get("category_main")
        clean_rec["price"]                  = price
        clean_rec["original_price"]         = original_price
        clean_rec["discount_amount"]        = discount_amount
        clean_rec["discount_percent"]       = item.get("discount_rate", 0)
        clean_rec["rating"]                 = item.get("rating_average", 0)
        clean_rec["review_count"]           = item.get("review_count", 0)
        clean_rec["sold_count"]             = sold_count
        clean_rec["favourite_count"]        = item.get("favourite_count", 0)
        clean_rec["estimated_revenue"]      = estimated_revenue
        clean_rec["seller_id"]              = item.get("seller_id", 0)
        clean_rec["seller_type"]            = "OFFICIAL_STORE" if is_official else "NONE"
        clean_rec["is_official_store"]      = bool(is_official)
        clean_rec["tiki_verified"]          = bool(tiki_verified)
        clean_rec["is_tiki_now"]            = bool(is_tiki_now)
        clean_rec["is_freeship"]            = bool(is_freeship)
        clean_rec["delivery_estimate_days"] = 1 if is_tiki_now else 3
        clean_rec["order_route"]            = "same_province"
        clean_rec["origin"]                 = "Việt Nam"
        clean_rec["is_imported"]            = False
        clean_rec["is_authentic"]           = True
        clean_rec["is_top_brand"]           = bool(is_top_brand)
        clean_rec["date_collected"]         = str(ngay_hom_nay)
        clean_rec["time_collected"]         = str(gio_hom_nay)
        
        clean_records.append(clean_rec)
        
    df_clean_today = pd.DataFrame(clean_records, columns=REQUIRED_COLUMNS)

    # --------------------------------------------------------
    # BƯỚC 3: KIỂM TRA VÀ GỘP LỊCH SỬ AN TOÀN
    # --------------------------------------------------------
    df_clean_old = pd.DataFrame()
    if os.path.exists(FILE_CLEAN):
        try:
            df_tmp = pd.read_excel(FILE_CLEAN)
            # Khóa chống lỗi cấu trúc: Chỉ lấy nếu file cũ có đủ số lượng cột chuẩn
            if len(df_tmp.columns) == len(REQUIRED_COLUMNS):
                df_clean_old = df_tmp
                print("📦 Đang tiến hành chuyển dữ liệu sạch ngày cũ vào kho lịch sử...")
            else:
                print("⚠️ Phát hiện file Clean cũ bị lệch cột, bỏ qua gộp để tránh sập hệ thống.")
        except Exception:
            pass

    if not df_clean_old.empty:
        df_history_old = pd.DataFrame()
        if os.path.exists(FILE_HISTORICAL):
            try:
                df_tmp_hist = pd.read_excel(FILE_HISTORICAL)
                if len(df_tmp_hist.columns) == len(REQUIRED_COLUMNS):
                    df_history_old = df_tmp_hist
            except Exception:
                pass
                
        # Đồng bộ gộp dữ liệu lịch sử
        df_history_combined = pd.concat([df_history_old, df_clean_old], ignore_index=True)
        
        # Ép định dạng ngày tháng và xóa trùng lặp
        df_history_combined["date_collected"] = pd.to_datetime(df_history_combined["date_collected"], errors="coerce")
        df_history_combined = df_history_combined.dropna(subset=["date_collected"])
        df_history_combined["date_collected"] = df_history_combined["date_collected"].dt.strftime('%Y-%m-%d')
        
        if "product_id" in df_history_combined.columns:
            df_history_combined = df_history_combined.drop_duplicates(subset=["date_collected", "product_id"]).reset_index(drop=True)
        
        # Giới hạn giữ tối đa 5 ngày gần nhất
        unique_days = sorted(df_history_combined["date_collected"].unique(), reverse=True)
        top_5_days  = unique_days[:5]
        df_history_final = df_history_combined[df_history_combined["date_collected"].isin(top_5_days)]
        
        df_history_final.to_excel(FILE_HISTORICAL, index=False)
        print(f"💾 2. Kho lịch sử '{FILE_HISTORICAL}' đã cập nhật an toàn. (Lưu giữ: {top_5_days})")

    # --------------------------------------------------------
    # BƯỚC 4: GHI ĐÈ FILE CLEAN DATA MỚI NHẤT HÔM NAY (Đúng 30 cột)
    # --------------------------------------------------------
    df_clean_today.to_excel(FILE_CLEAN, index=False)
    print(f"🎯 3. Đã làm sạch và cập nhật thành công dữ liệu mới vào file sạch '{FILE_CLEAN}'!")


if __name__ == "__main__":
    main()
