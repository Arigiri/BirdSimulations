from utils.vector import Vector2D
import numpy as np

def calculate_steering(bird, all_birds, separation_radius, alignment_radius, cohesion_radius, 
                       separation_weight, alignment_weight, cohesion_weight, food_positions=None, food_ripeness=None):
    """Tính toán và áp dụng các lực steering cho một con chim.
    
    Args:
        bird: Đối tượng Bird cần tính steering
        all_birds: Danh sách tất cả các Bird trong mô phỏng
        separation_radius: Bán kính tách biệt
        alignment_radius: Bán kính căn chỉnh
        cohesion_radius: Bán kính gắn kết
        separation_weight: Trọng số cho lực tách biệt
        alignment_weight: Trọng số cho lực căn chỉnh
        cohesion_weight: Trọng số cho lực gắn kết
        food_positions: Danh sách vị trí các thức ăn (tùy chọn)
        food_ripeness: Danh sách mức độ chín của thức ăn (tùy chọn)
    """
    # Tính các lực cơ bản của boids
    separation_force = separation(bird, all_birds, separation_radius)
    alignment_force = alignment(bird, all_birds, alignment_radius)
    cohesion_force = cohesion(bird, all_birds, cohesion_radius)
    
    # Áp dụng các lực với trọng số tương ứng
    bird.apply_force(separation_force * separation_weight)
    bird.apply_force(alignment_force * alignment_weight)
    bird.apply_force(cohesion_force * cohesion_weight)
    
    # Nếu có thức ăn, cũng tính lực hướng đến thức ăn
    if food_positions and food_ripeness and len(food_positions) > 0:
        food_force = seek_food(bird, food_positions, food_ripeness)
        bird.apply_force(food_force * 1.5)  # Trọng số thức ăn cao hơn
    
def separation(bird, birds, separation_radius):
    """Tránh va chạm với các chim lân cận."""
    steering = Vector2D()
    count = 0
    
    for other in birds:
        if other is bird:
            continue
            
        distance = bird.position.distance_to(other.position)
        
        if distance < separation_radius and distance > 0:
            # Vector hướng từ chim khác đến chim này
            diff = bird.position - other.position
            diff = diff.normalize()
            # Nếu càng gần thì càng phải tránh mạnh
            diff = diff / distance
            steering = steering + diff
            count += 1
    
    if count > 0:
        steering = steering / count
    
    if steering.magnitude() > 0:
        steering = steering.normalize() * bird.max_force
        
    return steering

def alignment(bird, birds, alignment_radius):
    """Điều chỉnh bay theo hướng chung của đàn."""
    steering = Vector2D()
    count = 0
    
    for other in birds:
        if other is bird:
            continue
            
        distance = bird.position.distance_to(other.position)
        
        if distance < alignment_radius:
            steering = steering + other.velocity
            count += 1
    
    if count > 0:
        steering = steering / count
        steering = steering.normalize() * bird.max_speed
        steering = steering - bird.velocity
        steering = steering.limit(bird.max_force)
        
    return steering

def cohesion(bird, birds, cohesion_radius):
    """Di chuyển về phía trung tâm đàn."""
    steering = Vector2D()
    count = 0
    
    for other in birds:
        if other is bird:
            continue
            
        distance = bird.position.distance_to(other.position)
        
        if distance < cohesion_radius:
            steering = steering + other.position
            count += 1
    
    if count > 0:
        steering = steering / count
        # Hướng đến vị trí trung bình
        steering = steering - bird.position
        
        # Tiêu chuẩn hóa và nhân với tốc độ tối đa
        if steering.magnitude() > 0:
            steering = steering.normalize() * bird.max_speed
            
        # Tính lực lái
        steering = steering - bird.velocity
        steering = steering.limit(bird.max_force)
        
    return steering

def seek_food(bird, food_positions, ripeness, food_radius=50.0):
    """Di chuyển đến nơi có thức ăn."""
    if not food_positions or len(food_positions) == 0:
        return Vector2D()
    
    # Tìm thức ăn gần nhất đã chín
    nearest_food = None
    min_distance = float('inf')
    
    for i, pos in enumerate(food_positions):
        if ripeness[i] >= 1.0:  # Chỉ quan tâm đến quả đã chín
            food_pos = Vector2D(pos[0], pos[1])
            distance = bird.position.distance_to(food_pos)
            
            if distance < food_radius and distance < min_distance:
                nearest_food = food_pos
                min_distance = distance
    
    if nearest_food is not None:
        desired = nearest_food - bird.position
        if desired.magnitude() > 0:
            desired = desired.normalize() * bird.max_speed
            steering = desired - bird.velocity
            return steering.limit(bird.max_force)
    
    return Vector2D()

def seek(bird, target):
    """Tìm kiếm đến một vị trí mục tiêu."""
    # Tính vector mong muốn
    desired = target - bird.position
    # Chuẩn hóa và nhân với tốc độ tối đa
    desired = desired.normalize() * bird.max_speed
    # Tính lực chỉ đạo (steering)
    steering = desired - bird.velocity
    # Giới hạn lực
    steering = steering.limit(bird.max_force)
    return steering