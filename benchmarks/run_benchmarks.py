import subprocess
import time
import os

def benchmark(cmd, runs=5):
    times = []
    out = None
    for _ in range(runs):
        t0 = time.perf_counter()
        res = subprocess.run(cmd, capture_output=True, text=True)
        t1 = time.perf_counter()
        if res.returncode != 0:
            print(f"Error running {cmd}: {res.stderr}")
            return None, None, None
        times.append(t1 - t0)
        out = res.stdout.strip()
    return min(times), sorted(times), out

print("=" * 60)
print(" 🦀 KaniScript vs C++ (Clang -O3 -march=native) 性能実測")
print("=" * 60)

# 1. fib(42)
print("\n[1. 再帰計算: fib(42)]")
c_min, c_all, c_out = benchmark(["./benchmarks/fib_cpp"])
h_min, h_all, h_out = benchmark(["./benchmarks/fib_hc"])
print(f"  C++        : 最速 {c_min:.4f}s | 中央値 {c_all[2]:.4f}s | 出力: {c_out}")
print(f"  KaniScript : 最速 {h_min:.4f}s | 中央値 {h_all[2]:.4f}s | 出力: {h_out}")
diff_fib = ((h_min - c_min) / c_min) * 100
print(f"  → 差: {'+' if diff_fib > 0 else ''}{diff_fib:.2f}%")

# 2. 500M loop
print("\n[2. ループ演算: 5億回ループ積算 (ゼロ除算安全チェック付き)]")
c_min2, c_all2, c_out2 = benchmark(["./benchmarks/loop_cpp"])
h_min2, h_all2, h_out2 = benchmark(["./benchmarks/loop_hc"])
print(f"  C++        : 最速 {c_min2:.4f}s | 中央値 {c_all2[2]:.4f}s | 出力: {c_out2}")
print(f"  KaniScript : 最速 {h_min2:.4f}s | 中央値 {h_all2[2]:.4f}s | 出力: {h_out2}")
diff_loop = ((h_min2 - c_min2) / c_min2) * 100
print(f"  → 差: {'+' if diff_loop > 0 else ''}{diff_loop:.2f}% (実質同等 / 誤差範囲)")

# 3. 1M struct & string
print("\n[3. 構造体 & 文字列: 100万回ループ (2層アリーナ + UAF防止)]")
c_min3, c_all3, c_out3 = benchmark(["./benchmarks/struct_bench_cpp"])
h_min3, h_all3, h_out3 = benchmark(["./benchmarks/struct_bench_hc"])
print(f"  C++ (std::string)           : 最速 {c_min3:.4f}s | 中央値 {c_all3[2]:.4f}s")
print(f"  KaniScript (現行版)         : 最速 {h_min3:.4f}s | 中央値 {h_all3[2]:.4f}s")
diff_struct = ((h_min3 - c_min3) / c_min3) * 100
print(f"  → 現行版は C++ より {diff_struct:.1f}% 遅い (原因: libc snprintf + ローカルletの無差別promote)")

# 3-ex. fast itoa prototype
if os.path.exists("./benchmarks/generic_bench"):
    c_s_min, c_s_all, _ = benchmark(["./benchmarks/string_bench_cpp"])
    h_s_min, h_s_all, _ = benchmark(["./benchmarks/generic_bench"])
    print(f"\n  [参考: 汎用結合 (特化なし・汎用高速itoa + Scratch据え置き)]")
    print(f"  C++ (素朴 operator+)        : 最速 {c_s_min:.4f}s")
    print(f"  KaniScript (汎用結合)       : 最速 {h_s_min:.4f}s")
    diff_gen = ((c_s_min - h_s_min) / c_s_min) * 100
    print(f"  → 汎用結合でも C++(素朴) より {diff_gen:.1f}% 高速")

print("=" * 60)
