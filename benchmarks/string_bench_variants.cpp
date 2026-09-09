#include <iostream>
#include <string>
#include <string_view>
#include <cstdint>
#include <charconv>
#include <chrono>
#include <vector>

// 1. 素朴な C++: operator+ と std::to_string (現状の benchmarks/string_bench.cpp)
void bench_naive() {
    auto t0 = std::chrono::high_resolution_clock::now();
    std::string last = "";
    for (int64_t i = 1; i <= 1000000; i++) {
        std::string s = "item_id_" + std::to_string(i);
        if (i == 1000000) last = s;
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    std::cout << "1. C++ Naive (operator+): " 
              << std::chrono::duration<double>(t1 - t0).count() << "s, last=" << last << std::endl;
}

// 2. C++ 最適化A: reserve() + append() (ループ毎に新規インスタンス生成、SSO範囲内)
void bench_reserve() {
    auto t0 = std::chrono::high_resolution_clock::now();
    std::string last = "";
    for (int64_t i = 1; i <= 1000000; i++) {
        std::string s;
        // SSOの恩恵を受けるため reserve はせず、直接 append
        s.append("item_id_");
        s.append(std::to_string(i));
        if (i == 1000000) last = s;
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    std::cout << "2. C++ Append (std::to_string): " 
              << std::chrono::duration<double>(t1 - t0).count() << "s, last=" << last << std::endl;
}

// 3. C++ 最適化B: std::to_chars (C++17標準の最速itoa) + std::string
void bench_to_chars_string() {
    auto t0 = std::chrono::high_resolution_clock::now();
    std::string last = "";
    for (int64_t i = 1; i <= 1000000; i++) {
        char buf[32];
        memcpy(buf, "item_id_", 8);
        auto [ptr, ec] = std::to_chars(buf + 8, buf + 32, i);
        std::string s(buf, ptr - buf);
        if (i == 1000000) last = s;
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    std::cout << "3. C++ std::to_chars + std::string: " 
              << std::chrono::duration<double>(t1 - t0).count() << "s, last=" << last << std::endl;
}

// 4. C++ 最適化C: 文字列バッファ再利用 (clear() して再利用)
void bench_reused_buffer() {
    auto t0 = std::chrono::high_resolution_clock::now();
    std::string s;
    s.reserve(32);
    std::string last = "";
    for (int64_t i = 1; i <= 1000000; i++) {
        s.clear();
        s.append("item_id_");
        char buf[24];
        auto [ptr, ec] = std::to_chars(buf, buf + 24, i);
        s.append(buf, ptr - buf);
        if (i == 1000000) last = s;
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    std::cout << "4. C++ Reused string buffer + to_chars: " 
              << std::chrono::duration<double>(t1 - t0).count() << "s, last=" << last << std::endl;
}

int main() {
    for (int run = 1; run <= 3; run++) {
        std::cout << "\n--- Run " << run << " ---" << std::endl;
        bench_naive();
        bench_reserve();
        bench_to_chars_string();
        bench_reused_buffer();
    }
    return 0;
}
