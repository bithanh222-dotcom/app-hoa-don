import streamlit as st
from openai import OpenAI
import base64
import pandas as pd
import json

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

st.set_page_config(page_title="Đọc hóa đơn", layout="wide")
st.title("📄 Đọc hóa đơn bằng ChatGPT")

files = st.file_uploader(
    "Upload ảnh hóa đơn",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png"]
)

if st.button("Xử lý"):
    if not files:
        st.warning("Vui lòng upload ít nhất 1 ảnh")
    else:
        all_data = []

        with st.spinner("ChatGPT đang xử lý..."):

            for file in files:
                img_base64 = base64.b64encode(file.read()).decode()

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": """
Đọc ảnh hóa đơn này.

Mỗi dòng sản phẩm có:
- SKU = cột Mã SP
- TenSanPham = cột Sản phẩm
- SoLuong = cột SL

Yêu cầu:
1. Trích toàn bộ sản phẩm
2. Chuẩn hóa SKU giống nhau
3. Chỉ trả về JSON thuần
4. Không giải thích
5. Không markdown
6. Không code block

Ví dụ đúng:

[
  {
    "sku": "8931234567890",
    "ten_san_pham": "Kim chi cải thảo",
    "so_luong": 5
  }
]
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

                    result_text = response.choices[0].message.content.strip()

                    # parse JSON
                    data = json.loads(result_text)

                    for item in data:
                        sku = str(item.get("sku", "")).strip()
                        ten = str(item.get("ten_san_pham", "")).strip()
                        qty = float(item.get("so_luong", 0))

                        if sku:
                            all_data.append([
                                sku,
                                ten,
                                qty
                            ])

                except Exception as e:
                    st.error(f"Lỗi file {file.name}: {str(e)}")

        if all_data:
            df = pd.DataFrame(
                all_data,
                columns=[
                    "SKU",
                    "TenSanPham",
                    "SoLuong"
                ]
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

            st.dataframe(
                final_result,
                use_container_width=True
            )

        else:
            st.error("Không đọc được dữ liệu từ ảnh")
