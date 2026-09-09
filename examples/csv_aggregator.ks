main() {
    start := time_now()

    path := "data/sales_1m.csv"
    content := read_file(path)
    trimmed := trim(content)
    lines := split(trimmed, "\n")
    n_lines := len(lines)

    total_qty := 0
    total_rev := 0.0
    target_qty := 0
    valid_rows := 0

    perm_before_loop := perm_used()

    each i in 0..n_lines {
        line := lines[i]
        cols := split(line, ",")
        when len(cols) == 5 {
            item := cols[1]
            qty := parse_i64(cols[2])
            price := parse_f64(cols[3])
            disc := parse_f64(cols[4])

            total_qty += qty
            total_rev += (qty * 1.0) * price * (1.0 - disc)
            when item == "Product_A" {
                target_qty += qty
            }
            valid_rows += 1
        }
    }

    perm_after_loop := perm_used()
    loop_leak := perm_after_loop - perm_before_loop

    elapsed := time_now() - start

    out "=== KaniScript 1,000,000 Rows CSV Aggregator ==="
    out "Rows: " + int_to_str(valid_rows)
    out "Total Qty: " + int_to_str(total_qty)
    out "Total Revenue: " + float_to_str(total_rev)
    out "Product_A Qty: " + int_to_str(target_qty)
    out "Elapsed: " + float_to_str(elapsed) + " s"
    out "Perm before loop: " + int_to_str(perm_before_loop) + " bytes"
    out "Perm after loop:  " + int_to_str(perm_after_loop) + " bytes"
    out "Loop Perm Leak:   " + int_to_str(loop_leak) + " bytes"
}
