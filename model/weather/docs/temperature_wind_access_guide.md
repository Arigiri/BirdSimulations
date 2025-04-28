# Truy xuất và Tùy chỉnh Dữ liệu Nhiệt độ & Gió

Tài liệu này mô tả chi tiết cách truy xuất thông tin nhiệt độ và gió tại các điểm cụ thể, cũng như cách tùy chỉnh điều kiện nhiệt độ ban đầu trong module mô phỏng thời tiết.

## Mục lục

- [Truy xuất Dữ liệu Nhiệt độ và Gió](#truy-xuất-dữ-liệu-nhiệt-độ-và-gió)
  - [Truy cập Nhiệt độ tại Điểm Cụ thể](#truy-cập-nhiệt-độ-tại-điểm-cụ-thể)
  - [Truy cập Thông tin Gió tại Điểm Cụ thể](#truy-cập-thông-tin-gió-tại-điểm-cụ-thể)
  - [Ví dụ Sử dụng](#ví-dụ-sử-dụng)
- [Tùy chỉnh Điều kiện Nhiệt độ Ban đầu](#tùy-chỉnh-điều-kiện-nhiệt-độ-ban-đầu)
  - [Tùy chỉnh Gradient Nhiệt độ](#tùy-chỉnh-gradient-nhiệt-độ)
  - [Thêm Nguồn Nhiệt Tùy chỉnh](#thêm-nguồn-nhiệt-tùy-chỉnh)
  - [Tạo Mô hình Nhiệt độ Phức tạp](#tạo-mô-hình-nhiệt-độ-phức-tạp)
  - [Tải Dữ liệu Nhiệt độ từ Nguồn Bên ngoài](#tải-dữ-liệu-nhiệt-độ-từ-nguồn-bên-ngoài)
- [Phương thức API](#phương-thức-api)
- [Mở rộng và Tích hợp](#mở-rộng-và-tích-hợp)

## Truy xuất Dữ liệu Nhiệt độ và Gió

Module mô phỏng thời tiết cho phép truy xuất dữ liệu nhiệt độ và gió tại các tọa độ cụ thể trong lưới mô phỏng. Phần này mô tả cách thực hiện các tác vụ này.

### Truy cập Nhiệt độ tại Điểm Cụ thể

Để truy cập nhiệt độ tại một điểm cụ thể trong lưới mô phỏng, thêm phương thức sau vào lớp `RealtimeWeatherSimulation`:

```python
def get_temperature_at_point(self, x, y):
    """
    Lấy giá trị nhiệt độ tại điểm (x, y) cụ thể.
    
    Args:
        x (int): Tọa độ x (0 <= x < width)
        y (int): Tọa độ y (0 <= y < height)
        
    Returns:
        float: Nhiệt độ tại điểm (x, y)
    """
    # Lấy mảng nhiệt độ 2D từ trường nhiệt
    temp_field = self.get_temperature()
    
    # Kiểm tra tọa độ có nằm trong phạm vi hợp lệ không
    if 0 <= x < self.width and 0 <= y < self.height:
        return temp_field[y, x]  # Chú ý: Numpy sử dụng [y, x] thay vì [x, y]
    else:
        raise ValueError(f"Tọa độ ({x}, {y}) nằm ngoài phạm vi lưới {self.width}x{self.height}")
```

**Chú ý quan trọng**: Khi truy cập mảng NumPy, chỉ số đầu tiên là y (dòng) và chỉ số thứ hai là x (cột), không phải ngược lại.

### Truy cập Thông tin Gió tại Điểm Cụ thể

Tương tự, để truy cập thông tin gió tại một điểm cụ thể:

```python
def get_wind_at_point(self, x, y):
    """
    Lấy vector gió tại điểm (x, y) cụ thể.
    
    Args:
        x (int): Tọa độ x (0 <= x < width)
        y (int): Tọa độ y (0 <= y < height)
        
    Returns:
        tuple: (wind_x, wind_y) - Vector gió tại điểm (x, y)
    """
    # Lấy mảng gió 2D cho cả thành phần x và y
    wind_x, wind_y = self.get_wind_field()
    
    # Kiểm tra tọa độ có nằm trong phạm vi hợp lệ không
    if 0 <= x < self.width and 0 <= y < self.height:
        return (wind_x[y, x], wind_y[y, x])  # Lưu ý thứ tự [y, x]
    else:
        raise ValueError(f"Tọa độ ({x}, {y}) nằm ngoài phạm vi lưới {self.width}x{self.height}")
```

Phương thức này trả về một tuple chứa các thành phần x và y của vector gió tại điểm được chỉ định.

### Ví dụ Sử dụng

Dưới đây là một ví dụ về cách sử dụng các phương thức trên để truy xuất và hiển thị thông tin thời tiết tại một điểm cụ thể:

```python
import math
from model.weather.python.visualization.realtime_simulation import RealtimeWeatherSimulation

# Khởi tạo mô phỏng
simulation = RealtimeWeatherSimulation(width=200, height=200)
simulation.set_initial_conditions()

# Lấy giá trị tại điểm giữa lưới
center_x = simulation.width // 2
center_y = simulation.height // 2

# Truy xuất dữ liệu
temperature = simulation.get_temperature_at_point(center_x, center_y)
wind_vector = simulation.get_wind_at_point(center_x, center_y)

# Tính toán các thông số bổ sung
wind_speed = math.sqrt(wind_vector[0]**2 + wind_vector[1]**2)
wind_direction = math.degrees(math.atan2(wind_vector[1], wind_vector[0]))

# Hiển thị kết quả
print(f"Thông tin thời tiết tại điểm ({center_x}, {center_y}):")
print(f"- Nhiệt độ: {temperature:.2f}°C")
print(f"- Vector gió: ({wind_vector[0]:.2f}, {wind_vector[1]:.2f})")
print(f"- Tốc độ gió: {wind_speed:.2f} đơn vị/s")
print(f"- Hướng gió: {wind_direction:.1f}° (0° = Đông, 90° = Bắc, 180° = Tây, 270° = Nam)")
```

## Tùy chỉnh Điều kiện Nhiệt độ Ban đầu

Module mô phỏng thời tiết cho phép tùy chỉnh linh hoạt các điều kiện nhiệt độ ban đầu. Phần này trình bày các cách khác nhau để đạt được điều này.

### Tùy chỉnh Gradient Nhiệt độ

Gradient nhiệt độ xác định sự thay đổi nhiệt độ theo một hướng cụ thể trên lưới. Bạn có thể tùy chỉnh gradient trong phương thức `set_initial_conditions()`:

```python
def set_initial_conditions(self):
    """Thiết lập điều kiện ban đầu"""
    # Các hướng gradient có sẵn:
    # - GradientDirection.NORTH_SOUTH: Từ Bắc (y lớn) xuống Nam (y nhỏ)
    # - GradientDirection.SOUTH_NORTH: Từ Nam lên Bắc
    # - GradientDirection.EAST_WEST: Từ Đông (x lớn) sang Tây (x nhỏ)
    # - GradientDirection.WEST_EAST: Từ Tây sang Đông
    
    # Ví dụ 1: Gradient từ Bắc (10°C) xuống Nam (30°C)
    self.temp_field.set_gradient(10.0, 30.0, self.cpp_weather.GradientDirection.NORTH_SOUTH)
    
    # Ví dụ 2: Gradient từ Tây (5°C) sang Đông (25°C)
    # self.temp_field.set_gradient(5.0, 25.0, self.cpp_weather.GradientDirection.WEST_EAST)
```

### Thêm Nguồn Nhiệt Tùy chỉnh

Bạn có thể thêm các nguồn nhiệt ở các vị trí tùy ý trong lưới:

```python
def set_initial_conditions(self):
    """Thiết lập điều kiện ban đầu"""
    # Đặt gradient cơ bản
    self.temp_field.set_gradient(15.0, 25.0, self.cpp_weather.GradientDirection.NORTH_SOUTH)
    
    # Thêm nguồn nhiệt ở giữa (điểm nóng)
    # Tham số: x, y, bán kính, nhiệt độ
    center_x = self.width // 2
    center_y = self.height // 2
    self.temp_field.add_heat_source(center_x, center_y, self.width // 10, 35.0)
    
    # Thêm điểm lạnh ở góc trên bên trái
    self.temp_field.add_heat_source(self.width // 10, self.height // 10, self.width // 15, 5.0)
    
    # Thêm điểm nóng ở góc dưới bên phải
    self.temp_field.add_heat_source(
        self.width - self.width // 10, 
        self.height - self.height // 10, 
        self.width // 12, 
        40.0
    )
```

### Tạo Mô hình Nhiệt độ Phức tạp

Bạn có thể kết hợp nhiều gradient và nguồn nhiệt để tạo các mô hình thời tiết phức tạp hơn:

```python
import math
import numpy as np

def create_complex_temperature_pattern(self):
    """Tạo mô hình nhiệt độ phức tạp"""
    # 1. Tạo gradient cơ bản
    self.temp_field.set_gradient(15.0, 25.0, self.cpp_weather.GradientDirection.NORTH_SOUTH)
    
    # 2. Thêm dãy núi nóng ở giữa (mô phỏng dãy núi)
    mountain_y = int(self.height * 0.6)
    for x in range(0, self.width):
        # Tạo đường zigzag cho dãy núi
        y_offset = int(10 * math.sin(x / 20.0))
        y_pos = mountain_y + y_offset
        
        # Nhiệt độ thay đổi dọc theo dãy núi
        temp = 30.0 + 5.0 * math.sin(x / 40.0)
        
        # Bán kính thay đổi để tạo hiệu ứng đỉnh và thung lũng
        radius = 5.0 + 3.0 * math.cos(x / 15.0)
        
        if 0 <= y_pos < self.height:
            self.temp_field.add_heat_source(x, y_pos, radius, temp)
    
    # 3. Thêm vùng lạnh ở góc trên bên phải (mô phỏng hồ lớn)
    lake_x = int(self.width * 0.75)
    lake_y = int(self.height * 0.25)
    self.temp_field.add_heat_source(lake_x, lake_y, self.width // 8, 5.0)
    
    # 4. Thêm vùng nóng ở góc dưới bên trái (mô phỏng sa mạc)
    desert_x = int(self.width * 0.25)
    desert_y = int(self.height * 0.75)
    self.temp_field.add_heat_source(desert_x, desert_y, self.width // 7, 40.0)
    
    # 5. Thêm một số điểm nóng/lạnh ngẫu nhiên (mô phỏng các đặc điểm địa lý nhỏ)
    np.random.seed(42)  # Để kết quả nhất quán
    for _ in range(15):
        x = np.random.randint(0, self.width)
        y = np.random.randint(0, self.height)
        
        # 50% khả năng là điểm nóng, 50% là điểm lạnh
        if np.random.random() > 0.5:
            temp = np.random.uniform(30.0, 45.0)  # Điểm nóng
        else:
            temp = np.random.uniform(0.0, 10.0)   # Điểm lạnh
            
        radius = np.random.uniform(self.width // 40, self.width // 20)
        self.temp_field.add_heat_source(x, y, radius, temp)
```

### Tải Dữ liệu Nhiệt độ từ Nguồn Bên ngoài

Nếu bạn có dữ liệu nhiệt độ từ nguồn bên ngoài (ví dụ: từ file hoặc API), bạn có thể đặt trực tiếp vào trường nhiệt độ:

```python
import numpy as np

def load_temperature_from_file(self, file_path):
    """
    Tải dữ liệu nhiệt độ từ file numpy.
    
    Args:
        file_path (str): Đường dẫn đến file .npy chứa mảng nhiệt độ
    
    Returns:
        bool: True nếu tải thành công, False nếu có lỗi
    """
    try:
        # Tải mảng numpy từ file
        temp_data = np.load(file_path)
        
        # Kiểm tra kích thước
        if temp_data.shape != (self.height, self.width):
            print(f"Cảnh báo: Kích thước dữ liệu {temp_data.shape} khác với kích thước lưới {self.height}x{self.width}")
            
            # Nếu cần, resize dữ liệu cho phù hợp
            temp_data = np.resize(temp_data, (self.height, self.width))
            print(f"Đã resize dữ liệu thành {temp_data.shape}")
        
        # Chuyển thành mảng 1D (C++ binding yêu cầu định dạng này)
        flat_data = temp_data.flatten()
        
        # Đặt dữ liệu vào trường nhiệt độ
        self.temp_field.set_temperature(flat_data)
        
        print(f"Đã tải dữ liệu nhiệt độ từ {file_path}")
        return True
        
    except Exception as e:
        print(f"Lỗi khi tải dữ liệu nhiệt độ: {e}")
        return False

def set_temperature_from_array(self, temp_array):
    """
    Đặt dữ liệu nhiệt độ từ mảng numpy 2D.
    
    Args:
        temp_array (numpy.ndarray): Mảng 2D chứa dữ liệu nhiệt độ
        
    Returns:
        bool: True nếu thành công, False nếu có lỗi
    """
    try:
        # Kiểm tra kích thước
        if temp_array.shape != (self.height, self.width):
            print(f"Cảnh báo: Kích thước dữ liệu {temp_array.shape} khác với kích thước lưới {self.height}x{self.width}")
            
            # Nếu cần, resize dữ liệu cho phù hợp
            temp_array = np.resize(temp_array, (self.height, self.width))
        
        # Chuyển thành mảng 1D (C++ binding yêu cầu định dạng này)
        flat_data = temp_array.flatten()
        
        # Đặt dữ liệu vào trường nhiệt độ
        self.temp_field.set_temperature(flat_data)
        
        print(f"Đã cập nhật dữ liệu nhiệt độ từ mảng tùy chỉnh")
        return True
        
    except Exception as e:
        print(f"Lỗi khi cập nhật dữ liệu nhiệt độ: {e}")
        return False
```

## Phương thức API

Bảng dưới đây tóm tắt các phương thức API chính để làm việc với dữ liệu nhiệt độ và gió:

| Phương thức | Mô tả | Tham số | Giá trị trả về |
|-------------|--------|---------|---------------|
| `get_temperature()` | Lấy toàn bộ trường nhiệt độ | N/A | mảng numpy 2D |
| `get_temperature_at_point(x, y)` | Lấy nhiệt độ tại điểm cụ thể | x, y: tọa độ | float: giá trị nhiệt độ |
| `get_wind_field()` | Lấy toàn bộ trường gió | N/A | tuple của 2 mảng numpy 2D (wind_x, wind_y) |
| `get_wind_at_point(x, y)` | Lấy vector gió tại điểm cụ thể | x, y: tọa độ | tuple (wind_x, wind_y) |
| `temp_field.set_gradient(min, max, direction)` | Đặt gradient nhiệt độ | min, max: nhiệt độ<br>direction: hướng gradient | N/A |
| `temp_field.add_heat_source(x, y, radius, temp)` | Thêm nguồn nhiệt | x, y: tọa độ<br>radius: bán kính<br>temp: nhiệt độ | N/A |
| `temp_field.set_temperature(data)` | Đặt dữ liệu nhiệt độ trực tiếp | data: mảng 1D | N/A |
| `wind_field.generate_gaussian_field(num_vortices, strength, radius)` | Tạo trường gió với các xoáy Gaussian | num_vortices: số xoáy<br>strength: cường độ<br>radius: bán kính | N/A |

## Mở rộng và Tích hợp

### Tạo Phương thức Phân tích

Bạn có thể mở rộng module bằng cách thêm các phương thức phân tích, ví dụ:

```python
def analyze_temperature_range(self):
    """Phân tích phạm vi nhiệt độ trong lưới"""
    temp = self.get_temperature()
    min_temp = np.min(temp)
    max_temp = np.max(temp)
    mean_temp = np.mean(temp)
    std_temp = np.std(temp)
    
    return {
        "min": min_temp,
        "max": max_temp,
        "mean": mean_temp, 
        "std": std_temp,
        "range": max_temp - min_temp
    }

def find_hottest_point(self):
    """Tìm điểm nóng nhất trong lưới"""
    temp = self.get_temperature()
    max_idx = np.argmax(temp)
    
    # Chuyển đổi từ chỉ số 1D sang tọa độ 2D
    y = max_idx // self.width
    x = max_idx % self.width
    
    return {
        "x": x,
        "y": y,
        "temperature": temp[y, x]
    }

def find_strongest_wind(self):
    """Tìm điểm có gió mạnh nhất trong lưới"""
    wind_x, wind_y = self.get_wind_field()
    wind_magnitude = np.sqrt(wind_x**2 + wind_y**2)
    max_idx = np.argmax(wind_magnitude)
    
    # Chuyển đổi từ chỉ số 1D sang tọa độ 2D
    y = max_idx // self.width
    x = max_idx % self.width
    
    return {
        "x": x,
        "y": y,
        "magnitude": wind_magnitude[y, x],
        "direction": math.degrees(math.atan2(wind_y[y, x], wind_x[y, x]))
    }
```

### Tích hợp với Hệ thống Hiển thị

Các phương thức này có thể được tích hợp với các hệ thống hiển thị để tạo ra ứng dụng thời tiết tương tác:

```python
def display_weather_info(self, x, y):
    """Hiển thị thông tin thời tiết chi tiết tại điểm được chọn"""
    temp = self.get_temperature_at_point(x, y)
    wind = self.get_wind_at_point(x, y)
    
    wind_speed = math.sqrt(wind[0]**2 + wind[1]**2)
    wind_direction = math.degrees(math.atan2(wind[1], wind[0]))
    
    info = f"""
    Thông tin thời tiết tại ({x}, {y}):
    -------------------------------
    Nhiệt độ: {temp:.1f}°C
    
    Gió:
      - Tốc độ: {wind_speed:.2f} đơn vị/s
      - Hướng: {wind_direction:.1f}°
      - Vector: ({wind[0]:.2f}, {wind[1]:.2f})
    """
    
    return info
```

Với các phương thức và kỹ thuật được mô tả trong tài liệu này, bạn có thể tùy chỉnh đầy đủ và truy xuất dữ liệu từ mô phỏng thời tiết cho các ứng dụng khác nhau.
