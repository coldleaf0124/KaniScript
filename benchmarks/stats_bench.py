import subprocess
import time
import statistics

def run_bench_stats(cmd, runs=20):
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        r = subprocess.run(cmd, capture_output=True, text=True)
        t1 = time.perf_counter()
        assert r.returncode == 0, r.stderr
        times.append(t1 - t0)
    valid = times[1:]  # ウォームアップ除外
    return {
        "min": min(valid),
        "mean": statistics.mean(valid),
        "median": statistics.median(valid),
        "stdev": statistics.stdev(valid),
        "runs": len(valid)
    }

print("=== 20回試行 統計ベンチマーク (N=19, 初回ウォームアップ除外) ===")

print("\n1. 文字列結合 100万回 (素朴コード)")
c_str = run_bench_stats(["./benchmarks/string_bench_cpp"])
k_str = run_bench_stats(["./benchmarks/string_bench_kani"])
print("  C++ Naive   : min={:.4f}s | mean={:.4f}s ± {:.4f}s | median={:.4f}s".format(
    c_str['min'], c_str['mean'], c_str['stdev'], c_str['median']))
print("  KaniScript  : min={:.4f}s | mean={:.4f}s ± {:.4f}s | median={:.4f}s".format(
    k_str['min'], k_str['mean'], k_str['stdev'], k_str['median']))
diff_str = ((c_str["mean"] - k_str["mean"]) / c_str["mean"]) * 100
print(f"  → 平均値比較: KaniScript が {diff_str:+.1f}% 高速")

print("\n2. 構造体生成 & エスケープ 100万回")
c_st = run_bench_stats(["./benchmarks/struct_bench_cpp"])
k_st = run_bench_stats(["./benchmarks/struct_bench_kani"])
print("  C++ struct  : min={:.4f}s | mean={:.4f}s ± {:.4f}s | median={:.4f}s".format(
    c_st['min'], c_st['mean'], c_st['stdev'], c_st['median']))
print("  KaniScript  : min={:.4f}s | mean={:.4f}s ± {:.4f}s | median={:.4f}s".format(
    k_st['min'], k_st['mean'], k_st['stdev'], k_st['median']))
diff_st = ((c_st["mean"] - k_st["mean"]) / c_st["mean"]) * 100
print(f"  → 平均値比較: KaniScript が {diff_st:+.1f}% 高速")
