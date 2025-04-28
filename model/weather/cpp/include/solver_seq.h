#ifndef SOLVER_SEQ_H
#define SOLVER_SEQ_H
#include <vector>
#include <algorithm>
#include <cmath>
class SolverSeq {
public:
    SolverSeq(int width, int height, double dx, double kappa);
    double computeCFLTimeStep(const std::vector<double>& windX, const std::vector<double>& windY);
    void computeGradients(const std::vector<double>& temperature,
                         std::vector<double>& gradX,
                         std::vector<double>& gradY);
    void computeLaplacian(const std::vector<double>& temperature,
                         std::vector<double>& laplacian);
    void evaluateTimeDerivative(const std::vector<double>& temperature,
                               const std::vector<double>& windX,
                               const std::vector<double>& windY,
                               std::vector<double>& result);
    void solveRK4Step(std::vector<double>& temperature, 
                     const std::vector<double>& windX, 
                     const std::vector<double>& windY, 
                     double dt);
private:
    int width_;
    int height_;
    double spacing_;
    double kappa_;
};
#endif // SOLVER_SEQ_H
