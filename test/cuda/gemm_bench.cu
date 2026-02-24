#include <gemm.cuh>
#include <iostream>
#include <iomanip>
#include <cmath>
#include <string>

// ---------------------------------------------------------------------------
// CUDA event timer — measures pure GPU execution time (excludes H2D/D2H)
// ---------------------------------------------------------------------------
struct GpuTimer {
    cudaEvent_t start, stop;
    GpuTimer()  { cudaEventCreate(&start); cudaEventCreate(&stop); }
    ~GpuTimer() { cudaEventDestroy(start); cudaEventDestroy(stop); }
    void begin() { cudaEventRecord(start); }
    float end()  { cudaEventRecord(stop); cudaEventSynchronize(stop);
                   float ms; cudaEventElapsedTime(&ms, start, stop); return ms; }
};

// ---------------------------------------------------------------------------
// Verify correctness (A=1, B=1  =>  every C[i][j] == K)
// ---------------------------------------------------------------------------
template <typename T>
static bool verify(const thrust::host_vector<T>& hC, int K)
{
    const T expected = static_cast<T>(K);
    for (std::size_t i = 0; i < hC.size(); ++i) {
        if (std::abs(hC[i] - expected) > static_cast<T>(1e-3)) {
            std::cerr << "  FAIL at " << i << ": got " << hC[i]
                      << " expected " << expected << '\n';
            return false;
        }
    }
    return true;
}

// ---------------------------------------------------------------------------
// Benchmark helpers — returns average kernel time in ms over `iters` runs
// ---------------------------------------------------------------------------
template <typename T>
static float bench_kernel(int M, int N, int K, int iters, bool& ok)
{
    thrust::device_vector<T> dA(thrust::host_vector<T>(M * K, T(1)));
    thrust::device_vector<T> dB(thrust::host_vector<T>(K * N, T(1)));
    thrust::device_vector<T> dC(M * N, T(0));

    // warm-up
    gemm<T>(dA, dB, dC, M, N, K);
    cudaDeviceSynchronize();

    GpuTimer t;
    t.begin();
    for (int i = 0; i < iters; ++i)
        gemm<T>(dA, dB, dC, M, N, K);
    float ms = t.end();

    ok = verify<T>(thrust::host_vector<T>(dC), K);
    return ms / iters;
}

template <typename T>
static float bench_thrust(int M, int N, int K, int iters, bool& ok)
{
    thrust::device_vector<T> dA(thrust::host_vector<T>(M * K, T(1)));
    thrust::device_vector<T> dB(thrust::host_vector<T>(K * N, T(1)));
    thrust::device_vector<T> dC(M * N, T(0));

    // warm-up
    gemm_thrust<T>(dA, dB, dC, M, N, K);
    cudaDeviceSynchronize();

    GpuTimer t;
    t.begin();
    for (int i = 0; i < iters; ++i)
        gemm_thrust<T>(dA, dB, dC, M, N, K);
    float ms = t.end();

    ok = verify<T>(thrust::host_vector<T>(dC), K);
    return ms / iters;
}

template <typename T>
static float bench_cublas(cublasHandle_t handle,
                          int M, int N, int K, int iters, bool& ok)
{
    thrust::device_vector<T> dA(thrust::host_vector<T>(M * K, T(1)));
    thrust::device_vector<T> dB(thrust::host_vector<T>(K * N, T(1)));
    thrust::device_vector<T> dC(M * N, T(0));

    // warm-up
    gemm_cublas<T>(handle, dA, dB, dC, M, N, K);
    cudaDeviceSynchronize();

    GpuTimer t;
    t.begin();
    for (int i = 0; i < iters; ++i)
        gemm_cublas<T>(handle, dA, dB, dC, M, N, K);
    float ms = t.end();

    ok = verify<T>(thrust::host_vector<T>(dC), K);
    return ms / iters;
}

// ---------------------------------------------------------------------------
// Pretty-print one row of the results table
// ---------------------------------------------------------------------------
static void print_row(const std::string& label, bool ok, float ms,
                      long long flops)
{
    double gflops = (ok ? (flops / ms * 1e-6) : 0.0);  // ms → GFLOP/s
    std::cout << std::left  << std::setw(28) << label
              << std::right << std::setw(8)  << (ok ? "PASS" : "FAIL")
              << std::setw(12) << std::fixed << std::setprecision(3) << ms
              << " ms"
              << std::setw(12) << std::fixed << std::setprecision(2) << gflops
              << " GFLOP/s\n";
}

int main()
{
    constexpr int M = 512, N = 512, K = 512;
    constexpr int ITERS = 20;
    const long long flops = 2LL * M * N * K;  // multiply-adds

    cublasHandle_t cublas;
    cublasCreate(&cublas);

    std::cout << "\nGEMM benchmark  " << M << 'x' << K
              << " * " << K << 'x' << N
              << "  (" << ITERS << " iters)\n\n";

    std::cout << std::left  << std::setw(28) << "variant"
              << std::right << std::setw(8)  << "result"
              << std::setw(14) << "avg time"
              << std::setw(14) << "throughput"  << '\n';
    std::cout << std::string(64, '-') << '\n';

    bool ok;
    float ms;

    ms = bench_kernel<float> (M, N, K, ITERS, ok);
    print_row("tiled kernel  <float>",  ok, ms, flops);

    ms = bench_kernel<double>(M, N, K, ITERS, ok);
    print_row("tiled kernel  <double>", ok, ms, flops);

    ms = bench_thrust<float> (M, N, K, ITERS, ok);
    print_row("thrust functor <float>",  ok, ms, flops);

    ms = bench_thrust<double>(M, N, K, ITERS, ok);
    print_row("thrust functor <double>", ok, ms, flops);

    ms = bench_cublas<float> (cublas, M, N, K, ITERS, ok);
    print_row("cuBLAS  <float>",  ok, ms, flops);

    ms = bench_cublas<double>(cublas, M, N, K, ITERS, ok);
    print_row("cuBLAS  <double>", ok, ms, flops);

    std::cout << '\n';
    cublasDestroy(cublas);
    return 0;
}
