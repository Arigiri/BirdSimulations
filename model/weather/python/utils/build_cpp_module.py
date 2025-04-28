"""
Script biên dịch module C++ cho mô hình thời tiết

HƯỚNG DẪN SỬ DỤNG:
1. Đảm bảo đã cài đặt pybind11:
   `pip install pybind11`
2. Chạy script này từ thư mục gốc của project:
   `python -m model.weather.python.build_cpp_module`
3. Sau khi biên dịch thành công, bạn có thể sử dụng các lớp trong cpp_weather_interface.py
"""

import os
import sys
import subprocess
import shutil
import logging
import platform

# Cài đặt logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root():
    """Lấy đường dẫn thư mục gốc của project."""
    # Giả sử script này đặt trong model/weather/python/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def check_dependencies():
    """Kiểm tra các phụ thuộc cần thiết."""
    # Kiểm tra CMake
    try:
        subprocess.run(['cmake', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("CMake đã được cài đặt.")
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("CMake không được tìm thấy. Vui lòng cài đặt CMake.")
        return False

    # Kiểm tra trình biên dịch C++
    compiler_found = False
    if platform.system() == 'Windows':
        try:
            subprocess.run(['cl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("MSVC compiler đã được tìm thấy.")
            compiler_found = True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
        if not compiler_found:
            try:
                subprocess.run(['g++', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.info("GCC compiler đã được tìm thấy.")
                compiler_found = True
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
    else:
        try:
            subprocess.run(['g++', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("GCC compiler đã được tìm thấy.")
            compiler_found = True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
    if not compiler_found:
        logger.error("Không tìm thấy trình biên dịch C++. Cài đặt MSVC, GCC, hoặc Clang.")
        return False

    # Kiểm tra pybind11
    try:
        import pybind11
        logger.info(f"pybind11 đã được cài đặt, phiên bản {pybind11.__version__}")
    except ImportError:
        logger.error("pybind11 chưa được cài đặt. Chạy 'pip install pybind11'")
        return False

    return True

def build_module():
    """Biên dịch module C++ sử dụng CMake."""
    project_root = get_project_root()
    module_dir = os.path.join(project_root, 'model', 'weather')
    build_dir = os.path.join(module_dir, 'cpp', 'build')
    
    # Tạo thư mục build nếu chưa tồn tại
    os.makedirs(build_dir, exist_ok=True)
    
    # Chạy CMake để tạo build files
    logger.info("Đang tạo build files với CMake...")
    
    # Thay đổi thư mục làm việc
    os.chdir(build_dir)
    
    # Chạy CMake
    try:
        cmake_cmd = ['cmake', '..']
        subprocess.run(cmake_cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Lỗi khi chạy CMake: {e}")
        return False
    
    # Build module
    logger.info("Đang biên dịch module C++...")
    try:
        build_cmd = ['cmake', '--build', '.', '--config', 'Release']
        subprocess.run(build_cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Lỗi khi biên dịch module: {e}")
        return False
    
    logger.info("Module C++ đã được biên dịch thành công.")
    
    # Kiểm tra file đầu ra
    module_name = None
    if platform.system() == 'Windows':
        module_name = 'cpp_weather.pyd'
    else:
        module_name = 'cpp_weather.so'
    
    output_path = os.path.join(module_dir, 'python', module_name)
    if not os.path.exists(output_path):
        logger.warning(f"Không tìm thấy file kết quả tại {output_path}")
        # Tìm kiếm file đầu ra trong các thư mục
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file.startswith('cpp_weather') and (file.endswith('.so') or file.endswith('.pyd')):
                    found_path = os.path.join(root, file)
                    logger.info(f"Tìm thấy module tại {found_path}")
                    # Di chuyển sang thư mục đích
                    shutil.copy2(found_path, output_path)
                    logger.info(f"Đã sao chép module vào {output_path}")
                    return True
        
        logger.error("Không tìm thấy module đã biên dịch.")
        return False
    
    return True

def main():
    """Hàm chính để biên dịch module."""
    logger.info("Kiểm tra các phụ thuộc...")
    if not check_dependencies():
        logger.error("Kiểm tra phụ thuộc thất bại. Không thể tiếp tục.")
        return 1
    
    logger.info("Bắt đầu biên dịch module C++...")
    if not build_module():
        logger.error("Biên dịch module C++ thất bại.")
        return 1
    
    logger.info("Quá trình biên dịch đã hoàn tất thành công.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
