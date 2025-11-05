#include <iostream>
#include <chrono>

static const int N = 4096;
static double A[N][N];            // global to avoid stack issues
static volatile double sink_var;  // prevents optimization

double row_major() {
    double sum = 0.0;
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            sum += A[i][j];
    sink_var = sum; // prevent removal
    return sum;
}

double col_major() {
    double sum = 0.0;
    for (int j = 0; j < N; ++j)
        for (int i = 0; i < N; ++i)
            sum += A[i][j];
    sink_var = sum; // prevent removal
    return sum;
}

double timeit(double (*fn)(), int iters) {
    using clock = std::chrono::high_resolution_clock;
    double total_ms = 0.0;

    for (int t = 0; t < iters; ++t) {
        clock::time_point start = clock::now();
        (void)fn(); // run function
        clock::time_point end = clock::now();
        std::chrono::duration<double, std::milli> ms = end - start;
        total_ms += ms.count();
    }

    return total_ms / iters; // average runtime
}

int main() {
    #ifdef __clang__
        std::cout << "Compiler: Clang/LLVM\n";
    #elif defined(__GNUC__)
        std::cout << "Compiler: GCC\n";
    #else
        std::cout << "Compiler: Unknown\n";
    #endif

    #if defined(__OPTIMIZE__) && !defined(__OPTIMIZE_SIZE__)
        std::cout << "Optimization: -O2 or higher (likely -O3 or -Ofast)\n";
    #elif defined(__OPTIMIZE_SIZE__)
        std::cout << "Optimization: -Os (optimize for size)\n";
    #else
        std::cout << "Optimization: -O0 (no optimization)\n";
    #endif


	// Initialize data
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            A[i][j] = i + j;

    int iters = 5;

    double t_row = timeit(&row_major, iters);
    double t_col = timeit(&col_major, iters);

    std::cout << "Matrix size: " << N << " x " << N << "\n";
    std::cout << "Row-major: " << t_row << " ms (avg over " << iters << " runs)\n";
    std::cout << "Col-major: " << t_col << " ms (avg over " << iters << " runs)\n";

    return 0;
}

