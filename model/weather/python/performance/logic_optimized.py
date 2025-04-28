"""
Kiểm tra logic mô phỏng thời tiết với C++ và Python multiprocessing
- Phiên bản tối ưu với grid lớn hơn để thấy rõ lợi ích multiprocessing
"""

import os
import sys
import numpy as np
import time
from multiprocessing import Pool, cpu_count, freeze_support, current_process

# Điều chỉnh Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Hàm xử lý subdomain ở cấp độ module
def process_subdomain(args):
    """
    Worker function cho multiprocessing
    """
    process_id = current_process().name
    
    start_row, end_row, width, height, kappa, dx, temp_array, wind_x_array, wind_y_array, dt = args
    
    # Import module C++ trong worker
    try:
        from model.weather.python.core import cpp_weather
    except ImportError as e:
        print(f"Process {process_id} failed to import C++ module: {e}")
        return start_row, end_row, temp_array
    
    # Tạo subdomain với ghost cells
    sub_height = end_row - start_row + 3  # +3 cho ghost cells
    
    # Xác định vùng dữ liệu với ghost cells
    ghost_start = max(0, start_row - 1)
    ghost_end = min(height - 1, end_row + 1)
    
    # Chuyển đổi mảng 1D thành 2D để dễ trích xuất subdomain
    temp_2d = temp_array.reshape(height, width)
    wind_x_2d = wind_x_array.reshape(height, width)
    wind_y_2d = wind_y_array.reshape(height, width)
    
    # Trích xuất subdomain với ghost cells
    sub_temp = temp_2d[ghost_start:ghost_end+1, :].copy()
    sub_wind_x = wind_x_2d[ghost_start:ghost_end+1, :].flatten()
    sub_wind_y = wind_y_2d[ghost_start:ghost_end+1, :].flatten()
    
    # Tạo solver cho subdomain
    sub_width = width
    sub_height = sub_temp.shape[0]
    sub_solver = cpp_weather.Solver(sub_width, sub_height, dx, kappa)
    
    # Giải subdomain
    sub_result = sub_solver.solve_rk4_step(sub_temp, sub_wind_x, sub_wind_y, dt)
    
    # Xác định phần kết quả cần trả về
    local_start = 1 if start_row > 0 else 0
    local_end = sub_height - 1 if end_row < height - 1 else sub_height
    
    # Chỉ trả về phần kết quả cho subdomain thực tế
    result_2d = sub_result[local_start:local_end, :]
    
    print(f"Process {process_id} completed subdomain [{start_row}:{end_row+1}]")
    return start_row, end_row, result_2d

class WeatherSimulation:
    """Mô phỏng thời tiết sử dụng module C++"""
    
    def __init__(self, width, height, multiprocessing=False, num_processes=None, dx=1.0, kappa=0.05):
        """
        Khởi tạo mô phỏng thời tiết.
        """
        self.width = width
        self.height = height
        self.use_mp = multiprocessing
        self.num_processes = num_processes or min(4, cpu_count())
        self.dx = dx
        self.kappa = kappa
        
        print(f"Initializing weather simulation ({width}x{height})")
        print(f"Multiprocessing: {'Enabled' if multiprocessing else 'Disabled'}")
        if multiprocessing:
            print(f"Number of processes: {self.num_processes}")
        
        # Import module C++
        from model.weather.python.core import cpp_weather
        self.cpp_weather = cpp_weather
        
        # Khởi tạo đối tượng C++
        self.solver = cpp_weather.Solver(width, height, dx, kappa)
        self.wind_field = cpp_weather.WindField(width, height)
        self.temp_field = cpp_weather.TemperatureField(width, height)
        
        # Khởi tạo dữ liệu lưu trữ
        self.time = 0.0
        self.steps = 0
        self.dt_history = []
        self.min_temp = []
        self.max_temp = []
        self.mean_temp = []
        
        # Chuẩn bị các subdomain nếu sử dụng multiprocessing
        if self.use_mp:
            self._prepare_subdomains()
    
    def _prepare_subdomains(self):
        """Phân chia lưới thành các subdomain"""
        rows_per_process = self.height // self.num_processes
        self.subdomains = []
        
        for i in range(self.num_processes):
            start_row = i * rows_per_process
            end_row = (i + 1) * rows_per_process - 1 if i < self.num_processes - 1 else self.height - 1
            self.subdomains.append((start_row, end_row))
            
        print(f"Created {len(self.subdomains)} subdomains")
    
    def set_initial_conditions(self):
        """Tạo điều kiện ban đầu thực tế"""
        # Tạo gradient nhiệt độ theo hướng North-South
        self.temp_field.set_gradient(10.0, 30.0, self.cpp_weather.GradientDirection.NORTH_SOUTH)
        
        # Thêm nguồn nhiệt ở giữa
        center_x = self.width // 2
        center_y = self.height // 2
        self.temp_field.add_heat_source(center_x, center_y, 15.0, self.width // 10)
        
        # Thêm nguồn nhiệt ngẫu nhiên
        np.random.seed(42)  # Để tái tạo kết quả
        num_sources = 5
        for _ in range(num_sources):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            strength = np.random.uniform(5.0, 10.0)
            radius = np.random.uniform(self.width // 20, self.width // 15)
            self.temp_field.add_heat_source(x, y, strength, radius)
        
        # Tạo trường gió Gaussian
        self.wind_field.generate_gaussian_field(8, 2.0, self.width // 8)
        
        # Lưu thống kê ban đầu
        temp = self.get_temperature()
        self.min_temp.append(np.min(temp))
        self.max_temp.append(np.max(temp))
        self.mean_temp.append(np.mean(temp))
        
        print("Initial conditions set")
        print(f"Initial temperature - Min: {self.min_temp[0]:.2f}, Max: {self.max_temp[0]:.2f}, Mean: {self.mean_temp[0]:.2f}")
    
    def step(self, dt=None):
        """
        Tiến hành một bước mô phỏng.
        """
        start_time = time.time()
        
        if self.use_mp:
            dt = self._step_multiprocessing(dt)
        else:
            dt = self._step_sequential(dt)
        
        end_time = time.time()
        step_time = end_time - start_time
        
        # Cập nhật thống kê
        temp = self.get_temperature()
        self.min_temp.append(np.min(temp))
        self.max_temp.append(np.max(temp))
        self.mean_temp.append(np.mean(temp))
        
        # Cập nhật trạng thái
        self.time += dt
        self.steps += 1
        self.dt_history.append(dt)
        
        print(f"Step {self.steps}, t = {self.time:.4f}, dt = {dt:.6f}, compute time: {step_time:.6f}s")
        print(f"  Temperature - Min: {self.min_temp[-1]:.2f}, Max: {self.max_temp[-1]:.2f}, Mean: {self.mean_temp[-1]:.2f}")
        
        return dt
    
    def _step_sequential(self, dt=None):
        """Xử lý tuần tự"""
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
    
    def _step_multiprocessing(self, dt=None):
        """Xử lý song song"""
        # Lấy dữ liệu
        temp = self.temp_field.get_temperature()
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Tính bước thời gian nếu cần
        if dt is None:
            dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Chuẩn bị tham số cho mỗi worker
        args_list = []
        for start_row, end_row in self.subdomains:
            args_list.append(
                (start_row, end_row, self.width, self.height, 
                 self.kappa, self.dx, temp, wind_x, wind_y, dt)
            )
        
        # Xử lý song song
        with Pool(processes=self.num_processes) as pool:
            results = pool.map(process_subdomain, args_list)
        
        # Kết hợp kết quả vào một mảng 2D
        temp_result = np.zeros((self.height, self.width), dtype=np.float64)
        for start_row, end_row, sub_result in results:
            # Cập nhật phần kết quả tương ứng
            temp_result[start_row:end_row+1, :] = sub_result
        
        # Cập nhật trường nhiệt độ chính
        self.temp_field.set_temperature(temp_result.flatten())
        
        return dt
    
    def get_temperature(self):
        """Lấy trường nhiệt độ hiện tại"""
        return self.temp_field.get_temperature().reshape(self.height, self.width)
        
    def randomize_wind(self):
        """Tạo ngẫu nhiên trường gió mới"""
        num_vortices = np.random.randint(3, 10)
        strength = np.random.uniform(1.0, 3.0)
        radius = np.random.uniform(self.width // 10, self.width // 5)
        
        self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
        print(f"Wind field randomized with {num_vortices} vortices")
    
    def print_statistics(self):
        """In thống kê mô phỏng"""
        print("\n=== Simulation Statistics ===")
        print(f"Total steps: {self.steps}")
        print(f"Simulation time: {self.time:.4f}")
        print(f"Average dt: {np.mean(self.dt_history):.6f}")
        
        # In biến đổi nhiệt độ
        if len(self.min_temp) > 1:
            temp_change = self.mean_temp[-1] - self.mean_temp[0]
            print(f"Temperature change: {temp_change:.2f}")
            print(f"Final temperature - Min: {self.min_temp[-1]:.2f}, Max: {self.max_temp[-1]:.2f}, Mean: {self.mean_temp[-1]:.2f}")

def run_single_test(use_multiprocessing=False, grid_size=300, num_steps=10):
    """
    Chạy một bài kiểm thử đơn với lưới lớn để đánh giá hiệu suất
    """
    print(f"\n=== Running {'Multiprocessing' if use_multiprocessing else 'Sequential'} Test ===")
    print(f"Grid size: {grid_size}x{grid_size}")
    print(f"Number of steps: {num_steps}")
    
    # Khởi tạo mô phỏng
    sim = WeatherSimulation(grid_size, grid_size, multiprocessing=use_multiprocessing)
    sim.set_initial_conditions()
    
    # Chạy mô phỏng
    start_time = time.time()
    for i in range(num_steps):
        sim.step()
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Completed in {total_time:.3f} seconds")
    sim.print_statistics()
    
    return total_time, sim.get_temperature()

def main():
    """Hàm chính"""
    print("Weather Simulation Optimized Test")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    
    try:
        # Kiểm thử với grid lớn hơn
        grid_size = 300  # Lưới lớn hơn để tận dụng multiprocessing
        num_steps = 10    # Giảm số bước để test nhanh hơn
        
        print("\n=== SEQUENTIAL TEST ===")
        seq_time, seq_result = run_single_test(False, grid_size, num_steps)
        
        print("\n=== MULTIPROCESSING TEST ===")
        par_time, par_result = run_single_test(True, grid_size, num_steps)
        
        # So sánh kết quả
        print("\n=== Performance Comparison ===")
        print(f"Sequential: {seq_time:.3f} seconds")
        print(f"Parallel: {par_time:.3f} seconds")
        
        if par_time > 0:
            speedup = seq_time / par_time
            print(f"Speedup: {speedup:.2f}x")
            
            # Phân tích hiệu suất
            print("\n=== Performance Analysis ===")
            if speedup > 1:
                efficiency = speedup / cpu_count() * 100
                print(f"Parallel efficiency: {efficiency:.1f}%")
                print("Multiprocessing is providing a performance benefit!")
            else:
                print("Sequential version is still faster for this problem size.")
                print("Consider increasing grid size or complexity for better multiprocessing benefit.")
        
        # So sánh độ chính xác
        diff = np.abs(seq_result - par_result)
        print("\n=== Accuracy Comparison ===")
        print(f"Max difference: {np.max(diff):.6f}")
        print(f"Mean difference: {np.mean(diff):.6f}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure the C++ module is compiled and available in the Python path")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    freeze_support()  # Cần thiết cho multiprocessing trên Windows
    main()
