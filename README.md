<div align="center">

# <img src="assets/kaniscript_icon.svg" width="48" height="48" alt="KaniScript Logo" style="vertical-align: middle;" /> KaniScript

**Python-like simplicity, native execution speed, exploring an alternative memory management model with zero GC.**

[![CI](https://github.com/coldleaf0124/kaniscript/actions/workflows/ci.yml/badge.svg)](https://github.com/coldleaf0124/kaniscript/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

[English](README.md) | [日本語 (Japanese)](README.ja.md)

<br>

> *KaniScript is human-designed and primarily human-written, with AI used for code review, refinement, and development assistance.*

</div>

---

## Why KaniScript?

Developers have long faced a hard choice:
- **Python / Go**: Highly productive, but garbage collection (GC) introduces memory bloat and runtime pauses.
- **Rust**: Blazing fast and memory safe, but the borrow checker and explicit lifetime annotations carry a steep learning curve.
- **C / C++**: Maximum performance, but manual memory management risks leaks, use-after-free (UAF), and lock contention.

**KaniScript** explores an alternative path:
1. **Ultra-minimalist syntax**: Removes keyword noise (`fn`, `def`, `let`, `print()` are gone).
2. **2-Layer Arena + Caller-Side Boundary Promotion**: Delivers native C speed without GC pauses or borrow checker annotations.

---

## 1,000,000 Rows CSV Benchmark

Parsing and aggregating a 28.4 MB CSV file (1,000,000 rows, 5 columns) on an **Apple M2** (macOS arm64, Clang -O3, Python 3.14, N=10 trials):

```bash
python3 benchmarks/csv_benchmark_runner.py
```

| Language / Implementation | Time (Mean, N=10) | vs Python | Peak RSS | SLOC | Temp Leak in Loop |
|---|---|---|---|---|---|
| **Python 3.14 (Standard)** | 0.4239s | 1.00x | 14.5 MB | 31 | N/A (GC) |
| **C++ Clang -O3 (Naive `ifstream` + `string`)** | 0.2085s | 2.03x | 1.6 MB | 42 | 0 B (Manual Free) |
| **KaniScript (2-Layer Arena + Slices)** | **0.1440s** | **2.94x** | 196.0 MB | 41 | **0 B (LIFO Reset)** |
| **C++ Clang -O3 (Hand-tuned `string_view` + `charconv`)** | 0.0790s | 5.37x | 29.1 MB | 49 | 0 B (Zero-Alloc) |

### Honest Technical Analysis
- **31% faster than naive C++**: Eliminates per-line heap allocation/deallocation overhead via arena pointer bumps and LIFO rewinds.
- **Approaching hand-tuned C++**: While hand-tuned zero-copy C++ (`string_view`) is ~1.8x faster (0.0790s vs 0.1440s), KaniScript achieves its speed with 25 lines of clean, Python-like code.
- **0 Bytes Per-Iteration Leak**: In this loop pattern, temporary per-iteration tokens yield **0 bytes of Persistent arena growth** over 1,000,000 iterations.
- **Trade-off (196 MB Peak RSS)**: Whole-file ingestion currently keeps all parsed tokens in the arena at once. Streaming line iterators are planned for gigabyte-scale datasets.

---

## Ultra-Minimalist Syntax

| Feature | Conventional (Rust / Python / C++) | **KaniScript** |
|---|---|---|
| **Function** | `fn add(...)` / `def add(...)` | **`add(a: i64, b: i64) -> i64 { a + b }`** (no `fn`/`def`) |
| **Variable** | `let mut x = 10;` / `x = 10` | **`x := 10`** (single `:=`) |
| **Output** | `println!(...)` / `print(...)` | **`out "Hello, World"`** (no parentheses) |
| **Branch** | `if ... else ...` | **`when total > 100 { ... } else { ... }`** |
| **Loop** | `for i in range(...):` | **`each i in 0..10 { ... }`** |
| **Return** | `return a + b;` | **Implicit expression return** |

### Quick Example (`examples/02_fibonacci.ks`)
```rust
fib(n: i64) -> i64 {
    when n <= 1 { return n }
    fib(n - 1) + fib(n - 2)
}

main() {
    out "Fibonacci(40):"
    out fib(40)
}
```

---

## Memory Architecture: Caller-Side Boundary Promotion

KaniScript uses two distinct memory arenas:
1. **Scratch Arena**: For temporary expressions, intermediate strings, and loop-local slices. Rewound on every loop iteration (`offset = mark`) with zero deallocation overhead.
2. **Persistent Arena**: For long-lived data that must survive the enclosing scope.

```
[Loop Start] size_t mark = zp_scratch_mark();
     │
     ├─ Temporary string / slice allocation (simple pointer bump)
     │
     ├─ Assignment to outer scope variable?
     │      ├─ YES: 【Caller-Side Boundary Promotion】Compiler promotes to Persistent Arena
     │      └─ NO : Stays in Scratch Arena
     │
[Loop End]   zp_scratch_reset(mark); // Instantly recycles all temporary memory
```

### Why "Caller-Side"?
Functions always return Scratch-backed data. The compiler tracks AST scope depth (`loop_depth`) and emits `zp_promote()` **only when the caller assigns the result to an outer-scope variable**. Calling string helper functions inside a loop creates **zero permanent memory accumulation**.

---

## Installation & Getting Started

### 1. One-Liner Install
```bash
git clone https://github.com/coldleaf0124/kaniscript.git
cd kaniscript
./install.sh
```

### 2. Python Package Install
```bash
pip install -e .
```

### 3. Run & Compile
```bash
# Run directly
kani run examples/01_hello.ks
ks run examples/02_fibonacci.ks

# Compile to native binary (-O3 optimized)
kani build examples/04_csv_aggregator.ks -o aggregator
./aggregator
```

---

## Testing

KaniScript includes a 44-test regression suite covering lexing, parsing, type checking, memory boundaries, and E2E execution:

```bash
python3 tests/test_all.py
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
