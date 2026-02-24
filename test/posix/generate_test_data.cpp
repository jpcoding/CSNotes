// generate_test_data.cpp
#include <cstdio>
#include <vector>
#include <random>

void generate_test_file(const char* filename, size_t num_floats) {
    FILE* f = fopen(filename, "wb");
    std::vector<float> buffer(1024 * 1024); // 1M floats at a time
    std::mt19937 gen(42);
    std::uniform_real_distribution<float> dist(0.0f, 1.0f);
    
    for (size_t i = 0; i < num_floats; i += buffer.size()) {
        size_t chunk = std::min(buffer.size(), num_floats - i);
        for (size_t j = 0; j < chunk; j++) {
            buffer[j] = dist(gen);
        }
        fwrite(buffer.data(), sizeof(float), chunk, f);
    }
    fclose(f);
}


int main() {
    generate_test_file("test_1gb.dat", 250 * 1024 * 1024);
    return 0;
}

