class TranslationError(Exception):
    pass

def get_error_visual(text: str, pos: int, message: str) -> str:
    """Генерирует ошибку с указателем на строку кода."""
    line_no = text.count('\n', 0, pos) + 1
    line_start = text.rfind('\n', 0, pos) + 1
    line_end = text.find('\n', pos)
    if line_end == -1: 
        line_end = len(text)
    
    line_content = text[line_start:line_end]
    col = pos - line_start
    pointer = " " * col + "^"
    
    return f"Error on line {line_no}:\n{line_content}\n{pointer}\n--> {message}"