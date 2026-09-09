// 再帰関数と文字列処理の安全性検証テスト

build_path(depth: i64) -> str {
    when depth <= 0 {
        return ""
    }
    when depth == 1 {
        return "root"
    }
    return "node_" + int_to_str(depth) + "/" + build_path(depth - 1)
}

main() {
    out "=== Recursive String Test ==="
    path := build_path(5)
    out "Path depth 5:"
    out path

    // 深い再帰 (深さ 50)
    deep_path := build_path(50)
    out "Deep path length:"
    out len(deep_path)

    out "✓ Recursive string processing survived without memory corruption!"
}
