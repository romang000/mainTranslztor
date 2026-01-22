#!/usr/bin/env python3
from compiler.lexer import Lexer
from compiler.parser import Parser, format_ast
from compiler.generator import CSharpGenerator

# Тест 1: Простой вызов функции
code1 = open('test_function_call.java').read()
print('=== Test 1: Simple Function Call ===')
try:
    lexer = Lexer(code1)
    tokens = lexer.tokenize()
    parser = Parser(tokens, code1)
    ast = parser.parse()
    print('✓ Parsing successful!')
    gen = CSharpGenerator()
    csharp_code = gen.generate(ast)
    print(csharp_code)
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '='*60 + '\n')

# Тест 2: Более сложный случай
code2 = """public class Test {
    public static void main(String[] args) {
        int result = add(5, 3);
        System.out.println(result);
    }
    
    public static int add(int a, int b) {
        return a + b;
    }
}"""

print('=== Test 2: Multiple Parameters ===')
try:
    lexer = Lexer(code2)
    tokens = lexer.tokenize()
    parser = Parser(tokens, code2)
    ast = parser.parse()
    print('✓ Parsing successful!')
    gen = CSharpGenerator()
    csharp_code = gen.generate(ast)
    print(csharp_code)
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
