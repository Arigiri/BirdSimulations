# Hướng Dẫn Tích Hợp Module Thời Tiết và Hiển Thị Nhiệt Độ

## Phương Pháp Tiếp Cận
Tích hợp module thời tiết vào mô phỏng chim để hiển thị và truy cập dữ liệu nhiệt độ tại các vị trí trong bản đồ, sử dụng phương pháp từng bước, kiểm tra mỗi bước trước khi tiến hành bước tiếp theo.

## Bước 1: Kiểm Tra Cấu Trúc Thư Mục và Module Hiện Có

### Xác nhận cấu trúc thư mục
```
├── model/
│   ├── weather/
│   │   ├── main/
│   │   │   └── weather_integration.py
│   │   └── python/
│   │       └── visualization/
│   │           └── heatmap_renderer.py
```

### Kiểm tra các module và phương thức
- [ ] Xác minh file `model/weather/main/weather_integration.py` tồn tại
- [ ] Xác minh class `WeatherIntegration` và các phương thức của nó
- [ ] Kiểm tra file `model/weather/python/visualization/heatmap_renderer.py`

## Bước 2: Phục Hồi Import Module Thời Tiết

```python
# Thử import module thời tiết, nếu không được thì bỏ qua
try:
    from model.weather.main.weather_integration import WeatherIntegration
    import numpy as np
    WEATHER_AVAILABLE = True
except ImportError as e:
    try:
        print(f"Không thể import module thời tiết: {e}")
    except UnicodeEncodeError:
        print("Khong the import module thoi tiet")
    WEATHER_AVAILABLE = False
```

## Bước 3: Phục Hồi Khởi Tạo Module Thời Tiết

```python
# Biến toàn cục
weather_integration = None

# Trong hàm main()
if WEATHER_AVAILABLE:
    try:
        weather_integration = WeatherIntegration(WINDOW_WIDTH, WINDOW_HEIGHT)
        try:
            print("Module thời tiết đã được khởi tạo thành công!")
        except UnicodeEncodeError:
            print("Module thoi tiet da duoc khoi tao thanh cong!")
    except Exception as e:
        try:
            print(f"Không thể khởi tạo module thời tiết: {e}")
        except UnicodeEncodeError:
            print("Khong the khoi tao module thoi tiet")
        weather_integration = None
```

## Bước 4: Kiểm Tra Module Đã Hoạt Động

```python
# Thêm vào hàm update()
if weather_integration:
    weather_integration.update(dt)
    
    # Kiểm tra in ra giá trị nhiệt độ tại một vị trí để xác nhận module hoạt động
    try:
        temp = weather_integration.get_temperature_at_position(100, 100)
        print(f"Nhiệt độ tại (100,100): {temp}")
    except Exception as e:
        print(f"Lỗi khi lấy nhiệt độ: {e}")
```

## Bước 5: Lấy Dữ Liệu Nhiệt Độ

### Xác minh các phương thức hiện có
- [ ] Kiểm tra xem `WeatherIntegration` có phương thức `get_temperature_at_position(x, y)` không
- [ ] Kiểm tra xem `WeatherIntegration` có phương thức `get_temperature_field()` không

### Nếu chưa có, cần thêm vào lớp WeatherIntegration
```python
def get_temperature_at_position(self, x, y):
    """Lấy nhiệt độ tại tọa độ (x, y)"""
    if self.temperature_field is None:
        return None
    
    # Chuyển đổi từ tọa độ màn hình sang tọa độ lưới
    grid_width = self.temperature_field.shape[1]
    grid_height = self.temperature_field.shape[0]
    
    grid_x = int((x / (self.window_width - INFO_PANEL_WIDTH)) * grid_width)
    grid_y = int((y / self.window_height) * grid_height)
    
    # Đảm bảo tọa độ grid nằm trong khoảng hợp lệ
    grid_x = max(0, min(grid_x, grid_width - 1))
    grid_y = max(0, min(grid_y, grid_height - 1))
    
    return self.temperature_field[grid_y, grid_x]
```

## Bước 6: Thêm Hiển Thị Bản Đồ Nhiệt Độ

### Các biến trạng thái
```python
# Thêm vào biến toàn cục
show_temperature_map = False  # Bật/tắt hiển thị bản đồ nhiệt độ
```

### Xử lý phím
```python
@window.event
def on_key_press(symbol, modifiers):
    global paused, show_weather, show_temperature_map
    
    # Các xử lý phím khác...
    
    elif symbol == key.T:
        # Bật/tắt hiển thị bản đồ nhiệt độ
        if weather_integration:
            show_temperature_map = not show_temperature_map
            try:
                print(f"Bản đồ nhiệt độ: {'Hiện' if show_temperature_map else 'Ẩn'}")
            except UnicodeEncodeError:
                print(f"Ban do nhiet do: {'Hien' if show_temperature_map else 'An'}")
```

### Vẽ bản đồ nhiệt độ với wrap-around
```python
def draw_temperature_map():
    """Vẽ bản đồ nhiệt độ với khả năng wrap-around khi vượt quá kích thước màn hình"""
    if not weather_integration:
        return
        
    # Lấy dữ liệu nhiệt độ
    temp_array = weather_integration.get_temperature_field()
    if temp_array is None:
        return
    
    # Lấy kích thước mảng nhiệt độ
    grid_height, grid_width = temp_array.shape
    
    # Xác định kích thước của mỗi ô trên màn hình
    cell_width = (WINDOW_WIDTH - INFO_PANEL_WIDTH) / grid_width
    cell_height = WINDOW_HEIGHT / grid_height
    
    # Lấy phạm vi nhiệt độ - cần kiểm tra nếu thuộc tính tồn tại
    try:
        min_temp = weather_integration.min_temp
        max_temp = weather_integration.max_temp
    except AttributeError:
        # Tính min/max từ dữ liệu nếu không có sẵn
        min_temp = np.min(temp_array)
        max_temp = np.max(temp_array)
    
    # Độ mờ của bản đồ nhiệt
    opacity = 150  # Giá trị từ 0-255, với 0 là hoàn toàn trong suốt
    
    # Vẽ các ô nhiệt độ với wrap-around
    for y in range(grid_height):
        for x in range(grid_width):
            # Tính toán vị trí thực tế trên màn hình
            screen_x = x * cell_width
            screen_y = y * cell_height
            
            # Áp dụng wrap-around khi vượt quá biên màn hình
            if screen_x >= WINDOW_WIDTH - INFO_PANEL_WIDTH:
                overflow_x = screen_x - (WINDOW_WIDTH - INFO_PANEL_WIDTH)
                screen_x = overflow_x
            
            if screen_y >= WINDOW_HEIGHT:
                overflow_y = screen_y - WINDOW_HEIGHT
                screen_y = overflow_y
                
            # Lấy giá trị nhiệt độ tại vị trí (x, y)
            temperature = temp_array[y, x]
            
            # Chuẩn hóa nhiệt độ về khoảng [0, 1]
            temp_range = max_temp - min_temp
            if temp_range == 0:  # Tránh chia cho 0
                normalized_temp = 0.5
            else:
                normalized_temp = max(0, min(1, (temperature - min_temp) / temp_range))
            
            # Ánh xạ từ nhiệt độ sang màu sắc (dùng cơ chế gradient)
            if normalized_temp < 0.25:  # Màu xanh -> xanh lá
                r = 0
                g = int(255 * (normalized_temp / 0.25))
                b = int(255 * (1 - normalized_temp / 0.25))
            elif normalized_temp < 0.5:  # Màu xanh lá -> vàng
                r = int(255 * ((normalized_temp - 0.25) / 0.25))
                g = 255
                b = 0
            elif normalized_temp < 0.75:  # Màu vàng -> cam
                r = 255
                g = int(255 * (1 - (normalized_temp - 0.5) / 0.25))
                b = 0
            else:  # Màu cam -> đỏ
                r = 255
                g = 0
                b = int(255 * ((normalized_temp - 0.75) / 0.25))
            
            # Vẽ hình chữ nhật biểu diễn nhiệt độ
            rect = pyglet.shapes.Rectangle(
                x=screen_x, 
                y=screen_y,
                width=cell_width,
                height=cell_height,
                color=(r, g, b)
            )
            rect.opacity = opacity
            rect.draw()
```

### Thêm gọi hàm trong on_draw
```python
@window.event
def on_draw():
    # Các code khác...
    
    # Vẽ bản đồ nhiệt độ nếu được bật
    if show_temperature_map and weather_integration:
        draw_temperature_map()
    
    # Tiếp tục các code khác...
```

## Bước 7: Hiển Thị Thông Tin Nhiệt Độ Tại Vị Trí Chim

```python
# Khi hiển thị thông tin chi tiết chim
if selected_bird and weather_integration:
    try:
        bird_x, bird_y = selected_bird.position.x, selected_bird.position.y
        temperature = weather_integration.get_temperature_at_position(bird_x, bird_y)
        if temperature is not None:
            bird_info_text += f"Nhiệt độ: {temperature:.1f}°C\n"
    except Exception as e:
        print(f"Lỗi khi lấy nhiệt độ tại vị trí chim: {e}")
```

## Bước Kiểm Tra và Xử Lý Sự Cố

### Kiểm tra thư mục
- [ ] Kiểm tra tất cả các đường dẫn có chính xác: `model/weather/main/weather_integration.py` và `model/weather/python/visualization/heatmap_renderer.py`

### Kiểm tra API
- [ ] Kiểm tra các phương thức của `WeatherIntegration` bằng cách in ra `dir(weather_integration)`
- [ ] Kiểm tra nhiệt độ có được trả về đúng từ `get_temperature_at_position()`

### Lỗi encoding tiếng Việt
- [ ] Đảm bảo tất cả các lệnh `print` với tiếng Việt đều có khối `try-except` để xử lý `UnicodeEncodeError`

### Kiểm tra rendering
- [ ] Kiểm tra xem bản đồ nhiệt độ có hiển thị đúng không
- [ ] Điều chỉnh `opacity` nếu bản đồ nhiệt quá rõ hoặc quá mờ

## Lưu Ý Quan Trọng

1. **Kiểm tra từng bước**: Cần triển khai và kiểm tra từng bước trước khi tiến hành bước tiếp theo
2. **Phương thức không tồn tại**: Nếu phương thức như `get_temperature_at_position()` không tồn tại, cần tự triển khai
3. **Điều chỉnh tọa độ**: Cần chú ý chuyển đổi giữa tọa độ màn hình và tọa độ lưới thời tiết
4. **Xử lý ngoại lệ**: Bọc các lệnh có thể gây lỗi trong khối try-except
5. **Kiểm tra NULL**: Luôn kiểm tra `weather_integration is not None` và `WEATHER_AVAILABLE` trước khi sử dụng

Thực hiện các bước theo thứ tự, kiểm tra kỹ mỗi bước trước khi tiếp tục.
