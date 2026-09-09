"""
Zenpo Parser — トークン列からAST(抽象構文木)を構築する
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from lexer import Token, TokenType


# ===== AST ノード定義 =====

@dataclass
class Node:
    line: int = field(default=0, repr=False)
    col: int = field(default=0, repr=False)

# 型ノード
@dataclass
class TypeNode(Node):
    name: str = ""
    params: List[Any] = field(default_factory=list)   # ジェネリクス用

# リテラル
@dataclass
class IntLit(Node):
    value: int = 0

@dataclass
class FloatLit(Node):
    value: float = 0.0

@dataclass
class StringLit(Node):
    value: str = ""

@dataclass
class BoolLit(Node):
    value: bool = False

@dataclass
class NullLit(Node):
    pass

# 識別子
@dataclass
class Ident(Node):
    name: str = ""

# 二項演算
@dataclass
class BinOp(Node):
    op: str = ""
    left: Any = None
    right: Any = None

# 単項演算
@dataclass
class UnaryOp(Node):
    op: str = ""
    operand: Any = None

# 代入
@dataclass
class Assign(Node):
    target: Any = None
    value: Any = None

# 複合代入 (+=, -= ...)
@dataclass
class AugAssign(Node):
    op: str = ""
    target: Any = None
    value: Any = None

# 関数呼び出し
@dataclass
class Call(Node):
    func: Any = None
    args: List[Any] = field(default_factory=list)

# 配列インデックス
@dataclass
class Index(Node):
    obj: Any = None
    idx: Any = None

# メンバアクセス
@dataclass
class Member(Node):
    obj: Any = None
    attr: str = ""

# let 文
@dataclass
class LetStmt(Node):
    name: str = ""
    mutable: bool = False
    type_annotation: Optional[TypeNode] = None
    value: Any = None

# const 文
@dataclass
class ConstStmt(Node):
    name: str = ""
    type_annotation: Optional[TypeNode] = None
    value: Any = None

# return 文
@dataclass
class ReturnStmt(Node):
    value: Any = None

# if 文
@dataclass
class IfStmt(Node):
    condition: Any = None
    then_body: List[Any] = field(default_factory=list)
    else_body: List[Any] = field(default_factory=list)

# for ループ
@dataclass
class ForStmt(Node):
    var: str = ""
    iter_start: Any = None
    iter_end: Any = None
    body: List[Any] = field(default_factory=list)

# while ループ
@dataclass
class WhileStmt(Node):
    condition: Any = None
    body: List[Any] = field(default_factory=list)

# 式文
@dataclass
class ExprStmt(Node):
    expr: Any = None

# 関数パラメータ
@dataclass
class Param(Node):
    name: str = ""
    type_annotation: TypeNode = None

# 関数定義
@dataclass
class FnDef(Node):
    name: str = ""
    params: List[Param] = field(default_factory=list)
    return_type: Optional[TypeNode] = None
    body: List[Any] = field(default_factory=list)

# 構造体フィールド
@dataclass
class StructField(Node):
    name: str = ""
    type_annotation: TypeNode = None

# 構造体定義
@dataclass
class StructDef(Node):
    name: str = ""
    fields: List[StructField] = field(default_factory=list)

# 配列リテラル
@dataclass
class ArrayLit(Node):
    elements: List[Any] = field(default_factory=list)

# プログラム全体
@dataclass
class Program:
    stmts: List[Any] = field(default_factory=list)


# ===== パーサー =====

class ParseError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"[Zenpo Parse Error] {msg} at line {line}, col {col}")

TYPE_TOKENS = {
    TokenType.TYPE_I8, TokenType.TYPE_I16, TokenType.TYPE_I32, TokenType.TYPE_I64,
    TokenType.TYPE_U8, TokenType.TYPE_U16, TokenType.TYPE_U32, TokenType.TYPE_U64,
    TokenType.TYPE_F32, TokenType.TYPE_F64, TokenType.TYPE_BOOL, TokenType.TYPE_STR,
    TokenType.TYPE_VOID, TokenType.IDENT,
}

BINOP_PREC = {
    '||': 1, '&&': 2,
    '==': 3, '!=': 3,
    '<': 4, '>': 4, '<=': 4, '>=': 4,
    '+': 5, '-': 5,
    '*': 6, '/': 6, '%': 6,
    '<<': 7, '>>': 7,
    '&': 8, '^': 9, '|': 10,
}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, ttype: TokenType) -> Token:
        tok = self.peek()
        if tok.type != ttype:
            raise ParseError(
                f"Expected {ttype.name}, got {tok.type.name} ({tok.value!r})",
                tok.line, tok.col
            )
        return self.advance()

    def check(self, *ttypes: TokenType) -> bool:
        return self.peek().type in ttypes

    def match(self, *ttypes: TokenType) -> Optional[Token]:
        if self.check(*ttypes):
            return self.advance()
        return None

    # ===== 型パース =====
    def parse_type(self) -> TypeNode:
        tok = self.peek()
        # 配列/スライス型: []T
        if tok.type == TokenType.LBRACKET:
            lbracket = self.advance()
            self.expect(TokenType.RBRACKET)
            elem_type = self.parse_type()
            return TypeNode(name=f"[]{elem_type.name}", line=lbracket.line, col=lbracket.col)

        if tok.type not in TYPE_TOKENS:
            raise ParseError(f"Expected type, got {tok.type.name}", tok.line, tok.col)
        self.advance()
        node = TypeNode(name=tok.value, line=tok.line, col=tok.col)
        return node

    # ===== 式パース（演算子優先順位付き） =====
    def parse_expr(self, min_prec: int = 0) -> Any:
        left = self.parse_unary()

        while True:
            tok = self.peek()
            op = tok.value
            prec = BINOP_PREC.get(op, -1)
            if prec < min_prec or prec == -1:
                break
            self.advance()
            right = self.parse_expr(prec + 1)
            left = BinOp(op=op, left=left, right=right, line=tok.line, col=tok.col)

        return left

    def parse_unary(self) -> Any:
        tok = self.peek()
        if tok.type in (TokenType.MINUS, TokenType.BANG):
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op=tok.value, operand=operand, line=tok.line, col=tok.col)
        return self.parse_postfix()

    def parse_postfix(self) -> Any:
        node = self.parse_primary()
        while True:
            tok = self.peek()
            if tok.type == TokenType.LPAREN:
                # 関数呼び出し
                self.advance()
                args = []
                while not self.check(TokenType.RPAREN, TokenType.EOF):
                    args.append(self.parse_expr())
                    if not self.match(TokenType.COMMA):
                        break
                self.expect(TokenType.RPAREN)
                node = Call(func=node, args=args, line=tok.line, col=tok.col)
            elif tok.type == TokenType.LBRACKET:
                # インデックスアクセス
                self.advance()
                idx = self.parse_expr()
                self.expect(TokenType.RBRACKET)
                node = Index(obj=node, idx=idx, line=tok.line, col=tok.col)
            elif tok.type == TokenType.DOT:
                # メンバアクセス
                self.advance()
                attr = self.expect(TokenType.IDENT)
                node = Member(obj=node, attr=attr.value, line=tok.line, col=tok.col)
            else:
                break
        return node

    def parse_primary(self) -> Any:
        tok = self.peek()

        if tok.type == TokenType.INT_LIT:
            self.advance()
            return IntLit(value=int(tok.value), line=tok.line, col=tok.col)

        if tok.type == TokenType.FLOAT_LIT:
            self.advance()
            return FloatLit(value=float(tok.value), line=tok.line, col=tok.col)

        if tok.type == TokenType.STRING_LIT:
            self.advance()
            return StringLit(value=tok.value, line=tok.line, col=tok.col)

        if tok.type == TokenType.TRUE:
            self.advance()
            return BoolLit(value=True, line=tok.line, col=tok.col)

        if tok.type == TokenType.FALSE:
            self.advance()
            return BoolLit(value=False, line=tok.line, col=tok.col)

        if tok.type == TokenType.NULL:
            self.advance()
            return NullLit(line=tok.line, col=tok.col)

        if tok.type == TokenType.IDENT:
            self.advance()
            return Ident(name=tok.value, line=tok.line, col=tok.col)

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr

        if tok.type == TokenType.LBRACKET:
            # 配列リテラル [1, 2, 3]
            self.advance()
            elements = []
            while not self.check(TokenType.RBRACKET, TokenType.EOF):
                elements.append(self.parse_expr())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RBRACKET)
            return ArrayLit(elements=elements, line=tok.line, col=tok.col)

        raise ParseError(f"Unexpected token: {tok.type.name} ({tok.value!r})", tok.line, tok.col)

    # ===== 文パース =====
    def parse_stmt(self) -> Any:
        tok = self.peek()

        # 短縮代入 (:=) による変数宣言: x := 10
        if tok.type == TokenType.IDENT and self.peek(1).type == TokenType.COLON_EQ:
            ident_tok = self.advance()  # consume IDENT
            self.advance()              # consume :=
            val = self.parse_expr()
            self.match(TokenType.SEMICOLON)
            return LetStmt(name=ident_tok.value, mutable=True, type_annotation=None, value=val, line=ident_tok.line, col=ident_tok.col)

        # out文 (KaniScript独自出力: out "hello" または out x)
        if tok.type == TokenType.OUT:
            self.advance()  # consume 'out'
            expr = self.parse_expr()
            self.match(TokenType.SEMICOLON)
            # 自動で println 呼び出しに変換
            return ExprStmt(expr=Call(func=Ident(name="println", line=tok.line, col=tok.col), args=[expr], line=tok.line, col=tok.col), line=tok.line, col=tok.col)

        # let文 / var文（let mutの短縮）
        if tok.type == TokenType.LET:
            return self.parse_let()
        if tok.type == TokenType.VAR:
            return self.parse_var()

        # const文
        if tok.type == TokenType.CONST:
            return self.parse_const()

        # return文
        if tok.type == TokenType.RETURN:
            self.advance()
            value = None
            if not self.check(TokenType.RBRACE, TokenType.SEMICOLON, TokenType.EOF):
                value = self.parse_expr()
            self.match(TokenType.SEMICOLON)
            return ReturnStmt(value=value, line=tok.line, col=tok.col)

        # if / when文 (KaniScript独自構文)
        if tok.type in (TokenType.IF, TokenType.WHEN):
            return self.parse_if()

        # for / each文 (KaniScript独自構文)
        if tok.type in (TokenType.FOR, TokenType.EACH):
            return self.parse_for()

        # while文
        if tok.type == TokenType.WHILE:
            return self.parse_while()

        # 式文（代入含む）
        expr = self.parse_expr()

        # 代入チェック
        if self.check(TokenType.EQ):
            self.advance()
            value = self.parse_expr()
            self.match(TokenType.SEMICOLON)
            return Assign(target=expr, value=value, line=tok.line, col=tok.col)

        # 複合代入チェック
        aug_ops = {
            TokenType.PLUS_EQ: '+=', TokenType.MINUS_EQ: '-=',
            TokenType.STAR_EQ: '*=', TokenType.SLASH_EQ: '/=',
        }
        if self.peek().type in aug_ops:
            op = aug_ops[self.advance().type]
            value = self.parse_expr()
            self.match(TokenType.SEMICOLON)
            return AugAssign(op=op, target=expr, value=value, line=tok.line, col=tok.col)

        self.match(TokenType.SEMICOLON)
        return ExprStmt(expr=expr, line=tok.line, col=tok.col)

    def parse_let(self) -> LetStmt:
        tok = self.advance()  # consume 'let'
        mutable = bool(self.match(TokenType.MUT))
        name = self.expect(TokenType.IDENT).value
        type_ann = None
        if self.match(TokenType.COLON):
            type_ann = self.parse_type()
        self.expect(TokenType.EQ)
        value = self.parse_expr()
        self.match(TokenType.SEMICOLON)
        return LetStmt(name=name, mutable=mutable, type_annotation=type_ann, value=value, line=tok.line, col=tok.col)

    def parse_var(self) -> LetStmt:
        """var x = 5  →  let mut x = 5 と同等"""
        tok = self.advance()  # consume 'var'
        name = self.expect(TokenType.IDENT).value
        type_ann = None
        if self.match(TokenType.COLON):
            type_ann = self.parse_type()
        self.expect(TokenType.EQ)
        value = self.parse_expr()
        self.match(TokenType.SEMICOLON)
        return LetStmt(name=name, mutable=True, type_annotation=type_ann, value=value, line=tok.line, col=tok.col)

    def parse_const(self) -> ConstStmt:
        tok = self.advance()  # consume 'const'
        name = self.expect(TokenType.IDENT).value
        type_ann = None
        if self.match(TokenType.COLON):
            type_ann = self.parse_type()
        self.expect(TokenType.EQ)
        value = self.parse_expr()
        self.match(TokenType.SEMICOLON)
        return ConstStmt(name=name, type_annotation=type_ann, value=value, line=tok.line, col=tok.col)

    def parse_if(self) -> IfStmt:
        tok = self.advance()  # consume 'if'
        condition = self.parse_expr()
        self.expect(TokenType.LBRACE)
        then_body = self.parse_block()
        else_body = []
        if self.match(TokenType.ELSE):
            if self.check(TokenType.IF, TokenType.WHEN):
                else_body = [self.parse_if()]
            else:
                self.expect(TokenType.LBRACE)
                else_body = self.parse_block()
        return IfStmt(condition=condition, then_body=then_body, else_body=else_body, line=tok.line, col=tok.col)

    def parse_for(self) -> ForStmt:
        tok = self.advance()  # consume 'for'
        var = self.expect(TokenType.IDENT).value
        self.expect(TokenType.IN)
        start = self.parse_expr()
        self.expect(TokenType.DOT_DOT)
        end = self.parse_expr()
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        return ForStmt(var=var, iter_start=start, iter_end=end, body=body, line=tok.line, col=tok.col)

    def parse_while(self) -> WhileStmt:
        tok = self.advance()  # consume 'while'
        condition = self.parse_expr()
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        return WhileStmt(condition=condition, body=body, line=tok.line, col=tok.col)

    def parse_block(self) -> List[Any]:
        stmts = []
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            stmts.append(self.parse_stmt())
        self.expect(TokenType.RBRACE)
        return stmts

    def is_fn_def(self) -> bool:
        """キーワードなし関数定義 (例: foo(...) { または foo(...) -> T {) かどうかを判定"""
        if not (self.check(TokenType.IDENT) and self.peek(1).type == TokenType.LPAREN):
            return False
        # 括弧の終わりを探す
        depth = 0
        i = 1
        while self.pos + i < len(self.tokens):
            t = self.peek(i).type
            if t == TokenType.LPAREN:
                depth += 1
            elif t == TokenType.RPAREN:
                depth -= 1
                if depth == 0:
                    # 閉じ括弧の次が ARROW (->) または LBRACE ({) なら関数定義
                    next_t = self.peek(i + 1).type
                    return next_t in (TokenType.ARROW, TokenType.LBRACE)
            i += 1
        return False

    def parse_fn(self, has_keyword: bool = True) -> FnDef:
        if has_keyword:
            tok = self.advance()  # consume 'fn' or 'def'
            name = self.expect(TokenType.IDENT).value
        else:
            tok = self.expect(TokenType.IDENT)
            name = tok.value

        self.expect(TokenType.LPAREN)
        params = []
        while not self.check(TokenType.RPAREN, TokenType.EOF):
            pname = self.expect(TokenType.IDENT).value
            self.expect(TokenType.COLON)
            ptype = self.parse_type()
            params.append(Param(name=pname, type_annotation=ptype, line=tok.line, col=tok.col))
            if not self.match(TokenType.COMMA):
                break
        self.expect(TokenType.RPAREN)
        ret_type = None
        if self.match(TokenType.ARROW):
            ret_type = self.parse_type()
        self.expect(TokenType.LBRACE)
        body = self.parse_block()

        # 暗黙return: 戻り値がある関数かつmain以外で、最後がExprStmtならReturnStmtに変換
        has_return_type = ret_type is not None and ret_type.name != "void"
        is_main = name == "main"
        if has_return_type and not is_main and body and isinstance(body[-1], ExprStmt):
            last = body[-1]
            body[-1] = ReturnStmt(value=last.expr, line=last.line, col=last.col)

        return FnDef(name=name, params=params, return_type=ret_type, body=body, line=tok.line, col=tok.col)

    def parse_struct(self) -> StructDef:
        tok = self.advance()  # consume 'struct'
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACE)
        fields = []
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            fname = self.expect(TokenType.IDENT).value
            self.expect(TokenType.COLON)
            ftype = self.parse_type()
            fields.append(StructField(name=fname, type_annotation=ftype, line=tok.line, col=tok.col))
            self.match(TokenType.COMMA)
        self.expect(TokenType.RBRACE)
        return StructDef(name=name, fields=fields, line=tok.line, col=tok.col)

    def parse(self) -> Program:
        stmts = []
        while not self.check(TokenType.EOF):
            tok = self.peek()
            if tok.type in (TokenType.FN, TokenType.DEF):
                stmts.append(self.parse_fn(has_keyword=True))
            elif self.is_fn_def():
                # キーワード不要の完全独自関数構文 (例: main() { ... } や fib(...) -> i64 { ... })
                stmts.append(self.parse_fn(has_keyword=False))
            elif tok.type == TokenType.STRUCT:
                stmts.append(self.parse_struct())
            elif tok.type in (TokenType.LET, TokenType.VAR, TokenType.CONST):
                stmts.append(self.parse_stmt())
            else:
                stmts.append(self.parse_stmt())
        return Program(stmts=stmts)
