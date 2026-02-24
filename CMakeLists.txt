cmake_minimum_required(VERSION 3.20)
project(cpp_training)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Detect CUDA toolkit; add CUDA tests only when available
find_package(CUDAToolkit QUIET)
if (CUDAToolkit_FOUND)
	message(STATUS "CUDA toolkit found; enabling CUDA targets")
	enable_language(CUDA)
	# Set CUDA architecture for RTX 4070 Laptop GPU
	set(CMAKE_CUDA_ARCHITECTURES 89)
	set(HAS_CUDA TRUE)
else()
	message(STATUS "CUDA toolkit not found; skipping CUDA tests")
	set(HAS_CUDA FALSE)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${CMAKE_SOURCE_DIR}/include)

add_subdirectory(${CMAKE_SOURCE_DIR}/test/posix)
if(HAS_CUDA)
	add_subdirectory(${CMAKE_SOURCE_DIR}/test/cuda)
endif()
add_subdirectory(${CMAKE_SOURCE_DIR}/test/network)
add_subdirectory(${CMAKE_SOURCE_DIR}/test/std)

