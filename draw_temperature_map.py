"""
Mô-đun chứa hàm vẽ bản đồ nhiệt độ với khả năng wrap-around.
Đây là wrapper cho module temperature_visualization mới.
"""

import numpy as np
from utils.config import WINDOW_WIDTH, WINDOW_HEIGHT, INFO_PANEL_WIDTH
from temperature_visualization import TemperatureRenderer

# Tạo đối tượng renderer toàn cục
_temperature_renderer = None

def reset_temp_map_cache():
    """Reset cache của bản đồ nhiệt, buộc phải vẽ lại toàn bộ bản đồ"""
    global _temperature_renderer
    if _temperature_renderer:
        _temperature_renderer.reset_cache()
    try:
        from main import print_safe
        print_safe("Đã reset cache bản đồ nhiệt", "Temperature map cache has been reset")
    except ImportError:
        try:
            print("Đã reset cache bản đồ nhiệt")
        except UnicodeEncodeError:
            print("Temperature map cache has been reset")

def draw_temperature_map(weather_integration, WEATHER_AVAILABLE, detail_level=2, force_update=False):
    """Vẽ bản đồ nhiệt độ với khả năng wrap-around khi vượt quá kích thước màn hình
    
    Args:
        weather_integration: Đối tượng tích hợp thời tiết
        WEATHER_AVAILABLE: Flag cho biết module thời tiết có khả dụng không
        detail_level: Mức độ chi tiết, từ 1 (cao nhất) đến 5 (thấp nhất)
        force_update: Buộc cập nhật dữ liệu ngay cả khi không thay đổi
    """
    global _temperature_renderer
    
    # Khởi tạo renderer nếu cần
    if _temperature_renderer is None:
        _temperature_renderer = TemperatureRenderer(WINDOW_WIDTH, WINDOW_HEIGHT, INFO_PANEL_WIDTH)
    
    # Sử dụng renderer mới
    _temperature_renderer.draw(weather_integration, WEATHER_AVAILABLE, detail_level, force_update)

def draw_temperature_legend(min_temp, max_temp):
    """Vẽ chú thích nhiệt độ (chỉ giữ lại cho tương thích ngược)
    
    Chú ý: Hàm này không làm gì vì legend đã được vẽ tự động bởi TemperatureRenderer
    """
    pass
