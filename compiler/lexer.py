from .tokens import TokenType, Token
from .errors import TranslationError, get_error_visual

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
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def parse_identifier(self):
        start = self.pos
        res = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            res += self.current_char
            self.advance()
        
        keywords = {
            'public': TokenType.PUBLIC, 'class': TokenType.CLASS, 'static': TokenType.STATIC, 
            'void': TokenType.VOID, 'int': TokenType.TYPE, 'boolean': TokenType.TYPE, 
            'String': TokenType.TYPE, 'for': TokenType.FOR, 'if': TokenType.IF, 
            'else': TokenType.ELSE, 'while': TokenType.WHILE, 'do': TokenType.DO
        }
        
        # Хак для System.out.println
        if res == 'System' and self.text[start:].startswith('System.out.println'):
            self.pos = start + 18
            self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
            return Token(TokenType.PRINT, 'System.out.println', start)
        
        return Token(keywords.get(res, TokenType.ID), res, start)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace(): self.skip_whitespace(); continue
            
            start = self.pos

            if self.current_char.isalpha(): return self.parse_identifier()
            
            if self.current_char.isdigit():
                num = ''
                while self.current_char and self.current_char.isdigit():
                    num += self.current_char; self.advance()
                return Token(TokenType.NUMBER, int(num), start)

            if self.current_char == '"':
                res = ''; self.advance()
                while self.current_char and self.current_char != '"':
                    res += self.current_char; self.advance()
                self.advance()
                return Token(TokenType.STRING, res, start)
            
            singles = {
                '=': TokenType.ASSIGN, ';': TokenType.SEMI, '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN, '[': TokenType.LBRACKET, ']': TokenType.RBRACKET
            }
            if self.current_char in singles:
                tk = Token(singles[self.current_char], self.current_char, start)
                self.advance()
                return tk
            
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
        tokens = []
        while True:
            tk = self.get_next_token()
            tokens.append(tk)
            if tk.type == TokenType.EOF: break
        return tokens