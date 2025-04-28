"""
Cài đặt cấu hình cho Mô phỏng đàn chim én.
"""

# Cài đặt cửa sổ
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
WINDOW_TITLE = "Mô phỏng đàn chim én"

INFO_PANEL_WIDTH = 250  # Chiều rộng của thanh thông tin bên phải

FULLSCREEN = False
VSYNC = True

# Cài đặt mô phỏng
MAX_BIRDS = 50
TARGET_FPS = 60
SIMULATION_SPEED = 1.0
INITIAL_BIRD_COUNT = 1

# Các tham số Boid
SEPARATION_RADIUS = 25.0
ALIGNMENT_RADIUS = 50.0
COHESION_RADIUS = 75.0
SEPARATION_WEIGHT = 1.5
ALIGNMENT_WEIGHT = 1.0
COHESION_WEIGHT = 1.0
EDGE_WEIGHT = 3.0
FOOD_WEIGHT = 1.5


MAX_SPEED = 50.0
MIN_SPEED = 40.0
MAX_FORCE = 3.0


MARGIN = 50

# Các tham số chim
BIRD_SIZE = 10.0
# Danh sách màu sắc cho chim
BIRD_COLORS = [
    (255, 255, 255, 255),  # Trắng
    (255, 0, 0, 255),      # Đỏ
    (0, 255, 0, 255),      # Xanh lá
    (0, 0, 255, 255),      # Xanh dương
    (255, 255, 0, 255),    # Vàng
    (255, 0, 255, 255),    # Hồng
    (0, 255, 255, 255),    # Xanh lam
    (255, 165, 0, 255),    # Cam
    (128, 0, 128, 255),    # Tím
]
# Màu mặc định cho chim
BIRD_COLOR = BIRD_COLORS[0]
HUNGER_RATE = 0.01  # Tỷ lệ đói mỗi frame

# Các tham số trái cây
FRUIT_RADIUS = 5.0
FRUIT_COLOR_UNRIPE = (0, 255, 0, 255)    # Xanh lá cây
FRUIT_COLOR_RIPE = (255, 165, 0, 255)    # Cam
RIPENING_RATE = 0.1                    # Tốc độ chín (đơn vị độ chín/giây)
FRUIT_NUTRITION_VALUE = 0.3            # Giá trị dinh dưỡng của mỗi quả (giảm độ đói)
