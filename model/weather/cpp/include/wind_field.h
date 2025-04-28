/**
 * @file wind_field.h
 * @brief Mô phỏng và tạo trường gió cho mô hình thời tiết.
 * 
 * HƯỚNG DẪN SỬ DỤNG:
 * 1. Tạo đối tượng WindField với kích thước lưới:
 *    WindField windField(width, height);
 * 
 * 2. Tạo trường gió với các phương pháp khác nhau:
 *    - Trường gió Gaussian:
 *      windField.generateGaussianField(numVortices, strength, radius);
 *    - Trường gió Perlin:
 *      windField.generatePerlinField(scale, octaves, persistence);
 *    - Trường gió xoáy:
 *      windField.generateVortexField(centers, strengths, radiuses);
 * 
 * 3. Lấy các thành phần của trường gió:
 *    const std::vector<double>& windX = windField.getWindX();
 *    const std::vector<double>& windY = windField.getWindY();
 */

#ifndef WIND_FIELD_H
#define WIND_FIELD_H

#include <vector>
#include <random>
#include <cmath>
#include <omp.h>

class WindField {
public:
    /**
     * @brief Khởi tạo trường gió với kích thước lưới.
     * @param width Chiều rộng lưới
     * @param height Chiều cao lưới
     */
    WindField(int width, int height);

    /**
     * @brief Tạo trường gió Gaussian.
     * @param numVortices Số lượng xoáy
     * @param strength Cường độ trung bình của xoáy
     * @param radius Bán kính trung bình của xoáy
     */
    void generateGaussianField(int numVortices, double strength, double radius);

    /**
     * @brief Tạo trường gió Perlin.
     * @param scale Kích thước scale của nhiễu Perlin
     * @param octaves Số lượng octaves
     * @param persistence Độ bền vững giữa các octave
     */
    void generatePerlinField(double scale, int octaves, double persistence);

    /**
     * @brief Tạo trường gió xoáy.
     * @param centers Vector chứa các tọa độ trung tâm xoáy (x1, y1, x2, y2, ...)
     * @param strengths Vector chứa cường độ của mỗi xoáy
     * @param radiuses Vector chứa bán kính của mỗi xoáy
     */
    void generateVortexField(const std::vector<double>& centers, 
                           const std::vector<double>& strengths, 
                           const std::vector<double>& radiuses);

    /**
     * @brief Lấy thành phần X của trường gió.
     * @return Vector thành phần X của trường gió
     */
    const std::vector<double>& getWindX() const { return windX_; }

    /**
     * @brief Lấy thành phần Y của trường gió.
     * @return Vector thành phần Y của trường gió
     */
    const std::vector<double>& getWindY() const { return windY_; }

private:
    int width_;          // Chiều rộng lưới
    int height_;         // Chiều cao lưới
    std::vector<double> windX_;  // Thành phần X của trường gió
    std::vector<double> windY_;  // Thành phần Y của trường gió
    std::mt19937 rng_;   // Bộ sinh số ngẫu nhiên

    /**
     * @brief Tạo nhiễu Perlin.
     * @param x Tọa độ x
     * @param y Tọa độ y
     * @param scale Kích thước scale
     * @return Giá trị nhiễu
     */
    double perlinNoise(double x, double y, double scale);

    /**
     * @brief Hàm nội suy tuyến tính.
     * @param a Giá trị 1
     * @param b Giá trị 2
     * @param t Tham số nội suy [0, 1]
     * @return Giá trị nội suy
     */
    double lerp(double a, double b, double t);

    /**
     * @brief Hàm làm mượt gradient.
     * @param t Giá trị đầu vào
     * @return Giá trị làm mượt
     */
    double smoothstep(double t);

    /**
     * @brief Tạo giá trị gradient ngẫu nhiên.
     * @param ix Chỉ số x
     * @param iy Chỉ số y
     * @return Giá trị gradient ngẫu nhiên
     */
    double randomGradient(int ix, int iy);
};

#endif // WIND_FIELD_H
