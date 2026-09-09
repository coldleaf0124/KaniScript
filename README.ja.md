<div align="center">

# <img src="assets/kaniscript_icon.svg" width="48" height="48" alt="KaniScript Logo" style="vertical-align: middle;" /> KaniScript (日本語)

**Pythonライクな手軽さで、GCなしのネイティブ速度と新メモリモデルを実験する自作プログラミング言語**

[English](README.md) | [日本語 (Japanese)](README.ja.md)

<br>

> *KaniScript is human-designed and primarily human-written, with AI used for code review, refinement, and development assistance.*<br>
> *(KaniScript は人間が設計し、主に人間が執筆したものであり、AI はコードレビュー、推敲、および開発支援として活用されています)*

</div>

---

## KaniScript の完全独自構文

| 機能 | 従来の言語 (Rust / C++ / Python) | **KaniScript** |
|---|---|---|
| **関数定義** | `fn add(...)` / `def add(...)` | **`add(a: i64, b: i64) -> i64 { a + b }`**（キーワード不要） |
| **変数宣言** | `let mut x = 10;` / `x = 10` | **`x := 10`**（コロンイコール一撃） |
| **出力** | `println!(...)` / `print(...)` | **`out "Hello, World"`**（カッコすら不要） |
| **条件分岐** | `if ... else ...` | **`when total > 100 { ... } else { ... }`** |
| **ループ** | `for i in range(...):` | **`each i in 0..10 { ... }`** |
| **返り値** | `return a + b;` | **式をそのまま置く暗黙return** |

---

## 100万行 CSV 集計ベンチマーク

Apple M2 (macOS arm64, Clang -O3, Python 3.14, N=10試行平均) における実測値:

| 言語 / 実装方式 | 実行時間 (平均) | vs Python | Peak RSS | 実質行数 | ループ一時値リーク |
|---|---|---|---|---|---|
| **Python 3.14 (Standard)** | 0.4239s | 1.00x | 14.5 MB | 31行 | N/A (GC) |
| **C++ Clang -O3 (素朴な `ifstream` + `string`)** | 0.2085s | 2.03x | 1.6 MB | 42行 | 0 B (手動Free) |
| **KaniScript (2層アリーナ + スライス)** | **0.1440s** | **2.94x** | 196.0 MB | 41行 | **0 B (完全回収)** |
| **C++ Clang -O3 (手動最適化 `string_view` + `charconv`)** | 0.0790s | 5.37x | 29.1 MB | 49行 | 0 B (ゼロアロケーション) |

- **素朴なC++より31%高速**: アリーナポインタ加算とLIFO巻き戻しにより、毎行のヒープ割り当てオーバーヘッドを排除。
- **手書き最適化C++には及ばない (0.1440s vs 0.0790s)**: 手書きゼロコピーC++には及びませんが、Pythonライクな平易な記述でネイティブ性能に肉薄。
- **反復ごとの一時値による永続領域増加 0 Bytes**: このループパターンにおいて、Caller-Side Boundary Promotion によりループ内の純粋な一時値が永続領域へ蓄積することを防ぎます。

---

## インストール & 使い方

```bash
# クローン
git clone https://github.com/coldleaf0124/kaniscript.git
cd kaniscript

# インストール
./install.sh

# 実行
kani run examples/01_hello.ks
ks run examples/02_fibonacci.ks

# ネイティブバイナリへビルド
kani build examples/04_csv_aggregator.ks -o aggregator
./aggregator
```

---

## ライセンス

MIT License
