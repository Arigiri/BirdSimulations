"""
Module chứa các hàm tính toán liên quan đến trái cây
"""

from utils.config import FRUIT_SPAWN_STEP_INTERVAL

class FruitSpawnStepper:
    """
    Bộ đếm step để quyết định khi nào được phép mọc quả mới.
    Dùng cho mô phỏng theo step discrete.
    """
    def __init__(self, interval=FRUIT_SPAWN_STEP_INTERVAL):
        self.interval = interval
        self.counter = 0
    def step(self):
        """Gọi hàm này mỗi step. Trả về True nếu tới lượt spawn, False nếu chưa."""
        self.counter += 1
        if self.counter >= self.interval:
            self.counter = 0
            return True
        return False


import random
import math
from utils.vector import Vector2D
from utils.config import WINDOW_WIDTH, WINDOW_HEIGHT, RIPENING_RATE, INFO_PANEL_WIDTH

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

def generate_fruit_position(location=None, temperature_field=None, num_samples=10):
    """
    Tạo vị trí ngẫu nhiên cho quả mới, ưu tiên nơi có nhiệt độ cao nếu có trường nhiệt độ.
    
    Args:
        location (tuple, optional): Vị trí trung tâm để tạo quả xung quanh
        temperature_field (np.ndarray or callable, optional): Trường nhiệt độ 2D hoặc hàm trả về nhiệt độ tại (x, y)
        num_samples (int): Số lượng điểm thử random (nếu dùng nhiệt độ)
    Returns:
        Vector2D: Vị trí của quả mới
    """
    padding = INFO_PANEL_WIDTH
    best_pos = None
    best_temp = -float('inf')
    
    def get_temp(x, y):
        if temperature_field is None:
            return 0
        if callable(temperature_field):
            return temperature_field(x, y)
        else:
            # Giả sử temperature_field là numpy array shape (H, W)
            h, w = temperature_field.shape
            ix = int(x / (WINDOW_WIDTH - padding) * (w-1))
            iy = int(y / WINDOW_HEIGHT * (h-1))
            ix = max(0, min(ix, w-1))
            iy = max(0, min(iy, h-1))
            return temperature_field[iy, ix]
    
    samples = num_samples if temperature_field is not None else 1
    for _ in range(samples):
        if location:
            center_x, center_y = location
            radius = 100
            r = radius * math.sqrt(random.random())
            theta = random.random() * 2 * math.pi
            x = center_x + r * math.cos(theta)
            y = center_y + r * math.sin(theta)
            x = max(0, min(x, WINDOW_WIDTH - padding))
            y = min(y, WINDOW_HEIGHT)
        else:
            x = random.uniform(0, WINDOW_WIDTH - padding)
            y = random.uniform(0, WINDOW_HEIGHT)
        temp = get_temp(x, y)
        if temp > best_temp:
            best_temp = temp
            best_pos = (x, y)
    return Vector2D(*best_pos)

def calculate_fruit_spawn_likelihood_at_point(temperature, temp_min, temp_max, weather=0.5, season=0):
    """
    Xác suất mọc quả tại một điểm, phụ thuộc nhiệt độ tại điểm đó, thời tiết, mùa.
    Args:
        temperature (float): Nhiệt độ tại điểm spawn
        temp_min (float): Nhiệt độ thấp nhất trong trường nhiệt độ
        temp_max (float): Nhiệt độ cao nhất trong trường nhiệt độ
        weather (float): Chỉ số thời tiết (0-1)
        season (int): Mùa hiện tại (0: Xuân, 1: Hạ, 2: Thu, 3: Đông)
    Returns:
        float: Xác suất mọc quả (0 đến 1)
    """
    if temp_max - temp_min < 1e-8:
        temp_norm = 0.0
    else:
        temp_norm = (temperature - temp_min) / (temp_max - temp_min)
    season_factors = [0.8, 1.0, 0.6, 0.2]
    likelihood = temp_norm * weather * season_factors[season]
    return max(0.0, min(likelihood, 1.0))

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