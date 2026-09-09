# KaniScript Memory Model: Two-Layer Arena & Caller-Side Boundary Promotion

KaniScript operates without a tracing garbage collector (GC) and without explicit borrow-checker lifetime annotations (like Rust). This document explains the underlying memory architecture, its design rationale, safety guarantees, and current limitations.

---

## 1. The Core Philosophy: Why No GC?

In traditional systems programming:
- **Tracing GC (Go, Python, Java)**: Periodically scans the entire object graph. This causes CPU spikes, memory bloat (often 2x–3x actual working set), and non-deterministic pause times.
- **Manual Allocation (C, C++)**: Calling `malloc()` / `free()` per string or struct causes heap fragmentation, cache misses, and lock contention in multithreaded allocators.
- **Compile-Time Borrow Checking (Rust)**: Extremely safe and performant, but introduces substantial cognitive burden (lifetimes, Pin, RefCell) for everyday scripting.

KaniScript adopts a technique widely used in high-frequency trading (HFT) and game engines: **Arena Allocation with LIFO Rewinding**, elevated to a first-class language semantic.

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

1. **Functions always return Scratch memory**: `make_label` constructs `"item_1"` in the Scratch arena and returns the raw pointer. It never allocates from Persistent memory.
2. **The compiler tracks AST scope depth (`loop_depth`)**:
   - Depth 0: Function top-level.
   - Depth > 0: Inside an `each` or `while` loop.
3. **Promotion only occurs across scope boundaries**:
   - If `lbl` is assigned to a variable defined *outside* the current loop, the compiler inserts `zp_promote()`:
     ```c
     // If escaping:
     outer_str = zp_promote(lbl);
     ```
   - If `lbl` is merely a local variable inside the loop, **no promotion occurs**:
     ```c
     // Inside loop (local):
     const char* lbl = make_label(i); // Remains on Scratch
     ```
   - At the end of the iteration, `zp_scratch_reset(mark)` instantly recycles `lbl`.

**Result**: In this loop pattern, temporary per-iteration allocations yield **0 bytes of Persistent arena growth** over 1,000,000 iterations.

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
