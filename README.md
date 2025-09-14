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

## Hướng dẫn Triển khai (Deployment)

Dự án cung cấp hai kịch bản triển khai trong thư mục `deploy/`:

1.  **`backend/`**: Một API đơn giản để phục vụ dự báo.
2.  **`test/`**: Một hệ thống streaming dữ liệu thời gian thực hoàn chỉnh sử dụng Kafka để mô phỏng và kiểm thử.

### Kịch bản 1: API Đơn giản (Thư mục `backend`)

Đây là cách triển khai cơ bản nhất, cung cấp các endpoint API để truy vấn dự báo mà không cần đến Kafka.

**Luồng hoạt động:** Người dùng gửi yêu cầu HTTP -> Server FastAPI xử lý -> Trả kết quả trực tiếp.

**Cách chạy:**

1.  **Di chuyển đến thư mục `backend`:**
    ```bash
    cd deploy/backend
    ```

2.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install fastapi uvicorn pandas joblib numpy
    ```

3.  **Khởi chạy server FastAPI:**
    ```bash
    uvicorn main:app --reload --port 8000
    ```

4.  Server sẽ chạy tại `http://127.0.0.1:8000`. Bạn có thể truy cập `http://127.0.0.1:8000/docs` để xem tài liệu API và thử nghiệm.

### Kịch bản 2: Hệ thống Real-time với Kafka (Thư mục `test`)

Kịch bản này mô phỏng một pipeline xử lý dữ liệu thời gian thực hoàn chỉnh.

**Luồng hoạt động:**
`producer.py` (giả lập người dùng) -> `main.py` (API Server & Kafka Producer) -> `Kafka` (Message Broker) -> `consumer.py` (xử lý dữ liệu).

**Cách chạy (Yêu cầu 4 terminal riêng biệt):**

1.  **Terminal 1: Khởi chạy Hạ tầng**
    - **Yêu cầu:** Đã cài đặt Docker và Docker Compose.
    - **Lệnh:**
      ```bash
      cd deploy/test
      docker-compose up -d
      ```
    - **Mục đích:** Khởi chạy Zookeeper, Kafka, và Redis trong các container Docker.

2.  **Terminal 2: Khởi chạy API Server (và Kafka Producer)**
    - **Lệnh:**
      ```bash
      cd deploy/test
      # Cài đặt thư viện nếu cần
      pip install -r ../../requirements.txt 
      uvicorn main:app --reload --port 8001
      ```
    - **Mục đích:** Chạy server FastAPI. Server này vừa trả lời API, vừa gửi dữ liệu vào Kafka.

3.  **Terminal 3: Chạy Trình mô phỏng Người dùng**
    - **Lệnh:**
      ```bash
      cd deploy/test
      python producer.py
      ```
    - **Mục đích:** Script này sẽ liên tục gọi các API trên server (chạy ở Terminal 2) để tạo ra luồng dữ liệu.

4.  **Terminal 4: Chạy Trình xử lý Dữ liệu (Consumer)**
    - **Lệnh:**
      ```bash
      cd deploy/test
      python consumer.py
      ```
    - **Mục đích:** Lắng nghe dữ liệu từ các topic trên Kafka và in ra màn hình. Đây là nơi bạn thấy kết quả cuối cùng của pipeline.

### Dừng hệ thống `test`

Để dừng tất cả các container Docker đã khởi chạy, chạy lệnh sau trong thư mục `deploy/test`:
```bash
docker-compose down
```

## Các mô hình chính

-   LSTM (Long Short-Term Memory)
-   SARIMAX (Seasonal AutoRegressive Integrated Moving Average with eXogenous regressors)