import requests
import pandas as pd
import time
from datetime import datetime
import os

# ============================================================
# CẤU HÌNH HỆ THỐNG FILE
# ============================================================
FILE_HISTORICAL = "tiki_historical_data.xlsx"

MAX_PAGES   = 10        # Mỗi category lấy tối đa 10 trang
PAGE_SIZE   = 40
DELAY       = 1.2       # Giây chờ để tránh bị block

CATEGORIES = {
    "Thời trang nữ":         915,
    "Thời trang nam":        931,
    "Giày dép nữ":           1686,
    "Giày dép nam":          1685,
    "Túi xách & Ví":         27498,
    "Phụ kiện thời trang":   4246,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    "Referer": "https://tiki.vn/",
    "x-guest-token": "FsRqGxDTtfbxFBmMnHcDpVxJHmzHLRME",
}

# ============================================================
# HÀM CÀO DỮ LIỆU GỐC (RAW DATA)
# ============================================================
def fetch_products(category_id: int, page: int) -> dict:
    url = "https://tiki.vn/api/personalish/v1/blocks/listings"
    params = {
        "limit":        PAGE_SIZE,
        "page":         page,
        "category":     category_id,
        "sort":         "top_seller",
        "urlKey":       "thoi-trang-phu-kien",
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ⚠️ Lỗi request trang {page}: {e}")
        return {}

def flatten_raw_item(item: dict, category_name: str) -> dict:
    """
    Giữ nguyên toàn bộ cấu trúc dict gốc từ Postman.
    """
    raw_data = item.copy()
    
    record = {
        "Ngay": datetime.now().strftime("%Y-%m-%d"),
        "Gio": datetime.now().strftime("%H:%M:%S"),
        "danh_muc_cao": category_name
    }
    
    for key, value in raw_data.items():
        if isinstance(value, (dict, list)):
            record[key] = str(value)
        else:
            record[key] = value
            
    return record

# ============================================================
# TIẾN TRÌNH CHÍNH (MAIN)
# ============================================================
def main():
    all_records = []
    seen_ids    = set()
    
    print("🤖 Bắt đầu thu thập TOÀN BỘ dữ liệu gốc từ Tiki...")
    
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
                    all_records.append(flatten_raw_item(item, cat_name))
            
            paging = data.get("paging", {})
            total  = paging.get("total", 0)
            if page * PAGE_SIZE >= total:
                break
            time.sleep(DELAY)
            
    if not all_records:
        print("❌ Không lấy được dữ liệu raw nào!")
        return

    df_today = pd.DataFrame(all_records)
    print(f"✅ Đã đóng gói xong {len(df_today)} sản phẩm với đầy đủ trường dữ liệu gốc.")

    # --- TIẾN HÀNH GỘP LỊCH SỬ & GIỚI HẠN 5 NGÀY GẦN NHẤT ---
    if os.path.exists(FILE_HISTORICAL):
        try:
            df_historical = pd.read_excel(FILE_HISTORICAL)
            df_tong = pd.concat([df_historical, df_today], ignore_index=True)
        except Exception as e:
            print(f"⚠️ Không đọc được file lịch sử cũ, tiến hành tạo mới. Chi tiết: {e}")
            df_tong = df_today
    else:
        df_tong = df_today

    # SỬA LỖI: Chuyển đổi cột Ngay sang định dạng DateTime, loại bỏ dòng lỗi/rỗng
    df_tong["Ngay"] = pd.to_datetime(df_tong["Ngay"], errors="coerce")
    df_tong = df_tong.dropna(subset=["Ngay"])
    
    # Đồng bộ về chuỗi ký tự dạng YYYY-MM-DD an toàn để so sánh
    df_tong["Ngay"] = df_tong["Ngay"].dt.strftime('%Y-%m-%d')
    
    # Xóa sản phẩm trùng lặp trong cùng một ngày cào dữ liệu
    df_tong = df_tong.drop_duplicates(subset=["Ngay", "id"]).reset_index(drop=True)
    
    # Lấy danh sách 5 ngày gần đây nhất (Lúc này chắc chắn toàn bộ là chuỗi chữ)
    danh_sach_ngay = sorted(df_tong["Ngay"].unique(), reverse=True)
    top_5_ngay = danh_sach_ngay[:5]
    df_cuoi_cung = df_tong[df_tong["Ngay"].isin(top_5_ngay)]
    
    # Xuất dữ liệu lưu đè lại
    df_cuoi_cung.to_excel(FILE_HISTORICAL, index=False)
    print(f"💾 Đã ghi đè file '{FILE_HISTORICAL}' thành công! (Dữ liệu lưu giữ của các ngày: {top_5_ngay})")


if __name__ == "__main__":
    main()
