import numpy as np
import time
import os
import sys
from utils.vector import Vector2D
from utils.config import *
from model.weather.visualization import HeatmapRenderer, WindFieldRenderer

# Thêm thư mục chứa module C++ vào path
current_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.abspath(os.path.join(current_dir, '..', 'python'))
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

class WeatherIntegration:
    """
    Lớp tích hợp module thời tiết C++ vào mô phỏng đàn chim.
    """
    
    def __init__(self, width, height):
        """
        Khởi tạo lớp tích hợp thời tiết.
        
        Args:
            width (int): Chiều rộng cửa sổ hiển thị
            height (int): Chiều cao cửa sổ hiển thị
        """
        self.window_width = width
        self.window_height = height
        
        # Cài đặt kích thước lưới (số điểm lưới)
        self.grid_width = GRID_SIZE_X
        self.grid_height = GRID_SIZE_Y
        
        # Tham số vật lý
        self.dx = GRID_SPACING_K
        self.kappa = THERMAL_DIFFUSIVITY
        
        # Đang với chuột
        self.mouse_pos = (0, 0)
        self.mouse_pressed = False
        self.cursor_size = 10
        self.cursor_strength = 30.0
        
        # Trạng thái hiện tại
        self.time = 0.0
        self.steps = 0
        self.statistics = {"min_temp": 15, "max_temp": 30, "mean_temp": 22}
        
        # Flag để kiểm tra xem module C++ đã được khởi tạo chưa
        self.initialized = False
        
        # Thử tải module C++
        try:
            # Import module C++
            import cpp_weather
            self.cpp_weather = cpp_weather
            
            # Khởi tạo các đối tượng C++
            self.solver = self.cpp_weather.Solver(
                self.grid_width, self.grid_height, self.dx, self.kappa
            )
            self.temp_field = self.cpp_weather.TemperatureField(
                self.grid_width, self.grid_height
            )
            self.wind_field = self.cpp_weather.WindField(
                self.grid_width, self.grid_height
            )
            
            # Đặt nhiệt độ ban đầu và tạo gió
            self.initialize_weather()
            
            # Khởi tạo các lớp renderer
            self.heatmap_renderer = HeatmapRenderer(
                self.temp_field, self.window_width, self.window_height
            )
            self.wind_renderer = WindFieldRenderer(
                self.wind_field, self.window_width, self.window_height
            )
            
            # Đánh dấu đã khởi tạo thành công
            self.initialized = True
            
            print("Khởi tạo module thời tiết C++ thành công")
        except ImportError as e:
            # Fix encoding for Windows console
            try:
                print(f"Không thể tải module C++ 'cpp_weather': {e}")
            except UnicodeEncodeError:
                print(f"Could not load C++ module 'cpp_weather': {e}")
            self.initialized = False
        except Exception as e:
            # Fix encoding for Windows console
            try:
                print(f"Lỗi khi khởi tạo module thời tiết: {e}")
            except UnicodeEncodeError:
                print(f"Error initializing weather module: {e}")
            self.initialized = False
    
    def initialize_weather(self):
        """
        Khởi tạo điều kiện thời tiết ban đầu.
        """
        if not self.initialized:
            return
            
        # Đặt nhiệt độ đồng nhất làm nền
        self.temp_field.set_uniform(INITIAL_TEMPERATURE)
            
        # Tạo gradient nhiệt độ theo hướng North-South
        try:
            # Thử dùng GradientDirection nếu có
            self.temp_field.set_gradient(
                15.0, 30.0, self.cpp_weather.GradientDirection.NORTH_SOUTH
            )
        except Exception:
            # Nếu không có, tự tạo gradient thủ công
            temps = self.temp_field.get_temperature().reshape(self.grid_height, self.grid_width)
            for i in range(self.grid_height):
                t = i / self.grid_height  # 0 -> 1
                row_temp = 15 + 15 * t  # 15 -> 30
                temps[i, :] = row_temp
            self.temp_field.set_temperature(temps.flatten())
            
        # Thêm một nguồn nhiệt ở giữa
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        self.temp_field.add_heat_source(center_x, center_y, 15.0, self.grid_width // 8)
            
        # Tạo trường gió
        self.wind_field.generate_gaussian_field(5, WIND_STRENGTH, self.grid_width // 8)
            
        # Cập nhật thống kê nhiệt độ
        self.update_statistics()
    
    def set_checkerboard_pattern(self):
        """
        Tạo mẫu bàn cờ cho trường nhiệt độ (chỉ để thử nghiệm).
        """
        if not self.initialized:
            return
        
        # Lấy mảng nhiệt độ hiện tại
        temps = self.temp_field.get_temperature().reshape(self.grid_height, self.grid_width)
        
        # Tạo mẫu bàn cờ
        for i in range(self.grid_height):
            for j in range(self.grid_width):
                if (i + j) % 2 == 0:
                    temps[i, j] = 30.0
                else:
                    temps[i, j] = 15.0
        
        # Đặt lại nhiệt độ
        self.temp_field.set_temperature(temps.flatten())
        self.update_statistics()
    
    def update(self, dt):
        """
        Cập nhật trạng thái thời tiết.
        
        Args:
            dt (float): Thời gian trôi qua kể từ lần cập nhật trước
        """
        if not self.initialized:
            return
            
        # Lấy dữ liệu hiện tại
        temp_data = self.temp_field.get_temperature()
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
            
        # Tính bước thời gian phù hợp với CFL
        sim_dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        sim_dt = min(0.1, sim_dt)  # Giới hạn dt để tránh không ổn định
            
        # Điều chỉnh dt với hệ số mô phỏng
        sim_dt *= SIMULATION_SPEED
            
        # Cập nhật trường nhiệt độ
        new_temp = self.solver.solve_rk4_step(
            temp_data, wind_x, wind_y, sim_dt
        )
        self.temp_field.set_temperature(new_temp)
            
        # Thêm nguồn nhiệt nếu đang nhấn chuột
        if self.mouse_pressed:
            # Chuyển đổi vị trí chuột thành chỉ số lưới
            grid_x = int(self.mouse_pos[0] / self.window_width * self.grid_width)
            grid_y = int(self.mouse_pos[1] / self.window_height * self.grid_height)
            
            # Đảm bảo chỉ số lưới hợp lệ
            grid_x = max(0, min(grid_x, self.grid_width - 1))
            grid_y = max(0, min(grid_y, self.grid_height - 1))
            
            # Thêm nguồn nhiệt
            self.temp_field.add_heat_source(
                grid_x, grid_y, self.cursor_strength, self.cursor_size
            )
            
        # Đôi khi cập nhật trường gió để tạo sự thay đổi
        if self.steps % 20 == 0 and self.steps > 0:
            self.wind_field.generate_gaussian_field(
                5, WIND_STRENGTH, self.grid_width // 8
            )
            
        # Cập nhật thống kê
        self.update_statistics()
            
        # Cập nhật thời gian mô phỏng
        self.time += sim_dt
        self.steps += 1
    
    def update_statistics(self):
        """Cập nhật thống kê nhiệt độ."""
        try:
            # Lấy dữ liệu nhiệt độ
            temp_data = self.temp_field.get_temperature()
            
            # Tính toán thống kê
            self.statistics = {
                "min_temp": np.min(temp_data),
                "max_temp": np.max(temp_data),
                "mean_temp": np.mean(temp_data)
            }
        except Exception as e:
            print(f"Lỗi khi cập nhật thống kê: {e}")
    
    def draw(self):
        """
        Vẽ trường nhiệt độ và gió.
        """
        if not self.initialized:
            return
            
        # Vẽ heatmap nhiệt độ
        self.heatmap_renderer.draw()
        
        # Vẽ trường gió
        self.wind_renderer.draw()
    
    def draw_ui(self):
        """
        Vẽ giao diện điều khiển và thông tin (nếu cần).
        """
        pass  # Sẽ cài đặt sau nếu cần
    
    def on_mouse_motion(self, x, y, dx, dy):
        """
        Xử lý sự kiện di chuyển chuột.
        
        Args:
            x, y: Vị trí hiện tại của chuột
            dx, dy: Thay đổi vị trí so với lần di chuyển trước
            
        Returns:
            bool: True nếu đã xử lý sự kiện, False nếu không
        """
        # Cập nhật vị trí chuột
        self.mouse_pos = (x, y)
        return False
    
    def on_mouse_press(self, x, y, button, modifiers):
        """
        Xử lý sự kiện nhấn chuột.
        
        Args:
            x, y: Vị trí nhấn chuột
            button: Nút chuột được nhấn
            modifiers: Phím modifier (Shift, Ctrl, etc.)
            
        Returns:
            bool: True nếu đã xử lý sự kiện, False nếu không
        """
        if not self.initialized:
            return False
            
        # Cập nhật vị trí và trạng thái chuột
        self.mouse_pos = (x, y)
        self.mouse_pressed = True
        
        # Kiểm tra xem vị trí click có nằm trong khu vực hiển thị thời tiết không
        # (trừ đi thanh thông tin ở bên phải)
        if x < self.window_width - INFO_PANEL_WIDTH:
            # Chuyển đổi vị trí chuột thành chỉ số lưới
            grid_x = int(x / self.window_width * self.grid_width)
            grid_y = int(y / self.window_height * self.grid_height)
            
            # Đảm bảo chỉ số lưới hợp lệ
            grid_x = max(0, min(grid_x, self.grid_width - 1))
            grid_y = max(0, min(grid_y, self.grid_height - 1))
            
            # Thêm nguồn nhiệt
            self.add_heat_source(grid_x, grid_y, self.cursor_strength, self.cursor_size)
            
            # Đã xử lý sự kiện
            return True
            
        return False
    
    def on_mouse_release(self, x, y, button, modifiers):
        """
        Xử lý sự kiện thả chuột.
        """
        self.mouse_pressed = False
        return False
    
    def on_key_press(self, symbol, modifiers):
        """
        Xử lý sự kiện nhấn phím.
        
        Args:
            symbol: Mã phím được nhấn
            modifiers: Phím modifier (Shift, Ctrl, etc.)
            
        Returns:
            bool: True nếu đã xử lý sự kiện, False nếu không
        """
        from pyglet.window import key
        
        if not self.initialized:
            return False
            
        # Phím R: Đặt lại trường nhiệt độ và gió
        if symbol == key.R:
            self.initialize_weather()
            return True
            
        # Phím C: Tạo mẫu bàn cờ
        elif symbol == key.C:
            self.set_checkerboard_pattern()
            return True
            
        # Phím G: Bật/tắt hiển thị trường gió
        elif symbol == key.G:
            self.wind_renderer.toggle_visibility()
            return True
            
        # Phím +/-: Tăng/giảm kích thước con trỏ
        elif symbol == key.PLUS or symbol == key.NUM_ADD:
            self.cursor_size = min(30, self.cursor_size + 2)
            print(f"Kích thước con trỏ: {self.cursor_size}")
            return True
            
        elif symbol == key.MINUS or symbol == key.NUM_SUBTRACT:
            self.cursor_size = max(2, self.cursor_size - 2)
            print(f"Kích thước con trỏ: {self.cursor_size}")
            return True
            
        # Phím Up/Down: Tăng/giảm cường độ nguồn nhiệt
        elif symbol == key.UP:
            self.cursor_strength += 5
            print(f"Cường độ nhiệt: {self.cursor_strength}")
            return True
            
        elif symbol == key.DOWN:
            self.cursor_strength = max(5, self.cursor_strength - 5)
            print(f"Cường độ nhiệt: {self.cursor_strength}")
            return True
            
        return False  # Không xử lý phím này
    
    def add_heat_source(self, x, y, strength, radius):
        """
        Thêm nguồn nhiệt vào trường nhiệt độ.
        
        Args:
            x, y: Vị trí nguồn nhiệt
            strength: Cường độ nguồn nhiệt
            radius: Bán kính ảnh hưởng
        """
        if not self.initialized:
            return
            
        try:
            self.temp_field.add_heat_source(x, y, strength, radius)
        except Exception as e:
            print(f"Lỗi khi thêm nguồn nhiệt: {e}")
    
    def get_temperature_at(self, x, y):
        """
        Lấy giá trị nhiệt độ tại một điểm trên màn hình.
        
        Args:
            x, y: Tọa độ điểm trên màn hình
            
        Returns:
            float: Giá trị nhiệt độ
        """
        if not self.initialized:
            return 0.0
            
        try:
            # Chuyển đổi tọa độ màn hình thành chỉ số lưới
            grid_x = int(x / self.window_width * self.grid_width)
            grid_y = int(y / self.window_height * self.grid_height)
            
            # Đảm bảo chỉ số lưới hợp lệ
            grid_x = max(0, min(grid_x, self.grid_width - 1))
            grid_y = max(0, min(grid_y, self.grid_height - 1))
            
            # Lấy nhiệt độ
            temps = self.temp_field.get_temperature().reshape(self.grid_height, self.grid_width)
            return temps[grid_y, grid_x]
        except Exception as e:
            print(f"Lỗi khi lấy nhiệt độ: {e}")
            return 0.0
    
    def get_wind_at(self, x, y):
        """
        Lấy vector gió tại một điểm trên màn hình.
        
        Args:
            x, y: Tọa độ điểm trên màn hình
            
        Returns:
            Vector2D: Vector gió
        """
        if not self.initialized:
            return Vector2D(0, 0)
            
        try:
            # Chuyển đổi tọa độ màn hình thành chỉ số lưới
            grid_x = int(x / self.window_width * self.grid_width)
            grid_y = int(y / self.window_height * self.grid_height)
            
            # Đảm bảo chỉ số lưới hợp lệ
            grid_x = max(0, min(grid_x, self.grid_width - 1))
            grid_y = max(0, min(grid_y, self.grid_height - 1))
            
            # Lấy vector gió
            wind_x = self.wind_field.get_wind_x().reshape(self.grid_height, self.grid_width)
            wind_y = self.wind_field.get_wind_y().reshape(self.grid_height, self.grid_width)
            
            return Vector2D(wind_x[grid_y, grid_x], wind_y[grid_y, grid_x])
        except Exception as e:
            print(f"Lỗi khi lấy gió: {e}")
            return Vector2D(0, 0)
    
    def get_weather_for_birds(self, x, y):
        """
        Lấy thông tin thời tiết tại vị trí của chim.
        
        Args:
            x, y: Vị trí của chim
            
        Returns:
            dict: Thông tin thời tiết, bao gồm nhiệt độ và gió
        """
        if not self.initialized:
            return {"temperature": 20.0, "wind": None}
            
        temperature = self.get_temperature_at(x, y)
        wind = self.get_wind_at(x, y)
            
        return {
            "temperature": temperature,
            "wind": wind
        }
    
    def get_weather_influence_on_fruit(self, x, y):
        """
        Tính toán hệ số ảnh hưởng của thời tiết đến tốc độ chín của quả.
        
        Args:
            x, y: Vị trí của quả
            
        Returns:
            float: Hệ số ảnh hưởng (>1: chín nhanh hơn, <1: chín chậm hơn)
        """
        if not self.initialized:
            return 1.0
            
        temperature = self.get_temperature_at(x, y)
        
        # Điều chỉnh hệ số tốc độ chín dựa trên nhiệt độ
        # - Nhiệt độ <10°C: chín chậm
        # - Nhiệt độ 20-25°C: bình thường
        # - Nhiệt độ >30°C: chín nhanh
        if temperature < 10:
            ripening_factor = 0.5
        elif temperature < 20:
            ripening_factor = 0.8
        elif temperature <= 25:
            ripening_factor = 1.0
        elif temperature <= 30:
            ripening_factor = 1.2
        else:
            ripening_factor = 1.5
            
        return ripening_factor
    
    def toggle_auto_iteration(self):
        """
        Bật/tắt chế độ lặp liên tục của mô hình thời tiết.
        
        Returns:
            bool: Trạng thái mới của chế độ lặp tự động
        """
        if not hasattr(self, 'auto_iterate'):
            self.auto_iterate = False
            
        self.auto_iterate = not self.auto_iterate
        
        if self.auto_iterate:
            # Tăng tần suất cập nhật trường gió khi ở chế độ tự động
            self.auto_update_interval = 10  # Cập nhật sau mỗi 10 bước
        
        return self.auto_iterate
        
    def get_temperature_field(self):
        """
        Lấy mảng 2D chứa dữ liệu nhiệt độ để hiển thị
        
        Returns:
            numpy.ndarray: Mảng 2D trường nhiệt độ, hoặc None nếu không khởi tạo
        """
        if not self.initialized or not hasattr(self, 'temp_field'):
            return None
            
        # Lấy dữ liệu nhiệt độ và chuyển thành mảng 2D
        raw_temp = self.temp_field.get_temperature()
        temp_array = raw_temp.reshape(self.grid_height, self.grid_width)
        
        # Cập nhật min/max nhiệt độ
        import numpy as np
        self.min_temp = max(0, np.min(temp_array) - 5)
        self.max_temp = min(45, np.max(temp_array) + 5)
        
        return temp_array
        
    def get_wind_field(self):
        """
        Lấy hai mảng 2D chứa dữ liệu gió (x, y) để hiển thị
        
        Returns:
            tuple: (wind_x, wind_y) hai mảng 2D, hoặc (None, None) nếu không khởi tạo
        """
        if not self.initialized or not hasattr(self, 'wind_field'):
            return None, None
            
        # Lấy dữ liệu gió và chuyển thành mảng 2D
        raw_wind_x = self.wind_field.get_wind_x()
        raw_wind_y = self.wind_field.get_wind_y()
        
        wind_x = raw_wind_x.reshape(self.grid_height, self.grid_width)
        wind_y = raw_wind_y.reshape(self.grid_height, self.grid_width)
        
        return wind_x, wind_y
