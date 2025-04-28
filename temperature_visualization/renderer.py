"""
Module vẽ bản đồ nhiệt độ với kỹ thuật batch rendering.
"""

import numpy as np
import pyglet
from .constants import (
    DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP, 
    DEFAULT_OPACITY, DEFAULT_DETAIL_LEVEL
)
from .utils import normalize_temperature, get_temperature_color, calculate_sample_rate
from .legend import LegendRenderer
from .updater import TemperatureUpdater

class TemperatureRenderer:
    """Lớp vẽ bản đồ nhiệt độ với kỹ thuật batch rendering."""
    
    def __init__(self, window_width, window_height, info_panel_width):
        """
        Khởi tạo renderer bản đồ nhiệt độ.
        
        Args:
            window_width (int): Chiều rộng cửa sổ
            window_height (int): Chiều cao cửa sổ
            info_panel_width (int): Chiều rộng panel thông tin
        """
        self.window_width = window_width
        self.window_height = window_height
        self.info_panel_width = info_panel_width
        
        # Các renderer phụ trợ
        self.legend_renderer = LegendRenderer()
        self.updater = TemperatureUpdater()
        
        # Cache để tối ưu hiệu suất
        self.temp_map_batch = None
        self.temp_map_rects = []
        self.last_temp_array = None
        self.last_min_temp = DEFAULT_MIN_TEMP
        self.last_max_temp = DEFAULT_MAX_TEMP
        
        # Cấu hình mặc định
        self.opacity = DEFAULT_OPACITY
        self.detail_level = DEFAULT_DETAIL_LEVEL
        
    def reset_cache(self):
        """Reset bộ đệm để buộc vẽ lại toàn bộ bản đồ."""
        self.temp_map_batch = None
        self.temp_map_rects = []
        self.last_temp_array = None
        self.last_min_temp = DEFAULT_MIN_TEMP
        self.last_max_temp = DEFAULT_MAX_TEMP
        
    def draw(self, weather_integration, weather_available=True, detail_level=None, force_update=False):
        """
        Vẽ bản đồ nhiệt độ.
        
        Args:
            weather_integration: Đối tượng tích hợp thời tiết
            weather_available (bool): Flag cho biết module thời tiết có khả dụng không
            detail_level (int): Mức độ chi tiết, từ 1 (cao nhất) đến 5 (thấp nhất)
            force_update (bool): Buộc cập nhật dữ liệu ngay cả khi không thay đổi
        """
        if not weather_available or not weather_integration:
            return
            
        # Sử dụng detail_level được cung cấp hoặc giá trị mặc định
        detail_level = detail_level or self.detail_level
        
        # 1. Cập nhật mô hình thời tiết
        self.updater.update_weather_model(weather_integration, dt=0.2, force_update=force_update)
        
        # 2. Lấy dữ liệu nhiệt độ
        temp_array, min_temp, max_temp = self.updater.get_temperature_data(weather_integration)
        
        if temp_array is None:
            return
            
        # 3. Kiểm tra xem dữ liệu đã thay đổi chưa
        data_changed = (
            self.last_temp_array is None or 
            not np.array_equal(temp_array, self.last_temp_array) or
            self.last_min_temp != min_temp or 
            self.last_max_temp != max_temp or
            force_update
        )
        
        # 4. Cập nhật cache
        self.last_temp_array = temp_array.copy()
        self.last_min_temp = min_temp
        self.last_max_temp = max_temp
        
        # 5. Nếu dữ liệu không thay đổi và batch đã tồn tại, chỉ vẽ batch
        if not data_changed and self.temp_map_batch is not None:
            self.temp_map_batch.draw()
            self.legend_renderer.draw(min_temp, max_temp)
            return
            
        # 6. Lấy kích thước mảng nhiệt độ
        grid_height, grid_width = temp_array.shape
        
        # 7. Xác định kích thước của mỗi ô trên màn hình
        cell_width = (self.window_width - self.info_panel_width) / grid_width
        cell_height = self.window_height / grid_height
        
        # 8. Tính toán tỷ lệ lấy mẫu dựa trên mức độ chi tiết
        sample_rate = calculate_sample_rate(detail_level)
        
        # 9. Tạo batch mới nếu cần
        if self.temp_map_batch is None or data_changed:
            # Xóa batch cũ và tạo mới
            self.temp_map_batch = pyglet.graphics.Batch()
            self.temp_map_rects = []
            
            # Vẽ nhiệt độ với tỷ lệ lấy mẫu
            for y in range(0, grid_height, sample_rate):
                for x in range(0, grid_width, sample_rate):
                    # Vị trí trên màn hình
                    screen_x = x * cell_width
                    screen_y = y * cell_height
                    
                    # Lấy nhiệt độ tại điểm (x, y)
                    temperature = temp_array[y, x]
                    
                    # Chuẩn hóa nhiệt độ (0.0 - 1.0)
                    normalized_temp = normalize_temperature(temperature, min_temp, max_temp)
                    
                    # Ánh xạ từ nhiệt độ sang màu sắc
                    color = get_temperature_color(normalized_temp)
                    
                    # Điều chỉnh kích thước mỗi ô để phù hợp với tỷ lệ lấy mẫu
                    rect_width = cell_width * sample_rate
                    rect_height = cell_height * sample_rate
                    
                    # Vẽ hình chữ nhật biểu diễn nhiệt độ và thêm vào batch
                    rect = pyglet.shapes.Rectangle(
                        x=screen_x, 
                        y=screen_y,
                        width=rect_width,
                        height=rect_height,
                        color=color,
                        batch=self.temp_map_batch
                    )
                    rect.opacity = self.opacity
                    self.temp_map_rects.append(rect)
        
        # 10. Vẽ tất cả các hình chữ nhật bằng batch (nhanh hơn nhiều so với vẽ từng cái)
        self.temp_map_batch.draw()
        
        # 11. Vẽ chú thích nhiệt độ
        self.legend_renderer.draw(min_temp, max_temp)
