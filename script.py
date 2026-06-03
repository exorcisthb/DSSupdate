import requests
import pandas as pd
import time
import ast
import os
from datetime import datetime, timedelta

# ============================================================
# CẤU HÌNH
# ============================================================
FILE_RAW        = "tiki_raw_data.xlsx"
FILE_CLEAN      = "tiki_clean_data.xlsx"
FILE_HISTORICAL = "tiki_historical_data.xlsx"
FILE_CHANGES    = "tiki_changes_report.xlsx"

MAX_PAGES = 10
PAGE_SIZE = 40
DELAY     = 1.2

CATEGORIES = {
    "Thời trang nữ":       915,
    "Thời trang nam":      931,
    "Giày dép nữ":         1686,
    "Giày dép nam":        1685,
    "Túi xách & Ví":       27498,
    "Phụ kiện thời trang": 4246,
}

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    "Referer":         "https://tiki.vn/",
}

REQUIRED_COLUMNS = [
    "product_id", "product_name", "product_link", "brand_name",
    "category_l1", "category_l2", "category_l3", "primary_category",
    "price", "original_price", "discount_amount", "discount_percent",
    "rating", "review_count", "sold_count", "favourite_count",
    "estimated_revenue", "seller_id", "seller_type", "is_official_store",
    "tiki_verified", "is_tiki_now", "is_freeship", "delivery_estimate_days",
    "order_route", "origin", "is_imported", "is_authentic", "is_top_brand",
    "date_collected", "time_collected"
]

CATEGORY_L2_MAP = {
    917: "Áo nữ", 921: "Đầm nữ", 929: "Quần nữ", 933: "Áo khoác nữ", 930: "Chân váy",
    932: "Áo nam", 934: "Quần nam", 938: "Áo khoác nam", 5351: "Đồ lót nam",
    1688: "Giày cao gót", 1694: "Giày sandals nữ", 6010: "Giày thể thao nữ",
    1691: "Giày tây nam", 1693: "Giày lười nam", 6012: "Giày thể thao nam",
    7529: "Túi xách nữ", 7533: "Ví nữ", 7531: "Balo nam/nữ", 7535: "Ví nam",
    4247: "Mắt kính", 4250: "Trang sức", 8479: "Đồng hồ"
}

# ============================================================
# HÀM TIỆN ÍCH
# ============================================================
def fetch_products(category_id: int, page: int) -> dict:
    url = "https://tiki.vn/api/personalish/v1/blocks/listings"
    params = {
        "limit": PAGE_SIZE, "page": page,
        "category": category_id, "sort": "top_seller",
        "urlKey": "thoi-trang-phu-kien",
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ⚠️ Lỗi request trang {page}: {e}")
        return {}

def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default

def get_sold_count(item):
    if item.get("quantity_sold_value") is not None:
        return safe_int(item.get("quantity_sold_value"))
    q_sold = item.get("quantity_sold")
    if isinstance(q_sold, dict):
        return q_sold.get("value", 0)
    if isinstance(q_sold, str) and "value" in q_sold:
        try:
            return ast.literal_eval(q_sold).get("value", 0)
        except:
            pass
    return safe_int(item.get("order_count", 0))

def load_clean_file_if_yesterday(ngay_hom_nay: str) -> pd.DataFrame:
    """Đọc file clean CŨ - chỉ dùng nếu dữ liệu là của ngày KHÁC hôm nay."""
    if not os.path.exists(FILE_CLEAN):
        print("ℹ️  Chưa có file clean cũ.")
        return pd.DataFrame()
    try:
        df = pd.read_excel(FILE_CLEAN, dtype={"product_id": str})
        if df.empty or "date_collected" not in df.columns:
            return pd.DataFrame()
        ngay_trong_file = str(df["date_collected"].iloc[0])[:10]
        if ngay_trong_file == ngay_hom_nay:
            print(f"⚠️  File clean hiện tại đã là dữ liệu hôm nay ({ngay_hom_nay}). Bỏ qua history/changes.")
            return pd.DataFrame()
        print(f"📂 Tìm thấy dữ liệu cũ ngày {ngay_trong_file} để so sánh.")
        return df
    except Exception as e:
        print(f"⚠️  Không đọc được file clean cũ: {e}")
        return pd.DataFrame()

# ============================================================
# MAIN
# ============================================================
def main():
    time_vn      = datetime.utcnow() + timedelta(hours=7)
    ngay_hom_nay = time_vn.strftime("%Y-%m-%d")
    gio_hom_nay  = time_vn.strftime("%H:%M:%S")

    print(f"🤖 Pipeline khởi chạy | Giờ VN: {ngay_hom_nay} {gio_hom_nay}")

    # ----------------------------------------------------------
    # ĐỌC DỮ LIỆU CŨ TRƯỚC KHI CÀO (quan trọng - phải đọc trước)
    # ----------------------------------------------------------
    df_clean_old = load_clean_file_if_yesterday(ngay_hom_nay)

    # ----------------------------------------------------------
    # BƯỚC 1: CÀO DỮ LIỆU THÔ
    # Không dedup ở đây - để mỗi sản phẩm giữ đúng category đang quét
    # Dedup sau khi làm sạch (giữ lần xuất hiện đầu tiên theo đúng category)
    # ----------------------------------------------------------
    raw_records = []

    for cat_name, cat_id in CATEGORIES.items():
        print(f"  → Quét: {cat_name}")
        seen_in_cat = set()  # chỉ dedup trong cùng 1 category
        for page in range(1, MAX_PAGES + 1):
            data  = fetch_products(cat_id, page)
            items = data.get("data", [])
            if not items:
                break
            for item in items:
                pid = item.get("id")
                if pid and pid not in seen_in_cat:
                    seen_in_cat.add(pid)
                    item["category_main"]  = cat_name
                    item["date_collected"] = ngay_hom_nay
                    item["time_collected"] = gio_hom_nay
                    raw_records.append(item)
            paging = data.get("paging", {})
            if page * PAGE_SIZE >= paging.get("total", 0):
                break
            time.sleep(DELAY)

    if not raw_records:
        print("❌ Không lấy được dữ liệu thô!")
        return

    # Ghi raw (flatten dict/list thành string)
    df_raw = pd.DataFrame([
        {k: str(v) if isinstance(v, (dict, list)) else v for k, v in r.items()}
        for r in raw_records
    ])
    df_raw.to_excel(FILE_RAW, index=False)
    print(f"💾 [1/4] Đã lưu raw data: {len(df_raw)} sản phẩm → '{FILE_RAW}'")

    # ----------------------------------------------------------
    # BƯỚC 2: LÀM SẠCH → CLEAN DATA HÔM NAY
    # ----------------------------------------------------------
    clean_records = []
    for item in raw_records:
        price          = item.get("price", 0)
        original_price = item.get("original_price", price)
        discount_amt   = max(0, original_price - price)
        discount_pct   = round(discount_amt / original_price * 100, 1) if original_price > 0 else 0
        sold_count     = get_sold_count(item)

        cat_path = item.get("primary_category_path", "")
        cat_ids  = [int(x) for x in cat_path.split("/") if x.isdigit()] if isinstance(cat_path, str) else []
        cat_l2   = next((CATEGORY_L2_MAP[c] for c in cat_ids if c in CATEGORY_L2_MAP), "Khác")

        seller      = item.get("current_seller") or {}
        if isinstance(seller, str):
            try: seller = ast.literal_eval(seller)
            except: seller = {}

        badges      = item.get("badges_new") or []
        if isinstance(badges, str):
            try: badges = ast.literal_eval(badges)
            except: badges = []
        badge_names = [b.get("code", "") for b in badges if isinstance(b, dict)]

        shipping    = item.get("shipping_info") or {}
        if isinstance(shipping, str):
            try: shipping = ast.literal_eval(shipping)
            except: shipping = {}

        pid = str(item.get("id", ""))
        clean_records.append({
            "product_id":             pid,
            "product_name":           item.get("name", ""),
            "product_link":           f"https://tiki.vn/{item.get('url_path', '')}" if item.get("url_path") else "",
            "brand_name":             item.get("brand_name", "") or (item.get("brand") or {}).get("name", "") if not isinstance(item.get("brand"), str) else "",
            "category_l1":            item.get("category_main", ""),
            "category_l2":            cat_l2,
            "category_l3":            "",
            "primary_category":       item.get("primary_category_name", ""),
            "price":                  price,
            "original_price":         original_price,
            "discount_amount":        discount_amt,
            "discount_percent":       discount_pct,
            "rating":                 round(float(item.get("rating_average", 0) or 0), 1),
            "review_count":           safe_int(item.get("review_count", 0)),
            "sold_count":             sold_count,
            "favourite_count":        safe_int(item.get("favourite_count", 0)),
            "estimated_revenue":      price * sold_count,
            "seller_id":              seller.get("id", item.get("seller_id", "")),
            "seller_type":            seller.get("store_type", item.get("seller_type", "")),
            "is_official_store":      bool(seller.get("is_official", False)),
            "tiki_verified":          "tiki_verified" in badge_names,
            "is_tiki_now":            bool(item.get("is_tikinow_delivery", False)),
            "is_freeship":            bool(item.get("freeship_campaign", False)),
            "delivery_estimate_days": round(float(shipping.get("estimate_days", 0) or 0), 1),
            "order_route":            item.get("order_route", ""),
            "origin":                 item.get("origin", ""),
            "is_imported":            bool(item.get("is_imported", False)),
            "is_authentic":           bool(item.get("is_authentic", False)),
            "is_top_brand":           bool(item.get("is_top_brand", False)),
            "date_collected":         ngay_hom_nay,
            "time_collected":         gio_hom_nay,
        })

    df_clean_today = pd.DataFrame(clean_records)[REQUIRED_COLUMNS]
    before = len(df_clean_today)
    df_clean_today = df_clean_today.drop_duplicates(subset=["product_id"], keep="first").reset_index(drop=True)
    after = len(df_clean_today)
    print(f"🧹 [2/4] Làm sạch xong: {after} sản phẩm (bỏ {before - after} trùng lặp cross-category)")

    # ----------------------------------------------------------
    # BƯỚC 3: CẬP NHẬT HISTORICAL (đẩy clean CŨ vào lịch sử)
    # ----------------------------------------------------------
    if not df_clean_old.empty:
        df_hist_old = pd.DataFrame()
        if os.path.exists(FILE_HISTORICAL):
            try:
                df_hist_old = pd.read_excel(FILE_HISTORICAL, dtype={"product_id": str})
            except:
                pass

        df_hist = pd.concat([df_hist_old, df_clean_old], ignore_index=True)
        df_hist["date_collected"] = pd.to_datetime(df_hist["date_collected"], errors="coerce").dt.strftime("%Y-%m-%d")
        df_hist = df_hist.dropna(subset=["date_collected"])

        if "product_id" in df_hist.columns:
            df_hist = df_hist.drop_duplicates(subset=["date_collected", "product_id"])

        # Giữ tối đa 5 ngày gần nhất
        top5 = sorted(df_hist["date_collected"].unique(), reverse=True)[:5]
        df_hist = df_hist[df_hist["date_collected"].isin(top5)].reset_index(drop=True)
        df_hist.to_excel(FILE_HISTORICAL, index=False)
        print(f"📚 [3/4] Historical cập nhật: {top5} → '{FILE_HISTORICAL}'")
    else:
        print("ℹ️  [3/4] Bỏ qua historical (không có dữ liệu cũ hợp lệ).")

    # ----------------------------------------------------------
    # BƯỚC 4: SO SÁNH CHANGES
    # ----------------------------------------------------------
    if not df_clean_old.empty:
        old_map = {str(r["product_id"]): r for _, r in df_clean_old.iterrows()}
        today_ids = set(df_clean_today["product_id"].astype(str))
        rows = []

        for _, row in df_clean_today.iterrows():
            pid = str(row["product_id"])
            if pid in old_map:
                old = old_map[pid]
                p_old, p_new   = old.get("price", 0), row["price"]
                s_old, s_new   = safe_int(old.get("sold_count", 0)), safe_int(row["sold_count"])
                r_old, r_new   = float(old.get("rating", 0) or 0), float(row["rating"] or 0)
                rv_old, rv_new = safe_int(old.get("review_count", 0)), safe_int(row["review_count"])
                if p_old == p_new and s_old == s_new and r_old == r_new and rv_old == rv_new:
                    continue
                rows.append({
                    "product_id": pid, "product_name": row["product_name"],
                    "product_link": row["product_link"], "category": row["category_l1"],
                    "brand_name": row["brand_name"],
                    "price_old": p_old, "price_new": p_new,
                    "price_change": p_new - p_old,
                    "price_change_pct": round((p_new - p_old) / p_old * 100, 2) if p_old > 0 else 0,
                    "sold_old": s_old, "sold_new": s_new, "sold_increase": s_new - s_old,
                    "revenue_increase": (s_new - s_old) * p_new,
                    "rating_old": r_old, "rating_new": r_new,
                    "rating_change": round(r_new - r_old, 2),
                    "review_old": rv_old, "review_new": rv_new,
                    "review_increase": rv_new - rv_old,
                    "date_compared": ngay_hom_nay, "status": "UPDATED"
                })
            else:
                rows.append({
                    "product_id": pid, "product_name": row["product_name"],
                    "product_link": row["product_link"], "category": row["category_l1"],
                    "brand_name": row["brand_name"],
                    "price_old": 0, "price_new": row["price"],
                    "price_change": row["price"], "price_change_pct": 0,
                    "sold_old": 0, "sold_new": safe_int(row["sold_count"]),
                    "sold_increase": safe_int(row["sold_count"]),
                    "revenue_increase": safe_int(row["estimated_revenue"]),
                    "rating_old": 0, "rating_new": float(row["rating"] or 0),
                    "rating_change": float(row["rating"] or 0),
                    "review_old": 0, "review_new": safe_int(row["review_count"]),
                    "review_increase": safe_int(row["review_count"]),
                    "date_compared": ngay_hom_nay, "status": "NEW"
                })

        # Sản phẩm bị xóa
        for pid, old in old_map.items():
            if pid not in today_ids:
                rows.append({
                    "product_id": pid, "product_name": old.get("product_name", ""),
                    "product_link": old.get("product_link", ""), "category": old.get("category_l1", ""),
                    "brand_name": old.get("brand_name", ""),
                    "price_old": old.get("price", 0), "price_new": 0,
                    "price_change": -old.get("price", 0), "price_change_pct": -100,
                    "sold_old": safe_int(old.get("sold_count", 0)), "sold_new": 0, "sold_increase": 0,
                    "revenue_increase": 0,
                    "rating_old": float(old.get("rating", 0) or 0), "rating_new": 0,
                    "rating_change": -float(old.get("rating", 0) or 0),
                    "review_old": safe_int(old.get("review_count", 0)), "review_new": 0, "review_increase": 0,
                    "date_compared": ngay_hom_nay, "status": "REMOVED"
                })

        if rows:
            df_ch = pd.DataFrame(rows).sort_values("revenue_increase", ascending=False)
            df_ch.to_excel(FILE_CHANGES, index=False)
            n_new = sum(1 for r in rows if r["status"] == "NEW")
            n_upd = sum(1 for r in rows if r["status"] == "UPDATED")
            n_rem = sum(1 for r in rows if r["status"] == "REMOVED")
            print(f"📊 [4/4] Changes: {n_new} mới | {n_upd} cập nhật | {n_rem} bị xóa → '{FILE_CHANGES}'")
        else:
            print("ℹ️  [4/4] Không có thay đổi nào so với ngày hôm qua.")
    else:
        print("ℹ️  [4/4] Bỏ qua changes (không có dữ liệu cũ hợp lệ).")

    # ----------------------------------------------------------
    # BƯỚC 5: GHI ĐÈ CLEAN DATA HÔM NAY (luôn làm cuối cùng)
    # ----------------------------------------------------------
    df_clean_today.to_excel(FILE_CLEAN, index=False)
    print(f"✅ [5/4] Đã ghi clean data hôm nay → '{FILE_CLEAN}'")
    print(f"🎉 Pipeline hoàn tất!")


if __name__ == "__main__":
    main()
