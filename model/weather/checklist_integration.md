# Checklist Tích hợp Module Weather C++ vào Dự án Chính

## Mục tiêu
Thay thế mô hình weather dựa trên Python hiện tại bằng module C++ đã biên dịch (`cpp_weather.pyd`) và tích hợp nó vào vòng lặp chính và hệ thống render của dự án (sử dụng Pyglet).

## Các Bước Thực Hiện

### Phần 1: Chuẩn bị và Cấu hình

-   [ ] **1. Xác nhận Import Module C++:**
    -   Đảm bảo file `cpp_weather.cp310-win_amd64.pyd` nằm ở vị trí có thể truy cập (ví dụ: `model/weather/python/`).
    -   Kiểm tra file `model/weather/python/cpp_weather_interface.py` (nếu có) để hiểu cách nó wrap các lớp C++.
    -   Trong `model/weather/main/weather_integration.py`, thêm code để import thành công các lớp `Solver`, `TemperatureField`, `WindField` (và các enum/const cần thiết) từ module C++. Xử lý `ImportError` nếu không tìm thấy.
-   [ ] **2. Hợp nhất Cấu hình:**
    -   Xem xét các tham số trong `model/weather/config/weather_config.py`.
    -   Đảm bảo các giá trị cấu hình cần thiết cho module C++ (kích thước lưới, dx, kappa ban đầu, etc.) được định nghĩa và sử dụng khi khởi tạo các đối tượng C++ trong `WeatherIntegration`.

### Phần 2: Cập nhật Lớp Tích hợp (`WeatherIntegration`)

-   [ ] **3. Sử dụng Đối tượng C++:**
    -   Trong `WeatherIntegration.__init__`:
        -   Xóa bỏ việc tạo instance của các lớp weather Python (nếu có).
        -   Tạo instance của các lớp C++: `Solver`, `TemperatureField`, `WindField` từ module đã import.
        -   Lưu trữ các instance C++ này làm thuộc tính của `WeatherIntegration`.
-   [ ] **4. Triển khai Logic `update`:**
    -   Trong `WeatherIntegration.update(dt)`:
        -   Triển khai logic tương tự hàm `step()` trong `realtime_simulation.py`.
        -   **Quan trọng:** Quyết định cách gọi solver C++:
            -   *Ưu tiên:* Nếu solver C++ có hàm `update` hoặc `step` hoạt động trực tiếp trên các đối tượng `TemperatureField`/`WindField` của nó, hãy gọi hàm đó.
            -   *Cách khác:* Nếu cần lấy/đặt dữ liệu NumPy, hãy gọi các phương thức `get_temperature`, `get_wind_x/y` từ đối tượng C++, gọi `solver.solve_rk4_step` (hoặc tương tự), rồi gọi `set_temperature` để cập nhật lại đối tượng C++.
        -   Sử dụng `dt` được truyền vào từ `main.py` (thay vì tính toán CFL trong Python, trừ khi API C++ yêu cầu).
        -   Thêm logic cập nhật trường gió định kỳ (`wind_field.generate_gaussian_field`).
        -   Cập nhật `self.time` và `self.steps`.
        -   Gọi `self.update_statistics()` định kỳ.
-   [ ] **5. Cập nhật Phương thức Lấy Dữ liệu:**
    -   Trong `WeatherIntegration.get_temperature_at(screen_x, screen_y)`: Chuyển đổi tọa độ màn hình sang chỉ số lưới và gọi phương thức tương ứng của đối tượng `TemperatureField` C++ (ví dụ: `get_temp_at_index`).
    -   Trong `WeatherIntegration.get_weather_for_birds(x, y)`: Tương tự, lấy nhiệt độ và gió (vx, vy) từ các đối tượng C++ tại chỉ số lưới tương ứng.
    -   Trong `WeatherIntegration.update_statistics()`: Gọi các phương thức `get_min_temp`, `get_max_temp`, `get_mean_temp` của đối tượng `TemperatureField` C++.
-   [ ] **6. Triển khai Khởi tạo Mẫu:**
    -   Trong `WeatherIntegration.initialize_with_pattern(pattern_type)`: Gọi các phương thức tương ứng của đối tượng `TemperatureField` C++ để thiết lập mẫu (ví dụ: `set_uniform`, `add_heat_source`, `set_gradient`, `set_checkerboard`, `set_random`).
-   [ ] **7. Triển khai Điều khiển Mô phỏng:**
    -   Trong `WeatherIntegration.start()`, `stop()`, `reset()`: Cập nhật trạng thái `self.is_running` và gọi các hàm khởi tạo/reset cần thiết (như `initialize_with_pattern`).
    -   Trong `WeatherIntegration.set_thermal_diffusivity(kappa)`: Gọi phương thức `set_kappa` của đối tượng `Solver` C++.

### Phần 3: Cập nhật Visualization và UI

-   [ ] **8. Điều chỉnh Renderers (`HeatmapRenderer`, `WindFieldRenderer`):**
    -   Trong `__init__`: Đảm bảo chúng có thể nhận các đối tượng `TemperatureField`, `WindField` C++ (thông qua `WeatherIntegration`).
    -   Trong `draw()`:
        -   Gọi các phương thức `get_temperature()`, `get_wind_x()`, `get_wind_y()` từ các đối tượng C++ được lưu trữ để lấy dữ liệu NumPy.
        -   Sử dụng dữ liệu NumPy này để vẽ bằng `pyglet.shapes` như bình thường.
        -   Đảm bảo `HeatmapRenderer` sử dụng đúng `min_temp`, `max_temp` (có thể lấy từ `self.statistics` của `WeatherIntegration` hoặc dùng giá trị cố định).
-   [ ] **9. Điều chỉnh UI Controls (`WeatherControls`):**
    -   Trong `__init__`: Đảm bảo nó nhận instance của `WeatherIntegration`.
    -   Trong các hàm xử lý sự kiện (ví dụ: khi nhấn nút, kéo thanh trượt):
        -   Gọi các phương thức tương ứng trên instance `WeatherIntegration` để tương tác với module C++ (ví dụ: `weather_integration.set_thermal_diffusivity(new_value)`, `weather_integration.initialize_with_pattern('gradient')`).

### Phần 4: Tích hợp vào Vòng lặp Chính (`main.py`)

-   [ ] **10. Khởi tạo `WeatherIntegration`:**
    -   Trong hàm `main()` hoặc nơi khởi tạo chính, tạo một instance của `WeatherIntegration`.
-   [ ] **11. Gọi `update` trong Vòng lặp Chính:**
    -   Trong hàm `update(dt)` của `main.py`, gọi `weather_integration.update(dt)`.
-   [ ] **12. Gọi `draw` và `draw_ui` trong `on_draw`:**
    -   Trong hàm `on_draw()` của `main.py`:
        -   Gọi `weather_integration.draw()` để vẽ heatmap và gió (nếu bật).
        -   Gọi `weather_integration.draw_ui()` để vẽ panel điều khiển.
-   [ ] **13. Chuyển tiếp Sự kiện:**
    -   Trong các hàm xử lý sự kiện của `main.py` (`on_key_press`, `on_mouse_motion`, `on_mouse_press`):
        -   Gọi các phương thức xử lý sự kiện tương ứng của `weather_integration` (ví dụ: `weather_integration.on_key_press(symbol, modifiers)`).
        -   Kiểm tra giá trị trả về để xem sự kiện đã được xử lý bởi module weather hay chưa.
-   [ ] **14. Sử dụng Dữ liệu Weather:**
    -   Trong `main.py` hoặc các module khác (ví dụ: `bird.py`), gọi các phương thức của `weather_integration` để lấy thông tin thời tiết khi cần (ví dụ: `weather_integration.get_weather_for_birds(bird.position.x, bird.position.y)`).

### Phần 5: Kiểm thử và Tinh chỉnh

-   [ ] **15. Kiểm tra Chức năng:**
    -   Chạy ứng dụng và kiểm tra xem mô phỏng thời tiết có hoạt động đúng không.
    -   Kiểm tra các điều khiển UI (start/stop, reset, thay đổi mẫu, thanh trượt).
    -   Kiểm tra hiển thị heatmap và gió.
-   [ ] **16. Kiểm tra Hiệu suất:**
    -   So sánh hiệu suất với phiên bản Python thuần túy (nếu có).
    -   Sử dụng profiler nếu cần để xác định các điểm nghẽn.
-   [ ] **17. Xử lý Lỗi:**
    -   Kiểm tra log để tìm lỗi import hoặc lỗi runtime từ module C++.
    -   Thêm các khối `try...except` cần thiết.
-   [ ] **18. Dọn dẹp Code:**
    -   Xóa bỏ các lớp và hàm weather Python không còn sử dụng.
    -   Cập nhật tài liệu (README, docstrings) để phản ánh việc sử dụng module C++.
