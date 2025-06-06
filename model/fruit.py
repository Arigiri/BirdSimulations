"""
Module quản lý trái cây trong mô phỏng đàn chim
"""

import time
import numpy as np
from utils.vector import Vector2D
from utils.config import FRUIT_RADIUS, FRUIT_COLOR_UNRIPE, FRUIT_COLOR_RIPE, RIPENING_RATE
from model.fruit_functions import calculate_ripeness, generate_fruit_position, FruitSpawnStepper, calculate_fruit_spawn_likelihood

class Fruit:
    """Lớp đại diện cho một quả trong mô phỏng"""
    
    def __init__(self, position=None, creation_time=None):
        """
        Khởi tạo một quả mới
        
        Args:
            position (Vector2D, optional): Vị trí của quả. Nếu None, sẽ được tạo ngẫu nhiên
            creation_time (float, optional): Thời điểm tạo quả. Nếu None, sẽ lấy thời gian hiện tại
        """
        self.position = position if position else generate_fruit_position()
        self.creation_time = creation_time if creation_time else time.time()
        self.ripeness = 0.0  # Quả bắt đầu chưa chín
        self.radius = FRUIT_RADIUS
        self.is_eaten = False
    
    def update(self, current_time, dt):
        """
        Cập nhật trạng thái của quả
        
        Args:
            current_time (float): Thời gian hiện tại
            dt (float): Thời gian trôi qua từ lần cập nhật trước
            
        Returns:
            bool: True nếu quả vẫn còn hiệu lực, False nếu quả đã quá chín (ripeness >= 2)
        """
        time_existed = current_time - self.creation_time
        self.ripeness = calculate_ripeness(time_existed)
        
        # Quả sẽ biến mất khi ripeness >= 2.0
        return self.ripeness < 2.0 and not self.is_eaten
    
    def get_color(self):
        """
        Tính toán màu sắc của quả dựa trên độ chín
        
        Returns:
            tuple: Giá trị màu RGBA
        """
        # print("Color: ", self.ripeness)
        if self.ripeness < 1.0:
            # Chuyển từ xanh lá sang đỏ khi độ chín tăng từ 0 -> 1
            red = int(255 * self.ripeness)
            green = int(255 * (1.0 - self.ripeness))
            return (red, green, 0, 255)
        else:
            # Quả đã chín, đỏ hoàn toàn
            # Sau đó giảm dần độ đậm (alpha) khi ripeness > 1 (quá chín)
            alpha = int(255 * (2.0 - self.ripeness)) if self.ripeness < 2.0 else 0
            return (255, 0, 0, alpha)
    
    def is_ripe(self):
        """Kiểm tra xem quả đã chín hay chưa"""
        return self.ripeness >= 1.0
    
    def get_life_duration(self, current_time):
        """Tính toán thời gian tồn tại của quả"""
        return current_time - self.creation_time
    
    def mark_as_eaten(self):
        """Đánh dấu quả đã bị ăn"""
        self.is_eaten = True

class FruitManager:
    """Lớp quản lý tập hợp các quả trong mô phỏng"""
    
    def __init__(self):
        """Khởi tạo trình quản lý quả"""
        self.fruits = []
        self.positions = []  # Danh sách vị trí để truyền vào hàm steering
        self.ripeness = []   # Danh sách độ chín tương ứng
        self.spawn_stepper = FruitSpawnStepper()
    
    def add_fruit(self, position=None):
        """Thêm một quả mới vào mô phỏng"""
        new_fruit = Fruit(position)
        self.fruits.append(new_fruit)
        self.update_arrays()
        return new_fruit
    
    def update(self, current_time, dt, temperature_field=None, weather=0.5, season=0, sim_time=0):
        """
        Cập nhật tất cả các quả và tự động spawn quả mới nếu đủ điều kiện
        Args:
            current_time (float): Thời gian hiện tại
            dt (float): Thời gian trôi qua từ lần cập nhật trước
            temperature_field (np.ndarray or callable): Trường nhiệt độ hiện tại
            weather (float): Chỉ số thời tiết (0-1)
            season (int): Mùa hiện tại (0: Xuân, 1: Hạ, 2: Thu, 3: Đông)
            sim_time (float): Thời gian mô phỏng (giây)
        """
        import random
        from model.fruit_functions import calculate_fruit_spawn_likelihood_at_point
        # Cập nhật từng quả và loại bỏ những quả đã quá chín hoặc đã bị ăn
        self.fruits = [fruit for fruit in self.fruits if fruit.update(current_time, dt)]
        self.update_arrays()
        # Tự động spawn quả mới
        if self.spawn_stepper.step() and temperature_field is not None:
            # Lấy min/max nhiệt độ
            if callable(temperature_field):
                # Không lấy được min/max, dùng mặc định
                temp_min, temp_max = 0.0, 1.0
            else:
                temp_min = float(temperature_field.min())
                temp_max = float(temperature_field.max())
            # Thử random 1 vị trí (hoặc nhiều nếu muốn)
            pos = generate_fruit_position(temperature_field=temperature_field)
            # Lấy nhiệt độ tại vị trí
            x, y = pos.x, pos.y
            if callable(temperature_field):
                temp = temperature_field(x, y)
            else:
                h, w = temperature_field.shape
                ix = int(x / (WINDOW_WIDTH - INFO_PANEL_WIDTH) * (w-1))
                iy = int(y / WINDOW_HEIGHT * (h-1))
                ix = max(0, min(ix, w-1))
                iy = max(0, min(iy, h-1))
                temp = temperature_field[iy, ix]
            likelihood = calculate_fruit_spawn_likelihood_at_point(temp, temp_min, temp_max, weather, season)
            if random.random() < likelihood:
                self.add_fruit(pos)
        elif self.spawn_stepper.step():
            # Nếu không có trường nhiệt độ, dùng xác suất cũ
            likelihood = calculate_fruit_spawn_likelihood(sim_time, weather, season)
            if random.random() < likelihood:
                pos = generate_fruit_position()
                self.add_fruit(pos)
    
    def update_arrays(self):
        """Cập nhật mảng vị trí và độ chín để sử dụng trong steering"""
        self.positions = [(fruit.position.x, fruit.position.y) for fruit in self.fruits]
        self.ripeness = [fruit.ripeness for fruit in self.fruits]
    
    def get_ripe_fruits(self):
        """Trả về danh sách các quả đã chín"""
        return [fruit for fruit in self.fruits if fruit.is_ripe()]
    
    def add_random_fruits(self, count):
        """Thêm nhiều quả ngẫu nhiên vào mô phỏng"""
        for _ in range(count):
            self.add_fruit()
    
    def consume_fruit(self, position, eat_radius):
        """
        Kiểm tra và đánh dấu quả bị ăn nếu có chim gần quả chín
        
        Args:
            position (Vector2D): Vị trí của chim
            eat_radius (float): Bán kính mà chim có thể ăn quả
            
        Returns:
            bool: True nếu chim đã ăn được quả, False nếu không
        """
        for fruit in self.fruits:
            if (not fruit.is_eaten and fruit.is_ripe() and
                fruit.position.distance_to(position) < eat_radius):
                fruit.mark_as_eaten()
                return True
        return False