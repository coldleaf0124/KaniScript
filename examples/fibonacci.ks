// Zenpo フィボナッチ数列 — 速度テスト用
fn fib(n: i64) -> i64 {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

fn main() {
    let result = fib(40)
    println(int_to_str(result))
}
