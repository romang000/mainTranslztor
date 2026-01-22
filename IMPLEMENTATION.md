# Поддержка вызовов функций в трансляторе Java→C#

## Реализованные возможности

### 1. **Вызовы функций в выражениях**
   - Поддержка синтаксиса: `foo(5)`, `add(a, b)`, `multiply(x)`
   - Вызовы функций могут использоваться в присваиваниях: `int a = foo(5);`
   - Вызовы функций как самостоятельные statements: `foo(5);`

### 2. **Объявление методов с параметрами**
   - Поддержка одного параметра: `public static int foo(int a)`
   - Поддержка нескольких параметров: `public static int add(int a, int b)`
   - Поддержка параметров-массивов: `public static void main(String[] args)`

### 3. **Return statement**
   - Возврат из методов: `return a + 1;`
   - Возврат значений выражений: `return a + b;`

### 4. **Бинарные операции**
   - Поддержка операторов: `+`, `-`, `*`, `/`
   - Использование в выражениях: `return a + b;`, `return x * 2;`

## Структура изменений

### Файлы, которые были обновлены:

1. **compiler/tokens.py**
   - Добавлены: `RETURN`, `COMMA`, `MINUS`, `MULT`, `DIV`

2. **compiler/lexer.py**
   - Распознавание ключевого слова `return`
   - Распознавание операторов: `*`, `/`, `-`, `,`

3. **compiler/ast_nodes.py**
   - Новые классы: `FunctionCall`, `ReturnStatement`, `MethodParam`

4. **compiler/parser.py**
   - Метод `parse_expression()` для парсинга выражений с функциями
   - Метод `parse_simple_expression()` для простых выражений
   - Обновлена обработка statements (добавлена поддержка return и вызовов функций)
   - Обновлена обработка параметров методов (несколько параметров через запятую)
   - Обновлён `format_ast()` для визуализации новых узлов

5. **compiler/generator.py**
   - Генерация вызовов функций: `foo(5);`, `add(a, b);`
   - Генерация return statements: `return a + 1;`
   - Поддержка методов с параметрами

## Примеры использования

### Пример 1: Простой вызов функции
```java
public class WhileLoopExample {
    public static void main(String[] args) {
        int a = foo(5);
        System.out.println(a);
    }
    
    public static int foo(int a) {
        return a + 1;
    }
}
```

Генерирует C#:
```csharp
using System;
public class WhileLoopExample
{
    public static void Main(string[] args)
    {
        int a = foo(5);
        Console.WriteLine(a);
    }
    public static int foo(int a)
    {
        return a + 1;
    }
}
```

### Пример 2: Функция с несколькими параметрами
```java
public class Test {
    public static void main(String[] args) {
        int result = add(5, 3);
        System.out.println(result);
    }
    
    public static int add(int a, int b) {
        return a + b;
    }
}
```

## Тестирование

Используйте файлы для тестирования:
- `test_function_call.java` - простой вызов функции
- `test_function_call_advanced.java` - более сложные примеры

Запуск:
```bash
python3 final_test.py
```
