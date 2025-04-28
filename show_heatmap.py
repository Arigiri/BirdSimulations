#!/usr/bin/env python
"""
Hiển thị biểu đồ nhiệt độc lập sử dụng renderer của dự án chính.
"""

import os
import sys
import time
import pyglet
import numpy as np
from pyglet.window import key

# Đảm bảo import các module dự án
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.config import WINDOW_WIDTH, WINDOW_HEIGHT
from model.weather.visualization.heatmap_renderer import HeatmapRenderer, WindFieldRenderer

# Import các module thời tiết C++
try:
    from model.weather.python.cpp_weather import TemperatureField, WindField, Solver
    print("Đã tải module C++ thành công")
except ImportError as e:
    print(f"Lỗi khi import module C++: {e}")
    print("Đảm bảo module C++ đã được biên dịch")
    sys.exit(1)

class HeatmapSimulation:
    """Mô phỏng biểu đồ nhiệt độ độc lập."""
    
    def __init__(self, width=200, height=200, window_width=800, window_height=600):
        """Khởi tạo mô phỏng biểu đồ nhiệt."""
        self.width = width
        self.height = height
        self.window_width = window_width
        self.window_height = window_height
        
        # Khởi tạo cửa sổ Pyglet
        self.window = pyglet.window.Window(
            width=window_width,
            height=window_height,
            caption="Biểu đồ nhiệt độ"
        )
        
        # Khởi tạo các trường dữ liệu C++
        self.temp_field = TemperatureField(width, height)
        self.wind_field = WindField(width, height)
        self.solver = Solver(width, height, 1.0, 0.05)  # dx=1.0, kappa=0.05
        
        # Khởi tạo renderer
        self.heatmap_renderer = HeatmapRenderer(self.temp_field, window_width, window_height)
        self.wind_renderer = WindFieldRenderer(self.wind_field, window_width, window_height)
        
        # Thiết lập sự kiện
        self.window.on_draw = self.on_draw
        self.window.on_key_press = self.on_key_press
        
        # Thông số mô phỏng
        self.time = 0.0
        self.steps = 0
        self.show_wind = True
        self.running = True
        
        # Thiết lập đồng hồ cập nhật
        pyglet.clock.schedule_interval(self.update, 1/60.0)
    
    def set_initial_conditions(self):
        """Thiết lập điều kiện ban đầu cho trường nhiệt độ và gió."""
        print("Thiết lập điều kiện ban đầu...")
        
        # Tạo gradient nhiệt độ theo hướng North-South
        self.temp_field.set_gradient(10.0, 30.0, 1)  # 1 = NORTH_SOUTH
        
        # Thêm nguồn nhiệt ở giữa
        center_x = self.width // 2
        center_y = self.height // 2
        self.temp_field.add_heat_source(center_x, center_y, 15.0, self.width // 10)
        
        # Thêm nguồn nhiệt ngẫu nhiên
        # np.random.seed(42)  # Để tái tạo kết quả
        num_sources = 5
        for _ in range(num_sources):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            strength = np.random.uniform(5.0, 10.0)
            radius = np.random.uniform(self.width // 20, self.width // 10)
            self.temp_field.add_heat_source(x, y, strength, radius)
        
        # Tạo trường gió Gaussian
        self.wind_field.generate_gaussian_field(8, 2.0, self.width // 8)
        
        print("Đã thiết lập điều kiện ban đầu")
    
    def update(self, dt):
        """Cập nhật mô phỏng."""
        if not self.running:
            return
            
        # Lấy dữ liệu
        temp = np.array(self.temp_field.get_temperature())
        wind_x = np.array(self.wind_field.get_wind_x())
        wind_y = np.array(self.wind_field.get_wind_y())
        
        # Tính bước thời gian
        sim_dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Cập nhật nhiệt độ
        new_temp = self.solver.solve_rk4_step(temp, wind_x, wind_y, sim_dt)
        self.temp_field.set_temperature(new_temp)
        
        # Đôi khi cập nhật trường gió để tạo sự thay đổi
        if self.steps % 20 == 0 and self.steps > 0:
            num_vortices = np.random.randint(3, 10)
            strength = np.random.uniform(1.0, 3.0)
            radius = np.random.uniform(self.width // 10, self.width // 5)
            self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
        
        # Cập nhật trạng thái
        self.time += sim_dt
        self.steps += 1
        
        # Cập nhật tiêu đề cửa sổ
        self.window.set_caption(
            f"Biểu đồ nhiệt độ - t={self.time:.2f}s - Bước {self.steps}"
        )
    
    def on_draw(self):
        """Xử lý sự kiện vẽ."""
        self.window.clear()
        
        # Vẽ biểu đồ nhiệt
        self.heatmap_renderer.draw()
        
        # Vẽ trường gió nếu được bật
        if self.show_wind:
            self.wind_renderer.draw()
        
        # Hiển thị thông tin trạng thái
        self.draw_status()
    
    def draw_status(self):
        """Hiển thị thông tin trạng thái."""
        status_text = [
            f"Thời gian: {self.time:.2f}s",
            f"Bước: {self.steps}",
            f"Kích thước lưới: {self.width}x{self.height}",
            f"Gió: {'Hiện' if self.show_wind else 'Ẩn'} (phím W để bật/tắt)",
            "Q: Thoát, Space: Tạm dừng/Tiếp tục"
        ]
        
        y = self.window_height - 20
        for line in status_text:
            pyglet.text.Label(
                line,
                font_name='Arial',
                font_size=12,
                x=10, y=y,
                color=(255, 255, 255, 255)
            ).draw()
            y -= 20
    
    def on_key_press(self, symbol, modifiers):
        """Xử lý sự kiện phím."""
        if symbol == key.Q:
            pyglet.app.exit()
        elif symbol == key.W:
            self.show_wind = not self.show_wind
        elif symbol == key.SPACE:
            self.running = not self.running
    
    def run(self):
        """Chạy mô phỏng."""
        self.set_initial_conditions()
        pyglet.app.run()

def main():
    """Hàm chính."""
    print("Khởi tạo mô phỏng biểu đồ nhiệt độ...")
    
    # Lấy kích thước cửa sổ từ config
    window_width = WINDOW_WIDTH
    window_height = WINDOW_HEIGHT
    
    # Kích thước lưới mô phỏng
    grid_width = 200
    grid_height = 200
    
    # Khởi tạo và chạy mô phỏng
    simulation = HeatmapSimulation(
        width=grid_width,
        height=grid_height,
        window_width=window_width,
        window_height=window_height
    )
    simulation.run()

if __name__ == "__main__":
    main()