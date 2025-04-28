"""
Test multiprocessing integration with C++ module
"""

import os
import sys
import numpy as np
import time
from multiprocessing import Pool, cpu_count, freeze_support

# Điều chỉnh Python path để tìm được module
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def create_and_test_model():
    """Khởi tạo và kiểm tra mô hình C++ cơ bản"""
    print("\nImporting C++ module directly...")
    import cpp_weather
    print("C++ module imported successfully!")
    
    # Tạo và kiểm thử các đối tượng cơ bản
    width, height = 100, 100
    
    # Tạo Solver
    solver = cpp_weather.Solver(width, height, 1.0, 0.1)
    print("Created solver")
    
    # Tạo WindField
    wind_field = cpp_weather.WindField(width, height)
    wind_field.generate_gaussian_field(5, 2.0, 10.0)
    print("Created and configured wind field")
    
    # Tạo TemperatureField
    temp_field = cpp_weather.TemperatureField(width, height)
    temp_field.set_uniform(20.0)
    print("Created and initialized temperature field")
    
    # Lấy dữ liệu
    temp = temp_field.get_temperature()
    wind_x = wind_field.get_wind_x()
    wind_y = wind_field.get_wind_y()
    
    # Chạy mô phỏng
    dt = solver.compute_cfl_time_step(wind_x, wind_y)
    print(f"CFL time step: {dt}")
    
    new_temp = solver.solve_rk4_step(temp, wind_x, wind_y, dt)
    print(f"Simulation step completed, shape: {new_temp.shape}")
    
    return cpp_weather

# Lớp mô hình thời tiết đơn giản
class SimpleWeatherModel:
    def __init__(self, width, height, cpp_weather_module):
        self.width = width
        self.height = height
        self.cpp_weather = cpp_weather_module
        
        # Khởi tạo các thành phần
        self.solver = self.cpp_weather.Solver(width, height, 1.0, 0.1)
        self.wind_field = self.cpp_weather.WindField(width, height)
        self.temp_field = self.cpp_weather.TemperatureField(width, height)
        
        # Khởi tạo dữ liệu
        self.temp_field.set_uniform(20.0)
        self.wind_field.generate_gaussian_field(5, 2.0, 10.0)
    
    def step_simulation(self, dt=None):
        # Lấy dữ liệu
        temp = self.temp_field.get_temperature()
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Tính bước thời gian nếu cần
        if dt is None:
            dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Cập nhật nhiệt độ
        new_temp = self.solver.solve_rk4_step(temp, wind_x, wind_y, dt)
        self.temp_field.set_temperature(new_temp.flatten())
        
        return dt
    
    def get_temperature(self):
        return self.temp_field.get_temperature().reshape(self.height, self.width)

def process_subdomain(args):
    """
    Hàm worker xử lý một phần của miền tính toán.
    
    Args:
        args (tuple): (start_row, end_row, width, height, dt, module_path)
    
    Returns:
        tuple: (start_row, end_row, processed_data)
    """
    start_row, end_row, width, height, dt, module_path = args
    
    # Đảm bảo đường dẫn module trong sys.path
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
    
    # Import module C++
    import cpp_weather
    
    # Tạo mô hình con cho subdomain này
    sub_model = SimpleWeatherModel(width, height, cpp_weather)
    
    # Chạy một bước
    actual_dt = sub_model.step_simulation(dt)
    
    # Lấy kết quả và trả về phần subdomain
    temp = sub_model.get_temperature()
    return (start_row, end_row, temp[start_row:end_row+1, :], actual_dt)

def test_sequential():
    """Kiểm thử mô hình tuần tự"""
    # Import module C++
    cpp_weather = create_and_test_model()
    
    print("\nTesting sequential model...")
    
    # Tạo mô hình
    width, height = 200, 200
    model = SimpleWeatherModel(width, height, cpp_weather)
    
    # Chạy vài bước
    start_time = time.time()
    
    num_steps = 10
    for i in range(num_steps):
        dt = model.step_simulation()
        print(f"Step {i+1}/{num_steps}, dt = {dt:.6f}")
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Lấy kết quả
    final_temp = model.get_temperature()
    
    print(f"Sequential model ran {num_steps} steps in {elapsed:.3f} seconds ({num_steps/elapsed:.2f} steps/second)")
    print(f"Final temperature shape: {final_temp.shape}")
    print(f"Min: {np.min(final_temp):.2f}, Max: {np.max(final_temp):.2f}, Mean: {np.mean(final_temp):.2f}")
    
    return elapsed

def test_multiprocessing():
    """Kiểm thử mô hình song song với multiprocessing"""
    print("\nTesting multiprocessing model...")
    
    # Tạo một mô hình lớn
    width, height = 200, 200
    
    # Phân chia miền tính toán
    num_processes = min(4, cpu_count())
    print(f"Using {num_processes} processes")
    
    rows_per_process = height // num_processes
    subdomains = []
    
    # Chuẩn bị tham số cho mỗi process
    for i in range(num_processes):
        start_row = i * rows_per_process
        end_row = (i + 1) * rows_per_process - 1 if i < num_processes - 1 else height - 1
        subdomains.append((start_row, end_row, width, height, 0.1, project_root))
    
    # Chạy song song
    start_time = time.time()
    
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_subdomain, subdomains)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Kiểm tra kết quả
    print(f"Multiprocessing completed in {elapsed:.3f} seconds")
    
    for start_row, end_row, result, dt in results:
        print(f"Subdomain [{start_row}:{end_row+1}], shape: {result.shape}, dt: {dt:.6f}")
    
    return elapsed

def main():
    """Hàm chính chạy toàn bộ kiểm thử"""
    print(f"Current directory: {current_dir}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")
    
    try:
        # Kiểm thử tuần tự
        seq_time = test_sequential()
        
        # Kiểm thử song song
        mp_time = test_multiprocessing()
        
        # So sánh
        print("\n--- Performance Comparison ---")
        print(f"Sequential: {seq_time:.3f} seconds")
        print(f"Multiprocessing: {mp_time:.3f} seconds")
        if mp_time > 0:
            print(f"Speedup: {seq_time/mp_time:.2f}x")
        
        print("\nAll tests completed successfully!")
        
    except ImportError as e:
        print(f"Import error: {e}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Cần thiết cho multiprocessing trên Windows
    freeze_support()
    main()
