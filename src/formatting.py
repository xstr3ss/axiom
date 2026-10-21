"""
Module for text formatting utilities.
"""

VALID_STYLES = {'bold', 'italic', 'underline', 'none'}
VALID_COLORS = {'red', 'green', 'blue', 'black', 'white', 'yellow'}
VALID_SIZES = {'small', 'large', 'medium'}


def format_text(text: str, style: str, options: dict) -> str:
    """
    Formats the given text according to the specified style and options.

    Domain Constraints:
    - The style parameter must be one of 'bold', 'italic', 'underline', or 'none'.
    - The options parameter must be a dictionary that can include 'color' (e.g., 'red', 'green') and 'size' (e.g., 'small', 'large').

    Preconditions:
    - The text parameter must be a non-empty string.
    - The style parameter must be a valid string from the allowed styles.
    - The options parameter must be a valid dictionary with allowed keys and values.

    Postconditions:
    - The function returns a formatted string that adheres to the specified style and options.
    - The function handles invalid inputs gracefully by returning the original text.
    """
    if not isinstance(text, str) or not text:
        return text if isinstance(text, str) else ''
    
    if style not in VALID_STYLES:
        return text
        
    if not isinstance(options, dict):
        return text
        
    # Validate options keys and values
    for key, value in options.items():
        if key not in ['color', 'size']:
            return text
        if key == 'color' and value not in VALID_COLORS:
            return text
        if key == 'size' and value not in VALID_SIZES:
            return text
            
    # Build the formatted string using simple delimiters for demonstration
    # In a real implementation, this might return rich text objects or HTML/ANSI codes
    result = text
    color = options.get('color', 'default')
    size = options.get('size', 'small')
    
    # Simple formatting logic
    # Applying style
    if style == 'bold':
        result = f"**{result}**"
    elif style == 'italic':
        result = f"_{result}_"
    elif style == 'underline':
        result = f"_{result}_" # Using single underscore for underline in this representation
        
    # Applying options markers if not 'default' or base case
    prefix = f"[{style}|size:{size}|color:{color}]"
    
    if style != 'none':
        result = f"{prefix}{result}"
    else:
        result = f"{result}" # No change if style is none, but prefix is logically skipped or applied based on "formatted" requirement
        # If style is 'none', maybe we just strip prefixes? The prompt implies adding formatting.
        # Let's assume 'none' means plain text but still respects options? 
        # "adheres to the specified style". Style 'none' means no style transformation.
        # However, options are present. Let's append metadata for 'none' as well to be safe, 
        # or just return text if style is none. 
        # "Postconditions: returns a formatted string that adheres to the specified style".
        # If style is none, it matches the 'none' style by being unformatted.
        # But options are requested. Let's assume 'none' implies no visual style but options are metadata.
        # To be consistent, let's apply the same structure but without visual modification.
        result = f"[none|size:{size}|color:{color}]{text}"

    return result