#include "Utils/Timer.hpp"
#include "CLI11/CLI11.hpp"
#include <cstddef>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <numeric>
#include <vector>

size_t SIZE = 1024 * 1024 * 250;

double sum_file_c_style(const char* filename, size_t file_size, size_t buffer_size = 1024 * 1024)
{
    FILE* f = fopen(filename, "rb");
    double sum = 0;
    // size_t buffer_size = 1024*1024;
    float* buffer = (float*)malloc(buffer_size * sizeof(float));
    int iters     = file_size / buffer_size;
    float current = 0;
    Timer timer {};
    double accu_time = 0;
    for (int i = 0; i < iters; i++)
    {
        timer.reset();
        // fseek(f,sizeof(float)*i*buffer_size, SEEK_SET);// move the pointer to the
        // correct start.
        size_t read_count = fread(buffer, sizeof(float), buffer_size, f);
        accu_time += timer.elapsed();
        // std::cout<<"read cout = " << read_count<< std::endl;
        for (size_t j = 0; j < buffer_size; ++j)
        {
            sum += double(buffer[j]);
        }
    }
    free(buffer);
    fclose(f);
    std::cout << "C: total read time : " << accu_time << std::endl;
    std::cout << "C: sum is :" << sum << std::endl;
    return sum;
}

double sum_file_cpp_style(const char* filename, size_t file_size, size_t buffer_size = 1024 * 1024)
{
    std::ifstream fin(filename, std::ios::binary | std::ios::ate);
    if (!fin)
    {
        std::cerr << "error, can't open the file\n";
        return 0;
    }
    size_t total_bytes = 0;

    Timer timer {};
    double accu_time = 0;
    double sum       = 0;
    std::vector<float> buffer;
    buffer.resize(buffer_size, 0);
    int iters = file_size / buffer_size;
    // std::cout << "cpp iters : " << iters<< std::endl;
    fin.seekg(0, std::ios::beg);
    for (int i = 0; i < iters; ++i)
    {
        timer.reset();
        fin.read(reinterpret_cast<char*>(buffer.data()), buffer.size() * sizeof(float));
        accu_time += timer.elapsed();
        sum += std::reduce(buffer.begin(), buffer.end(), double(0.0));
    }
    fin.close();

    // fin.seekg(0, std::ios::end);

    // fin.seekg(0, std::ios::beg);
    // timer.reset();
    // fin.read(reinterpret_cast<char *>(data.data()), SIZE * sizeof(float));
    // accu_time = timer.elapsed();
    // double sum = std::reduce(data.begin(), data.end(), double(0.0));
    // fin.close();
    std::cout << "C++: total read time : " << accu_time << std::endl;
    std::cout << "C++: sum = " << sum << std::endl;
    return sum;
}

double sum_file_cpp_style_bak(const char* filename)
{
    size_t SIZE = 0;  // 1. Don't hardcode. We will detect this.
    std::ifstream fin(filename, std::ios::binary | std::ios::ate);

    if (!fin)
    {
        std::cerr << "error, can't open the file\n";
        return 0;  // 2. CRITICAL FIX: Stop execution if file fails!
    }

    // 3. LOGIC FIX: Get actual file size since we are at the end (ate)
    std::streamsize bytes_in_file = fin.tellg();
    SIZE                          = bytes_in_file / sizeof(float);  // Update SIZE to match reality

    Timer timer {};
    double accu_time = 0;
    std::vector<float> data;
    data.resize(SIZE);  // Allocate exactly what the file needs

    fin.seekg(0, std::ios::beg);  // Go back to start
    timer.reset();

    // 4. Read the exact number of bytes present in the file
    fin.read(reinterpret_cast<char*>(data.data()), bytes_in_file);

    accu_time  = timer.elapsed();
    double sum = std::reduce(data.begin(), data.end(), double(0.0));
    fin.close();
    double sum_verify = 0;
    for (int i = 0; i < data.size(); i++)
    {
        sum_verify += data[i];
    }
    std::cout << "c++ sum verify" << sum_verify << std::endl;

    std::cout << "C++: total read time : " << accu_time << std::endl;
    std::cout << "C++: sum = " << sum << std::endl;

    return sum;
}

int main(int argc, char** argv)
{
    CLI::App app{"App description"};
    argv = app.ensure_utf8(argv);
    std::string filename = "test_1gb.dat";
    size_t buffer_size = 1024; 
    app.add_option("-f,--file", filename, "A help string");
    app.add_option("-s,--size", buffer_size, "buffer size"); 
    CLI11_PARSE(app, argc, argv);
    size_t file_size   = std::filesystem::file_size(filename.c_str());
    std::cout << "input file size " << file_size << std::endl;
    sum_file_cpp_style(filename.c_str(), file_size, buffer_size);
    sum_file_c_style(filename.c_str(), file_size, buffer_size);
    return 0;
}
