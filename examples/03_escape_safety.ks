// KaniScript メモリ安全性・エスケープ検証テスト (Boundary Promotion Test)
// 目的: ループごとの Scratch 巻き戻し下で、あらゆるエスケープ経路で UAF (Use-After-Free) が起きず、
// かつ不要なメモリ蓄積 (Perm 枯渇) が起きないことを検証する。

struct Item {
    name: str,
    price: i64
}

// 1. 関数からの文字列脱出
make_label(n: i64) -> str {
    "item_" + int_to_str(n)
}

// 2. 関数からの struct (文字列フィールド含む) 脱出
make_item(n: i64, p: i64) -> Item {
    Item("item_" + int_to_str(n), p)
}

main() {
    out "=== Safety Test 1: if分岐内での外側変数エスケープ ==="
    saved_str := ""
    each i in 1..10001 {
        tmp := "label_" + int_to_str(i)
        when i == 10000 {
            saved_str = tmp  // if分岐内での外側スコープ代入
        }
    }
    out "saved_str (expected: label_10000):"
    out saved_str

    out "=== Safety Test 2: if分岐内での外側struct代入エスケープ ==="
    best_item := Item("", 0)
    each i in 1..10001 {
        item := Item("prod_" + int_to_str(i), i * 10)
        when i == 10000 {
            best_item = item // if分岐内での外側struct代入
        }
    }
    out "best_item.name (expected: prod_10000):"
    out best_item.name
    out "best_item.price (expected: 100000):"
    out best_item.price

    out "=== Safety Test 3: ネストループからの多段エスケープ ==="
    nested_str := ""
    each i in 1..11 {
        each j in 1..11 {
            cell := "cell_" + int_to_str(i) + "_" + int_to_str(j)
            when i == 10 {
                when j == 10 {
                    nested_str = cell // 2重ループの底から最外周へ脱出
                }
            }
        }
    }
    out "nested_str (expected: cell_10_10):"
    out nested_str

    out "=== Safety Test 4: 関数戻り値経由のエスケープ ==="
    fn_ret_str := make_label(777)
    out "fn_ret_str (expected: item_777):"
    out fn_ret_str

    fn_ret_item := make_item(888, 9999)
    out "fn_ret_item.name (expected: item_888):"
    out fn_ret_item.name
    out "fn_ret_item.price (expected: 9999):"
    out fn_ret_item.price

    out "✓ All escape boundary tests completed successfully!"
}
