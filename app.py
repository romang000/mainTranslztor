import streamlit as st
import traceback

# Импорт компонента редактора кода
from streamlit_ace import st_ace

# Импорт логики компилятора
from compiler.lexer import Lexer
from compiler.parser import Parser, format_ast
from compiler.generator import CSharpGenerator
from compiler.errors import TranslationError

st.set_page_config(layout="wide", page_title="Compiler Demo", page_icon="☕")

st.title("Java to C# Transpiler 🚀")
st.markdown("Архитектура: **Lexer** (Tokens) → **Parser** (AST) → **Generator** (C#)")

# Разметка колонок
col_input, col_process, col_output = st.columns([1.2, 0.8, 1])

DEFAULT_CODE = """public class WhileLoopExample {
    public static void main(String[] args) {
        int i = 1;
        int sum = 0;

        while (i <= 5) {
            sum = sum + i;
            i = i + 1;
        }

        System.out.println("Сумма: " + sum);
    }
}"""

# --- Колонка 1: Ввод (Редактор кода) ---
with col_input:
    st.header("1. Input (Java)")
    
    # Замена st.text_area на st_ace для номеров строк и подсветки
    java_code = st_ace(
        value=DEFAULT_CODE,
        language="java",        # Подсветка синтаксиса Java
        theme="monokai",        # Темная тема (как в Sublime Text)
        show_gutter=True,       # ПОКАЗАТЬ НОМЕРА СТРОК
        font_size=14,
        height=500,
        key="ace_editor"
    )
    
    translate_btn = st.button("▶ Compile & Translate", type="primary", use_container_width=True)

# Переменные состояния
tokens_display = []
ast_display = ""
result_code = ""
error_msg = None

# Логика компиляции
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

# --- Колонка 2: Внутренности ---
with col_process:
    st.header("2. Internals")
    tab1, tab2 = st.tabs(["🧩 Tokens", "🌳 AST"])
    
    with tab1:
        if tokens_display:
            st.code("\n".join(tokens_display), language="text")
        else:
            st.info("Waiting for compilation...")
            
    with tab2:
        if ast_display:
            st.code(ast_display, language="text")
        else:
            st.info("Waiting for compilation...")

# --- Колонка 3: Вывод ---
with col_output:
    st.header("3. Output (C#)")
    
    if error_msg:
        st.error("Compilation Failed")
        st.text(error_msg) # Выводим ошибку текстом, чтобы сохранить форматирование стрелочки
    elif result_code:
        st.success("Compilation Successful!")
        # Используем st_ace и для вывода, чтобы было красиво (readonly)
        st_ace(
            value=result_code,
            language="csharp",
            theme="monokai",
            readonly=True,
            show_gutter=True,
            height=450,
            font_size=14,
            key="output_editor"
        )
    else:
        st.info("Ready to translate.")