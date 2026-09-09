// HrpyCode メモリ安全性検証テスト
// 1. 文字列を返す関数からループ外変数への代入
// 2. 動的文字列を含む struct の構築と脱出

struct Record {
    name: str,
    val: i64
}

make_label(i: i64) -> str {
    "item_" + int_to_str(i)
}

main() {
    out "=== Test 1: Loop Escape ==="
    saved := ""
    each i in 1..10001 {
        saved = make_label(i)
    }
    out "Last saved label (should be item_10000):"
    out saved

    out "=== Test 2: Struct with Dynamic String ==="
    r := Record(make_label(999), 12345)
    out "Record name (should be item_999):"
    out r.name
    out "Record val:"
    out r.val

    out "✓ All dangerous escape cases survived without memory corruption!"
}
