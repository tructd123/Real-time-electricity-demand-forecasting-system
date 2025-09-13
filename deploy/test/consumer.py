from kafka import KafkaConsumer
import json
import pandas as pd
import numpy as np
import redis
import joblib
from pyspark.sql import SparkSession

# Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Spark session
spark = SparkSession.builder \
    .appName("ElectricDemandConsumer") \
    .getOrCreate()


df_respondents = spark.read.csv("all_respondents_feature_filtered.csv", header=True, inferSchema=True)
df_fuel = spark.read.csv("df_fuel.csv", header=True, inferSchema=True)


pdf_respondents = df_respondents.toPandas()
pdf_fuel = df_fuel.toPandas()
pdf_respondents["date"] = pd.to_datetime(pdf_respondents["date"]).dt.date
pdf_fuel["date"] = pd.to_datetime(pdf_fuel["period"]).dt.date

# Load model ML
models = joblib.load("ml_results.joblib")

fueltype_mapping = {
    "COL": "Coal", "HYD": "Hydro", "NG": "Natural Gas", "NUC": "Nuclear",
    "OTH": "Other", "OIL": "Petroleum", "SUN": "Solar", "WND": "Wind"
}

consumer = KafkaConsumer(
    'dashboard-request', 'forecast-request', 'generation-request',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='processing-group'
)

for msg in consumer:
    topic = msg.topic
    payload = msg.value
    request_id = payload.get("request_id")
    if not request_id:
        continue

    if topic == 'dashboard-request':
        date_filter = pd.to_datetime(payload['date']).date()
        states = payload.get('states', [])

        df_filtered = pdf_respondents[pdf_respondents["date"] == date_filter]
        if states:
            df_filtered = df_filtered[df_filtered["region"].isin(states)]

        result = {
            "date": str(date_filter),
            "total_consumption": float(df_filtered["value"].sum()),
            "avg_temperature": float(df_filtered["tavg"].mean()),
            "avg_wind_speed": float(df_filtered["wspd"].mean()),
            "state_consumption": df_filtered.groupby("region")["value"].sum().reset_index().to_dict(orient="records")
        }
        r.set(request_id, json.dumps(result), ex=60)

    elif topic == 'forecast-request':
        date_filter = pd.to_datetime(payload['date']).date()
        state = payload['state']

        model_data = models[state]['RandomForest']
        features = model_data['features']
        scaler = model_data['scaler']
        model = model_data['model']

        date_list = [date_filter - pd.Timedelta(days=i) for i in range(7, -2, -1)]
        results = []

        for day in date_list:
            sample = pdf_respondents[(pdf_respondents["date"] == day) & (pdf_respondents["respondent"] == state)]
            if sample.empty:
                results.append({"date": str(day), "forecast_value": None, "actual_value": None, "note": "No data"})
                continue

            test = sample[features].copy()
            target_scaled = sample['value'].iloc[0]
            test_scaled = scaler.transform(test)
            arr_new = test_scaled[:, 1:]

            prediction_scaled = model.predict(arr_new).flatten()[0] + np.random.uniform(-0.01, 0.01)
            dummy_forecast = np.zeros((1, test_scaled.shape[1]))
            dummy_forecast[0, 1:] = arr_new[0]
            dummy_forecast[0, 0] = prediction_scaled
            forecast_value = scaler.inverse_transform(dummy_forecast)[0, 0]

            results.append({
                "date": str(day),
                "forecast_value": float(forecast_value),
                "actual_value": float(target_scaled)
            })

        output = {"state": state, "date_filter": payload['date'], "forecast_results": results}
        r.set(request_id, json.dumps(output), ex=60)

    elif topic == 'generation-request':
        date_filter = pd.to_datetime(payload['date']).date()
        state = payload['state']

        df_filtered = pdf_fuel[(pdf_fuel["date"] == date_filter) & (pdf_fuel["respondent"] == state)]

        if df_filtered.empty:
            result = {"message": "No data", "state": state, "date": payload['date']}
        else:
            df_source = df_filtered.groupby("fueltype")["value"].sum().reset_index()
            df_source["fueltype"] = df_source["fueltype"].map(fueltype_mapping).fillna(df_source["fueltype"])
            df_source = df_source.rename(columns={"fueltype": "source", "value": "total_generation"})
            df_source["total_generation"] = df_source["total_generation"].astype(float)

            result = {
                "state": state,
                "date_filter": payload['date'],
                "generation_results": df_source.to_dict(orient="records")
            }
        r.set(request_id, json.dumps(result), ex=60)
