#include <cmath>
#include <iostream>
// #include<cuda.h>
#include <chrono>
#include <omp.h>

class Timer {
private:
  // Type aliases to make accessing nested type easier
  using Clock = std::chrono::steady_clock;
  using Second = std::chrono::duration<double, std::ratio<1>>;

  std::chrono::time_point<Clock> m_beg{Clock::now()};

public:
  void reset() { m_beg = Clock::now(); }

  double elapsed() const {
    return std::chrono::duration_cast<Second>(Clock::now() - m_beg).count();
  }
};

double pi_cpu(size_t steps) {
  double sum = 0.0;
  for (int i = 0; i < steps; i++) {
    double x = (i + 0.5) / steps;
    sum += 4.0 / (1.0 + x * x);
  }
  return sum / steps;
}

double pi_omp(size_t steps) {
  double sum = 0.0;
#pragma omp parallel for reduction(+ : sum)
  for (int i = 0; i < steps; i++) {
    double x = (i + 0.5) / steps;
    sum += 4.0 / (1.0 + x * x);
  }
  return sum / steps;
}

int main() {
  size_t steps = 1000000;
  int iters = 10;

  Timer timer;
  double cpu_serial_time = 0.0;
  double cpu_parallel_time = 0.0;

  for (int i = 0; i < iters; i++) {
    timer.reset();
    double pi = pi_cpu(steps);
    cpu_serial_time += timer.elapsed();

    timer.reset();
    double omp_pi = pi_omp(steps);
    cpu_parallel_time += timer.elapsed();
  }

  double cpu_pi = pi_cpu(steps);
  double omp_pi = pi_omp(steps);

  std::cout << "CPU Serial Time: " << cpu_serial_time / iters << " seconds"
            << std::endl;
  std::cout << "CPU Parallel Time: " << cpu_parallel_time / iters << " seconds"
            << std::endl;
}