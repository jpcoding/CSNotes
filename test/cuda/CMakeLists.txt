
add_executable(get_device
    get_device.cu
)

add_executable(get_pi_cpu pi.cpp)

add_executable(gemm_bench
    gemm_bench.cu
    ${CMAKE_SOURCE_DIR}/src/cuda/gemm.cu
)
target_link_libraries(gemm_bench PRIVATE CUDA::cublas)

# Install executables
install(TARGETS get_device get_pi_cpu gemm_bench
    RUNTIME DESTINATION bin/tests
)
