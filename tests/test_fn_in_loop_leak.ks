make_label(i: i64) -> str {
    "label_" + int_to_str(i)
}

main() {
    total_len := 0
    each i in 1..1000001 {
        // ループ内で文字列を返すヘルパー関数を毎周呼び出す (一時変数)
        lbl := make_label(i)
        total_len += len(lbl)
    }
    out "Finished 1,000,000 iterations. total_len:"
    out total_len
}
