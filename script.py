import pandas as pd
from datetime import datetime
import os

# 1. Khai báo các tên file (giữ chính xác theo tên file trên GitHub của bạn)
FILE_CLEAN = "tiki_clean_data.xlsx"
FILE_HISTORICAL = "tiki_historical_data.xlsx"


def cao_du_lieu_tiki_cua_ban():
    """
    HÀM CÀO DỮ LIỆU TIKI CỦA BẠN
    Nhiệm vụ của bạn: Hãy dán toàn bộ đoạn code cào Tiki hiện tại của bạn vào ĐÂY.
    Lưu ý: Kết quả cào cuối cùng phải trả về một DataFrame (ví dụ: df_ket_qua_cao).
    """
    # =========================================================================
    # 💥 BẮT ĐẦU: DÁN CODE CÀO TIKI CỦA BẠN XUỐNG DƯỚI DÒNG NÀY 💥
    
    # (Đoạn code dưới đây chỉ là mẫu minh họa, bạn hãy xóa đi và dán code của bạn vào)
    print("Đang chạy hệ thống cào dữ liệu Tiki...")
    
    df_ket_qua_cao = pd.DataFrame({
        "Ten_SanPham": ["Sách Đắc Nhân Tâm bản đẹp", "Chuột máy tính Logitech B100"],
        "Gia_Ban": [75000, 120000],
        # Nếu code cào của bạn chưa có cột "Ngay", hệ thống phía dưới sẽ tự bù vào.
    })
    
    # 💥 KẾT THÚC ĐOẠN DÁN CODE CÀO CỦA BẠN 💥
    # =========================================================================
    return df_ket_qua_cao


def main():
    # --- Bước 1: Đọc cấu trúc các cột chuẩn từ file clean ---
    if not os.path.exists(FILE_CLEAN):
        print(f"❌ Lỗi: Không tìm thấy file khuôn mẫu '{FILE_CLEAN}' trên hệ thống GitHub!")
        return
        
    df_clean = pd.read_excel(FILE_CLEAN)
    cac_cot_chuan = df_clean.columns.tolist()
    print(f"🤖 Đã lấy cấu trúc chuẩn gồm {len(cac_cot_chuan)} cột từ file clean.")

    # --- Bước 2: Chạy hàm cào dữ liệu mới của ngày hôm nay ---
    try:
        df_raw_today = cao_du_lieu_tiki_cua_ban()
    except Exception as e:
        print(f"❌ Lỗi trong quá trình cào dữ liệu: {e}")
        return

    # Lấy ngày hôm nay theo định dạng chuỗi chuẩn YYYY-MM-DD
    ngay_hom_nay = datetime.now().strftime("%Y-%m-%d")

    # Nếu dữ liệu cào về chưa có sẵn cột ngày, tự động tạo để thuật toán chạy không lỗi
    if 'Ngay' not in df_raw_today.columns:
        df_raw_today['Ngay'] = ngay_hom_nay

    # --- Bước 3: Tự động ép chuẩn các trường dữ liệu ---
    # (Cột thừa tự xóa, cột thiếu tự thêm trống, thứ tự cột tự sắp xếp khớp 100% với file clean)
    df_today_standardized = df_raw_today.reindex(columns=cac_cot_chuan)
    
    # Điền ngày hôm nay vào cột 'Ngay' nếu cột này đang bị trống sau khi ép chuẩn
    if 'Ngay' in df_today_standardized.columns:
        df_today_standardized['Ngay'] = df_today_standardized['Ngay'].fillna(ngay_hom_nay)

    # --- Bước 4: Đọc file lịch sử và gộp dữ liệu mới vào ---
    if os.path.exists(FILE_HISTORICAL):
        df_historical = pd.read_excel(FILE_HISTORICAL)
        # Gộp dữ liệu cũ và dữ liệu mới cào lại thành một bảng chung
        df_tong = pd.concat([df_historical, df_today_standardized], ignore_index=True)
        print("👉 Đã gộp dữ liệu mới vào file lịch sử.")
    else:
        df_tong = df_today_standardized
        print("👉 Chưa có file lịch sử cũ, hệ thống tự tạo file lịch sử mới.")

    # --- Bước 5: Giới hạn dữ liệu trong vòng 5 ngày gần nhất ---
    # Chuẩn hóa cột Ngay về dạng chuỗi YYYY-MM-DD để tránh lỗi lệch định dạng
    df_tong['Ngay'] = pd.to_datetime(df_tong['Ngay']).dt.strftime('%Y-%m-%d')
    
    # Tìm tất cả các ngày duy nhất đang có và xếp từ mới nhất đến cũ nhất
    danh_sach_ngay = sorted(df_tong['Ngay'].unique(), reverse=True)
    
    # Giữ lại tối đa 5 ngày mới nhất (Ngày thứ 6 trở đi sẽ tự động bị loại bỏ)
    top_5_ngay = danh_sach_ngay[:5]
    print(f"📅 Danh sách 5 ngày được giữ lại trong file: {top_5_ngay}")

    # Lọc lại bảng dữ liệu tổng theo danh sách 5 ngày này
    df_cuoi_cung = df_tong[df_tong['Ngay'].isin(top_5_ngay)]

    # --- Bước 6: Ghi đè file dữ liệu mới lên GitHub ---
    df_cuoi_cung.to_excel(FILE_HISTORICAL, index=False)
    print(f"✅ Thành công! File '{FILE_HISTORICAL}' đã được cập nhật chuẩn hóa lúc 8h sáng.")


if __name__ == "__main__":
    main()
