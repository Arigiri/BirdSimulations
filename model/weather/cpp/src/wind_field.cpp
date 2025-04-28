/**
 * @file wind_field.cpp
 * @brief Triển khai các phương thức tạo và quản lý trường gió.
 */

#include "../include/wind_field.h"
#include <iostream>
#include <chrono>

WindField::WindField(int width, int height)
    : width_(width), height_(height) {
    // Khởi tạo mảng trường gió với kích thước phù hợp
    windX_.resize(width * height, 0.0);
    windY_.resize(width * height, 0.0);
    
    // Khởi tạo bộ sinh số ngẫu nhiên với seed từ thời gian
    unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
    rng_.seed(seed);
}

void WindField::generateGaussianField(int numVortices, double strength, double radius) {
    // Reset trường gió về 0
    std::fill(windX_.begin(), windX_.end(), 0.0);
    std::fill(windY_.begin(), windY_.end(), 0.0);
    
    // Phân phối ngẫu nhiên
    std::uniform_real_distribution<double> xDist(0, width_ - 1);
    std::uniform_real_distribution<double> yDist(0, height_ - 1);
    std::normal_distribution<double> strengthDist(strength, strength * 0.3);
    std::normal_distribution<double> radiusDist(radius, radius * 0.2);
    
    // Tạo các xoáy
    for (int i = 0; i < numVortices; ++i) {
        double centerX = xDist(rng_);
        double centerY = yDist(rng_);
        double vortexStrength = strengthDist(rng_);
        double vortexRadius = std::max(1.0, radiusDist(rng_));
        
        // Dấu của vortexStrength quyết định hướng xoáy (CW/CCW)
        if (std::uniform_real_distribution<double>(0, 1)(rng_) < 0.5) {
            vortexStrength = -vortexStrength;
        }
        
        // Áp dụng xoáy lên trường gió
        #pragma omp parallel for collapse(2)
        for (int y = 0; y < height_; ++y) {
            for (int x = 0; x < width_; ++x) {
                int idx = y * width_ + x;
                
                // Tính khoảng cách từ điểm tới tâm xoáy
                double dx = x - centerX;
                double dy = y - centerY;
                double distance = std::sqrt(dx * dx + dy * dy);
                
                // Sử dụng hàm mũ Gaussian để tính cường độ
                double factor = vortexStrength * std::exp(-distance * distance / (2 * vortexRadius * vortexRadius));
                
                // Góc 90 độ để tạo chuyển động xoáy
                windX_[idx] += factor * (-dy) / (distance + 1e-10);
                windY_[idx] += factor * dx / (distance + 1e-10);
            }
        }
    }
}

// Hàm nội suy tuyến tính
double WindField::lerp(double a, double b, double t) {
    return a + t * (b - a);
}

// Hàm làm mượt gradient
double WindField::smoothstep(double t) {
    return t * t * (3 - 2 * t);
}

// Tạo giá trị gradient ngẫu nhiên
double WindField::randomGradient(int ix, int iy) {
    // Sử dụng phương pháp hash ngẫu nhiên
    const unsigned w = 8 * sizeof(unsigned);
    const unsigned s = w / 2;
    unsigned a = ix, b = iy;
    a *= 3284157443; b ^= a << s | a >> (w-s);
    b *= 1911520717; a ^= b << s | b >> (w-s);
    a *= 2048419325;
    
    // Chuyển đổi sang góc
    float random = a * (3.14159265 / ~(~0u >> 1));
    return random;
}

// Tạo nhiễu Perlin
double WindField::perlinNoise(double x, double y, double scale) {
    // Scale đầu vào
    x /= scale;
    y /= scale;
    
    // Xác định ô lưới chứa điểm
    int x0 = (int)floor(x);
    int x1 = x0 + 1;
    int y0 = (int)floor(y);
    int y1 = y0 + 1;
    
    // Xác định vị trí tương đối trong ô
    double sx = x - (double)x0;
    double sy = y - (double)y0;
    
    // Làm mượt vị trí để giảm artifacts
    double u = smoothstep(sx);
    double v = smoothstep(sy);
    
    // Tính các gradient ngẫu nhiên
    double n0 = randomGradient(x0, y0);
    double n1 = randomGradient(x1, y0);
    double ix0 = lerp(n0, n1, u);
    
    n0 = randomGradient(x0, y1);
    n1 = randomGradient(x1, y1);
    double ix1 = lerp(n0, n1, u);
    
    // Nội suy theo y
    double value = lerp(ix0, ix1, v);
    
    // Chuẩn hóa sang [-1, 1]
    return value * 2.0 - 1.0;
}

void WindField::generatePerlinField(double scale, int octaves, double persistence) {
    #pragma omp parallel for collapse(2)
    for (int y = 0; y < height_; ++y) {
        for (int x = 0; x < width_; ++x) {
            int idx = y * width_ + x;
            
            double amplitude = 1.0;
            double frequency = 1.0;
            double windX = 0.0;
            double windY = 0.0;
            double totalAmplitude = 0.0;
            
            // Kết hợp nhiều octave để tạo chi tiết
            for (int o = 0; o < octaves; ++o) {
                // Offset để các octave không trùng nhau
                double offsetX = o * 4.0;
                double offsetY = o * 4.0;
                
                // Tạo hai nhiễu Perlin khác nhau cho X và Y
                double perlinX = perlinNoise((x + offsetX) / frequency, (y + offsetY) / frequency, scale);
                double perlinY = perlinNoise((x + offsetY + 31.41) / frequency, (y + offsetX + 27.18) / frequency, scale);
                
                windX += perlinX * amplitude;
                windY += perlinY * amplitude;
                
                totalAmplitude += amplitude;
                amplitude *= persistence;
                frequency *= 2.0;
            }
            
            // Chuẩn hóa
            windX_[idx] = windX / totalAmplitude;
            windY_[idx] = windY / totalAmplitude;
        }
    }
}

void WindField::generateVortexField(const std::vector<double>& centers, 
                                 const std::vector<double>& strengths, 
                                 const std::vector<double>& radiuses) {
    // Kiểm tra số lượng tham số đầu vào
    size_t numVortices = strengths.size();
    if (centers.size() != numVortices * 2 || radiuses.size() != numVortices) {
        std::cerr << "Mismatch in array sizes for vortex field generation" << std::endl;
        return;
    }
    
    // Reset trường gió về 0
    std::fill(windX_.begin(), windX_.end(), 0.0);
    std::fill(windY_.begin(), windY_.end(), 0.0);
    
    // Áp dụng từng xoáy
    for (size_t i = 0; i < numVortices; ++i) {
        double centerX = centers[i * 2];
        double centerY = centers[i * 2 + 1];
        double vortexStrength = strengths[i];
        double vortexRadius = radiuses[i];
        
        // Áp dụng xoáy lên trường gió
        #pragma omp parallel for collapse(2)
        for (int y = 0; y < height_; ++y) {
            for (int x = 0; x < width_; ++x) {
                int idx = y * width_ + x;
                
                // Tính khoảng cách từ điểm tới tâm xoáy
                double dx = x - centerX;
                double dy = y - centerY;
                double distance = std::sqrt(dx * dx + dy * dy);
                
                // Sử dụng profile xoáy hình chuông
                double profile;
                if (distance < vortexRadius) {
                    profile = distance / vortexRadius; // Tăng tuyến tính tới bán kính
                } else {
                    profile = vortexRadius / distance; // Giảm đi khi ra xa
                }
                
                double factor = vortexStrength * profile;
                
                // Góc 90 độ để tạo chuyển động xoáy
                windX_[idx] += factor * (-dy) / (distance + 1e-10);
                windY_[idx] += factor * dx / (distance + 1e-10);
            }
        }
    }
}
