#include <iostream>
#include <vector>
#include <string>
#include "../include/solver.h"
#include "../include/solver_seq.h"

void run_parallel() {
    std::cout << "[Parallel] Running simulation with Solver (OpenMP)...\n";
    Solver solver(100, 100, 1.0, 0.1, true); // song song
    std::vector<double> temp(100*100, 20.0);
    std::vector<double> windX(100*100, 1.0);
    std::vector<double> windY(100*100, 0.0);
    solver.solveRK4Step(temp, windX, windY, 0.01);
    std::cout << "[Parallel] Done. Sample T[0] = " << temp[0] << std::endl;
}

void run_sequential() {
    std::cout << "[Sequential] Running simulation with SolverSeq (single-thread)...\n";
    SolverSeq solver(100, 100, 1.0, 0.1);
    std::vector<double> temp(100*100, 20.0);
    std::vector<double> windX(100*100, 1.0);
    std::vector<double> windY(100*100, 0.0);
    solver.solveRK4Step(temp, windX, windY, 0.01);
    std::cout << "[Sequential] Done. Sample T[0] = " << temp[0] << std::endl;
}

int main(int argc, char* argv[]) {
    std::string mode = "parallel";
    if (argc > 1) mode = argv[1];
    if (mode == "parallel") {
        run_parallel();
    } else if (mode == "seq" || mode == "sequential") {
        run_sequential();
    } else {
        std::cout << "Usage: " << argv[0] << " [parallel|seq]" << std::endl;
    }
    return 0;
}
