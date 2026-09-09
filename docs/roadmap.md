# KaniScript Roadmap & Known Limitations

This document tracks the technical evolution of KaniScript, explicitly detailing known limitations in v0.1 and planned architectural solutions for v0.2 and beyond.

---

## 🗺️ Roadmap Overview

```
v0.1.0 (Current) ──────▶ v0.2.0 (Planned) ──────▶ v0.3.0 (Future)
- 2-Layer Arena           - Bounds-checking panics  - Thread-local Arenas
- Caller-Side Promotion   - Streaming file iterators - Parallel execution
- Minimalist Syntax       - Struct method syntax    - LSP & Debugger
- 44-Test Suite           - Self-hosting parser     - Package manager
```

---

## 📌 v0.2.0 Milestones

### 1. Spatial Memory Safety (Array & Slice Bounds Checking)
- **Current State (v0.1)**:
  Index expressions (`list[i]`) compile to direct C array access (`list.data[i]`). Out-of-bounds indexing causes undefined behavior at the C level.
- **Planned Solution (v0.2)**:
  The compiler will emit a branch with a safe panic if `(size_t)i >= list.len`:
  ```c
  if (__builtin_expect((size_t)i >= list.len, 0)) {
      zp_panic_bounds("Slice index out of bounds", __FILE__, __LINE__);
  }
  ```
- **Target**: Zero undefined behavior on out-of-bounds array access.

---

### 2. Streaming Line Iterator (Reducing Peak RSS from 196 MB)
- **Current State (v0.1)**:
  Ingesting 28.4 MB of CSV currently splits all 1,000,000 lines upfront into memory (`split(content, "\n")`), causing ~196 MB peak RSS due to slice metadata and whole-buffer retention.
- **Planned Solution (v0.2)**:
  Introduce a lazy streaming file iterator:
  ```rust
  each line in file_lines("data/sales_1m.csv") {
      // Processes line-by-line without buffering 1M rows
      fields := split(line, ",")
  }
  ```
- **Target**: Keep 1,000,000-row peak RSS under 15 MB (matching or beating Python and standard C++).

---

### 3. Extended Escape Analysis
- **Current State (v0.1)**:
  Caller-Side Boundary Promotion currently analyzes outer-scope variable assignments, function returns, and direct struct fields.
- **Planned Solution (v0.2)**:
  Deeper escape tracking through nested containers (e.g. slices of slices, dynamic maps) to ensure promotions propagate deeply across arbitrary nesting levels.

---

## 📌 v0.3.0 Milestones

### 4. Thread-Local Scratch Arenas
- **Current State (v0.1)**:
  `g_zp_scratch` and `g_zp_perm` are process-global, limiting execution to single-threaded workloads.
- **Planned Solution (v0.3)**:
  Thread-local storage (`_Thread_local` / `thread_local`) for the Scratch arena, allowing concurrent workers to process batches independently without lock contention or allocation stalls.

---

## 🤝 Contributing

We welcome RFCs, issue reports, and pull requests! See [CONTRIBUTING.md](../CONTRIBUTING.md) to get involved.
