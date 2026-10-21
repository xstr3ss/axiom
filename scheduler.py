from typing import Dict, List, Set


class CyclicDependencyError(Exception):
    """Raised when a cycle is detected in the dependency graph."""
    pass


def resolve_execution_order(
    dependencies: Dict[str, Set[str]]
) -> List[str]:
    """
    Resolve a valid execution order for a Directed Acyclic Graph (DAG) of tasks.

    Domain Constraints:
        - The input represents a DAG where nodes are task identifiers (strings).
        - Edges represent dependencies: if task A depends on task B, B must execute before A.
        - The graph may be disconnected.

    Preconditions:
        - `dependencies` is a dictionary mapping each task ID to a set of task IDs it depends on.
        - All task IDs referenced in the dependency sets must also be keys in the dictionary
          (i.e., the graph is closed under dependency references).
        - Task IDs are unique strings.

    Postconditions:
        - Returns a list of task IDs representing a valid topological ordering.
        - For every task T in the returned list, all tasks in dependencies[T] appear earlier in the list.
        - If a cycle is detected in the dependency graph, raises CyclicDependencyError.
        - The returned list contains exactly the same set of task IDs as the keys of `dependencies`.

    Args:
        dependencies: A dictionary where each key is a task ID and the value is a set of task IDs
                      that the key task depends on.

    Returns:
        A list of task IDs in a valid execution order.

    Raises:
        CyclicDependencyError: If the dependency graph contains a cycle.
    """
    # State: 0 = unvisited, 1 = visiting (in current recursion stack), 2 = visited
    state = {task: 0 for task in dependencies}
    result = []

    def visit(task: str) -> None:
        if state[task] == 1:
            raise CyclicDependencyError(f"Cycle detected involving task: {task}")
        if state[task] == 2:
            return
        
        state[task] = 1
        for dep in dependencies[task]:
            # Ensure dependency exists in state (precondition says it should, but guard just in case)
            if dep not in state:
                # If a dependency is missing from the keys, it's an invalid graph structure 
                # based on preconditions, but we can treat it as a node to visit if we were building 
                # a full graph. However, the contract says keys are the universe. 
                # If dep is not in dependencies, it violates preconditions. 
                # We assume preconditions hold. If not, we might want to raise ValueError, 
                # but the contract only specifies CyclicDependencyError. 
                # We will assume valid input per preconditions.
                pass
            visit(dep)
        state[task] = 2
        result.append(task)

    for task in dependencies:
        if state[task] == 0:
            visit(task)

    return result
