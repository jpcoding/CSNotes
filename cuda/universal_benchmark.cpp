// Universal GPU/CPU Benchmark - SYCL 2020 USM Edition
//
// Tiled matrix multiplication (2048x2048) across all SYCL-visible devices.
// Uses SYCL2020 Unified Shared Memory (USM) with in-order queues for minimal
// overhead. Automatically discovers and benchmarks NVIDIA, AMD, and CPU devices
// from a single source, single binary.
//
// Tested on:
//   - NVIDIA GeForce RTX 4070 Laptop GPU (CUDA)    ~1438 GFLOPS
//   - AMD Ryzen 7 8845HS CPU (OpenMP/AVX-512)       ~202 GFLOPS
//   - AMD Radeon 780M iGPU (HIP/ROCm)               ~187 GFLOPS
//
// Build with AdaptiveCpp (https://github.com/AdaptiveCpp/AdaptiveCpp):
//   acpp -O2 -o universal_benchmark universal_benchmark.cpp
//
// Build with Intel oneAPI DPC++ (Intel GPUs + CPU only without Codeplay plugin):
//   icpx -fsycl -O2 -o universal_benchmark universal_benchmark.cpp
//
// Notes:
//   - OpenCL platform is skipped; AMD's OpenCL CPU runtime doesn't support
//     SPIR-V ingestion via AdaptiveCpp's SSCP JIT path. CPU is covered by
//     the OpenMP backend instead.
//   - First run incurs JIT compilation overhead. Run twice for peak numbers.
//   - AdaptiveCpp built against LLVM 19 is required for ROCm 6.x compatibility
//     (ROCm's comgr uses LLVM 19 internally; mismatched IR versions will fail).
//

#include <sycl/sycl.hpp>
#include <iostream>
#include <vector>
#include <chrono>
#include <string>
#include <cmath>

#define N 2048
#define BLOCK_SIZE 16

bool verifyResult(const float *c, float expected) {
    int errors = 0;
    for (int i = 0; i < N * N && errors < 5; ++i) {
        if (std::fabs(c[i] - expected) > 0.1f) {
            std::cout << "   MISMATCH at [" << i/N << "][" << i%N << "]: "
                      << c[i] << " != " << expected << std::endl;
            ++errors;
        }
    }
    return errors == 0;
}

void matrixMul(sycl::queue &q, const std::vector<float> &hostA, const std::vector<float> &hostB, std::vector<float> &hostC) {
    float *dA = sycl::malloc_device<float>(N * N, q);
    float *dB = sycl::malloc_device<float>(N * N, q);
    float *dC = sycl::malloc_device<float>(N * N, q);

    q.memcpy(dA, hostA.data(), N * N * sizeof(float));
    q.memcpy(dB, hostB.data(), N * N * sizeof(float));
    q.wait();

    sycl::range<2> global_range(N, N);
    sycl::range<2> local_range(BLOCK_SIZE, BLOCK_SIZE);

    auto start = std::chrono::high_resolution_clock::now();

    q.submit([&](sycl::handler &h) {
        sycl::local_accessor<float, 2> tileA(sycl::range<2>(BLOCK_SIZE, BLOCK_SIZE), h);
        sycl::local_accessor<float, 2> tileB(sycl::range<2>(BLOCK_SIZE, BLOCK_SIZE), h);

        h.parallel_for(sycl::nd_range<2>(global_range, local_range),
            [=](sycl::nd_item<2> item) {
            int row = item.get_global_id(0);
            int col = item.get_global_id(1);
            int localRow = item.get_local_id(0);
            int localCol = item.get_local_id(1);

            float sum = 0.0f;

            for (int m = 0; m < N / BLOCK_SIZE; ++m) {
                tileA[localRow][localCol] = dA[row * N + m * BLOCK_SIZE + localCol];
                tileB[localRow][localCol] = dB[(m * BLOCK_SIZE + localRow) * N + col];

                item.barrier(sycl::access::fence_space::local_space);

                for (int k = 0; k < BLOCK_SIZE; ++k) {
                    sum += tileA[localRow][k] * tileB[k][localCol];
                }
                item.barrier(sycl::access::fence_space::local_space);
            }

            dC[row * N + col] = sum;
        });
    });
    q.wait();

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;

    q.memcpy(hostC.data(), dC, N * N * sizeof(float));
    q.wait();

    double gflops = (2.0 * N * N * N) / (duration.count() * 1e9);
    std::cout << "   Time: " << duration.count() * 1000 << " ms" << std::endl;
    std::cout << "   Speed: " << gflops << " GFLOPS" << std::endl;

    float expected = 1.0f * 2.0f * N;
    if (verifyResult(hostC.data(), expected))
        std::cout << "   Verify: PASS" << std::endl;
    else
        std::cout << "   Verify: FAIL" << std::endl;

    sycl::free(dA, q);
    sycl::free(dB, q);
    sycl::free(dC, q);
}

int main() {
    std::vector<float> a(N * N, 1.0f);
    std::vector<float> b(N * N, 2.0f);
    std::vector<float> c(N * N, 0.0f);

    std::cout << "=== The Grand Unified Benchmark (USM) ===" << std::endl;
    std::cout << "Matrix Size: " << N << "x" << N << std::endl;
    std::cout << "Scanning for devices..." << std::endl;

    auto platforms = sycl::platform::get_platforms();

    for (const auto &p : platforms) {
        std::string platName = p.get_info<sycl::info::platform::name>();

        if (platName.find("OpenCL") != std::string::npos) {
            std::cout << "\nPlatform: " << platName << " [skipped]" << std::endl;
            continue;
        }

        std::cout << "\nPlatform: " << platName << std::endl;

        auto devices = p.get_devices();
        for (const auto &d : devices) {
            std::cout << " -> Device: " << d.get_info<sycl::info::device::name>() << std::endl;

            if (d.is_cpu() || d.is_gpu()) {
                try {
                    sycl::queue q(d, sycl::property::queue::in_order{});
                    std::cout << "    [Running Benchmark...]" << std::endl;
                    matrixMul(q, a, b, c);
                } catch (sycl::exception &e) {
                    std::cout << "    [Failed]: " << e.what() << std::endl;
                } catch (std::exception &e) {
                    std::cout << "    [Error]: " << e.what() << std::endl;
                }
            }
        }
    }

    return 0;
}
