// シンプル構文デモ — KaniScript
// def, var, 暗黙return, スマートprint を使う

def greet(name: str) {
    print("Hello, ")
    println(name)
}

def add(a: i64, b: i64) -> i64 {
    a + b   // returnいらない！最後の式が自動でreturn
}

def square(n: i64) -> i64 {
    n * n   // 超シンプル！
}

def main() {
    greet("KaniScript!")

    // var = 可変変数
    var count: i64 = 0
    for i in 0..5 {
        count += square(i)
    }

    print("0^2 + 1^2 + ... + 4^2 = ")
    println(count)     // 数値をそのまま渡せる！

    let result = add(10, 32)
    println(result)

    println(3.14)      // floatも直接OK
    println(true)      // boolも直接OK
}
