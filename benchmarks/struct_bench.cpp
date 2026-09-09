#include <iostream>
#include <string>
#include <cstdint>

struct SaleItem {
    std::string name;
    int64_t price;
    int64_t qty;
};

int main() {
    SaleItem best = {"", 0, 0};
    int64_t total_sales = 0;
    for (int64_t i = 1; i <= 1000000; i++) {
        int64_t p = (i % 100) + 10;
        int64_t q = (i % 5) + 1;
        std::string n = "item_" + std::to_string(i);
        SaleItem item = {n, p, q};
        int64_t total = item.price * item.qty;
        total_sales += total;
        if (total > best.price * best.qty) {
            best = item;
        }
    }
    std::cout << "total=" << total_sales << " best=" << best.name << " (" << best.price << "x" << best.qty << ")" << std::endl;
    return 0;
}
