import numpy as np
from utils.vector import Vector2D
from model.bird import Bird
from utils.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, SEPARATION_RADIUS, 
    ALIGNMENT_RADIUS, COHESION_RADIUS, 
    SEPARATION_WEIGHT, ALIGNMENT_WEIGHT, COHESION_WEIGHT,
    INITIAL_BIRD_COUNT
)

class BoidSimulation:
    """Lớp điều khiển mô phỏng boids."""
    
    def __init__(self):
        """Khởi tạo mô phỏng."""
        self.birds = []
        self.fruits = []
        self.running = False
        self.time = 0
        self.create_initial_birds()
        
    def create_initial_birds(self):
        """Tạo đàn chim ban đầu"""
        for _ in range(INITIAL_BIRD_COUNT):
            self.birds.append(Bird())
    
    def add_birds(self, count=1, x=None, y=None):
        """Thêm chim vào mô phỏng"""
        for _ in range(count):
            self.birds.append(Bird(x, y))
    
    def toggle_simulation(self):
        """Bật/tắt mô phỏng"""
        self.running = not self.running
        return self.running
    
    def reset(self):
        """Đặt lại mô phỏng"""
        self.birds = []
        self.fruits = []
        self.time = 0
        self.create_initial_birds()
        
    def update(self, dt):
        """Cập nhật trạng thái mô phỏng"""
        if not self.running:
            return
            
        self.time += dt
        
        # Loại bỏ chim đã chết
        self.birds = [bird for bird in self.birds if bird.is_alive()]
        
        # Áp dụng các quy tắc boids và cập nhật chim
        for bird in self.birds:
            # Áp dụng các lực từ quy tắc boids
            separation = self.calculate_separation(bird)
            alignment = self.calculate_alignment(bird)
            cohesion = self.calculate_cohesion(bird)
            
            # Áp dụng các lực với trọng số
            bird.apply_force(separation * SEPARATION_WEIGHT)
            bird.apply_force(alignment * ALIGNMENT_WEIGHT)
            bird.apply_force(cohesion * COHESION_WEIGHT)
            
            # Cập nhật vị trí và vận tốc
            bird.update(dt)
            
            # Xử lý biên
            bird.edges()
    
    def calculate_separation(self, bird):
        """Tính lực tách biệt - tránh va chạm với chim khác"""
        steering = Vector2D(0, 0)
        total = 0
        
        for other in self.birds:
            if other is bird:
                continue
                
            # Tính khoảng cách giữa bird và other
            d = (bird.position - other.position).magnitude()
            
            # Nếu trong phạm vi tách biệt
            if d < SEPARATION_RADIUS and d > 0:
                # Tính vector tránh xa
                diff = bird.position - other.position
                diff = diff.normalize()
                diff = diff / d  # Trọng số ngược với khoảng cách
                steering = steering + diff
                total += 1
        
        if total > 0:
            steering = steering / total
            steering = steering.normalize() * bird.max_speed
            steering = steering - bird.velocity
            steering = steering.limit(bird.max_force)
            
        return steering
    
    def calculate_alignment(self, bird):
        """Tính lực căn chỉnh - bay cùng hướng với các chim lân cận"""
        steering = Vector2D(0, 0)
        total = 0
        
        for other in self.birds:
            if other is bird:
                continue
                
            # Tính khoảng cách
            d = (bird.position - other.position).magnitude()
            
            # Nếu trong phạm vi căn chỉnh
            if d < ALIGNMENT_RADIUS:
                # Cộng vận tốc
                steering = steering + other.velocity
                total += 1
        
        if total > 0:
            steering = steering / total
            steering = steering.normalize() * bird.max_speed
            steering = steering - bird.velocity
            steering = steering.limit(bird.max_force)
            
        return steering
    
    def calculate_cohesion(self, bird):
        """Tính lực gắn kết - bay về phía trung tâm đàn"""
        steering = Vector2D(0, 0)
        center = Vector2D(0, 0)
        total = 0
        
        for other in self.birds:
            if other is bird:
                continue
                
            # Tính khoảng cách
            d = (bird.position - other.position).magnitude()
            
            # Nếu trong phạm vi gắn kết
            if d < COHESION_RADIUS:
                center = center + other.position
                total += 1
        
        if total > 0:
            center = center / total
            # Sử dụng hàm seek để tìm đường đến trung tâm
            steering = bird.seek(center)
            
        return steering