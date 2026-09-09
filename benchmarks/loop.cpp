#include <iostream>
#include <cstdint>

int64_t compute(int64_t n) {
    int64_t sum = 0;
    for (int64_t i = 0; i < n; i++) {
        int64_t x = i % 10;
        sum += x * 3 - (i % 5);
    }
    return sum;
}

int main() {
    std::cout << compute(500000000) << std::endl;
    return 0;
}
