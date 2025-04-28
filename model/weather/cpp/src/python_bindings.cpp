/**
 * @file python_bindings.cpp
 * @brief Tạo Python bindings cho các lớp C++ sử dụng pybind11.
 * 
 * HƯỚNG DẪN SỬ DỤNG:
 * - File này tạo một module Python "cpp_weather" có thể import từ Python
 * - Nó bọc các lớp C++ Solver, WindField, và TemperatureField cho Python
 * - Module này cần được build thành một file .pyd (Windows) hoặc .so (Linux/Mac)
 * - Sau khi build, import module từ Python: `import cpp_weather`
 */

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "../include/solver.h"
#include "../include/wind_field.h"
#include "../include/temperature_field.h"

namespace py = pybind11;

// Helper để chuyển đổi numpy array sang std::vector
template <typename T>
std::vector<T> numpy_to_vector(py::array_t<T> array) {
    py::buffer_info buf = array.request();
    T* ptr = static_cast<T*>(buf.ptr);
    return std::vector<T>(ptr, ptr + buf.size);
}

// Helper để chuyển đổi std::vector sang numpy array
template <typename T>
py::array_t<T> vector_to_numpy(const std::vector<T>& vec, const std::vector<ssize_t>& shape) {
    return py::array_t<T>(shape, vec.data());
}

PYBIND11_MODULE(cpp_weather, m) {
    m.doc() = "C++ backend for the BirdSimulations weather model";

    // Expose Solver class
    py::class_<Solver>(m, "Solver")
        .def(py::init<int, int, double, double, bool>(), py::arg("width"), py::arg("height"), py::arg("dx"), py::arg("kappa"), py::arg("parallel") = true)
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
        .def("generate_gaussian_field", &WindField::generateGaussianField)
        .def("generate_perlin_field", &WindField::generatePerlinField)
        .def("generate_vortex_field", &WindField::generateVortexField)
        .def("get_wind_x", [](const WindField& wf) {
            return vector_to_numpy(wf.getWindX(), {static_cast<ssize_t>(wf.getWindX().size())});
        })
        .def("get_wind_y", [](const WindField& wf) {
            return vector_to_numpy(wf.getWindY(), {static_cast<ssize_t>(wf.getWindY().size())});
        });

    // Expose TemperatureField class
    py::enum_<TemperatureField::GradientDirection>(m, "GradientDirection")
        .value("NORTH_SOUTH", TemperatureField::NORTH_SOUTH)
        .value("SOUTH_NORTH", TemperatureField::SOUTH_NORTH)
        .value("EAST_WEST", TemperatureField::EAST_WEST)
        .value("WEST_EAST", TemperatureField::WEST_EAST)
        .value("RADIAL_IN", TemperatureField::RADIAL_IN)
        .value("RADIAL_OUT", TemperatureField::RADIAL_OUT)
        .export_values();

    py::class_<TemperatureField>(m, "TemperatureField")
        .def(py::init<int, int>())
        .def("set_uniform", &TemperatureField::setUniform)
        .def("set_gradient", &TemperatureField::setGradient)
        .def("set_custom_gradient", &TemperatureField::setCustomGradient)
        .def("add_heat_source", &TemperatureField::addHeatSource)
        .def("get_temperature", [](const TemperatureField& tf) {
            const auto& temp = tf.getTemperature();
            return vector_to_numpy(temp, {static_cast<ssize_t>(tf.getHeight()), 
                                          static_cast<ssize_t>(tf.getWidth())});
        })
        .def("set_temperature", [](TemperatureField& tf, py::array_t<double> temp) {
            return tf.setTemperature(numpy_to_vector(temp));
        })
        .def("get_value_at", &TemperatureField::getValueAt)
        .def("get_width", &TemperatureField::getWidth)
        .def("get_height", &TemperatureField::getHeight);
}
