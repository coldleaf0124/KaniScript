"""
Zenpo Lexer — ソースコードをトークン列に変換する
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    # リテラル
    INT_LIT    = auto()
    FLOAT_LIT  = auto()
    STRING_LIT = auto()
    BOOL_LIT   = auto()

    # 識別子・キーワード
    IDENT      = auto()
    FN         = auto()
    DEF        = auto()   # fn の別名（シンプル構文）
    LET        = auto()
    MUT        = auto()
    VAR        = auto()   # let mut の短縮形
    RETURN     = auto()
    IF         = auto()
    WHEN       = auto()   # KaniScript 独自条件文 (when)
    ELSE       = auto()
    FOR        = auto()
    EACH       = auto()   # KaniScript 独自ループ文 (each)
    IN         = auto()
    WHILE      = auto()
    OUT        = auto()   # KaniScript 独自出力文 (out)
    STRUCT     = auto()
    IMPORT     = auto()
    CONST      = auto()
    TRUE       = auto()
    FALSE      = auto()
    NULL       = auto()

    # 型
    TYPE_I8    = auto()
    TYPE_I16   = auto()
    TYPE_I32   = auto()
    TYPE_I64   = auto()
    TYPE_U8    = auto()
    TYPE_U16   = auto()
    TYPE_U32   = auto()
    TYPE_U64   = auto()
    TYPE_F32   = auto()
    TYPE_F64   = auto()
    TYPE_BOOL  = auto()
    TYPE_STR   = auto()
    TYPE_VOID  = auto()

    # 演算子
    PLUS       = auto()
    MINUS      = auto()
    STAR       = auto()
    SLASH      = auto()
    PERCENT    = auto()
    EQ         = auto()
    EQ_EQ      = auto()
    BANG_EQ    = auto()
    LT         = auto()
    GT         = auto()
    LT_EQ      = auto()
    GT_EQ      = auto()
    AND_AND    = auto()
    OR_OR      = auto()
    BANG       = auto()
    AMP        = auto()
    PIPE       = auto()
    CARET      = auto()
    SHL        = auto()
    SHR        = auto()
    PLUS_EQ    = auto()
    MINUS_EQ   = auto()
    STAR_EQ    = auto()
    SLASH_EQ   = auto()
    DOT_DOT    = auto()

    # 区切り文字
    LPAREN     = auto()
    RPAREN     = auto()
    LBRACE     = auto()
    RBRACE     = auto()
    LBRACKET   = auto()
    RBRACKET   = auto()
    COMMA      = auto()
    COLON      = auto()
    COLON_EQ   = auto()   # := (短縮変数宣言)
    SEMICOLON  = auto()
    ARROW      = auto()
    DOT        = auto()

    # 特殊
    EOF        = auto()


KEYWORDS = {
    "fn": TokenType.FN, "def": TokenType.DEF,
    "let": TokenType.LET, "mut": TokenType.MUT, "var": TokenType.VAR,
    "return": TokenType.RETURN,
    "if": TokenType.IF, "when": TokenType.WHEN, "else": TokenType.ELSE,
    "for": TokenType.FOR, "each": TokenType.EACH, "in": TokenType.IN, "while": TokenType.WHILE,
    "out": TokenType.OUT,
    "struct": TokenType.STRUCT, "import": TokenType.IMPORT, "const": TokenType.CONST,
    "true": TokenType.TRUE, "false": TokenType.FALSE, "null": TokenType.NULL,
    "i8": TokenType.TYPE_I8, "i16": TokenType.TYPE_I16,
    "i32": TokenType.TYPE_I32, "i64": TokenType.TYPE_I64,
    "u8": TokenType.TYPE_U8,  "u16": TokenType.TYPE_U16,
    "u32": TokenType.TYPE_U32, "u64": TokenType.TYPE_U64,
    "f32": TokenType.TYPE_F32, "f64": TokenType.TYPE_F64,
    "bool": TokenType.TYPE_BOOL, "str": TokenType.TYPE_STR, "void": TokenType.TYPE_VOID,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


class LexError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"[Zenpo Lex Error] {msg} at line {line}, col {col}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def error(self, msg: str):
        raise LexError(msg, self.line, self.col)

    def peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx >= len(self.source):
            return None
        return self.source[idx]

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.peek()
            if ch in (' ', '\t', '\r', '\n'):
                self.advance()
            elif ch == '/' and self.peek(1) == '/':
                while self.pos < len(self.source) and self.peek() != '\n':
                    self.advance()
            elif ch == '/' and self.peek(1) == '*':
                self.advance(); self.advance()
                while self.pos < len(self.source):
                    if self.peek() == '*' and self.peek(1) == '/':
                        self.advance(); self.advance()
                        break
                    self.advance()
            else:
                break

    def read_string(self) -> Token:
        line, col = self.line, self.col
        self.advance()
        buf = []
        while self.pos < len(self.source):
            ch = self.peek()
            if ch == '\\':
                self.advance()
                esc = self.advance()
                escape_map = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\'}
                buf.append(escape_map.get(esc, esc))
            elif ch == '"':
                self.advance()
                break
            elif ch is None:
                self.error("Unterminated string literal")
            else:
                buf.append(self.advance())
        return Token(TokenType.STRING_LIT, ''.join(buf), line, col)

    def read_number(self) -> Token:
        line, col = self.line, self.col
        buf = []
        is_float = False
        while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == '_'):
            ch = self.advance()
            if ch != '_':
                buf.append(ch)
        if self.peek() == '.' and self.peek(1) and self.peek(1).isdigit():
            is_float = True
            buf.append(self.advance())
            while self.pos < len(self.source) and self.peek().isdigit():
                buf.append(self.advance())
        if self.peek() in ('f', 'F'):
            is_float = True
            self.advance()
        return Token(TokenType.FLOAT_LIT if is_float else TokenType.INT_LIT, ''.join(buf), line, col)

    def read_ident_or_keyword(self) -> Token:
        line, col = self.line, self.col
        buf = []
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
            buf.append(self.advance())
        word = ''.join(buf)
        tok_type = KEYWORDS.get(word, TokenType.IDENT)
        return Token(tok_type, word, line, col)

    def tokenize(self) -> List[Token]:
        while True:
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
                break

            line, col = self.line, self.col
            ch = self.peek()

            if ch == '"':
                self.tokens.append(self.read_string())
            elif ch.isdigit():
                self.tokens.append(self.read_number())
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self.read_ident_or_keyword())
            else:
                self.advance()
                nxt = self.peek()
                def tok(t): return Token(t, ch, line, col)
                def tok2(t, c2): return Token(t, ch + c2, line, col)

                if ch == '+':
                    if nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.PLUS_EQ, '='))
                    else: self.tokens.append(tok(TokenType.PLUS))
                elif ch == '-':
                    if nxt == '>': self.advance(); self.tokens.append(tok2(TokenType.ARROW, '>'))
                    elif nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.MINUS_EQ, '='))
                    else: self.tokens.append(tok(TokenType.MINUS))
                elif ch == '*':
                    if nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.STAR_EQ, '='))
                    else: self.tokens.append(tok(TokenType.STAR))
                elif ch == '/':
                    if nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.SLASH_EQ, '='))
                    else: self.tokens.append(tok(TokenType.SLASH))
                elif ch == '%': self.tokens.append(tok(TokenType.PERCENT))
                elif ch == '=':
                    if nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.EQ_EQ, '='))
                    else: self.tokens.append(tok(TokenType.EQ))
                elif ch == '!':
                    if nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.BANG_EQ, '='))
                    else: self.tokens.append(tok(TokenType.BANG))
                elif ch == '<':
                    if nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.LT_EQ, '='))
                    elif nxt == '<': self.advance(); self.tokens.append(tok2(TokenType.SHL, '<'))
                    else: self.tokens.append(tok(TokenType.LT))
                elif ch == '>':
                    if nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.GT_EQ, '='))
                    elif nxt == '>': self.advance(); self.tokens.append(tok2(TokenType.SHR, '>'))
                    else: self.tokens.append(tok(TokenType.GT))
                elif ch == '&':
                    if nxt == '&': self.advance(); self.tokens.append(tok2(TokenType.AND_AND, '&'))
                    else: self.tokens.append(tok(TokenType.AMP))
                elif ch == '|':
                    if nxt == '|': self.advance(); self.tokens.append(tok2(TokenType.OR_OR, '|'))
                    else: self.tokens.append(tok(TokenType.PIPE))
                elif ch == '^': self.tokens.append(tok(TokenType.CARET))
                elif ch == '.':
                    if nxt == '.': self.advance(); self.tokens.append(tok2(TokenType.DOT_DOT, '.'))
                    else: self.tokens.append(tok(TokenType.DOT))
                elif ch == '(': self.tokens.append(tok(TokenType.LPAREN))
                elif ch == ')': self.tokens.append(tok(TokenType.RPAREN))
                elif ch == '{': self.tokens.append(tok(TokenType.LBRACE))
                elif ch == '}': self.tokens.append(tok(TokenType.RBRACE))
                elif ch == '[': self.tokens.append(tok(TokenType.LBRACKET))
                elif ch == ']': self.tokens.append(tok(TokenType.RBRACKET))
                elif ch == ',': self.tokens.append(tok(TokenType.COMMA))
                elif ch == ':':
                    if nxt == '=': self.advance(); self.tokens.append(tok2(TokenType.COLON_EQ, '='))
                    else: self.tokens.append(tok(TokenType.COLON))
                elif ch == ';': self.tokens.append(tok(TokenType.SEMICOLON))
                else:
                    self.error(f"Unexpected character: {ch!r}")

        return self.tokens
