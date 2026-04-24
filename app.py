import streamlit as st
from openai import OpenAI
import base64
import pandas as pd

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("Đọc hóa đơn")

files = st.file_uploader("Upload ảnh", accept_multiple_files=True)

if st.button("Xử lý"):
    all_data = []

    for file in files:
        img_base64 = base64.b64encode(file.read()).decode()

        res = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
Đọc hóa đơn này và trích đúng 3 cột sau:

SKU = cột Mã SP (mã vạch sản phẩm)
TenSanPham = cột Sản phẩm
SoLuong = cột SL

Chỉ trả về đúng định dạng:
SKU | TenSanPham | SoLuong

Không giải thích.
Không thêm dòng thừa.
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

        text = res.choices[0].message.content

        for line in text.split("\n"):
            if "|" in line:
                try:
                    parts = line.split("|")

                    if len(parts) == 3:
                        sku = parts[0].strip()
                        ten_san_pham = parts[1].strip()
                        so_luong = float(parts[2].strip())

                        all_data.append([
                            sku,
                            ten_san_pham,
                            so_luong
                        ])
                except:
                    pass

    if all_data:
        df = pd.DataFrame(
            all_data,
            columns=["SKU", "TenSanPham", "SoLuong"]
        )

        # Gom nhóm theo SKU + Tên sản phẩm
        result = (
            df.groupby(["SKU", "TenSanPham"], as_index=False)
            ["SoLuong"]
            .sum()
        )

        st.write(result)
    else:
        st.warning("Không đọc được dữ liệu từ ảnh.")
