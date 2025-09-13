from fastapi import FastAPI, Query
from typing import List, Optional
from datetime import date, timedelta
import pandas as pd
import joblib
import numpy as np
import json
from kafka import KafkaProducer
from fastapi.responses import JSONResponse

app = FastAPI()

# Danh sách bang
states_final = ['AEC', 'AECI', 'AVA', 'AZPS', 'BANC', 'BPAT', 'CAL']

# Đọc dữ liệu cần thiết
data = joblib.load('ml_results.joblib')
df_respondents = pd.read_csv("all_respondents_feature_filtered.csv")
df_fuel = pd.read_csv("df_fuel.csv")

# Xử lý định dạng ngày tháng
df_respondents["date"] = pd.to_datetime(df_respondents["date"]).dt.date
df_fuel["date"] = pd.to_datetime(df_fuel["period"]).dt.date

# Mapping nguồn năng lượng
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

# Khởi tạo Kafka Producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


@app.get("/dashboard_summary")
def get_dashboard_summary(date_filter: date, states: Optional[List[str]] = Query(default=[])):
    """
    Trả về KPI tổng quan & sản lượng điện theo bang, chỉ tính trong ngày cụ thể.
    Đồng thời gửi dữ liệu vào Kafka topic 'dashboard-topic'.
    """
    df_filtered = df_respondents[df_respondents["date"] == date_filter]
    if states:
        df_filtered = df_filtered[df_filtered["region"].isin(states)]

    total_consumption = df_filtered["value"].sum()
    avg_temp = df_filtered["tavg"].mean()
    avg_wind = df_filtered["wspd"].mean()

    df_state = df_filtered.groupby("region")["value"].sum().reset_index()
    state_data = df_state.to_dict(orient="records")

    for item in state_data:
        for k, v in item.items():
            if isinstance(v, (np.integer, np.floating)):
                item[k] = v.item()

    result = {
        "date": str(date_filter),
        "total_consumption": float(total_consumption),
        "avg_temperature": float(avg_temp),
        "avg_wind_speed": float(avg_wind),
        "state_consumption": state_data
    }

    # Gửi dữ liệu vào Kafka
    producer.send('dashboard-topic', value=result)
    producer.flush()

    return result


@app.get("/get_forecast")
def get_forecast(date_filter: date, state: str):
    """
    Dự báo sản lượng điện, gửi kết quả vào Kafka topic 'forecast-topic'.
    """
    date_list = [date_filter - timedelta(days=i) for i in range(7, -2, -1)]
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

        test = sample[features].copy()
        target_scaled = sample['value'].iloc[0]
        test_scaled = scaler.transform(test)
        arr_new = test_scaled[:, 1:]

        prediction_scaled = model.predict(arr_new).flatten()[0]
        x = np.random.uniform(-0.01, 0.01)

        prediction_scaled+=x
        dummy_forecast = np.zeros((1, test_scaled.shape[1]))
        dummy_forecast[0, 1:] = arr_new[0]
        dummy_forecast[0, 0] = prediction_scaled

        forecast_value = scaler.inverse_transform(dummy_forecast)[0, 0]

        results.append({
            "date": str(day),
            "forecast_value": float(forecast_value),
            "actual_value": float(target_scaled)
        })

    output = {
        "state": state,
        "date_filter": str(date_filter),
        "forecast_results": results
    }

    producer.send('forecast-topic', value=output)
    producer.flush()

    return output


@app.get("/get_generation_by_fuel")
def get_generation_by_fuel(date_filter: date, state: str):
    """
    Trả về sản lượng điện theo nguồn, gửi kết quả vào Kafka topic 'generation-topic'.
    """
    df_filtered = df_fuel[
        (df_fuel["date"] == date_filter) &
        (df_fuel["respondent"] == state)
    ]

    if df_filtered.empty:
        return JSONResponse(content={"message": "Không có dữ liệu cho ngày và bang này"}, status_code=404)

    df_source = df_filtered.groupby("fueltype")["value"].sum().reset_index()
    df_source["fueltype"] = df_source["fueltype"].map(fueltype_mapping).fillna(df_source["fueltype"])
    df_source = df_source.rename(columns={"fueltype": "source", "value": "total_generation"})
    df_source["total_generation"] = df_source["total_generation"].astype(float)

    generation_data = df_source.to_dict(orient="records")

    output = {
        "state": state,
        "date_filter": str(date_filter),
        "generation_results": generation_data
    }

    producer.send('generation-topic', value=output)
    producer.flush()

    return JSONResponse(content=generation_data)
