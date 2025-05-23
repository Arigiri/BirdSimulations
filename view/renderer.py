import pyglet
import random
import numpy as np
from utils.vector import Vector2D
from utils.config import *
from model.bird import Bird
from model.steering import calculate_steering

class SimpleRenderer:
    """Renderer đơn giản để vẽ các con chim chuyển động"""
    
    def __init__(self, window_width, window_height):
        """Khởi tạo renderer với kích thước cửa sổ"""
        self.window_width = window_width - INFO_PANEL_WIDTH  # Trừ đi thanh thông tin
        self.window_height = window_height
        self.birds = []
        self.food_positions = []  # Vị trí các thức ăn
        self.food_ripeness = []   # Độ chín của các thức ăn
        self.create_birds(INITIAL_BIRD_COUNT)  # Sử dụng số lượng chim cấu hình
    
    def create_birds(self, num_birds):
        """Tạo các con chim với vị trí, màu sắc và vận tốc ngẫu nhiên"""
        for _ in range(num_birds):
            # Tạo vị trí ngẫu nhiên
            x = random.randint(50, self.window_width - 50)
            y = random.randint(50, self.window_height - 50)
            
            # Tạo vận tốc ngẫu nhiên
            vx = random.uniform(-1, 1)
            vy = random.uniform(-1, 1)
            velocity = Vector2D(vx, vy).normalize() * random.uniform(MIN_SPEED, MAX_SPEED)
            
            # Tạo đối tượng Bird mới
            bird = Bird(x, y, velocity)
            
            # Gán màu ngẫu nhiên từ BIRD_COLORS
            bird.color = random.choice(BIRD_COLORS)
            
            self.birds.append(bird)
    
    def update(self, dt):
        """Cập nhật trạng thái của tất cả các con chim"""
        # Áp dụng các quy tắc boids nếu có đủ chim
        if len(self.birds) >= 1:
            self.apply_boid_rules()
        
        # Tạo một danh sách chim còn sống sau khi update
        living_birds = []
        
        for bird in self.birds:
            # Truyền thông tin thức ăn nếu có
            food_positions = getattr(self, 'food_positions', None)
            food_ripeness = getattr(self, 'food_ripeness', None)
            
            # Kiểm tra xem bird.update có nhận tham số food không
            import inspect
            bird_update_params = inspect.signature(bird.update).parameters
            
            if len(bird_update_params) >= 4 and food_positions is not None:
                bird.update(dt, self.birds, food_positions, food_ripeness)
            else:
                bird.update(dt, self.birds)
            
            # Kiểm tra biên
            bird.edges()
            
            # Chỉ giữ lại chim còn sống
            if not bird.is_dead and bird.is_alive():
                living_birds.append(bird)
        
        self.birds = living_birds
    
    def draw(self):
        """Vẽ tất cả các con chim"""
        for bird in self.birds:
            bird.draw()
    
    def add_birds(self, count=1):
        """Thêm một số lượng chim vào mô phỏng"""
        self.create_birds(count)
    
    def get_bird_count(self):
        """Trả về số lượng chim hiện tại"""
        return len(self.birds)
    
    def apply_boid_rules(self):
        """Áp dụng các quy tắc boids: separation, alignment, cohesion"""
        for bird in self.birds:
            # Truyền thông tin thức ăn nếu có
            food_positions = getattr(self, 'food_positions', None)
            food_ripeness = getattr(self, 'food_ripeness', None)
            
            # Đảm bảo truyền đúng các tham số
            calculate_steering(
                bird, 
                self.birds, 
                SEPARATION_RADIUS, 
                ALIGNMENT_RADIUS, 
                COHESION_RADIUS, 
                food_positions,
                food_ripeness
            )