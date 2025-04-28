"""
Kiểm tra mô phỏng thời tiết đầy đủ với C++ và Python multiprocessing

Script này tạo một mô phỏng thực tế với:
1. Gradient nhiệt độ và nguồn nhiệt
2. Trường gió Gaussian động
3. Hiển thị tiến triển của mô phỏng qua thời gian
4. So sánh phiên bản tuần tự và song song
"""

import os
import sys
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib import cm
from multiprocessing import Pool, cpu_count, freeze_support

# Điều chỉnh Python path để tìm được module
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class WeatherSimulation:
    """Mô phỏng thời tiết sử dụng module C++"""
    
    def __init__(self, width, height, multiprocessing=False, num_processes=None):
        """
        Khởi tạo mô phỏng thời tiết.
        
        Args:
            width (int): Chiều rộng lưới
            height (int): Chiều cao lưới
            multiprocessing (bool): Sử dụng multiprocessing
            num_processes (int): Số lượng processes, mặc định là số core
        """
        self.width = width
        self.height = height
        self.use_mp = multiprocessing
        self.num_processes = num_processes or min(4, cpu_count())
        
        print(f"Initializing weather simulation ({width}x{height})")
        print(f"Multiprocessing: {'Enabled' if multiprocessing else 'Disabled'}")
        if multiprocessing:
            print(f"Number of processes: {self.num_processes}")
        
        # Import module C++
        import cpp_weather
        self.cpp_weather = cpp_weather
        
        # Khởi tạo đối tượng C++
        self.solver = cpp_weather.Solver(width, height, 1.0, 0.05)  # Kappa nhỏ hơn để thấy rõ đối lưu
        self.wind_field = cpp_weather.WindField(width, height)
        self.temp_field = cpp_weather.TemperatureField(width, height)
        
        # Khởi tạo dữ liệu lưu trữ
        self.time = 0.0
        self.steps = 0
        self.temperature_history = []
        self.dt_history = []
        
        # Chuẩn bị các subdomain nếu sử dụng multiprocessing
        if self.use_mp:
            self._prepare_subdomains()
    
    def _prepare_subdomains(self):
        """Phân chia lưới thành các subdomain cho multiprocessing"""
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
        
        # Lưu trạng thái ban đầu
        self.temperature_history.append(self.get_temperature())
        
        print("Initial conditions set")
    
    def step(self, dt=None):
        """
        Tiến hành một bước mô phỏng.
        
        Args:
            dt (float, optional): Bước thời gian. Nếu None, sẽ tính theo CFL.
        
        Returns:
            float: Bước thời gian được sử dụng
        """
        start_time = time.time()
        
        if self.use_mp:
            dt = self._step_multiprocessing(dt)
        else:
            dt = self._step_sequential(dt)
        
        end_time = time.time()
        step_time = end_time - start_time
        
        # Cập nhật trạng thái
        self.time += dt
        self.steps += 1
        self.dt_history.append(dt)
        self.temperature_history.append(self.get_temperature())
        
        print(f"Step {self.steps}, t = {self.time:.4f}, dt = {dt:.6f}, compute time: {step_time:.6f}s")
        
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
    
    def _process_subdomain(self, args):
        """
        Xử lý một subdomain (được sử dụng bởi các worker).
        
        Args:
            args: (start_row, end_row, temp, wind_x, wind_y, dt)
            
        Returns:
            tuple: (start_row, end_row, sub_result)
        """
        start_row, end_row, temp, wind_x, wind_y, dt = args
        
        # Tạo solver cho subdomain
        sub_height = end_row - start_row + 1 + 2  # +2 cho ghost cells
        sub_solver = self.cpp_weather.Solver(self.width, sub_height, 1.0, 0.05)
        
        # Trích xuất subdomain với ghost cells
        sub_start = max(0, start_row - 1)
        sub_end = min(self.height - 1, end_row + 1)
        
        sub_temp = temp[sub_start:sub_end + 1, :]
        sub_wind_x = wind_x.reshape(self.height, self.width)[sub_start:sub_end + 1, :].flatten()
        sub_wind_y = wind_y.reshape(self.height, self.width)[sub_start:sub_end + 1, :].flatten()
        
        # Giải subdomain
        new_sub_temp = sub_solver.solve_rk4_step(sub_temp, sub_wind_x, sub_wind_y, dt)
        
        # Xác định phạm vi kết quả cần giữ lại (loại bỏ ghost cells)
        ghost_offset_start = 1 if start_row > 0 else 0
        ghost_offset_end = 1 if end_row < self.height - 1 else 0
        
        actual_result = new_sub_temp[ghost_offset_start:sub_temp.shape[0]-ghost_offset_end, :]
        
        return (start_row, end_row, actual_result)
    
    def _step_multiprocessing(self, dt=None):
        """Xử lý song song"""
        # Lấy dữ liệu
        temp = self.get_temperature()
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Tính bước thời gian nếu cần
        if dt is None:
            dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Chuẩn bị tham số cho mỗi worker
        args_list = []
        for start_row, end_row in self.subdomains:
            args_list.append((start_row, end_row, temp, wind_x, wind_y, dt))
        
        # Xử lý song song
        with Pool(processes=self.num_processes) as pool:
            results = pool.map(self._process_subdomain, args_list)
        
        # Kết hợp kết quả
        for start_row, end_row, sub_result in results:
            temp[start_row:end_row+1, :] = sub_result
        
        # Cập nhật trường nhiệt độ chính
        self.temp_field.set_temperature(temp.flatten())
        
        return dt
    
    def get_temperature(self):
        """Lấy trường nhiệt độ hiện tại dưới dạng mảng 2D"""
        return self.temp_field.get_temperature().reshape(self.height, self.width)
    
    def get_wind_field(self):
        """Lấy trường gió hiện tại dưới dạng hai mảng 2D (x, y)"""
        wind_x = self.wind_field.get_wind_x().reshape(self.height, self.width)
        wind_y = self.wind_field.get_wind_y().reshape(self.height, self.width)
        return wind_x, wind_y
    
    def randomize_wind(self):
        """Tạo ngẫu nhiên trường gió mới"""
        num_vortices = np.random.randint(3, 10)
        strength = np.random.uniform(1.0, 3.0)
        radius = np.random.uniform(self.width // 10, self.width // 5)
        
        self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
        print(f"Wind field randomized with {num_vortices} vortices")
    
    def plot_current_state(self, show_wind=True, density=15):
        """
        Vẽ trạng thái hiện tại của mô phỏng.
        
        Args:
            show_wind (bool): Hiển thị trường gió
            density (int): Mật độ vector gió (càng cao càng ít vector)
        """
        plt.figure(figsize=(12, 10))
        
        # Lấy dữ liệu
        temp = self.get_temperature()
        
        # Vẽ nhiệt độ
        plt.imshow(temp, cmap=cm.hot, origin='lower')
        plt.colorbar(label='Temperature')
        
        # Vẽ gió nếu cần
        if show_wind:
            wind_x, wind_y = self.get_wind_field()
            
            # Tạo lưới cho vector gió
            y, x = np.mgrid[0:self.height:1, 0:self.width:1]
            
            # Giảm mật độ để dễ nhìn
            plt.quiver(x[::density, ::density], 
                      y[::density, ::density],
                      wind_x[::density, ::density], 
                      wind_y[::density, ::density],
                      color='white', scale=50, alpha=0.7)
        
        plt.title(f'Weather Simulation (Step {self.steps}, t={self.time:.2f}s)')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.tight_layout()
        plt.show()
    
    def plot_temperature_history(self, interval=1):
        """
        Vẽ lịch sử nhiệt độ qua các bước thời gian.
        
        Args:
            interval (int): Khoảng bước để hiển thị
        """
        if len(self.temperature_history) <= 1:
            print("Not enough history to plot")
            return
        
        num_steps = len(self.temperature_history)
        steps_to_plot = range(0, num_steps, interval)
        
        num_rows = (len(steps_to_plot) + 3) // 4  # 4 cột mỗi hàng
        num_cols = min(4, len(steps_to_plot))
        
        plt.figure(figsize=(16, 4 * num_rows))
        
        for i, step_idx in enumerate(steps_to_plot):
            plt.subplot(num_rows, num_cols, i + 1)
            plt.imshow(self.temperature_history[step_idx], cmap=cm.hot, origin='lower')
            plt.colorbar()
            t = sum(self.dt_history[:step_idx]) if step_idx > 0 else 0
            plt.title(f'Step {step_idx}, t={t:.2f}s')
            plt.xlabel('X')
            plt.ylabel('Y')
        
        plt.tight_layout()
        plt.show()

def run_comparison_test(grid_size=200, num_steps=50, step_interval=5):
    """
    Chạy và so sánh mô phỏng tuần tự và song song.
    
    Args:
        grid_size (int): Kích thước lưới vuông
        num_steps (int): Số bước mô phỏng
        step_interval (int): Khoảng bước để hiển thị kết quả
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
    
    # Hiển thị kết quả tuần tự
    seq_sim.plot_current_state()
    seq_sim.plot_temperature_history(step_interval)
    
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
    
    # Hiển thị kết quả song song
    par_sim.plot_current_state()
    par_sim.plot_temperature_history(step_interval)
    
    # So sánh hiệu suất
    print("\n=== Performance Comparison ===")
    print(f"Sequential: {seq_time:.3f} seconds")
    print(f"Parallel: {par_time:.3f} seconds")
    print(f"Speedup: {seq_time/par_time:.2f}x")
    
    # So sánh kết quả
    seq_final = seq_sim.get_temperature()
    par_final = par_sim.get_temperature()
    diff = np.abs(seq_final - par_final)
    
    print("\n=== Result Comparison ===")
    print(f"Max difference: {np.max(diff):.6f}")
    print(f"Mean difference: {np.mean(diff):.6f}")
    print(f"Sequential - Min: {np.min(seq_final):.2f}, Max: {np.max(seq_final):.2f}, Mean: {np.mean(seq_final):.2f}")
    print(f"Parallel - Min: {np.min(par_final):.2f}, Max: {np.max(par_final):.2f}, Mean: {np.mean(par_final):.2f}")

def main():
    """Hàm chính"""
    print("Weather Simulation Test")
    print(f"Current directory: {current_dir}")
    
    try:
        # Các tham số mô phỏng
        grid_size = 200  # Kích thước lưới
        num_steps = 50   # Số bước mô phỏng
        step_interval = 5  # Khoảng bước để hiển thị kết quả
        
        # Chạy so sánh
        run_comparison_test(grid_size, num_steps, step_interval)
        
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
