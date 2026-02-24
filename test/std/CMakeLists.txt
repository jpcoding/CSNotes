add_executable(test_cpp23_fmt test_cpp23_fmt.cpp)
add_executable(test_cpp23_span test_cpp23_span.cpp)

set_target_properties(test_cpp23_fmt     PROPERTIES CXX_STANDARD 23 CXX_STANDARD_REQUIRED YES)
set_target_properties(test_cpp23_span    PROPERTIES CXX_STANDARD 23 CXX_STANDARD_REQUIRED YES)

find_program(CLANG_CXX clang++)

if(CLANG_CXX)
    add_custom_target(test_cpp23_mdspan ALL
        COMMAND ${CLANG_CXX} -std=c++23 -stdlib=libc++
            ${CMAKE_CURRENT_SOURCE_DIR}/test_cpp23_mdspan.cpp
            -o ${CMAKE_CURRENT_BINARY_DIR}/test_cpp23_mdspan
        COMMENT "Building test_cpp23_mdspan with clang++ -stdlib=libc++"
    )
else()
    message(STATUS "clang++ not found - skipping test_cpp26_mdspan")
endif()

find_package(fmt QUIET)
if(fmt_FOUND)
    target_link_libraries(test_cpp23_fmt PRIVATE fmt::fmt)
endif()