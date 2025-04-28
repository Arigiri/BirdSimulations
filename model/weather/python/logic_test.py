"""
Kiểm tra logic mô phỏng thời tiết với C++ và Python multiprocessing
- Không sử dụng đồ họa, chỉ kiểm tra logic và hiệu suất
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
        import cpp_weather
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
        num_sources = 3
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

def run_comparison_test(grid_size=100, num_steps=20):
    """
    Chạy và so sánh mô phỏng tuần tự và song song.
    """
    # Chạy phiên bản tuần tự
    print("\n=== Running Sequential Simulation ===")
    seq_sim = WeatherSimulation(grid_size, grid_size, multiprocessing=False)
    seq_sim.set_initial_conditions()
    
    start_time = time.time()
    for i in range(num_steps):
        seq_sim.step()
        if i > 0 and i % 10 == 0:
            # Đổi trường gió sau mỗi 10 bước
            seq_sim.randomize_wind()
    
    seq_time = time.time() - start_time
    print(f"Sequential simulation completed in {seq_time:.3f} seconds")
    seq_sim.print_statistics()
    
    # Lưu kết quả cuối cùng tuần tự để so sánh
    seq_final = seq_sim.get_temperature()
    
    # Chạy phiên bản song song
    print("\n=== Running Parallel Simulation ===")
    par_sim = WeatherSimulation(grid_size, grid_size, multiprocessing=True)
    par_sim.set_initial_conditions()
    
    start_time = time.time()
    for i in range(num_steps):
        par_sim.step()
        if i > 0 and i % 10 == 0:
            # Đổi trường gió sau mỗi 10 bước
            par_sim.randomize_wind()
    
    par_time = time.time() - start_time
    print(f"Parallel simulation completed in {par_time:.3f} seconds")
    par_sim.print_statistics()
    
    # So sánh hiệu suất
    print("\n=== Performance Comparison ===")
    print(f"Sequential: {seq_time:.3f} seconds")
    print(f"Parallel: {par_time:.3f} seconds")
    
    if par_time > 0:
        print(f"Speedup: {seq_time/par_time:.2f}x")
    
    # So sánh kết quả
    par_final = par_sim.get_temperature()
    diff = np.abs(seq_final - par_final)
    
    print("\n=== Result Comparison ===")
    print(f"Max difference: {np.max(diff):.6f}")
    print(f"Mean difference: {np.mean(diff):.6f}")
    
    # Lưu kết quả dưới dạng npy để phân tích sau nếu cần
    try:
        np.save(os.path.join(current_dir, 'seq_result.npy'), seq_final)
        np.save(os.path.join(current_dir, 'par_result.npy'), par_final)
        print("Results saved as numpy arrays for further analysis")
    except:
        print("Could not save results to disk")

def test_large_scale(grid_size=1000, num_steps=20):
    """
    Chạy kiểm thử với lưới lớn để đánh giá hiệu suất thực tế
    """
    print("\n=== Large Scale Test ===")
    print(f"Grid size: {grid_size}x{grid_size}")
    print(f"Number of steps: {num_steps}")
    
    # Chạy phiên bản tuần tự
    print("\nRunning Sequential Large Scale:")
    seq_sim = WeatherSimulation(grid_size, grid_size, multiprocessing=False)
    seq_sim.set_initial_conditions()
    
    start_time = time.time()
    for i in range(num_steps):
        seq_sim.step()
    seq_time = time.time() - start_time
    
    print(f"Sequential large-scale completed in {seq_time:.3f} seconds")
    
    # Chạy phiên bản song song
    print("\nRunning Parallel Large Scale:")
    par_sim = WeatherSimulation(grid_size, grid_size, multiprocessing=True)
    par_sim.set_initial_conditions()
    
    start_time = time.time()
    for i in range(num_steps):
        par_sim.step()
    par_time = time.time() - start_time
    
    print(f"Parallel large-scale completed in {par_time:.3f} seconds")
    
    # So sánh
    if par_time > 0:
        print(f"Large-scale speedup: {seq_time/par_time:.2f}x")
    
    return seq_time, par_time

def main():
    """Hàm chính"""
    print("Weather Simulation Logic Test")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    
    try:
        # Kiểm thử cơ bản
        grid_size = 100  # Kích thước lưới
        num_steps = 20   # Số bước mô phỏng
        
        # Chạy so sánh
        run_comparison_test(grid_size, num_steps)
        
        # Kiểm thử quy mô lớn (tùy chọn, bỏ comment nếu muốn chạy)
        # print("\nDo you want to run a large-scale test? This may take several minutes. (y/n)")
        # choice = input().lower()
        # if choice == 'y':
        #     test_large_scale(500, 10)  # Grid 500x500, 10 bước
        
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
