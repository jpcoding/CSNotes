// test_cpp23_span.cpp
// Test C++23 std::span usage
#include <iostream>
#include <span>
#include <vector>

void print_span(std::span<const int> s) {
    for (int v : s) {
        std::cout << v << ' ';
    }
    std::cout << "\n";
}

int main() {
    std::vector<int> data{1, 2, 3, 4, 5};
    std::span<int> s1{data};
    print_span(s1);

    int arr[] = {10, 20, 30};
    std::span<int> s2{arr};
    print_span(s2);

    // Subspan example
    auto sub = s1.subspan(1, 3); // elements 2, 3, 4
    print_span(sub);

    return 0;
}
