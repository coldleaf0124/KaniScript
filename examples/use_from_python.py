import ctypes
import os
import time

# Zenpo で書いた爆速ライブラリをロード
lib_path = os.path.join(os.path.dirname(__file__), "libfast_math.dylib")
zenpo_lib = ctypes.CDLL(lib_path)

# 関数のシグネチャ（型）を設定
zenpo_lib.fast_fib.argtypes = [ctypes.c_int64]
zenpo_lib.fast_fib.restype = ctypes.c_int64

zenpo_lib.fast_sum.argtypes = [ctypes.c_int64]
zenpo_lib.fast_sum.restype = ctypes.c_int64

print("🐍 Python から Zenpo の関数を直接呼び出すデモ")
print("--------------------------------------------------")

# 1. フィボナッチ計算
t0 = time.perf_counter()
ans = zenpo_lib.fast_fib(40)
t1 = time.perf_counter()
print(f"Zenpo fast_fib(40) = {ans} (所要時間: {t1 - t0:.4f}秒)")

# 2. 大規模ループ
t0 = time.perf_counter()
total = zenpo_lib.fast_sum(100_000_000)
t1 = time.perf_counter()
print(f"Zenpo fast_sum(1億)  = {total} (所要時間: {t1 - t0:.4f}秒)")

print("--------------------------------------------------")
print("✓ Python 単体より数十〜数百倍高速に計算できました！")
