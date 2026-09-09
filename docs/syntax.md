# KaniScript Syntax Reference

KaniScript strips away boilerplate keywords while maintaining strict static typing and explicit contracts.

---

## 1. Variables

Use `:=` for type-inferred variable declaration:

```rust
count := 42            // i64 (default integer)
rate := 0.05           // f64 (default float)
name := "Kani"         // str
active := true         // bool
```

Mutable re-assignment uses standard `=`:
```rust
count := 0
count = count + 1
count += 10
```

---

## 2. Functions

Functions require no `fn` or `def` keyword. The return type is indicated by `->`. The last evaluated expression is implicitly returned.

```rust
// Implicit return
square(x: i64) -> i64 {
    x * x
}

// Explicit return
abs_val(x: i64) -> i64 {
    when x < 0 { return -x }
    x
}

// Void function
greet(name: str) {
    out "Hello, " + name
}
```

---

## 3. Control Flow

### `when` - `else`
```rust
when score >= 90 {
    out "Grade: A"
} else when score >= 80 {
    out "Grade: B"
} else {
    out "Grade: C"
}
```

### `each` Loop
Loops over half-open integer ranges `start..end`:

```rust
each i in 0..5 {
    out i // Prints 0, 1, 2, 3, 4
}
```

---

## 4. Dynamic Slices

Slices represent dynamically sized lists (`[]str`, `[]i64`):

```rust
lines := split("apple\nbanana\ncherry", "\n")

n := len(lines)          // Element count (i64)
first := lines[0]        // Index access
out first                // "apple"
```

---

## 5. Built-in Standard Library

### File I/O
```rust
content := read_file("input.txt")
ok := write_file("output.txt", "content")
```

### String Operations
```rust
trimmed := trim("  hello  ")
parts := split("a,b,c", ",")
when parts[0] == "a" { out "match!" }
```

### Conversions
```rust
n := parse_i64("123")
f := parse_f64("3.14")
s1 := int_to_str(100)
s2 := float_to_str(2.718)
```

### Diagnostics & Timing
```rust
start := time_now()       // High-resolution timestamp (f64 seconds)
perm := perm_used()       // Persistent arena bytes used (i64)
scratch := scratch_used() // Scratch arena bytes used (i64)
```
