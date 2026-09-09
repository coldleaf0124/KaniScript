# KaniScript Benchmark Suite: 1,000,000 Rows CSV Ingestion

This directory contains the reproducible benchmark suite comparing **KaniScript**, **Python 3**, and **C++ (Clang -O3)** on real-world CSV parsing and aggregation.

---

## 1. Quick Reproduction

Run the automated runner with a single command:

```bash
./benchmarks/run_benchmarks.sh
```

This script:
1. Automatically generates `data/sales_1m.csv` (28.4 MB, 1M rows, seed `42`) if missing.
2. Compiles C++ naive and hand-tuned implementations with `clang++ -O3 -std=c++17`.
3. Compiles KaniScript implementation with `kani build`.
4. Runs 10 trials for each implementation and outputs mean execution times, peak RSS, and SLOC.

---

## 2. Benchmark Task Description

The benchmark parses a 28.4 MB CSV file containing 1,000,000 rows with 5 columns:
`id,item_name,quantity,price,discount` (e.g., `1,Product_B,2,250,0.05`).

Operations performed per row:
1. String split by comma into 5 fields.
2. Integer parsing for `quantity`.
3. Float parsing for `price` and `discount`.
4. Cumulative calculation: `total_qty += quantity` and `total_revenue += quantity * price * (1.0 - discount)`.
5. Conditional filter: count quantity where `item == "Product_A"`.

**Verification Target**: All 4 implementations must yield identical numerical results:
- Rows: `1,000,000`
- Total Qty: `10,500,000`
- Total Revenue: `10,901,500,000.00`
- Product_A Qty: `1,700,000`

---

## 3. Implementations

| Implementation | Source File | Description |
|---|---|---|
| **Python 3** | [`csv_aggregator.py`](csv_aggregator.py) | Standard idiomatic Python (`open()`, `line.split(",")`, `int()`, `float()`). |
| **C++ Naive** | [`csv_aggregator_std.cpp`](csv_aggregator_std.cpp) | Standard C++ using `std::ifstream`, `std::getline()`, and `std::string::substr()`. |
| **KaniScript** | [`../examples/04_csv_aggregator.ks`](../examples/04_csv_aggregator.ks) | Idiomatic KaniScript using 2-layer arena, dynamic slices, and Caller-Side Boundary Promotion. |
| **C++ Hand-Tuned** | [`csv_aggregator_fast.cpp`](csv_aggregator_fast.cpp) | Expert C++ using whole-file ingestion, `std::string_view`, and `std::from_chars()`. |

---

## 4. Hardware & Environment Specifications

- **Machine**: Apple M2 (8-core CPU: 4 performance + 4 efficiency), 16 GB Unified Memory
- **Operating System**: macOS 27.0 arm64
- **C++ Compiler**: Apple clang version 17.0.0 (`-O3 -std=c++17`)
- **Python Runtime**: Python 3.14.6
- **KaniScript**: v0.1.0 (Clang -O3 backend)
