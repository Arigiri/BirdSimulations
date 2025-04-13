"""
Module chứa các hàm tính toán liên quan đến trái cây
"""

import random
import math
from utils.vector import Vector2D
from utils.config import WINDOW_WIDTH, WINDOW_HEIGHT, RIPENING_RATE

def calculate_ripeness(time_existed):
    """
    Tính toán độ chín của quả dựa trên thời gian tồn tại
    
    Args:
        time_existed (float): Thời gian quả đã tồn tại (giây)
        
    Returns:
        float: Độ chín của quả (0 đến 2, với 0 là chưa chín, 1 là chín, 2 là quá chín)
    """
    # Áp dụng công thức độ chín: ripeness = RIPENING_RATE * time_existed
    # Độ chín tăng tuyến tính theo thời gian
    ripeness = RIPENING_RATE * time_existed
    # Giới hạn độ chín tối đa là 2.0
    return min(ripeness, 2.0)

def generate_fruit_position(location=None):
    """
    Tạo vị trí ngẫu nhiên cho quả mới
    
    Args:
        location (tuple, optional): Vị trí trung tâm để tạo quả xung quanh
                                   Nếu None, sẽ tạo ngẫu nhiên trong toàn màn hình
        
    Returns:
        Vector2D: Vị trí của quả mới
    """
    # Thêm padding để tránh tạo quả quá gần viền màn hình
    padding = 50
    
    if location:
        # Nếu có vị trí trung tâm, tạo quả trong phạm vi quanh vị trí đó
        center_x, center_y = location
        radius = 100  # Bán kính tạo quả
        
        # Tạo vị trí ngẫu nhiên trong hình tròn với bán kính radius
        r = radius * math.sqrt(random.random())  # Để đảm bảo phân bố đều
        theta = random.random() * 2 * math.pi
        
        x = center_x + r * math.cos(theta)
        y = center_y + r * math.sin(theta)
        
        # Giới hạn trong màn hình
        x = max(padding, min(x, WINDOW_WIDTH - padding))
        y = max(padding, min(y, WINDOW_HEIGHT - padding))
    else:
        # Tạo ngẫu nhiên trong toàn màn hình
        x = random.uniform(padding, WINDOW_WIDTH - padding)
        y = random.uniform(padding, WINDOW_HEIGHT - padding)
    
    return Vector2D(x, y)

def calculate_fruit_spawn_likelihood(time, weather=0.5, season=0):
    """
    Tính xác suất mọc quả dựa trên thời gian, thời tiết và mùa
    
    Args:
        time (float): Thời gian hiện tại
        weather (float): Chỉ số thời tiết (0 đến 1)
        season (int): Mùa hiện tại (0: Xuân, 1: Hạ, 2: Thu, 3: Đông)
        
    Returns:
        float: Xác suất mọc quả (0 đến 1)
    """
    # Mùa ảnh hưởng đến xác suất mọc quả
    season_factors = [0.8, 1.0, 0.6, 0.2]  # Xuân, Hạ, Thu, Đông
    
    # Thời tiết càng tốt, xác suất mọc quả càng cao
    likelihood = weather * season_factors[season]
    
    # Có thể thêm các yếu tố khác như chu kỳ ngày/đêm
    # day_factor = math.sin(time / 86400 * 2 * math.pi) * 0.2 + 0.8  # Chu kỳ ngày/đêm
    # likelihood *= day_factor
    
    return max(0.0, min(likelihood, 1.0))  # Giới hạn trong khoảng [0, 1]