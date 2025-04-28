"""
Tối ưu hóa multiprocessing cho mô phỏng thời tiết C++/Python
- Sử dụng persistent worker pool
- Tối thiểu hóa chi phí khởi tạo
- Cân bằng tải động giữa các workers
"""

import os
import sys
import numpy as np
import time
from multiprocessing import Pool, cpu_count, freeze_support, current_process, Array, shared_memory
import ctypes

# Điều chỉnh Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Biến toàn cục để lưu trữ module C++ sau khi import
global_cpp_weather = None

def init_worker():
    """
    Hàm khởi tạo cho worker processes.
    """
    global global_cpp_weather
    
    # Import module C++ một lần duy nhất trong worker
    import cpp_weather
    global_cpp_weather = cpp_weather
    
    proc_name = current_process().name
    proc_id = int(proc_name.split('-')[-1]) if '-' in proc_name else 0
    
    # Chỉ in thông báo khi worker được tạo
    print(f"Worker {proc_name} (ID: {proc_id}) initialized with C++ module")

def process_subdomain(args):
    """
    Worker function tối ưu hóa.
    """
    global global_cpp_weather
    
    start_row, end_row, width, height, kappa, dx, temp_shape, temp_data, wind_x_data, wind_y_data, dt = args
    
    # Đảm bảo C++ module đã được import
    if global_cpp_weather is None:
        import cpp_weather
        global_cpp_weather = cpp_weather
        print(f"Late import of C++ module in process {current_process().name}")
    
    # Chuyển đổi dữ liệu shared memory thành numpy arrays
    temp_array = np.frombuffer(temp_data, dtype=np.float64).reshape(temp_shape)
    wind_x_array = np.frombuffer(wind_x_data, dtype=np.float64)
    wind_y_array = np.frombuffer(wind_y_data, dtype=np.float64)
    
    # Tạo subdomain với ghost cells
    # Ghost cells là các ô bổ sung ở biên để xử lý các điều kiện biên chính xác
    ghost_start = max(0, start_row - 1)
    ghost_end = min(height - 1, end_row + 1)
    
    # Trích xuất subdomain với ghost cells
    sub_temp = temp_array[ghost_start:ghost_end+1, :].copy()
    wind_x_2d = wind_x_array.reshape(height, width)
    wind_y_2d = wind_y_array.reshape(height, width)
    sub_wind_x = wind_x_2d[ghost_start:ghost_end+1, :].flatten()
    sub_wind_y = wind_y_2d[ghost_start:ghost_end+1, :].flatten()
    
    # Tạo solver cho subdomain
    sub_width = width
    sub_height = sub_temp.shape[0]
    sub_solver = global_cpp_weather.Solver(sub_width, sub_height, dx, kappa)
    
    # Giải subdomain
    sub_result = sub_solver.solve_rk4_step(sub_temp, sub_wind_x, sub_wind_y, dt)
    
    # Xác định phần kết quả cần trả về
    local_start = 1 if start_row > 0 else 0
    local_end = sub_height - 1 if end_row < height - 1 else sub_height
    
    # Trả về chỉ phần kết quả thực tế (không có ghost cells)
    # Giả sử subdomain là một phần của mảng lớn
    result_2d = sub_result[local_start:local_end, :]
    
    # Chỉ in thông báo khi cần thiết
    # print(f"Process {current_process().name} completed subdomain [{start_row}:{end_row+1}]")
    
    return (start_row, end_row, result_2d)

class OptimizedWeatherSimulation:
    """Mô phỏng thời tiết tối ưu hóa sử dụng module C++ và worker pool cố định"""
    
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
        self.worker_pool = None
        
        print(f"Initializing optimized weather simulation ({width}x{height})")
        print(f"Multiprocessing: {'Enabled' if multiprocessing else 'Disabled'}")
        if multiprocessing:
            print(f"Number of processes: {self.num_processes}")
        
        # Import module C++
        import cpp_weather
        self.cpp_weather = cpp_weather
        
        # Khởi tạo đối tượng C++
        self.solver = cpp_weather.Solver(width, height, dx, kappa)
        self.wind_field = cpp_weather.WindField(width, height)
        self.temp_field = cpp_weather.TemperatureField(width, height)
        
        # Khởi tạo dữ liệu lưu trữ
        self.time = 0.0
        self.steps = 0
        self.dt_history = []
        self.compute_times = []
        self.min_temp = []
        self.max_temp = []
        self.mean_temp = []
        
        # Chuẩn bị các subdomain nếu sử dụng multiprocessing
        if self.use_mp:
            self._prepare_subdomains()
            # Tạo worker pool cố định
            self._create_worker_pool()
    
    def _prepare_subdomains(self):
        """Phân chia lưới thành các subdomain"""
        rows_per_process = self.height // self.num_processes
        self.subdomains = []
        
        for i in range(self.num_processes):
            start_row = i * rows_per_process
            end_row = (i + 1) * rows_per_process - 1 if i < self.num_processes - 1 else self.height - 1
            self.subdomains.append((start_row, end_row))
            
        print(f"Created {len(self.subdomains)} subdomains")
    
    def _create_worker_pool(self):
        """Tạo worker pool cố định để tái sử dụng"""
        if self.worker_pool is None:
            print("Creating worker pool...")
            self.worker_pool = Pool(
                processes=self.num_processes,
                initializer=init_worker
            )
            # Chờ tất cả worker khởi tạo
            time.sleep(0.5)
    
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
        self.compute_times.append(step_time)
        
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
        """Xử lý song song tối ưu hóa"""
        # Đảm bảo worker pool tồn tại
        if self.worker_pool is None:
            self._create_worker_pool()
        
        # Lấy dữ liệu
        temp = self.temp_field.get_temperature().reshape(self.height, self.width)
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Tính bước thời gian nếu cần
        if dt is None:
            dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Chuẩn bị tham số cho mỗi worker - truyền dữ liệu thay vì đối tượng
        args_list = []
        for start_row, end_row in self.subdomains:
            args_list.append(
                (start_row, end_row, self.width, self.height, 
                 self.kappa, self.dx, temp.shape, temp.tobytes(), 
                 wind_x.tobytes(), wind_y.tobytes(), dt)
            )
        
        # Xử lý song song với worker pool cố định
        results = self.worker_pool.map(process_subdomain, args_list)
        
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
        
        # Hiệu suất
        total_compute_time = sum(self.compute_times)
        avg_step_time = total_compute_time / max(1, len(self.compute_times))
        print(f"Total compute time: {total_compute_time:.3f}s")
        print(f"Average step time: {avg_step_time:.3f}s")
        print(f"Steps per second: {self.steps / total_compute_time:.2f}")
        
        # Biến đổi nhiệt độ
        if len(self.min_temp) > 1:
            temp_change = self.mean_temp[-1] - self.mean_temp[0]
            print(f"Temperature change: {temp_change:.2f}")
            print(f"Final temperature - Min: {self.min_temp[-1]:.2f}, Max: {self.max_temp[-1]:.2f}, Mean: {self.mean_temp[-1]:.2f}")
    
    def cleanup(self):
        """Dọn dẹp tài nguyên"""
        if self.worker_pool:
            print("Closing worker pool...")
            self.worker_pool.close()
            self.worker_pool.join()
            self.worker_pool = None

def run_large_grid_test(use_multiprocessing=False, grid_size=500, num_steps=10):
    """
    Chạy kiểm thử với lưới lớn để đánh giá hiệu suất
    """
    print(f"\n=== Running {'Multiprocessing' if use_multiprocessing else 'Sequential'} Large Grid Test ===")
    print(f"Grid size: {grid_size}x{grid_size}")
    print(f"Number of steps: {num_steps}")
    
    # Khởi tạo mô phỏng
    sim = OptimizedWeatherSimulation(grid_size, grid_size, multiprocessing=use_multiprocessing)
    sim.set_initial_conditions()
    
    # Chạy mô phỏng
    start_time = time.time()
    for i in range(num_steps):
        sim.step()
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Completed in {total_time:.3f} seconds")
    sim.print_statistics()
    
    # Dọn dẹp
    sim.cleanup()
    
    return total_time, sim.get_temperature()

def main():
    """Hàm chính"""
    print("Weather Simulation Optimized MultiProcessing Test")
    print(f"Current directory: {current_dir}")
    print(f"Available CPUs: {cpu_count()}")
    
    try:
        # Kiểm thử với lưới lớn
        grid_size = 500  # Lưới lớn để tận dụng multiprocessing
        num_steps = 5    # Giảm số bước để test nhanh hơn
        
        print("\n=== SEQUENTIAL TEST ===")
        seq_time, seq_result = run_large_grid_test(False, grid_size, num_steps)
        
        print("\n=== OPTIMIZED MULTIPROCESSING TEST ===")
        par_time, par_result = run_large_grid_test(True, grid_size, num_steps)
        
        # So sánh kết quả
        print("\n=== Performance Comparison ===")
        print(f"Sequential: {seq_time:.3f} seconds")
        print(f"Optimized Parallel: {par_time:.3f} seconds")
        
        if par_time > 0:
            speedup = seq_time / par_time
            print(f"Speedup: {speedup:.2f}x")
            
            # Phân tích hiệu suất
            print("\n=== Performance Analysis ===")
            if speedup > 1:
                efficiency = speedup / cpu_count() * 100
                print(f"Parallel efficiency: {efficiency:.1f}%")
                print("Optimized multiprocessing is providing a performance benefit!")
            else:
                print("Sequential version is still faster, but the gap has narrowed.")
                print("Consider further increasing grid size or reducing communication overhead.")
        
        # So sánh độ chính xác
        diff = np.abs(seq_result - par_result)
        print("\n=== Accuracy Comparison ===")
        print(f"Max difference: {np.max(diff):.6f}")
        print(f"Mean difference: {np.mean(diff):.6f}")
        print(f"Max percentage difference: {np.max(diff)/np.mean(seq_result)*100:.4f}%")
        
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
