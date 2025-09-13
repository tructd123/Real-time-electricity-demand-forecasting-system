import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta, date
import requests
import time

st.set_page_config(page_title="US Electricity & Forecast Dashboard", layout="wide")

# Giả lập dữ liệu
np.random.seed(42)
today = date(2020, 9, 23)
dates_real = pd.date_range(start="2020-06-13", end=today)
states = ['AEC', 'AECI', 'AVA', 'AZPS', 'BANC', 'BPAT', 'CAL']
API_BASE_URL = "http://localhost:8000"  # Sửa nếu FastAPI chạy ở nơi khác
forecast_days = 7

# Khởi tạo session_state cho ngày tự động
if "auto_date" not in st.session_state:
    st.session_state.auto_date = today

# Sidebar bộ lọc
st.sidebar.header("Bộ lọc")
selected_state = st.sidebar.selectbox("Chọn bang", states)
auto_update = st.sidebar.checkbox("Tự động cập nhật ngày", key="auto_update")

selected_date = st.session_state.auto_date

# Tổng quan toàn bộ dữ liệu - KHÔNG phụ thuộc lọc bang
st.title("⚡ US Electricity & Forecast Dashboard")

# Gọi API dashboard_summary
params = {
    "date_filter": selected_date.isoformat(),
    "state": selected_state
}

try:
    response = requests.get(f"{API_BASE_URL}/dashboard_summary", params=params)
    print(response.content)
    if response.status_code == 200:
        data_summary = response.json()
        total_consumption = data_summary["total_consumption"]
        avg_temp = data_summary["avg_temperature"]
        avg_wind = data_summary["avg_wind_speed"]
        state_data = data_summary["state_consumption"]
    else:
        st.error(f"Lỗi gọi API dashboard_summary: {response.text} {selected_date.isoformat()}")
        total_consumption = avg_temp = avg_wind = 0
        state_data = []
except Exception as e:
    st.error(f"Lỗi kết nối API: {e}")
    total_consumption = avg_temp = avg_wind = 0
    state_data = []

# Hiển thị tổng quan
col1, col2, col3 = st.columns(3)
col1.metric("Tổng sản lượng (MWh)", f"{total_consumption:,.0f}")
col2.metric("Nhiệt độ TB (°C)", f"{avg_temp:.2f}")
col3.metric("Tốc độ gió TB (m/s)", f"{avg_wind:.2f}")

# Biểu đồ tiêu thụ & dự báo

response = requests.get(
    f"{API_BASE_URL}/get_forecast",
    params={"date_filter": selected_date.isoformat(), "state": selected_state}
)
if response.status_code == 200:
    print(response.content)
    data = response.json()
    df_merged = pd.DataFrame(data["forecast_results"])

    st.subheader(f"🔹 Tiêu thụ điện & Dự báo tại {selected_state} từ 7 ngày trước tới ngày {selected_date}")
    fig = px.line(df_merged, x="date", y="forecast_value", markers=True,
                  labels={"forecast_value": "Dự báo (MWh)", "date": "Ngày"},
                  title="Sản lượng điện dự báo")

    # Lọc bỏ ngày cuối cùng cho actual_value
    if df_merged["actual_value"].notna().any():
        df_filtered = df_merged.iloc[:-1]  # Loại bỏ hàng cuối cùng
        if df_filtered["actual_value"].notna().any():
            fig.add_scatter(x=df_filtered["date"], y=df_filtered["actual_value"],
                            mode="lines+markers", name="Thực tế", line=dict(color="green"))

    st.plotly_chart(fig, use_container_width=True)
# Phân tích theo bang
df_state = pd.DataFrame(state_data)
st.subheader(f"🔹 Sản lượng điện theo bang ngày {selected_date}")
fig2 = px.bar(df_state, x="region", y="value", color="region", text_auto=True)
st.plotly_chart(fig2, use_container_width=True)

# Phân tích theo nguồn
response = requests.get(
    f"{API_BASE_URL}/get_generation_by_fuel",
    params={"date_filter": selected_date.isoformat(), "state": selected_state}
)

if response.status_code == 200:

    data = response.json()  # Toàn bộ JSON
    df_source = pd.DataFrame(data["generation_results"])  # Chỉ lấy phần dữ liệu cần vẽ

    st.subheader(f"🔹 Sản lượng điện theo nguồn tại {selected_state} ngày {selected_date}")

    fig3 = px.pie(df_source, names="source", values="total_generation",
                title="Tỷ trọng sản lượng theo nguồn điện")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Không có dữ liệu cho ngày và bang đã chọn")

# Tự động tăng ngày sau mỗi 10 giây
if st.session_state.auto_update:
    time.sleep(10)
    st.session_state.auto_date += timedelta(days=1)
    st.rerun()
