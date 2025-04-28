"""
Module visualization nhiệt độ - cung cấp các lớp để vẽ và quản lý bản đồ nhiệt độ.
"""

from .renderer import TemperatureRenderer
from .legend import LegendRenderer
from .updater import TemperatureUpdater

# Hàm tiện ích để tạo nhanh một renderer hoàn chỉnh
def create_temperature_visualizer(window_width, window_height, info_panel_width):
    """
    Tạo một renderer nhiệt độ hoàn chỉnh.
    
    Args:
        window_width (int): Chiều rộng cửa sổ
        window_height (int): Chiều cao cửa sổ
        info_panel_width (int): Chiều rộng của panel thông tin
        
    Returns:
        TemperatureRenderer: Renderer đã được cấu hình
    """
    return TemperatureRenderer(window_width, window_height, info_panel_width)
