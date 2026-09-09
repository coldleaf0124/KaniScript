"""
Zenpo Type Checker — ASTを走査して型を検証・推論する
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from parser import (
    Program, FnDef, StructDef, LetStmt, ConstStmt, ReturnStmt,
    IfStmt, ForStmt, WhileStmt, ExprStmt, Assign, AugAssign,
    BinOp, UnaryOp, Call, Index, Member, Ident,
    IntLit, FloatLit, StringLit, BoolLit, NullLit, ArrayLit,
    TypeNode, Param, Node
)


# ===== 型システム =====

@dataclass
class ZType:
    name: str

    def __eq__(self, other):
        if isinstance(other, ZType):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.name


# 組み込み型
T_I8   = ZType("i8")
T_I16  = ZType("i16")
T_I32  = ZType("i32")
T_I64  = ZType("i64")
T_U8   = ZType("u8")
T_U16  = ZType("u16")
T_U32  = ZType("u32")
T_U64  = ZType("u64")
T_F32  = ZType("f32")
T_F64  = ZType("f64")
T_BOOL = ZType("bool")
T_STR  = ZType("str")
T_VOID = ZType("void")
T_NULL = ZType("null")

INT_TYPES   = {T_I8, T_I16, T_I32, T_I64, T_U8, T_U16, T_U32, T_U64}
FLOAT_TYPES = {T_F32, T_F64}
NUM_TYPES   = INT_TYPES | FLOAT_TYPES

TYPE_MAP = {
    "i8": T_I8, "i16": T_I16, "i32": T_I32, "i64": T_I64,
    "u8": T_U8, "u16": T_U16, "u32": T_U32, "u64": T_U64,
    "f32": T_F32, "f64": T_F64,
    "bool": T_BOOL, "str": T_STR, "void": T_VOID,
}


@dataclass
class FnType:
    params: List[ZType]
    ret: ZType


@dataclass
class Symbol:
    name: str
    type: ZType
    mutable: bool = True


class TypeError(Exception):
    def __init__(self, msg: str, line: int = 0, col: int = 0):
        super().__init__(f"[Zenpo Type Error] {msg}" + (f" at line {line}" if line else ""))


class TypeChecker:
    def __init__(self):
        self.scopes: List[Dict[str, Symbol]] = [{}]
        self.fn_types: Dict[str, FnType] = {}
        self.struct_types: Dict[str, Dict[str, ZType]] = {}
        self.current_return_type: Optional[ZType] = None
        self._init_builtins()

    def _init_builtins(self):
        # 組み込み関数
        self.fn_types["print"]   = FnType(params=[T_STR], ret=T_VOID)
        self.fn_types["println"] = FnType(params=[T_STR], ret=T_VOID)
        self.fn_types["len"]     = FnType(params=[T_STR], ret=T_I64)
        self.fn_types["int_to_str"] = FnType(params=[T_I64], ret=T_STR)
        self.fn_types["float_to_str"] = FnType(params=[T_F64], ret=T_STR)
        self.fn_types["read_file"] = FnType(params=[T_STR], ret=T_STR)
        self.fn_types["write_file"] = FnType(params=[T_STR, T_STR], ret=T_BOOL)
        self.fn_types["split"] = FnType(params=[T_STR, T_STR], ret=ZType("[]str"))
        self.fn_types["trim"] = FnType(params=[T_STR], ret=T_STR)
        self.fn_types["parse_i64"] = FnType(params=[T_STR], ret=T_I64)
        self.fn_types["parse_f64"] = FnType(params=[T_STR], ret=T_F64)
        self.fn_types["time_now"]  = FnType(params=[], ret=T_F64)
        self.fn_types["perm_used"] = FnType(params=[], ret=T_I64)
        self.fn_types["scratch_used"] = FnType(params=[], ret=T_I64)

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def define(self, name: str, typ: ZType, mutable: bool = True):
        self.scopes[-1][name] = Symbol(name=name, type=typ, mutable=mutable)

    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def resolve_type(self, node: TypeNode) -> ZType:
        if node.name in TYPE_MAP:
            return TYPE_MAP[node.name]
        if node.name in self.struct_types:
            return ZType(node.name)
        if node.name.startswith("[]"):
            elem_name = node.name[2:]
            elem_t = self.resolve_type(TypeNode(name=elem_name, line=node.line, col=node.col))
            return ZType(f"[]{elem_t.name}")
        raise TypeError(f"Unknown type: {node.name}", node.line, node.col)

    # ===== 式の型推論 =====
    def infer(self, node) -> ZType:
        if isinstance(node, IntLit):
            return T_I64
        if isinstance(node, FloatLit):
            return T_F64
        if isinstance(node, StringLit):
            return T_STR
        if isinstance(node, BoolLit):
            return T_BOOL
        if isinstance(node, NullLit):
            return T_NULL
        if isinstance(node, ArrayLit):
            if not node.elements:
                return ZType("[]void")
            elem_t = self.infer(node.elements[0])
            return ZType(f"[]{elem_t.name}")
        if isinstance(node, Ident):
            sym = self.lookup(node.name)
            if sym is None:
                raise TypeError(f"Undefined variable: {node.name}", node.line, node.col)
            return sym.type
        if isinstance(node, BinOp):
            return self.infer_binop(node)
        if isinstance(node, UnaryOp):
            t = self.infer(node.operand)
            if node.op == '!' and t != T_BOOL:
                raise TypeError(f"! requires bool, got {t}", node.line, node.col)
            if node.op == '-' and t not in NUM_TYPES:
                raise TypeError(f"- requires numeric type, got {t}", node.line, node.col)
            return t
        if isinstance(node, Call):
            return self.infer_call(node)
        if isinstance(node, Index):
            return self.infer_index(node)
        if isinstance(node, Member):
            return self.infer_member(node)
        raise TypeError(f"Cannot infer type of {type(node).__name__}", getattr(node, 'line', 0))

    def infer_binop(self, node: BinOp) -> ZType:
        lt = self.infer(node.left)
        rt = self.infer(node.right)
        op = node.op

        # 比較演算子 → bool
        if op in ('==', '!=', '<', '>', '<=', '>='):
            return T_BOOL
        # 論理演算子 → bool
        if op in ('&&', '||'):
            if lt != T_BOOL or rt != T_BOOL:
                raise TypeError(f"{op} requires bool operands", node.line, node.col)
            return T_BOOL
        # 算術演算子
        if op in ('+', '-', '*', '/', '%'):
            # 文字列連結
            if op == '+' and lt == T_STR and rt == T_STR:
                return T_STR
            if lt in NUM_TYPES and rt in NUM_TYPES:
                # 浮動小数点が優先
                if lt in FLOAT_TYPES or rt in FLOAT_TYPES:
                    return T_F64
                return lt
            raise TypeError(f"Type mismatch in {op}: {lt} vs {rt}", node.line, node.col)
        # ビット演算
        if op in ('&', '|', '^', '<<', '>>'):
            if lt in INT_TYPES and rt in INT_TYPES:
                return lt
            raise TypeError(f"{op} requires integer types", node.line, node.col)
        raise TypeError(f"Unknown operator: {op}", node.line, node.col)

    def infer_call(self, node: Call) -> ZType:
        if isinstance(node.func, Ident):
            name = node.func.name
            if name in self.struct_types:
                return ZType(name)
            if name == "len":
                if len(node.args) != 1:
                    raise TypeError("len() takes exactly 1 argument", node.line, node.col)
                arg_t = self.infer(node.args[0])
                if arg_t == T_STR or arg_t.name.startswith("[]"):
                    return T_I64
                raise TypeError(f"len() requires str or slice, got {arg_t}", node.line, node.col)
            if name in self.fn_types:
                fn = self.fn_types[name]
                return fn.ret
            raise TypeError(f"Undefined function or struct: {name}", node.line, node.col)
        return T_VOID

    def infer_index(self, node: Index) -> ZType:
        obj_t = self.infer(node.obj)
        if obj_t.name.startswith("[]"):
            return ZType(obj_t.name[2:])
        raise TypeError(f"Cannot index into {obj_t}", node.line, node.col)

    def infer_member(self, node: Member) -> ZType:
        obj_t = self.infer(node.obj)
        if obj_t.name in self.struct_types:
            fields = self.struct_types[obj_t.name]
            if node.attr in fields:
                return fields[node.attr]
            raise TypeError(f"No field {node.attr!r} on {obj_t}", node.line, node.col)
        raise TypeError(f"Cannot access member of {obj_t}", node.line, node.col)

    # ===== 文のチェック =====
    def check_stmt(self, node):
        if isinstance(node, LetStmt):
            val_t = self.infer(node.value)
            if node.type_annotation:
                ann_t = self.resolve_type(node.type_annotation)
                if val_t != ann_t and not (val_t in INT_TYPES and ann_t in INT_TYPES) \
                        and not (val_t in FLOAT_TYPES and ann_t in FLOAT_TYPES):
                    raise TypeError(f"Type mismatch: {ann_t} = {val_t}", node.line, node.col)
                self.define(node.name, ann_t, node.mutable)
            else:
                self.define(node.name, val_t, node.mutable)

        elif isinstance(node, ConstStmt):
            val_t = self.infer(node.value)
            if node.type_annotation:
                ann_t = self.resolve_type(node.type_annotation)
                self.define(node.name, ann_t, mutable=False)
            else:
                self.define(node.name, val_t, mutable=False)

        elif isinstance(node, ReturnStmt):
            if node.value:
                ret_t = self.infer(node.value)
                if self.current_return_type and ret_t != self.current_return_type:
                    if not (ret_t in NUM_TYPES and self.current_return_type in NUM_TYPES):
                        raise TypeError(
                            f"Return type mismatch: expected {self.current_return_type}, got {ret_t}",
                            node.line, node.col
                        )

        elif isinstance(node, IfStmt):
            cond_t = self.infer(node.condition)
            if cond_t != T_BOOL:
                raise TypeError(f"if condition must be bool, got {cond_t}", node.line, node.col)
            self.push_scope()
            for s in node.then_body:
                self.check_stmt(s)
            self.pop_scope()
            if node.else_body:
                self.push_scope()
                for s in node.else_body:
                    self.check_stmt(s)
                self.pop_scope()

        elif isinstance(node, ForStmt):
            start_t = self.infer(node.iter_start)
            end_t   = self.infer(node.iter_end)
            if start_t not in INT_TYPES or end_t not in INT_TYPES:
                raise TypeError("for range requires integer types", node.line, node.col)
            self.push_scope()
            self.define(node.var, T_I64)
            for s in node.body:
                self.check_stmt(s)
            self.pop_scope()

        elif isinstance(node, WhileStmt):
            cond_t = self.infer(node.condition)
            if cond_t != T_BOOL:
                raise TypeError(f"while condition must be bool, got {cond_t}", node.line, node.col)
            self.push_scope()
            for s in node.body:
                self.check_stmt(s)
            self.pop_scope()

        elif isinstance(node, Assign):
            self.infer(node.target)  # 変数が存在するかチェック
            self.infer(node.value)

        elif isinstance(node, AugAssign):
            self.infer(node.target)
            self.infer(node.value)

        elif isinstance(node, ExprStmt):
            self.infer(node.expr)

        elif isinstance(node, FnDef):
            self.check_fn(node)

        elif isinstance(node, StructDef):
            self.check_struct(node)

    def check_fn(self, node: FnDef):
        # 関数シグネチャを登録
        param_types = []
        for p in node.params:
            param_types.append(self.resolve_type(p.type_annotation))
        ret_type = self.resolve_type(node.return_type) if node.return_type else T_VOID
        self.fn_types[node.name] = FnType(params=param_types, ret=ret_type)

        # ボディをチェック
        prev_ret = self.current_return_type
        self.current_return_type = ret_type
        self.push_scope()
        for p, pt in zip(node.params, param_types):
            self.define(p.name, pt)
        for s in node.body:
            self.check_stmt(s)
        self.pop_scope()
        self.current_return_type = prev_ret

    def check_struct(self, node: StructDef):
        fields = {}
        for f in node.fields:
            fields[f.name] = self.resolve_type(f.type_annotation)
        self.struct_types[node.name] = fields

    def check(self, program: Program):
        # 1パス目：関数・構造体シグネチャを先に登録
        for stmt in program.stmts:
            if isinstance(stmt, FnDef):
                param_types = [self.resolve_type(p.type_annotation) for p in stmt.params]
                ret_type = self.resolve_type(stmt.return_type) if stmt.return_type else T_VOID
                self.fn_types[stmt.name] = FnType(params=param_types, ret=ret_type)
            elif isinstance(stmt, StructDef):
                self.check_struct(stmt)

        # 2パス目：全体チェック
        for stmt in program.stmts:
            self.check_stmt(stmt)
