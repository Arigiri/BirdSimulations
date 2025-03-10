"""
Điểm khởi đầu cho ứng dụng mô phỏng đàn chim én.
"""

import pyglet
from pyglet.window import key
from utils.config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
from view.renderer import SimpleRenderer

# Khởi tạo render
renderer = None

def update(dt):
    """Cập nhật trạng thái mô phỏng"""
    if renderer:
        renderer.update(dt)

def main():
    """Hàm chính để khởi chạy ứng dụng."""
    global renderer
    
    # Tạo cửa sổ pyglet
    window = pyglet.window.Window(
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        caption=WINDOW_TITLE
    )
    
    # Khởi tạo renderer
    renderer = SimpleRenderer(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # Trạng thái tạm dừng/chạy
    paused = False
    
    # Tạo FPS display một lần duy nhất
    fps_display = pyglet.window.FPSDisplay(window=window)
    fps_display.label.x = window.width - 100
    fps_display.label.y = window.height - 30
    fps_display.label.font_size = 14
    
    # Tạo labels thông tin
    info_label = pyglet.text.Label(
        'Birds: 0',
        font_name='Arial',
        font_size=14,
        x=10,
        y=WINDOW_HEIGHT - 60,
        color=(255, 255, 255, 255)
    )
    
    # Hàm xử lý phím
    @window.event
    def on_key_press(symbol, modifiers):
        nonlocal paused
        
        if symbol == key.SPACE:
            # Tạm dừng/tiếp tục mô phỏng
            paused = not paused
        
        elif symbol == key.B:
            # Thêm 10 chim mới
            renderer.add_birds(10)
        
        elif symbol == key.R:
            # Đặt lại mô phỏng
            renderer.birds = []
            renderer.create_birds(50)
    
    @window.event
    def on_draw():
        window.clear()
        
        # Vẽ tiêu đề
        pyglet.text.Label(
            'Mô phỏng đàn chim én - Boids',
            font_name='Arial',
            font_size=24,
            x=window.width//2,
            y=window.height - 30,
            anchor_x='center',
            anchor_y='center'
        ).draw()
        
        # Cập nhật và vẽ label thông tin
        info_label.text = f'Birds: {renderer.get_bird_count()} | {"PAUSED" if paused else "RUNNING"}'
        info_label.draw()
        
        # Vẽ hướng dẫn
        instructions = [
            'SPACE: Tạm dừng/Tiếp tục',
            'B: Thêm 10 chim',
            'R: Đặt lại mô phỏng'
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
        
        # Vẽ các con chim
        renderer.draw()
        
        # Hiển thị FPS - chỉ vẽ, không tạo mới
        fps_display.draw()
    
    def update_with_pause(dt):
        if not paused:
            update(dt)
    
    # Đăng ký hàm update với khoảng thời gian 1/60 giây
    pyglet.clock.schedule_interval(update_with_pause, 1/60.0)
    
    pyglet.app.run()

if __name__ == "__main__":
    main()