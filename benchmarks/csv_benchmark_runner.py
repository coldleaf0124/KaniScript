import subprocess
import time
import statistics
import os

TRIALS = 10

def get_peak_rss(cmd):
    # macOS time -l
    p = subprocess.Popen(["/usr/bin/time", "-l"] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, err = p.communicate()
    for line in err.decode("utf-8").splitlines():
        if "maximum resident set size" in line:
            return int(line.split()[0]) / (1024 * 1024)
    return 0.0

def measure_command(cmd):
    times = []
    for _ in range(TRIALS):
        start = time.perf_counter()
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        elapsed = time.perf_counter() - start
        if p.returncode != 0:
            raise RuntimeError(f"Command failed: {cmd}\n{err.decode('utf-8')}")
        times.append(elapsed)
    
    return {
        "mean": statistics.mean(times),
        "std": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "rss": get_peak_rss(cmd),
    }

def count_sloc(path):
    with open(path) as f:
        lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("//") and not l.strip().startswith("#")]
        return len(lines)

def main():
    print(f"=== 1,000,000 Rows CSV Aggregator Benchmark (N={TRIALS} trials) ===")
    print("Dataset: data/sales_1m.csv (28 MB, 1,000,000 rows, 5 columns)")
    print("Environment: Apple Silicon (macOS), Clang -O3, Python 3.12")
    print("-" * 85)
    
    configs = [
        ("Python 3.12 (Standard)", ["python3", "benchmarks/csv_aggregator.py"], "benchmarks/csv_aggregator.py", "N/A (GC)"),
        ("C++ Clang -O3 (std::ifstream / std::string)", ["./bin/csv_aggregator_cpp_std"], "benchmarks/csv_aggregator_std.cpp", "0 B (Manual Free)"),
        ("KaniScript (2-Layer Arena + Slices)", ["./bin/csv_aggregator_ks"], "examples/csv_aggregator.ks", "0 B (LIFO Reset)"),
        ("C++ Clang -O3 (Fast string_view / charconv)", ["./bin/csv_aggregator_cpp_fast"], "benchmarks/csv_aggregator_fast.cpp", "0 B (Zero-Alloc)"),
    ]
    
    data = []
    for name, cmd, src_path, leak_desc in configs:
        print(f"Running {name} ...")
        res = measure_command(cmd)
        sloc = count_sloc(src_path)
        data.append((name, res["mean"], res["std"], res["min"], res["rss"], sloc, leak_desc))
    
    py_mean = data[0][1]
    
    print("\n" + "=" * 96)
    header = f"{'Language / Implementation':<38} | {'Mean Time':<10} | {'vs Py':<6} | {'Peak RSS':<9} | {'SLOC':<5} | {'Temp Leak in Loop'}"
    print(header)
    print("-" * 96)
    for name, mean_t, std_t, min_t, rss, sloc, leak in data:
        speedup = f"{py_mean / mean_t:.2f}x"
        time_str = f"{mean_t:.4f}s"
        rss_str = f"{rss:.1f} MB"
        print(f"{name:<38} | {time_str:<10} | {speedup:<6} | {rss_str:<9} | {sloc:<5} | {leak}")
    print("=" * 96)

if __name__ == "__main__":
    main()
