/**
 * @file temperature_field.cpp
 * @brief Triển khai các phương thức quản lý trường nhiệt độ.
 */

#include "../include/temperature_field.h"
#include <iostream>
#include <stdexcept>

TemperatureField::TemperatureField(int width, int height)
    : width_(width), height_(height) {
    // Khởi tạo trường nhiệt độ với kích thước phù hợp
    temperature_.resize(width * height, 0.0);
}

void TemperatureField::setUniform(double temperature) {
    #pragma omp parallel for
    for (size_t i = 0; i < temperature_.size(); ++i) {
        temperature_[i] = temperature;
    }
}

void TemperatureField::setGradient(double minTemp, double maxTemp, GradientDirection direction) {
    #pragma omp parallel for collapse(2)
    for (int y = 0; y < height_; ++y) {
        for (int x = 0; x < width_; ++x) {
            int idx = y * width_ + x;
            double normalizedPosition;
            
            switch (direction) {
                case NORTH_SOUTH: // Bắc (lạnh) -> Nam (nóng)
                    normalizedPosition = static_cast<double>(y) / (height_ - 1);
                    break;
                    
                case SOUTH_NORTH: // Nam (lạnh) -> Bắc (nóng)
                    normalizedPosition = 1.0 - static_cast<double>(y) / (height_ - 1);
                    break;
                    
                case EAST_WEST: // Đông (lạnh) -> Tây (nóng)
                    normalizedPosition = 1.0 - static_cast<double>(x) / (width_ - 1);
                    break;
                    
                case WEST_EAST: // Tây (lạnh) -> Đông (nóng)
                    normalizedPosition = static_cast<double>(x) / (width_ - 1);
                    break;
                    
                case RADIAL_IN: { // Trung tâm (lạnh) -> Biên (nóng)
                    double centerX = width_ / 2.0;
                    double centerY = height_ / 2.0;
                    double dx = x - centerX;
                    double dy = y - centerY;
                    double distance = std::sqrt(dx * dx + dy * dy);
                    double maxDistance = std::sqrt(centerX * centerX + centerY * centerY);
                    normalizedPosition = distance / maxDistance;
                    break;
                }
                    
                case RADIAL_OUT: { // Trung tâm (nóng) -> Biên (lạnh)
                    double centerX = width_ / 2.0;
                    double centerY = height_ / 2.0;
                    double dx = x - centerX;
                    double dy = y - centerY;
                    double distance = std::sqrt(dx * dx + dy * dy);
                    double maxDistance = std::sqrt(centerX * centerX + centerY * centerY);
                    normalizedPosition = 1.0 - distance / maxDistance;
                    break;
                }
                    
                default:
                    normalizedPosition = 0.5;
                    break;
            }
            
            // Nội suy tuyến tính giữa nhiệt độ min và max
            temperature_[idx] = minTemp + normalizedPosition * (maxTemp - minTemp);
        }
    }
}

void TemperatureField::setCustomGradient(double minTemp, double maxTemp, double angleInDegrees) {
    // Chuyển đổi góc từ độ sang radian
    double angleInRadians = angleInDegrees * M_PI / 180.0;
    
    // Tính vector định hướng
    double dirX = std::cos(angleInRadians);
    double dirY = std::sin(angleInRadians);
    
    // Tính điểm góc của lưới (để xác định range)
    double corners[4][2] = {
        {0, 0},                  // Góc trái-dưới
        {width_ - 1, 0},         // Góc phải-dưới
        {0, height_ - 1},        // Góc trái-trên
        {width_ - 1, height_ - 1} // Góc phải-trên
    };
    
    // Tìm giá trị chiếu nhỏ nhất và lớn nhất
    double minProj = std::numeric_limits<double>::max();
    double maxProj = std::numeric_limits<double>::lowest();
    
    for (int i = 0; i < 4; ++i) {
        double proj = corners[i][0] * dirX + corners[i][1] * dirY;
        minProj = std::min(minProj, proj);
        maxProj = std::max(maxProj, proj);
    }
    
    double projRange = maxProj - minProj;
    
    #pragma omp parallel for collapse(2)
    for (int y = 0; y < height_; ++y) {
        for (int x = 0; x < width_; ++x) {
            int idx = y * width_ + x;
            
            // Chiếu điểm lên vector định hướng
            double proj = x * dirX + y * dirY;
            
            // Chuẩn hóa phép chiếu
            double normalizedPosition = (proj - minProj) / projRange;
            
            // Nội suy tuyến tính nhiệt độ
            temperature_[idx] = minTemp + normalizedPosition * (maxTemp - minTemp);
        }
    }
}

void TemperatureField::addHeatSource(double x, double y, double strength, double radius) {
    #pragma omp parallel for collapse(2)
    for (int py = 0; py < height_; ++py) {
        for (int px = 0; px < width_; ++px) {
            int idx = py * width_ + px;
            
            // Tính khoảng cách từ điểm tới nguồn nhiệt
            double dx = px - x;
            double dy = py - y;
            double distance = std::sqrt(dx * dx + dy * dy);
            
            // Áp dụng nguồn nhiệt theo phân phối Gaussian
            if (distance <= radius * 3.0) { // Cắt ở khoảng 3 lần bán kính để tiết kiệm tính toán
                double factor = strength * std::exp(-(distance * distance) / (2.0 * radius * radius));
                temperature_[idx] += factor;
            }
        }
    }
}

bool TemperatureField::setTemperature(const std::vector<double>& temperature) {
    if (temperature.size() != width_ * height_) {
        return false;
    }
    
    temperature_ = temperature;
    return true;
}

double TemperatureField::getValueAt(int x, int y) const {
    // Kiểm tra tọa độ có hợp lệ
    if (x < 0 || x >= width_ || y < 0 || y >= height_) {
        throw std::out_of_range("TemperatureField::getValueAt - Tọa độ ngoài phạm vi");
    }
    
    return temperature_[y * width_ + x];
}
