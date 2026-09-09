# Changelog

All notable changes to **KaniScript** will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-09

### Added
- **Minimalist Syntax**: Keyword-less function definitions (`add(a: i64, b: i64) -> i64`), short declaration (`:=`), parentheses-free `out`, `when-else`, and `each` loop expressions.
- **2-Layer Arena Memory Architecture**: High-speed Scratch arena with LIFO pointer rewinds and Persistent arena for surviving data.
- **Caller-Side Boundary Promotion**: Static compiler tracking of AST scope depth to eliminate function-in-loop memory leaks.
- **Dynamic Slices & Operations**: Built-in support for `[]str` and `[]i64`, slicing, dynamic indexing (`list[i]`), and `len(slice)`.
- **Practical Standard Library**:
  - File I/O: `read_file`, `write_file`
  - String manipulation: `split`, `trim`, string equality (`==`, `!=`)
  - Numeric conversions: `parse_i64`, `parse_f64`, `int_to_str`, `float_to_str`
  - Diagnostics & timing: `time_now()`, `perm_used()`, `scratch_used()`
- **CLI Suite**:
  - `kani run <file.ks>`: Instant compilation and execution
  - `kani build <file.ks>`: Native binary compilation with Clang -O3
  - `kani init [name.ks]`: Interactive tutorial template generator
  - `kani cheat`: 30-second ANSI color terminal cheat sheet
  - `kani --version`: Version inspection
- **Developer Tools**:
  - VS Code extension with syntax highlighting, brackets, and language configuration (`editors/vscode/`)
  - Reproducible 1,000,000 rows CSV aggregation benchmark suite (`benchmarks/`)
  - 44-test automated test suite (`tests/test_all.py`)
