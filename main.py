"""
Điểm khởi đầu cho ứng dụng mô phỏng đàn chim én.
"""

import pyglet
import time
import threading
import numpy as np
from pyglet.window import key
from utils.config import *
from view.renderer import SimpleRenderer
from model.fruit import FruitManager
from model.weather.main.weather_integration import WeatherIntegration

# Import module cho hiển thị thời tiết chi tiết
import matplotlib
matplotlib.use('TkAgg')  # Sử dụng backend TkAgg để tạo cửa sổ riêng biệt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Thêm đường dẫn root
import os
import sys
root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_path)

# Biến toàn cục cho cửa sổ thời tiết chi tiết
weather_window = None
weather_animation = None

# Khởi tạo render, quản lý trái cây và module thời tiết
renderer = None
fruit_manager = None
weather_integration = None

# Thêm biến toàn cục để theo dõi chim đang được chọn
selected_bird = None
bird_info_label = None

# Thêm biến toàn cục mới cho thông tin đàn
flock_info_label = None

# Định nghĩa kích thước thanh thông tin

def update(dt):
    """Cập nhật trạng thái mô phỏng với phương pháp linh hoạt"""
    global renderer, fruit_manager, selected_bird, weather_integration
    
    current_time = time.time()
    
    # Cập nhật module thời tiết
    if weather_integration:
        weather_integration.update(dt)
    
    # Cập nhật trái cây
    if fruit_manager:
        # Lấy thông tin ảnh hưởng thời tiết đến quá trình chín
        if weather_integration:
            # Cập nhật tốc độ chín của mỗi quả dựa trên nhiệt độ tại vị trí
            for fruit in fruit_manager.fruits:
                pos_x, pos_y = fruit.position.x, fruit.position.y
                weather_factor = weather_integration.get_weather_influence_on_fruit(pos_x, pos_y)
                fruit.weather_factor = weather_factor
                
        # Cập nhật trái cây với thời gian hiện tại
        fruit_manager.update(current_time, dt)
    
    # Cập nhật renderer và chim
    if renderer:
        # Lưu thông tin trái cây vào renderer để các thành phần khác có thể truy cập
        if fruit_manager:
            # Cập nhật thuộc tính food_positions và food_ripeness của renderer
            renderer.food_positions = fruit_manager.positions
            renderer.food_ripeness = fruit_manager.ripeness
        
        # Sử dụng thông tin thời tiết để ảnh hưởng đến chim
        if weather_integration and hasattr(renderer, 'birds'):
            for bird in renderer.birds:
                bird_pos_x, bird_pos_y = bird.position.x, bird.position.y
                # Lấy thông tin thời tiết tại vị trí của chim
                weather_data = weather_integration.get_weather_for_birds(bird_pos_x, bird_pos_y)
                # Áp dụng ảnh hưởng của gió vào chim
                if weather_data["wind"]:
                    # Tạo lực gió ảnh hưởng đến chim (wind steering)
                    bird.apply_wind_force(weather_data["wind"], WIND_STEERING_FACTOR)
                
                # Áp dụng ảnh hưởng của nhiệt độ (nếu cần)
                if "temperature" in weather_data:
                    # Có thể thêm ảnh hưởng nhiệt độ đến chim ở đây
                    pass
        
        # Gọi phương thức update với tham số phù hợp
        renderer.update(dt)
        
        # Xử lý tương tác giữa chim và trái cây
        if fruit_manager and hasattr(renderer, 'birds'):
            for bird in renderer.birds:
                if fruit_manager.consume_fruit(bird.position, 15.0):
                    # Kiểm tra và lưu lại giá trị đói trước khi cho ăn (để hiển thị hiệu ứng)
                    old_hunger = bird.hunger if hasattr(bird, 'hunger') else None
                    
                    # Nếu chim có phương thức feed, gọi nó với giá trị từ config
                    if hasattr(bird, 'feed'):
                        bird.feed(FRUIT_NUTRITION_VALUE)  # Sử dụng hằng số từ config
                        
                        # Thêm thuộc tính hiển thị thông báo
                        bird.show_feed_message = True
                        bird.feed_message_time = current_time + 1.0  # Hiển thị trong 1 giây
                        
                        # Lưu thông tin về sự thay đổi đói để hiển thị
                        if old_hunger is not None:
                            bird.hunger_change = old_hunger - bird.hunger
                        
                        # Thêm hiệu ứng đổi màu tạm thời cho chim (nếu có thuộc tính color)
                        if hasattr(bird, 'color'):
                            # Lưu màu gốc nếu chưa được lưu
                            if not hasattr(bird, 'original_color'):
                                bird.original_color = bird.color.copy()
                            
                            # Đổi sang màu xanh lá (ăn no)
                            bird.color = (0, 255, 0)
                            
                            # Đặt thời gian để phục hồi màu
                            bird.color_reset_time = current_time + 0.5  # 0.5 giây
                    
                    # In thông báo để debug và kiểm tra giá trị hunger trước và sau
                    if old_hunger is not None:
                        print(f"Chim đã ăn quả! Độ đói: {old_hunger:.2f} -> {bird.hunger:.2f} (giảm {old_hunger - bird.hunger:.2f})")
                    else:
                        print(f"Chim đã ăn quả! Độ đói hiện tại: {bird.hunger if hasattr(bird, 'hunger') else 'N/A'}")

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

def show_detailed_weather(weather_integration):
    """Hiển thị cửa sổ thời tiết chi tiết giống như trong realtime_simulation.py"""
    global weather_window, weather_animation
    
    # Nếu đã có cửa sổ đang mở, không mở cửa sổ mới
    if weather_window and plt.fignum_exists(weather_window.number):
        print("Cửa sổ thời tiết chi tiết đã được mở")
        return
        
    # Lấy dữ liệu từ weather_integration
    width = weather_integration.width
    height = weather_integration.height
    
    # Tạo figure mới
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.canvas.manager.set_window_title('Mô phỏng thời tiết chi tiết')
    weather_window = fig
    
    # Lấy dữ liệu ban đầu
    temp = weather_integration.temp_field.get_temperature().reshape(height, width)
    wind_x = weather_integration.wind_field.get_wind_x().reshape(height, width)
    wind_y = weather_integration.wind_field.get_wind_y().reshape(height, width)
    
    # Thiết lập giá trị nhiệt độ min/max
    min_temp = max(0, np.min(temp) - 5)
    max_temp = min(45, np.max(temp) + 5)
    
    # Tham số hiển thị
    quiver_density = 10  # Hiển thị 1 mũi tên cho mỗi quiver_density ô
    cmap = plt.cm.hot
    
    # Vẽ trường nhiệt độ
    temp_plot = ax.imshow(temp, origin='lower', cmap=cmap, 
                         vmin=min_temp, vmax=max_temp, animated=True)
    
    # Thêm colorbar
    colorbar = fig.colorbar(temp_plot, ax=ax)
    colorbar.set_label('Nhiệt độ (°C)')
    
    # Tạo lưới cho vector gió
    y, x = np.mgrid[0:height:quiver_density, 0:width:quiver_density]
    
    # Vẽ gió
    quiver_plot = ax.quiver(
        x, y,
        wind_x[::quiver_density, ::quiver_density],
        wind_y[::quiver_density, ::quiver_density],
        color='white', scale=50, alpha=0.7
    )
    
    # Thêm tiêu đề và nhãn
    ax.set_title(f'Mô phỏng thời tiết chi tiết')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    
    # Thêm chú thích
    plt.figtext(0.02, 0.02, 'Phím Q: Thoát', fontsize=9)
    
    # Hàm khởi tạo animation
    def init_animation():
        temp_plot.set_array(temp)
        quiver_plot.set_UVC(
            wind_x[::quiver_density, ::quiver_density],
            wind_y[::quiver_density, ::quiver_density]
        )
        return temp_plot, quiver_plot
    
    # Hàm cập nhật animation
    def update_animation(frame):
        # Lấy dữ liệu mới từ weather_integration
        temp = weather_integration.temp_field.get_temperature().reshape(height, width)
        wind_x = weather_integration.wind_field.get_wind_x().reshape(height, width)
        wind_y = weather_integration.wind_field.get_wind_y().reshape(height, width)
        
        # Cập nhật trường nhiệt độ
        temp_plot.set_array(temp)
        
        # Cập nhật vector gió
        if frame % 2 == 0:  # Chỉ cập nhật gió mỗi 2 frames để tăng hiệu suất
            quiver_plot.set_UVC(
                wind_x[::quiver_density, ::quiver_density],
                wind_y[::quiver_density, ::quiver_density]
            )
        
        # Cập nhật tiêu đề
        steps = weather_integration.steps
        time_val = weather_integration.time
        ax.set_title(f'Mô phỏng thời tiết chi tiết (t={time_val:.2f}s, bước {steps})')
        
        return temp_plot, quiver_plot
    
    # Kết nối sự kiện nhấn phím
    def on_key_press(event):
        if event.key == 'q':
            plt.close(fig)
    
    fig.canvas.mpl_connect('key_press_event', on_key_press)
    
    # Tạo animation
    weather_animation = FuncAnimation(
        fig, update_animation, frames=1000,
        init_func=init_animation, blit=True, interval=50
    )
    
    # Hiển thị animation trong một luồng không chặn
    plt.tight_layout()
    plt.show(block=False)

def main():
    """Hàm chính để khởi chạy ứng dụng."""
    global renderer, fruit_manager, weather_integration
    
    # Tạo cửa sổ pyglet
    window = pyglet.window.Window(
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        caption=WINDOW_TITLE
    )
    
    # Khởi tạo renderer và fruit manager
    renderer = SimpleRenderer(WINDOW_WIDTH, WINDOW_HEIGHT)
    fruit_manager = FruitManager()
    
    # Khởi tạo module thời tiết
    try:
        weather_integration = WeatherIntegration(WINDOW_WIDTH, WINDOW_HEIGHT)
        print("Module thời tiết C++ đã được khởi tạo thành công!")
    except Exception as e:
        print(f"Không thể khởi tạo module thời tiết: {e}")
        weather_integration = None
    
    # Tạo một số trái cây ban đầu
    fruit_manager.add_random_fruits(5)
    
    # Trạng thái tạm dừng/chạy
    paused = False
    
    # Trạng thái hiển thị thời tiết
    show_weather = True
    
    # Tạo FPS display 
    fps_display = pyglet.window.FPSDisplay(window=window)
    fps_display.label.x = window.width - 100
    fps_display.label.y = window.height - 30
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
    
    # Tạo label thông tin thời tiết
    weather_info_label = pyglet.text.Label(
        'Weather: OK',
        font_name='Arial',
        font_size=14,
        x=10,
        y=WINDOW_HEIGHT - 85,
        color=(255, 255, 255, 255)
    )
    
    # Hàm xử lý phím
    @window.event
    def on_key_press(symbol, modifiers):
        nonlocal paused, show_weather
        
        # Nếu module thời tiết xử lý phím này, không thực hiện thêm
        if weather_integration and weather_integration.on_key_press(symbol, modifiers):
            return
        
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
            renderer.create_birds(50)
            
            # Cũng đặt lại trái cây
            fruit_manager = FruitManager()
            fruit_manager.add_random_fruits(5)
            
        elif symbol == key.W:
            # Hiển thị/ẩn thời tiết
            show_weather = not show_weather
            
        elif symbol == key.V:
            # Hiển thị cửa sổ thời tiết chi tiết
            if weather_integration:
                show_detailed_weather(weather_integration)
                print("Đã mở cửa sổ thời tiết chi tiết")
            else:
                print("Không có module thời tiết để hiển thị chi tiết")
                
        elif symbol == key.I:
            # Bật/tắt chế độ lặp liên tục cho mô hình thời tiết
            if weather_integration:
                auto_iterate = weather_integration.toggle_auto_iteration()
                print(f"Chế độ lặp tự động thời tiết: {'BẬT' if auto_iterate else 'TẮT'}")
            else:
                print("Không có module thời tiết để điều khiển")
    
    @window.event
    def on_mouse_motion(x, y, dx, dy):
        # Chuyển tiếp sự kiện cho module thời tiết nếu có
        if weather_integration:
            weather_integration.on_mouse_motion(x, y, dx, dy)
    
    @window.event
    def on_mouse_press(x, y, button, modifiers):
        global selected_bird, bird_info_label
        
        # Chuyển tiếp sự kiện cho module thời tiết nếu có
        if weather_integration:
            if weather_integration.on_mouse_press(x, y, button, modifiers):
                return
        
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
            
            # Thêm thông tin thời tiết tại vị trí chim nếu có module thời tiết
            if weather_integration:
                weather_data = weather_integration.get_weather_for_birds(
                    selected_bird.position.x, selected_bird.position.y
                )
                if weather_data:
                    info_text += "\nThời tiết tại vị trí chim:\n"
                    info_text += f"Nhiệt độ: {weather_data['temperature']:.1f}°C\n"
                    if weather_data["wind"]:
                        wind = weather_data["wind"]
                        info_text += f"Gió: ({wind.x:.2f}, {wind.y:.2f})\n"
                
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

    def update_weather_info():
        """Cập nhật thông tin thời tiết"""
        if weather_integration:
            stats = weather_integration.statistics
            weather_info_label.text = (f'Thời tiết: '
                                     f'Min: {stats["min_temp"]:.1f}°C, '
                                     f'Max: {stats["max_temp"]:.1f}°C, '
                                     f'TB: {stats["mean_temp"]:.1f}°C')
            weather_info_label.draw()

    @window.event
    def on_draw():
        window.clear()
        
        # Vẽ module thời tiết nếu được bật
        if show_weather and weather_integration:
            weather_integration.draw()
        
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
            bold=True,
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
            width=2,
            color=(100, 100, 100)
        )
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
        
        # Cập nhật thông tin thời tiết
        update_weather_info()
        
        # Vẽ hướng dẫn
        instructions = [
            'SPACE: Tạm dừng/Tiếp tục',
            'B: Thêm 10 chim',
            'F: Thêm 5 trái cây',
            'R: Đặt lại mô phỏng',
            'W: Hiển thị/ẩn thời tiết',
            'Click trái: Chọn chim',
            'Click phải: Tạo trái cây'
        ]
        
        for i, text in enumerate(instructions):
            pyglet.text.Label(
                text,
                font_name='Arial',
                font_size=12,
                x=10,
                y=WINDOW_HEIGHT - 110 - i * 20,
                color=(200, 200, 200, 255)
            ).draw()
        
        # Vẽ trái cây
        draw_fruits()
        
        # Vẽ các con chim
        renderer.draw()
        
        # Vẽ UI module thời tiết
        if weather_integration:
            weather_integration.draw_ui()
        
        # Vẽ thông báo cho các chim đang ăn
        if hasattr(renderer, 'birds'):
            for bird in renderer.birds:
                if hasattr(bird, 'show_feed_message') and bird.show_feed_message:
                    if hasattr(bird, 'hunger_change'):
                        message = f"-{bird.hunger_change:.1f}"
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
                width=1,
                color=(100, 100, 100)
            )
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
                        width=2, 
                        color=(255, 255, 0)
                    )
                    line.draw()
        
        # Hiển thị FPS
        fps_display.draw()
    
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