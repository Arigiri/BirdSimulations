"""
Script kiểm tra đơn giản cho việc tích hợp C++ với Python
"""

import numpy as np
import matplotlib.pyplot as plt
import time
import os
import sys

print("Current directory:", os.getcwd())
print("Python version:", sys.version)
print("Python executable:", sys.executable)

# Tạo một trường nhiệt độ đơn giản cho việc kiểm thử
def create_temperature_field(width, height):
    """Tạo trường nhiệt độ mẫu có dạng gradient và một nguồn nhiệt."""
    temp = np.zeros((height, width))
    
    # Tạo gradient từ trên xuống dưới
    for y in range(height):
        for x in range(width):
            temp[y, x] = 20.0 + 10.0 * y / height
    
    # Thêm nguồn nhiệt hình tròn
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) // 4
    
    for y in range(height):
        for x in range(width):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            if dist < radius:
                temp[y, x] += 10.0 * (1.0 - dist / radius)
    
    return temp

# Hiển thị trường nhiệt độ
def plot_temperature(temp, title):
    """Vẽ trường nhiệt độ dưới dạng heatmap."""
    plt.figure(figsize=(10, 8))
    plt.imshow(temp, cmap='hot')
    plt.colorbar(label='Nhiệt độ (°C)')
    plt.title(title)
    plt.tight_layout()
    plt.show()

def main():
    """Hàm chính để kiểm thử."""
    width, height = 100, 100
    print(f"Tạo trường nhiệt độ {width}x{height}...")
    
    # Tạo trường nhiệt độ
    temp = create_temperature_field(width, height)
    
    # Hiển thị trường nhiệt độ ban đầu
    print("Trường nhiệt độ đã được tạo thành công.")
    
    try:
        # Thử import WeatherModelCpp
        print("Đang thử import WeatherModelCpp...")
        from model.weather.python.cpp_weather_interface import WeatherModelCpp
        
        print("Import thành công! Khởi tạo mô hình...")
        model = WeatherModelCpp(width, height)
        
        # Đặt dữ liệu nhiệt độ
        print("Đặt dữ liệu nhiệt độ...")
        success = model.set_temperature_data(temp)
        print(f"Đặt dữ liệu nhiệt độ: {'thành công' if success else 'thất bại'}")
        
        # Tạo trường gió
        print("Tạo trường gió Gaussian...")
        model.generate_wind_field("gaussian", num_vortices=3, strength=2.0, radius=15.0)
        
        # Lấy trường gió
        print("Lấy dữ liệu trường gió...")
        wind_x, wind_y = model.get_wind_field()
        print(f"Kích thước wind_x: {wind_x.shape}, wind_y: {wind_y.shape}")
        
        # Chạy 10 bước mô phỏng
        num_steps = 10
        print(f"Chạy {num_steps} bước mô phỏng...")
        start_time = time.time()
        
        for i in range(num_steps):
            dt = model.step_simulation()
            print(f"Bước {i+1}/{num_steps}, dt = {dt:.5f}")
        
        end_time = time.time()
        print(f"Mô phỏng hoàn thành trong {end_time - start_time:.2f} giây")
        
        # Lấy kết quả
        result_temp = model.get_temperature()
        print(f"Kích thước kết quả: {result_temp.shape}")
        
        # Vẽ kết quả nếu matplotlib có sẵn
        print("Vẽ kết quả...")
        plot_temperature(temp, "Nhiệt độ ban đầu")
        plot_temperature(result_temp, f"Nhiệt độ sau {num_steps} bước mô phỏng")
        
        print("Kiểm thử hoàn thành thành công!")
        
    except ImportError as e:
        print(f"Lỗi import: {e}")
        print("Có thể module C++ chưa được biên dịch. Chạy 'python -m model.weather.python.build_cpp_module'")
    except Exception as e:
        print(f"Lỗi khi thực thi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
