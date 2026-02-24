#include <gemm.cuh>

// Explicit instantiations — keeps compile times down for users of the header

// Raw pointer
template void gemm<float> (const float*,  const float*,  float*,  int, int, int, float,  float);
template void gemm<double>(const double*, const double*, double*, int, int, int, double, double);

// Thrust device_vector overload
template void gemm<float> (const thrust::device_vector<float>&,
                            const thrust::device_vector<float>&,
                            thrust::device_vector<float>&,
                            int, int, int, float,  float);
template void gemm<double>(const thrust::device_vector<double>&,
                            const thrust::device_vector<double>&,
                            thrust::device_vector<double>&,
                            int, int, int, double, double);

// Thrust functor implementation
template void gemm_thrust<float> (const thrust::device_vector<float>&,
                                   const thrust::device_vector<float>&,
                                   thrust::device_vector<float>&,
                                   int, int, int, float,  float);
template void gemm_thrust<double>(const thrust::device_vector<double>&,
                                   const thrust::device_vector<double>&,
                                   thrust::device_vector<double>&,
                                   int, int, int, double, double);
