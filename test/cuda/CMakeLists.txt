
add_executable(get_device
    get_device.cu
)

add_executable(get_pi_cpu pi.cpp)


# Install executables
install(TARGETS get_device get_pi_cpu
    RUNTIME DESTINATION bin/tests
)
