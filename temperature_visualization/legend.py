"""
Module vẽ chú thích nhiệt độ.
"""

import pyglet
from .constants import (
    LEGEND_WIDTH, LEGEND_HEIGHT, LEGEND_X, LEGEND_Y, 
    LEGEND_SEGMENTS, ABS_MIN_TEMP, ABS_MAX_TEMP
)
from .utils import get_temperature_color

class LegendRenderer:
    """Lớp vẽ chú thích nhiệt độ cho bản đồ nhiệt."""
    
    def __init__(self, x=LEGEND_X, y=LEGEND_Y, width=LEGEND_WIDTH, height=LEGEND_HEIGHT):
        """
        Khởi tạo renderer chú thích.
        
        Args:
            x (int): Vị trí x của chú thích
            y (int): Vị trí y của chú thích
            width (int): Chiều rộng chú thích
            height (int): Chiều cao chú thích
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.segments = LEGEND_SEGMENTS
        self.segment_width = width / self.segments
        
    def draw(self, min_temp=ABS_MIN_TEMP, max_temp=ABS_MAX_TEMP):
        """
        Vẽ chú thích nhiệt độ.
        
        Args:
            min_temp (float): Nhiệt độ tối thiểu hiển thị
            max_temp (float): Nhiệt độ tối đa hiển thị
        """
        # Vẽ tiêu đề chú thích
        title = pyglet.text.Label(
            f'Nhiệt độ (°C): {min_temp:.1f} - {max_temp:.1f}',
            font_name='Arial',
            font_size=12,
            x=self.x,
            y=self.y + self.height + 5,
            color=(255, 255, 255, 255)
        )
        title.draw()
        
        # Vẽ thanh gradient màu
        for i in range(self.segments):
            normalized_temp = i / (self.segments - 1)  # Từ 0 đến 1
            
            # Xác định màu sắc cho từng phân đoạn của thanh gradient
            color = get_temperature_color(normalized_temp)
            
            # Vẽ mỗi phần của thanh gradient
            segment = pyglet.shapes.Rectangle(
                x=self.x + i * self.segment_width,
                y=self.y,
                width=self.segment_width,
                height=self.height,
                color=color
            )
            segment.opacity = 200
            segment.draw()
        
        # Vẽ đường viền cho thanh gradient
        border = pyglet.shapes.Rectangle(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            color=(50, 50, 50)
        )
        border.opacity = 150
        pyglet.gl.glLineWidth(1.5)
        border.draw()
