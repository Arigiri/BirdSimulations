"""
Module visualization cho hệ thống mô phỏng thời tiết.
Cung cấp các class để vẽ bản đồ nhiệt độ và trường gió.
"""

import numpy as np
import pyglet
import math
from utils.config import GRID_SIZE_X, GRID_SIZE_Y

class HeatmapRenderer:
    """Lớp vẽ bản đồ nhiệt độ sử dụng Pyglet"""
    
    def __init__(self, temp_field, width, height):
        """Khởi tạo bản đồ nhiệt với kích thước xác định
        
        Args:
            temp_field: Đối tượng trường nhiệt độ từ module C++
            width: Chiều rộng cửa sổ
            height: Chiều cao cửa sổ
        """
        self.temp_field = temp_field
        self.width = width
        self.height = height
        # Khởi tạo mảng nhiệt độ rỗng
        self.temperature_field = np.zeros((GRID_SIZE_Y, GRID_SIZE_X))
        # Giá trị nhiệt độ min và max
        self.min_temp = 0
        self.max_temp = 100
        
    def update(self, temperature_field=None, min_temp=None, max_temp=None):
        """Cập nhật dữ liệu nhiệt độ"""
        if temperature_field is not None:
            self.temperature_field = temperature_field
        if min_temp is not None:
            self.min_temp = min_temp
        if max_temp is not None:
            self.max_temp = max_temp
    
    def _get_color_for_temperature(self, temperature):
        """Chuyển đổi nhiệt độ thành màu sắc (gradient từ lạnh đến nóng)"""
        # Chuẩn hóa nhiệt độ về khoảng [0, 1]
        temp_range = self.max_temp - self.min_temp
        if temp_range == 0:  # Tránh chia cho 0
            normalized_temp = 0.5
        else:
            normalized_temp = max(0, min(1, (temperature - self.min_temp) / temp_range))
        
        # Ánh xạ từ nhiệt độ sang màu sắc (dùng cơ chế gradient)
        if normalized_temp < 0.25:  # Màu xanh -> xanh lá
            r = 0
            g = int(255 * (normalized_temp / 0.25))
            b = int(255 * (1 - normalized_temp / 0.25))
        elif normalized_temp < 0.5:  # Màu xanh lá -> vàng
            r = int(255 * ((normalized_temp - 0.25) / 0.25))
            g = 255
            b = 0
        elif normalized_temp < 0.75:  # Màu vàng -> cam
            r = 255
            g = int(255 * (1 - (normalized_temp - 0.5) / 0.25))
            b = 0
        else:  # Màu cam -> đỏ
            r = 255
            g = 0
            b = int(255 * ((normalized_temp - 0.75) / 0.25))
        
        return (r, g, b)
    
    def draw(self, window_width, window_height, opacity=150):
        """Vẽ bản đồ nhiệt lên màn hình"""
        if self.temperature_field is None:
            return
        
        # Lấy kích thước mảng nhiệt độ
        grid_height, grid_width = self.temperature_field.shape
        
        # Xác định kích thước mỗi ô trên màn hình
        cell_width = window_width / grid_width
        cell_height = window_height / grid_height
        
        # Vẽ các ô nhiệt độ
        for y in range(grid_height):
            for x in range(grid_width):
                # Tính toán vị trí thực tế trên màn hình
                screen_x = x * cell_width
                screen_y = y * cell_height
                
                # Lấy giá trị nhiệt độ tại vị trí (x, y)
                temperature = self.temperature_field[y, x]
                
                # Lấy màu sắc dựa trên nhiệt độ
                color = self._get_color_for_temperature(temperature)
                
                # Vẽ hình chữ nhật biểu diễn nhiệt độ
                rect = pyglet.shapes.Rectangle(
                    x=screen_x, 
                    y=screen_y,
                    width=cell_width,
                    height=cell_height,
                    color=color
                )
                rect.opacity = opacity
                rect.draw()

class WindFieldRenderer:
    """Lớp vẽ trường gió sử dụng Pyglet"""
    
    def __init__(self, wind_field, width, height):
        """Khởi tạo trường gió với kích thước xác định
        
        Args:
            wind_field: Đối tượng trường gió từ module C++
            width: Chiều rộng cửa sổ
            height: Chiều cao cửa sổ
        """
        self.wind_field = wind_field
        self.width = width
        self.height = height
        # Khởi tạo mảng vectơ gió rỗng (u, v là các thành phần vận tốc)
        self.wind_field_u = np.zeros((GRID_SIZE_Y, GRID_SIZE_X))  # thành phần gió theo hướng x
        self.wind_field_v = np.zeros((GRID_SIZE_Y, GRID_SIZE_X))  # thành phần gió theo hướng y
    
    def update(self, wind_field_u=None, wind_field_v=None):
        """Cập nhật dữ liệu trường gió"""
        if wind_field_u is not None:
            self.wind_field_u = wind_field_u
        if wind_field_v is not None:
            self.wind_field_v = wind_field_v
    
    def draw(self, window_width, window_height, scale=1.0, arrow_color=(0, 0, 255), opacity=200):
        """Vẽ trường gió lên màn hình với các mũi tên"""
        if self.wind_field_u is None or self.wind_field_v is None:
            return
        
        # Lấy kích thước mảng trường gió
        grid_height, grid_width = self.wind_field_u.shape
        
        # Xác định kích thước mỗi ô trên màn hình
        cell_width = window_width / grid_width
        cell_height = window_height / grid_height
        
        # Vẽ các mũi tên biểu diễn hướng và độ mạnh của gió
        for y in range(grid_height):
            for x in range(grid_width):
                # Chỉ vẽ một số điểm để không quá dày đặc
                if x % 3 == 0 and y % 3 == 0:
                    # Tính toán vị trí trung tâm của ô trên màn hình
                    center_x = (x + 0.5) * cell_width
                    center_y = (y + 0.5) * cell_height
                    
                    # Lấy thành phần gió tại vị trí (x, y)
                    u = self.wind_field_u[y, x]
                    v = self.wind_field_v[y, x]
                    
                    # Tính độ dài mũi tên dựa trên tốc độ gió
                    magnitude = np.sqrt(u*u + v*v)
                    arrow_length = magnitude * scale * cell_width * 0.8  # điều chỉnh độ dài phù hợp
                    
                    if magnitude > 0:
                        # Tính toán điểm cuối của mũi tên
                        end_x = center_x + arrow_length * u / magnitude
                        end_y = center_y + arrow_length * v / magnitude
                        
                        # Vẽ thân mũi tên
                        line = pyglet.shapes.Line(
                            center_x, center_y, end_x, end_y,
                            color=arrow_color, width=1
                        )
                        line.opacity = opacity
                        line.draw()
                        
                        # Vẽ đầu mũi tên
                        arrow_head_size = min(cell_width, cell_height) * 0.2
                        angle = math.atan2(v, u)
                        
                        # Tính toán 2 điểm cho đầu mũi tên
                        head1_x = end_x - arrow_head_size * math.cos(angle + math.pi/6)
                        head1_y = end_y - arrow_head_size * math.sin(angle + math.pi/6)
                        head2_x = end_x - arrow_head_size * math.cos(angle - math.pi/6)
                        head2_y = end_y - arrow_head_size * math.sin(angle - math.pi/6)
                        
                        # Vẽ 2 đường cho đầu mũi tên
                        head_line1 = pyglet.shapes.Line(
                            end_x, end_y, head1_x, head1_y,
                            color=arrow_color, width=1
                        )
                        head_line1.opacity = opacity
                        head_line1.draw()
                        
                        head_line2 = pyglet.shapes.Line(
                            end_x, end_y, head2_x, head2_y,
                            color=arrow_color, width=1
                        )
                        head_line2.opacity = opacity
                        head_line2.draw()