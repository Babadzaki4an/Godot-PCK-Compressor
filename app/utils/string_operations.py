

import re


def _build_pattern(find: str) -> str:
    """Строит regex-паттерн из строки find, игнорируя пробелы/переносы между словами."""
    parts = re.split(r'(\s+)', find)
    pattern_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part:
                pattern_parts.append(re.escape(part))
    return r'\s+'.join(pattern_parts)


def _find_span(content: str, find: str) -> tuple[int, int] | None:
    """Возвращает (start, end) первого вхождения find в content, игнорируя пробелы,
    или None, если вхождение не найдено."""
    pattern = _build_pattern(find)
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.span()
    return None


def replace_ignoring_whitespace(content: str, find: str, change: str) -> str:
    span = _find_span(content, find)
    if span:
        start, end = span
        content = content[:start] + change + content[end:]
    return content


def insert_after_ignoring_whitespace(content: str, find: str, insert_text: str) -> str:
    span = _find_span(content, find)
    if span:
        start, end = span
        content = content[:end] + insert_text + content[end:]
    return content


def insert_before_ignoring_whitespace(content: str, find: str, insert_text: str) -> str:
    span = _find_span(content, find)
    if span:
        start, end = span
        content = content[:start] + insert_text + content[start:]
    return content