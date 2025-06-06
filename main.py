"""
Điểm khởi đầu cho ứng dụng mô phỏng đàn chim én.
"""

import pyglet
import time
from pyglet.window import key
from utils.config import *
from view.renderer import SimpleRenderer
from model.fruit import FruitManager
from draw_temperature_map import draw_temperature_map

# Hàm giúp in an toàn với tiếng Việt
def print_safe(text_vn, text_en=None):
    """In thông báo an toàn với tiếng Việt, nếu lỗi UnicodeEncodeError thì in phiên bản tiếng Anh"""
    try:
        print(text_vn)
    except UnicodeEncodeError:
        if text_en:
            print(text_en)
        else:
            # Tạo phiên bản không dấu
            text = text_vn.replace("à", "a").replace("á", "a").replace("ả", "a").replace("ã", "a").replace("ạ", "a")
            text = text.replace("è", "e").replace("é", "e").replace("ẻ", "e").replace("ẽ", "e").replace("ẹ", "e")
            text = text.replace("ì", "i").replace("í", "i").replace("ỉ", "i").replace("ĩ", "i").replace("ị", "i")
            text = text.replace("ò", "o").replace("ó", "o").replace("ỏ", "o").replace("õ", "o").replace("ọ", "o")
            text = text.replace("ù", "u").replace("ú", "u").replace("ủ", "u").replace("ũ", "u").replace("ụ", "u")
            text = text.replace("ỳ", "y").replace("ý", "y").replace("ỷ", "y").replace("ỹ", "y").replace("ỵ", "y")
            text = text.replace("đ", "d")
            print(text)

# Thử import module thời tiết, nếu không được thì bỏ qua
try:
    from model.weather.main.weather_integration import WeatherIntegration
    import numpy as np
    print_safe("Module thời tiết đã được import thành công", "Weather module imported successfully")
    WEATHER_AVAILABLE = True
except ImportError as e:
    print_safe(f"Không thể import module thời tiết: {e}", f"Cannot import weather module: {e}")
    WEATHER_AVAILABLE = False
except Exception as e:
    print_safe(f"Lỗi không xác định khi import module thời tiết: {e}", f"Unknown error importing weather module: {e}")
    WEATHER_AVAILABLE = False

# Khởi tạo render và quản lý trái cây
renderer = None
fruit_manager = None

# Khởi tạo module thời tiết
weather_integration = None

# Trạng thái hiển thị thời tiết
show_weather = False
show_temperature_map = False
show_wind_field = False  # Trạng thái hiển thị hướng gió
temp_map_detail_level = 2  # Mức độ chi tiết ban đầu: 1 = cao nhất, 5 = thấp nhất
temp_data_update_interval = 0.5  # Khoảng thời gian cập nhật dữ liệu nhiệt độ (giây)
last_temp_update_time = 0

# Thêm biến toàn cục để theo dõi chim đang được chọn
selected_bird = None
bird_info_label = None

# Thêm biến toàn cục mới cho thông tin đàn
flock_info_label = None

# Định nghĩa kích thước thanh thông tin
def update_bird_info_label():
    """Cập nhật label hiển thị thông tin chim được chọn"""
    global bird_info_label
    
    # Xóa label cũ nếu có
    if bird_info_label:
        bird_info_label = None
    
    # Nếu có chim được chọn, tạo label thông tin
    if selected_bird:
        # Tạo text hiển thị
        info_text = "\n\nTHÔNG TIN CHIM ĐƯỢC CHỌN\n"
        info_text += "------------------------\n"
        
        # Truy cập trực tiếp thuộc tính của bird thay vì qua get_info()
        info_text += f"Vị trí: ({selected_bird.position.x:.1f}, {selected_bird.position.y:.1f})\n"
        info_text += f"Vận tốc: ({selected_bird.velocity.x:.1f}, {selected_bird.velocity.y:.1f})\n"
        info_text += f"Tốc độ: {selected_bird.velocity.magnitude():.1f}\n"
        
        # Hiển thị thông tin tùy chọn nếu có
        if hasattr(selected_bird, 'hunger'):
            info_text += f"Đói: {selected_bird.hunger:.2f}\n"
        
        if hasattr(selected_bird, 'lifetime'):
            info_text += f"Tuổi thọ: {selected_bird.lifetime:.1f}s\n"
        
        if hasattr(selected_bird, 'energy'):
            info_text += f"Năng lượng: {selected_bird.energy:.2f}\n"
            
        # Tạo label mới
        bird_info_label = pyglet.text.Label(
            info_text,
            font_name='Arial',
            font_size=12,
            x=WINDOW_WIDTH - INFO_PANEL_WIDTH + 10,
            y=WINDOW_HEIGHT - 250,
            width=INFO_PANEL_WIDTH - 20,
            multiline=True,
            color=(255, 255, 0, 255)
        )

def update(dt):
    """Cập nhật trạng thái mô phỏng với phương pháp linh hoạt"""
    global renderer, fruit_manager, selected_bird, weather_integration
    current_time = time.time()
    
    # Cập nhật module thời tiết
    if WEATHER_AVAILABLE and weather_integration:
        try:
            weather_integration.update(dt)
        except Exception as e:
            try:
                print(f"Lỗi khi cập nhật module thời tiết: {e}")
            except UnicodeEncodeError:
                print(f"Loi khi cap nhat module thoi tiet: {e}")
    # Cập nhật trái cây
    if fruit_manager:
        fruit_manager.update(current_time, dt)
    
    # Cập nhật renderer và chim
    if renderer:
        # Lưu thông tin trái cây vào renderer để các thành phần khác có thể truy cập
        if fruit_manager:
            # Cập nhật thuộc tính food_positions và food_ripeness của renderer
            renderer.food_positions = fruit_manager.positions
            renderer.food_ripeness = fruit_manager.ripeness
        
        # Gọi phương thức update với tham số phù hợp
        renderer.update(dt)
        
        # Xử lý tương tác giữa chim và trái cây
        if fruit_manager and hasattr(renderer, 'birds'):
            for bird in renderer.birds:
                # Chim không ăn nếu đã no
                if hasattr(bird, 'hunger') and bird.hunger >= 0.8:
                    continue  # Bỏ qua nếu chim đã no

                if fruit_manager.consume_fruit(bird.position, 15.0):
                    # Kiểm tra và lưu lại giá trị đói trước khi cho ăn (để hiển thị hiệu ứng)
                    old_hunger = bird.hunger if hasattr(bird, 'hunger') else None
                    
                    # Nếu chim có phương thức feed, gọi nó với giá trị từ config
                    if hasattr(bird, 'eat'):
                        bird.eat(FRUIT_NUTRITION_VALUE)  # Sử dụng hằng số từ config
                        
                        # Thêm thuộc tính hiển thị thông báo
                        bird.show_feed_message = True
                        bird.feed_message_time = current_time + 1.0  # Hiển thị trong 1 giây
                        
                        # Lưu thông tin về sự thay đổi đói để hiển thị
                        if old_hunger is not None:
                            bird.hunger_change = bird.hunger - old_hunger
                        
                        # Thêm hiệu ứng đổi màu tạm thời cho chim (nếu có thuộc tính color)
                        if hasattr(bird, 'color'):
                            # Lưu màu gốc nếu chưa được lưu
                            if not hasattr(bird, 'original_color'):
                                bird.original_color = tuple(bird.color)
                            
                            # Đổi sang màu xanh lá (ăn no)
                            bird.color = (0, 255, 0, 0)
                            
                            # Đặt thời gian để phục hồi màu
                            bird.color_reset_time = current_time + 0.5  # 0.5 giây
                    
                    # In thông báo để debug và kiểm tra giá trị hunger trước và sau
                    if old_hunger is not None:
                        print_safe(
                            f"Chim đã ăn quả! Độ đói: {old_hunger:.2f} -> {bird.hunger:.2f} (giảm {bird.hunger - old_hunger:.2f})",
                            f"Bird ate fruit! Hunger: {old_hunger:.2f} -> {bird.hunger:.2f} (reduced by {bird.hunger - old_hunger:.2f})"
                        )
                    else:
                        print_safe(
                            f"Chim đã ăn quả! Độ đói hiện tại: {bird.hunger if hasattr(bird, 'hunger') else 'N/A'}",
                            f"Bird ate fruit! Current hunger: {bird.hunger if hasattr(bird, 'hunger') else 'N/A'}"
                        )

        # Khôi phục màu gốc cho chim sau khi hiệu ứng kết thúc
        if hasattr(renderer, 'birds'):
            for bird in renderer.birds:
                if hasattr(bird, 'color_reset_time') and current_time >= bird.color_reset_time:
                    if hasattr(bird, 'original_color'):
                        bird.color = bird.original_color
                    # Xóa thuộc tính tạm thời
                    delattr(bird, 'color_reset_time')

        # Xử lý hiển thị thông báo ăn của chim
        if hasattr(renderer, 'birds'):
            for bird in renderer.birds:
                if hasattr(bird, 'show_feed_message') and bird.show_feed_message:
                    if current_time >= bird.feed_message_time:
                        bird.show_feed_message = False
                    # Nếu đây là chim được chọn, cập nhật thông tin ngay lập tức
                    if bird is selected_bird:
                        update_bird_info_label()

def main():
    """Hàm chính để khởi chạy ứng dụng."""
    import argparse
    global renderer, fruit_manager, weather_integration, WEATHER_AVAILABLE
    global selected_bird, bird_info_label, flock_info_label
    global temp_map_detail_level, temp_data_update_interval, last_temp_update_time

    # Parse arguments
    parser = argparse.ArgumentParser(description='Bird Simulation')
    parser.add_argument('--heat_scenario', type=str, default='default',
                        help="Kịch bản khởi tạo nhiệt độ: default, checkerboard, random_sources, stripe, uniform")
    parser.add_argument('--weather_mode', type=str, default='parallel',
                        help="Chế độ solver: parallel hoặc seq")
    args = parser.parse_args()
    heat_scenario = args.heat_scenario
    weather_mode = args.weather_mode
    valid_scenarios = ['default', 'checkerboard', 'random_sources', 'stripe', 'uniform']
    if heat_scenario not in valid_scenarios:
        print_safe(f"Kịch bản nhiệt không hợp lệ: {heat_scenario}. Chọn một trong: {valid_scenarios}",
                   f"Invalid heat scenario: {heat_scenario}. Choose from: {valid_scenarios}")
        heat_scenario = 'default'
    # Tạo cửa sổ pyglet
    window = pyglet.window.Window(
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        caption=WINDOW_TITLE
    )
    
    # Khởi tạo renderer và fruit manager
    renderer = SimpleRenderer(WINDOW_WIDTH, WINDOW_HEIGHT)
    fruit_manager = FruitManager()
    
    # Tạo một số trái cây ban đầu
    fruit_manager.add_random_fruits(5)
    
    # Khởi tạo module thởi tiết nếu có sẵn
    if WEATHER_AVAILABLE:
        try:
            print_safe("Đang khởi tạo module thởi tiết...", "Initializing weather module...")
            weather_integration = WeatherIntegration(WINDOW_WIDTH - INFO_PANEL_WIDTH, WINDOW_HEIGHT, mode=weather_mode)
            # Gọi initialize_weather với kịch bản mong muốn
            print("Current heat_scenario", heat_scenario)
            weather_integration.initialize_weather(scenario=heat_scenario)
            # Thử gọi phương thức get_temperature_field() để kiểm tra hoạt động
            temp_field = weather_integration.get_temperature_field()
            if temp_field is not None:
                print_safe(f"Đã tạo trường nhiệt độ kích thước {temp_field.shape}", 
                          f"Created temperature field with shape {temp_field.shape}")
            print_safe(f"Module thởi tiết đã được khởi tạo thành công với kịch bản '{heat_scenario}'!", 
                       f"Weather module has been initialized successfully with scenario '{heat_scenario}'!")
        except Exception as e:
            import traceback
            print_safe(f"Lỗi khi khởi tạo module thởi tiết: {e}", f"Error initializing weather module: {e}")
            traceback.print_exc()  # In chi tiết lỗi
            weather_integration = None
            WEATHER_AVAILABLE = False  # Tắt tính năng thởi tiết nếu có lỗi
            weather_integration = None
    else:
        weather_integration = None
        
    # Trạng thái tạm dừng/chạy
    paused = False
    
    # Tạo FPS display 
    fps_display = pyglet.window.FPSDisplay(window=window)
    fps_display.label.x = 30
    fps_display.label.y = 30
    fps_display.label.font_size = 14
    
    # Tạo labels thông tin
    info_label = pyglet.text.Label(
        'Birds: 0 | Fruits: 0',
        font_name='Arial',
        font_size=14,
        x=10,
        y=WINDOW_HEIGHT - 60,
        color=(255, 255, 255, 255)
    )
    
    # Hàm xử lý phím
    @window.event
    def on_key_press(symbol, modifiers):
        global fruit_manager, show_weather, show_temperature_map, temp_map_detail_level
        nonlocal paused
        
        if symbol == key.SPACE:
            # Tạm dừng/tiếp tục mô phỏng
            paused = not paused
        
        elif symbol == key.B:
            # Thêm 10 chim mới
            renderer.add_birds(10)
        
        elif symbol == key.F:
            # Thêm 5 trái cây mới
            fruit_manager.add_random_fruits(5)
        
        elif symbol == key.R:
            # Đặt lại mô phỏng
            renderer.birds = []
            renderer.create_birds(1)
            
            # Cũng đặt lại trái cây
            fruit_manager = FruitManager()
            fruit_manager.add_random_fruits(5)
            
        elif symbol == key.W:
            # Bật/tắt hiển thị module thời tiết
            show_weather = not show_weather
            try:
                print(f"Hiển thị thởi tiết: {'Bật' if show_weather else 'Tắt'}")
            except UnicodeEncodeError:
                print(f"Hien thi thoi tiet: {'Bat' if show_weather else 'Tat'}")
                
        elif symbol == key.T:
            # Bật/tắt hiển thị bản đồ nhiệt độ
            if WEATHER_AVAILABLE and weather_integration:
                show_temperature_map = not show_temperature_map
                try:
                    print(f"Bản đồ nhiệt độ: {'Hiện' if show_temperature_map else 'Ẩn'}")
                except UnicodeEncodeError:
                    print(f"Ban do nhiet do: {'Hien' if show_temperature_map else 'An'}")
                    
        elif symbol == key.G:
            # Bật/tắt hiển thị hướng gió
            if WEATHER_AVAILABLE and weather_integration:
                global show_wind_field
                show_wind_field = not show_wind_field
                try:
                    print(f"Hiển thị hướng gió: {'Bật' if show_wind_field else 'Tắt'}")
                except UnicodeEncodeError:
                    print(f"Hien thi huong gio: {'Bat' if show_wind_field else 'Tat'}")
        
        # Điều chỉnh độ chi tiết của bản đồ nhiệt độ bằng phím tắt Shift+UP và Shift+DOWN
        elif symbol == key.UP and modifiers & key.MOD_SHIFT:
            if WEATHER_AVAILABLE and weather_integration and show_temperature_map:
                # Tăng độ chi tiết (giảm giá trị detail_level)
                temp_map_detail_level = max(1, temp_map_detail_level - 1)
                from draw_temperature_map import reset_temp_map_cache
                reset_temp_map_cache()
                print_safe(f"Độ chi tiết bản đồ nhiệt độ: {temp_map_detail_level} (cao nhất: 1, thấp nhất: 5)", 
                           f"Temperature map detail level: {temp_map_detail_level} (highest: 1, lowest: 5)")
        
        elif symbol == key.DOWN and modifiers & key.MOD_SHIFT:
            if WEATHER_AVAILABLE and weather_integration and show_temperature_map:
                # Giảm độ chi tiết (tăng giá trị detail_level)
                temp_map_detail_level = min(5, temp_map_detail_level + 1)
                from draw_temperature_map import reset_temp_map_cache
                reset_temp_map_cache()
                print_safe(f"Độ chi tiết bản đồ nhiệt độ: {temp_map_detail_level} (cao nhất: 1, thấp nhất: 5)", 
                           f"Temperature map detail level: {temp_map_detail_level} (highest: 1, lowest: 5)")
    
    @window.event
    def on_mouse_press(x, y, button, modifiers):
        global selected_bird, bird_info_label
        
        # Thêm trái cây tại vị trí click chuột (phải)
        if button == pyglet.window.mouse.RIGHT:
            from utils.vector import Vector2D
            fruit_manager.add_fruit(Vector2D(x, y))
        
        # Chọn chim khi click chuột trái
        elif button == pyglet.window.mouse.LEFT:
            # Bỏ chọn chim hiện tại nếu có
            selected_bird = None
            
            # Kiểm tra xem có click vào chim nào không
            for bird in renderer.birds:
                if bird.contains_point(x, y):
                    selected_bird = bird
                    break
                    
            # Cập nhật label thông tin chim
            update_bird_info_label()

    def update_flock_info():
        """Cập nhật và hiển thị thông tin tổng quan về đàn chim"""
        global flock_info_label
        
        if renderer and hasattr(renderer, 'birds'):
            birds = renderer.birds
            
            if not birds:
                flock_info_text = "THÔNG TIN ĐÀN\n"
                flock_info_text += "----------------\n"
                flock_info_text += "Không có chim nào"
            else:
                # Tính toán các thông số của đàn
                avg_speed = sum(bird.velocity.magnitude() for bird in birds) / len(birds)
                min_speed = min(bird.velocity.magnitude() for bird in birds)
                max_speed = max(bird.velocity.magnitude() for bird in birds)
                
                # Tính trung tâm đàn
                center_x = sum(bird.position.x for bird in birds) / len(birds)
                center_y = sum(bird.position.y for bird in birds) / len(birds)
                
                # Tính bán kính đàn (khoảng cách trung bình từ tâm)
                distances = [((bird.position.x - center_x)**2 + 
                             (bird.position.y - center_y)**2)**0.5 for bird in birds]
                avg_radius = sum(distances) / len(distances)
                max_radius = max(distances)
                
                # Tính các thông số khác
                hunger_stats = []
                for bird in birds:
                    if hasattr(bird, 'hunger'):
                        hunger_stats.append(bird.hunger)
                
                # Tạo text hiển thị
                flock_info_text = "THÔNG TIN ĐÀN\n"
                flock_info_text += "----------------\n"
                flock_info_text += f"Số lượng: {len(birds)}\n"
                flock_info_text += f"Tốc độ TB: {avg_speed:.1f}\n"
                flock_info_text += f"Tốc độ (min/max): {min_speed:.1f}/{max_speed:.1f}\n"
                flock_info_text += f"Tâm đàn: ({center_x:.1f}, {center_y:.1f})\n"
                flock_info_text += f"Bán kính TB: {avg_radius:.1f}\n"
                flock_info_text += f"Bán kính max: {max_radius:.1f}\n"
                
                if hunger_stats:
                    avg_hunger = sum(hunger_stats) / len(hunger_stats)
                    flock_info_text += f"Độ đói TB: {avg_hunger:.2f}\n"
            
            # Tạo hoặc cập nhật label
            if not flock_info_label:
                flock_info_label = pyglet.text.Label(
                    flock_info_text,
                    font_name='Arial',
                    font_size=12,
                    x=WINDOW_WIDTH - INFO_PANEL_WIDTH + 10,  # Căn lề trái của panel
                    y=WINDOW_HEIGHT - 50,  # Đặt ở phía trên của panel
                    width=INFO_PANEL_WIDTH - 20,  # Để có biên 10px ở mỗi bên
                    multiline=True,
                    color=(255, 255, 255, 255)
                )
            else:
                flock_info_label.text = flock_info_text
        
        # Vẽ label nếu có
        if flock_info_label:
            flock_info_label.draw()

    @window.event
    def on_draw():
        global last_temp_update_time
        window.clear()
        
        # Vẽ bản đồ nhiệt độ nếu được bật
        if show_temperature_map and WEATHER_AVAILABLE and weather_integration:
            try:
                # Kiểm tra xem đã đến thời gian cập nhật dữ liệu mới hay chưa
                current_time = time.time()
                force_update = False
                
                if current_time - last_temp_update_time >= temp_data_update_interval:
                    last_temp_update_time = current_time
                    force_update = True
                
                # Gọi hàm vẽ với độ chi tiết và trạng thái cập nhật
                draw_temperature_map(weather_integration, WEATHER_AVAILABLE, temp_map_detail_level, force_update)
                
                # Hiển thị thông tin độ chi tiết của bản đồ nhiệt độ
                detail_info = pyglet.text.Label(
                    f'Độ chi tiết bản đồ nhiệt độ: {temp_map_detail_level} (Shift+↑/↓ để điều chỉnh)',
                    font_name='Arial',
                    font_size=12,
                    x=10,
                    y=10,
                    color=(255, 255, 255, 200)
                )
                detail_info.draw()
            except Exception as e:
                import traceback
                print_safe(
                    f"Lỗi khi vẽ bản đồ nhiệt độ: {e}",
                    f"Error drawing temperature map: {e}"
                )
                traceback.print_exc()  # In chi tiết lỗi
        
        # Vẽ hướng gió nếu được bật
        if show_wind_field and WEATHER_AVAILABLE and weather_integration:
            try:
                # Lấy dữ liệu trường gió
                wind_x, wind_y = weather_integration.get_wind_field()
                if wind_x is not None and wind_y is not None:
                    # Tạo và cập nhật WindFieldRenderer
                    if not hasattr(weather_integration, 'wind_renderer'):
                        # Tạo mới nếu chưa có
                        from model.weather.visualization import WindFieldRenderer
                        weather_integration.wind_renderer = WindFieldRenderer(
                            weather_integration.wind_field, 
                            WINDOW_WIDTH - INFO_PANEL_WIDTH, 
                            WINDOW_HEIGHT
                        )
                    
                    # Cập nhật dữ liệu gió
                    weather_integration.wind_renderer.update(wind_x, wind_y)
                    
                    # Vẽ mũi tên gió
                    weather_integration.wind_renderer.draw(
                        WINDOW_WIDTH - INFO_PANEL_WIDTH, 
                        WINDOW_HEIGHT, 
                        scale=3.0,  # Điều chỉnh kích thước mũi tên
                        arrow_color=(0, 150, 255),  # Màu xanh dương nhạt
                        opacity=200
                    )
                    
                    # Hiển thị chú thích
                    legend = pyglet.text.Label(
                        "Hướng gió (G: Ẩn/Hiện)",
                        font_name='Arial',
                        font_size=12,
                        x=10,
                        y=35,
                        color=(0, 150, 255, 255)
                    )
                    legend.draw()
            except Exception as e:
                import traceback
                print_safe(
                    f"Lỗi khi vẽ hướng gió: {e}",
                    f"Error drawing wind field: {e}"
                )
                traceback.print_exc()
        
        # Vẽ module thời tiết nếu được bật
        if show_weather and WEATHER_AVAILABLE and weather_integration:
            try:
                weather_integration.draw()
            except Exception as e:
                print_safe(
                    f"Lỗi khi vẽ module thời tiết: {e}",
                    f"Error drawing weather module: {e}"
                )
        
        # Vẽ thanh thông tin bên phải
        info_panel = pyglet.shapes.Rectangle(
            x=WINDOW_WIDTH - INFO_PANEL_WIDTH,
            y=0,
            width=INFO_PANEL_WIDTH,
            height=WINDOW_HEIGHT,
            color=(30, 30, 30)  # Màu xám đậm
        )
        info_panel.opacity = 200  # Hơi trong suốt
        info_panel.draw()
        
        # Vẽ tiêu đề thanh thông tin
        pyglet.text.Label(
            'BẢNG ĐIỀU KHIỂN',
            font_name='Arial',
            font_size=16,
            x=WINDOW_WIDTH - INFO_PANEL_WIDTH + (INFO_PANEL_WIDTH // 2),
            y=WINDOW_HEIGHT - 25,
            anchor_x='center',
            anchor_y='center',
            color=(200, 200, 255, 255)
        ).draw()
        
        # Vẽ đường kẻ phân cách
        separator = pyglet.shapes.Line(
            WINDOW_WIDTH - INFO_PANEL_WIDTH + 10, WINDOW_HEIGHT - 40,
            WINDOW_WIDTH - 10, WINDOW_HEIGHT - 40,
            color=(100, 100, 100)
        )
        separator.width = 2
        separator.draw()
        
        # Vẽ tiêu đề
        pyglet.text.Label(
            'Mô phỏng đàn chim én - Boids',
            font_name='Arial',
            font_size=24,
            x=(WINDOW_WIDTH - INFO_PANEL_WIDTH)//2,
            y=WINDOW_HEIGHT - 30,
            anchor_x='center',
            anchor_y='center'
        ).draw()
        
        # Cập nhật và vẽ label thông tin
        info_label.text = (f'Birds: {renderer.get_bird_count()} | '
                          f'Fruits: {len(fruit_manager.fruits)} | '
                          f'{"PAUSED" if paused else "RUNNING"}')
        info_label.draw()
        
        # Vẽ hướng dẫn
        instructions = [
            'SPACE: Tạm dừng/Tiếp tục',
            'B: Thêm 10 chim',
            'F: Thêm 5 trái cây',
            'R: Đặt lại mô phỏng',
            'Click trái: Chọn chim',
            'Click phải: Tạo trái cây'
        ]
        
        for i, text in enumerate(instructions):
            pyglet.text.Label(
                text,
                font_name='Arial',
                font_size=12,
                x=10,
                y=WINDOW_HEIGHT - 90 - i * 20,
                color=(200, 200, 200, 255)
            ).draw()
        fps_display.draw()
        # return 
        # Vẽ trái cây
        draw_fruits()
        
        # Vẽ các con chim
        renderer.draw()
        
        # Vẽ thông báo cho các chim đang ăn
        if hasattr(renderer, 'birds'):
            for bird in renderer.birds:
                if hasattr(bird, 'show_feed_message') and bird.show_feed_message:
                    if hasattr(bird, 'hunger_change'):
                        message = f"+{bird.hunger_change:.1f}"
                    else:
                        message = "Đã ăn!"
                    
                    # Tạo nhãn thông báo trên đầu chim
                    pyglet.text.Label(
                        message,
                        font_name='Arial',
                        font_size=10,
                        x=bird.position.x,
                        y=bird.position.y + 20,  # Hiển thị phía trên chim
                        anchor_x='center',
                        anchor_y='center',
                        color=(0, 255, 0, 255)
                    ).draw()
        
        # Hiển thị thông tin đàn chim
        if flock_info_label:
            flock_info_label.draw()
        
        # Hiển thị thông tin chim được chọn
        if bird_info_label:
            # Vẽ đường kẻ phân cách trên thông tin chim
            separator2 = pyglet.shapes.Line(
                WINDOW_WIDTH - INFO_PANEL_WIDTH + 10, WINDOW_HEIGHT - 230,
                WINDOW_WIDTH - 10, WINDOW_HEIGHT - 230,
                color=(100, 100, 100)
            )
            separator2.width = 1
            separator2.draw()
            
            # Vẽ label
            bird_info_label.draw()
            
            # Đánh dấu chim được chọn bằng viền sáng
            if selected_bird:
                vertices = selected_bird.get_vertices()
                
                # Vẽ đường viền quanh chim được chọn
                pyglet.gl.glLineWidth(2)
                for i in range(len(vertices)):
                    # Lấy điểm hiện tại và điểm tiếp theo
                    start = vertices[i]
                    end = vertices[(i + 1) % len(vertices)]  # Quay lại điểm đầu nếu là điểm cuối cùng
                    
                    # Vẽ đường thẳng nối hai điểm
                    line = pyglet.shapes.Line(
                        start[0], start[1], 
                        end[0], end[1], 
                        color=(255, 255, 0)
                    )
                    line.width = 2
                    line.draw()
        
        # Hiển thị FPS
        
    
    def draw_fruits():
        """Vẽ tất cả trái cây từ fruit manager"""
        for fruit in fruit_manager.fruits:
            # Lấy màu sắc dựa trên độ chín
            color = fruit.get_color()
            
            # Vẽ hình tròn đại diện cho trái cây
            x, y = fruit.position.x, fruit.position.y
            radius = fruit.radius
            
            # Tạo hình tròn với 16 đỉnh
            circle = pyglet.shapes.Circle(
                x=x, y=y, 
                radius=radius,
                color=color[:3],  # RGB
                batch=None
            )
            circle.opacity = color[3]  # Alpha
            circle.draw()
    
    def update_with_pause(dt):
        if not paused:
            update(dt)
        
        # Cập nhật thông tin đàn chim theo thời gian thực
        update_flock_info()
        
        # Cập nhật thông tin chim được chọn theo thời gian thực
        if selected_bird:
            update_bird_info_label()
    
    # Đăng ký hàm update với khoảng thời gian 1/60 giây
    pyglet.clock.schedule_interval(update_with_pause, 1/60.0)
    
    # Lập lịch tạo trái cây mới theo thời gian
    def spawn_random_fruit(dt):
        if not paused and fruit_manager and len(fruit_manager.fruits) < 50:  # Giới hạn tối đa 50 trái cây
            # 20% cơ hội tạo trái cây mới mỗi 2 giây
            import random
            if random.random() < 0.2:
                fruit_manager.add_random_fruits(1)
                
    pyglet.clock.schedule_interval(spawn_random_fruit, 2.0)
    
    pyglet.app.run()

if __name__ == "__main__":
    main()