import ast

class ASTSemanticAuditor:
    """
    Zero-Token Semantic Verification Gate.
    Uses Python AST static analysis to catch 'Phantom Success' & LLM reward hacking
    before promoting code from the Shadow Workspace to the real host environment.
    """

    @staticmethod
    def _extract_string_and_num_literals(source_code: str) -> set:
        """Extracts non-trivial literals from a file to detect hardcoded test answers."""
        literals = set()
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant):
                    val = node.value
                    if isinstance(val, str) and len(val) > 3:
                        literals.add(val)
                    elif isinstance(val, (int, float)) and not isinstance(val, bool) and val not in (0, 1, -1):
                        literals.add(val)
        except SyntaxError:
            pass
        return literals

    @classmethod
    def verify_patch_integrity(cls, filename: str, original_code: str, patched_code: str, test_files: dict) -> tuple[bool, str]:
        if not filename.endswith(".py"):
            return True, "Non-Python file bypassed AST semantic check."

        try:
            orig_tree = ast.parse(original_code) if original_code.strip() else None
            patch_tree = ast.parse(patched_code)
        except SyntaxError as e:
            return False, f"Syntax error in patched AST: {e}"

        # 1. Check for Swallowed Exceptions (try ... except: pass)
        for node in ast.walk(patch_tree):
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Expr)):
                    if isinstance(node.body[0], ast.Pass) or (
                        isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)
                    ):
                        return False, "Semantic Violation: Patch silently swallows exceptions with an empty except block."

        # 2. Check for Hollowed-Out Functions (def foo(): pass)
        for node in ast.walk(patch_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    return False, f"Semantic Violation: Function '{node.name}' was hollowed out with 'pass'."

        # 3. Check for Deleted Public Functions/Methods
        if orig_tree:
            orig_funcs = {n.name for n in ast.walk(orig_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            patch_funcs = {n.name for n in ast.walk(patch_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            missing = orig_funcs - patch_funcs
            if missing:
                return False, f"Semantic Violation: Patch deleted existing function(s): {', '.join(missing)}"

        # 4. Check for Test-Literal Reward Hacking (Hardcoding test assertion values in source code)
        orig_literals = cls._extract_string_and_num_literals(original_code)
        patch_literals = cls._extract_string_and_num_literals(patched_code)
        newly_introduced_literals = patch_literals - orig_literals

        test_literals = set()
        for t_code in test_files.values():
            test_literals.update(cls._extract_string_and_num_literals(t_code))

        cheated_literals = newly_introduced_literals.intersection(test_literals)
        if cheated_literals:
            return False, (
                f"Reward-Hacking Detected: Patch hardcoded test assertion literal(s) "
                f"{cheated_literals} directly into {filename}!"
            )

        return True, f"Semantic integrity verified for {filename}."
