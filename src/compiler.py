"""
HrpyCode Compiler — メインエントリポイント
使い方: hc run <source.hc> / hc build <source.hc>
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# src/ ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

from lexer import Lexer, LexError
from parser import Parser, ParseError
from typechecker import TypeChecker
from codegen import CodeGen


STDLIB_DIR = Path(__file__).parent.parent / "stdlib"
if not (STDLIB_DIR / "std.h").exists():
    alt_stdlib = Path(__file__).parent / "stdlib"
    if (alt_stdlib / "std.h").exists():
        STDLIB_DIR = alt_stdlib
COLORS = {
    'red':    '\033[91m',
    'green':  '\033[92m',
    'yellow': '\033[93m',
    'blue':   '\033[94m',
    'bold':   '\033[1m',
    'reset':  '\033[0m',
}

def c(color, text):
    return COLORS[color] + text + COLORS['reset']


def banner():
    print(c('bold', c('blue', r"""
    _  __            _ ____            _       _   
   | |/ /__ _ _ __  (_) ___|  ___ _ __(_)_ __ | |_ 
   | ' // _` | '_ \ | \___ \ / __| '__| | '_ \| __|
   | . \ (_| | | | || |___) | (__| |  | | |_) | |_ 
   |_|\_\__,_|_| |_|/ |____/ \___|_|  |_| .__/ \__|
                  |__/                  |_|        
""")))
    print(c('yellow', "  🦀 KaniScript (kani / ks) v0.1 — Fast, Safe, Simple\n"))


def compile_file(source_path: Path, output_path: Path, verbose: bool = False,
                  emit_c: bool = False, skip_typecheck: bool = False,
                  shared: bool = False) -> bool:
    source = source_path.read_text(encoding='utf-8')
    filename = source_path.name

    try:
        # --- Step 1: Lexing ---
        if verbose:
            print(c('blue', f"[1/4] Lexing {filename}..."))
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        if verbose:
            print(f"      {len(tokens)} tokens generated")

        # --- Step 2: Parsing ---
        if verbose:
            print(c('blue', "[2/4] Parsing..."))
        parser = Parser(tokens)
        ast = parser.parse()
        if verbose:
            print(f"      {len(ast.stmts)} top-level statements")

        # --- Step 3: Type Checking ---
        checker = None
        if not skip_typecheck:
            if verbose:
                print(c('blue', "[3/4] Type checking..."))
            checker = TypeChecker()
            checker.check(ast)
            if verbose:
                print("      Type check passed ✓")
        else:
            if verbose:
                print(c('yellow', "[3/4] Type checking skipped"))

        # --- Step 4: Code Generation ---
        if verbose:
            print(c('blue', "[4/4] Generating C code..."))
        gen = CodeGen(type_checker=checker)
        c_code = gen.generate(ast)

        # 一時Cファイル
        c_file = output_path.parent / (output_path.stem + "_kani_gen.c")
        c_file.write_text(c_code, encoding='utf-8')

        if emit_c:
            print(c('green', f"C code written to: {c_file}"))
            return True

        # --- Compile C → Native Binary / Shared Library ---
        if verbose:
            mode_desc = "shared library" if shared else "native binary"
            print(c('blue', f"      Compiling to {mode_desc}..."))

        include_dir = str(STDLIB_DIR)
        cmd = [
            "cc",
            "-O3",                   # 最大最適化
            "-march=native",         # CPU最適化
            "-fstrict-aliasing",     # no-aliasing保証
            "-ffast-math",           # 高速浮動小数点
            "-std=c11",
            f"-I{include_dir}",
        ]
        if shared:
            cmd.extend(["-shared", "-fPIC"])
        cmd.extend([str(c_file), "-o", str(output_path)])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(c('red', "Compilation error (C backend):"))
            print(result.stderr)
            c_file.unlink(missing_ok=True)
            return False

        # 一時ファイル削除
        if not verbose:
            c_file.unlink(missing_ok=True)
        else:
            print(f"      C file kept at: {c_file}")

        if verbose:
            print(c('green', f"✓ Compiled successfully: {output_path}"))
        return True

    except LexError as e:
        print(c('red', f"Lex Error: {e}"))
        return False
    except ParseError as e:
        print(c('red', f"Parse Error: {e}"))
        return False
    except Exception as e:
        print(c('red', f"Error: {type(e).__name__}: {e}"))
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def show_cheat():
    banner()
    print(c('bold', c('yellow', "=== 🦀 KaniScript 30-Second Syntax Cheat Sheet ===\n")))
    print(c('bold', "1. Variables (:= 一撃宣言)"))
    print("   x := 10                 # i64")
    print("   name := \"crab\"          # str")
    print("   pi := 3.14              # f64\n")
    print(c('bold', "2. Output (カッコ不要の out)"))
    print("   out \"Hello, KaniScript!\"")
    print("   out x + 5\n")
    print(c('bold', "3. Functions (fn/def 不要 & 式が暗黙return)"))
    print("   add(a: i64, b: i64) -> i64 {")
    print("       a + b               # 最後の式をそのままreturn")
    print("   }\n")
    print(c('bold', "4. Conditionals (when - else)"))
    print("   when x > 5 {")
    print("       out \"big\"")
    print("   } else {")
    print("       out \"small\"")
    print("   }\n")
    print(c('bold', "5. Loops (each による範囲ループ)"))
    print("   each i in 0..10 {")
    print("       out i")
    print("   }\n")
    print(c('bold', "6. Standard Library (ファイルI/O・スライス)"))
    print("   content := read_file(\"data.txt\")")
    print("   lines := split(content, \"\\n\")")
    print("   first := lines[0]")
    print("   n := len(lines)")
    print("   val := parse_i64(\"123\")")
    print("   t := time_now()\n")
    print(c('green', "Run a script:      kani run file.ks"))
    print(c('green', "Build binary:      kani build file.ks -o myapp"))
    print(c('green', "Create template:   kani init\n"))


def cmd_init(args):
    target = Path(args[0]) if args else Path("main.ks")
    if target.exists():
        print(c('yellow', f"Warning: {target} already exists."))
        sys.exit(1)

    template = '''// main.ks - Welcome to KaniScript!
// Run with: kani run main.ks

// 1. Functions need no keywords. The last expression is returned.
add(a: i64, b: i64) -> i64 {
    a + b
}

// 2. Entry point is main()
main() {
    out "🦀 Hello from KaniScript!"

    // 3. Variable declaration with :=
    x := 10
    y := 20
    out "x + y = " + int_to_str(add(x, y))

    // 4. Loops with each
    total := 0
    each i in 1..6 {
        total += i
    }
    out "Sum from 1 to 5: " + int_to_str(total)

    // 5. Branch with when
    when total > 10 {
        out "Total is greater than 10!"
    } else {
        out "Total is small."
    }
}
'''
    target.write_text(template, encoding='utf-8')
    print(c('green', f"✓ Created template: {target}"))
    print("Next step:")
    print(f"  kani run {target}")


VERSION = "0.1.0"


def main():
    import tempfile

    raw_args = sys.argv[1:]
    if not raw_args or raw_args[0] in ('-h', '--help'):
        banner()
        print("コマンド:")
        print("  kani run <file.ks>             # コンパイルして即実行 (手軽!)")
        print("  kani build <file.ks> [-o out]  # ネイティブバイナリをビルド")
        print("  kani init [filename.ks]        # チュートリアル付きひな形コードを生成")
        print("  kani new [filename.ks]         # (init のエイリアス)")
        print("  kani cheat                     # 30秒でわかる構文チートシートを表示")
        print("  kani --version                 # バージョンを表示")
        print("  kani <file.ks>                 # build と同等")
        print("  ※ エイリアスとして 'ks' コマンドも利用可能です")
        print("\nオプション:")
        print("  -o, --output <path>           # 出力ファイル名")
        print("  -S, --emit-c                  # 生成Cコードを出力")
        print("  -v, --verbose                 # 詳細ログを表示")
        print("  --shared                      # 共有ライブラリを出力")
        print("  --no-typecheck                # 型チェックをスキップ")
        sys.exit(0)

    if raw_args[0] in ('-V', '--version', 'version'):
        print(f"KaniScript {VERSION}")
        sys.exit(0)

    # 特殊サブコマンド
    if raw_args[0] in ("cheat", "cheatsheet", "help-syntax"):
        show_cheat()
        sys.exit(0)

    if raw_args[0] in ("init", "new"):
        cmd_init(raw_args[1:])
        sys.exit(0)

    # サブコマンド判定
    mode = "build"
    if raw_args[0] == "run":
        mode = "run"
        raw_args = raw_args[1:]
    elif raw_args[0] == "build":
        mode = "build"
        raw_args = raw_args[1:]

    parser = argparse.ArgumentParser(prog="kani", description="KaniScript Compiler")
    parser.add_argument("source", help="KaniScriptソースファイル (.ks)")
    parser.add_argument("-o", "--output", help="出力バイナリパス", default=None)
    parser.add_argument("-S", "--emit-c", action="store_true", help="Cコードを出力して終了")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細出力")
    parser.add_argument("--shared", action="store_true", help="共有ライブラリを出力")
    parser.add_argument("--no-typecheck", action="store_true", help="型チェックをスキップ")
    parser.add_argument("--no-banner", action="store_true", help="バナーを非表示")
    args = parser.parse_args(raw_args)

    source_path = Path(args.source)
    if not source_path.exists():
        print(c('red', f"Error: File not found: {source_path}"))
        sys.exit(1)
    if source_path.suffix not in ('.ks', '.kani', '.hc', '.hrpy', '.zp'):
        print(c('yellow', f"Warning: Expected .ks extension, got {source_path.suffix}"))

    if mode == "run":
        # 一時実行ファイルを作成して実行
        with tempfile.NamedTemporaryFile(prefix="kani_exec_", delete=False) as tmp:
            tmp_out = Path(tmp.name)
        try:
            success = compile_file(
                source_path=source_path,
                output_path=tmp_out,
                verbose=args.verbose,
                emit_c=args.emit_c,
                skip_typecheck=args.no_typecheck,
                shared=False,
            )
            if success:
                res = subprocess.run([str(tmp_out)])
                sys.exit(res.returncode)
            else:
                sys.exit(1)
        finally:
            tmp_out.unlink(missing_ok=True)
    else:
        # build モード
        if args.output:
            output_path = Path(args.output)
        else:
            ext = ".dylib" if sys.platform == "darwin" else ".so"
            output_path = source_path.with_suffix(ext if args.shared else '')

        success = compile_file(
            source_path=source_path,
            output_path=output_path,
            verbose=args.verbose,
            emit_c=args.emit_c,
            skip_typecheck=args.no_typecheck,
            shared=args.shared,
        )
        if success and not args.verbose:
            print(c('green', f"✓ {output_path} を作成しました"))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
