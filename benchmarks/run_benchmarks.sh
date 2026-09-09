#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=================================================="
echo " 🦀 KaniScript Benchmark Suite Runner"
echo "=================================================="

# 1. Generate 1,000,000 rows CSV dataset if missing
mkdir -p data bin
if [ ! -f "data/sales_1m.csv" ]; then
    echo "[1/4] Generating data/sales_1m.csv (1M rows)..."
    python3 -c '
import random
random.seed(42)
items = ["Product_A", "Product_B", "Product_C", "Product_D", "Product_E"]
prices = [100, 250, 500, 1200, 3000]
with open("data/sales_1m.csv", "w", encoding="utf-8") as f:
    for i in range(1, 1000001):
        idx = i % 5
        qty = (i % 20) + 1
        price = prices[idx]
        disc = (i % 4) * 0.05
        f.write(f"{i},{items[idx]},{qty},{price},{disc:.2f}\n")
'
    echo "      Done (28.4 MB generated)"
else
    echo "[1/4] Dataset data/sales_1m.csv already exists."
fi

# 2. Compile C++ benchmarks (-O3)
echo "[2/4] Compiling C++ implementations (Clang -O3)..."
clang++ -O3 -std=c++17 benchmarks/csv_aggregator_std.cpp -o bin/csv_aggregator_cpp_std
clang++ -O3 -std=c++17 benchmarks/csv_aggregator_fast.cpp -o bin/csv_aggregator_cpp_fast

# 3. Build KaniScript implementation (-O3)
echo "[3/4] Compiling KaniScript implementation..."
./bin/kani build examples/csv_aggregator.ks -o bin/csv_aggregator_ks

# 4. Run Benchmark Runner (10 trials)
echo "[4/4] Executing 10-trial benchmarks..."
echo ""
python3 benchmarks/csv_benchmark_runner.py
echo "=================================================="
