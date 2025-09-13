# Dự án Phân tích và Dự báo Năng lượng

Dự án này tập trung xây dựng một hệ thống dự báo nhu cầu điện theo thời gian thực. Toàn bộ quy trình bao gồm: thu thập dữ liệu về sản lượng điện và yếu tố thời tiết, làm sạch và tiền xử lý dữ liệu, sau đó áp dụng cả mô hình học sâu (LSTM) và mô hình thống kê (SARIMAX) để tạo ra các dự báo chính xác.

Điểm đặc biệt của hệ thống là sự kết hợp giữa các công nghệ dữ liệu lớn và các mô hình phân tích tiên tiến. Trong đó, Apache Kafka được sử dụng để xử lý luồng dữ liệu liên tục, trong khi Redis hỗ trợ lưu trữ kết quả tạm thời nhằm tối ưu tốc độ truy xuất. Phần kết quả dự báo được triển khai thông qua API backend (FastAPI) và một giao diện trực quan với Streamlit, giúp người dùng dễ dàng theo dõi, kiểm tra và truy vấn thông tin dự báo trong thời gian thực.

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
