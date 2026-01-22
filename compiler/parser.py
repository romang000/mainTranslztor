from .tokens import TokenType
from .ast_nodes import *
from .errors import TranslationError, get_error_visual

class Parser:
    def __init__(self, tokens, text):
        self.tokens = tokens
        self.text = text
        self.pos = 0
        self.current_token = tokens[0]

    def fail(self, msg):
        raise TranslationError(get_error_visual(self.text, self.current_token.start_pos, msg))

    def eat(self, t):
        if self.current_token.type == t:
            self.pos += 1
            if self.pos < len(self.tokens): self.current_token = self.tokens[self.pos]
        else:
            self.fail(f"Expected {t.name}, got {self.current_token.type.name}")

    # --- НОВАЯ ФУНКЦИЯ: Парсинг выражений (числа, переменные, операции, вызовы функций) ---
    def parse_expression(self):
        # Сначала парсим левую часть (число, строку или переменную)
        left = self.current_token.value
        is_id = False
        if self.current_token.type in (TokenType.ID, TokenType.NUMBER, TokenType.STRING):
            is_id = self.current_token.type == TokenType.ID
            self.eat(self.current_token.type)
        else:
            self.fail("Expected value (ID, Number, String)")

        # Проверяем, является ли это вызовом функции (ID + LPAREN)
        if is_id and self.current_token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            args = []
            # Парсим аргументы функции (разделены запятыми)
            if self.current_token.type != TokenType.RPAREN:
                args.append(self.parse_simple_expression())
                # Используем запятую как разделитель
                while self.current_token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    args.append(self.parse_simple_expression())
            self.eat(TokenType.RPAREN)
            return FunctionCall(left, args)

        # Проверяем бинарные операции
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS, TokenType.MULT, TokenType.DIV):
            op_token = self.current_token.type
            op_map = {TokenType.PLUS: '+', TokenType.MINUS: '-', TokenType.MULT: '*', TokenType.DIV: '/'}
            op = op_map[op_token]
            self.eat(op_token)
            right = self.current_token.value
            if self.current_token.type in (TokenType.ID, TokenType.NUMBER, TokenType.STRING):
                self.eat(self.current_token.type)
                left = BinaryOp(left, op, right)
            else:
                self.fail(f"Expected right operand for {op} operation")
        
        return left

    def parse_simple_expression(self):
        # Парсим простое выражение (без цепочки операторов)
        val = self.current_token.value
        if self.current_token.type in (TokenType.ID, TokenType.NUMBER, TokenType.STRING):
            self.eat(self.current_token.type)
        else:
            self.fail("Expected value (ID, Number, String)")
        return val

    def parse_condition(self):
        # (Оставляем как было, или можно тоже использовать parse_expression для гибкости)
        left = self.current_token.value
        if self.current_token.type in (TokenType.ID, TokenType.NUMBER): self.eat(self.current_token.type)
        else: self.fail("Invalid condition left operand")
        
        op_map = {TokenType.LT:'<', TokenType.LTE:'<=', TokenType.GT:'>', TokenType.GTE:'>='}
        if self.current_token.type in op_map:
            op = op_map[self.current_token.type]
            self.eat(self.current_token.type)
        else: self.fail("Expected comparison operator")
        
        right = self.current_token.value
        if self.current_token.type in (TokenType.ID, TokenType.NUMBER): self.eat(self.current_token.type)
        else: self.fail("Invalid condition right operand")
        
        return BinaryOp(left, op, right)

    def parse_statement(self):
        # 1. Объявление переменной (int x = ...)
        if self.current_token.type == TokenType.TYPE:
            t = self.current_token.value; self.eat(TokenType.TYPE)
            n = self.current_token.value; self.eat(TokenType.ID)
            self.eat(TokenType.ASSIGN)
            # Используем parse_expression чтобы поддерживать int sum = 0;
            val = self.parse_expression()
            self.eat(TokenType.SEMI)
            return VarDecl(t, n, val)
        
        # 2. Вывод (System.out.println)
        elif self.current_token.type == TokenType.PRINT:
            self.eat(TokenType.PRINT); self.eat(TokenType.LPAREN)
            # Теперь используем parse_expression, чтобы работало "Text " + val
            expr = self.parse_expression() 
            self.eat(TokenType.RPAREN); self.eat(TokenType.SEMI)
            return PrintStatement(expr)
        
        # 3. Return statement
        elif self.current_token.type == TokenType.RETURN:
            self.eat(TokenType.RETURN)
            expr = self.parse_expression()
            self.eat(TokenType.SEMI)
            return ReturnStatement(expr)
        
        # 4. For Loop
        elif self.current_token.type == TokenType.FOR:
            self.eat(TokenType.FOR); self.eat(TokenType.LPAREN)
            init = self.parse_statement()
            cond = self.parse_condition(); self.eat(TokenType.SEMI)
            u = self.current_token.value; self.eat(TokenType.ID); self.eat(TokenType.INC)
            self.eat(TokenType.RPAREN)
            return ForLoop(init, cond, UnaryOp(u, "++"), self.parse_block())
        
        # 5. If / Else
        elif self.current_token.type == TokenType.IF:
            self.eat(TokenType.IF); self.eat(TokenType.LPAREN)
            cond = self.parse_condition(); self.eat(TokenType.RPAREN)
            tb = self.parse_block(); fb = None
            if self.current_token.type == TokenType.ELSE:
                self.eat(TokenType.ELSE)
                fb = [self.parse_statement()] if self.current_token.type == TokenType.IF else self.parse_block()
            return IfStatement(cond, tb, fb)
        
        # 6. While Loop
        elif self.current_token.type == TokenType.WHILE:
            self.eat(TokenType.WHILE); self.eat(TokenType.LPAREN)
            cond = self.parse_condition(); self.eat(TokenType.RPAREN)
            return WhileLoop(cond, self.parse_block())
        
        # 7. Do-While
        elif self.current_token.type == TokenType.DO:
            self.eat(TokenType.DO); body = self.parse_block()
            self.eat(TokenType.WHILE); self.eat(TokenType.LPAREN)
            cond = self.parse_condition(); self.eat(TokenType.RPAREN); self.eat(TokenType.SEMI)
            return DoWhileLoop(body, cond)
        
        # 8. ДЕЙСТВИЯ С ПЕРЕМЕННОЙ (Assign, Increment, или вызов функции)
        elif self.current_token.type == TokenType.ID:
            name = self.current_token.value
            self.eat(TokenType.ID)
            
            # ВАРИАНТ В: Вызов функции (foo(5);)
            if self.current_token.type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                args = []
                # Парсим аргументы функции
                if self.current_token.type != TokenType.RPAREN:
                    args.append(self.parse_simple_expression())
                    while self.current_token.type == TokenType.COMMA:  # Разделитель - запятая
                        self.eat(TokenType.COMMA)
                        args.append(self.parse_simple_expression())
                self.eat(TokenType.RPAREN)
                self.eat(TokenType.SEMI)
                return FunctionCall(name, args)
            
            # ВАРИАНТ А: Присваивание (sum = sum + i;)
            elif self.current_token.type == TokenType.ASSIGN:
                self.eat(TokenType.ASSIGN)
                expr = self.parse_expression() # Парсим правую часть
                self.eat(TokenType.SEMI)
                return Assignment(name, expr)
            
            # ВАРИАНТ Б: Инкремент (i++;)
            elif self.current_token.type == TokenType.INC:
                self.eat(TokenType.INC)
                self.eat(TokenType.SEMI)
                return UnaryOp(name, "++")
            
            else:
                self.fail("Expected '(', '=' or '++' after variable name")
        
        else: self.fail(f"Unknown statement: {self.current_token}")

    def parse_block(self):
        self.eat(TokenType.LBRACE); stmts = []
        while self.current_token.type not in (TokenType.RBRACE, TokenType.EOF):
            stmts.append(self.parse_statement())
        self.eat(TokenType.RBRACE)
        return stmts

    # ... (parse_method, parse_class, parse остаются без изменений)
    def parse_method(self):
        self.eat(TokenType.PUBLIC); self.eat(TokenType.STATIC)
        rt = "void"
        if self.current_token.type == TokenType.VOID: self.eat(TokenType.VOID)
        else: rt = self.current_token.value; self.eat(TokenType.TYPE)
        
        name = self.current_token.value; self.eat(TokenType.ID); self.eat(TokenType.LPAREN)
        args = []
        # Парсим параметры (могут быть несколько, разделены запятыми)
        while self.current_token.type == TokenType.TYPE: 
            param_type = self.current_token.value
            self.eat(TokenType.TYPE)
            # Проверяем, это массив (String[]) или обычный параметр (int a)
            is_array = False
            if self.current_token.type == TokenType.LBRACKET:
                self.eat(TokenType.LBRACKET); self.eat(TokenType.RBRACKET)
                is_array = True
            param_name = self.current_token.value
            self.eat(TokenType.ID)
            args.append(MethodParam(param_type, param_name, is_array))
            # Проверяем, есть ли ещё параметры
            if self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
        self.eat(TokenType.RPAREN)
        return MethodDecl(name, rt, args, self.parse_block())

    def parse_class(self):
        self.eat(TokenType.PUBLIC); self.eat(TokenType.CLASS)
        name = self.current_token.value; self.eat(TokenType.ID)
        self.eat(TokenType.LBRACE); methods = []
        while self.current_token.type != TokenType.RBRACE:
            methods.append(self.parse_method())
        self.eat(TokenType.RBRACE)
        return ClassDecl(name, methods)

    def parse(self): 
        classes = []
        while self.current_token.type != TokenType.EOF:
            classes.append(self.parse_class())
        return Program(classes)

# Helper для форматирования тоже нужно обновить
def format_ast(node, level=0):
    indent = "  " * level
    result = f"{indent}{node.__class__.__name__}"
    
    # ... (существующие проверки)
    if isinstance(node, Program):
        for c in node.classes: result += "\n" + format_ast(c, level+1)
    elif isinstance(node, ClassDecl):
        result += f": {node.name}"
        for m in node.methods: result += "\n" + format_ast(m, level+1)
    elif isinstance(node, MethodDecl):
        result += f": {node.name}"
        if node.args:
            result += f" (args: {', '.join(arg.param_type + ' ' + arg.name for arg in node.args)})"
        for s in node.body: result += "\n" + format_ast(s, level+1)
    elif isinstance(node, VarDecl):
        val_str = format_ast(node.value) if isinstance(node.value, ASTNode) else str(node.value)
        result += f" ({node.var_type} {node.name} = {val_str})"
    elif isinstance(node, Assignment): # <-- ДОБАВЛЕНО
        val_str = format_ast(node.value) if isinstance(node.value, ASTNode) else str(node.value)
        result += f" ({node.name} = {val_str})"
    elif isinstance(node, FunctionCall):
        args_str = ", ".join(format_ast(arg) if isinstance(arg, ASTNode) else str(arg) for arg in node.args)
        result += f" ({node.name}({args_str}))"
    elif isinstance(node, ReturnStatement):
        val_str = format_ast(node.expression) if isinstance(node.expression, ASTNode) else str(node.expression)
        result += f" (return {val_str})"
    elif isinstance(node, PrintStatement):
        val_str = format_ast(node.expression) if isinstance(node.expression, ASTNode) else str(node.expression)
        result += f" ({val_str})"
    elif isinstance(node, BinaryOp):
        result += f" ({node.left} {node.op} {node.right})"
    # ... (остальные)
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
    elif isinstance(node, UnaryOp):
        result += f" ({node.expr}{node.op})"
        
    return result