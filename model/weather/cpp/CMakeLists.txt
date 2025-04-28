cmake_minimum_required(VERSION 3.10)
project(cpp_weather)

# Chỉ định compiler rõ ràng cho MinGW
set(CMAKE_CXX_COMPILER g++)
set(CMAKE_C_COMPILER gcc)

# Tìm kiếm Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Tìm kiếm OpenMP
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
endif()

# Đặt C++11 là tiêu chuẩn tối thiểu
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Thêm thư mục include
include_directories(include)

# Thêm pybind11 (cần được cài đặt trước)
# Sử dụng một trong hai cách sau để tìm pybind11:

# Cách 1: Nếu pybind11 được cài đặt qua pip
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
find_package(pybind11 CONFIG REQUIRED)

# Cách 2: Nếu pybind11 là submodule
# add_subdirectory(pybind11)

# Định nghĩa module Python
pybind11_add_module(cpp_weather 
    src/solver.cpp
    src/wind_field.cpp
    src/temperature_field.cpp
    src/python_bindings.cpp
)

# Đặt đích output
set_target_properties(cpp_weather PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../python"
)

# Thêm các cờ biên dịch cụ thể cho MinGW - liên kết tĩnh hoàn toàn
if(MINGW)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -static -static-libgcc -static-libstdc++")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -static -s")
    target_link_libraries(cpp_weather PRIVATE -static-libgcc -static-libstdc++ -static)
endif()

# Thông tin biên dịch
message(STATUS "Python libraries: ${Python_LIBRARIES}")
message(STATUS "Python include dirs: ${Python_INCLUDE_DIRS}")
message(STATUS "pybind11 include dirs: ${pybind11_INCLUDE_DIRS}")

# Hướng dẫn sử dụng (dành cho MinGW):
# 1. Tạo thư mục build: mkdir build
# 2. Chuyển đến thư mục build: cd build
# 3. Chạy CMake với MinGW generator: cmake .. -G "MinGW Makefiles"
# 4. Build module: cmake --build .
# Module được tạo ra sẽ đặt tại ../python/
