import numpy as np
import time
from utils.vector import Vector2D
from model.bird import Bird
from model.fruit import FruitManager
from model.weather.main.weather_integration import WeatherIntegration
from utils.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, SEPARATION_RADIUS, 
    ALIGNMENT_RADIUS, COHESION_RADIUS, 
    SEPARATION_WEIGHT, ALIGNMENT_WEIGHT, COHESION_WEIGHT,
    FOOD_WEIGHT, EDGE_WEIGHT, FRUIT_RADIUS,
    INITIAL_BIRD_COUNT, INFO_PANEL_WIDTH
)

class BoidSimulation:
    """Lớp điều khiển mô phỏng boids."""
    
    def __init__(self):
        """Khởi tạo mô phỏng."""
        self.birds = []
        self.fruit_manager = FruitManager()
        self.running = False
        self.time = 0
        self.simulation_time = time.time()
        
        # Khởi tạo module thời tiết
        effective_width = WINDOW_WIDTH - INFO_PANEL_WIDTH
        self.weather = WeatherIntegration(effective_width, WINDOW_HEIGHT)
        
        # Kết nối module thời tiết với quả
        self.fruit_manager.set_weather_integration(self.weather)
        
        # Tạo chim ban đầu
        self.create_initial_birds()
        
        # Trạng thái hiển thị
        self.show_weather = True
        
    def create_initial_birds(self):
        """Tạo đàn chim ban đầu"""
        for _ in range(INITIAL_BIRD_COUNT):
            self.birds.append(Bird())
    
    def add_birds(self, count=1, x=None, y=None):
        """Thêm chim vào mô phỏng"""
        for _ in range(count):
            self.birds.append(Bird(x, y))
    
    def add_fruits(self, count=1):
        """Thêm quả vào mô phỏng"""
        self.fruit_manager.add_random_fruits(count)
    
    def toggle_simulation(self):
        """Bật/tắt mô phỏng"""
        self.running = not self.running
        return self.running
    
    def toggle_weather_display(self):
        """Bật/tắt hiển thị thời tiết"""
        self.show_weather = not self.show_weather
        return self.show_weather
    
    def reset(self):
        """Đặt lại mô phỏng"""
        self.birds = []
        self.fruit_manager = FruitManager()
        # Kết nối lại module thời tiết với quả
        self.fruit_manager.set_weather_integration(self.weather)
        self.time = 0
        self.simulation_time = time.time()
        self.create_initial_birds()
        
        # Khởi tạo lại module thời tiết
        if self.weather.initialized:
            self.weather.initialize_weather()
        
    def update(self, dt):
        """Cập nhật trạng thái mô phỏng"""
        if not self.running:
            return
            
        self.time += dt
        current_time = time.time()
        
        # Cập nhật module thời tiết
        self.weather.update(dt)
        
        # Cập nhật quả
        self.fruit_manager.update(current_time, dt)
        
        # Loại bỏ chim đã chết
        self.birds = [bird for bird in self.birds if bird.is_alive()]
        
        # Áp dụng các quy tắc boids và cập nhật chim
        for bird in self.birds:
            # Áp dụng các lực từ quy tắc boids
            separation = self.calculate_separation(bird)
            alignment = self.calculate_alignment(bird)
            cohesion = self.calculate_cohesion(bird)
            food_seeking = self.calculate_food_seeking(bird)
            edges = self.calculate_edge_avoidance(bird)
            
            # Áp dụng các lực với trọng số
            bird.apply_force(separation * SEPARATION_WEIGHT)
            bird.apply_force(alignment * ALIGNMENT_WEIGHT)
            bird.apply_force(cohesion * COHESION_WEIGHT)
            bird.apply_force(food_seeking * FOOD_WEIGHT)
            bird.apply_force(edges * EDGE_WEIGHT)
            
            # Áp dụng ảnh hưởng của thời tiết (gió)
            if self.weather.initialized:
                # Lấy thông tin thời tiết tại vị trí của chim
                weather_info = self.weather.get_weather_for_birds(
                    bird.position.x, bird.position.y
                )
                # Áp dụng lực gió
                if "wind" in weather_info and weather_info["wind"]:
                    bird.apply_wind_force(weather_info["wind"])
            
            # Cập nhật vị trí và vận tốc
            bird.update(dt, self.birds, 
                      self.fruit_manager.positions, 
                      self.fruit_manager.ripeness)
            
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
    
    def calculate_food_seeking(self, bird):
        """Tính lực tìm kiếm thức ăn - bay về phía quả chín"""
        steering = Vector2D(0, 0)
        
        # Kiểm tra nếu không có quả nào
        if not self.fruit_manager.positions:
            return steering
            
        # Tìm quả chín gần nhất
        nearest_dist = float('inf')
        nearest_pos = None
        
        for i, pos in enumerate(self.fruit_manager.positions):
            ripeness = self.fruit_manager.ripeness[i]
            
            # Chỉ quan tâm đến quả đã chín
            if ripeness >= 0.5:  # Bắt đầu hướng đến quả khi nó chín 50% trở lên
                food_pos = Vector2D(pos[0], pos[1])
                dist = (bird.position - food_pos).magnitude()
                
                # Cập nhật quả gần nhất
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_pos = food_pos
        
        # Nếu tìm thấy quả chín
        if nearest_pos:
            # Tính lực steering về phía quả
            desired = nearest_pos - bird.position
            
            # Điều chỉnh lực dựa trên khoảng cách
            # Càng gần quả, lực càng mạnh
            dist = desired.magnitude()
            desired = desired.normalize()
            
            # Điều chỉnh lực theo khoảng cách
            if dist < 100:  # Trong khoảng 100 pixel
                # Tỷ lệ nghịch với khoảng cách (càng gần càng mạnh)
                scale = ((100 - dist) / 100) * bird.max_speed
                desired = desired * scale
            else:
                desired = desired * (bird.max_speed / 2)  # Lực yếu hơn khi xa
                
            # Tính lực chỉ đạo
            steering = desired - bird.velocity
            steering = steering.limit(bird.max_force)
        
        return steering
    
    def calculate_edge_avoidance(self, bird):
        """Tính lực tránh biên - tránh bay ra khỏi màn hình"""
        steering = Vector2D(0, 0)
        margin = 50  # Khoảng cách từ biên để bắt đầu tránh
        
        # Chiều rộng hiệu dụng (trừ info panel)
        effective_width = WINDOW_WIDTH - INFO_PANEL_WIDTH
        
        # Kiểm tra các biên
        # Biên trái
        if bird.position.x < margin:
            steering.x += 1.0 * (1.0 - bird.position.x / margin)
            
        # Biên phải
        elif bird.position.x > effective_width - margin:
            steering.x -= 1.0 * (1.0 - (effective_width - bird.position.x) / margin)
            
        # Biên dưới
        if bird.position.y < margin:
            steering.y += 1.0 * (1.0 - bird.position.y / margin)
            
        # Biên trên
        elif bird.position.y > WINDOW_HEIGHT - margin:
            steering.y -= 1.0 * (1.0 - (WINDOW_HEIGHT - bird.position.y) / margin)
        
        # Nếu có lực tránh biên
        if steering.magnitude() > 0:
            steering = steering.normalize() * bird.max_speed
            steering = steering - bird.velocity
            steering = steering.limit(bird.max_force)
            
        return steering
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Xử lý sự kiện di chuyển chuột"""
        # Chuyển tiếp sự kiện đến module thời tiết
        return self.weather.on_mouse_motion(x, y, dx, dy)
        
    def on_mouse_press(self, x, y, button, modifiers):
        """Xử lý sự kiện nhấn chuột"""
        # Thêm chim khi nhấp chuột nếu không trong khu vực thời tiết
        if not self.weather.on_mouse_press(x, y, button, modifiers):
            self.add_birds(1, x, y)
            return True
        return False
        
    def on_mouse_release(self, x, y, button, modifiers):
        """Xử lý sự kiện thả chuột"""
        # Chuyển tiếp sự kiện đến module thời tiết
        return self.weather.on_mouse_release(x, y, button, modifiers)
    
    def on_key_press(self, symbol, modifiers):
        """Xử lý sự kiện nhấn phím"""
        from pyglet.window import key
        
        # Phím F: Tạo ngẫu nhiên 5 quả mới
        if symbol == key.F:
            self.fruit_manager.add_random_fruits(5)
            return True
            
        # Phím W: Bật/tắt hiển thị thời tiết
        elif symbol == key.W:
            self.toggle_weather_display()
            return True
            
        # Chuyển tiếp sự kiện đến module thời tiết
        return self.weather.on_key_press(symbol, modifiers)
    
    def draw(self):
        """Vẽ tất cả đối tượng trong mô phỏng"""
        # Vẽ module thời tiết nếu được bật
        if self.show_weather and self.weather.initialized:
            self.weather.draw()
        
        # Vẽ các đối tượng khác (chim, quả, ...)
        # Cài đặt chi tiết trong render.py