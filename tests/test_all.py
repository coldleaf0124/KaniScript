#!/usr/bin/env python3
"""
KaniScript テストスイート
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import Lexer, TokenType
from parser import Parser, IntLit, BinOp, FnDef, LetStmt
from typechecker import TypeChecker, T_I64, T_F64, T_BOOL


PASS = 0
FAIL = 0


def ok(name: str):
    global PASS
    PASS += 1
    print(f"  ✓ {name}")


def fail(name: str, reason: str):
    global FAIL
    FAIL += 1
    print(f"  ✗ {name}: {reason}")


def run(name: str, fn):
    try:
        fn()
        ok(name)
    except AssertionError as e:
        fail(name, f"AssertionError {e}")
    except Exception as e:
        fail(name, f"{type(e).__name__}: {e}")


def lex(src):
    return Lexer(src).tokenize()

def parse_prog(src):
    tokens = Lexer(src).tokenize()
    return Parser(tokens).parse()

def parse_expr(src):
    tokens = Lexer(src).tokenize()
    return Parser(tokens).parse_expr()

def typecheck(src):
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    tc = TypeChecker()
    tc.check(ast)
    return tc

def infer(src):
    expr = parse_expr(src)
    tc = TypeChecker()
    return tc.infer(expr)


# ===== Lexer Tests =====
print("\n" + "="*50)
print("  Lexer Tests")
print("="*50)

def t_int_lit():
    t = lex("42")
    assert t[0].type == TokenType.INT_LIT
    assert t[0].value == "42"
run("整数リテラル", t_int_lit)

def t_float_lit():
    t = lex("3.14")
    assert t[0].type == TokenType.FLOAT_LIT
run("浮動小数点リテラル", t_float_lit)

def t_str_lit():
    t = lex('"hello"')
    assert t[0].type == TokenType.STRING_LIT
    assert t[0].value == "hello"
run("文字列リテラル", t_str_lit)

def t_escape():
    t = lex('"a\\nb"')
    assert t[0].value == "a\nb"
run("エスケープ文字", t_escape)

def t_kw_fn():
    t = lex("fn")
    assert t[0].type == TokenType.FN
run("キーワード fn", t_kw_fn)

def t_kw_letmut():
    t = lex("let mut x")
    assert t[0].type == TokenType.LET
    assert t[1].type == TokenType.MUT
run("キーワード let mut", t_kw_letmut)

def t_arrow():
    t = lex("->")
    assert t[0].type == TokenType.ARROW
run("演算子 ->", t_arrow)

def t_dotdot():
    t = lex("0..10")
    assert t[1].type == TokenType.DOT_DOT
run("演算子 ..", t_dotdot)

def t_plus_eq():
    t = lex("x += 1")
    assert t[1].type == TokenType.PLUS_EQ
run("複合代入 +=", t_plus_eq)

def t_comment():
    t = lex("// comment\n42")
    assert t[0].type == TokenType.INT_LIT
run("コメントスキップ", t_comment)

def t_block_comment():
    t = lex("/* block */42")
    assert t[0].type == TokenType.INT_LIT
run("ブロックコメントスキップ", t_block_comment)

def t_type_i32():
    t = lex("i32")
    assert t[0].type == TokenType.TYPE_I32
run("型キーワード i32", t_type_i32)

def t_underscore_num():
    t = lex("1_000_000")
    assert t[0].value == "1000000"
run("アンダースコア数値区切り", t_underscore_num)

def t_bool_true():
    t = lex("true")
    assert t[0].type == TokenType.TRUE
run("true リテラル", t_bool_true)


# ===== Parser Tests =====
print("\n" + "="*50)
print("  Parser Tests")
print("="*50)

def t_fn_def():
    p = parse_prog("fn f() { return 42 }")
    assert isinstance(p.stmts[0], FnDef)
run("関数定義パース", t_fn_def)

def t_binop_prec():
    expr = parse_expr("1 + 2 * 3")
    assert isinstance(expr, BinOp) and expr.op == "+"
run("演算子優先順位 1+2*3", t_binop_prec)

def t_let():
    p = parse_prog("let x = 5")
    s = p.stmts[0]
    assert isinstance(s, LetStmt) and s.name == "x"
run("let文パース", t_let)

def t_let_mut():
    p = parse_prog("let mut y = 10")
    assert p.stmts[0].mutable == True
run("let mut パース", t_let_mut)

def t_type_ann():
    p = parse_prog("let x: i32 = 5")
    assert p.stmts[0].type_annotation.name == "i32"
run("型アノテーション", t_type_ann)

def t_fn_params():
    p = parse_prog("fn add(a: i32, b: i32) -> i32 { return a }")
    fn = p.stmts[0]
    assert fn.name == "add" and len(fn.params) == 2
run("関数定義・パラメータ", t_fn_params)

def t_if():
    parse_prog("fn f() { if true { return 1 } }")
run("if文パース", t_if)

def t_if_else():
    parse_prog("fn f() { if true { return 1 } else { return 2 } }")
run("if-else文パース", t_if_else)

def t_for():
    parse_prog("fn f() { for i in 0..10 { } }")
run("for文パース", t_for)

def t_while():
    parse_prog("fn f() { let mut x: i64 = 0 while x < 10 { x += 1 } }")
run("while文パース", t_while)

def t_nested_call():
    parse_prog("fn f() { println(int_to_str(42)) }")
run("ネストした関数呼び出し", t_nested_call)

def t_array_lit():
    parse_prog("let arr = [1, 2, 3]")
run("配列リテラル", t_array_lit)

# 独自構文テスト
def t_unique_fn():
    p = parse_prog("add(a: i64, b: i64) -> i64 { a + b }")
    assert len(p.stmts) == 1 and p.stmts[0].name == "add"
run("完全独自: キーワードなし関数定義", t_unique_fn)

def t_unique_short_var():
    p = parse_prog("fn f() { x := 42 }")
    assert True
run("完全独自: 短縮代入 (:=)", t_unique_short_var)

def t_unique_out():
    p = parse_prog("fn f() { out 42 }")
    assert True
run("完全独自: out 出力文", t_unique_out)

def t_unique_when():
    p = parse_prog("fn f() { when true { out 1 } else { out 2 } }")
    assert True
run("完全独自: when-else 条件文", t_unique_when)

def t_unique_each():
    p = parse_prog("fn f() { each i in 0..10 { out i } }")
    assert True
run("完全独自: each ループ文", t_unique_each)


# ===== Type Checker Tests =====
print("\n" + "="*50)
print("  Type Checker Tests")
print("="*50)

def t_infer_int():
    assert infer("42") == T_I64
run("整数型推論", t_infer_int)

def t_infer_float():
    assert infer("3.14") == T_F64
run("浮動小数点型推論", t_infer_float)

def t_infer_bool():
    assert infer("true") == T_BOOL
run("bool型推論", t_infer_bool)

def t_infer_arith():
    assert infer("1 + 2") == T_I64
run("算術式型推論", t_infer_arith)

def t_infer_cmp():
    assert infer("1 < 2") == T_BOOL
run("比較式はbool", t_infer_cmp)

def t_check_fn():
    typecheck("fn add(a: i32, b: i32) -> i32 { return a }")
run("関数定義チェック", t_check_fn)

def t_check_for():
    typecheck("fn f() { for i in 0..10 { } }")
run("for ループチェック", t_check_for)

def t_check_let():
    typecheck("let x: i64 = 42")
run("let文型チェック", t_check_let)

def t_check_recursive():
    typecheck("""
fn fib(n: i64) -> i64 {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}
""")
run("再帰関数型チェック", t_check_recursive)

# ===== Practical & Slice Tests =====
print("\n" + "="*50)
print("  Slice & Practical Feature Tests")
print("="*50)

def t_parse_slice_type():
    t = Parser(Lexer("[]str").tokenize()).parse_type()
    assert t.name == "[]str"
run("スライス型パース ([]str)", t_parse_slice_type)

def t_typecheck_slice():
    typecheck("""
fn process(lines: []str) -> i64 {
    first := lines[0]
    return len(lines)
}
""")
run("スライス引数・Index・len型チェック", t_typecheck_slice)

def t_typecheck_practical_builtins():
    typecheck("""
fn test_builtins() {
    ok := write_file("dummy.txt", "hello")
    data := read_file("dummy.txt")
    trimmed := trim(data)
    parts := split(trimmed, ",")
    n := parse_i64("123")
    f := parse_f64("3.14")
    t := time_now()
    p := perm_used()
}
""")
run("実用組み込み関数群の型チェック", t_typecheck_practical_builtins)

def t_e2e_practical():
    import subprocess
    repo_root = Path(__file__).resolve().parent.parent
    compiler_path = repo_root / "src" / "compiler.py"
    target_ks = repo_root / "tests" / "test_practical.ks"
    cmd = [sys.executable, str(compiler_path), "run", str(target_ks)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(repo_root))
    assert res.returncode == 0, f"Failed with {res.stderr}"
    assert "ALL PRACTICAL FEATURES VERIFIED" in res.stdout
run("E2E実用テスト実行 (ファイルI/O・split・型変換・集計)", t_e2e_practical)



# ===== 結果 =====
total = PASS + FAIL
print(f"\n{'='*50}")
print(f"  総合結果: {PASS}/{total} passed")
print(f"{'='*50}\n")
sys.exit(0 if FAIL == 0 else 1)
