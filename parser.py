from interpreter import *
import re


# 간단한 토큰 정규식
TOKEN_SPEC = [
    ('NUMBER',   r'\d+(\.\d*)?'),
    ('IF',       r'if\b'),
    ('ELSE',     r'else\b'),
    ('WHILE',    r'while\b'),
    ('IDENT',    r'[A-Za-z_]\w*'),
    ('EQ',       r'='),
    ('OP',       r'[+\-*/<>]'),
    ('COLON',    r':'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[ \t]+'),
    ('MISMATCH', r'.'),
]

TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)

def tokenize(code):
    tokens = []
    for mo in re.finditer(TOKEN_REGEX, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
            tokens.append((kind, value))
        elif kind in ('IF', 'ELSE', 'WHILE', 'IDENT', 'EQ', 'OP', 'COLON', 'LPAREN', 'RPAREN'):
            tokens.append((kind, value))
        elif kind == 'NEWLINE':
            tokens.append((kind, value))
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f"Unexpected token: {value}")
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ('EOF', '')

    def eat(self, token_type):
        tok = self.current()
        if tok[0] == token_type:
            self.pos += 1
            return tok
        raise SyntaxError(f"Expected token {token_type} but got {tok}")

    def parse_program(self):
        statements = []
        while self.current()[0] != 'EOF':
            stmt = self.parse_statement()
            statements.append(stmt)
            # 간단하게 NEWLINE을 소비
            if self.current()[0] == 'NEWLINE':
                self.eat('NEWLINE')
        return BlockNode(statements)

    def parse_statement(self):
        # NEWLINE 토큰들을 건너뛰기
        while self.current()[0] == 'NEWLINE':
            self.eat('NEWLINE')
        tok_type, _ = self.current()
        if tok_type == 'IF':
            return self.parse_if()
        elif tok_type == 'WHILE':
            return self.parse_while()
        elif self.current()[0] == 'IDENT' and self.peek()[0] == 'EQ':
            return self.parse_assignment()
        else:
            return self.parse_expr()

    def peek(self):
        return self.tokens[self.pos+1] if self.pos+1 < len(self.tokens) else ('EOF', '')

    def parse_assignment(self):
        ident = self.eat('IDENT')[1]
        self.eat('EQ')
        expr = self.parse_expr()
        return AssignNode(ident, expr)

    def parse_if(self):
        self.eat('IF')
        cond = self.parse_expr()
        self.eat('COLON')
        then_body = self.parse_block()
        else_body = None
        if self.current()[0] == 'ELSE':
            self.eat('ELSE')
            self.eat('COLON')
            else_body = self.parse_block()
        return IfNode(cond, then_body, else_body)

    def parse_while(self):
        self.eat('WHILE')
        cond = self.parse_expr()
        self.eat('COLON')
        body = self.parse_block()
        # 파서는 WhileNode를 생성하지 않고, 나중에 매크로 변환을 위해 if문 형태로 변환할 수 있음.
        # 여기서는 간단히 IfNode로 반환합니다.
        return IfNode(cond, body)

    def parse_block(self):
        # 여기서는 NEWLINE을 기준으로 블록을 구분한다고 가정.
        stmts = []
        while self.current()[0] != 'EOF' and self.current()[0] != 'DEDENT':
            stmt = self.parse_statement()
            stmts.append(stmt)
            if self.current()[0] == 'NEWLINE':
                self.eat('NEWLINE')
            else:
                break
        return BlockNode(stmts)

    def parse_expr(self):
        left = self.parse_term()
        # 비교 연산자와 산술 연산자 모두 처리하도록 확장합니다.
        while self.current()[0] == 'OP' and self.current()[1] in ('+', '-', '<', '>', '==', '!=', '<=', '>='):
            op = self.eat('OP')[1]
            right = self.parse_term()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.current()[0] == 'OP' and self.current()[1] in ('*', '/'):
            op = self.eat('OP')[1]
            right = self.parse_factor()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_factor(self):
        tok_type, value = self.current()
        if tok_type == 'NEWLINE':
            self.eat('NEWLINE')
            return self.parse_factor()
        if tok_type == 'NUMBER':
            self.eat('NUMBER')
            return LiteralNode(value)
        elif tok_type == 'IDENT':
            self.eat('IDENT')
            return VarNode(value)
        elif tok_type == 'LPAREN':
            self.eat('LPAREN')
            expr = self.parse_expr()
            self.eat('RPAREN')
            return expr
        else:
            raise SyntaxError(f"Unexpected token in factor: {self.current()}")

source_code = """
x = 7
if x > 5:
    x = x + 1
"""

tokens = tokenize(source_code)
parser = Parser(tokens)
ast_root = parser.parse_program()
print(ast_root)

interpreter = Interpreter()
interpreter.exec(ast_root)
print(interpreter.global_env.get("x"))
