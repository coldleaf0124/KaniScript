#include <iostream>
#include <string>
#include <cstdint>

int main() {
    std::string last = "";
    for (int64_t i = 1; i <= 1000000; i++) {
        std::string s = "item_id_" + std::to_string(i);
        if (i == 1000000) {
            last = s;
        }
    }
    std::cout << "last=" << last << std::endl;
    return 0;
}
