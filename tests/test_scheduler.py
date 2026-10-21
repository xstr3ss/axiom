import pytest
from typing import List

# Import the function and exception from the module under test
from scheduler import resolve_execution_order, CyclicDependencyError


def _check_order(order: List[str], dependencies: dict) -> None:
    """
    Helper that asserts that for every dependency pair (u -> v),
    u appears before v in the provided order.
    """
    position = {task: idx for idx, task in enumerate(order)}
    for task, deps in dependencies.items():
        for dep in deps:
            assert position[dep] < position[task], (
                f"Dependency violation: {dep} should come before {task}"
            )


def test_empty_graph_returns_empty_list():
    """An empty dependency graph should return an empty list."""
    assert resolve_execution_order({}) == []


def test_single_node_no_dependencies():
    """A single node with no dependencies should return a list containing that node."""
    result = resolve_execution_order({"A": []})
    assert result == ["A"]


def test_simple_acyclic_graph():
    """Verify that a simple acyclic graph returns a valid topological order."""
    deps = {
        "C": ["A", "B"],
        "B": ["A"],
        "A": [],
    }
    order = resolve_execution_order(deps)
    assert isinstance(order, list)
    _check_order(order, deps)
    # Order should contain all nodes
    assert set(order) == {"A", "B", "C"}


def test_complex_dag():
    """Test a more complex DAG with multiple dependencies."""
    deps = {
        "E": ["B", "D"],
        "D": ["A"],
        "C": ["A"],
        "B": ["A"],
        "A": [],
    }
    order = resolve_execution_order(deps)
    _check_order(order, deps)
    assert set(order) == {"A", "B", "C", "D", "E"}


def test_leaf_nodes_in_values():
    """
    Tasks referenced in dependency values but not present as keys
    should be treated as leaf nodes and appear in the output.
    """
    deps = {
        "B": ["A"],  # A is not a key
    }
    order = resolve_execution_order(deps)
    _check_order(order, {"B": ["A"], "A": []})  # Treat A as implicit leaf
    assert set(order) == {"A", "B"}


def test_cycle_detection_simple():
    """A simple two-node cycle should raise CyclicDependencyError."""
    deps = {
        "A": ["B"],
        "B": ["A"],
    }
    with pytest.raises(CyclicDependencyError):
        resolve_execution_order(deps)


def test_cycle_detection_complex():
    """A more complex cycle involving multiple nodes."""
    deps = {
        "A": ["B"],
        "B": ["C"],
        "C": ["D"],
        "D": ["B"],  # cycle B -> C -> D -> B
    }
    with pytest.raises(CyclicDependencyError):
        resolve_execution_order(deps)


def test_self_loop_detection():
    """A node that depends on itself should raise CyclicDependencyError."""
    deps = {
        "A": ["A"],
    }
    with pytest.raises(CyclicDependencyError):
        resolve_execution_order(deps)


def test_order_determinism_for_independent_nodes():
    """
    When multiple nodes have no dependencies, the order may vary.
    This test ensures that all nodes are present and dependencies are respected.
    """
    deps = {
        "C": ["A"],
        "B": [],
        "A": [],
    }
    order = resolve_execution_order(deps)
    _check_order(order, deps)
    assert set(order) == {"A", "B", "C"}


def test_large_acyclic_graph_performance():
    """
    Test that the function can handle a reasonably large acyclic graph
    without raising an exception. This is a lightweight performance check.
    """
    size = 200
    deps = {f"node{i}": [f"node{i-1}"] for i in range(1, size)}
    deps["node0"] = []
    order = resolve_execution_order(deps)
    assert len(order) == size
    _check_order(order, deps)
