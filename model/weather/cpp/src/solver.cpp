/**
 * @file solver.cpp
 * @brief Triển khai các phương thức giải quyết phương trình đối lưu-khuếch tán.
 */

#include "../include/solver.h"
#include <iostream>

Solver::Solver(int width, int height, double dx, double kappa)
    : width_(width), height_(height), spacing_(dx), kappa_(kappa) {
    // Constructor không cần khởi tạo thêm
}

double Solver::computeCFLTimeStep(const std::vector<double>& windX, const std::vector<double>& windY) {
    // Tìm vận tốc lớn nhất trong trường gió
    double maxVelocity = 0.0;
    
    #pragma omp parallel for reduction(max:maxVelocity)
    for (size_t i = 0; i < windX.size(); ++i) {
        double velocity = std::sqrt(windX[i] * windX[i] + windY[i] * windY[i]);
        maxVelocity = std::max(maxVelocity, velocity);
    }
    
    // Tránh chia cho 0
    if (maxVelocity < 1e-10) {
        maxVelocity = 1e-10;
    }

    // Điều kiện CFL: dt <= dx / max_velocity
    // Thêm hệ số an toàn 0.8
    double dt_advection = 0.8 * spacing_ / maxVelocity;
    
    // Điều kiện ổn định cho phương trình khuếch tán: dt <= dx^2 / (2*kappa)
    double dt_diffusion = 0.8 * spacing_ * spacing_ / (2.0 * kappa_);
    
    // Trả về bước thời gian nhỏ hơn (giới hạn chặt chẽ hơn)
    return std::min(dt_advection, dt_diffusion);
}

void Solver::computeGradients(const std::vector<double>& temperature,
                           std::vector<double>& gradX,
                           std::vector<double>& gradY) {
    gradX.resize(width_ * height_, 0.0);
    gradY.resize(width_ * height_, 0.0);
    
    #pragma omp parallel for collapse(2)
    for (int y = 1; y < height_ - 1; ++y) {
        for (int x = 1; x < width_ - 1; ++x) {
            int idx = y * width_ + x;
            
            // Sử dụng sai phân trung tâm để ước lượng gradient không gian
            gradX[idx] = (temperature[idx + 1] - temperature[idx - 1]) / (2.0 * spacing_);
            gradY[idx] = (temperature[idx + width_] - temperature[idx - width_]) / (2.0 * spacing_);
        }
    }
    
    // Xử lý biên - dùng sai phân một phía
    #pragma omp parallel for
    for (int x = 0; x < width_; ++x) {
        // Biên dưới
        int idxBottom = 0 * width_ + x;
        gradY[idxBottom] = (temperature[idxBottom + width_] - temperature[idxBottom]) / spacing_;
        
        // Biên trên
        int idxTop = (height_ - 1) * width_ + x;
        gradY[idxTop] = (temperature[idxTop] - temperature[idxTop - width_]) / spacing_;
    }
    
    #pragma omp parallel for
    for (int y = 0; y < height_; ++y) {
        // Biên trái
        int idxLeft = y * width_ + 0;
        gradX[idxLeft] = (temperature[idxLeft + 1] - temperature[idxLeft]) / spacing_;
        
        // Biên phải
        int idxRight = y * width_ + (width_ - 1);
        gradX[idxRight] = (temperature[idxRight] - temperature[idxRight - 1]) / spacing_;
    }
}

void Solver::computeLaplacian(const std::vector<double>& temperature,
                           std::vector<double>& laplacian) {
    laplacian.resize(width_ * height_, 0.0);
    
    #pragma omp parallel for collapse(2)
    for (int y = 1; y < height_ - 1; ++y) {
        for (int x = 1; x < width_ - 1; ++x) {
            int idx = y * width_ + x;
            
            // Sử dụng xấp xỉ sai phân hữu hạn 5 điểm cho Laplacian
            laplacian[idx] = (
                temperature[idx - 1] + temperature[idx + 1] +
                temperature[idx - width_] + temperature[idx + width_] - 
                4.0 * temperature[idx]
            ) / (spacing_ * spacing_);
        }
    }
    
    // Xử lý biên - điều kiện Neumann (gradient = 0)
    #pragma omp parallel for
    for (int x = 1; x < width_ - 1; ++x) {
        // Biên dưới (y = 0)
        int idxBottom = 0 * width_ + x;
        laplacian[idxBottom] = 2.0 * (temperature[idxBottom + width_] - temperature[idxBottom]) / 
                              (spacing_ * spacing_);
        
        // Biên trên (y = height - 1)
        int idxTop = (height_ - 1) * width_ + x;
        laplacian[idxTop] = 2.0 * (temperature[idxTop - width_] - temperature[idxTop]) / 
                           (spacing_ * spacing_);
    }
    
    #pragma omp parallel for
    for (int y = 1; y < height_ - 1; ++y) {
        // Biên trái (x = 0)
        int idxLeft = y * width_ + 0;
        laplacian[idxLeft] = 2.0 * (temperature[idxLeft + 1] - temperature[idxLeft]) / 
                            (spacing_ * spacing_);
        
        // Biên phải (x = width - 1)
        int idxRight = y * width_ + (width_ - 1);
        laplacian[idxRight] = 2.0 * (temperature[idxRight - 1] - temperature[idxRight]) / 
                             (spacing_ * spacing_);
    }
    
    // Góc
    laplacian[0] = 0;
    laplacian[width_ - 1] = 0;
    laplacian[(height_ - 1) * width_] = 0;
    laplacian[height_ * width_ - 1] = 0;
}

void Solver::evaluateTimeDerivative(const std::vector<double>& temperature,
                                 const std::vector<double>& windX,
                                 const std::vector<double>& windY,
                                 std::vector<double>& result) {
    // Cấp phát bộ nhớ cho kết quả
    result.resize(width_ * height_, 0.0);
    
    // Tính toán gradient và Laplacian
    std::vector<double> gradX, gradY, laplacian;
    computeGradients(temperature, gradX, gradY);
    computeLaplacian(temperature, laplacian);
    
    // Tính toán đạo hàm thời gian: dT/dt = -u*dT/dx - v*dT/dy + kappa*∇²T
    #pragma omp parallel for collapse(2)
    for (int y = 0; y < height_; ++y) {
        for (int x = 0; x < width_; ++x) {
            int idx = y * width_ + x;
            
            // Đối lưu: -u*dT/dx - v*dT/dy
            double advection = -windX[idx] * gradX[idx] - windY[idx] * gradY[idx];
            
            // Khuếch tán: kappa*∇²T
            double diffusion = kappa_ * laplacian[idx];
            
            // Đạo hàm thời gian tổng hợp
            result[idx] = advection + diffusion;
        }
    }
}

void Solver::solveRK4Step(std::vector<double>& temperature, 
                       const std::vector<double>& windX, 
                       const std::vector<double>& windY, 
                       double dt) {
    size_t n = temperature.size();
    std::vector<double> k1(n), k2(n), k3(n), k4(n);
    std::vector<double> temp(n);
    
    // Bước 1: k1 = f(T_n)
    evaluateTimeDerivative(temperature, windX, windY, k1);
    
    // Bước 2: k2 = f(T_n + dt/2 * k1)
    #pragma omp parallel for
    for (size_t i = 0; i < n; ++i) {
        temp[i] = temperature[i] + dt * 0.5 * k1[i];
    }
    evaluateTimeDerivative(temp, windX, windY, k2);
    
    // Bước 3: k3 = f(T_n + dt/2 * k2)
    #pragma omp parallel for
    for (size_t i = 0; i < n; ++i) {
        temp[i] = temperature[i] + dt * 0.5 * k2[i];
    }
    evaluateTimeDerivative(temp, windX, windY, k3);
    
    // Bước 4: k4 = f(T_n + dt * k3)
    #pragma omp parallel for
    for (size_t i = 0; i < n; ++i) {
        temp[i] = temperature[i] + dt * k3[i];
    }
    evaluateTimeDerivative(temp, windX, windY, k4);
    
    // Cập nhật: T_{n+1} = T_n + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
    #pragma omp parallel for
    for (size_t i = 0; i < n; ++i) {
        temperature[i] += dt / 6.0 * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]);
    }
}

void Solver::solveSubdomain(std::vector<double>& temperature, 
                         const std::vector<double>& windX, 
                         const std::vector<double>& windY, 
                         int startRow, int endRow, double dt) {
    // Kiểm tra tham số đầu vào
    if (startRow < 0 || endRow >= height_ || startRow > endRow) {
        std::cerr << "Invalid subdomain range: [" << startRow << ", " << endRow << "]" << std::endl;
        return;
    }
    
    // Sao chép phần địa phương của vùng và thêm ghost cells
    int subHeight = endRow - startRow + 1;
    int subSize = subHeight * width_;
    std::vector<double> subTemp(subSize);
    
    // Sao chép dữ liệu từ vùng lớn
    for (int y = startRow; y <= endRow; ++y) {
        for (int x = 0; x < width_; ++x) {
            int srcIdx = y * width_ + x;
            int dstIdx = (y - startRow) * width_ + x;
            subTemp[dstIdx] = temperature[srcIdx];
        }
    }
    
    // Tạo các trường gió con
    std::vector<double> subWindX(subSize);
    std::vector<double> subWindY(subSize);
    
    for (int y = startRow; y <= endRow; ++y) {
        for (int x = 0; x < width_; ++x) {
            int srcIdx = y * width_ + x;
            int dstIdx = (y - startRow) * width_ + x;
            subWindX[dstIdx] = windX[srcIdx];
            subWindY[dstIdx] = windY[srcIdx];
        }
    }
    
    // Tạo solver con với kích thước phù hợp
    Solver subSolver(width_, subHeight, spacing_, kappa_);
    
    // Giải phương trình trên miền con
    subSolver.solveRK4Step(subTemp, subWindX, subWindY, dt);
    
    // Sao chép kết quả trở lại trường lớn
    for (int y = startRow; y <= endRow; ++y) {
        for (int x = 0; x < width_; ++x) {
            int dstIdx = y * width_ + x;
            int srcIdx = (y - startRow) * width_ + x;
            temperature[dstIdx] = subTemp[srcIdx];
        }
    }
}
