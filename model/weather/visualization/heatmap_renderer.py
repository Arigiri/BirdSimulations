"""
Module hiển thị thời tiết (nhiệt độ và gió) cho mô phỏng.
"""

import numpy as np
import pyglet
from pyglet.gl import *
from utils.config import HEATMAP_ALPHA, WIND_SAMPLING, WIND_SCALE, WIND_COLOR

class HeatmapRenderer:
    """
    Lớp hiển thị trường nhiệt độ dưới dạng bản đồ nhiệt (heatmap).
    """
    
    def __init__(self, temp_field, window_width, window_height):
        """
        Khởi tạo trình hiển thị bản đồ nhiệt.
        
        Args:
            temp_field: Đối tượng TemperatureField từ module C++
            window_width: Chiều rộng cửa sổ hiển thị
            window_height: Chiều cao cửa sổ hiển thị
        """
        self.temp_field = temp_field
        self.window_width = window_width
        self.window_height = window_height
        
        # Kích thước lưới
        self.grid_width = None
        self.grid_height = None
        
        # Cập nhật thông tin kích thước từ temp_field
        self.update_grid_dimensions()
        
        # Tạo texture cho heatmap
        self.texture = None
        self.create_texture()
        
        # Phạm vi nhiệt độ để tô màu
        self.min_temp = 0.0
        self.max_temp = 40.0
        
        # Trạng thái hiển thị
        self.visible = True
        
        # Alpha (độ trong suốt)
        self.alpha = HEATMAP_ALPHA
    
    def update_grid_dimensions(self):
        """Cập nhật thông tin kích thước lưới từ trường nhiệt độ."""
        try:
            # Lấy kích thước từ temp_field
            temp_data = self.temp_field.get_temperature()
            size = len(temp_data)
            
            # Xác định kích thước lưới từ tổng số phần tử
            # Giả sử lưới vuông nếu không xác định được chính xác
            grid_size = int(np.sqrt(size))
            
            if grid_size * grid_size == size:
                # Lưới vuông
                self.grid_width = grid_size
                self.grid_height = grid_size
            else:
                # Nếu không phải lưới vuông, thử đoán kích thước
                # (Kích thước thực tế nên được lấy từ temp_field)
                self.grid_width = grid_size
                self.grid_height = size // grid_size
                
            print(f"Kích thước lưới nhiệt: {self.grid_width}x{self.grid_height}")
        except Exception as e:
            print(f"Lỗi khi cập nhật kích thước lưới: {e}")
            # Giá trị mặc định nếu có lỗi
            self.grid_width = 50
            self.grid_height = 50
    
    def create_texture(self):
        """Tạo texture cho hiển thị heatmap."""
        try:
            # Tạo texture trống
            if not self.grid_width or not self.grid_height:
                return
            
            self.texture = pyglet.image.Texture.create(
                self.grid_width, self.grid_height, 
                GL_RGBA, 
                rectangle=True
            )
        except Exception as e:
            print(f"Lỗi khi tạo texture: {e}")
            self.texture = None
    
    def temperature_to_color(self, temp):
        """
        Chuyển đổi nhiệt độ thành màu RGB.
        
        Args:
            temp: Giá trị nhiệt độ
            
        Returns:
            tuple: (R, G, B) trong khoảng 0-255
        """
        # Chuẩn hóa nhiệt độ về khoảng [0, 1]
        t = max(0.0, min(1.0, (temp - self.min_temp) / (self.max_temp - self.min_temp)))
        
        # Blue -> Cyan -> Green -> Yellow -> Red
        if t < 0.25:
            # Blue to Cyan (0.0 -> 0.25)
            # Thay đổi từ (0,0,255) -> (0,255,255)
            t_scaled = t * 4.0  # 0.0 -> 1.0
            r = 0
            g = int(255 * t_scaled)
            b = 255
        elif t < 0.5:
            # Cyan to Green (0.25 -> 0.5)
            # Thay đổi từ (0,255,255) -> (0,255,0)
            t_scaled = (t - 0.25) * 4.0  # 0.0 -> 1.0
            r = 0
            g = 255
            b = int(255 * (1.0 - t_scaled))
        elif t < 0.75:
            # Green to Yellow (0.5 -> 0.75)
            # Thay đổi từ (0,255,0) -> (255,255,0)
            t_scaled = (t - 0.5) * 4.0  # 0.0 -> 1.0
            r = int(255 * t_scaled)
            g = 255
            b = 0
        else:
            # Yellow to Red (0.75 -> 1.0)
            # Thay đổi từ (255,255,0) -> (255,0,0)
            t_scaled = (t - 0.75) * 4.0  # 0.0 -> 1.0
            r = 255
            g = int(255 * (1.0 - t_scaled))
            b = 0
            
        return (r, g, b)
    
    def update_temperature_range(self, min_temp, max_temp):
        """
        Cập nhật phạm vi nhiệt độ để hiển thị màu chính xác hơn.
        
        Args:
            min_temp: Nhiệt độ thấp nhất
            max_temp: Nhiệt độ cao nhất
        """
        self.min_temp = min_temp
        self.max_temp = max_temp
    
    def update_texture(self):
        """Cập nhật texture dựa trên dữ liệu nhiệt độ hiện tại."""
        try:
            if not self.texture or not self.grid_width or not self.grid_height:
                return
                
            # Lấy dữ liệu nhiệt độ và reshape thành mảng 2D
            temps = self.temp_field.get_temperature().reshape(self.grid_height, self.grid_width)
            
            # Xác định phạm vi nhiệt độ tự động nếu cần
            min_temp = np.min(temps)
            max_temp = np.max(temps)
            
            # Mở rộng phạm vi một chút để có hiệu ứng đẹp hơn
            self.min_temp = min_temp - 3.0
            self.max_temp = max_temp + 3.0
            
            # Tạo mảng chứa dữ liệu pixel RGBA cho texture
            texture_data = np.zeros((self.grid_height, self.grid_width, 4), dtype=np.uint8)
            
            # Chuyển đổi giá trị nhiệt độ thành màu
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    r, g, b = self.temperature_to_color(temps[y, x])
                    texture_data[y, x, 0] = r
                    texture_data[y, x, 1] = g
                    texture_data[y, x, 2] = b
                    texture_data[y, x, 3] = int(self.alpha * 255)  # Kênh alpha
            
            # Cập nhật texture từ mảng pixel
            self.texture.blit_into(
                pyglet.image.ImageData(
                    self.grid_width, self.grid_height,
                    'RGBA', texture_data.tobytes(),
                    -4 * self.grid_width
                ),
                0, 0, 0
            )
        except Exception as e:
            print(f"Lỗi khi cập nhật texture: {e}")
    
    def set_alpha(self, alpha):
        """Cập nhật độ trong suốt của heatmap."""
        self.alpha = max(0.0, min(1.0, alpha))
    
    def toggle_visibility(self):
        """Bật/tắt hiển thị heatmap."""
        self.visible = not self.visible
        return self.visible
    
    def draw(self):
        """Vẽ bản đồ nhiệt."""
        if not self.visible or not self.texture:
            return
            
        # Cập nhật texture trước khi vẽ
        self.update_texture()
        
        # Cấu hình OpenGL
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Vẽ texture lên toàn bộ cửa sổ
        glClear(GL_COLOR_BUFFER_BIT)
        self.texture.width = self.window_width
        self.texture.height = self.window_height
        self.texture.blit(0, 0)
        
        # Đặt lại OpenGL
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

class WindFieldRenderer:
    """
    Lớp hiển thị trường gió bằng các vector mũi tên.
    """
    
    def __init__(self, wind_field, window_width, window_height):
        """
        Khởi tạo trình hiển thị trường gió.
        
        Args:
            wind_field: Đối tượng WindField từ module C++
            window_width: Chiều rộng cửa sổ hiển thị
            window_height: Chiều cao cửa sổ hiển thị
        """
        self.wind_field = wind_field
        self.window_width = window_width
        self.window_height = window_height
        
        # Kích thước lưới
        self.grid_width = None
        self.grid_height = None
        
        # Cập nhật thông tin kích thước từ wind_field
        self.update_grid_dimensions()
        
        # Mật độ hiển thị (hiển thị 1 mũi tên mỗi sampling_factor ô lưới)
        self.sampling_factor = WIND_SAMPLING
        
        # Độ dài và độ rộng của mũi tên
        self.scale_factor = WIND_SCALE
        
        # Màu sắc mũi tên
        self.arrow_color = WIND_COLOR
        
        # Trạng thái hiển thị
        self.visible = True
        
        # Batch cho hiệu suất tốt hơn
        self.batch = pyglet.graphics.Batch()
        self.arrow_vertices = []
    
    def update_grid_dimensions(self):
        """Cập nhật thông tin kích thước lưới từ trường gió."""
        try:
            # Lấy kích thước từ wind_field
            wind_x = self.wind_field.get_wind_x()
            size = len(wind_x)
            
            # Xác định kích thước lưới từ tổng số phần tử
            grid_size = int(np.sqrt(size))
            
            if grid_size * grid_size == size:
                # Lưới vuông
                self.grid_width = grid_size
                self.grid_height = grid_size
            else:
                # Nếu không phải lưới vuông, thử đoán kích thước
                self.grid_width = grid_size
                self.grid_height = size // grid_size
                
            print(f"Kích thước lưới gió: {self.grid_width}x{self.grid_height}")
        except Exception as e:
            print(f"Lỗi khi cập nhật kích thước lưới gió: {e}")
            # Giá trị mặc định nếu có lỗi
            self.grid_width = 50
            self.grid_height = 50
    
    def toggle_visibility(self):
        """Bật/tắt hiển thị trường gió."""
        self.visible = not self.visible
        return self.visible
    
    def draw_arrow(self, x, y, dx, dy):
        """
        Vẽ một mũi tên gió.
        
        Args:
            x, y: Vị trí bắt đầu mũi tên
            dx, dy: Vector gió (được thay đổi tỷ lệ)
        """
        # Tính vị trí kết thúc mũi tên
        end_x = x + dx
        end_y = y + dy
        
        # Vẽ thân mũi tên
        pyglet.graphics.draw(
            2, pyglet.gl.GL_LINES,
            ('v2f', (x, y, end_x, end_y)),
            ('c4B', self.arrow_color * 2)
        )
        
        # Tính toán cho mũi tên
        arrow_size = 3  # Kích thước mũi tên
        angle = np.arctan2(dy, dx)
        arrow1_angle = angle + np.pi * 0.8  # Góc cho nửa đầu tiên của mũi tên
        arrow2_angle = angle - np.pi * 0.8  # Góc cho nửa thứ hai của mũi tên
        
        arrow1_x = end_x + arrow_size * np.cos(arrow1_angle)
        arrow1_y = end_y + arrow_size * np.sin(arrow1_angle)
        arrow2_x = end_x + arrow_size * np.cos(arrow2_angle)
        arrow2_y = end_y + arrow_size * np.sin(arrow2_angle)
        
        # Vẽ hai nửa của mũi tên
        pyglet.graphics.draw(
            2, pyglet.gl.GL_LINES,
            ('v2f', (end_x, end_y, arrow1_x, arrow1_y)),
            ('c4B', self.arrow_color * 2)
        )
        
        pyglet.graphics.draw(
            2, pyglet.gl.GL_LINES,
            ('v2f', (end_x, end_y, arrow2_x, arrow2_y)),
            ('c4B', self.arrow_color * 2)
        )
    
    def update_arrows(self):
        """Cập nhật vị trí và hướng của mũi tên gió."""
        try:
            # Lấy dữ liệu gió
            wind_x = self.wind_field.get_wind_x().reshape(self.grid_height, self.grid_width)
            wind_y = self.wind_field.get_wind_y().reshape(self.grid_height, self.grid_width)
            
            # Tính toán khoảng cách ô lưới trên màn hình
            cell_width = self.window_width / self.grid_width
            cell_height = self.window_height / self.grid_height
            
            # Lưu trữ thông tin mũi tên để vẽ sau
            self.arrow_vertices = []
            
            # Lấy mẫu mũi tên để hiển thị (không vẽ tất cả các ô lưới)
            for y in range(0, self.grid_height, self.sampling_factor):
                for x in range(0, self.grid_width, self.sampling_factor):
                    # Tính tọa độ trên màn hình
                    screen_x = (x + 0.5) * cell_width
                    screen_y = (y + 0.5) * cell_height
                    
                    # Lấy vector gió và thay đổi tỷ lệ
                    dx = wind_x[y, x] * self.scale_factor
                    dy = wind_y[y, x] * self.scale_factor
                    
                    # Thêm thông tin mũi tên
                    self.arrow_vertices.append((screen_x, screen_y, dx, dy))
                    
        except Exception as e:
            print(f"Lỗi khi cập nhật mũi tên gió: {e}")
    
    def draw(self):
        """Vẽ trường gió."""
        if not self.visible or not self.grid_width or not self.grid_height:
            return
            
        # Cập nhật mũi tên trước khi vẽ
        self.update_arrows()
        
        # Cấu hình OpenGL
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(1.0)
        
        # Vẽ tất cả mũi tên
        for x, y, dx, dy in self.arrow_vertices:
            self.draw_arrow(x, y, dx, dy)
            
        # Đặt lại OpenGL
        glDisable(GL_BLEND)
