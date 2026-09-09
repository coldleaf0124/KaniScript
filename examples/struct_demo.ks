// KaniScript Struct & Memory Arena Demo
// 構造体の値渡し、フィールドアクセス、およびループ内での文字列操作とアリーナ巻き戻しを実証

struct SaleItem {
    name: str,
    price: i64,
    quantity: i64
}

calc_total(item: SaleItem) -> i64 {
    item.price * item.quantity
}

main() {
    out "=== KaniScript Struct & Memory Test ==="

    // 1. 構造体のインスタンス化 (値セマンティクス)
    apple := SaleItem("Apple", 120, 3)
    banana := SaleItem("Banana", 80, 5)

    out "Item 1 total:"
    out calc_total(apple)

    out "Item 2 total:"
    out calc_total(banana)

    // 2. 文字列操作を含むループ (アリーナ巻き戻しが毎周自動実行される)
    total_batch_price := 0
    each i in 1..10001 {
        // 毎周一時文字列を作成
        item := SaleItem("Product", i % 50 + 10, 2)
        total_batch_price += calc_total(item)
    }

    out "Batch processing 10,000 items total:"
    out total_batch_price
    out "✓ Structs and memory arena working seamlessly!"
}
