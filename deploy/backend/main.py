from fastapi import FastAPI, Query
from typing import List, Optional
from datetime import date, timedelta
import pandas as pd
import joblib
import numpy as np
from fastapi.responses import JSONResponse
app = FastAPI()
states_final =['AEC' ,'AECI' ,'AVA' , 'AZPS' ,'BANC', 'BPAT','CAL']
# Đọc file joblib
# data = joblib.load('all_models_bundle.joblib')
data = joblib.load('ml_results.joblib')
# Load dữ liệu đã tổng hợp
df_respondents = pd.read_csv("all_respondents_feature_filtered.csv")
df_fuel = pd.read_csv("df_fuel.csv") 
# Đảm bảo cột date có định dạng datetime.date
df_respondents["date"] = pd.to_datetime(df_respondents["date"]).dt.date
df_fuel["date"] = pd.to_datetime(df_fuel["period"]).dt.date

fueltype_mapping = {
    "COL": "Coal",
    "HYD": "Hydro",
    "NG": "Natural Gas",
    "NUC": "Nuclear",
    "OTH": "Other",
    "OIL": "Petroleum",
    "SUN": "Solar",
    "WND": "Wind"
}

@app.get("/dashboard_summary")
def get_dashboard_summary(
    date_filter: date, 
    states: Optional[List[str]] = Query(default=[])
):
    """
    Trả về KPI tổng quan & sản lượng điện theo bang, chỉ tính trong ngày cụ thể.
    """
    # Lọc theo ngày
    df_filtered = df_respondents[df_respondents["date"] == date_filter]

    # Lọc theo bang nếu có
    if states:
        df_filtered = df_filtered[df_filtered["region"].isin(states)]

    # Tổng sản lượng
    total_consumption = df_filtered["value"].sum()

    # Tỷ lệ tái tạo

    # Thời tiết trung bình
    avg_temp = df_filtered["tavg"].mean()
    avg_wind = df_filtered["wspd"].mean()

    # Sản lượng điện theo bang
    df_state = df_filtered.groupby("region")["value"].sum().reset_index()
    state_data = df_state.to_dict(orient="records")

    # Ép kiểu toàn bộ giá trị về dạng Python chuẩn để tránh lỗi JSON encode
    for item in state_data:
        for k, v in item.items():
            if isinstance(v, (np.integer, np.floating)):
                item[k] = v.item()
    print(state_data)
    return {
        "date": str(date_filter),
        "total_consumption": float(total_consumption),
        "avg_temperature": float(avg_temp) ,
        "avg_wind_speed": float(avg_wind) ,
        "state_consumption": state_data
    }

@app.get("/get_forecast")
def get_forecast(
    date_filter: date, 
    state: str
):
    # Tạo danh sách: 7 ngày trước + ngày hiện tại + ngày mai
    date_list = [date_filter - timedelta(days=i) for i in range(7, -2, -1)]  # từ ngày -7 tới +1

    # Lấy thông tin mô hình, scaler và features
    features = data[state]['RandomForest']['features']
    scaler = data[state]['RandomForest']['scaler']
    model = data[state]['RandomForest']['model']

    results = []

    for day in date_list:
        sample = df_respondents[
            (df_respondents["date"] == day) & 
            (df_respondents["respondent"] == state)
        ].copy()

        if sample.empty:
            results.append({
                "date": str(day),
                "forecast_value": None,
                "actual_value": None,
                "note": "No data for this date"
            })
            continue

                # Chuẩn bị dữ liệu
        test = sample[features].copy()
        target_scaled = sample['value'].iloc[0]  # Giá trị thực tế đã scale
        test_scaled = scaler.transform(test)
        arr_new = test_scaled[:, 1:]  # Loại cột 'value'

        # Dự đoán
        input_for_model = arr_new
        prediction_scaled = model.predict(input_for_model).flatten()[0]
        print(target_scaled)
        # Chuẩn bị dummy để inverse transform
        dummy_forecast = np.zeros((1, test_scaled.shape[1]))
        dummy_forecast[0, 1:] = arr_new[0]
        dummy_forecast[0, 0] = prediction_scaled

        forecast_value = scaler.inverse_transform(dummy_forecast)[0, 0]

        # Dummy cho actual_valu
        results.append({
            "date": str(day),
            "forecast_value": float(forecast_value),
            "actual_value": float(target_scaled)
        })

    return {
        "state": state,
        "date_filter": str(date_filter),
        "forecast_results": results
    }

@app.get("/get_generation_by_fuel")
def get_generation_by_fuel(date_filter: date, state: str):
    """
    Trả về tổng sản lượng điện theo từng nguồn năng lượng,
    lọc theo cột 'period' và mã vùng (respondent).
    """
    df_filtered = df_fuel[df_fuel["date"] == date_filter]
    df_filtered = df_filtered[df_filtered["respondent"] == state]
    # Lọc dữ liệu theo period và respondent
    print(df_filtered)

    if df_filtered.empty:
        return JSONResponse(content={"message": "Không có dữ liệu cho ngày và bang này"}, status_code=404)

    # Group theo nguồn năng lượng
    df_source = df_filtered.groupby("fueltype")["value"].sum().reset_index()

    # Mapping tên đầy đủ
    df_source["fueltype"] = df_source["fueltype"].map(fueltype_mapping).fillna(df_source["fueltype"])

    df_source = df_source.rename(columns={"fueltype": "source", "value": "total_generation"})

    # Ép kiểu đảm bảo sạch dữ liệu
    df_source["total_generation"] = df_source["total_generation"].astype(float)

    return JSONResponse(content=df_source.to_dict(orient="records"))