"""
Module quản lý tính toán song song cho mô hình thời tiết dùng multiprocessing

HƯỚNG DẪN SỬ DỤNG:
1. Import module này trong mã Python của bạn:
   `from model.weather.python.weather_multiprocessing import WeatherMultiprocessingManager`
2. Khởi tạo trình quản lý đa tiến trình:
   ```python
   mp_manager = WeatherMultiprocessingManager(width=100, height=100, num_processes=4)
   ```
3. Thiết lập các trường ban đầu:
   ```python
   mp_manager.set_uniform_temperature(20.0)
   mp_manager.generate_wind_field("gaussian", num_vortices=5)
   ```
4. Thực hiện mô phỏng song song:
   ```python
   # Chạy một bước với bước thời gian tự động
   mp_manager.step_simulation()
   # Hoặc
   # Chạy nhiều bước
   mp_manager.run_simulation(num_steps=100)
   ```
5. Truy cập kết quả:
   ```python
   temperature = mp_manager.get_temperature()
   wind_x, wind_y = mp_manager.get_wind_field()
   ```
"""

import numpy as np
import time
from multiprocessing import Pool, cpu_count
import logging

# Cài đặt logging
logger = logging.getLogger(__name__)

# Import lớp interface C++
try:
    from model.weather.python.cpp_weather_interface import WeatherModelCpp
    CPP_MODULE_AVAILABLE = True
except ImportError:
    logger.warning("Không thể import module C++. Đảm bảo module đã được biên dịch.")
    CPP_MODULE_AVAILABLE = False

def solve_subdomain(args):
    """
    Hàm worker để xử lý một subdomain (được gọi bởi pool.map)
    
    Args:
        args (tuple): (start_row, end_row, temperature, wind_x, wind_y, dt, width, height, dx, kappa)
        
    Returns:
        tuple: (start_row, end_row, temperature_result)
    """
    start_row, end_row, temperature, wind_x, wind_y, dt, width, height, dx, kappa = args
    
    # Phân tích subdomain từ mảng đầu vào
    rows = end_row - start_row + 1
    subdomain_height = rows + 2  # Thêm ghost cells
    subdomain_temp = np.zeros((subdomain_height, width))
    
    # Sao chép dữ liệu vào subdomain (bao gồm ghost cells)
    if start_row > 0:
        subdomain_temp[0, :] = temperature[start_row - 1, :]
    else:
        subdomain_temp[0, :] = temperature[0, :]
        
    subdomain_temp[1:rows+1, :] = temperature[start_row:end_row+1, :]
    
    if end_row < height - 1:
        subdomain_temp[rows+1, :] = temperature[end_row + 1, :]
    else:
        subdomain_temp[rows+1, :] = temperature[end_row, :]
        
    # Cắt trường gió tương ứng
    subdomain_wind_x = wind_x[max(0, start_row-1):min(height, end_row+2), :]
    subdomain_wind_y = wind_y[max(0, start_row-1):min(height, end_row+2), :]
    
    # Tạo đối tượng trình giải
    solver = WeatherModelCpp(width, subdomain_height, dx, kappa)
    
    # Đặt dữ liệu nhiệt độ và gió
    solver.set_temperature_data(subdomain_temp)
    
    # Chạy một bước mô phỏng
    solver.step_simulation(dt)
    
    # Lấy kết quả (chỉ phần không có ghost cells)
    result = solver.get_temperature()[1:rows+1, :]
    
    return (start_row, end_row, result)


class WeatherMultiprocessingManager:
    """Quản lý tính toán song song cho mô hình thời tiết."""

    def __init__(self, width, height, dx=1.0, kappa=0.1, num_processes=None):
        """
        Khởi tạo trình quản lý đa tiến trình.
        
        Args:
            width (int): Chiều rộng lưới
            height (int): Chiều cao lưới
            dx (float): Khoảng cách lưới
            kappa (float): Hệ số khuếch tán
            num_processes (int, optional): Số lượng tiến trình. Mặc định là số CPU.
        
        Raises:
            ImportError: Nếu module C++ không có sẵn
        """
        if not CPP_MODULE_AVAILABLE:
            raise ImportError("Module C++ không khả dụng. Chạy build script để biên dịch.")
        
        self.width = width
        self.height = height
        self.dx = dx
        self.kappa = kappa
        
        # Xác định số process
        self.num_processes = num_processes or cpu_count()
        logger.info(f"Khởi tạo WeatherMultiprocessingManager với {self.num_processes} tiến trình")
        
        # Khởi tạo mô hình tuần tự để quản lý dữ liệu và tạo trường gió
        self.model = WeatherModelCpp(width, height, dx, kappa)
        
        # Khởi tạo Pool để tính toán song song
        self.pool = Pool(processes=self.num_processes)
        
        # Xác định phân chia subdomain
        self._calculate_subdomains()

    def _calculate_subdomains(self):
        """Tính toán phân chia subdomain dựa trên số processes."""
        # Tối ưu: chia đều số hàng cho mỗi process
        rows_per_process = self.height // self.num_processes
        remainder = self.height % self.num_processes
        
        self.subdomains = []
        start_row = 0
        
        for i in range(self.num_processes):
            # Điều chỉnh để phân phối dư số hàng
            extra = 1 if i < remainder else 0
            rows = rows_per_process + extra
            end_row = start_row + rows - 1
            
            self.subdomains.append((start_row, end_row))
            start_row = end_row + 1
            
        logger.debug(f"Đã tạo {len(self.subdomains)} subdomain: {self.subdomains}")

    def set_uniform_temperature(self, temp_value):
        """
        Đặt nhiệt độ đồng nhất trên toàn lưới.
        
        Args:
            temp_value (float): Giá trị nhiệt độ
        """
        self.model.set_uniform_temperature(temp_value)
    
    def set_temperature_gradient(self, min_temp, max_temp, direction="NORTH_SOUTH"):
        """
        Đặt gradient nhiệt độ theo hướng chỉ định.
        
        Args:
            min_temp (float): Nhiệt độ tối thiểu
            max_temp (float): Nhiệt độ tối đa
            direction (str): Hướng gradient
        """
        self.model.set_temperature_gradient(min_temp, max_temp, direction)
    
    def add_heat_source(self, x, y, strength, radius):
        """
        Thêm nguồn nhiệt vào vị trí cụ thể.
        
        Args:
            x (float): Tọa độ x của nguồn nhiệt
            y (float): Tọa độ y của nguồn nhiệt
            strength (float): Cường độ nguồn nhiệt
            radius (float): Bán kính ảnh hưởng
        """
        self.model.add_heat_source(x, y, strength, radius)
    
    def generate_wind_field(self, method, **kwargs):
        """
        Tạo trường gió sử dụng phương pháp được chỉ định.
        
        Args:
            method (str): Phương pháp tạo gió, một trong "gaussian", "perlin", hoặc "vortex"
            **kwargs: Tham số cho mỗi phương pháp
        """
        self.model.generate_wind_field(method, **kwargs)
    
    def step_simulation(self, dt=None):
        """
        Tiến hành mô phỏng song song một bước thời gian.
        
        Args:
            dt (float, optional): Bước thời gian. Nếu None, sẽ tự động tính theo CFL.
            
        Returns:
            float: Bước thời gian được sử dụng
        """
        start_time = time.time()
        
        # Lấy dữ liệu hiện tại
        temperature = self.model.get_temperature()
        wind_x, wind_y = self.model.get_wind_field()
        
        # Tính bước thời gian nếu cần
        if dt is None:
            dt = self.model.solver.compute_cfl_time_step(wind_x.flatten(), wind_y.flatten())
            logger.debug(f"Bước thời gian CFL được tính: {dt}")
        
        # Chuẩn bị tham số cho mỗi subdomain
        worker_args = []
        for start_row, end_row in self.subdomains:
            worker_args.append((
                start_row, end_row, temperature, wind_x, wind_y, dt,
                self.width, self.height, self.dx, self.kappa
            ))
        
        # Xử lý song song
        results = self.pool.map(solve_subdomain, worker_args)
        
        # Kết hợp kết quả từ các subdomain
        for start_row, end_row, result in results:
            temperature[start_row:end_row+1, :] = result
        
        # Cập nhật mô hình chính
        self.model.set_temperature_data(temperature)
        
        end_time = time.time()
        logger.debug(f"Bước mô phỏng song song hoàn thành trong {end_time - start_time:.3f} giây")
        
        return dt
    
    def run_simulation(self, num_steps=10, dt=None):
        """
        Chạy nhiều bước mô phỏng.
        
        Args:
            num_steps (int): Số lượng bước
            dt (float, optional): Bước thời gian cố định. Nếu None, sẽ tính lại ở mỗi bước.
            
        Returns:
            list: Danh sách các bước thời gian đã sử dụng
        """
        dt_values = []
        for _ in range(num_steps):
            used_dt = self.step_simulation(dt)
            dt_values.append(used_dt)
        
        return dt_values
    
    def get_temperature(self):
        """
        Lấy dữ liệu nhiệt độ hiện tại.
        
        Returns:
            numpy.ndarray: Ma trận 2D của dữ liệu nhiệt độ
        """
        return self.model.get_temperature()
    
    def get_wind_field(self):
        """
        Lấy dữ liệu trường gió hiện tại.
        
        Returns:
            tuple: (wind_x, wind_y) - Hai ma trận 2D cho thành phần X và Y của gió
        """
        return self.model.get_wind_field()
    
    def close(self):
        """Đóng pool tiến trình khi kết thúc."""
        if hasattr(self, 'pool'):
            self.pool.close()
            self.pool.join()
            logger.info("Đã đóng pool tiến trình")
    
    def __del__(self):
        """Destructor để đảm bảo pool được đóng lại."""
        self.close()
