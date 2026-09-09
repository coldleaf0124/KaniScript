// KaniScript 完全独自構文デモ
// PythonにもC++にもRustにも似ていない、究極に簡単で速い言語！

// 1. キーワードなし関数定義
fib(n: i64) -> i64 {
    when n <= 1 { return n }
    fib(n - 1) + fib(n - 2)
}

square(x: i64) -> i64 {
    x * x
}

// 2. メイン関数
main() {
    out "🚀 Welcome to KaniScript!"

    // 3. := で一撃変数宣言
    total := 0

    // 4. each ループ
    each i in 0..5 {
        total += square(i)
    }

    out "Sum of squares 0..4:"
    out total

    // 5. when 条件文
    when total > 20 {
        out "Total is big!"
    } else {
        out "Total is small!"
    }

    out "Fibonacci(40):"
    out fib(40)
}
