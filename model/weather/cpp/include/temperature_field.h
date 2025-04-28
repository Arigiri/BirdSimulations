/**
 * @file temperature_field.h
 * @brief Quản lý trường nhiệt độ cho mô hình thời tiết.
 * 
 * HƯỚNG DẪN SỬ DỤNG:
 * 1. Tạo đối tượng TemperatureField với kích thước lưới:
 *    TemperatureField tempField(width, height);
 * 
 * 2. Khởi tạo trường nhiệt độ với các phương pháp khác nhau:
 *    - Nhiệt độ đồng nhất:
 *      tempField.setUniform(temperature);
 *    - Gradient nhiệt độ:
 *      tempField.setGradient(minTemp, maxTemp, direction);
 *    - Nguồn nhiệt điểm:
 *      tempField.addHeatSource(x, y, strength, radius);
 * 
 * 3. Lấy dữ liệu trường nhiệt độ:
 *    const std::vector<double>& temp = tempField.getTemperature();
 */

#ifndef TEMPERATURE_FIELD_H
#define TEMPERATURE_FIELD_H

#include <vector>
#include <cmath>
#include <algorithm>
#include <string>

class TemperatureField {
public:
    /**
     * @brief Hướng gradient nhiệt độ có sẵn.
     */
    enum GradientDirection {
        NORTH_SOUTH,  // Bắc (lạnh) -> Nam (nóng)
        SOUTH_NORTH,  // Nam (lạnh) -> Bắc (nóng)
        EAST_WEST,    // Đông (lạnh) -> Tây (nóng)
        WEST_EAST,    // Tây (lạnh) -> Đông (nóng)
        RADIAL_IN,    // Trung tâm (lạnh) -> Biên (nóng)
        RADIAL_OUT    // Trung tâm (nóng) -> Biên (lạnh)
    };

    /**
     * @brief Khởi tạo trường nhiệt độ với kích thước lưới.
     * @param width Chiều rộng lưới
     * @param height Chiều cao lưới
     */
    TemperatureField(int width, int height);

    /**
     * @brief Thiết lập nhiệt độ đồng nhất trên toàn bộ lưới.
     * @param temperature Giá trị nhiệt độ
     */
    void setUniform(double temperature);

    /**
     * @brief Thiết lập gradient nhiệt độ.
     * @param minTemp Nhiệt độ tối thiểu
     * @param maxTemp Nhiệt độ tối đa
     * @param direction Hướng gradient
     */
    void setGradient(double minTemp, double maxTemp, GradientDirection direction);

    /**
     * @brief Thiết lập gradient nhiệt độ với hướng tùy chỉnh.
     * @param minTemp Nhiệt độ tối thiểu
     * @param maxTemp Nhiệt độ tối đa
     * @param angleInDegrees Góc (theo độ) của gradient, 0° = Đông, tăng ngược chiều kim đồng hồ
     */
    void setCustomGradient(double minTemp, double maxTemp, double angleInDegrees);

    /**
     * @brief Thêm nguồn nhiệt điểm.
     * @param x Tọa độ x của nguồn nhiệt
     * @param y Tọa độ y của nguồn nhiệt
     * @param strength Cường độ nguồn nhiệt
     * @param radius Bán kính ảnh hưởng
     */
    void addHeatSource(double x, double y, double strength, double radius);

    /**
     * @brief Lấy dữ liệu trường nhiệt độ.
     * @return Vector chứa dữ liệu nhiệt độ
     */
    const std::vector<double>& getTemperature() const { return temperature_; }

    /**
     * @brief Thiết lập dữ liệu trường nhiệt độ trực tiếp.
     * @param temperature Vector chứa dữ liệu nhiệt độ
     * @return true nếu kích thước vector phù hợp, ngược lại false
     */
    bool setTemperature(const std::vector<double>& temperature);

    /**
     * @brief Truy cập giá trị nhiệt độ tại một điểm cụ thể.
     * @param x Tọa độ x
     * @param y Tọa độ y
     * @return Giá trị nhiệt độ tại điểm (x,y)
     */
    double getValueAt(int x, int y) const;

    /**
     * @brief Lấy chiều rộng lưới.
     * @return Chiều rộng lưới
     */
    int getWidth() const { return width_; }

    /**
     * @brief Lấy chiều cao lưới.
     * @return Chiều cao lưới
     */
    int getHeight() const { return height_; }

private:
    int width_;                  // Chiều rộng lưới
    int height_;                 // Chiều cao lưới
    std::vector<double> temperature_;  // Dữ liệu nhiệt độ
};

#endif // TEMPERATURE_FIELD_H
