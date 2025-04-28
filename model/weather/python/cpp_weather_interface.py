"""
Module giao tiếp với mã C++ của mô hình thời tiết

HƯỚNG DẪN SỬ DỤNG:
1. Đảm bảo module C++ đã được biên dịch (xem hướng dẫn trong /cpp/README.md)
2. Import module này trong mã Python của bạn:
   `from model.weather.python.cpp_weather_interface import WeatherModelCpp`
3. Khởi tạo mô hình:
   ```python
   model = WeatherModelCpp(width=100, height=100)
   ```
4. Thiết lập trường nhiệt độ ban đầu:
   ```python
   model.set_uniform_temperature(20.0)  # Nhiệt độ đồng nhất
   # Hoặc
   model.set_temperature_gradient(10.0, 30.0, "NORTH_SOUTH")  # Gradient nhiệt độ
   ```
5. Tạo trường gió:
   ```python
   model.generate_wind_field("gaussian", num_vortices=5, strength=2.0, radius=10.0)
   # Hoặc
   model.generate_wind_field("perlin", scale=10.0, octaves=4, persistence=0.5)
   ```
6. Tiến hành mô phỏng:
   ```python
   # Một bước với bước thời gian tự động theo điều kiện CFL
   model.step_simulation()
   # Hoặc
   # Một bước với bước thời gian xác định
   model.step_simulation(dt=0.1)
   ```
7. Truy cập dữ liệu:
   ```python
   temperature = model.get_temperature()  # Numpy array
   wind_x, wind_y = model.get_wind_field()  # Numpy arrays
   ```
"""

import os
import numpy as np
import logging

# Cài đặt logging
logger = logging.getLogger(__name__)

try:
    # Thử import mô-đun C++
    from model.weather.python.cpp_weather import Solver, WindField, TemperatureField, GradientDirection
    CPP_MODULE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Không thể import module C++: {e}. Chạy 'python -m model.weather.python.build_cpp_module' để biên dịch.")
    logger.warning("Chỉ có thể dùng mô hình Python (hiệu suất thấp hơn).")
    CPP_MODULE_AVAILABLE = False


class WeatherModelCpp:
    """Python wrapper cho các tính năng C++ của mô hình thời tiết."""

    def __init__(self, width, height, dx=1.0, kappa=0.1):
        """
        Khởi tạo mô hình thời tiết tích hợp C++.
        
        Args:
            width (int): Chiều rộng lưới mô phỏng
            height (int): Chiều cao lưới mô phỏng
            dx (float): Khoảng cách lưới
            kappa (float): Hệ số khuếch tán nhiệt
        
        Raises:
            ImportError: Nếu module C++ không được biên dịch
        """
        if not CPP_MODULE_AVAILABLE:
            raise ImportError("Module C++ không khả dụng. Chạy build script để biên dịch.")
        
        self.width = width
        self.height = height
        self.dx = dx
        self.kappa = kappa
        
        # Khởi tạo các đối tượng C++
        self.solver = Solver(width, height, dx, kappa)
        self.wind_field = WindField(width, height)
        self.temperature_field = TemperatureField(width, height)
        
        # Map định danh GradientDirection thành đối tượng enum
        self.gradient_directions = {
            "NORTH_SOUTH": GradientDirection.NORTH_SOUTH,
            "SOUTH_NORTH": GradientDirection.SOUTH_NORTH,
            "EAST_WEST": GradientDirection.EAST_WEST,
            "WEST_EAST": GradientDirection.WEST_EAST,
            "RADIAL_IN": GradientDirection.RADIAL_IN,
            "RADIAL_OUT": GradientDirection.RADIAL_OUT
        }

    def set_uniform_temperature(self, temp_value):
        """
        Đặt nhiệt độ đồng nhất trên toàn lưới.
        
        Args:
            temp_value (float): Giá trị nhiệt độ
        """
        self.temperature_field.set_uniform(temp_value)
    
    def set_temperature_gradient(self, min_temp, max_temp, direction="NORTH_SOUTH"):
        """
        Đặt gradient nhiệt độ theo hướng chỉ định.
        
        Args:
            min_temp (float): Nhiệt độ tối thiểu
            max_temp (float): Nhiệt độ tối đa
            direction (str): Hướng gradient, một trong các giá trị: 
                          "NORTH_SOUTH", "SOUTH_NORTH", "EAST_WEST", "WEST_EAST",
                          "RADIAL_IN", "RADIAL_OUT"
        
        Raises:
            ValueError: Nếu hướng không hợp lệ
        """
        if direction not in self.gradient_directions:
            raise ValueError(f"Hướng không hợp lệ. Phải là một trong: {', '.join(self.gradient_directions.keys())}")
        
        self.temperature_field.set_gradient(min_temp, max_temp, self.gradient_directions[direction])
    
    def set_custom_temperature_gradient(self, min_temp, max_temp, angle_degrees):
        """
        Đặt gradient nhiệt độ theo góc tùy chỉnh.
        
        Args:
            min_temp (float): Nhiệt độ tối thiểu
            max_temp (float): Nhiệt độ tối đa
            angle_degrees (float): Góc theo độ, 0° = Đông, tăng ngược chiều kim đồng hồ
        """
        self.temperature_field.set_custom_gradient(min_temp, max_temp, angle_degrees)
    
    def add_heat_source(self, x, y, strength, radius):
        """
        Thêm nguồn nhiệt vào vị trí cụ thể.
        
        Args:
            x (float): Tọa độ x của nguồn nhiệt
            y (float): Tọa độ y của nguồn nhiệt
            strength (float): Cường độ nguồn nhiệt
            radius (float): Bán kính ảnh hưởng
        """
        self.temperature_field.add_heat_source(x, y, strength, radius)
    
    def generate_wind_field(self, method, **kwargs):
        """
        Tạo trường gió sử dụng các phương pháp khác nhau.
        
        Args:
            method (str): Phương pháp tạo gió, một trong "gaussian", "perlin", hoặc "vortex"
            **kwargs: Tham số cho mỗi phương pháp:
                - gaussian: num_vortices, strength, radius
                - perlin: scale, octaves, persistence
                - vortex: centers, strengths, radiuses
        
        Raises:
            ValueError: Nếu phương pháp không được hỗ trợ
        """
        if method == "gaussian":
            num_vortices = kwargs.get("num_vortices", 5)
            strength = kwargs.get("strength", 2.0)
            radius = kwargs.get("radius", 10.0)
            self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
        
        elif method == "perlin":
            scale = kwargs.get("scale", 10.0)
            octaves = kwargs.get("octaves", 4)
            persistence = kwargs.get("persistence", 0.5)
            self.wind_field.generate_perlin_field(scale, octaves, persistence)
        
        elif method == "vortex":
            centers = kwargs.get("centers", [])
            strengths = kwargs.get("strengths", [])
            radiuses = kwargs.get("radiuses", [])
            self.wind_field.generate_vortex_field(centers, strengths, radiuses)
        
        else:
            raise ValueError(f"Phương pháp '{method}' không được hỗ trợ. Hãy sử dụng: 'gaussian', 'perlin', or 'vortex'")
    
    def step_simulation(self, dt=None):
        """
        Tiến hành mô phỏng một bước thời gian.
        
        Args:
            dt (float, optional): Bước thời gian. Nếu None, sẽ tự động tính theo CFL.
            
        Returns:
            float: Bước thời gian được sử dụng
        """
        # Lấy dữ liệu từ các đối tượng C++
        temp = self.temperature_field.get_temperature()
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Tính bước thời gian nếu cần
        if dt is None:
            dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Giải đồ thị nhiệt
        temp = self.solver.solve_rk4_step(temp, wind_x, wind_y, dt)
        
        # Cập nhật trường nhiệt độ
        self.temperature_field.set_temperature(temp)
        
        return dt
    
    def get_temperature(self):
        """
        Lấy dữ liệu nhiệt độ hiện tại.
        
        Returns:
            numpy.ndarray: Ma trận 2D của dữ liệu nhiệt độ
        """
        return self.temperature_field.get_temperature()
    
    def get_wind_field(self):
        """
        Lấy dữ liệu trường gió hiện tại.
        
        Returns:
            tuple: (wind_x, wind_y) - Hai ma trận 2D cho thành phần X và Y của gió
        """
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Reshape thành 2D arrays
        wind_x = wind_x.reshape(self.height, self.width)
        wind_y = wind_y.reshape(self.height, self.width)
        
        return wind_x, wind_y
    
    def set_temperature_data(self, temperature_array):
        """
        Đặt dữ liệu nhiệt độ trực tiếp từ numpy array.
        
        Args:
            temperature_array (numpy.ndarray): Ma trận 2D của dữ liệu nhiệt độ
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        if temperature_array.shape != (self.height, self.width):
            logger.error(f"Kích thước mảng ({temperature_array.shape}) không khớp với kích thước lưới ({self.height}, {self.width})")
            return False
        
        return self.temperature_field.set_temperature(temperature_array.flatten())
