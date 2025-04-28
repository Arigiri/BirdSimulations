# Tài liệu tích hợp C++ với Python cho mô hình thời tiết

## 1. Tổng quan

Tài liệu này mô tả cách tích hợp code C++ vào mô hình thời tiết Python của dự án BirdSimulations để tối ưu hiệu suất tính toán. Chúng ta sẽ sử dụng C++ để triển khai các thuật toán tính toán nặng và tích hợp chúng với Python thông qua giao diện pybind11, đồng thời tận dụng multiprocessing của Python để song song hóa quá trình tính toán.

Lợi ích chính của phương pháp này:
- **Hiệu suất cao**: C++ cung cấp hiệu suất tính toán vượt trội cho các phép toán số học phức tạp
- **Tận dụng đa nhân**: Multiprocessing cho phép tận dụng đa nhân CPU mà không cần GPU
- **Tích hợp dễ dàng**: Giữ phần giao diện người dùng và điều khiển trong Python

## 2. Cấu trúc dự án

```
model/weather/
├── cpp/
│   ├── include/            # Header files
│   │   ├── solver.h         # Định nghĩa các phương pháp số
│   │   ├── wind_field.h     # Định nghĩa mô hình trường gió
│   │   └── temperature_field.h  # Định nghĩa mô hình trường nhiệt
│   ├── src/                # Source files
│   │   ├── solver.cpp       # Triển khai các thuật toán
│   │   ├── wind_field.cpp   # Triển khai mô hình gió
│   │   ├── temperature_field.cpp # Triển khai mô hình nhiệt
│   │   └── python_bindings.cpp # Bindings cho Python
│   ├── CMakeLists.txt      # Build script
│   └── build.sh            # Script để build module
├── python/
│   ├── weather_multiprocessing.py  # Module quản lý multiprocessing
│   └── cpp_weather_interface.py    # Interface với C++ module
└── doc_Cpp.md              # Tài liệu này
```

## 3. Các thành phần C++

### 3.1 Các file header

#### `include/solver.h`

```cpp
#pragma once
#include <vector>
#include <omp.h>  // OpenMP cho song song hóa trong một process

namespace weather {

class Solver {
public:
    // Constructor với kích thước grid và các tham số
    Solver(int width, int height, double dx, double kappa);

    // Tính toán gradient
    void computeGradients(const std::vector<double>& field, 
                         std::vector<double>& gradX, 
                         std::vector<double>& gradY);

    // Tính Laplacian
    void computeLaplacian(const std::vector<double>& field,
                         std::vector<double>& laplacian);

    // Phương pháp Runge-Kutta bậc 4 cho phương trình advection-diffusion
    void solveRK4Step(std::vector<double>& temperature,
                   const std::vector<double>& windX,
                   const std::vector<double>& windY,
                   double dt);

    // Tính time step dựa trên điều kiện CFL
    double computeCFLTimeStep(const std::vector<double>& windX,
                            const std::vector<double>& windY);

    // Xử lý subdomain (phân vùng) cho multiprocessing
    void solveSubdomain(std::vector<double>& temperature,
                     const std::vector<double>& windX,
                     const std::vector<double>& windY,
                     int startRow, int endRow, 
                     double dt);

private:
    int width_;
    int height_;
    double dx_;
    double kappa_;
    // Vectors trung gian để tránh phân bổ lại bộ nhớ
    std::vector<double> k1_, k2_, k3_, k4_, temp_;
};

} // namespace weather
```

#### `include/wind_field.h`

```cpp
#pragma once
#include <vector>
#include <random>

namespace weather {

class WindField {
public:
    WindField(int width, int height);

    // Tạo trường gió Gaussian
    void generateGaussianWind(double meanX, double meanY,
                            double stddevX, double stddevY);

    // Tạo trường gió Perlin
    void generatePerlinWind(double scale, double amplitude);

    // Tạo vortex (xoáy)
    void addVortex(int centerX, int centerY, double strength, double radius);

    // Getter cho dữ liệu trường gió
    const std::vector<double>& getWindX() const;
    const std::vector<double>& getWindY() const;

private:
    int width_;
    int height_;
    std::vector<double> windX_;
    std::vector<double> windY_;
    std::mt19937 rng_;
};

} // namespace weather
```

#### `include/temperature_field.h`

```cpp
#pragma once
#include <vector>

namespace weather {

class TemperatureField {
public:
    TemperatureField(int width, int height);

    // Khởi tạo trường nhiệt với giá trị đều
    void initializeUniform(double value);

    // Khởi tạo trường nhiệt ngẫu nhiên
    void initializeRandom(double minTemp, double maxTemp);

    // Khởi tạo mẫu nhiệt
    void initializePattern(const std::string& patternType);

    // Getter và setter
    std::vector<double>& getData();
    const std::vector<double>& getData() const;

    // Tính toán các thống kê
    double getMinTemperature() const;
    double getMaxTemperature() const;
    double getMeanTemperature() const;

private:
    int width_;
    int height_;
    std::vector<double> data_;
};

} // namespace weather
```

### 3.2 Triển khai Python bindings

#### `src/python_bindings.cpp`

```cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "solver.h"
#include "wind_field.h"
#include "temperature_field.h"

namespace py = pybind11;
using namespace weather;

// Helper để chuyển đổi numpy array sang std::vector
template <typename T>
std::vector<T> numpy_to_vector(py::array_t<T> array) {
    py::buffer_info buf = array.request();
    T* ptr = static_cast<T*>(buf.ptr);
    return std::vector<T>(ptr, ptr + buf.size);
}

// Helper để chuyển đổi std::vector sang numpy array
template <typename T>
py::array_t<T> vector_to_numpy(const std::vector<T>& vec, const std::vector<int>& shape) {
    return py::array_t<T>(shape, vec.data());
}

PYBIND11_MODULE(cpp_weather, m) {
    m.doc() = "C++ backend for the BirdSimulations weather model";

    // Expose Solver class
    py::class_<Solver>(m, "Solver")
        .def(py::init<int, int, double, double>())
        .def("compute_cfl_time_step", [](Solver& solver, py::array_t<double> windX, py::array_t<double> windY) {
            return solver.computeCFLTimeStep(numpy_to_vector(windX), numpy_to_vector(windY));
        })
        .def("solve_rk4_step", [](Solver& solver, py::array_t<double> temp, py::array_t<double> windX, 
                                py::array_t<double> windY, double dt) {
            auto temp_vec = numpy_to_vector(temp);
            solver.solveRK4Step(temp_vec, numpy_to_vector(windX), numpy_to_vector(windY), dt);
            
            // Trả về numpy array từ đầu ra C++
            py::buffer_info buf = temp.request();
            return vector_to_numpy(temp_vec, {buf.shape[0], buf.shape[1]});
        })
        .def("solve_subdomain", [](Solver& solver, py::array_t<double> temp, py::array_t<double> windX,
                                py::array_t<double> windY, int startRow, int endRow, double dt) {
            auto temp_vec = numpy_to_vector(temp);
            solver.solveSubdomain(temp_vec, numpy_to_vector(windX), numpy_to_vector(windY), 
                               startRow, endRow, dt);
            
            py::buffer_info buf = temp.request();
            return vector_to_numpy(temp_vec, {buf.shape[0], buf.shape[1]});
        });

    // Expose WindField class
    py::class_<WindField>(m, "WindField")
        .def(py::init<int, int>())
        .def("generate_gaussian_wind", &WindField::generateGaussianWind)
        .def("generate_perlin_wind", &WindField::generatePerlinWind)
        .def("add_vortex", &WindField::addVortex)
        .def("get_wind_x", [](const WindField& wf) {
            return vector_to_numpy(wf.getWindX(), {wf.getWidth(), wf.getHeight()});
        })
        .def("get_wind_y", [](const WindField& wf) {
            return vector_to_numpy(wf.getWindY(), {wf.getWidth(), wf.getHeight()});
        });

    // Expose TemperatureField class
    py::class_<TemperatureField>(m, "TemperatureField")
        .def(py::init<int, int>())
        .def("initialize_uniform", &TemperatureField::initializeUniform)
        .def("initialize_random", &TemperatureField::initializeRandom)
        .def("initialize_pattern", &TemperatureField::initializePattern)
        .def("get_data", [](const TemperatureField& tf) {
            return vector_to_numpy(tf.getData(), {tf.getWidth(), tf.getHeight()});
        })
        .def("get_min_temperature", &TemperatureField::getMinTemperature)
        .def("get_max_temperature", &TemperatureField::getMaxTemperature)
        .def("get_mean_temperature", &TemperatureField::getMeanTemperature);
}
```

## 4. Tích hợp Python-C++

### 4.1 Python interface cho C++ module

#### `python/cpp_weather_interface.py`

```python
import numpy as np

# Import C++ module sau khi build
try:
    import cpp_weather
except ImportError:
    raise ImportError("C++ module không được tìm thấy. Chạy 'cd cpp && ./build.sh' trước.")

class WeatherModelCpp:
    """Python wrapper cho các tính năng C++."""
    
    def __init__(self, width, height, dx=1.0, kappa=0.01):
        self.width = width
        self.height = height
        
        # Khởi tạo các đối tượng C++
        self.solver = cpp_weather.Solver(width, height, dx, kappa)
        self.wind_field = cpp_weather.WindField(width, height)
        self.temperature_field = cpp_weather.TemperatureField(width, height)
        
        # Khởi tạo trường nhiệt
        self.temperature_field.initialize_uniform(20.0)  # Nhiệt độ mặc định 20°C
        
        # Tạo trường gió Gaussian
        self.wind_field.generate_gaussian_wind(0.0, 0.0, 1.0, 1.0)
    
    def update_temperature(self, dt=None):
        """Cập nhật trường nhiệt sử dụng phương pháp RK4."""
        # Lấy dữ liệu gió và nhiệt độ
        temp = self.temperature_field.get_data()
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Tính time step tối ưu nếu không được cung cấp
        if dt is None:
            dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Cập nhật trường nhiệt
        new_temp = self.solver.solve_rk4_step(temp, wind_x, wind_y, dt)
        return new_temp
    
    def update_wind(self, wind_type="gaussian", **params):
        """Cập nhật trường gió với loại được chỉ định."""
        if wind_type == "gaussian":
            mean_x = params.get("mean_x", 0.0)
            mean_y = params.get("mean_y", 0.0)
            std_x = params.get("std_x", 1.0)
            std_y = params.get("std_y", 1.0)
            self.wind_field.generate_gaussian_wind(mean_x, mean_y, std_x, std_y)
        elif wind_type == "perlin":
            scale = params.get("scale", 0.1)
            amplitude = params.get("amplitude", 1.0)
            self.wind_field.generate_perlin_wind(scale, amplitude)
        elif wind_type == "vortex":
            center_x = params.get("center_x", self.width // 2)
            center_y = params.get("center_y", self.height // 2)
            strength = params.get("strength", 1.0)
            radius = params.get("radius", self.width // 4)
            
            # Reset trước khi thêm xoáy
            self.wind_field.generate_gaussian_wind(0.0, 0.0, 0.1, 0.1)
            self.wind_field.add_vortex(center_x, center_y, strength, radius)
        
        # Trả về dữ liệu gió
        return {
            "wind_x": self.wind_field.get_wind_x(),
            "wind_y": self.wind_field.get_wind_y()
        }
```

## 5. Multiprocessing

### 5.1 Multiprocessing manager cho tính toán song song

#### `python/weather_multiprocessing.py`

```python
import numpy as np
from multiprocessing import Pool, cpu_count
import cpp_weather_interface as cw

class WeatherMultiprocessingManager:
    """Quản lý tính toán song song cho mô hình thời tiết."""
    
    def __init__(self, width, height, dx=1.0, kappa=0.01, num_processes=None):
        self.width = width
        self.height = height
        self.dx = dx
        self.kappa = kappa
        
        # Xác định số process
        self.num_processes = num_processes or cpu_count()
        
        # Khởi tạo weather model trung tâm
        self.weather_model = cw.WeatherModelCpp(width, height, dx, kappa)
        
        # Tính toán rows per process
        self.rows_per_process = height // self.num_processes
        if self.rows_per_process < 2:
            # Cần ít nhất 2 hàng cho mỗi process để xử lý gradient
            self.num_processes = height // 2
            self.rows_per_process = height // self.num_processes
    
    def _process_subdomain(self, args):
        """Hàm worker để xử lý một subdomain."""
        proc_idx, start_row, end_row, temp, wind_x, wind_y, dt = args
        
        # Khởi tạo solver local cho mỗi process
        solver = cpp_weather.Solver(self.width, self.height, self.dx, self.kappa)
        
        # Xử lý subdomain
        result = solver.solve_subdomain(temp, wind_x, wind_y, start_row, end_row, dt)
        
        return proc_idx, start_row, end_row, result
    
    def update_parallel(self, dt=None):
        """Cập nhật trường nhiệt song song trên nhiều process."""
        # Lấy dữ liệu hiện tại
        temp = self.weather_model.temperature_field.get_data()
        wind_x = self.weather_model.wind_field.get_wind_x()
        wind_y = self.weather_model.wind_field.get_wind_y()
        
        # Tính time step tối ưu nếu không được cung cấp
        if dt is None:
            dt = self.weather_model.solver.compute_cfl_time_step(wind_x, wind_y)
        
        # Chuẩn bị các tham số cho mỗi subdomain
        tasks = []
        for i in range(self.num_processes):
            start_row = i * self.rows_per_process
            end_row = (i + 1) * self.rows_per_process
            
            # Điều chỉnh hàng cuối
            if i == self.num_processes - 1:
                end_row = self.height
            
            # Thêm overlap để tính gradient và laplacian chính xác
            proc_start = max(0, start_row - 1)
            proc_end = min(self.height, end_row + 1)
            
            # Tạo view nhỏ hơn của dữ liệu
            subdomain_temp = temp[proc_start:proc_end, :]
            
            tasks.append((i, proc_start, proc_end, subdomain_temp, wind_x, wind_y, dt))
        
        # Xử lý song song
        result_map = {}
        with Pool(processes=self.num_processes) as pool:
            results = pool.map(self._process_subdomain, tasks)
            
            # Thu thập kết quả
            for proc_idx, start_row, end_row, result in results:
                result_map[(start_row, end_row)] = result
        
        # Tái tạo trường nhiệt hoàn chỉnh
        new_temp = np.copy(temp)
        for (start_row, end_row), result in result_map.items():
            # Bỏ qua hàng overlap khi ghép lại
            actual_start = start_row
            if start_row > 0:
                actual_start += 1
                
            actual_end = end_row
            if end_row < self.height:
                actual_end -= 1
                
            # Cập nhật phần chính của subdomain, bỏ qua phần overlap
            overlap_offset = 0 if start_row == 0 else 1
            new_temp[actual_start:actual_end, :] = result[overlap_offset:overlap_offset + (actual_end - actual_start), :]
        
        return new_temp
```

## 6. Hướng dẫn cài đặt

### 6.1 Yêu cầu

- **C++17 compiler** (GCC 7+ hoặc MSVC 2019+)
- **Python 3.7+**
- **CMake 3.12+**
- **pybind11** (để tạo Python bindings)
- **OpenMP** (cho song song hóa trong-thread)

### 6.2 Cài đặt thư viện phụ thuộc

```bash
# Cài đặt pybind11
pip install pybind11

# Trên Ubuntu, cài đặt công cụ development
sudo apt-get install build-essential cmake

# Trên Windows với MSVC, cài đặt Visual Studio với C++ workload
# hoặc sử dụng MinGW-w64
```

### 6.3 Build C++ module

Tạo file `cpp/build.sh` (hoặc `build.bat` trên Windows):

```bash
#!/bin/bash

# Tạo build directory
mkdir -p build
cd build

# Chạy CMake
cmake ..

# Build
make -j4

# Copy module vào thư mục Python
cp cpp_weather*.so ../python/
```

CMake configuration (`cpp/CMakeLists.txt`):

```cmake
cmake_minimum_required(VERSION 3.12)
project(cpp_weather)

# Yêu cầu C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Bật OpenMP
find_package(OpenMP REQUIRED)
if(OpenMP_CXX_FOUND)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
endif()

# Tìm pybind11
find_package(pybind11 REQUIRED)

# Thêm include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Thêm source files
set(SOURCES
    src/solver.cpp
    src/wind_field.cpp
    src/temperature_field.cpp
    src/python_bindings.cpp
)

# Tạo Python module
pybind11_add_module(cpp_weather ${SOURCES})
```

## 7. Ví dụ tích hợp

### 7.1 Sử dụng C++ backend từ Python

```python
# main.py
from model.weather.python.weather_multiprocessing import WeatherMultiprocessingManager
import numpy as np
import time

# Khởi tạo weather manager
weather_manager = WeatherMultiprocessingManager(
    width=200,  # 200x200 grid
    height=200,
    dx=1.0,     # Khoảng cách grid
    kappa=0.01,  # Hệ số khuếch tán
    num_processes=4  # 4 processes
)

# Thiết lập wind field ban đầu
weather_manager.weather_model.update_wind(
    wind_type="vortex",
    center_x=100,
    center_y=100,
    strength=2.0,
    radius=50
)

# Thiết lập nhiệt độ ban đầu (source ngẫu nhiên)
temp_field = weather_manager.weather_model.temperature_field
temp_field.initialize_random(15.0, 25.0)  # 15-25°C

# Đo hiệu suất
start_time = time.time()

# Chạy mô phỏng
num_steps = 100
for step in range(num_steps):
    # Cập nhật song song
    new_temp = weather_manager.update_parallel()
    
    # In tiến trình
    if step % 10 == 0:
        min_temp = np.min(new_temp)
        max_temp = np.max(new_temp)
        mean_temp = np.mean(new_temp)
        print(f"Step {step}: Min={min_temp:.2f}°C, Max={max_temp:.2f}°C, Mean={mean_temp:.2f}°C")

end_time = time.time()
print(f"Completed {num_steps} steps in {end_time - start_time:.2f} seconds")
print(f"Average per step: {(end_time - start_time) / num_steps * 1000:.2f} ms")
```

### 7.2 Tích hợp với mô phỏng BirdSimulations

Trong `main.py` của BirdSimulations:

```python
# Import weather model
from model.weather.python.weather_multiprocessing import WeatherMultiprocessingManager

# Khởi tạo trong hàm main
def main():
    # Các khởi tạo khác...
    
    # Khởi tạo weather model với multiprocessing
    global weather_integration
    weather_integration = WeatherIntegration(
        cpp_backend=True,  # Sử dụng C++ backend
        num_processes=4    # 4 processes
    )
    
    # Trong hàm update
    def update(dt):
        # Cập nhật weather model với C++ backend
        if weather_integration:
            weather_integration.update_parallel(dt)
        
        # Áp dụng thông tin thời tiết vào các chim và trái cây
        # ...
```

Class `WeatherIntegration` sẽ quản lý tương tác giữa weather model và các thành phần khác của mô phỏng.
