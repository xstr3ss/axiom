import ast
import json


def _node_to_dict(node):
    """
    Recursively convert an AST node to a custom dictionary representation.
    """
    if isinstance(node, ast.Assign):
        # Handle simple assignment: x = value
        if len(node.targets) != 1:
            raise ValueError("Only single target assignments are supported.")
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise ValueError("Assignment target must be a simple name.")
        # Determine if the value is a simple number or a binary operation
        if isinstance(node.value, (ast.Num, ast.Constant)) and isinstance(
            getattr(node.value, "n", getattr(node.value, "value", None)), (int, float)
        ):
            # Numeric literal
            value = getattr(node.value, "n", getattr(node.value, "value", None))
            return {
                "type": "Assign",
                "target": target.id,
                "value": value,
            }
        elif isinstance(node.value, ast.BinOp):
            return {
                "type": "Assign",
                "target": target.id,
                "operation": _node_to_dict(node.value),
            }
        else:
            raise ValueError(
                f"Unsupported assignment value type: {type(node.value).__name__}"
            )
    elif isinstance(node, (ast.Num, ast.Constant)):
        # Handle numeric literals
        value = getattr(node, "n", getattr(node, "value", None))
        if not isinstance(value, (int, float)):
            raise ValueError(f"Unsupported numeric literal type: {type(value).__name__}")
        return {
            "type": "Num",
            "n": value,
        }
    elif isinstance(node, ast.BinOp):
        # Handle binary operations
        if isinstance(node.op, ast.Add):
            op_type = "Add"
        elif isinstance(node.op, ast.Sub):
            op_type = "Sub"
        else:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

        return {
            "type": "BinOp",
            "op": op_type,
            "left": _node_to_dict(node.left),
            "right": _node_to_dict(node.right),
        }
    else:
        raise ValueError(f"Unsupported AST node type: {type(node).__name__}")


def python_to_json_ast(code: str) -> str:
    """
    Convert a limited Python source snippet into a JSON string representing a custom AST.

    Domain constraints:
    - The input ``code`` must be a syntactically valid Python fragment.
    - Only simple assignment statements (e.g., ``x = 42``) and binary operations
      using the ``Add`` or ``Sub`` operators are supported.  Other constructs are
      ignored or may raise errors in later processing.

    Preconditions:
    - ``code`` is a non‑empty string.
    - The string contains at most one top‑level statement.

    Postconditions:
    - Returns a JSON‑encoded ``str`` that follows the format expected by the test
      suite (e.g., ``{"type": "Assign", "target": "x", "value": 42}``).
    - If the source cannot be parsed, a ``ValueError`` is raised instead of a
      ``SyntaxError``.

    Raises:
        ValueError: If ``code`` contains invalid Python syntax or unsupported constructs.
    """
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Input code must be a non-empty string.")

    try:
        parsed = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise ValueError(f"Invalid Python syntax: {exc}") from exc

    # Ensure exactly one top‑level statement as per the contract.
    if len(parsed.body) != 1:
        raise ValueError("Only a single top-level statement is supported.")

    stmt = parsed.body[0]
    # Convert the AST node to our custom dictionary representation.
    result_dict = _node_to_dict(stmt)

    # The test suite expects the JSON to contain a top‑level ``body`` list.
    wrapped = {"body": [result_dict]}

    return json.dumps(wrapped, separators=(",", ":"))
