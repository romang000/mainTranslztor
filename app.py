import streamlit as st
from enum import Enum, auto
import traceback

# ==========================================
# 0. ВИЗУАЛИЗАЦИЯ ОШИБОК
# ==========================================

class TranslationError(Exception):
    pass

def get_error_visual(text: str, pos: int, message: str) -> str:
    line_no = text.count('\n', 0, pos) + 1
    line_start = text.rfind('\n', 0, pos) + 1
    line_end = text.find('\n', pos)
    if line_end == -1: line_end = len(text)
    line_content = text[line_start:line_end]
    col = pos - line_start
    pointer = " " * col + "^"
    return f"Error on line {line_no}:\n{line_content}\n{pointer}\n--> {message}"

# ==========================================
# 1. КОМПИЛЯТОР (ЛОГИКА)
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
        self.type = type_; self.value = value; self.start_pos = start_pos
    def __repr__(self): return f"[{self.type.name}] '{self.value}'"

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
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right
class UnaryOp(ASTNode): 
    def __init__(self, expr, op): self.expr = expr; self.op = op
class ForLoop(ASTNode):
    def __init__(self, init, condition, update, body):
        self.init = init; self.condition = condition; self.update = update; self.body = body
class IfStatement(ASTNode):
    def __init__(self, condition, true_body, false_body=None):
        self.condition = condition; self.true_body = true_body; self.false_body = false_body
class WhileLoop(ASTNode):
    def __init__(self, condition, body): self.condition = condition; self.body = body
class DoWhileLoop(ASTNode):
    def __init__(self, body, condition): self.body = body; self.condition = condition

# --- Lexer ---
class Lexer:
    def __init__(self, text: str):
        self.text = text; self.pos = 0; self.current_char = self.text[0] if self.text else None

    def fail(self, message): raise TranslationError(get_error_visual(self.text, self.pos, message))
    def advance(self):
        self.pos += 1; self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
    def peek(self):
        peek_pos = self.pos + 1
        return self.text[peek_pos] if peek_pos < len(self.text) else None
    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace(): self.advance()

    def parse_identifier(self):
        start = self.pos; res = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            res += self.current_char; self.advance()
        keywords = {'public': TokenType.PUBLIC, 'class': TokenType.CLASS, 'static': TokenType.STATIC, 
                    'void': TokenType.VOID, 'int': TokenType.TYPE, 'boolean': TokenType.TYPE, 
                    'String': TokenType.TYPE, 'for': TokenType.FOR, 'if': TokenType.IF, 
                    'else': TokenType.ELSE, 'while': TokenType.WHILE, 'do': TokenType.DO}
        if res == 'System' and self.text[start:].startswith('System.out.println'):
            self.pos = start + 18; self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
            return Token(TokenType.PRINT, 'System.out.println', start)
        return Token(keywords.get(res, TokenType.ID), res, start)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace(): self.skip_whitespace(); continue
            start = self.pos
            if self.current_char.isalpha(): return self.parse_identifier()
            if self.current_char.isdigit():
                num = ''; 
                while self.current_char and self.current_char.isdigit(): num+=self.current_char; self.advance()
                return Token(TokenType.NUMBER, int(num), start)
            if self.current_char == '"':
                res = ''; self.advance()
                while self.current_char and self.current_char != '"': res+=self.current_char; self.advance()
                self.advance(); return Token(TokenType.STRING, res, start)
            
            singles = {'=':TokenType.ASSIGN, ';':TokenType.SEMI, '{':TokenType.LBRACE, '}':TokenType.RBRACE,
                       '(':TokenType.LPAREN, ')':TokenType.RPAREN, '[':TokenType.LBRACKET, ']':TokenType.RBRACKET}
            if self.current_char in singles:
                tk = Token(singles[self.current_char], self.current_char, start); self.advance(); return tk
            
            if self.current_char == '<':
                if self.peek() == '=': self.advance(); self.advance(); return Token(TokenType.LTE, '<=', start)
                self.advance(); return Token(TokenType.LT, '<', start)
            if self.current_char == '>':
                if self.peek() == '=': self.advance(); self.advance(); return Token(TokenType.GTE, '>=', start)
                self.advance(); return Token(TokenType.GT, '>', start)
            if self.current_char == '+':
                if self.peek() == '+': self.advance(); self.advance(); return Token(TokenType.INC, '++', start)
                self.advance(); return Token(TokenType.PLUS, '+', start)
            
            self.fail(f"Unexpected char '{self.current_char}'")
        return Token(TokenType.EOF, None, self.pos)

    def tokenize(self):
        tokens = []; 
        while True:
            tk = self.get_next_token(); tokens.append(tk)
            if tk.type == TokenType.EOF: break
        return tokens

# --- Parser ---
class Parser:
    def __init__(self, tokens, text): self.tokens = tokens; self.text = text; self.pos = 0; self.current_token = tokens[0]
    def fail(self, msg): raise TranslationError(get_error_visual(self.text, self.current_token.start_pos, msg))
    def eat(self, t):
        if self.current_token.type == t:
            self.pos += 1; 
            if self.pos < len(self.tokens): self.current_token = self.tokens[self.pos]
        else: self.fail(f"Expected {t.name}, got {self.current_token.type.name}")

    def parse_condition(self):
        left = self.current_token.value
        if self.current_token.type in (TokenType.ID, TokenType.NUMBER): self.eat(self.current_token.type)
        else: self.fail("Invalid condition left operand")
        op_map = {TokenType.LT:'<', TokenType.LTE:'<=', TokenType.GT:'>', TokenType.GTE:'>='}
        if self.current_token.type in op_map: op = op_map[self.current_token.type]; self.eat(self.current_token.type)
        else: self.fail("Expected comparison operator")
        right = self.current_token.value
        if self.current_token.type in (TokenType.ID, TokenType.NUMBER): self.eat(self.current_token.type)
        else: self.fail("Invalid condition right operand")
        return BinaryOp(left, op, right)

    def parse_statement(self):
        if self.current_token.type == TokenType.TYPE:
            t = self.current_token.value; self.eat(TokenType.TYPE)
            n = self.current_token.value; self.eat(TokenType.ID); self.eat(TokenType.ASSIGN)
            v = self.current_token.value
            if self.current_token.type in (TokenType.NUMBER, TokenType.STRING, TokenType.ID): self.eat(self.current_token.type)
            else: self.fail("Invalid value")
            self.eat(TokenType.SEMI); return VarDecl(t, n, v)
        elif self.current_token.type == TokenType.PRINT:
            self.eat(TokenType.PRINT); self.eat(TokenType.LPAREN); expr = self.current_token.value
            if self.current_token.type in (TokenType.STRING, TokenType.ID, TokenType.NUMBER): self.eat(self.current_token.type)
            self.eat(TokenType.RPAREN); self.eat(TokenType.SEMI); return PrintStatement(expr)
        elif self.current_token.type == TokenType.FOR:
            self.eat(TokenType.FOR); self.eat(TokenType.LPAREN); init = self.parse_statement(); cond = self.parse_condition(); self.eat(TokenType.SEMI)
            u = self.current_token.value; self.eat(TokenType.ID); self.eat(TokenType.INC); self.eat(TokenType.RPAREN)
            return ForLoop(init, cond, UnaryOp(u, "++"), self.parse_block())
        elif self.current_token.type == TokenType.IF:
            self.eat(TokenType.IF); self.eat(TokenType.LPAREN); cond = self.parse_condition(); self.eat(TokenType.RPAREN)
            tb = self.parse_block(); fb = None
            if self.current_token.type == TokenType.ELSE:
                self.eat(TokenType.ELSE)
                fb = [self.parse_statement()] if self.current_token.type == TokenType.IF else self.parse_block()
            return IfStatement(cond, tb, fb)
        elif self.current_token.type == TokenType.WHILE:
            self.eat(TokenType.WHILE); self.eat(TokenType.LPAREN); cond = self.parse_condition(); self.eat(TokenType.RPAREN); return WhileLoop(cond, self.parse_block())
        elif self.current_token.type == TokenType.DO:
            self.eat(TokenType.DO); body = self.parse_block(); self.eat(TokenType.WHILE); self.eat(TokenType.LPAREN)
            cond = self.parse_condition(); self.eat(TokenType.RPAREN); self.eat(TokenType.SEMI); return DoWhileLoop(body, cond)
        elif self.current_token.type == TokenType.ID:
            n = self.current_token.value; self.eat(TokenType.ID); self.eat(TokenType.INC); self.eat(TokenType.SEMI); return UnaryOp(n, "++")
        else: self.fail("Unknown statement")

    def parse_block(self):
        self.eat(TokenType.LBRACE); stmts = []
        while self.current_token.type not in (TokenType.RBRACE, TokenType.EOF): stmts.append(self.parse_statement())
        self.eat(TokenType.RBRACE); return stmts

    def parse_method(self):
        self.eat(TokenType.PUBLIC); self.eat(TokenType.STATIC)
        rt = "void"
        if self.current_token.type == TokenType.VOID: self.eat(TokenType.VOID)
        else: rt = self.current_token.value; self.eat(TokenType.TYPE)
        name = self.current_token.value; self.eat(TokenType.ID); self.eat(TokenType.LPAREN)
        if self.current_token.type == TokenType.TYPE: 
             self.eat(TokenType.TYPE); self.eat(TokenType.LBRACKET); self.eat(TokenType.RBRACKET); self.eat(TokenType.ID)
        self.eat(TokenType.RPAREN); return MethodDecl(name, rt, [], self.parse_block())

    def parse_class(self):
        self.eat(TokenType.PUBLIC); self.eat(TokenType.CLASS); name = self.current_token.value; self.eat(TokenType.ID)
        self.eat(TokenType.LBRACE); methods = []
        while self.current_token.type != TokenType.RBRACE: methods.append(self.parse_method())
        self.eat(TokenType.RBRACE); return ClassDecl(name, methods)

    def parse(self): 
        classes = []
        while self.current_token.type != TokenType.EOF: classes.append(self.parse_class())
        return Program(classes)

# --- Generator ---
class CSharpGenerator:
    def __init__(self): self.lines = []; self.indent = 0
    def add(self, s): self.lines.append("    " * self.indent + s)
    def visit(self, node):
        if isinstance(node, Program):
            self.add("using System;"); 
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
            v = node.expression; 
            if isinstance(v, str) and not v.isidentifier() and not v.isdigit(): v = f'"{v}"'
            self.add(f"Console.WriteLine({v});")
        elif isinstance(node, UnaryOp): self.add(f"{node.expr}{node.op};")
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
            self.add("do"); self.add("{"); self.indent+=1; 
            for s in node.body: self.visit(s)
            self.indent-=1; cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            self.add(f"}} while ({cond});")

    def generate(self, tree): self.visit(tree); return "\n".join(self.lines)

# --- Helper to print AST ---
def format_ast(node, level=0):
    indent = "  " * level
    result = f"{indent}{node.__class__.__name__}"
    if isinstance(node, Program):
        for c in node.classes: result += "\n" + format_ast(c, level+1)
    elif isinstance(node, ClassDecl):
        result += f": {node.name}"
        for m in node.methods: result += "\n" + format_ast(m, level+1)
    elif isinstance(node, MethodDecl):
        result += f": {node.name}"
        for s in node.body: result += "\n" + format_ast(s, level+1)
    elif isinstance(node, VarDecl):
        result += f" ({node.var_type} {node.name} = {node.value})"
    elif isinstance(node, PrintStatement):
        result += f" ({node.expression})"
    elif isinstance(node, BinaryOp):
        result += f" ({node.left} {node.op} {node.right})"
    elif isinstance(node, ForLoop):
        result += "\n" + format_ast(node.init, level+1)
        result += "\n" + format_ast(node.condition, level+1)
        for s in node.body: result += "\n" + format_ast(s, level+1)
    elif isinstance(node, IfStatement):
        result += "\n" + format_ast(node.condition, level+1)
        result += f"\n{indent}  Then:"
        for s in node.true_body: result += "\n" + format_ast(s, level+2)
        if node.false_body:
            result += f"\n{indent}  Else:"
            for s in node.false_body: result += "\n" + format_ast(s, level+2)
    elif isinstance(node, WhileLoop):
        result += "\n" + format_ast(node.condition, level+1)
        for s in node.body: result += "\n" + format_ast(s, level+1)
    elif isinstance(node, DoWhileLoop):
        result += " (Do)"
        for s in node.body: result += "\n" + format_ast(s, level+1)
        result += "\n" + format_ast(node.condition, level+1)
    return result

# ==========================================
# 2. STREAMLIT UI
# ==========================================

st.set_page_config(layout="wide", page_title="Compiler Demo", page_icon="☕")

st.title("Java to C# Transpiler 🚀")
st.markdown("Полноценный пайплайн компиляции: Лексер -> Парсер (AST) -> Генератор.")

# Создаем 3 колонки
col_input, col_process, col_output = st.columns([1, 1, 1])

DEFAULT_CODE = """public class Demo {
    public static void main(String[] args) {
        int x = 10;
        if (x > 5) {
            System.out.println("Java works!");
        }
        
        for (int i=0; i<3; i++) {
            System.out.println(i);
        }
    }
}"""

with col_input:
    st.header("1. Input (Java)")
    java_code = st.text_area("Write your code here:", value=DEFAULT_CODE, height=500, key="input_area")
    translate_btn = st.button("▶ Compile & Translate", type="primary", use_container_width=True)

# Инициализируем переменные для UI
tokens_display = []
ast_display = ""
result_code = ""
error_msg = None

if translate_btn and java_code:
    try:
        # 1. Lexing
        lexer = Lexer(java_code)
        tokens = lexer.tokenize()
        tokens_display = [str(t) for t in tokens]
        
        # 2. Parsing
        parser = Parser(tokens, java_code)
        ast = parser.parse()
        ast_display = format_ast(ast)
        
        # 3. Generation
        generator = CSharpGenerator()
        result_code = generator.generate(ast)
        
    except TranslationError as e:
        error_msg = str(e)
    except Exception as e:
        error_msg = f"Internal System Error:\n{traceback.format_exc()}"

# Отображение 2-й колонки (Процесс)
with col_process:
    st.header("2. Process (Internals)")
    
    # Вкладки для токенов и AST
    tab1, tab2 = st.tabs(["🧩 Tokens (Lexer)", "🌳 AST Structure (Parser)"])
    
    with tab1:
        if tokens_display:
            st.code("\n".join(tokens_display), language="text")
        else:
            st.info("Waiting for input...")
            
    with tab2:
        if ast_display:
            st.code(ast_display, language="text")
        else:
            st.info("Waiting for input...")

# Отображение 3-й колонки (Результат)
with col_output:
    st.header("3. Output (C#)")
    if error_msg:
        st.error(error_msg)
    elif result_code:
        st.code(result_code, language="csharp")
        st.success("Compilation Successful!")
    else:
        st.info("Ready to translate.")