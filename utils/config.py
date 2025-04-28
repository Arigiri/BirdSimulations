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
MAX_BIRDS = 60             # Tăng số chim tối đa để mô phỏng đông vui hơn
TARGET_FPS = 60
SIMULATION_SPEED = 6.0      # Tăng tốc mô phỏng cho cảm giác sống động
INITIAL_BIRD_COUNT = 6      # Bắt đầu với nhiều chim hơn để hệ sinh thái hoạt động ngay

# Các tham số Boid
SEPARATION_RADIUS = 22.0           # Chim tránh nhau sát hơn một chút
ALIGNMENT_RADIUS = 48.0
COHESION_RADIUS = 72.0
SEPARATION_WEIGHT = 1.6            # Tăng nhẹ sức mạnh tránh va chạm
ALIGNMENT_WEIGHT = 1.1
COHESION_WEIGHT = 1.0
EDGE_WEIGHT = 3.2                   # Tăng nhẹ lực đẩy khỏi biên
FOOD_WEIGHT = 1.8                   # Tăng động lực tìm quả

MAX_SPEED = 53.0                    # Chim bay nhanh hơn
MIN_SPEED = 41.0
MAX_FORCE = 3.2

MARGIN = 48

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
HUNGER_RATE = 0.012  # Chim đói nhanh hơn một chút, tạo động lực tìm quả

# Các tham số trái cây
FRUIT_RADIUS = 6.0
FRUIT_COLOR_UNRIPE = (0, 255, 0, 255)    # Xanh lá cây
FRUIT_COLOR_RIPE = (255, 80, 0, 255)     # Đỏ cam nổi bật hơn
RIPENING_RATE = 0.12                     # Quả chín nhanh hơn
FRUIT_NUTRITION_VALUE = 2.5              # Giá trị dinh dưỡng tăng nhẹ
FRUIT_SPAWN_STEP_INTERVAL = 7            # Quả mọc thường xuyên hơn

# -----------------------------
# Cài đặt cho Weather Module
# -----------------------------

# Cài đặt kích thước lưới
GRID_SIZE_X = 100  # Số điểm lưới theo chiều ngang
GRID_SIZE_Y = 80   # Số điểm lưới theo chiều dọc
GRID_SPACING_K = 10.0  # Khoảng cách giữa các điểm lưới (đơn vị)

# Cài đặt nhiệt độ
THERMAL_DIFFUSIVITY = 0.92  # Hệ số khuếch tán nhiệt κ, giúp bản đồ nhiệt động hơn
INITIAL_TEMPERATURE = 18.0  # Nhiệt độ nền thấp hơn, vùng nóng nổi bật hơn
HOTSPOT_TEMPERATURE = 42.0  # Nhiệt độ tại điểm nóng tăng nhẹ

# Cài đặt vật lý
DELTA_T = 0.1  # Bước thời gian mỗi lần cập nhật (giây)
T_MAX = 1000.0  # Thời gian mô phỏng tối đa (giây)

# Cài đặt gió
WIND_STRENGTH = 5.0  # Cường độ gió
WIND_ANIMATION_SPEED = 0.1  # Tốc độ thay đổi trường gió

# Cài đặt hiển thị
HEATMAP_ALPHA = 180  # Độ đậm của heatmap (0-255)
HEATMAP_RESOLUTION = 1  # Độ phân giải heatmap (1 = đầy đủ, 2 = giảm 1/2,...)
WIND_ARROW_SCALE = 0.1  # Tỷ lệ kích thước mũi tên gió
WIND_SCALE = WIND_ARROW_SCALE  # Alias cho WIND_ARROW_SCALE để tương thích với heatmap_renderer
WIND_SAMPLING = 20  # Số ô lưới giữa các mũi tên gió để giảm độ dày đặc
WIND_COLOR = (255, 255, 255, 180)  # Màu sắc của mũi tên gió (RGBA)

# Cài đặt tác động của thời tiết
RIPENING_TEMPERATURE_FACTOR = 0.07  # Tăng ảnh hưởng của nhiệt độ đến tốc độ chín của quả
WIND_STEERING_FACTOR = 0.2  # Hệ số ảnh hưởng của gió đến hướng bay của chim
