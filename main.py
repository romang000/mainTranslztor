import uvicorn
import traceback
from typing import List, Any
from enum import Enum, auto
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

# ==========================================
# 0. ERROR HANDLING HELPER
# ==========================================

class TranslationError(Exception):
    pass

def get_error_visual(text: str, pos: int, message: str) -> str:
    """
    Генерирует красивое сообщение об ошибке с контекстом строки.
    """
    # Вычисляем номер строки
    line_no = text.count('\n', 0, pos) + 1
    
    # Находим начало и конец строки, где произошла ошибка
    line_start = text.rfind('\n', 0, pos) + 1
    line_end = text.find('\n', pos)
    if line_end == -1: 
        line_end = len(text)
    
    # Извлекаем саму строку кода
    line_content = text[line_start:line_end]
    
    # Вычисляем позицию курсора внутри строки
    col = pos - line_start
    
    # Формируем указатель (стрелочку)
    pointer = " " * col + "^"
    
    return f"Error on line {line_no}:\n{line_content}\n{pointer}\n--> {message}"

# ==========================================
# 1. DEFINITIONS
# ==========================================

class TokenType(Enum):
    PUBLIC = auto(); CLASS = auto(); STATIC = auto(); VOID = auto()
    TYPE = auto(); FOR = auto(); IF = auto(); ELSE = auto()
    WHILE = auto(); DO = auto()
    
    ID = auto(); NUMBER = auto(); STRING = auto()
    
    LBRACE = auto(); RBRACE = auto(); LPAREN = auto(); RPAREN = auto()
    LBRACKET = auto(); RBRACKET = auto(); SEMI = auto(); ASSIGN = auto()
    
    LT = auto(); LTE = auto(); GT = auto(); GTE = auto()
    PLUS = auto(); INC = auto()
    
    PRINT = auto(); EOF = auto()

class Token:
    def __init__(self, type_: TokenType, value: str, start_pos: int):
        self.type = type_
        self.value = value
        self.start_pos = start_pos  # <-- Важно: храним позицию начала токена
    
    def __repr__(self): 
        return f"Token({self.type.name}, '{self.value}')"

# --- AST Nodes ---
class ASTNode: pass
class Program(ASTNode):
    def __init__(self, classes): self.classes = classes
class ClassDecl(ASTNode):
    def __init__(self, name, methods): self.name = name; self.methods = methods
class MethodDecl(ASTNode):
    def __init__(self, name, ret, args, body):
        self.name = name; self.return_type = ret; self.args = args; self.body = body
class VarDecl(ASTNode):
    def __init__(self, t, n, v): self.var_type = t; self.name = n; self.value = v
class PrintStatement(ASTNode):
    def __init__(self, expr): self.expression = expr
class BinaryOp(ASTNode): 
    def __init__(self, left, op, right):
        self.left = left; self.op = op; self.right = right
class UnaryOp(ASTNode): 
    def __init__(self, expr, op):
        self.expr = expr; self.op = op
class ForLoop(ASTNode):
    def __init__(self, init, condition, update, body):
        self.init = init; self.condition = condition; self.update = update; self.body = body
class IfStatement(ASTNode):
    def __init__(self, condition, true_body, false_body=None):
        self.condition = condition; self.true_body = true_body; self.false_body = false_body
class WhileLoop(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition; self.body = body
class DoWhileLoop(ASTNode):
    def __init__(self, body, condition):
        self.body = body; self.condition = condition

# ==========================================
# 2. LEXER
# ==========================================

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if self.text else None

    def fail(self, message):
        raise TranslationError(get_error_visual(self.text, self.pos, message))

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos < len(self.text): return self.text[peek_pos]
        return None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def parse_identifier(self):
        start_pos = self.pos
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        keywords = {
            'public': TokenType.PUBLIC, 'class': TokenType.CLASS,
            'static': TokenType.STATIC, 'void': TokenType.VOID,
            'int': TokenType.TYPE, 'boolean': TokenType.TYPE, 'String': TokenType.TYPE,
            'for': TokenType.FOR, 'if': TokenType.IF, 'else': TokenType.ELSE,
            'while': TokenType.WHILE, 'do': TokenType.DO
        }
        
        if result == 'System':
            # Проверка System.out.println
            remaining = self.text[start_pos:]
            if remaining.startswith('System.out.println'):
                # Пропускаем .out.println (12 символов после System (6)) -> итого 18, но мы уже считали System
                # Проще просто сдвинуть pos
                self.pos = start_pos + 18
                self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                return Token(TokenType.PRINT, 'System.out.println', start_pos)
        
        return Token(keywords.get(result, TokenType.ID), result, start_pos)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace(): self.skip_whitespace(); continue
            
            start_pos = self.pos

            if self.current_char.isalpha(): return self.parse_identifier()
            
            if self.current_char.isdigit():
                num = ''
                while self.current_char is not None and self.current_char.isdigit():
                    num += self.current_char; self.advance()
                return Token(TokenType.NUMBER, int(num), start_pos)

            if self.current_char == '"': 
                res = ''; self.advance() # skip "
                while self.current_char is not None and self.current_char != '"':
                    res += self.current_char; self.advance()
                if self.current_char != '"': self.fail("Unclosed string literal")
                self.advance() # skip closing "
                return Token(TokenType.STRING, res, start_pos)
            
            # Operators map
            single_chars = {
                '=': TokenType.ASSIGN, ';': TokenType.SEMI,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET
            }
            
            if self.current_char in single_chars:
                tk = Token(single_chars[self.current_char], self.current_char, start_pos)
                self.advance()
                return tk

            if self.current_char == '<':
                if self.peek() == '=': self.advance(); self.advance(); return Token(TokenType.LTE, '<=', start_pos)
                self.advance(); return Token(TokenType.LT, '<', start_pos)
            if self.current_char == '>':
                if self.peek() == '=': self.advance(); self.advance(); return Token(TokenType.GTE, '>=', start_pos)
                self.advance(); return Token(TokenType.GT, '>', start_pos)
            if self.current_char == '+':
                if self.peek() == '+': self.advance(); self.advance(); return Token(TokenType.INC, '++', start_pos)
                self.advance(); return Token(TokenType.PLUS, '+', start_pos)

            self.fail(f"Unexpected character: '{self.current_char}'")
        
        return Token(TokenType.EOF, None, self.pos)

    def tokenize(self):
        tokens = []
        while True:
            tk = self.get_next_token()
            tokens.append(tk)
            if tk.type == TokenType.EOF: break
        return tokens

# ==========================================
# 3. PARSER
# ==========================================

class Parser:
    def __init__(self, tokens: List[Token], source_text: str):
        self.tokens = tokens
        self.source_text = source_text
        self.pos = 0
        self.current_token = tokens[0]

    def fail(self, message):
        # Используем start_pos текущего токена для контекста ошибки
        raise TranslationError(get_error_visual(self.source_text, self.current_token.start_pos, message))

    def eat(self, t):
        if self.current_token.type == t:
            self.pos += 1
            if self.pos < len(self.tokens): self.current_token = self.tokens[self.pos]
        else:
            self.fail(f"Expected {t.name}, but got {self.current_token.type.name} ('{self.current_token.value}')")

    def parse_condition(self):
        left = self.current_token.value
        if self.current_token.type in (TokenType.ID, TokenType.NUMBER): self.eat(self.current_token.type)
        else: self.fail("Invalid condition: expected ID or Number")
        
        op_map = {TokenType.LT: '<', TokenType.LTE: '<=', TokenType.GT: '>', TokenType.GTE: '>='}
        if self.current_token.type in op_map:
            op = op_map[self.current_token.type]
            self.eat(self.current_token.type)
        else: self.fail("Expected comparison operator (<, >, <=, >=)")
        
        right = self.current_token.value
        if self.current_token.type in (TokenType.ID, TokenType.NUMBER): self.eat(self.current_token.type)
        else: self.fail("Invalid condition right operand")
        
        return BinaryOp(left, op, right)

    def parse_statement(self):
        if self.current_token.type == TokenType.TYPE:
            t = self.current_token.value; self.eat(TokenType.TYPE)
            n = self.current_token.value; self.eat(TokenType.ID)
            self.eat(TokenType.ASSIGN)
            val = self.current_token.value
            if self.current_token.type in (TokenType.NUMBER, TokenType.STRING, TokenType.ID): self.eat(self.current_token.type)
            else: self.fail("Invalid value definition")
            self.eat(TokenType.SEMI)
            return VarDecl(t, n, val)
        
        elif self.current_token.type == TokenType.PRINT:
            self.eat(TokenType.PRINT); self.eat(TokenType.LPAREN)
            expr = self.current_token.value
            if self.current_token.type in [TokenType.STRING, TokenType.ID, TokenType.NUMBER]: self.eat(self.current_token.type)
            self.eat(TokenType.RPAREN); self.eat(TokenType.SEMI)
            return PrintStatement(expr)
        
        elif self.current_token.type == TokenType.FOR:
            self.eat(TokenType.FOR); self.eat(TokenType.LPAREN)
            init = self.parse_statement() 
            cond = self.parse_condition(); self.eat(TokenType.SEMI)
            u_var = self.current_token.value; self.eat(TokenType.ID)
            self.eat(TokenType.INC)
            self.eat(TokenType.RPAREN)
            return ForLoop(init, cond, UnaryOp(u_var, "++"), self.parse_block())

        elif self.current_token.type == TokenType.IF:
            self.eat(TokenType.IF); self.eat(TokenType.LPAREN)
            cond = self.parse_condition()
            self.eat(TokenType.RPAREN)
            true_body = self.parse_block()
            false_body = None
            if self.current_token.type == TokenType.ELSE:
                self.eat(TokenType.ELSE)
                if self.current_token.type == TokenType.IF:
                    false_body = [self.parse_statement()]
                else:
                    false_body = self.parse_block()
            return IfStatement(cond, true_body, false_body)

        elif self.current_token.type == TokenType.WHILE:
            self.eat(TokenType.WHILE); self.eat(TokenType.LPAREN)
            cond = self.parse_condition()
            self.eat(TokenType.RPAREN)
            body = self.parse_block()
            return WhileLoop(cond, body)

        elif self.current_token.type == TokenType.DO:
            self.eat(TokenType.DO)
            body = self.parse_block()
            self.eat(TokenType.WHILE); self.eat(TokenType.LPAREN)
            cond = self.parse_condition()
            self.eat(TokenType.RPAREN); self.eat(TokenType.SEMI)
            return DoWhileLoop(body, cond)

        elif self.current_token.type == TokenType.ID:
            name = self.current_token.value; self.eat(TokenType.ID)
            self.eat(TokenType.INC); self.eat(TokenType.SEMI)
            return UnaryOp(name, "++")

        else:
            self.fail(f"Unknown statement or unexpected token '{self.current_token.value}'")

    def parse_block(self):
        self.eat(TokenType.LBRACE)
        stmts = []
        while self.current_token.type not in (TokenType.RBRACE, TokenType.EOF):
            stmts.append(self.parse_statement())
        self.eat(TokenType.RBRACE)
        return stmts

    def parse_method(self):
        self.eat(TokenType.PUBLIC); self.eat(TokenType.STATIC)
        rt = "void"; 
        if self.current_token.type == TokenType.VOID: self.eat(TokenType.VOID)
        else: rt = self.current_token.value; self.eat(TokenType.TYPE)
        name = self.current_token.value; self.eat(TokenType.ID)
        self.eat(TokenType.LPAREN)
        if self.current_token.type == TokenType.TYPE: 
             self.eat(TokenType.TYPE); self.eat(TokenType.LBRACKET); self.eat(TokenType.RBRACKET); self.eat(TokenType.ID)
        self.eat(TokenType.RPAREN)
        return MethodDecl(name, rt, [], self.parse_block())

    def parse_class(self):
        self.eat(TokenType.PUBLIC); self.eat(TokenType.CLASS)
        name = self.current_token.value; self.eat(TokenType.ID)
        self.eat(TokenType.LBRACE)
        methods = []
        while self.current_token.type != TokenType.RBRACE: methods.append(self.parse_method())
        self.eat(TokenType.RBRACE)
        return ClassDecl(name, methods)

    def parse(self): 
        classes = []
        while self.current_token.type != TokenType.EOF:
            classes.append(self.parse_class())
        return Program(classes)

# ==========================================
# 4. GENERATOR (Без изменений)
# ==========================================

class CSharpGenerator:
    def __init__(self): self.lines = []; self.indent = 0
    def add(self, s): self.lines.append("    " * self.indent + s)
    
    def visit(self, node):
        if isinstance(node, Program):
            self.add("using System;")
            for c in node.classes: self.visit(c)
        elif isinstance(node, ClassDecl):
            self.add(f"public class {node.name}"); self.add("{"); self.indent+=1
            for m in node.methods: self.visit(m)
            self.indent-=1; self.add("}")
        elif isinstance(node, MethodDecl):
            n = "Main" if node.name == "main" else node.name
            self.add(f"public static {node.return_type} {n}(string[] args)"); self.add("{"); self.indent+=1
            for s in node.body: self.visit(s)
            self.indent-=1; self.add("}")
        elif isinstance(node, VarDecl):
            t = "string" if node.var_type == "String" else node.var_type
            v = f'"{node.value}"' if node.var_type == "String" and isinstance(node.value, str) and not node.value.isdigit() else node.value
            self.add(f"{t} {node.name} = {v};")
        elif isinstance(node, PrintStatement):
            v = node.expression
            if isinstance(v, str) and not v.isidentifier() and not v.isdigit(): v = f'"{v}"'
            self.add(f"Console.WriteLine({v});")
        elif isinstance(node, UnaryOp):
            self.add(f"{node.expr}{node.op};")
        elif isinstance(node, ForLoop):
            init = f"{node.init.var_type} {node.init.name} = {node.init.value}"
            cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            upd = f"{node.update.expr}{node.update.op}"
            self.add(f"for ({init}; {cond}; {upd})"); self.add("{"); self.indent+=1
            for s in node.body: self.visit(s)
            self.indent-=1; self.add("}")
        elif isinstance(node, IfStatement):
            cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            self.add(f"if ({cond})"); self.add("{"); self.indent+=1
            for s in node.true_body: self.visit(s)
            self.indent-=1; self.add("}")
            if node.false_body:
                self.add("else"); self.add("{"); self.indent+=1
                for s in node.false_body: self.visit(s)
                self.indent-=1; self.add("}")
        elif isinstance(node, WhileLoop):
            cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            self.add(f"while ({cond})"); self.add("{"); self.indent+=1
            for s in node.body: self.visit(s)
            self.indent-=1; self.add("}")
        elif isinstance(node, DoWhileLoop):
            self.add("do"); self.add("{"); self.indent+=1
            for s in node.body: self.visit(s)
            self.indent-=1
            cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            self.add(f"}} while ({cond});")

    def generate(self, tree): self.visit(tree); return "\n".join(self.lines)

# ==========================================
# 5. FASTAPI
# ==========================================

app = FastAPI()

@app.post("/translate", response_class=PlainTextResponse)
async def translate_text(request: Request):
    try:
        body_bytes = await request.body()
        java_code = body_bytes.decode("utf-8")
        if not java_code.strip(): 
            return "Error: Empty code provided"

        # 1. Lexer
        lexer = Lexer(java_code)
        tokens = lexer.tokenize()
        
        # 2. Parser (теперь передаем и исходный текст для ошибок)
        parser = Parser(tokens, java_code)
        ast = parser.parse()
        
        # 3. Generator
        generator = CSharpGenerator()
        return generator.generate(ast)
    
    except TranslationError as e:
        # Ловим наши красивые ошибки
        return str(e)
    except Exception as e:
        # Ловим системные ошибки (баги транслятора)
        return f"Internal Error: {str(e)}\n{traceback.format_exc()}"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)