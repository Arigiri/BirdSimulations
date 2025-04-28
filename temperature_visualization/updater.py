"""
Module cập nhật dữ liệu nhiệt độ từ mô hình.
"""

import numpy as np
import random
from .utils import print_safe

class TemperatureUpdater:
    """Lớp xử lý cập nhật dữ liệu nhiệt độ từ mô hình."""
    
    def __init__(self):
        """Khởi tạo updater."""
        self.steps = 0
        
    def update_weather_model(self, weather_integration, dt=1.0, force_update=False):
        """
        Cập nhật mô hình thời tiết.
        
        Args:
            weather_integration: Đối tượng tích hợp thời tiết
            dt (float): Bước thời gian cập nhật
            force_update (bool): Buộc cập nhật ngay cả khi không cần thiết
            
        Returns:
            bool: True nếu cập nhật thành công, False nếu không
        """
        if not weather_integration:
            return False
            
        try:
            # Khởi tạo mô hình một lần (không reset khi force_update)
            if self.steps == 0:
                try:
                    weather_integration.initialize_weather()
                except Exception as e:
                    print_safe(f"Khởi tạo mô hình thời tiết không thành công: {e}",
                              f"Failed to initialize weather model: {e}")
            
            # Cập nhật mô hình
            if hasattr(weather_integration, 'update') and callable(getattr(weather_integration, 'update')):
                weather_integration.update(dt)
                self.steps += 1
                # Thêm nguồn nhiệt định kỳ
                # if hasattr(weather_integration, 'add_heat_source') and self.steps % 30 == 0:
                #     self._add_random_heat_source(weather_integration)
                
                return True
                
        except Exception as e:
            print_safe(f"Không thể cập nhật mô hình thời tiết: {e}", 
                      f"Cannot update weather model: {e}")
            
        return False
        
    def get_temperature_data(self, weather_integration):
        """
        Lấy dữ liệu nhiệt độ từ mô hình thời tiết.
        
        Args:
            weather_integration: Đối tượng tích hợp thời tiết
            
        Returns:
            tuple: (temp_array, min_temp, max_temp) hoặc (None, None, None) nếu lỗi
        """
        if not weather_integration:
            return None, None, None
            
        try:
            # Lấy dữ liệu nhiệt độ
            if hasattr(weather_integration, 'get_temperature_field'):
                temp_array = weather_integration.get_temperature_field()
                
                if temp_array is not None:
                    # Kiểm tra dữ liệu nhiệt độ
                    if np.all(temp_array == 0):
                        print_safe("Phát hiện trường nhiệt độ toàn 0, tạo lại gradient nhiệt độ...",
                                  "Detected all-zero temperature, recreating temperature gradient...")
                        
                        # Tái tạo dữ liệu nhiệt độ
                        weather_integration.initialize_weather()
                        temp_array = weather_integration.get_temperature_field()
                
                    # Tính min/max
                    min_temp = float(np.min(temp_array))
                    max_temp = float(np.max(temp_array))
                    
                    return temp_array, min_temp, max_temp
                    
        except Exception as e:
            print_safe(f"Lỗi khi lấy dữ liệu nhiệt độ: {e}", 
                      f"Error getting temperature data: {e}")
            
        return None, None, None
        
    def _add_random_heat_source(self, weather_integration):
        """
        Thêm một nguồn nhiệt ngẫu nhiên vào mô hình.
        
        Args:
            weather_integration: Đối tượng tích hợp thời tiết
        """
        try:
            # Lấy kích thước lưới
            grid_width = getattr(weather_integration, 'grid_width', 100)
            grid_height = getattr(weather_integration, 'grid_height', 100)
            
            # Danh sách các vị trí tiềm năng cho nguồn nhiệt
            heat_positions = [
                (int(grid_width * 0.1), int(grid_height * 0.1)),  # Góc trái dưới  
                (int(grid_width * 0.1), int(grid_height * 0.9)),  # Góc trái trên
                (int(grid_width * 0.9), int(grid_height * 0.1)),  # Góc phải dưới
                (int(grid_width * 0.9), int(grid_height * 0.9)),  # Góc phải trên
                (int(grid_width * 0.5), int(grid_height * 0.5)),  # Trung tâm
            ]
            
            # Lấy một vị trí ngẫu nhiên
            x, y = random.choice(heat_positions)
            strength = 15.0  # Cường độ nguồn nhiệt
            radius = 8  # Bán kính
            
            # Thêm nguồn nhiệt và in thông báo
            weather_integration.add_heat_source(x, y, strength, radius)
            print_safe(f"Thêm nguồn nhiệt tại ({x}, {y}) với strength={strength:.1f}", 
                      f"Added heat source at ({x}, {y}) with strength={strength:.1f}")
                      
        except Exception as e:
            print_safe(f"Không thể thêm nguồn nhiệt: {e}", 
                      f"Cannot add heat source: {e}")
