#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/user/Desktop/fefu/dilda/mainTranslztor')

from compiler.lexer import Lexer
from compiler.parser import Parser, format_ast
from compiler.generator import CSharpGenerator

# Исходный код из запроса
code = """public class WhileLoopExample {
    public static void main(String[] args) {
        
        int a = foo(5);
        
        System.out.println(a);
    }
    
    public static int foo(int a) {
        
        return a + 1;
    }
}"""

print('=== Input Java Code ===')
print(code)
print('\n=== Compilation ===')

try:
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens, code)
    ast = parser.parse()
    print('✓ SUCCESS: Compilation successful!')
    print('\n=== Generated C# Code ===')
    gen = CSharpGenerator()
    csharp_code = gen.generate(ast)
    print(csharp_code)
except Exception as e:
    print(f'✗ FAILED: {e}')
    import traceback
    traceback.print_exc()
