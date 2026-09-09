// Zenpo ループと演算デモ
fn sum_to(n: i64) -> i64 {
    let mut total: i64 = 0
    for i in 0..n {
        total += i
    }
    return total
}

fn fizzbuzz(n: i64) {
    for i in 1..n {
        if i % 15 == 0 {
            println("FizzBuzz")
        } else if i % 3 == 0 {
            println("Fizz")
        } else if i % 5 == 0 {
            println("Buzz")
        } else {
            println(int_to_str(i))
        }
    }
}

fn main() {
    let s = sum_to(100)
    print("Sum 0..100 = ")
    println(int_to_str(s))
    fizzbuzz(20)
}
