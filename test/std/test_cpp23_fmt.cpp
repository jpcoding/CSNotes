// test_cpp23_fmt.cpp
// Test C++23 features with fmt library
#include <iostream>
#include <format>
#include <vector>

int main() {
    // C++23: std::format with fmtlib (if supported by your compiler)
    int year = 2026;
    std::string msg = std::format("Welcome to C++{}!", 23);
    std::cout << msg << std::endl;

    // C++23: deducing this, range-based for with initializer
    for (std::vector v{1, 2, 3, 4, 5}; auto& x : v) {
        std::cout << std::format("Element: {}\n", x);
    }

    // C++23: use std::print
    std::print(std::cout, "Year: {}\n", year);
    

    // C++23: if consteval
    if consteval {
        // This block runs at compile time if possible
    }

    return 0;
}
