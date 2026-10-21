"""
Text formatting utility for standardizing string presentation.
"""

from __future__ import annotations


def format_text(
    text: str,
    line_length: int | None = None,
    uppercase: bool = False,
) -> str:
    """
    Format a text string according to domain constraints.

    This utility normalizes whitespace, optionally wraps lines to a maximum
    width, and optionally uppercases the result.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    
    if line_length is not None:
        if not isinstance(line_length, int) or isinstance(line_length, bool):
            raise TypeError("line_length must be an integer or None")
        if line_length < 1:
            raise ValueError("line_length must be >= 1")

    # 1. Strip leading/trailing whitespace
    text = text.strip()
    
    # 2. Collapse internal whitespace
    # Split by whitespace and rejoin with single space
    text = ' '.join(text.split())
    
    # 3. Wrap if requested
    if line_length is not None:
        # Standard word_wrap logic
        words = text.split(' ')
        current_line = ""
        lines = []
        
        for word in words:
            if not current_line:
                current_line = word
            else:
                # Check if adding word exceeds limit
                # Plus 1 for the space
                if len(current_line) + 1 + len(word) <= line_length:
                    current_line += ' ' + word
                else:
                    lines.append(current_line)
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        text = '\n'.join(lines)

    # 4. Uppercase if requested
    if uppercase:
        text = text.upper()

    return text