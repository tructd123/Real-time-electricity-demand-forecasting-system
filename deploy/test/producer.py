from fastapi import FastAPI, Query
from typing import Optional, List
from datetime import date
from kafka import KafkaProducer
import redis
import json
import uuid
import time
from fastapi.responses import JSONResponse

app = FastAPI()

# Khởi tạo Kafka Producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Kết nối Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Hàm hỗ trợ đợi kết quả từ Redis
def wait_for_result(request_id, timeout=10):
    """
    Đợi kết quả từ Redis với timeout giây.
    """
    for _ in range(timeout * 10):
        res = r.get(request_id)
        if res:
            return json.loads(res)
        time.sleep(0.1)
    return {"message": "Timeout: Không nhận được kết quả từ backend"}

# --------- Các API gửi & nhận ----------

@app.get("/dashboard_summary")
def request_dashboard(date_filter: date, states: Optional[List[str]] = Query(default=[])):
    request_id = str(uuid.uuid4())
    payload = {
        "date": str(date_filter),
        "states": states,
        "request_id": request_id
    }
    producer.send('dashboard-request', value=payload)
    producer.flush()

    result = wait_for_result(request_id)
    return JSONResponse(content=result)


@app.get("/get_forecast")
def request_forecast(date_filter: date, state: str):
    request_id = str(uuid.uuid4())
    payload = {
        "date": str(date_filter),
        "state": state,
        "request_id": request_id
    }
    producer.send('forecast-request', value=payload)
    producer.flush()

    result = wait_for_result(request_id)
    return JSONResponse(content=result)


@app.get("/get_generation_by_fuel")
def request_generation(date_filter: date, state: str):
    request_id = str(uuid.uuid4())
    payload = {
        "date": str(date_filter),
        "state": state,
        "request_id": request_id
    }
    producer.send('generation-request', value=payload)
    producer.flush()

    result = wait_for_result(request_id)
    return JSONResponse(content=result)
