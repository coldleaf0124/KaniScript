main() {
    path := "data/test_io.txt"
    sample := "apple, 100, 1.5\nbanana, 200, 2.75\ncherry, 300, 3.25\n"

    // 1. File write
    ok := write_file(path, sample)
    when ok {
        out "write_file OK"
    } else {
        out "write_file FAILED"
    }

    // 2. File read
    read_data := read_file(path)
    trimmed := trim(read_data)
    out "File read length: " + int_to_str(len(trimmed))

    // 3. Split by newline
    lines := split(trimmed, "\n")
    n_lines := len(lines)
    out "Line count: " + int_to_str(n_lines)

    total_qty := 0
    total_val := 0.0

    // 4. Iterate and parse
    each i in 0..n_lines {
        line := lines[i]
        cols := split(line, ",")
        when len(cols) == 3 {
            item := trim(cols[0])
            qty := parse_i64(cols[1])
            price := parse_f64(cols[2])

            total_qty += qty
            total_val += price * 1.0

            out "Parsed: " + item + " qty=" + int_to_str(qty)
        }
    }

    out "Total Qty: " + int_to_str(total_qty)
    when total_qty == 600 {
        out "ALL PRACTICAL FEATURES VERIFIED"
    } else {
        out "VERIFICATION FAILED"
    }
}
