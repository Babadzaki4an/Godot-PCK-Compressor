

import re


def replace_ignoring_whitespace(content: str, find: str, change: str) -> str:
    parts = re.split(r'(\s+)', find)
    pattern_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part: 
                pattern_parts.append(re.escape(part))
    pattern = r'\s+'.join(pattern_parts)
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        start, end = match.span()
        content = content[:start] + change + content[end:]
    return content

def insert_after_ignoring_whitespace(content: str, find: str, insert_text: str) -> str:
    parts = re.split(r'(\s+)', find)
    pattern_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part:
                pattern_parts.append(re.escape(part))
    pattern = r'\s+'.join(pattern_parts)
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        start, end = match.span()
        content = content[:end] + insert_text + content[end:]
    return content