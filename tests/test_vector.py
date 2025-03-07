import pytest
import numpy as np
from utils.vector import Vector2D

class TestVector2D:
    def test_initialization(self):
        """Kiểm tra khởi tạo Vector2D"""
        v = Vector2D(3, 4)
        assert v.x == 3
        assert v.y == 4
        
        # Kiểm tra khởi tạo mặc định
        v_default = Vector2D()
        assert v_default.x == 0
        assert v_default.y == 0
    
    def test_addition(self):
        """Kiểm tra phép cộng vector"""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        result = v1 + v2
        assert result.x == 4
        assert result.y == 6
    
    def test_subtraction(self):
        """Kiểm tra phép trừ vector"""
        v1 = Vector2D(5, 7)
        v2 = Vector2D(2, 3)
        result = v1 - v2
        assert result.x == 3
        assert result.y == 4
    
    def test_multiplication_by_scalar(self):
        """Kiểm tra phép nhân với số vô hướng"""
        v = Vector2D(2, 3)
        result = v * 2
        assert result.x == 4
        assert result.y == 6
    
    def test_division_by_scalar(self):
        """Kiểm tra phép chia cho số vô hướng"""
        v = Vector2D(6, 9)
        result = v / 3
        assert result.x == 2
        assert result.y == 3
    
    def test_magnitude(self):
        """Kiểm tra độ lớn vector"""
        v = Vector2D(3, 4)
        assert v.magnitude() == 5.0
        
        v_zero = Vector2D(0, 0)
        assert v_zero.magnitude() == 0.0
    
    def test_normalize(self):
        """Kiểm tra chuẩn hóa vector"""
        v = Vector2D(3, 4)
        normalized = v.normalize()
        assert pytest.approx(normalized.x) == 0.6
        assert pytest.approx(normalized.y) == 0.8
        assert pytest.approx(normalized.magnitude()) == 1.0
        
        # Kiểm tra vector không
        v_zero = Vector2D(0, 0)
        zero_normalized = v_zero.normalize()
        assert zero_normalized.x == 0
        assert zero_normalized.y == 0
    
    def test_limit(self):
        """Kiểm tra giới hạn độ lớn vector"""
        v = Vector2D(3, 4)  # Độ lớn = 5
        limited = v.limit(2)
        assert pytest.approx(limited.magnitude()) == 2.0
        assert pytest.approx(limited.x) == 1.2
        assert pytest.approx(limited.y) == 1.6
        
        # Kiểm tra vector có độ lớn nhỏ hơn giới hạn
        v_small = Vector2D(1, 1)  # Độ lớn ~ 1.414
        limited_small = v_small.limit(2)
        assert pytest.approx(limited_small.x) == 1
        assert pytest.approx(limited_small.y) == 1
    
    def test_as_tuple(self):
        """Kiểm tra chuyển đổi sang tuple"""
        v = Vector2D(3, 4)
        t = v.as_tuple()
        assert t == (3, 4)
    
    def test_to_array(self):
        """Kiểm tra chuyển đổi sang numpy array"""
        v = Vector2D(3, 4)
        arr = v.to_array()
        assert isinstance(arr, np.ndarray)
        assert arr[0] == 3
        assert arr[1] == 4
    
    def test_from_array(self):
        """Kiểm tra tạo Vector2D từ numpy array"""
        arr = np.array([3, 4])
        v = Vector2D.from_array(arr)
        assert v.x == 3
        assert v.y == 4

# Kiểm tra các helper functions
def test_vector_helpers():
    """Kiểm tra các hàm helper cho numpy arrays"""
    from utils.vector import vector_add, vector_sub, vector_magnitude, vector_normalize, vector_limit
    
    v1 = np.array([1, 2])
    v2 = np.array([3, 4])
    
    # Test vector_add
    result_add = vector_add(v1, v2)
    assert np.array_equal(result_add, np.array([4, 6]))
    
    # Test vector_sub
    result_sub = vector_sub(v1, v2)
    assert np.array_equal(result_sub, np.array([-2, -2]))
    
    # Test vector_magnitude
    v3 = np.array([3, 4])
    assert vector_magnitude(v3) == 5.0
    
    # Test vector_normalize
    normalized = vector_normalize(v3)
    assert pytest.approx(normalized[0]) == 0.6
    assert pytest.approx(normalized[1]) == 0.8
    assert pytest.approx(vector_magnitude(normalized)) == 1.0
    
    # Test vector_limit
    v4 = np.array([3, 4])
    limited = vector_limit(v4, 2)
    assert pytest.approx(vector_magnitude(limited)) == 2.0