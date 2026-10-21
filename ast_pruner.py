import ast
import sys

def prune_file(filepath, focus_node=None):
    try:
        with open(filepath, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        return f"Error: File {filepath} not found."

    # Parse the raw code into an Abstract Syntax Tree
    tree = ast.parse(source)

    class SkeletonPruner(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # If this is the specific function we are debugging, keep all its code!
            if focus_node and node.name == focus_node:
                return node
            
            # Otherwise, strip it down to a skeleton
            new_body = []
            
            # 1. Keep the docstring if it exists so the AI knows what the function does
            if ast.get_docstring(node):
                new_body.append(node.body[0])
                
            # 2. Replace the actual logic with '...'
            new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))
            
            node.body = new_body
            return node

        # Do the exact same thing for asynchronous functions
        def visit_AsyncFunctionDef(self, node):
            return self.visit_FunctionDef(node)

    # Apply the pruning transformations
    pruner = SkeletonPruner()
    modified_tree = pruner.visit(tree)
    ast.fix_missing_locations(modified_tree)
    
    # Convert the modified AST back into raw Python code text
    # (ast.unparse is natively available in Python 3.9+)
    return ast.unparse(modified_tree)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ast_pruner.py <filepath.py> [focus_function_name]")
        sys.exit(1)
        
    file_path = sys.argv[1]
    focus = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(prune_file(file_path, focus))
