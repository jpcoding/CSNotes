#pragma once

#include <thrust/device_vector.h>
#include <thrust/host_vector.h>
#include <thrust/for_each.h>
#include <thrust/iterator/counting_iterator.h>
#include <cublas_v2.h>
#include <cuda_runtime.h>

// ---------------------------------------------------------------------------
// Tiled GEMM kernel:  C = alpha * A * B + beta * C
//   A : M x K  (row-major)
//   B : K x N  (row-major)
//   C : M x N  (row-major)
// ---------------------------------------------------------------------------
static constexpr int GEMM_TILE = 16;

template <typename T>
__global__ void gemm_kernel(const T* __restrict__ A,
                             const T* __restrict__ B,
                             T*       __restrict__ C,
                             int M, int N, int K,
                             T alpha, T beta)
{
    __shared__ T sA[GEMM_TILE][GEMM_TILE];
    __shared__ T sB[GEMM_TILE][GEMM_TILE];

    const int row = blockIdx.y * GEMM_TILE + threadIdx.y;
    const int col = blockIdx.x * GEMM_TILE + threadIdx.x;

    T acc = T(0);

    for (int t = 0; t < (K + GEMM_TILE - 1) / GEMM_TILE; ++t) {
        const int aCol = t * GEMM_TILE + threadIdx.x;
        const int bRow = t * GEMM_TILE + threadIdx.y;

        sA[threadIdx.y][threadIdx.x] = (row < M && aCol < K) ? A[row * K + aCol] : T(0);
        sB[threadIdx.y][threadIdx.x] = (bRow < K && col < N) ? B[bRow * N + col] : T(0);

        __syncthreads();

        #pragma unroll
        for (int k = 0; k < GEMM_TILE; ++k)
            acc += sA[threadIdx.y][k] * sB[k][threadIdx.x];

        __syncthreads();
    }

    if (row < M && col < N)
        C[row * N + col] = alpha * acc + beta * C[row * N + col];
}

// ---------------------------------------------------------------------------
// Raw-pointer wrapper — caller manages device memory
// ---------------------------------------------------------------------------
template <typename T>
void gemm(const T* d_A, const T* d_B, T* d_C,
          int M, int N, int K,
          T alpha = T(1), T beta = T(0))
{
    const dim3 block(GEMM_TILE, GEMM_TILE);
    const dim3 grid((N + GEMM_TILE - 1) / GEMM_TILE,
                    (M + GEMM_TILE - 1) / GEMM_TILE);
    gemm_kernel<T><<<grid, block>>>(d_A, d_B, d_C, M, N, K, alpha, beta);
}

// ---------------------------------------------------------------------------
// Thrust overload — device_vector owns the memory
// ---------------------------------------------------------------------------
template <typename T>
void gemm(const thrust::device_vector<T>& A,
          const thrust::device_vector<T>& B,
          thrust::device_vector<T>&       C,
          int M, int N, int K,
          T alpha = T(1), T beta = T(0))
{
    gemm(thrust::raw_pointer_cast(A.data()),
         thrust::raw_pointer_cast(B.data()),
         thrust::raw_pointer_cast(C.data()),
         M, N, K, alpha, beta);
}

// ---------------------------------------------------------------------------
// Thrust kernel — no __global__, no <<<>>>
//
// thrust::for_each dispatches one work-item per output element across [0, M*N).
// GemmFunctor runs entirely on the device via the counting_iterator range.
// ---------------------------------------------------------------------------
template <typename T>
struct GemmFunctor {
    const T* A;
    const T* B;
    T*       C;
    int N, K;
    T alpha, beta;

    __device__ void operator()(int idx) const {
        const int row = idx / N;
        const int col = idx % N;
        T acc = T(0);
        for (int k = 0; k < K; ++k)
            acc += A[row * K + k] * B[k * N + col];
        C[idx] = alpha * acc + beta * C[idx];
    }
};

// ---------------------------------------------------------------------------
// cuBLAS wrapper
//
// cuBLAS is column-major. For row-major C = alpha*A*B + beta*C we exploit:
//   C^T = alpha * B^T * A^T + beta * C^T
// so we pass B first and A second with the dimensions swapped.
// Caller owns the cublasHandle_t lifetime.
// ---------------------------------------------------------------------------
inline cublasStatus_t cublas_gemm_impl(cublasHandle_t h,
    int N, int M, int K,
    const float*  alpha, const float*  B, const float*  A,
    const float*  beta,        float*  C)
{
    return cublasSgemm(h, CUBLAS_OP_N, CUBLAS_OP_N, N, M, K,
                       alpha, B, N, A, K, beta, C, N);
}

inline cublasStatus_t cublas_gemm_impl(cublasHandle_t h,
    int N, int M, int K,
    const double* alpha, const double* B, const double* A,
    const double* beta,       double*  C)
{
    return cublasDgemm(h, CUBLAS_OP_N, CUBLAS_OP_N, N, M, K,
                       alpha, B, N, A, K, beta, C, N);
}

template <typename T>
void gemm_cublas(cublasHandle_t handle,
                 const thrust::device_vector<T>& A,
                 const thrust::device_vector<T>& B,
                 thrust::device_vector<T>&       C,
                 int M, int N, int K,
                 T alpha = T(1), T beta = T(0))
{
    cublas_gemm_impl(handle, N, M, K, &alpha,
                     thrust::raw_pointer_cast(B.data()),
                     thrust::raw_pointer_cast(A.data()),
                     &beta,
                     thrust::raw_pointer_cast(C.data()));
}

template <typename T>
void gemm_thrust(const thrust::device_vector<T>& A,
                 const thrust::device_vector<T>& B,
                 thrust::device_vector<T>&       C,
                 int M, int N, int K,
                 T alpha = T(1), T beta = T(0))
{
    thrust::for_each(
        thrust::counting_iterator<int>(0),
        thrust::counting_iterator<int>(M * N),
        GemmFunctor<T>{
            thrust::raw_pointer_cast(A.data()),
            thrust::raw_pointer_cast(B.data()),
            thrust::raw_pointer_cast(C.data()),
            N, K, alpha, beta
        }
    );
}
