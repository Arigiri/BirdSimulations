"""
Script đơn giản để kiểm tra cài đặt pybind11
"""

import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import pybind11
    print(f"pybind11 version: {pybind11.__version__}")
    print(f"pybind11 path: {pybind11.__file__}")
    print(f"pybind11 include dir: {pybind11.get_include()}")
    print(f"pybind11 cmake dir: {pybind11.get_cmake_dir()}")
    print("pybind11 is installed correctly!")
except ImportError as e:
    print(f"Error importing pybind11: {e}")
