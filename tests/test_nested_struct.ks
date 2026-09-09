struct Item {
    name: str,
    price: i64
}

struct Order {
    item: Item,
    quantity: i64
}

main() {
    out "=== Nested Struct Escape Test ==="
    best_order := Order(Item("", 0), 0)

    each i in 1..10001 {
        it := Item("prod_" + int_to_str(i), i * 10)
        ord := Order(it, i % 5 + 1)
        when i == 10000 {
            best_order = ord // 入れ子構造体の脱出！
        }
    }

    out "best_order.item.name (expected: prod_10000):"
    out best_order.item.name
    out "best_order.item.price (expected: 100000):"
    out best_order.item.price
    out "best_order.quantity (expected: 1):"
    out best_order.quantity

    out "✓ Nested struct escape survived without memory corruption!"
}
