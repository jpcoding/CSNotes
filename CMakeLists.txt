cmake_minimum_required(VERSION 3.20)
project(cpp_training)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Enable CUDA language
enable_language(CUDA)
# Set CUDA architecture for RTX 4070 Laptop GPU
set(CMAKE_CUDA_ARCHITECTURES 89)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)


include_directories(${CMAKE_SOURCE_DIR}/include)

add_subdirectory(${CMAKE_SOURCE_DIR}/test/posix)
add_subdirectory(${CMAKE_SOURCE_DIR}/test/cuda)
add_subdirectory(${CMAKE_SOURCE_DIR}/test/network)
add_subdirectory(${CMAKE_SOURCE_DIR}/test/std)

