"""
KaniScript Code Generator — ASTからCコードを生成する
C言語経由でネイティブバイナリを生成（最終的にLLVM IR化予定）
"""

from typing import List, Dict, Optional
from parser import (
    Program, FnDef, StructDef, LetStmt, ConstStmt, ReturnStmt,
    IfStmt, ForStmt, WhileStmt, ExprStmt, Assign, AugAssign,
    BinOp, UnaryOp, Call, Index, Member, Ident,
    IntLit, FloatLit, StringLit, BoolLit, NullLit, ArrayLit,
    TypeNode, Param
)


# Zenpo型 → C型 マッピング
TYPE_C_MAP = {
    "i8":   "int8_t",
    "i16":  "int16_t",
    "i32":  "int32_t",
    "i64":  "int64_t",
    "u8":   "uint8_t",
    "u16":  "uint16_t",
    "u32":  "uint32_t",
    "u64":  "uint64_t",
    "f32":  "float",
    "f64":  "double",
    "bool": "bool",
    "str":  "const char*",
    "void": "void",
}


def type_to_c(node_or_name) -> str:
    if node_or_name is None:
        return "void"
    if hasattr(node_or_name, "name"):
        name = node_or_name.name
    else:
        name = str(node_or_name)
    if name in TYPE_C_MAP:
        return TYPE_C_MAP[name]
    if name == "[]str":
        return "zp_list_str_t"
    if name == "[]i64":
        return "zp_list_i64_t"
    if name.startswith("[]"):
        inner = name[2:]
        return f"zp_list_{inner}_t"
    return name  # ユーザー定義型（struct）


class CodeGen:
    def __init__(self, type_checker=None):
        self.output: List[str] = []
        self.indent_level = 0
        self.tmp_counter = 0
        self.tc = type_checker           # TypeCheckerから型情報を参照
        self.var_types: Dict[str, str] = {}  # 変数名 → 型名のマップ
        self.var_loop_depth: Dict[str, int] = {}  # 変数名 → 定義された loop_depth
        self.loop_depth = 0              # 現在のループ深度 (0 = 関数本体)
        self._current_scope = True       # 常にTrue（スコープトラッキング用）

    def indent(self):
        return "    " * self.indent_level

    def emit(self, line: str = ""):
        self.output.append(self.indent() + line)

    def fresh_tmp(self) -> str:
        self.tmp_counter += 1
        return f"__zp_tmp{self.tmp_counter}"

    def _infer_type_name(self, node) -> str:
        """式から型名を推論（スマートprint用）"""
        if isinstance(node, IntLit):   return "i64"
        if isinstance(node, FloatLit): return "f64"
        if isinstance(node, BoolLit):  return "bool"
        if isinstance(node, StringLit): return "str"
        if isinstance(node, Ident):
            # var_typesから変数の型を参照
            return self.var_types.get(node.name, "str")
        if isinstance(node, Index):
            obj_t = self._infer_type_name(node.obj)
            if obj_t.startswith("[]"):
                return obj_t[2:]
            return "str"
        if isinstance(node, Call):
            # 構造体コンストラクタまたは関数の戻り値型を取得
            if isinstance(node.func, Ident):
                if node.func.name in ("int_to_str", "float_to_str", "zp_int_to_str", "zp_float_to_str", "trim", "read_file", "read_line", "substr", "tcp_recv"):
                    return "str"
                if node.func.name in ("parse_i64", "len", "perm_used", "scratch_used", "http_listen", "tcp_listen", "tcp_accept"):
                    return "i64"
                if node.func.name in ("parse_f64", "time_now"):
                    return "f64"
                if node.func.name in ("write_file", "http_respond", "str_contains"):
                    return "bool"
                if node.func.name == "http_accept":
                    return "HttpRequest"
                if node.func.name in ("http_close", "tcp_send", "tcp_close"):
                    return "void"
                if node.func.name == "split":
                    return "[]str"
                if self.tc and node.func.name in self.tc.struct_types:
                    return node.func.name
                if self.tc:
                    fn = self.tc.fn_types.get(node.func.name)
                    if fn:
                        return fn.ret.name
        if isinstance(node, Member):
            # 構造体フィールドの型を取得
            obj_t = self._infer_type_name(node.obj)
            if self.tc and obj_t in self.tc.struct_types:
                fields = self.tc.struct_types[obj_t]
                if node.attr in fields:
                    return fields[node.attr].name
            return "str"
        if isinstance(node, BinOp):
            if node.op in ('==', '!=', '<', '>', '<=', '>=', '&&', '||'):
                return "bool"
            lt = self._infer_type_name(node.left)
            rt = self._infer_type_name(node.right)
            if node.op == '+' and (lt == "str" or rt == "str"):
                return "str"
            if "f64" in (lt, rt) or "f32" in (lt, rt):
                return "f64"
            if lt not in ("str", "bool"):
                return lt
            if rt not in ("str", "bool"):
                return rt
            return "str"  # フォールバック

    # ===== 式のCコード生成 =====
    def gen_expr(self, node) -> str:
        if isinstance(node, IntLit):
            return str(node.value)

        if isinstance(node, FloatLit):
            return str(node.value)

        if isinstance(node, StringLit):
            # エスケープ
            escaped = node.value.replace('\\', '\\\\').replace('"', '\\"') \
                                .replace('\n', '\\n').replace('\t', '\\t')
            return f'"{escaped}"'

        if isinstance(node, BoolLit):
            return "true" if node.value else "false"

        if isinstance(node, NullLit):
            return "NULL"

        if isinstance(node, Ident):
            return node.name

        if isinstance(node, BinOp):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            # 文字列連結は専用関数
            if node.op == '+' and self._is_string_op(node):
                return f'zp_str_concat({left}, {right})'
            # 文字列比較
            if node.op in ('==', '!=') and self._is_string_op(node):
                if node.op == '==':
                    return f'(strcmp({left}, {right}) == 0)'
                else:
                    return f'(strcmp({left}, {right}) != 0)'
            # ゼロ除算・剰余の安全化 (未定義動作防止)
            if node.op == '/':
                lt = self._infer_type_name(node.left)
                rt = self._infer_type_name(node.right)
                if lt != "f64" and rt != "f64":
                    return f'zp_div_i64({left}, {right})'
            if node.op == '%':
                return f'zp_mod_i64({left}, {right})'
            return f"({left} {node.op} {right})"

        if isinstance(node, UnaryOp):
            operand = self.gen_expr(node.operand)
            return f"({node.op}{operand})"

        if isinstance(node, Call):
            return self.gen_call(node)

        if isinstance(node, Index):
            obj = self.gen_expr(node.obj)
            idx = self.gen_expr(node.idx)
            obj_t = self._infer_type_name(node.obj)
            if obj_t.startswith("[]"):
                return f"{obj}.data[{idx}]"
            return f"{obj}[{idx}]"

        if isinstance(node, Member):
            obj = self.gen_expr(node.obj)
            return f"{obj}.{node.attr}"

        if isinstance(node, ArrayLit):
            elems = ", ".join(self.gen_expr(e) for e in node.elements)
            return f"{{{elems}}}"

        return "/* unknown expr */"

    def _is_string_op(self, node: BinOp) -> bool:
        if isinstance(node.left, StringLit) or isinstance(node.right, StringLit):
            return True
        lt = self._infer_type_name(node.left)
        rt = self._infer_type_name(node.right)
        return lt == "str" or rt == "str"

    def gen_call(self, node: Call) -> str:
        args = ", ".join(self.gen_expr(a) for a in node.args)
        if isinstance(node.func, Ident):
            name = node.func.name
            # 組み込み関数マッピング
            BUILTIN_SIMPLE = {
                "int_to_str":   "zp_int_to_str",
                "float_to_str": "zp_float_to_str",
                "read_file":    "zp_read_file",
                "write_file":   "zp_write_file",
                "split":        "zp_split",
                "trim":         "zp_trim",
                "parse_i64":    "zp_parse_i64",
                "parse_f64":    "zp_parse_f64",
                "time_now":     "zp_time_now",
                "perm_used":    "zp_perm_used",
                "scratch_used": "zp_scratch_used",
                "http_listen":  "zp_http_listen",
                "http_accept":  "zp_http_accept",
                "http_respond": "zp_http_respond",
                "http_close":   "zp_http_close",
                "read_line":    "zp_read_line",
                "substr":       "zp_substr",
                "str_contains": "zp_str_contains",
                "tcp_listen":   "zp_tcp_listen",
                "tcp_accept":   "zp_tcp_accept",
                "tcp_recv":     "zp_tcp_recv",
                "tcp_send":     "zp_tcp_send",
                "tcp_close":    "zp_tcp_close",
            }
            if name == "len" and len(node.args) == 1:
                arg = node.args[0]
                a = self.gen_expr(arg)
                arg_t = self._infer_type_name(arg)
                if arg_t.startswith("[]"):
                    return f"((int64_t)({a}.len))"
                else:
                    return f"((int64_t)strlen({a}))"
            if name in ("print", "println") and len(node.args) == 1:
                arg = node.args[0]
                a = self.gen_expr(arg)
                tname = self._infer_type_name(arg)
                is_ln = (name == "println")
                nl = "\\n" if is_ln else ""

                # 文字列の println は puts() を使用して高速化 & シンプル化
                if tname == "str" and is_ln:
                    return f'puts({a})'

                # 型に応じた正しい printf 呼び出しを1回で生成 (カンマ演算子を排除)
                PRINT_C = {
                    "i8":   f'printf("%d{nl}", (int)({a}))',
                    "i16":  f'printf("%d{nl}", (int)({a}))',
                    "i32":  f'printf("%d{nl}", (int)({a}))',
                    "i64":  f'printf("%lld{nl}", (long long)({a}))',
                    "u8":   f'printf("%u{nl}", (unsigned)({a}))',
                    "u16":  f'printf("%u{nl}", (unsigned)({a}))',
                    "u32":  f'printf("%u{nl}", (unsigned)({a}))',
                    "u64":  f'printf("%llu{nl}", (unsigned long long)({a}))',
                    "f32":  f'printf("%g{nl}", (double)({a}))',
                    "f64":  f'printf("%g{nl}", ({a}))',
                    "bool": f'printf("%s{nl}", ({a}) ? "true" : "false")',
                    "str":  f'printf("%s{nl}", ({a}))',
                }
                return PRINT_C.get(tname, f'printf("%s{nl}", ({a}))')
            if self.tc and name in self.tc.struct_types:
                # 構造体コンストラクタ: フィールドは素のまま初期化 (Boundary Promotion により外に出る時だけ promote される)
                arg_exprs = [self.gen_expr(arg) for arg in node.args]
                args_c = ", ".join(arg_exprs)
                return f"({name}){{{args_c}}}"
            if name in BUILTIN_SIMPLE:
                return f"{BUILTIN_SIMPLE[name]}({args})"
            return f"{name}({args})"
        func = self.gen_expr(node.func)
        return f"{func}({args})"

    # ===== 文のCコード生成 =====
    def gen_stmt(self, node):
        if isinstance(node, LetStmt):
            val = self.gen_expr(node.value)
            tname = node.type_annotation.name if node.type_annotation else self._infer_type_name(node.value)
            self.var_types[node.name] = tname
            self.var_loop_depth[node.name] = self.loop_depth
            c_type = type_to_c(node.type_annotation if node.type_annotation else tname)
            # ループ外 (関数トップレベル: loop_depth == 0) の宣言時のみ、関数生存期間に合わせてプロモート
            if self.loop_depth == 0:
                if tname == "str":
                    val = f"zp_promote({val})"
                elif tname == "[]str":
                    val = f"zp_list_str_promote({val})"
                elif self.tc and tname in self.tc.struct_types:
                    val = f"{tname}_promote({val})"
            # loop_depth > 0 (ループ内一時変数) は Scratch に据え置き
            if not node.mutable:
                self.emit(f"const {c_type} {node.name} = {val};")
            else:
                self.emit(f"{c_type} {node.name} = {val};")

        elif isinstance(node, ConstStmt):
            val = self.gen_expr(node.value)
            tname = node.type_annotation.name if node.type_annotation else self._infer_type_name(node.value)
            self.var_types[node.name] = tname
            self.var_loop_depth[node.name] = self.loop_depth
            c_type = type_to_c(node.type_annotation if node.type_annotation else tname)
            if self.loop_depth == 0:
                if tname == "str":
                    val = f"zp_promote({val})"
                elif tname == "[]str":
                    val = f"zp_list_str_promote({val})"
                elif self.tc and tname in self.tc.struct_types:
                    val = f"{tname}_promote({val})"
            self.emit(f"const {c_type} {node.name} = {val};")

        elif isinstance(node, ReturnStmt):
            if node.value:
                val = self.gen_expr(node.value)
                # 関数自身は素直に返し、呼び出し元のスコープ境界 (LetStmt / Assign) で必要に応じて promote される
                self.emit(f"return {val};")
            else:
                self.emit("return;")

        elif isinstance(node, IfStmt):
            cond = self.gen_expr(node.condition)
            self.emit(f"if ({cond}) {{")
            self.indent_level += 1
            for s in node.then_body:
                self.gen_stmt(s)
            self.indent_level -= 1
            if node.else_body:
                self.emit("} else {")
                self.indent_level += 1
                for s in node.else_body:
                    self.gen_stmt(s)
                self.indent_level -= 1
            self.emit("}")

        elif isinstance(node, ForStmt):
            start = self.gen_expr(node.iter_start)
            end   = self.gen_expr(node.iter_end)
            v = node.var
            self.var_types[v] = "i64"
            self.var_loop_depth[v] = self.loop_depth + 1
            mark = self.fresh_tmp()
            self.emit(f"for (int64_t {v} = {start}; {v} < {end}; {v}++) {{")
            self.indent_level += 1
            self.emit(f"size_t {mark} = zp_scratch_mark();")
            self.loop_depth += 1
            for s in node.body:
                self.gen_stmt(s)
            self.loop_depth -= 1
            self.emit(f"zp_scratch_reset({mark});")
            self.indent_level -= 1
            self.emit("}")

        elif isinstance(node, WhileStmt):
            cond = self.gen_expr(node.condition)
            mark = self.fresh_tmp()
            self.emit(f"while ({cond}) {{")
            self.indent_level += 1
            self.emit(f"size_t {mark} = zp_scratch_mark();")
            self.loop_depth += 1
            for s in node.body:
                self.gen_stmt(s)
            self.loop_depth -= 1
            self.emit(f"zp_scratch_reset({mark});")
            self.indent_level -= 1
            self.emit("}")

        elif isinstance(node, Assign):
            target = self.gen_expr(node.target)
            val    = self.gen_expr(node.value)
            tname = self._infer_type_name(node.target)

            # Boundary Promotion (エスケープ判定):
            # 代入先が現在のループ深度より外側 (浅い) か判定
            is_escape = False
            if isinstance(node.target, Ident):
                target_depth = self.var_loop_depth.get(node.target.name, 0)
                if self.loop_depth > target_depth:
                    is_escape = True
            elif isinstance(node.target, Member):
                curr = node.target.obj
                while isinstance(curr, Member):
                    curr = curr.obj
                if isinstance(curr, Ident):
                    target_depth = self.var_loop_depth.get(curr.name, 0)
                    if self.loop_depth > target_depth:
                        is_escape = True
            else:
                if self.loop_depth > 0:
                    is_escape = True

            if is_escape:
                if tname == "str":
                    val = f"zp_promote({val})"
                elif tname == "[]str":
                    val = f"zp_list_str_promote({val})"
                elif self.tc and tname in self.tc.struct_types:
                    val = f"{tname}_promote({val})"

            self.emit(f"{target} = {val};")

        elif isinstance(node, AugAssign):
            target = self.gen_expr(node.target)
            val    = self.gen_expr(node.value)
            op = node.op[0]  # '+=' → '+'
            self.emit(f"{target} {node.op} {val};")

        elif isinstance(node, ExprStmt):
            expr = self.gen_expr(node.expr)
            self.emit(f"{expr};")

    def gen_fn(self, node: FnDef):
        self.loop_depth = 0
        self._current_fn_ret = node.return_type.name if node.return_type else "void"
        ret = type_to_c(node.return_type)
        # main関数は常に int main() にする（C言語の要件）
        if node.name == "main":
            ret = "int"
        params_str = ", ".join(
            f"{type_to_c(p.type_annotation)} {p.name}" for p in node.params
        )
        self.emit(f"{ret} {node.name}({params_str}) {{")
        self.indent_level += 1
        # mainの先頭で2層アリーナ初期化 (Perm: 256MB, Scratch: 512MB - 仮想メモリ予約)
        if node.name == "main":
            self.emit("zp_arena_init(256 * 1024 * 1024, 512 * 1024 * 1024);")
        # パラメータ型をvar_typesに登録（スマートprint用）
        for p in node.params:
            if p.type_annotation:
                self.var_types[p.name] = p.type_annotation.name
                self.var_loop_depth[p.name] = 0
        for s in node.body:
            self.gen_stmt(s)
        # main関数には自動的に return 0 を追加
        if node.name == "main":
            self.emit("return 0;")
        self.indent_level -= 1
        self.emit("}")
        self.emit()

    def gen_struct(self, node: StructDef):
        self.emit(f"typedef struct {{")
        self.indent_level += 1
        for f in node.fields:
            c_type = type_to_c(f.type_annotation)
            self.emit(f"{c_type} {f.name};")
        self.indent_level -= 1
        self.emit(f"}} {node.name};")

        # 構造体フィールドを Perm へ安全退避する promote 関数
        self.emit(f"static inline {node.name} {node.name}_promote({node.name} s) {{")
        self.indent_level += 1
        for f in node.fields:
            if f.type_annotation:
                if f.type_annotation.name == "str":
                    self.emit(f"s.{f.name} = zp_promote(s.{f.name});")
                elif f.type_annotation.name == "[]str":
                    self.emit(f"s.{f.name} = zp_list_str_promote(s.{f.name});")
                elif self.tc and f.type_annotation.name in self.tc.struct_types:
                    self.emit(f"s.{f.name} = {f.type_annotation.name}_promote(s.{f.name});")
        self.emit("return s;")
        self.indent_level -= 1
        self.emit("}")
        self.emit()

    def generate(self, program: Program) -> str:
        # ヘッダー
        self.emit("// Generated by KaniScript Compiler")
        self.emit("// !! DO NOT EDIT !!")
        self.emit('#include "std.h"')
        self.emit()

        # 構造体定義を先に出力
        for stmt in program.stmts:
            if isinstance(stmt, StructDef):
                self.gen_struct(stmt)

        # 関数プロトタイプ
        for stmt in program.stmts:
            if isinstance(stmt, FnDef):
                ret = "int" if stmt.name == "main" else type_to_c(stmt.return_type)
                params = ", ".join(
                    f"{type_to_c(p.type_annotation)} {p.name}" for p in stmt.params
                )
                self.emit(f"{ret} {stmt.name}({params});")
        self.emit()

        # グローバル変数
        for stmt in program.stmts:
            if isinstance(stmt, (LetStmt, ConstStmt)):
                self.gen_stmt(stmt)
        self.emit()

        # 関数本体
        for stmt in program.stmts:
            if isinstance(stmt, FnDef):
                self.gen_fn(stmt)

        return "\n".join(self.output)
