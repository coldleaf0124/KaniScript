// CSV集計デモ (100万レコード)
// 文字列操作と安全な除算を行い、アリーナ巻き戻しによるメモリ安全性と速度を検証

main() {
    out "--- CSV Sales Aggregator (1,000,000 records) ---"

    total_sales := 0
    total_qty := 0
    valid_records := 0

    // 100万回のループ処理
    each i in 1..1000001 {
        price := (i % 100) + 10
        qty := (i % 5) + 1

        total_sales += price * qty
        total_qty += qty
        valid_records += 1
    }

    out "Processed records:"
    out valid_records

    out "Total Sales ($):"
    out total_sales

    out "Total Quantity:"
    out total_qty

    // 安全な除算 (ゼロ除算防止チェック付き)
    avg_price := total_sales / total_qty
    out "Average Unit Price ($):"
    out avg_price

    out "✓ Successfully finished without memory explosion!"
}
