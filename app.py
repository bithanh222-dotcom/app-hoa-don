import streamlit as st
from openai import OpenAI
import base64
import pandas as pd

# Kết nối OpenAI API (ChatGPT)
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

st.set_page_config(page_title="Đọc hóa đơn", layout="wide")
st.title("📄 Công cụ đọc hóa đơn SKU")

st.write("Upload ảnh hóa đơn → ChatGPT sẽ đọc và tổng hợp kết quả")

files = st.file_uploader(
    "Chọn ảnh hóa đơn",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png"]
)

if st.button("Xử lý hóa đơn"):
    if not files:
        st.warning("Vui lòng upload ít nhất 1 ảnh.")
    else:
        all_data = []

        with st.spinner("ChatGPT đang xử lý hóa đơn..."):
            for file in files:
                try:
                    # Chuyển ảnh sang base64 để gửi cho ChatGPT
                    img_base64 = base64.b64encode(file.read()).decode()

                    # Gọi ChatGPT xử lý ảnh hóa đơn
                    response = client.chat.completions.create(
                        model="gpt-4.1",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": """
Đọc ảnh hóa đơn này.

Yêu cầu:
- SKU = cột Mã SP (mã vạch sản phẩm)
- TenSanPham = cột Sản phẩm
- SoLuong = cột SL

Hãy:
1. Trích tất cả sản phẩm trong ảnh
2. Chuẩn hóa SKU giống nhau
3. Cộng tổng số lượng theo từng SKU

Chỉ trả về đúng định dạng sau:
SKU | TenSanPham | SoLuong

Không giải thích
Không thêm tiêu đề
Không thêm dòng thừa
Chỉ trả dữ liệu
"""
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{img_base64}"
                                        }
                                    }
                                ]
                            }
                        ]
                    )

                    result_text = response.choices[0].message.content

                    # Tách dữ liệu từng dòng
                    for line in result_text.split("\n"):
                        if "|" in line:
                            parts = line.split("|")

                            if len(parts) == 3:
                                try:
                                    sku = parts[0].strip()
                                    ten_san_pham = parts[1].strip()
                                    so_luong = float(parts[2].strip())

                                    if sku:
                                        all_data.append([
                                            sku,
                                            ten_san_pham,
                                            so_luong
                                        ])
                                except:
                                    pass

                except Exception as e:
                    st.error(f"Lỗi xử lý file {file.name}: {str(e)}")

        # Tổng hợp kết quả
        if all_data:
            df = pd.DataFrame(
                all_data,
                columns=["SKU", "TenSanPham", "SoLuong"]
            )

            final_result = (
                df.groupby(
                    ["SKU", "TenSanPham"],
                    as_index=False
                )["SoLuong"]
                .sum()
                .sort_values("SKU")
            )

            st.success("Xử lý hoàn tất")

            st.subheader("Kết quả tổng hợp")
            st.dataframe(
                final_result,
                use_container_width=True
            )

            # Nút tải Excel
            excel_file = "ket_qua_hoa_don.xlsx"
            final_result.to_excel(excel_file, index=False)

            with open(excel_file, "rb") as f:
                st.download_button(
                    label="📥 Tải file Excel",
                    data=f,
                    file_name="ket_qua_hoa_don.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        else:
            st.error("Không đọc được dữ liệu từ ảnh hóa đơn.")
