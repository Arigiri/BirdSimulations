import numpy as np
import pyglet
from utils.vector import Vector2D
from utils.config import *

class Bird:
    """
    Lớp Bird biểu diễn một con chim trong mô phỏng.
    Sử dụng thuật toán boids để điều khiển chuyển động.
    """
    
    def __init__(self, x=None, y=None, velocity=None, max_lifespan=1000):
        """Khởi tạo chim với vị trí và vận tốc."""
        # Khởi tạo vị trí ngẫu nhiên nếu không được cung cấp
        if x is None or y is None:
            x = np.random.uniform(0, WINDOW_WIDTH)
            y = np.random.uniform(0, WINDOW_HEIGHT)
        self.position = Vector2D(x, y)
        
        # Khởi tạo vận tốc ngẫu nhiên nếu không được cung cấp
        if velocity is None:
            vx = np.random.uniform(-1, 1)
            vy = np.random.uniform(-1, 1)
            velocity = Vector2D(vx, vy).normalize() * np.random.uniform(1, MAX_SPEED)
        self.velocity = velocity
        self.max_speed = MAX_SPEED
        
        # Lưu trữ tốc độ ban đầu - đây sẽ là hằng số
        self.speed = self.velocity.magnitude()
        
        # Thuộc tính steering (thay cho acceleration)
        self.steering = Vector2D(0, 0)
        self.max_force = MAX_FORCE  # Giới hạn lực lái tối đa
        
        # Thuộc tính sức khỏe và năng lượng
        self.health = 1.0  # Đầy đủ sức khỏe
        self.energy = 1.0  # Đầy đủ năng lượng
        self.lifetime = 0  # Thời gian đã sống
        
        # Thuộc tính đói/thời gian
        self.max_lifespan = max_lifespan
        self.lifespan = max_lifespan  # Thời gian sống còn lại
        self.hunger = 1.0  # 1.0 = no đủ, 0.0 = đói hoàn toàn
        self.is_dead = False
        
        # Kích thước và màu sắc
        self.size = BIRD_SIZE
        self.color = BIRD_COLOR
        
    def apply_force(self, force):
        """Áp dụng lực lái lên chim (chỉ thay đổi hướng, không thay đổi tốc độ)."""
        self.steering = self.steering + force
    
    def update(self, dt=1.0):
        """Cập nhật vị trí và trạng thái của chim."""
        # Giới hạn lực lái
        self.steering = self.steering.limit(self.max_force)
        
        # Chỉ điều chỉnh hướng bay, không thay đổi tốc độ
        if self.steering.magnitude() > 0:
            # Thêm lực lái vào vận tốc hiện tại
            new_velocity = self.velocity + self.steering
            
            # Chuẩn hóa và đặt lại tốc độ ban đầu
            self.velocity = new_velocity.normalize() * self.speed
        
        # Đặt lại steering về 0
        self.steering = Vector2D(0, 0)
        
        # Cập nhật vị trí
        self.position = self.position + (self.velocity * dt)
        
        # Giảm thời gian sống còn lại và đói
        self.lifespan -= 1
        self.hunger -= HUNGER_RATE * dt
        
        # Kiểm tra nếu chim đã hết thời gian sống hoặc quá đói
        if self.lifespan <= 0 or self.hunger <= 0:
            self.is_dead = True

        # Giảm năng lượng theo thời gian
        self.energy -= HUNGER_RATE * dt
        self.energy = max(0.0, min(1.0, self.energy))
        # Tăng thời gian sống
        self.lifetime += dt
    
    def consume_food(self, food_positions, ripeness, food_radius=5.0):
        """
        Tiêu thụ thức ăn nếu ở gần.
        Trả về chỉ số của thức ăn đã tiêu thụ hoặc -1.
        """
        if not food_positions:
            return -1
            
        for i, pos in enumerate(food_positions):
            if ripeness[i] >= 1.0:  # Chỉ có thể ăn quả đã chín
                food_pos = Vector2D(pos[0], pos[1])
                distance = self.position.distance_to(food_pos)
                
                if distance < food_radius:
                    # Phục hồi năng lượng khi ăn
                    self.hunger = min(1.0, self.hunger + 0.5)
                    self.lifespan = min(self.max_lifespan, self.lifespan + 100)
                    return i
        
        return -1
    
    def get_vertices(self):
        """Tính toán các đỉnh của hình tam giác cho việc vẽ."""
        # Hướng mũi chim
        angle = np.arctan2(self.velocity.y, self.velocity.x)
        
        # Ba đỉnh tam giác
        v1 = Vector2D(
            self.position.x + self.size * np.cos(angle),
            self.position.y + self.size * np.sin(angle)
        )
        
        v2 = Vector2D(
            self.position.x + self.size * 0.5 * np.cos(angle + 2.5),
            self.position.y + self.size * 0.5 * np.sin(angle + 2.5)
        )
        
        v3 = Vector2D(
            self.position.x + self.size * 0.5 * np.cos(angle - 2.5),
            self.position.y + self.size * 0.5 * np.sin(angle - 2.5)
        )
        
        return [v1, v2, v3]
    
    def get_color(self):
        """Trả về màu sắc dựa trên mức độ đói và năng lượng."""
        r, g, b, a = self.color
        
        # Sử dụng giá trị nhỏ hơn giữa hunger và energy cho alpha
        health_factor = min(self.hunger, self.energy)
        alpha = int(a * health_factor)
        
        return (r, g, b, alpha)
    
    def get_info(self):
        """Trả về thông tin của chim cho frontend."""
        return {
            'position': self.position.as_tuple(),
            'velocity': self.velocity.as_tuple(),
            'life_duration': self.max_lifespan - self.lifespan,
            'time_left': self.lifespan,
            'hunger': self.hunger,
            'is_dead': self.is_dead
        }

    def seek(self, target):
        """Tìm kiếm đến một vị trí mục tiêu"""
        # Tính vector mong muốn
        desired = target - self.position
        # Chuẩn hóa và nhân với tốc độ tối đa
        desired = desired.normalize() * self.max_speed
        # Tính lực chỉ đạo (steering)
        steering = desired - self.velocity
        # Giới hạn lực
        steering = steering.limit(self.max_force)
        return steering
        
    def edges(self):
        """Xử lý biên màn hình"""
        # Bọc quanh theo chiều ngang
        if self.position.x < 0:
            self.position.x = WINDOW_WIDTH
        elif self.position.x > WINDOW_WIDTH:
            self.position.x = 0
            
        # Bọc quanh theo chiều dọc
        if self.position.y < 0:
            self.position.y = WINDOW_HEIGHT
        elif self.position.y > WINDOW_HEIGHT:
            self.position.y = 0

    def is_alive(self):
        """Kiểm tra chim còn sống không"""
        # Chim chết nếu energy quá thấp hoặc đã được đánh dấu là chết
        return not self.is_dead and self.energy > 0.1
    
    def eat(self, amount):
        """Chim ăn và tăng năng lượng/giảm đói"""
        self.energy += amount
        self.hunger += amount
        self.energy = min(1.0, self.energy)
        self.hunger = min(1.0, self.hunger)
    
    def draw(self):
        """Vẽ chim lên màn hình."""
        # Lấy các đỉnh tam giác
        vertices = self.get_vertices()
        
        # Lấy màu sắc
        r, g, b, a = self.get_color()
        
        # Tạo danh sách các điểm
        points = [
            vertices[0].x, vertices[0].y,
            vertices[1].x, vertices[1].y,
            vertices[2].x, vertices[2].y
        ]
        
        # Vẽ tam giác sử dụng pyglet.shapes
        triangle = pyglet.shapes.Triangle(
            points[0], points[1],
            points[2], points[3],
            points[4], points[5],
            color=(r, g, b)
        )
        triangle.opacity = a
        triangle.draw()