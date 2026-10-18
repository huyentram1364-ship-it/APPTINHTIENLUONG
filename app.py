
import streamlit as st
import pandas as pd
import os
from io import BytesIO
from datetime import datetime

# =====================================================
# 1. CẤU HÌNH ỨNG DỤNG
# =====================================================
st.set_page_config(
    page_title="Phần mềm tính lương hàng loạt",
    page_icon="💰",
    layout="wide"
)

# Hiển thị ảnh nếu ảnh nằm cùng thư mục với app.py
if os.path.exists("IMG_0724.jpg"):
    st.image("IMG_0724.jpg", use_container_width=True)

st.title("💰 PHẦN MỀM TÍNH LƯƠNG - LÊ NGÔ HUYỀN TRĂM")
st.caption(
    "Tính lương, bảo hiểm, thuế TNCN và tiền thực lãnh "
    "cho tối đa 500 người lao động trong một lần."
)

st.info(
    "Đơn vị tiền tệ: triệu đồng/tháng. "
    "Công thức và mức giảm trừ được giữ theo chương trình ban đầu."
)

# =====================================================
# 2. CÁC THAM SỐ TÍNH TOÁN
# =====================================================
GIAM_TRU_BAN_THAN = 15.5
GIAM_TRU_PHU_THUOC = 6.2
TY_LE_BAO_HIEM = 0.105
SO_NHAN_VIEN_TOI_DA = 500

COT_DAU_VAO = [
    "Mã nhân viên",
    "Họ và tên",
    "Lương cơ bản",
    "Tiền thưởng",
    "Phụ cấp tính BHXH",
    "Phụ cấp không tính BHXH",
    "Số người phụ thuộc",
]

COT_TIEN = [
    "Lương cơ bản",
    "Tiền thưởng",
    "Phụ cấp tính BHXH",
    "Phụ cấp không tính BHXH",
]

# =====================================================
# 3. CÁC HÀM HỖ TRỢ
# =====================================================
def dinh_dang_tien(so_tien):
    return f"{so_tien:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tinh_thue_tncn(thu_nhap_tinh_thue):
    """
    Biểu thuế theo code ban đầu.
    Đơn vị: triệu đồng/tháng.
    """
    thu_nhap_tinh_thue = max(0.0, float(thu_nhap_tinh_thue))

    if thu_nhap_tinh_thue <= 10:
        return thu_nhap_tinh_thue * 0.05
    elif thu_nhap_tinh_thue <= 30:
        return thu_nhap_tinh_thue * 0.10 - 0.5
    elif thu_nhap_tinh_thue <= 60:
        return thu_nhap_tinh_thue * 0.20 - 3.5
    elif thu_nhap_tinh_thue <= 100:
        return thu_nhap_tinh_thue * 0.30 - 9.5
    else:
        return thu_nhap_tinh_thue * 0.35 - 14.5


def tao_du_lieu_mac_dinh(so_luong):
    """Tạo bảng nhập liệu cho số nhân viên được chọn."""
    return pd.DataFrame({
        "Mã nhân viên": [f"NV{i:03d}" for i in range(1, so_luong + 1)],
        "Họ và tên": ["" for _ in range(so_luong)],
        "Lương cơ bản": [15.0 for _ in range(so_luong)],
        "Tiền thưởng": [0.0 for _ in range(so_luong)],
        "Phụ cấp tính BHXH": [0.0 for _ in range(so_luong)],
        "Phụ cấp không tính BHXH": [0.0 for _ in range(so_luong)],
        "Số người phụ thuộc": [0 for _ in range(so_luong)],
    })


def chuan_hoa_du_lieu(df, so_luong):
    """Đảm bảo dữ liệu có đúng số dòng và đủ các cột cần thiết."""
    df = df.copy()

    for cot in COT_DAU_VAO:
        if cot not in df.columns:
            if cot == "Mã nhân viên":
                df[cot] = [f"NV{i:03d}" for i in range(1, len(df) + 1)]
            elif cot == "Họ và tên":
                df[cot] = ""
            else:
                df[cot] = 0

    df = df[COT_DAU_VAO].head(so_luong).copy()

    if len(df) < so_luong:
        bo_sung = tao_du_lieu_mac_dinh(so_luong - len(df))
        bo_sung["Mã nhân viên"] = [
            f"NV{i:03d}" for i in range(len(df) + 1, so_luong + 1)
        ]
        df = pd.concat([df, bo_sung], ignore_index=True)

    df = df.reset_index(drop=True)

    # Chuyển cột tiền sang số; ô trống được hiểu là 0
    for cot in COT_TIEN:
        df[cot] = pd.to_numeric(df[cot], errors="coerce").fillna(0.0)

    df["Số người phụ thuộc"] = (
        pd.to_numeric(df["Số người phụ thuộc"], errors="coerce")
        .fillna(0)
        .clip(lower=0)
        .astype(int)
    )

    df["Mã nhân viên"] = df["Mã nhân viên"].fillna("").astype(str)
    df["Họ và tên"] = df["Họ và tên"].fillna("").astype(str)

    return df


def tinh_bang_luong(df):
    """Tính toán cho tất cả nhân viên trong bảng."""
    kq = df.copy()

    kq["Tổng thu nhập"] = (
        kq["Lương cơ bản"]
        + kq["Tiền thưởng"]
        + kq["Phụ cấp tính BHXH"]
        + kq["Phụ cấp không tính BHXH"]
    )

    kq["Bảo hiểm người lao động đóng"] = (
        kq["Lương cơ bản"] + kq["Phụ cấp tính BHXH"]
    ) * TY_LE_BAO_HIEM

    kq["Giảm trừ bản thân"] = GIAM_TRU_BAN_THAN
    kq["Giảm trừ người phụ thuộc"] = (
        GIAM_TRU_PHU_THUOC * kq["Số người phụ thuộc"]
    )

    kq["Thu nhập tính thuế"] = (
        kq["Tổng thu nhập"]
        - kq["Bảo hiểm người lao động đóng"]
        - kq["Giảm trừ bản thân"]
        - kq["Giảm trừ người phụ thuộc"]
    ).clip(lower=0)

    kq["Thuế TNCN"] = kq["Thu nhập tính thuế"].apply(tinh_thue_tncn)

    kq["Tiền thực lãnh"] = (
        kq["Tổng thu nhập"]
        - kq["Bảo hiểm người lao động đóng"]
        - kq["Thuế TNCN"]
    )

    return kq


def tao_file_excel(df_ket_qua):
    """Xuất Excel gồm bảng lương chi tiết và bảng tổng hợp."""
    buffer = BytesIO()

    cot_xuat = [
        "Mã nhân viên",
        "Họ và tên",
        "Lương cơ bản",
        "Tiền thưởng",
        "Phụ cấp tính BHXH",
        "Phụ cấp không tính BHXH",
        "Tổng thu nhập",
        "Số người phụ thuộc",
        "Bảo hiểm người lao động đóng",
        "Giảm trừ bản thân",
        "Giảm trừ người phụ thuộc",
        "Thu nhập tính thuế",
        "Thuế TNCN",
        "Tiền thực lãnh",
    ]

    df_xuat = df_ket_qua[cot_xuat].copy()

    bang_tong_hop = pd.DataFrame({
        "Chỉ tiêu": [
            "Số người lao động",
            "Tổng lương cơ bản",
            "Tổng tiền thưởng",
            "Tổng phụ cấp tính BHXH",
            "Tổng phụ cấp không tính BHXH",
            "Tổng thu nhập",
            "Tổng bảo hiểm người lao động đóng",
            "Tổng thu nhập tính thuế",
            "Tổng thuế TNCN",
            "Tổng tiền thực lãnh",
        ],
        "Số tiền / số lượng": [
            len(df_ket_qua),
            df_ket_qua["Lương cơ bản"].sum(),
            df_ket_qua["Tiền thưởng"].sum(),
            df_ket_qua["Phụ cấp tính BHXH"].sum(),
            df_ket_qua["Phụ cấp không tính BHXH"].sum(),
            df_ket_qua["Tổng thu nhập"].sum(),
            df_ket_qua["Bảo hiểm người lao động đóng"].sum(),
            df_ket_qua["Thu nhập tính thuế"].sum(),
            df_ket_qua["Thuế TNCN"].sum(),
            df_ket_qua["Tiền thực lãnh"].sum(),
        ]
    })

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_xuat.to_excel(writer, index=False, sheet_name="Bang luong chi tiet")
        bang_tong_hop.to_excel(writer, index=False, sheet_name="Tong hop")

        # Định dạng bảng Excel
        for sheet_name in ["Bang luong chi tiet", "Tong hop"]:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions

            for col in ws.columns:
                max_length = max(
                    len(str(cell.value)) if cell.value is not None else 0
                    for cell in col
                )
                ws.column_dimensions[col[0].column_letter].width = min(
                    max(max_length + 2, 14), 32
                )

        ws = writer.sheets["Bang luong chi tiet"]
        for row in ws.iter_rows(min_row=2, min_col=3, max_col=14):
            for cell in row:
                if cell.column != 8:  # Cột số người phụ thuộc
                    cell.number_format = '#,##0.000'

        ws2 = writer.sheets["Tong hop"]
        for row in ws2.iter_rows(min_row=2, min_col=2, max_col=2):
            row[0].number_format = '#,##0.000'

    buffer.seek(0)
    return buffer.getvalue()


def tao_file_mau_excel():
    """Tạo file Excel mẫu để nhập dữ liệu nhân viên."""
    buffer = BytesIO()
    df_mau = tao_du_lieu_mac_dinh(1)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_mau.to_excel(writer, index=False, sheet_name="Nhan vien")
        ws = writer.sheets["Nhan vien"]
        ws.freeze_panes = "A2"

        for col in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = max(
                max_length + 2, 16
            )

    buffer.seek(0)
    return buffer.getvalue()


# =====================================================
# 4. CHỌN SỐ LƯỢNG NHÂN VIÊN
# =====================================================
st.subheader("1. Chọn số lượng người lao động")

so_luong_nhan_vien = st.number_input(
    "Bạn cần tính lương cho bao nhiêu người?",
    min_value=1,
    max_value=SO_NHAN_VIEN_TOI_DA,
    value=10,
    step=1,
    help="Có thể tính từ 1 đến tối đa 500 người trong một lần."
)

st.caption(f"Số lượng đang chọn: {so_luong_nhan_vien} người.")

st.download_button(
    label="📥 Tải file Excel mẫu nhập nhân viên",
    data=tao_file_mau_excel(),
    file_name="mau_nhap_luong_nhan_vien.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# =====================================================
# 5. NHẬP DỮ LIỆU NHÂN VIÊN
# =====================================================
st.subheader("2. Nhập dữ liệu người lao động")

st.write(
    "Bạn có thể nhập trực tiếp vào bảng bên dưới hoặc tải lên file Excel "
    "đã điền theo mẫu. Khi tải file lên, dữ liệu sẽ được đưa vào bảng để "
    "bạn kiểm tra và chỉnh sửa trước khi tính."
)

file_excel = st.file_uploader(
    "Tải file Excel danh sách nhân viên (không bắt buộc)",
    type=["xlsx"],
    help="File cần có một trang tính với các tiêu đề cột giống file mẫu."
)

du_lieu_nguon = tao_du_lieu_mac_dinh(int(so_luong_nhan_vien))

if file_excel is not None:
    try:
        df_doc = pd.read_excel(file_excel, sheet_name=0)
        du_lieu_nguon = chuan_hoa_du_lieu(
            df_doc,
            int(so_luong_nhan_vien)
        )
        st.success(
            f"Đã đọc dữ liệu từ file {file_excel.name}. "
            f"Vui lòng kiểm tra bảng trước khi tính."
        )
    except Exception as e:
        st.error(
            "Không đọc được file Excel. Hãy sử dụng file mẫu do ứng dụng "
            "cung cấp và kiểm tra lại tiêu đề cột."
        )
        st.stop()

# Dùng khóa riêng theo số dòng và tên file để làm mới bảng khi đổi số lượng
ten_file = file_excel.name if file_excel is not None else "nhap_tay"
khoa_bang = f"bang_nhan_vien_{int(so_luong_nhan_vien)}_{ten_file}"

df_nhap = st.data_editor(
    du_lieu_nguon,
    key=khoa_bang,
    num_rows="fixed",
    hide_index=True,
    use_container_width=True,
    height=420,
    column_config={
        "Mã nhân viên": st.column_config.TextColumn(
            "Mã nhân viên",
            help="Mã định danh riêng cho từng người."
        ),
        "Họ và tên": st.column_config.TextColumn(
            "Họ và tên",
            help="Nhập họ tên người lao động."
        ),
        "Lương cơ bản": st.column_config.NumberColumn(
            "Lương cơ bản (triệu)",
            min_value=0.0,
            step=0.5,
            format="%.3f"
        ),
        "Tiền thưởng": st.column_config.NumberColumn(
            "Tiền thưởng (triệu)",
            min_value=0.0,
            step=0.5,
            format="%.3f"
        ),
        "Phụ cấp tính BHXH": st.column_config.NumberColumn(
            "Phụ cấp tính BHXH (triệu)",
            min_value=0.0,
            step=0.5,
            format="%.3f"
        ),
        "Phụ cấp không tính BHXH": st.column_config.NumberColumn(
            "Phụ cấp không tính BHXH (triệu)",
            min_value=0.0,
            step=0.5,
            format="%.3f"
        ),
        "Số người phụ thuộc": st.column_config.NumberColumn(
            "Số người phụ thuộc",
            min_value=0,
            step=1,
            format="%d"
        ),
    },
)

st.caption(
    "Kiểm tra mã nhân viên, họ tên và các khoản thu nhập trước khi tính. "
    "Các ô tiền để trống hoặc không hợp lệ sẽ được xử lý thành 0."
)

# =====================================================
# 6. NÚT TÍNH LƯƠNG HÀNG LOẠT
# =====================================================
st.divider()

if st.button(
    "🧮 TÍNH LƯƠNG CHO TẤT CẢ NHÂN VIÊN",
    type="primary",
    use_container_width=True,
):
    try:
        df_dau_vao = chuan_hoa_du_lieu(
            df_nhap,
            int(so_luong_nhan_vien)
        )

        # Cảnh báo mã nhân viên trùng
        ma_khong_rong = df_dau_vao["Mã nhân viên"].str.strip()
        ma_trung = ma_khong_rong[
            (ma_khong_rong != "") & ma_khong_rong.duplicated(keep=False)
        ].unique()

        if len(ma_trung) > 0:
            st.warning(
                "Có mã nhân viên bị trùng: "
                + ", ".join(ma_trung)
                + ". Hãy kiểm tra lại trước khi sử dụng kết quả."
            )

        df_ket_qua = tinh_bang_luong(df_dau_vao)

        # Lưu kết quả trong session để có thể tải file sau khi tính
        st.session_state["ket_qua_luong"] = df_ket_qua
        st.session_state["thoi_diem_tinh"] = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

    except Exception as e:
        st.error(f"Không thể tính lương: {e}")


# =====================================================
# 7. HIỂN THỊ KẾT QUẢ VÀ XUẤT EXCEL
# =====================================================
if "ket_qua_luong" in st.session_state:
    df_ket_qua = st.session_state["ket_qua_luong"]

    st.divider()
    st.subheader("3. Kết quả tính lương hàng loạt")

    st.caption(
        f"Thời điểm tính gần nhất: "
        f"{st.session_state.get('thoi_diem_tinh', '')}"
    )

    # Các chỉ tiêu tổng hợp
    tong_nhan_vien = len(df_ket_qua)
    tong_thu_nhap = df_ket_qua["Tổng thu nhập"].sum()
    tong_bao_hiem = df_ket_qua["Bảo hiểm người lao động đóng"].sum()
    tong_thu_nhap_tinh_thue = df_ket_qua["Thu nhập tính thuế"].sum()
    tong_thue = df_ket_qua["Thuế TNCN"].sum()
    tong_thuc_lanh = df_ket_qua["Tiền thực lãnh"].sum()

    c1, c2, c3 = st.columns(3)

    c1.metric("Số người lao động", f"{tong_nhan_vien:,}")
    c2.metric("Tổng thu nhập", f"{dinh_dang_tien(tong_thu_nhap)} triệu")
    c3.metric("Tổng bảo hiểm", f"{dinh_dang_tien(tong_bao_hiem)} triệu")

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Tổng thu nhập tính thuế",
        f"{dinh_dang_tien(tong_thu_nhap_tinh_thue)} triệu"
    )
    c5.metric("Tổng thuế TNCN", f"{dinh_dang_tien(tong_thue)} triệu")
    c6.metric("TỔNG THỰC LÃNH", f"{dinh_dang_tien(tong_thuc_lanh)} triệu")

    # Bảng chi tiết
    st.subheader("4. Bảng lương chi tiết từng người")

    cot_hien_thi = [
        "Mã nhân viên",
        "Họ và tên",
        "Lương cơ bản",
        "Tiền thưởng",
        "Phụ cấp tính BHXH",
        "Phụ cấp không tính BHXH",
        "Tổng thu nhập",
        "Số người phụ thuộc",
        "Bảo hiểm người lao động đóng",
        "Thu nhập tính thuế",
        "Thuế TNCN",
        "Tiền thực lãnh",
    ]

    df_hien_thi = df_ket_qua[cot_hien_thi].copy()

    cot_tien_ket_qua = [
        "Lương cơ bản",
        "Tiền thưởng",
        "Phụ cấp tính BHXH",
        "Phụ cấp không tính BHXH",
        "Tổng thu nhập",
        "Bảo hiểm người lao động đóng",
        "Thu nhập tính thuế",
        "Thuế TNCN",
        "Tiền thực lãnh",
    ]

    for cot in cot_tien_ket_qua:
        df_hien_thi[cot] = df_hien_thi[cot].map(dinh_dang_tien)

    st.dataframe(
        df_hien_thi,
        use_container_width=True,
        hide_index=True,
        height=500
    )

    # Bảng tổng hợp
    st.subheader("5. Tổng hợp quỹ lương")

    df_tong_hop = pd.DataFrame({
        "Chỉ tiêu": [
            "Số người lao động",
            "Tổng lương cơ bản",
            "Tổng tiền thưởng",
            "Tổng phụ cấp tính BHXH",
            "Tổng phụ cấp không tính BHXH",
            "Tổng thu nhập",
            "Tổng bảo hiểm người lao động đóng",
            "Tổng thu nhập tính thuế",
            "Tổng thuế TNCN",
            "Tổng tiền thực lãnh",
        ],
        "Giá trị": [
            tong_nhan_vien,
            df_ket_qua["Lương cơ bản"].sum(),
            df_ket_qua["Tiền thưởng"].sum(),
            df_ket_qua["Phụ cấp tính BHXH"].sum(),
            df_ket_qua["Phụ cấp không tính BHXH"].sum(),
            tong_thu_nhap,
            tong_bao_hiem,
            tong_thu_nhap_tinh_thue,
            tong_thue,
            tong_thuc_lanh,
        ]
    })

    df_tong_hop_hien_thi = df_tong_hop.copy()
    df_tong_hop_hien_thi["Giá trị"] = df_tong_hop_hien_thi.apply(
        lambda row: (
            f"{int(row['Giá trị']):,}"
            if row["Chỉ tiêu"] == "Số người lao động"
            else dinh_dang_tien(row["Giá trị"])
        ),
        axis=1
    )

    st.dataframe(
        df_tong_hop_hien_thi,
        use_container_width=True,
        hide_index=True
    )

    # Xuất Excel
    st.subheader("6. Xuất kết quả ra Excel")

    try:
        file_excel_ket_qua = tao_file_excel(df_ket_qua)

        st.download_button(
            label="📥 TẢI FILE EXCEL BẢNG LƯƠNG (.xlsx)",
            data=file_excel_ket_qua,
            file_name="bang_luong_hang_loat.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True,
        )

        st.success(
            "Đã tạo file Excel gồm 2 sheet: "
            "'Bang luong chi tiet' và 'Tong hop'."
        )

    except Exception as e:
        st.error(f"Không thể tạo file Excel: {e}")

    # Công thức
    with st.expander("📘 Xem công thức tính"):
        st.markdown("""
        **1. Tổng thu nhập**

        Lương cơ bản + Tiền thưởng + Phụ cấp tính BHXH
        + Phụ cấp không tính BHXH.

        **2. Bảo hiểm theo code ban đầu**

        (Lương cơ bản + Phụ cấp tính BHXH) × 10,5%.

        **3. Thu nhập tính thuế**

        Tổng thu nhập − Bảo hiểm − Giảm trừ bản thân
        − Giảm trừ người phụ thuộc.

        Nếu kết quả nhỏ hơn 0, thu nhập tính thuế được tính bằng 0.

        **4. Thuế TNCN**

        Áp dụng biểu thuế theo hàm `tinh_thue_tncn()` ở đầu chương trình.

        **5. Tiền thực lãnh**

        Tổng thu nhập − Bảo hiểm − Thuế TNCN.
        """)

st.divider()

st.caption(
    "Lưu ý: Kết quả phụ thuộc vào dữ liệu đầu vào và các tham số thuế, "
    "bảo hiểm được cài đặt. Hãy kiểm tra quy định pháp luật hiện hành "
    "trước khi dùng làm căn cứ trả lương hoặc kê khai thuế chính thức."
)
