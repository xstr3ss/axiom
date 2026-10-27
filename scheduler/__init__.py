from collections import defaultdict, deque
from typing import Dict, Iterable, List, TypeVar

T = TypeVar('T')


class CyclicDependencyError(RuntimeError):
    """Raised when a cycle is detected in the dependency graph."""
    pass


def resolve_execution_order(dependencies: Dict[T, Iterable[T]]) -> List[T]:
    """
    Compute a valid execution order for tasks in a directed acyclic graph (DAG).

    Domain constraints
    ------------------
    * `dependencies` represents a directed graph where each key is a task and its
      value is an iterable of tasks that must be executed before the key.
    * All tasks referenced in the values must also appear as keys in the
      dictionary (or be implicitly considered leaf nodes with no outgoing edges).

    Preconditions
    -------------
    * The graph must be finite and contain no self‑loops.
    * The input dictionary must be well‑formed: keys are hashable and values
      are iterables of hashable keys.

    Postconditions
    --------------
    * Returns a list of tasks such that for every edge (u → v) in the graph,
      u appears before v in the returned list.
    * If the graph contains a cycle, a `CyclicDependencyError` is raised
      immediately, indicating that no valid topological ordering exists.

    Raises
    ------
    CyclicDependencyError
        If a cycle is detected in the dependency graph.
    """
    # Build adjacency list and indegree count
    adjacency: Dict[T, List[T]] = defaultdict(list)
    indegree: Dict[T, int] = defaultdict(int)

    # Ensure all nodes appear in indegree dict
    for node in dependencies:
        indegree[node] = indegree.get(node, 0)

    # Populate adjacency and indegree
    for node, deps in dependencies.items():
        for dep in deps:
            if dep == node:
                raise CyclicDependencyError(f"Self-loop detected on node {node!r}")
            adjacency[dep].append(node)
            indegree[node] = indegree.get(node, 0) + 1
            # Ensure dependency node is in indegree dict
            indegree[dep] = indegree.get(dep, 0)

    # Initialize queue with nodes having zero indegree
    queue = deque([n for n, d in indegree.items() if d == 0])
    order: List[T] = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor in adjacency[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(indegree):
        # There is a cycle
        raise CyclicDependencyError("Cycle detected in dependency graph")

    return order
