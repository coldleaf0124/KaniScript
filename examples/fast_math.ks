def fast_fib(n: i64) -> i64 {
    if n <= 1 {
        return n
    }
    fast_fib(n - 1) + fast_fib(n - 2)
}

def fast_sum(n: i64) -> i64 {
    var total: i64 = 0
    for i in 0..n {
        total += i
    }
    total
}
