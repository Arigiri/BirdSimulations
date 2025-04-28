/**
 * @file solver.h
 * @brief Giải quyết phương trình đối lưu-khuếch tán cho mô hình thời tiết.
 * 
 * HƯỚNG DẪN SỬ DỤNG:
 * 1. Tạo đối tượng Solver với kích thước lưới và các tham số vật lý:
 *    Solver solver(width, height, dx, kappa);
 * 
 * 2. Sử dụng phương thức computeCFLTimeStep để tính bước thời gian ổn định:
 *    double dt = solver.computeCFLTimeStep(windX, windY);
 * 
 * 3. Sử dụng phương thức solveRK4Step để cập nhật trường nhiệt độ:
 *    solver.solveRK4Step(temperature, windX, windY, dt);
 * 
 * 4. Hoặc, để giải trong một phạm vi hàng nhất định (cho đa luồng):
 *    solver.solveSubdomain(temperature, windX, windY, startRow, endRow, dt);
 */

#ifndef SOLVER_H
#define SOLVER_H

#include <vector>
#include <algorithm>
#include <cmath>
#include <omp.h>

class Solver {
public:
    /**
     * @brief Khởi tạo solver với kích thước lưới và các tham số vật lý.
     * @param width Chiều rộng lưới
     * @param height Chiều cao lưới
     * @param dx Khoảng cách lưới
     * @param kappa Hệ số khuếch tán
     */
    Solver(int width, int height, double dx, double kappa);

    /**
     * @brief Tính toán bước thời gian ổn định dựa trên điều kiện CFL.
     * @param windX Thành phần X của trường gió
     * @param windY Thành phần Y của trường gió
     * @return Bước thời gian ổn định tối đa
     */
    double computeCFLTimeStep(const std::vector<double>& windX, const std::vector<double>& windY);

    /**
     * @brief Cập nhật trường nhiệt độ sử dụng phương pháp Runge-Kutta bậc 4.
     * @param temperature Trường nhiệt độ
     * @param windX Thành phần X của trường gió
     * @param windY Thành phần Y của trường gió
     * @param dt Bước thời gian
     */
    void solveRK4Step(std::vector<double>& temperature, 
                      const std::vector<double>& windX, 
                      const std::vector<double>& windY, 
                      double dt);

    /**
     * @brief Giải phương trình trong một phạm vi hàng cụ thể (cho đa luồng).
     * @param temperature Trường nhiệt độ
     * @param windX Thành phần X của trường gió
     * @param windY Thành phần Y của trường gió
     * @param startRow Hàng bắt đầu
     * @param endRow Hàng kết thúc
     * @param dt Bước thời gian
     */
    void solveSubdomain(std::vector<double>& temperature, 
                        const std::vector<double>& windX, 
                        const std::vector<double>& windY, 
                        int startRow, int endRow, double dt);

private:
    int width_;        // Chiều rộng lưới
    int height_;       // Chiều cao lưới
    double spacing_;   // Khoảng cách lưới
    double kappa_;     // Hệ số khuếch tán

    /**
     * @brief Tính toán các gradient không gian.
     * @param temperature Trường nhiệt độ
     * @param gradX Gradient theo X (output)
     * @param gradY Gradient theo Y (output)
     */
    void computeGradients(const std::vector<double>& temperature,
                          std::vector<double>& gradX,
                          std::vector<double>& gradY);

    /**
     * @brief Tính toán Laplacian.
     * @param temperature Trường nhiệt độ
     * @param laplacian Laplacian (output)
     */
    void computeLaplacian(const std::vector<double>& temperature,
                         std::vector<double>& laplacian);

    /**
     * @brief Đánh giá đạo hàm thời gian của phương trình đối lưu-khuếch tán.
     * @param temperature Trường nhiệt độ
     * @param windX Thành phần X của trường gió
     * @param windY Thành phần Y của trường gió
     * @param result Kết quả đánh giá (output)
     */
    void evaluateTimeDerivative(const std::vector<double>& temperature,
                               const std::vector<double>& windX,
                               const std::vector<double>& windY,
                               std::vector<double>& result);
};

#endif // SOLVER_H
