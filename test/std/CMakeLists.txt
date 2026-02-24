add_executable(test_cpp23_fmt test_cpp23_fmt.cpp)
add_executable(test_cpp23_span test_cpp23_span.cpp)

# C++26: std::mdspan test
add_executable(test_cpp26_mdspan test_cpp26_mdspan.cpp)
# Use C++23 for mdspan test (reference implementation)
# set_target_properties(test_cpp26_mdspan PROPERTIES CXX_STANDARD 23 CXX_STANDARD_REQUIRED YES)
set_target_properties(test_cpp23_span PROPERTIES CXX_STANDARD 23 CXX_STANDARD_REQUIRED YES)
set_target_properties(test_cpp23_fmt PROPERTIES CXX_STANDARD 23 CXX_STANDARD_REQUIRED YES)

# Require C++26 for this target
set_target_properties(test_cpp26_mdspan PROPERTIES CXX_STANDARD 26 CXX_STANDARD_REQUIRED YES)

# Find and link fmt if available (CMake >= 3.20 has FindFmt)


find_package(fmt QUIET)
if(fmt_FOUND)
    target_link_libraries(test_cpp23_fmt PRIVATE fmt::fmt)
endif()
