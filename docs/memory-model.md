# KaniScript Memory Model: Two-Layer Arena & Caller-Side Boundary Promotion

KaniScript operates without a tracing garbage collector (GC) and without explicit borrow-checker lifetime annotations (like Rust). This document explains the underlying memory architecture, its design rationale, safety guarantees, and current limitations.

---

## 1. The Core Philosophy: Why an Alternative Memory Model?

In traditional systems programming:
- **Managed Runtimes (e.g. Go, Python, Java)**: Highly productive, but runtime memory management can introduce allocation, scanning, or collection overhead under data-intensive loops.
- **Manual Heap Allocation (C, C++)**: Calling `malloc()` / `free()` per string or struct risks heap fragmentation, cache misses, and manual lifecycle bugs (use-after-free, double-free).
- **Ownership & Borrow Checking (Rust)**: Provides strong compile-time guarantees without GC, but ownership and lifetime rules can add cognitive overhead for scripting-style workloads.

KaniScript explores an alternative paradigm: **Arena Allocation with LIFO Rewinding combined with Compiler-Directed Caller-Side Boundary Promotion**, bringing seamless scripting simplicity without runtime GC or manual lifetime annotations.

---

## 2. Two-Layer Arena Architecture

KaniScript divides process memory into two continuous memory buffers:

```
+---------------------------------------------------------------+
|                       KaniScript Memory                       |
+---------------------------------------------------------------+
| 1. Scratch Arena (Temporary Workspace)                        |
|    - Used for: string concatenation, split tokens, temp math  |
|    - Allocation: simple pointer increment (ptr += aligned)   |
|    - Deallocation: LIFO rewind (offset = mark) per loop       |
+---------------------------------------------------------------+
                               │ (Only if escaping to outer scope)
                               ▼ 【Caller-Side Boundary Promotion】
+---------------------------------------------------------------+
| 2. Persistent Arena (Long-Lived Storage)                      |
|    - Used for: global state, outer variables, structs         |
|    - Survives until process exit                              |
+---------------------------------------------------------------+
```

### 1. Scratch Arena
- Every temporary allocation inside an expression or loop comes from the Scratch arena.
- Allocation is a **bump-pointer advance** (`offset += size`) with a capacity check, avoiding the locking, bin searches, and heap metadata overhead of general-purpose `malloc()`.
- When an `each` loop completes an iteration, the allocator rewinds the offset to the iteration's watermark (`offset = mark`).
- **Deallocation cost is amortized zero per object.** Instead of traversing individual heap objects or running destructors, millions of intermediate allocations are discarded simultaneously in a single pointer rewind.

### 2. Persistent Arena
- Data that must survive beyond the current loop iteration or function lifecycle is stored here.
- Backed by dynamic virtual memory doubling.

---

## 3. The Classic Problem: Function Leaks Inside Loops

Consider this common code pattern:

```rust
make_label(i: i64) -> str {
    "item_" + int_to_str(i)
}

main() {
    total := 0
    each i in 0..1000000 {
        lbl := make_label(i)
        total += len(lbl)
    }
}
```

If the compiler automatically promotes any returned string to the Persistent arena, **calling a helper function inside a 1,000,000-iteration loop leaks 1,000,000 strings into permanent memory**.

### The Solution: Caller-Side Boundary Promotion

KaniScript solves this by inverting the promotion responsibility from the *callee* to the *caller*:

```text
Function Returns
       │
       ▼
Raw Scratch pointer
       │
       ▼
Caller examines escape boundary:
┌──────────────────────────────────────────────┐
│ Case A: Local use inside loop                │ ──▶ Stays on Scratch (Recycled at iteration end)
│ Case B: Escapes to outer variable or struct  │ ──▶ Promote to Persistent Arena (zp_promote deep copy)
└──────────────────────────────────────────────┘
```

1. **Functions always return Scratch memory**: `make_label` constructs `"item_1"` in the Scratch arena and returns the raw pointer. It never allocates from Persistent memory.
2. **The compiler tracks AST scope depth (`loop_depth`)**:
   - Depth 0: Function top-level.
   - Depth > 0: Inside an `each` or `while` loop.
3. **Promotion only occurs across scope boundaries**:

#### Case A: Local Temporary (No Promotion)
```rust
// KaniScript Source
each i in 0..1000000 {
    lbl := make_label(i)
    total += len(lbl)
}
```
Lowers conceptually to:
```c
// Emitted C
for (int64_t i = 0; i < 1000000; ++i) {
    size_t mark = zp_scratch_mark();
    
    const char* lbl = make_label(i);    // Stays on Scratch
    total += zp_len_str(lbl);
    
    zp_scratch_reset(mark);              // Recycled in bulk!
}
```

#### Case B: Escaping to Outer Scope (Compiler Inserts Promotion)
```rust
// KaniScript Source
last_label := ""
each i in 0..1000000 {
    last_label = make_label(i)          // Assigned to variable outside loop!
}
```
Lowers conceptually to:
```c
// Emitted C
const char* last_label = "";
for (int64_t i = 0; i < 1000000; ++i) {
    size_t mark = zp_scratch_mark();
    
    const char* tmp = make_label(i);     // Returns raw Scratch pointer
    last_label = zp_promote(tmp);         // Compiler inserts: promoted to Persistent!
    
    zp_scratch_reset(mark);              // Scratch unwound; last_label safe in Perm!
}
```

**Result**: In this loop pattern, temporary per-iteration allocations yield **0 bytes of Persistent arena growth** over 1,000,000 iterations.

### Contrast with Rust's Borrow Checker

| Design Dimension | Rust Borrow Checker | KaniScript Caller-Side Promotion |
|---|---|---|
| **Programmer Burden** | Explicit ownership, borrowing rules, and lifetime annotations (`'a`, `&str`) | **Zero lifetime annotations** (syntax feels like Python or Go) |
| **Enforcement Point** | Compile-time static lifetime verification | Compiler-inserted promotion (`zp_promote`) at scope boundaries |
| **Trade-off** | Zero runtime memory footprint overhead, steep cognitive curve | Small deep-copy cost only when escaping, effortless scripting |

Instead of enforcing static lifetime constraints onto the user, KaniScript's compiler takes responsibility for observing scope boundaries and automatically promoting escaping data.

---

## 4. Arena Lifetime Guarantees (Scope of Safety in v0.1)

> [!IMPORTANT]
> **Distinction Between Arena Lifetime Safety and Universal Memory Safety**:
> KaniScript v0.1 provides **Arena Lifetime Safety** for managed strings, slices, and records across function and loop boundaries. It eliminates manual `free()`, double-free hazards, and scope-boundary use-after-free bugs through compiler-inserted promotion.
>
> However, **KaniScript is NOT yet a universally memory-safe language like Rust**. Low-level spatial memory safety features — specifically array bounds checking — are currently unchecked (compiling directly to C pointer indexing). Accessing an index beyond array bounds results in C undefined behavior until runtime bounds-checking panics are introduced in v0.2.

| Category | Guarantee in KaniScript v0.1 | Current Status & Technical Details |
|---|---|---|
| **Double Free** | **Eliminated by Design** | Developers never invoke `free()`. Memory reclamation is managed strictly through arena watermark resets. |
| **Arena Use-After-Free (UAF)** | **Prevented for Compiler-Tracked Escapes** | For assignments, returns, and struct fields analyzed by the compiler, values escaping across loop or function boundaries are automatically deep-copied (`zp_promote`) into the Persistent arena before the inner Scratch buffer is rewound, preventing dangling pointers. |
| **Division by Zero** | **Safe Runtime Panic** | `zp_div_i64` and `zp_mod_i64` abort with a descriptive diagnostic message rather than hardware trap faults. |
| **Array Bounds Checking** | **Unchecked (Work in Progress)** | Slice indexing `list[i]` currently compiles to direct C access (`list.data[i]`). Out-of-bounds indexing is undefined behavior in C (Bounds-checking panics are planned for v0.2). |
| **Raw Pointer Arithmetic** | **Not Exposed** | KaniScript syntax does not expose raw pointer arithmetic or arbitrary address manipulation to user code. |

---

## 5. Current Limitations & Roadmap

We believe in complete transparency about current architectural trade-offs:

1. **Memory Ingestion Peak (196 MB RSS on 28 MB Input)**:
   - Ingesting a 28 MB CSV and calling `split(content, "\n")` currently materializes all 1,000,000 line pointers in the Scratch arena, and then promotes the top-level slice into Persistent memory.
   - While leak-free, this uses more peak memory than stream-processing C++ (`std::ifstream`).
   - *Roadmap*: A streaming line iterator (`each line in file_lines("data.csv")`) is scheduled for v0.2.
2. **Array Bounds Checking**:
   - Slice indexing `list[i]` compiles to `list.data[i]`. Currently, out-of-bounds indexing triggers undefined behavior in C.
   - *Roadmap*: Runtime bounds check panics will be added in the next release.
3. **Single-Threaded Model**:
   - The Scratch and Persistent arenas are currently process-global.
   - *Roadmap*: Thread-local Scratch arenas for parallel execution.

---

## 6. Technical FAQ (Anticipated Systems Questions)

### Q1: How does recursion interact with the Scratch arena?
In recursive functions, intermediate string concatenations or slice calculations allocate linearly from the Scratch buffer. Because Scratch is an arena, these allocations never trigger individual `malloc()`/`free()` overhead. When the recursive call finishes and the caller assigns the result to a variable at an outer scope, boundary promotion copies the final result to Persistent memory, and Scratch can be unwound safely.

### Q2: What happens in nested loops?
Each loop level tracks its own scope depth (`loop_depth`). In nested loops:
- Inner loops acquire an inner watermark: `size_t mark_inner = zp_scratch_mark();`
- Temporaries created inside the inner loop are reclaimed at the end of each inner iteration.
- If an inner expression escapes to the outer loop's scope, the compiler emits promotion before the inner watermark resets.

### Q3: How deep does escape analysis go in v0.1?
v0.1 tracks AST scope depth across:
1. Variable assignments (`outer_var = local_expr`)
2. Return statements (`return local_expr`)
3. Struct field assignments (`my_struct.field = local_expr`)
4. Direct slice promotions (`zp_promote_slice`)

Indirect escapes through deeply nested dynamic maps or arbitrary pointer aliases are scheduled for formal escape graph analysis in v0.2.

### Q4: Why does the 1M-row benchmark consume 196 MB RSS?
KaniScript currently loads the 28.4 MB CSV into memory and calls `split(content, "\n")`. This creates 1,000,000 slice pointers in the Scratch arena, and then promotes the top-level slice array into Persistent memory. The arena memory is clean and leak-free, but holding all 1M row slices in memory simultaneously requires ~196 MB RSS. Introducing streaming line iterators (`each line in file_lines(...)`) in v0.2 will reduce RSS to under 15 MB.
