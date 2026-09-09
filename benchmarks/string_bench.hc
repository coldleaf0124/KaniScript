main() {
    last := ""
    each i in 1..1000001 {
        s := "item_id_" + int_to_str(i)
        when i == 1000000 {
            last = s
        }
    }
    out "last="
    out last
}
