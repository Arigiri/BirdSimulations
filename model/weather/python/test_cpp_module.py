"""
Test script to verify that the C++ weather module can be imported and used properly.
"""

import os
import sys
import time

# Add the python directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    print("Kiểm tra import module C++ cpp_weather")
    
    try:
        import cpp_weather
        print("✓ Đã import thành công module cpp_weather")
        
        # Check which classes and functions are available
        print("\nModule cpp_weather có các thuộc tính sau:")
        module_attrs = [attr for attr in dir(cpp_weather) if not attr.startswith('__')]
        for attr in module_attrs:
            print(f"- {attr}")
        
        # Try to create instances of the basic classes
        print("\nThử tạo các instance của class:")
        
        try:
            # Parameters
            width = 100
            height = 100
            dx = 1.0
            kappa = 0.05
            
            # Create instances
            print(f"Tạo Solver({width}, {height}, {dx}, {kappa})")
            solver = cpp_weather.Solver(width, height, dx, kappa)
            print("✓ Đã tạo instance của Solver")
            
            print(f"Tạo TemperatureField({width}, {height})")
            temp_field = cpp_weather.TemperatureField(width, height)
            print("✓ Đã tạo instance của TemperatureField")
            
            print(f"Tạo WindField({width}, {height})")
            wind_field = cpp_weather.WindField(width, height)
            print("✓ Đã tạo instance của WindField")
            
            # Check if GradientDirection enum exists
            print("\nKiểm tra enum GradientDirection:")
            if hasattr(cpp_weather, 'GradientDirection'):
                print("✓ Enum GradientDirection tồn tại")
                directions = [dir for dir in dir(cpp_weather.GradientDirection) 
                              if not dir.startswith('__')]
                print(f"Các giá trị: {directions}")
            else:
                print("✗ Enum GradientDirection không tồn tại")
            
            # Initialize temperature field with a pattern
            print("\nKhởi tạo trường nhiệt độ với mẫu:")
            temp_field.set_uniform(20.0)  # Set background to 20°C
            print("✓ Đã đặt uniform temperature")
            
            # Add a heat source
            center_x, center_y = width // 2, height // 2
            temp_field.add_heat_source(center_x, center_y, 30.0, width // 10)
            print(f"✓ Đã thêm nguồn nhiệt tại ({center_x}, {center_y})")
            
            # Initialize wind field
            print("\nKhởi tạo trường gió:")
            wind_field.generate_gaussian_field(5, 2.0, width // 8)
            print("✓ Đã tạo trường gió Gaussian")
            
            # Run a simulation step
            print("\nChạy một bước mô phỏng:")
            # Get current data
            temp = temp_field.get_temperature()
            wind_x = wind_field.get_wind_x()
            wind_y = wind_field.get_wind_y()
            print(f"✓ Đã lấy dữ liệu: temp.shape={temp.shape}, wind_x.shape={wind_x.shape}")
            
            # Compute time step
            dt = solver.compute_cfl_time_step(wind_x, wind_y)
            print(f"✓ Đã tính dt theo CFL: {dt:.4f}s")
            
            # Update temperature
            print("Đang cập nhật nhiệt độ...")
            start_time = time.time()
            new_temp = solver.solve_rk4_step(temp, wind_x, wind_y, dt)
            end_time = time.time()
            print(f"✓ Đã cập nhật nhiệt độ trong {end_time - start_time:.4f}s")
            
            # Update temperature field
            temp_field.set_temperature(new_temp)
            print("✓ Đã cập nhật trường nhiệt độ")
            
            # Get statistics
            min_temp = temp_field.get_min_temp()
            max_temp = temp_field.get_max_temp()
            mean_temp = temp_field.get_mean_temp()
            print(f"✓ Thống kê: min={min_temp:.2f}, max={max_temp:.2f}, mean={mean_temp:.2f}")
            
            print("\n=== KIỂM TRA THÀNH CÔNG ===")
            
        except TypeError as e:
            print(f"✗ Lỗi Type Error: {e}")
            print("Có thể do tham số không hợp lệ hoặc thiếu tham số khi tạo đối tượng")
            
        except AttributeError as e:
            print(f"✗ Lỗi Attribute Error: {e}")
            print("Có thể do tên phương thức không đúng hoặc không tồn tại")
            
        except Exception as e:
            print(f"✗ Lỗi khi sử dụng module: {e}")
            print(f"Loại lỗi: {type(e).__name__}")
            
    except ImportError as e:
        print(f"✗ Không thể import module cpp_weather: {e}")
        print("Kiểm tra xem module đã được biên dịch chưa và có đúng phiên bản Python không")
    
    except Exception as e:
        print(f"✗ Lỗi không xác định: {e}")
        print(f"Loại lỗi: {type(e).__name__}")
        
if __name__ == "__main__":
    main()