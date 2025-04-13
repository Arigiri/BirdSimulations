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
    
    def update(self, dt=1.0, nearby_birds=None, food_positions=None, food_ripeness=None):
        """
        Cập nhật vị trí và trạng thái của chim.
        
        Args:
            dt (float): Thời gian trôi qua từ lần cập nhật trước
            nearby_birds (list): Danh sách các chim lân cận
            food_positions (list): Danh sách vị trí các thức ăn
            food_ripeness (list): Danh sách độ chín của thức ăn
        """
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
        
        # Kiểm tra và tiêu thụ thức ăn nếu có
        if food_positions and food_ripeness:
            food_index = self.consume_food(food_positions, food_ripeness)
            if food_index >= 0:
                # Chim đã ăn được thức ăn
                self.eat(0.5)  # Tăng năng lượng/giảm đói
        
        # Giảm thời gian sống còn lại và đói
        self.lifespan -= 1
        self.hunger -= HUNGER_RATE * dt
        self.hunger = max(0.0, self.hunger)  # Đảm bảo hunger không âm
        
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
        """Tính các đỉnh của hình tam giác đại diện cho chim."""
        # Tính các đỉnh dựa trên vị trí, hướng và kích thước
        angle = self.velocity.heading()
        
        # Các đỉnh của hình tam giác
        vertices = []
        
        # Đỉnh trước (mũi chim)
        front_x = self.position.x + self.size * np.cos(angle)
        front_y = self.position.y + self.size * np.sin(angle)
        vertices.append((front_x, front_y))  # Trả về tuple (x, y) thay vì Vector2D
        
        # Đỉnh phải
        right_angle = angle + 2.5  # Khoảng 140 độ so với hướng bay
        right_x = self.position.x + self.size * 0.7 * np.cos(right_angle)
        right_y = self.position.y + self.size * 0.7 * np.sin(right_angle)
        vertices.append((right_x, right_y))  # Trả về tuple (x, y)
        
        # Đỉnh trái
        left_angle = angle - 2.5  # Khoảng -140 độ so với hướng bay
        left_x = self.position.x + self.size * 0.7 * np.cos(left_angle)
        left_y = self.position.y + self.size * 0.7 * np.sin(left_angle)
        vertices.append((left_x, left_y))  # Trả về tuple (x, y)
        
        return vertices
    
    def get_color(self):
        """Trả về màu sắc dựa trên mức độ đói và năng lượng."""
        r, g, b, a = self.color
        
        # Sử dụng giá trị nhỏ hơn giữa hunger và energy cho alpha
        health_factor = min(self.hunger, self.energy)
        alpha = int(a * health_factor)
        
        return (r, g, b, alpha)
    
    def get_info(self):
        """Trả về thông tin chi tiết về chim để hiển thị"""
        info = {
            "position": f"Vị trí: ({int(self.position.x)}, {int(self.position.y)})",
            "velocity": f"Vận tốc: {int(self.velocity.magnitude())}",
            "lifetime": f"Tuổi: {int(self.lifetime)} giây",
            "health": f"Sức khỏe: {int(self.health * 100)}%",
            "energy": f"Năng lượng: {int(self.energy * 100)}%"
        }
        
        # Thêm thông tin về đói nếu có
        if hasattr(self, 'hunger'):
            info["hunger"] = f"Đói: {int(self.hunger * 100)}%"
        
        return info
    
    def contains_point(self, x, y):
        """Kiểm tra xem một điểm có nằm trong chim không."""
        vertices = self.get_vertices()
        
        # Sử dụng thuật toán ray casting để kiểm tra điểm nằm trong đa giác
        inside = False
        j = len(vertices) - 1
        
        for i in range(len(vertices)):
            # Truy cập x, y qua tuple index (vertices trả về danh sách tuple (x,y))
            xi = vertices[i][0]
            yi = vertices[i][1]
            xj = vertices[j][0]
            yj = vertices[j][1]
            
            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
            if intersect:
                inside = not inside
            
            j = i
        
        return inside
    
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
        # Sử dụng kích thước màn hình hiệu quả (trừ đi info panel)
        effective_width = WINDOW_WIDTH - INFO_PANEL_WIDTH
        
        # Bọc quanh theo chiều ngang
        if self.position.x < 0:
            self.position.x = effective_width
        elif self.position.x > effective_width:
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
            vertices[0][0], vertices[0][1],  # Truy cập x, y qua tuple index
            vertices[1][0], vertices[1][1],  # Truy cập x, y qua tuple index
            vertices[2][0], vertices[2][1]   # Truy cập x, y qua tuple index
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