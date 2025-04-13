import numpy as np

class Vector2D:
    """Lớp Vector2D hỗ trợ các phép toán vector cơ bản."""
    
    def __init__(self, x=0, y=0):
        """Khởi tạo vector với tọa độ (x, y)."""
        self.x = x
        self.y = y
    
    def __add__(self, other):
        """Phép cộng vector."""
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        """Phép trừ vector."""
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        """Phép nhân vector với số vô hướng."""
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar):
        """Phép chia vector cho số vô hướng."""
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def __repr__(self):
        return f"Vector2D({self.x}, {self.y})"
    
    def magnitude(self):
        """Tính độ lớn của vector."""
        return np.sqrt(self.x**2 + self.y**2)
    
    def normalize(self):
        """Chuẩn hóa vector (đưa về độ dài 1)."""
        mag = self.magnitude()
        if mag > 0:
            return self / mag
        return Vector2D(0, 0)
    
    def limit(self, max_val):
        """Giới hạn độ lớn của vector."""
        mag = self.magnitude()
        if mag > max_val:
            return self.normalize() * max_val
        return Vector2D(self.x, self.y)
    
    def distance_to(self, other):
        """Tính khoảng cách Euclidean từ vector này đến vector khác."""
        dx = other.x - self.x
        dy = other.y - self.y
        return np.sqrt(dx**2 + dy**2)
    
    def as_tuple(self):
        """Chuyển vector thành tuple."""
        return (self.x, self.y)
    
    def to_array(self):
        """Chuyển vector thành mảng NumPy."""
        return np.array([self.x, self.y])
    
    @staticmethod
    def from_array(array):
        """Tạo vector từ mảng NumPy."""
        return Vector2D(array[0], array[1])

    def heading(self):
        """Trả về góc của vector (radians)"""
        import math
        return math.atan2(self.y, self.x)


# Helper functions for numpy arrays
def vector_add(v1, v2):
    """Cộng hai vector dạng mảng NumPy."""
    return np.add(v1, v2)

def vector_sub(v1, v2):
    """Trừ hai vector dạng mảng NumPy."""
    return np.subtract(v1, v2)

def vector_magnitude(v):
    """Tính độ lớn vector."""
    return np.sqrt(np.sum(v**2))

def vector_normalize(v):
    """Chuẩn hóa vector."""
    mag = vector_magnitude(v)
    return v / mag if mag > 0 else np.zeros_like(v)

def vector_limit(v, max_val):
    """Giới hạn độ lớn vector."""
    mag = vector_magnitude(v)
    if mag > max_val:
        return vector_normalize(v) * max_val
    return v