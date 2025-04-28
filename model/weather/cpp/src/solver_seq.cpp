#include "../include/solver_seq.h"
#include <iostream>

SolverSeq::SolverSeq(int width, int height, double dx, double kappa)
    : width_(width), height_(height), spacing_(dx), kappa_(kappa) {}

double SolverSeq::computeCFLTimeStep(const std::vector<double>& windX, const std::vector<double>& windY) {
    double maxVelocity = 0.0;
    for (size_t i = 0; i < windX.size(); ++i) {
        double velocity = std::sqrt(windX[i] * windX[i] + windY[i] * windY[i]);
        maxVelocity = std::max(maxVelocity, velocity);
    }
    if (maxVelocity < 1e-10) maxVelocity = 1e-10;
    double dt_advection = 0.8 * spacing_ / maxVelocity;
    double dt_diffusion = 0.8 * spacing_ * spacing_ / (2.0 * kappa_);
    return std::min(dt_advection, dt_diffusion);
}

void SolverSeq::computeGradients(const std::vector<double>& temperature,
                           std::vector<double>& gradX,
                           std::vector<double>& gradY) {
    gradX.resize(width_ * height_, 0.0);
    gradY.resize(width_ * height_, 0.0);
    for (int y = 0; y < height_; ++y) {
        for (int x = 0; x < width_; ++x) {
            int idx = y * width_ + x;
            int xp1 = (x + 1) % width_;
            int xm1 = (x - 1 + width_) % width_;
            int yp1 = (y + 1) % height_;
            int ym1 = (y - 1 + height_) % height_;
            gradX[idx] = (temperature[y * width_ + xp1] - temperature[y * width_ + xm1]) / (2.0 * spacing_);
            gradY[idx] = (temperature[yp1 * width_ + x] - temperature[ym1 * width_ + x]) / (2.0 * spacing_);
        }
    }
}

void SolverSeq::computeLaplacian(const std::vector<double>& temperature,
                           std::vector<double>& laplacian) {
    laplacian.resize(width_ * height_, 0.0);
    for (int y = 0; y < height_; ++y) {
        for (int x = 0; x < width_; ++x) {
            int idx = y * width_ + x;
            int xp1 = (x + 1) % width_;
            int xm1 = (x - 1 + width_) % width_;
            int yp1 = (y + 1) % height_;
            int ym1 = (y - 1 + height_) % height_;
            laplacian[idx] = (
                temperature[y * width_ + xp1] +
                temperature[y * width_ + xm1] +
                temperature[yp1 * width_ + x] +
                temperature[ym1 * width_ + x] -
                4.0 * temperature[idx]
            ) / (spacing_ * spacing_);
        }
    }
}

void SolverSeq::evaluateTimeDerivative(const std::vector<double>& temperature,
                                 const std::vector<double>& windX,
                                 const std::vector<double>& windY,
                                 std::vector<double>& result) {
    result.resize(width_ * height_, 0.0);
    std::vector<double> gradX, gradY, laplacian;
    computeGradients(temperature, gradX, gradY);
    computeLaplacian(temperature, laplacian);
    for (int y = 0; y < height_; ++y) {
        for (int x = 0; x < width_; ++x) {
            int idx = y * width_ + x;
            double advection = -windX[idx] * gradX[idx] - windY[idx] * gradY[idx];
            double diffusion = kappa_ * laplacian[idx];
            result[idx] = advection + diffusion;
        }
    }
}

void SolverSeq::solveRK4Step(std::vector<double>& temperature, 
                       const std::vector<double>& windX, 
                       const std::vector<double>& windY, 
                       double dt) {
    size_t n = temperature.size();
    std::vector<double> k1(n), k2(n), k3(n), k4(n);
    std::vector<double> temp(n);
    evaluateTimeDerivative(temperature, windX, windY, k1);
    for (size_t i = 0; i < n; ++i) temp[i] = temperature[i] + dt * 0.5 * k1[i];
    evaluateTimeDerivative(temp, windX, windY, k2);
    for (size_t i = 0; i < n; ++i) temp[i] = temperature[i] + dt * 0.5 * k2[i];
    evaluateTimeDerivative(temp, windX, windY, k3);
    for (size_t i = 0; i < n; ++i) temp[i] = temperature[i] + dt * k3[i];
    evaluateTimeDerivative(temp, windX, windY, k4);
    for (size_t i = 0; i < n; ++i) temperature[i] += dt / 6.0 * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]);
}
