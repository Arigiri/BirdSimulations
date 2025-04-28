"""
Simplified test for the C++ weather module
"""

import os
import sys
import numpy as np

# Điều chỉnh Python path để có thể import các module cần thiết
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Current directory: {current_dir}")
print(f"Project root: {project_root}")
print(f"Python path: {sys.path}")

# Import trực tiếp module C++
try:
    print("\nImporting C++ module directly...")
    import cpp_weather
    print("C++ module imported successfully!")
    
    # Tạo và kiểm thử các đối tượng cơ bản
    width, height = 100, 100
    
    solver = cpp_weather.Solver(width, height, 1.0, 0.1)
    print("Created solver")
    
    wind_field = cpp_weather.WindField(width, height)
    wind_field.generate_gaussian_field(5, 2.0, 10.0)
    print("Created and configured wind field")
    
    # Tạo dữ liệu nhiệt độ
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
    
    print("\nNow trying multiprocessing integration...")
    
    # Tạo phiên bản đơn giản của WeatherModelCpp
    class SimpleWeatherModel:
        def __init__(self, width, height):
            self.width = width
            self.height = height
            self.solver = cpp_weather.Solver(width, height, 1.0, 0.1)
            self.wind_field = cpp_weather.WindField(width, height)
            self.temp_field = cpp_weather.TemperatureField(width, height)
            
            # Khởi tạo
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
    
    # Kiểm thử mô hình đơn giản
    model = SimpleWeatherModel(width, height)
    
    # Chạy một vài bước
    for i in range(5):
        dt = model.step_simulation()
        print(f"Step {i+1}, dt = {dt:.6f}")
    
    # Lấy kết quả
    final_temp = model.get_temperature()
    print(f"Final temperature shape: {final_temp.shape}")
    print(f"Min: {np.min(final_temp):.2f}, Max: {np.max(final_temp):.2f}, Mean: {np.mean(final_temp):.2f}")
    
    print("\nSimple multiprocessing test...")
    
    from multiprocessing import Pool, cpu_count
    import time
    
    def process_subdomain(args):
        """Hàm xử lý một phần của miền tính toán"""
        start_row, end_row, width, height, dt = args
        
        # Tạo mô hình con cho subdomain này
        sub_model = SimpleWeatherModel(width, height)
        
        # Chạy một bước
        sub_dt = sub_model.step_simulation(dt)
        
        # Trả về kết quả
        return (start_row, end_row, sub_model.get_temperature()[start_row:end_row+1, :])
    
    # Tạo một mô hình lớn hơn để kiểm thử song song
    large_width, large_height = 200, 200
    large_model = SimpleWeatherModel(large_width, large_height)
    
    # Phân chia miền tính toán
    num_processes = min(4, cpu_count())
    print(f"Using {num_processes} processes")
    
    rows_per_process = large_height // num_processes
    subdomains = []
    
    for i in range(num_processes):
        start_row = i * rows_per_process
        end_row = (i + 1) * rows_per_process - 1 if i < num_processes - 1 else large_height - 1
        subdomains.append((start_row, end_row, large_width, large_height, 0.1))
    
    # Tạo pool và chạy song song
    start_time = time.time()
    
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_subdomain, subdomains)
    
    end_time = time.time()
    print(f"Multiprocessing completed in {end_time - start_time:.3f} seconds")
    
    # Kiểm tra kết quả
    for start_row, end_row, result in results:
        print(f"Subdomain [{start_row}:{end_row+1}], shape: {result.shape}")
    
    print("\nAll tests completed successfully!")
    
except ImportError as e:
    print(f"Import error: {e}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
