def compute(n: i64) -> i64 {
    var sum: i64 = 0
    for i in 0..n {
        var x: i64 = i % 10
        sum += x * 3 - (i % 5)
    }
    sum
}

def main() {
    println(compute(500000000))
}
