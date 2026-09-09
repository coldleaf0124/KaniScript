import sys
import time

def run():
    start = time.perf_counter()
    
    total_qty = 0
    total_rev = 0.0
    target_qty = 0
    count = 0

    with open("data/sales_1m.csv", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cols = line.split(",")
            if len(cols) == 5:
                qty = int(cols[2])
                price = float(cols[3])
                disc = float(cols[4])
                total_qty += qty
                total_rev += qty * price * (1.0 - disc)
                if cols[1] == "Product_A":
                    target_qty += qty
                count += 1

    elapsed = time.perf_counter() - start
    print(f"Rows: {count}")
    print(f"Total Qty: {total_qty}")
    print(f"Total Revenue: {total_rev:.2f}")
    print(f"Product_A Qty: {target_qty}")
    print(f"Elapsed: {elapsed:.4f} s")

if __name__ == "__main__":
    run()
