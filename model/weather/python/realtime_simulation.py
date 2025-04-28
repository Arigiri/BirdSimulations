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
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

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
        
        print(f"Khởi tạo mô phỏng thời tiết thời gian thực ({width}x{height})")
        
        # Import module C++
        try:
            import cpp_weather
            self.cpp_weather = cpp_weather
            print("Đã tải module C++ thành công")
        except ImportError as e:
            print(f"Lỗi import module C++: {e}")
            print("Đảm bảo module C++ đã được biên dịch và có trong Python path")
            sys.exit(1)
        
        # Khởi tạo các đối tượng C++
        self.solver = self.cpp_weather.Solver(width, height, dx, kappa)
        self.wind_field = self.cpp_weather.WindField(width, height)
        self.temp_field = self.cpp_weather.TemperatureField(width, height)
        print("Đã khởi tạo các đối tượng C++")
        
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
        print("Thiết lập điều kiện ban đầu...")
        
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
            radius = np.random.uniform(self.width // 20, self.width // 10)
            self.temp_field.add_heat_source(x, y, strength, radius)
        
        # Tạo trường gió Gaussian
        self.wind_field.generate_gaussian_field(8, 2.0, self.width // 8)
        
        # Lấy dữ liệu ban đầu
        temp = self.get_temperature()
        
        # Cập nhật phạm vi nhiệt độ
        self.min_temp = max(0, np.min(temp) - 5)
        self.max_temp = min(45, np.max(temp) + 5)
        print(f"Phạm vi nhiệt độ: {self.min_temp:.1f} - {self.max_temp:.1f}")
        
        print("Đã thiết lập điều kiện ban đầu")
    
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
        self.colorbar.set_label('Nhiệt độ (°C)')
        
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
        self.ax.set_title(f'Mô phỏng thời tiết (t={self.time:.2f}s, bước {self.steps})')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        
        # Thêm chú thích
        plt.figtext(0.02, 0.02, 'Phím Q: Thoát', fontsize=9)
        
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
        self.ax.set_title(f'Mô phỏng thời tiết (t={self.time:.2f}s, bước {self.steps})\n'
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
        print(f"Chạy animation với {num_frames} frames, interval={interval}ms")
        
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
    print("Mô phỏng thời tiết thời gian thực")
    
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
    
    print("Mô phỏng kết thúc")

if __name__ == "__main__":
    main()
