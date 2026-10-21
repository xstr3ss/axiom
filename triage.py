import ast
import logging
import os

log = logging.getLogger("fable.triage")

class TriageAgent:
    @staticmethod
    def extract_function(code: str, func_name: str) -> str:
        """Slices a single function out of a larger file."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                    lines = code.splitlines()
                    return "\n".join(lines[node.lineno - 1 : node.end_lineno])
        except SyntaxError:
            pass
        return ""

    @staticmethod
    def condense_error(raw_pytest_output: str, llm_client=None) -> str:
        """Uses the Local SLM (3B) to condense logs."""
        marker = "=================================== FAILURES ==================================="
        failures = raw_pytest_output.split(marker)[1] if marker in raw_pytest_output else raw_pytest_output[-2000:]
        
        if llm_client:
            prompt = (
                "Extract ONLY the failing file name, line number, and exact error message "
                f"from this test output in under 3 lines. Be extremely concise:\n\n{failures[:2000]}"
            )
            condensed = llm_client.get_local_response(prompt, agent_role="Triage")
            if condensed.strip():
                return condensed.strip()
                
        return failures[:1500].strip()

    @staticmethod
    def get_local_imports(code: str) -> dict:
        """AST Pass 1: Maps imported function names to their source files."""
        imports = {}
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                    for alias in node.names:
                        # Assuming local files end in .py and match module name
                        imports[alias.name] = f"{module}.py"
        except SyntaxError:
            pass
        return imports

    @staticmethod
    def get_function_calls(func_code: str) -> set:
        """AST Pass 2: Finds all function executions inside a block of code."""
        calls = set()
        try:
            tree = ast.parse(func_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
        except SyntaxError:
            pass
        return calls

    @staticmethod
    def build_dependency_graph(filename: str, func_name: str, files_context: dict) -> str:
        """
        The Multi-File Router: Traces a failing function into other files.
        Returns a unified string containing the target function AND its cross-file dependencies.
        """
        if filename not in files_context:
            return ""
            
        code = files_context[filename]
        target_func_code = TriageAgent.extract_function(code, func_name)
        if not target_func_code:
            return ""
            
        context_str = f"🚨 TARGET FILE: {filename} | FAILING FUNCTION: {func_name}\n```python\n{target_func_code}\n```\n\n"
        
        # 1. Find what other functions this target is calling
        called_funcs = TriageAgent.get_function_calls(target_func_code)
        if not called_funcs:
            return context_str
            
        # 2. Find where those functions are imported from
        imports = TriageAgent.get_local_imports(code)
        
        # 3. Extract the dependent code from the other files
        found_deps = False
        dep_str = "🔍 CROSS-FILE DEPENDENCIES DETECTED:\n"
        for called_func in called_funcs:
            if called_func in imports:
                dep_file = imports[called_func]
                if dep_file in files_context:
                    dep_code = TriageAgent.extract_function(files_context[dep_file], called_func)
                    if dep_code:
                        dep_str += f"FILE: {dep_file} | IMPORTED FUNCTION: {called_func}\n```python\n{dep_code}\n```\n\n"
                        found_deps = True
        
        if found_deps:
            context_str += dep_str
            
        return context_str
