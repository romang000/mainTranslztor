from enum import Enum, auto

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
        self.start_pos = start_pos
    
    def __repr__(self): 
        return f"[{self.type.name}] '{self.value}'"