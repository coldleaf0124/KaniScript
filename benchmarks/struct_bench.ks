struct SaleItem {
    name: str,
    price: i64,
    qty: i64
}

main() {
    best := SaleItem("", 0, 0)
    total_sales := 0
    each i in 1..1000001 {
        p := (i % 100) + 10
        q := (i % 5) + 1
        n := "item_" + int_to_str(i)
        item := SaleItem(n, p, q)
        total := item.price * item.qty
        total_sales += total
        when total > (best.price * best.qty) {
            best = item
        }
    }
    out "total="
    out total_sales
    out "best="
    out best.name
}
