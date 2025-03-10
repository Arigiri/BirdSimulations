from utils.vector import Vector2D
import numpy as np
from utils.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, MARGIN, SEPARATION_WEIGHT, ALIGNMENT_WEIGHT, COHESION_WEIGHT, EDGE_WEIGHT)

def calculate_steering(bird, all_birds, separation_radius, alignment_radius, cohesion_radius, 
                       food_positions=None, food_ripeness=None):

    """Tính toán và áp dụng các lực steering cho một con chim."""
    # Tính các lực cơ bản của boids
    separation_force = separation(bird, all_birds, separation_radius)
    alignment_force = alignment(bird, all_birds, alignment_radius)
    cohesion_force = cohesion(bird, all_birds, cohesion_radius)
    
    # Tính lực tránh biên màn hình với trọng số cao hơn
    edge_force = avoid_edges(bird, MARGIN)  # Tăng khoảng cách tránh biên lên 150px
    
    # Áp dụng các lực với trọng số tương ứng
    bird.apply_force(separation_force * SEPARATION_WEIGHT)
    bird.apply_force(alignment_force * ALIGNMENT_WEIGHT)
    bird.apply_force(cohesion_force * COHESION_WEIGHT)
    bird.apply_force(edge_force * EDGE_WEIGHT)  # Tăng trọng số lực biên lên 3.0
    
    # Nếu có thức ăn, cũng tính lực hướng đến thức ăn
    if food_positions and food_ripeness and len(food_positions) > 0:
        food_force = seek_food(bird, food_positions, food_ripeness)
        bird.apply_force(food_force * 1.5)
    
    # Ràng buộc vị trí chim trong màn hình
    # constrain_to_screen(bird)

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
        
    return steering.normalize()

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
        
    return steering.normalize()

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
        
    return steering.normalize()

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

def avoid_edges(bird, margin):
    """
    Tạo lực đẩy dựa trên đường cong (spline) giữa vận tốc hiện tại 
    và hướng song song với tường khi tiếp cận biên màn hình.
    """
    steering = Vector2D()
    x, y = bird.position.x, bird.position.y
    vx, vy = bird.velocity.x, bird.velocity.y
    d_left = x
    d_right = WINDOW_WIDTH - x
    d_up = y
    d_down = WINDOW_HEIGHT - y
    M = bird.max_force
    # print(x, y)
    if y > WINDOW_HEIGHT - margin:
        # print("UP")
        if vx < 0:
            steering.x = (d_left / WINDOW_WIDTH) * (d_left / WINDOW_WIDTH)
            steering.y = -(d_up / WINDOW_HEIGHT) * (d_up / WINDOW_HEIGHT)
        else:
            steering.x = (d_right / WINDOW_WIDTH) * (d_right / WINDOW_WIDTH)
            steering.y = -(d_up / WINDOW_HEIGHT) * (d_up / WINDOW_HEIGHT)
    elif y < margin:
        # print("DOWN")
        if vx < 0:
            steering.x = (d_left / WINDOW_WIDTH) * (d_left / WINDOW_WIDTH)
            steering.y = (d_down / WINDOW_HEIGHT) * (d_down / WINDOW_HEIGHT)
        else:
            steering.x = (d_right / WINDOW_WIDTH) * (d_right / WINDOW_WIDTH)
            steering.y = (d_down / WINDOW_HEIGHT) * d_down / WINDOW_HEIGHT

    return steering.normalize()

def constrain_to_screen(bird):
    """Ràng buộc trực tiếp vị trí của chim trong màn hình."""
    padding = 5  # Khoảng đệm nhỏ để tránh bám sát biên
    print("BIRDS POSITION:", bird.position.x, bird.position.y)
    # Ràng buộc trục X
    if bird.position.x < padding:
        bird.position.x = padding
        bird.velocity.x *= -0.5  # Đảo ngược phần vận tốc theo X và giảm
    elif bird.position.x > WINDOW_WIDTH - padding:
        bird.position.x = WINDOW_WIDTH - padding
        bird.velocity.x *= -0.5
        
    # Ràng buộc trục Y
    if bird.position.y < padding:
        bird.position.y = padding
        bird.velocity.y *= -0.5  # Đảo ngược phần vận tốc theo Y và giảm
    elif bird.position.y > WINDOW_HEIGHT - padding:
        bird.position.y = WINDOW_HEIGHT - padding
        bird.velocity.y *= -0.5