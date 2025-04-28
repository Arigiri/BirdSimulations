"""
Các hàm tiện ích cho module visualization nhiệt độ.
"""

import numpy as np
from .constants import DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP

def normalize_temperature(temperature, min_temp=DEFAULT_MIN_TEMP, max_temp=DEFAULT_MAX_TEMP):
    """
    Chuẩn hóa nhiệt độ thành giá trị từ 0 đến 1.
    
    Args:
        temperature (float): Giá trị nhiệt độ cần chuẩn hóa
        min_temp (float): Nhiệt độ tối thiểu trong dải
        max_temp (float): Nhiệt độ tối đa trong dải
        
    Returns:
        float: Giá trị chuẩn hóa từ 0-1
    """
    # Đảm bảo không chia cho 0
    if max_temp == min_temp:
        return 0.5
    
    # Chuẩn hóa và giới hạn trong khoảng [0, 1]
    normalized = (temperature - min_temp) / (max_temp - min_temp)
    return max(0.0, min(1.0, normalized))

def get_temperature_color(normalized_temp):
    """
    Chuyển đổi nhiệt độ đã chuẩn hóa thành màu RGB.
    Sử dụng gradient màu: lạnh (xanh-trắng) -> nóng (đỏ)
    
    Args:
        normalized_temp (float): Giá trị nhiệt độ đã chuẩn hóa (0-1)
        
    Returns:
        tuple: Màu RGB (r, g, b) với mỗi thành phần từ 0-255
    """
    r = int(255 * normalized_temp)       # Màu đỏ tăng dần theo nhiệt độ  
    g = int(255 * (1 - normalized_temp)) # Màu xanh giảm dần theo nhiệt độ
    b = int(255 * (1 - normalized_temp)) # Màu xanh giảm dần theo nhiệt độ
    
    return (r, g, b)

def calculate_sample_rate(detail_level):
    """
    Tính tỷ lệ lấy mẫu dựa trên mức độ chi tiết.
    
    Args:
        detail_level (int): Mức độ chi tiết, từ 1 (cao nhất) đến 5 (thấp nhất)
        
    Returns:
        int: Tỷ lệ lấy mẫu (số lượng ô grid được bỏ qua + 1)
    """
    # Đảm bảo detail_level hợp lệ
    detail_level = max(1, min(5, detail_level))
    
    # Ánh xạ mức độ chi tiết sang tỷ lệ lấy mẫu
    sample_rates = {
        1: 1,   # Chi tiết cao nhất: hiển thị mọi ô
        2: 2,   # Chi tiết cao: hiển thị 1 ô, bỏ qua 1 ô
        3: 4,   # Chi tiết trung bình: hiển thị 1 ô, bỏ qua 3 ô
        4: 8,   # Chi tiết thấp: hiển thị 1 ô, bỏ qua 7 ô
        5: 16   # Chi tiết thấp nhất: hiển thị 1 ô, bỏ qua 15 ô
    }
    
    return sample_rates[detail_level]

def print_safe(text_vn, text_en=None):
    """In thông báo an toàn với tiếng Việt, nếu lỗi UnicodeEncodeError thì in phiên bản tiếng Anh"""
    try:
        print(text_vn)
    except UnicodeEncodeError:
        if text_en:
            print(text_en)
        else:
            # Tạo phiên bản không dấu
            text = text_vn.replace("à", "a").replace("á", "a").replace("ả", "a")
            print(text)
