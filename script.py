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
    Chuyển đổi các danh sách hoặc dict phức tạp (như badges_new, visible_impression_info) 
    thành chuỗi text/json để lưu trữ an toàn vào Excel mà không bị mất dữ liệu.
    """
    # Tạo một bản sao để tránh ghi đè trực tiếp lên dữ liệu gốc
    raw_data = item.copy()
    
    # Thêm các trường phân loại và thời gian cào dữ liệu vào đầu bản ghi
    record = {
        "Ngay": datetime.now().strftime("%Y-%m-%d"),
        "Gio": datetime.now().strftime("%H:%M:%S"),
        "danh_muc_cao": category_name
    }
    
    # Duyệt và ép kiểu chuỗi đối với các trường phức tạp để Excel không bị lỗi cấu trúc
    for key, value in raw_data.items():
        if isinstance(value, (dict, list)):
            record[key] = str(value)  # Lưu trữ trọn vẹn dưới dạng text JSON
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
                    # Thu thập toàn bộ các trường JSON chuẩn Postman
                    all_records.append(flatten_raw_item(item, cat_name))
            
            paging = data.get("paging", {})
            total  = paging.get("total", 0)
            if page * PAGE_SIZE >= total:
                break
            time.sleep(DELAY)
            
    if not all_records:
        print("❌ Không lấy được dữ liệu raw nào!")
        return

    # Chuyển đổi dữ liệu ngày hôm nay thành DataFrame
    df_today = pd.DataFrame(all_records)
    print(f"✅ Đã đóng gói xong {len(df_today)} sản phẩm với đầy đủ trường dữ liệu gốc.")

    # --- TIẾN HÀNH GỘP LỊCH SỬ & GIỚI HẠN 5 NGÀY GẦN NHẤT ---
    if os.path.exists(FILE_HISTORICAL):
        try:
            df_historical = pd.read_excel(FILE_HISTORICAL)
            # Gộp dữ liệu cũ và mới lại với nhau
            df_tong = pd.concat([df_historical, df_today], ignore_index=True)
            # Xóa trùng lặp sản phẩm trùng nhau trong cùng một ngày cào dữ liệu
            df_tong = df_tong.drop_duplicates(subset=["Ngay", "id"]).reset_index(drop=True)
        except Exception as e:
            print(f"⚠️ Không đọc được file lịch sử cũ (có thể do đổi cấu trúc cột), tiến hành tạo mới. Chi tiết: {e}")
            df_tong = df_today
    else:
        df_tong = df_today

    # Đồng bộ lại định dạng chuỗi ngày tháng YYYY-MM-DD
    df_tong["Ngay"] = pd.to_datetime(df_tong["Ngay"]).dt.strftime('%Y-%m-%d')
    
    # Lọc lấy danh sách 5 ngày gần đây nhất
    danh_sach_ngay = sorted(df_tong["Ngay"].unique(), reverse=True)
    top_5_ngay = danh_sach_ngay[:5]
    df_cuoi_cung = df_tong[df_tong["Ngay"].isin(top_5_ngay)]
    
    # Xuất dữ liệu lưu lại trực tiếp lên GitHub
    df_cuoi_cung.to_excel(FILE_HISTORICAL, index=False)
    print(f"💾 Đã ghi đè file '{FILE_HISTORICAL}' thành công! (Dữ liệu lưu giữ của các ngày: {top_5_ngay})")


if __name__ == "__main__":
    main()
