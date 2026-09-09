# Getting Started with KaniScript

KaniScript is designed for zero-friction setup on macOS and Linux.

---

## 1. Installation

### Option A: One-Liner (Recommended)
Clone and run the installer:
```bash
git clone https://github.com/coldleaf0124/kaniscript.git
cd kaniscript
./install.sh
```

### Option B: Editable Python Package
```bash
pip install -e .
```

Verify your installation:
```bash
kani --version
# Output: KaniScript 0.1.0
```

---

## 2. Your First Program

Create a new project template with `kani init`:

```bash
kani init my_app.ks
```

This generates a runnable template:

```rust
// my_app.ks
add(a: i64, b: i64) -> i64 {
    a + b
}

main() {
    out "🦀 Hello from KaniScript!"
    x := 10
    y := 20
    out "x + y = " + int_to_str(add(x, y))
}
```

Run it immediately:
```bash
kani run my_app.ks
```

Output:
```text
🦀 Hello from KaniScript!
x + y = 30
```

---

## 3. Compiling to Standalone Native Binary

To produce an optimized native binary (via Clang -O3):

```bash
kani build my_app.ks -o my_app
./my_app
```

---

## 4. Useful CLI Commands

| Command | Description |
|---|---|
| `kani run <file.ks>` | Compile and run instantly in one step |
| `kani build <file.ks> -o <bin>` | Compile to standalone native binary |
| `kani init [name.ks]` | Generate a tutorial template |
| `kani cheat` | Display the 30-second color cheat sheet in terminal |
| `kani --version` | Display version information |
| `ks <cmd>` | Short alias for `kani` |
