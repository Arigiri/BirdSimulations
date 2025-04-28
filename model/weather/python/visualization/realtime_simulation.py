"""
Mô phỏng thời tiết thời gian thực sử dụng C++ và Python
Hiển thị sự thay đổi của trường nhiệt độ và gió theo thời gian
"""

import os
import sys
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.animation import FuncAnimation
from matplotlib.colors import Normalize

# Điều chỉnh Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Thêm các thư mục cha vào python path
python_dir = os.path.abspath(os.path.join(current_dir, '..'))
weather_dir = os.path.abspath(os.path.join(python_dir, '..'))
model_dir = os.path.abspath(os.path.join(weather_dir, '..'))
project_root = os.path.abspath(os.path.join(model_dir, '..'))

# Thêm các thư mục vào python path
for path in [current_dir, python_dir, weather_dir, model_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

class RealtimeWeatherSimulation:
    """Mô phỏng thời tiết thời gian thực"""
    
    def __init__(self, width=200, height=200, dx=1.0, kappa=0.05):
        """
        Khởi tạo mô phỏng thời tiết thời gian thực.
        
        Args:
            width (int): Chiều rộng lưới
            height (int): Chiều cao lưới
            dx (float): Khoảng cách lưới
            kappa (float): Hệ số khuếch tán
        """
        self.width = width
        self.height = height
        self.dx = dx
        self.kappa = kappa
        
        # Fix encoding for Windows terminal
        try:
            print(f"Khởi tạo mô phỏng thời tiết thời gian thực ({width}x{height})")
        except UnicodeEncodeError:
            print(f"Initializing real-time weather simulation ({width}x{height})")
        
        # Import module C++
        try:
            # Thử import bằng các cách khác nhau để hỗ trợ chạy trực tiếp hoặc qua module
            try:
                # Nếu chạy qua module (model.weather.python...)
                from model.weather.python.core import cpp_weather
            except ImportError:
                # Nếu chạy trực tiếp từ thư mục visualization
                sys.path.append(os.path.join(python_dir, 'core'))
                import cpp_weather
            
            self.cpp_weather = cpp_weather
            # Fix encoding for Windows terminal
            try:
                print("Đã tải module C++ thành công")
            except UnicodeEncodeError:
                print("C++ module loaded successfully")
        except ImportError as e:
            # Fix encoding for Windows terminal
            try:
                print(f"Lỗi import module C++: {e}")
                print("Đảm bảo module C++ đã được biên dịch và có trong Python path")
            except UnicodeEncodeError:
                print(f"Error importing C++ module: {e}")
                print("Make sure the C++ module is compiled and in the Python path")
            sys.exit(1)
        
        # Khởi tạo các đối tượng C++
        self.solver = self.cpp_weather.Solver(width, height, dx, kappa)
        self.wind_field = self.cpp_weather.WindField(width, height)
        self.temp_field = self.cpp_weather.TemperatureField(width, height)
        # Fix encoding for Windows terminal
        try:
            print("Đã khởi tạo các đối tượng C++")
        except UnicodeEncodeError:
            print("C++ objects initialized")
        
        # Khởi tạo dữ liệu lưu trữ
        self.time = 0.0
        self.steps = 0
        self.real_time_factor = 1.0  # Hệ số thời gian thực
        
        # Tạo figure và axes cho animation
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.fig.canvas.manager.set_window_title('Mô phỏng thời tiết thời gian thực')
        
        # Tạo plots để cập nhật sau này
        self.temp_plot = None
        self.quiver_plot = None
        self.colorbar = None
        
        # Tham số hiển thị
        self.quiver_density = 10  # Hiển thị 1 mũi tên cho mỗi quiver_density ô
        
        # Thông số vật lý
        self.min_temp = 0
        self.max_temp = 40
        
        # Hàm chuyển mã màu
        self.cmap = cm.hot
    
    def set_initial_conditions(self):
        """Tạo điều kiện ban đầu thực tế"""
        # Fix encoding for Windows terminal
        try:
            print("Thiết lập điều kiện ban đầu...")
        except UnicodeEncodeError:
            print("Setting up initial conditions...")
        
        # Tạo gradient nhiệt độ theo hướng North-South
        self.temp_field.set_gradient(10.0, 30.0, self.cpp_weather.GradientDirection.NORTH_SOUTH)
        
        # Thêm nguồn nhiệt ở giữa
        heat_source_x = self.width // 2
        heat_source_y = self.height // 2
        heat_source_radius = min(self.width, self.height) // 10
        heat_source_temp = 35.0
        self.temp_field.add_heat_source(heat_source_x, heat_source_y, heat_source_radius, heat_source_temp)
        
        # Tạo trường gió Gaussian với một số vịnh xoáy ngẫu nhiên
        # Thông số: số lượng vịnh xoáy, cường độ, bán kính
        self.wind_field.generate_gaussian_field(8, 2.0, self.width // 10)
        
        # Lấy dữ liệu ban đầu
        temp = self.get_temperature()
        
        # Cập nhật phạm vi nhiệt độ
        self.min_temp = max(0, np.min(temp) - 5)
        self.max_temp = min(45, np.max(temp) + 5)
        
        # Fix encoding for Windows terminal
        try:
            print(f"Phạm vi nhiệt độ: {self.min_temp:.1f} - {self.max_temp:.1f}")
        except UnicodeEncodeError:
            print(f"Temperature range: {self.min_temp:.1f} - {self.max_temp:.1f}")
        
        # Fix encoding for Windows terminal
        try:
            print("Đã thiết lập điều kiện ban đầu")
        except UnicodeEncodeError:
            print("Initial conditions set up successfully")
    
    def get_temperature(self):
        """Lấy trường nhiệt độ hiện tại dưới dạng mảng 2D"""
        return self.temp_field.get_temperature().reshape(self.height, self.width)
    
    def get_wind_field(self):
        """Lấy trường gió hiện tại dưới dạng hai mảng 2D (x, y)"""
        wind_x = self.wind_field.get_wind_x().reshape(self.height, self.width)
        wind_y = self.wind_field.get_wind_y().reshape(self.height, self.width)
        return wind_x, wind_y
    
    def step(self):
        """
        Tiến hành một bước mô phỏng.
        
        Returns:
            float: Bước thời gian được sử dụng
        """
        # Lấy dữ liệu
        temp = self.temp_field.get_temperature()
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Tính bước thời gian
        dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Cập nhật nhiệt độ
        new_temp = self.solver.solve_rk4_step(temp, wind_x, wind_y, dt)
        self.temp_field.set_temperature(new_temp.flatten())
        
        # Đôi khi cập nhật trường gió để tạo sự thay đổi
        if self.steps % 20 == 0 and self.steps > 0:
            num_vortices = np.random.randint(3, 10)
            strength = np.random.uniform(1.0, 3.0)
            radius = np.random.uniform(self.width // 10, self.width // 5)
            self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
        
        # Cập nhật trạng thái
        self.time += dt
        self.steps += 1
        
        return dt
    
    def init_animation(self):
        """Khởi tạo animation"""
        # Lấy dữ liệu ban đầu
        temp = self.get_temperature()
        wind_x, wind_y = self.get_wind_field()
        
        # Vẽ trường nhiệt độ
        norm = Normalize(vmin=self.min_temp, vmax=self.max_temp)
        self.temp_plot = self.ax.imshow(temp, origin='lower', cmap=self.cmap, norm=norm, animated=True)
        
        # Thêm colorbar
        self.colorbar = self.fig.colorbar(self.temp_plot, ax=self.ax)
        try:
            self.colorbar.set_label('Nhiệt độ (°C)')
        except UnicodeEncodeError:
            self.colorbar.set_label('Temperature (°C)')
        
        # Tạo lưới cho vector gió
        y, x = np.mgrid[0:self.height:self.quiver_density, 0:self.width:self.quiver_density]
        
        # Vẽ gió
        self.quiver_plot = self.ax.quiver(
            x, y,
            wind_x[::self.quiver_density, ::self.quiver_density],
            wind_y[::self.quiver_density, ::self.quiver_density],
            color='white', scale=50, alpha=0.7
        )
        
        # Thêm tiêu đề và nhãn
        try:
            self.ax.set_title(f'Mô phỏng thời tiết (t={self.time:.2f}s, bước {self.steps})')
        except UnicodeEncodeError:
            self.ax.set_title(f'Weather Simulation (t={self.time:.2f}s, step {self.steps})')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        
        # Thêm chú thích
        try:
            plt.figtext(0.02, 0.02, 'Phím Q: Thoát', fontsize=9)
        except UnicodeEncodeError:
            plt.figtext(0.02, 0.02, 'Press Q: Exit', fontsize=9)
        
        return self.temp_plot, self.quiver_plot
    
    def update_animation(self, frame):
        """Cập nhật animation"""
        # Thực hiện một bước mô phỏng
        start_time = time.time()
        dt = self.step()
        compute_time = time.time() - start_time
        
        # Lấy dữ liệu mới
        temp = self.get_temperature()
        wind_x, wind_y = self.get_wind_field()
        
        # Cập nhật trường nhiệt độ
        self.temp_plot.set_array(temp)
        
        # Cập nhật vector gió
        if frame % 2 == 0:  # Chỉ cập nhật gió mỗi 2 frames để tăng hiệu suất
            self.quiver_plot.set_UVC(
                wind_x[::self.quiver_density, ::self.quiver_density],
                wind_y[::self.quiver_density, ::self.quiver_density]
            )
        
        # Cập nhật tiêu đề
        try:
            self.ax.set_title(f'Mô phỏng thời tiết (t={self.time:.2f}s, bước {self.steps})\n'
                            f'FPS: {1.0/max(0.001, compute_time):.1f}, dt: {dt:.4f}s')
        except UnicodeEncodeError:
            self.ax.set_title(f'Weather Simulation (t={self.time:.2f}s, step {self.steps})\n'
                            f'FPS: {1.0/max(0.001, compute_time):.1f}, dt: {dt:.4f}s')
        
        return self.temp_plot, self.quiver_plot
    
    def on_key_press(self, event):
        """Xử lý sự kiện nhấn phím"""
        if event.key == 'q':
            plt.close(self.fig)
    
    def run_animation(self, num_frames=1000, interval=50):
        """
        Chạy animation thời gian thực.
        
        Args:
            num_frames (int): Số lượng frames
            interval (int): Khoảng thời gian giữa các frames (ms)
        """
        # Fix encoding for Windows terminal
        try:
            print(f"Chạy animation với {num_frames} frames, interval={interval}ms")
        except UnicodeEncodeError:
            print(f"Running animation with {num_frames} frames, interval={interval}ms")
        
        # Kết nối sự kiện nhấn phím
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # Tạo animation
        self.animation = FuncAnimation(
            self.fig, self.update_animation, frames=num_frames,
            init_func=self.init_animation, blit=True, interval=interval
        )
        
        # Hiển thị animation
        plt.tight_layout()
        plt.show()

def main():
    """Hàm chính"""
    # Fix encoding for Windows terminal
    try:
        print("Mô phỏng thời tiết thời gian thực")
    except UnicodeEncodeError:
        print("Real-time Weather Simulation")
    
    # Tham số mô phỏng
    width = 200
    height = 200
    frames = 1000
    interval = 50  # ms
    
    # Khởi tạo mô phỏng
    simulation = RealtimeWeatherSimulation(width, height)
    simulation.set_initial_conditions()
    
    # Chạy animation
    simulation.run_animation(num_frames=frames, interval=interval)
    
    # Fix encoding for Windows terminal
    try:
        print("Mô phỏng kết thúc")
    except UnicodeEncodeError:
        print("Simulation finished")

if __name__ == "__main__":
    main()
