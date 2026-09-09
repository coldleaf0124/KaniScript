#include <iostream>
#include <fstream>
#include <string>
#include <chrono>

int main() {
    auto start = std::chrono::high_resolution_clock::now();

    std::ifstream file("data/sales_1m.csv");
    if (!file.is_open()) {
        std::cerr << "Failed to open file\n";
        return 1;
    }

    int64_t total_qty = 0;
    double total_rev = 0.0;
    int64_t target_qty = 0;
    int64_t count = 0;

    std::string line;
    while (std::getline(file, line)) {
        if (line.empty()) continue;

        size_t p1 = line.find(',');
        if (p1 == std::string::npos) continue;
        size_t p2 = line.find(',', p1 + 1);
        if (p2 == std::string::npos) continue;
        size_t p3 = line.find(',', p2 + 1);
        if (p3 == std::string::npos) continue;
        size_t p4 = line.find(',', p3 + 1);
        if (p4 == std::string::npos) continue;

        std::string item = line.substr(p1 + 1, p2 - p1 - 1);
        int64_t qty = std::stoll(line.substr(p2 + 1, p3 - p2 - 1));
        double price = std::stod(line.substr(p3 + 1, p4 - p3 - 1));
        double disc = std::stod(line.substr(p4 + 1));

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
