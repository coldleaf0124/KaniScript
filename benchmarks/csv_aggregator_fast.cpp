#include <iostream>
#include <fstream>
#include <string>
#include <string_view>
#include <charconv>
#include <chrono>

int main() {
    auto start = std::chrono::high_resolution_clock::now();

    std::ifstream file("data/sales_1m.csv", std::ios::binary | std::ios::ate);
    if (!file.is_open()) return 1;
    std::streamsize sz = file.tellg();
    file.seekg(0, std::ios::beg);

    std::string buffer(sz, '\0');
    if (!file.read(&buffer[0], sz)) return 1;

    int64_t total_qty = 0;
    double total_rev = 0.0;
    int64_t target_qty = 0;
    int64_t count = 0;

    std::string_view sv(buffer);
    size_t pos = 0;
    while (pos < sv.size()) {
        size_t nl = sv.find('\n', pos);
        std::string_view line = (nl == std::string_view::npos) ? sv.substr(pos) : sv.substr(pos, nl - pos);
        pos = (nl == std::string_view::npos) ? sv.size() : nl + 1;
        if (line.empty()) continue;

        size_t p1 = line.find(',');
        if (p1 == std::string_view::npos) continue;
        size_t p2 = line.find(',', p1 + 1);
        if (p2 == std::string_view::npos) continue;
        size_t p3 = line.find(',', p2 + 1);
        if (p3 == std::string_view::npos) continue;
        size_t p4 = line.find(',', p3 + 1);
        if (p4 == std::string_view::npos) continue;

        std::string_view item = line.substr(p1 + 1, p2 - p1 - 1);
        int64_t qty = 0;
        std::from_chars(line.data() + p2 + 1, line.data() + p3, qty);

        char* end_ptr = nullptr;
        double price = strtod(line.data() + p3 + 1, &end_ptr);
        double disc = strtod(line.data() + p4 + 1, &end_ptr);

        total_qty += qty;
        total_rev += qty * price * (1.0 - disc);
        if (item == "Product_A") {
            target_qty += qty;
        }
        count++;
    }

    auto end = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(end - start).count();

    std::cout << "Rows: " << count << "\n";
    std::cout << "Total Qty: " << total_qty << "\n";
    std::cout << "Total Revenue: " << total_rev << "\n";
    std::cout << "Product_A Qty: " << target_qty << "\n";
    std::cout << "Elapsed: " << elapsed << " s\n";

    return 0;
}
