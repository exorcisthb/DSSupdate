import pandas as pd
from datetime import datetime
import os

file_name = "du_lieu_cua_toi.xlsx"

# --- 1. CODE LẤY DỮ LIỆU MỚI ---
# (Bạn thay thế phần này bằng code cào web hoặc gọi API của bạn để lấy dữ liệu hôm nay)
ngay_hom_nay = datetime.now().strftime("%Y-%m-%d")
df_moi = pd.DataFrame({
    "Ngay": [ngay_hom_nay, ngay_hom_nay],  # Cột ngày bắt buộc phải có để lọc
    "Ten_Du_Lieu": ["Dữ liệu mẫu A", "Dữ liệu mẫu B"],
    "Gia_Tri": [100, 200]
})
# --------------------------------

# 2. Đọc file Excel cũ nếu đã tồn tại
if os.path.exists(file_name):
    df_cu = pd.read_excel(file_name)
    # Gộp dữ liệu cũ và dữ liệu mới lại với nhau
    df_tong = pd.concat([df_cu, df_moi], ignore_index=True)
else:
    df_tong = df_moi

# 3. Xử lý lọc dữ liệu (Chỉ giữ lại 5 ngày gần nhất)
# Chuyển cột Ngay sang định dạng datetime để sắp xếp chính xác
df_tong['Ngay'] = pd.to_datetime(df_tong['Ngay'])

# Tìm tất cả các ngày duy nhất đang có và sắp xếp giảm dần (mới nhất xếp đầu)
cac_ngay_duy_nhat = sorted(df_tong['Ngay'].unique(), reverse=True)

# Lấy ra tối đa 5 ngày mới nhất
top_5_ngay = cac_ngay_duy_nhat[:5]

# Lọc lại bảng dữ liệu: Chỉ giữ lại các dòng thuộc về 5 ngày này
df_ket_qua = df_tong[df_tong['Ngay'].isin(top_5_ngay)]

# Chuyển định dạng ngày về lại dạng chuỗi YYYY-MM-DD cho đẹp mắt
df_ket_qua['Ngay'] = df_ket_qua['Ngay'].dt.strftime('%Y-%m-%d')

# 4. Lưu đè lại vào file Excel ban đầu
df_ket_qua.to_excel(file_name, index=False)
print("Đã cập nhật dữ liệu thành công và giới hạn trong 5 ngày gần nhất!")