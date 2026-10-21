def extract_json_payload(line: str) -> str:
    """Extracts the JSON payload from a line containing the 'PAYLOAD:' prefix.

    Domain constraints:
        - `line` must be a string containing the substring 'PAYLOAD:'.
        - The JSON payload follows the prefix, possibly preceded by any number of whitespace characters.

    Preconditions:
        - `line` is a non-empty string.
        - `line` contains 'PAYLOAD:'.

    Postconditions:
        - Returns a string containing the JSON payload with no leading or trailing whitespace.
        - If no payload is found after the prefix, returns an empty string.

    Raises:
        - ValueError if 'PAYLOAD:' is not present in `line`.
    """
    if not line:
        raise ValueError("Empty line")
    idx = line.find('PAYLOAD:')
    if idx == -1:
        raise ValueError("Missing PAYLOAD:")
    start = idx + len('PAYLOAD:')
    payload = line[start:].lstrip()
    return payload.rstrip()
