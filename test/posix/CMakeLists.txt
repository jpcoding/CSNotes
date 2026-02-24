
add_executable(basic_io
    basic_io.cpp
)
add_executable(generate_test_data
    generate_test_data.cpp
)


# Install executables
install(TARGETS basic_io generate_test_data
    RUNTIME DESTINATION bin/tests
)
