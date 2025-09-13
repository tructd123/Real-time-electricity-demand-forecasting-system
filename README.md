# Dự án Phân tích và Dự báo Năng lượng

Dự án này thu thập, phân tích và dự báo dữ liệu năng lượng và thời tiết bằng các mô hình học máy (LSTM, SARIMAX) để dự đoán nhu cầu năng lượng.

## Cấu trúc dự án

-   **Notebooks (`.ipynb`):**
    -   `collect_*.ipynb`: Thu thập dữ liệu.
    -   `DQ.ipynb`: Làm sạch và tiền xử lý dữ liệu.
    -   `Visualize.ipynb`: Trực quan hóa dữ liệu.
    -   `LSTM_ML.ipynb` & `trainsarimax.ipynb`: Huấn luyện mô hình dự báo.
-   **`data/`**: Chứa dữ liệu thô và đã được feature engineering.
-   **`deploy/`**:
    -   `app.py`: Giao diện người dùng (Streamlit).
    -   `backend/main.py`: API dự báo (FastAPI).
    -   `test/`: Kịch bản kiểm thử streaming với Kafka và Redis (`docker-compose.yml`).
-   **`requirements.txt`**: Danh sách các thư viện cần thiết.

## Cách chạy dự án

1.  **Cài đặt thư viện:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Chạy Notebooks:** Thực thi các tệp `.ipynb` để xử lý dữ liệu và huấn luyện mô hình.
3.  **Triển khai (Tùy chọn):**
    -   Khởi chạy backend: `uvicorn deploy.backend.main:app --reload`
    -   Khởi chạy frontend: `streamlit run deploy/app.py`
    -   Sử dụng `docker-compose up` trong `deploy/test/` để chạy môi trường Kafka/Redis.

## Các mô hình chính

-   LSTM (Long Short-Term Memory)
-   SARIMAX (Seasonal AutoRegressive Integrated Moving Average with eXogenous regressors)
