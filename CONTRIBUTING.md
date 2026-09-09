# Contributing to KaniScript

Thank you for your interest in contributing to **KaniScript**! We welcome bug reports, feature requests, syntax enhancements, and performance optimizations.

## Getting Started

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/coldleaf0124/kaniscript.git
   cd kaniscript
   ```

2. Run the test suite to ensure your environment is working:
   ```bash
   python3 tests/test_all.py
   ```

3. Install in editable mode:
   ```bash
   pip install -e .
   ```

## Development Guidelines

- **Minimalist Syntax**: Keep the language free of unnecessary keywords. Features should be intuitive and readable.
- **Memory Safety First**: Any new feature involving allocations must respect the 2-layer arena architecture (`Scratch` vs `Persistent`) and `Caller-Side Boundary Promotion`.
- **Unit Tests**: Always add test cases in `tests/` and register them in `tests/test_all.py`.
- **Regression Checks**: Ensure all existing 44 tests and escape safety tests pass without leaks before opening a Pull Request.

## Pull Request Process

1. Create a feature branch (`git checkout -b feature/my-feature`).
2. Make your changes and run `python3 tests/test_all.py`.
3. Commit with clear, descriptive commit messages.
4. Push to your branch and open a Pull Request.
