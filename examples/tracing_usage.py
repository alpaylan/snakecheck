"""
Tracing and dataflow examples for SnakeCheck property-based testing.

This demonstrates the new generation tracing functionality that enables
dataflow-aware shrinking algorithms.
"""

from snakecheck import choices, integers, traced_composite
from snakecheck.trace import TraceableDrawFn


# Example 1: Simple sequence with dependencies
@traced_composite
def sequence_strategy(draw: TraceableDrawFn):
    """Generate a sequence where later values depend on earlier ones."""
    x = draw(integers(0, 10))
    draw.record_assignment("x", x)

    y = draw(integers(0, x))  # y depends on x
    draw.record_assignment("y", y)

    z = draw(integers(y, x + 5))  # z depends on both x and y
    draw.record_assignment("z", z)

    return {"x": x, "y": y, "z": z}


# Example 2: List generation with size dependencies
@traced_composite
def list_with_dependencies_strategy(draw: TraceableDrawFn):
    """Generate a list where the content depends on the size."""
    size = draw(integers(1, 5))
    draw.record_assignment("size", size)

    # Generate list elements that depend on the size
    elements = []
    for i in range(size):
        # Each element depends on size and position
        max_val = size * 10 + i
        element = draw(integers(0, max_val))
        draw.record_assignment(f"element_{i}", element)
        elements.append(element)

    return {"size": size, "elements": elements}


# Example 3: Tree structure with parent-child dependencies
@traced_composite
def tree_strategy(draw: TraceableDrawFn):
    """Generate a tree structure with dependencies."""
    root_value = draw(integers(-100, 100))
    draw.record_assignment("root_value", root_value)

    # Number of children depends on root value
    child_count = draw(integers(0, min(5, abs(root_value) // 20)))
    draw.record_assignment("child_count", child_count)

    children = []
    for i in range(child_count):
        # Child values depend on parent value
        child_value = draw(integers(root_value - 50, root_value + 50))
        draw.record_assignment(f"child_{i}_value", child_value)

        # Child size depends on child value
        child_size = draw(integers(0, abs(child_value) // 10))
        draw.record_assignment(f"child_{i}_size", child_size)

        children.append({"value": child_value, "size": child_size})

    return {"root_value": root_value, "child_count": child_count, "children": children}


# Example 4: Matrix generation with row/column dependencies
@traced_composite
def matrix_strategy(draw: TraceableDrawFn):
    """Generate a matrix where elements depend on row/column properties."""
    rows = draw(integers(2, 4))
    draw.record_assignment("rows", rows)

    cols = draw(integers(2, 4))
    draw.record_assignment("cols", cols)

    # Row sums depend on number of columns
    row_sums = []
    for i in range(rows):
        max_sum = cols * 10
        row_sum = draw(integers(0, max_sum))
        draw.record_assignment(f"row_sum_{i}", row_sum)
        row_sums.append(row_sum)

    # Generate matrix elements
    matrix = []
    for i in range(rows):
        row = []
        remaining_sum = row_sums[i]

        for j in range(cols):
            if j == cols - 1:
                # Last element must make the row sum correct
                element = remaining_sum
            else:
                # Other elements depend on remaining sum
                max_element = min(remaining_sum, 10)
                element = draw(integers(0, max_element))
                remaining_sum -= element

            draw.record_assignment(f"element_{i}_{j}", element)
            row.append(element)

        matrix.append(row)

    return {"rows": rows, "cols": cols, "row_sums": row_sums, "matrix": matrix}


# Example 5: Graph generation with edge dependencies
@traced_composite
def graph_strategy(draw: TraceableDrawFn):
    """Generate a graph where edge weights depend on node properties."""
    node_count = draw(integers(3, 6))
    draw.record_assignment("node_count", node_count)

    # Node capacities depend on node count
    node_capacities = []
    for i in range(node_count):
        capacity = draw(integers(10, 20 + node_count * 5))
        draw.record_assignment(f"node_capacity_{i}", capacity)
        node_capacities.append(capacity)

    # Edge count depends on node count
    edge_count = draw(integers(node_count - 1, node_count * 2))
    draw.record_assignment("edge_count", edge_count)

    edges = []
    for i in range(edge_count):
        from_node = draw(choices(range(node_count)))
        draw.record_assignment(f"edge_{i}_from", from_node)

        to_node = draw(choices(range(node_count)))
        draw.record_assignment(f"edge_{i}_to", to_node)

        # Edge weight depends on connected node capacities
        max_weight = min(node_capacities[from_node], node_capacities[to_node])
        weight = draw(integers(1, max_weight))
        draw.record_assignment(f"edge_{i}_weight", weight)

        edges.append({"from": from_node, "to": to_node, "weight": weight})

    return {
        "node_count": node_count,
        "node_capacities": node_capacities,
        "edge_count": edge_count,
        "edges": edges,
    }


# Example 6: Complex nested structure with multiple dependency levels
@traced_composite
def complex_nested_strategy(draw: TraceableDrawFn):
    """Generate a complex nested structure with multiple dependency levels."""
    # Level 1: Basic properties
    base_size = draw(integers(5, 15))
    draw.record_assignment("base_size", base_size)

    # Level 2: Derived properties
    derived_count = draw(integers(1, base_size // 2))
    draw.record_assignment("derived_count", derived_count)

    # Level 3: Nested structures
    nested_structures = []
    for i in range(derived_count):
        # Each nested structure depends on base_size and derived_count
        nested_size = draw(integers(1, base_size - derived_count))
        draw.record_assignment(f"nested_size_{i}", nested_size)

        # Generate nested elements
        nested_elements = []
        for j in range(nested_size):
            # Element values depend on nested size and position
            max_val = nested_size * 2 + j
            element = draw(integers(0, max_val))
            draw.record_assignment(f"nested_element_{i}_{j}", element)
            nested_elements.append(element)

        nested_structures.append({"size": nested_size, "elements": nested_elements})

    # Level 4: Final aggregation
    total_elements = sum(ns["size"] for ns in nested_structures)
    draw.record_assignment("total_elements", total_elements)

    # Final value depends on all previous values
    final_value = draw(integers(0, total_elements * 2))
    draw.record_assignment("final_value", final_value)

    return {
        "base_size": base_size,
        "derived_count": derived_count,
        "nested_structures": nested_structures,
        "total_elements": total_elements,
        "final_value": final_value,
    }


# Test functions to demonstrate tracing functionality
def test_sequence_tracing():
    """Test that sequence generation creates proper traces."""
    result, trace = sequence_strategy.generate_with_trace()

    print("Sequence Strategy Trace:")
    print(f"Generated result: {result}")
    print(f"Trace entries: {len(trace.entries)}")
    print(f"Variable assignments: {trace.variable_assignments}")

    # Check dependencies
    x_deps = trace.get_variable_dependencies("x")
    y_deps = trace.get_variable_dependencies("y")
    z_deps = trace.get_variable_dependencies("z")

    print(f"x dependencies: {x_deps}")
    print(f"y dependencies: {y_deps}")
    print(f"z dependencies: {z_deps}")

    # Verify that y depends on x
    assert "x" in trace.variable_assignments
    assert "y" in trace.variable_assignments
    assert "z" in trace.variable_assignments

    # Check that y and z have dependencies
    assert len(y_deps) > 0
    assert len(z_deps) > 0


def test_list_dependencies_tracing():
    """Test that list generation creates proper dependency traces."""
    result, trace = list_with_dependencies_strategy.generate_with_trace()

    print("\nList Dependencies Strategy Trace:")
    print(f"Generated result: {result}")
    print(f"Trace entries: {len(trace.entries)}")

    # Check that size is recorded
    assert "size" in trace.variable_assignments

    # Check that elements depend on size
    size_dependents = trace.get_dependent_variables("size")

    print(f"Size dependents: {size_dependents}")
    assert len(size_dependents) > 0


def test_tree_dependencies_tracing():
    """Test that tree generation creates proper dependency traces."""
    result, trace = tree_strategy.generate_with_trace()

    print("\nTree Strategy Trace:")
    print(f"Generated result: {result}")
    print(f"Trace entries: {len(trace.entries)}")

    # Check dependencies
    root_deps = trace.get_variable_dependencies("root_value")
    child_count_deps = trace.get_variable_dependencies("child_count")

    print(f"Root dependencies: {root_deps}")
    print(f"Child count dependencies: {child_count_deps}")

    # Verify that child_count depends on root_value
    assert len(child_count_deps) > 0


def test_matrix_dependencies_tracing():
    """Test that matrix generation creates proper dependency traces."""
    result, trace = matrix_strategy.generate_with_trace()

    print("\nMatrix Strategy Trace:")
    print(f"Generated result: {result}")
    print(f"Trace entries: {len(trace.entries)}")

    # Check that matrix elements depend on row sums
    for i in range(result["rows"]):
        row_sum_deps = trace.get_dependent_variables(f"row_sum_{i}")
        print(f"Row {i} sum dependents: {row_sum_deps}")
        assert len(row_sum_deps) > 0


def test_graph_dependencies_tracing():
    """Test that graph generation creates proper dependency traces."""
    result, trace = graph_strategy.generate_with_trace()

    print("\nGraph Strategy Trace:")
    print(f"Generated result: {result}")
    print(f"Trace entries: {len(trace.entries)}")

    # Check that edge weights depend on node capacities
    for i in range(result["edge_count"]):
        edge_weight_deps = trace.get_variable_dependencies(f"edge_{i}_weight")
        print(f"Edge {i} weight dependencies: {edge_weight_deps}")
        assert len(edge_weight_deps) > 0


def test_complex_nested_tracing():
    """Test that complex nested generation creates proper dependency traces."""
    result, trace = complex_nested_strategy.generate_with_trace()

    print("\nComplex Nested Strategy Trace:")
    print(f"Generated result: {result}")
    print(f"Trace entries: {len(trace.entries)}")

    # Check dependency graph
    dependency_graph = trace.get_dependency_graph()
    reverse_deps = trace.get_reverse_dependencies()
    components = trace.get_connected_components()

    print(f"Dependency graph: {dependency_graph}")
    print(f"Reverse dependencies: {reverse_deps}")
    print(f"Connected components: {len(components)}")

    # Verify that we have dependencies
    assert len(dependency_graph) > 0
    assert len(components) > 0


def test_trace_analysis():
    """Test various trace analysis methods."""
    result, trace = sequence_strategy.generate_with_trace()

    print("\nTrace Analysis:")

    # Get all variable dependencies
    all_vars = list(trace.variable_assignments.keys())
    print(f"All variables: {all_vars}")

    for var in all_vars:
        deps = trace.get_variable_dependencies(var)
        dependents = trace.get_dependent_variables(var)
        print(f"{var}: depends on {deps}, dependents: {dependents}")

    # Check connected components
    components = trace.get_connected_components()
    print(f"Connected components: {components}")

    # Verify trace integrity
    assert len(trace.entries) > 0
    assert len(trace.variable_assignments) > 0


if __name__ == "__main__":
    print("Running SnakeCheck Tracing Examples...")
    print("=" * 60)

    tests = [
        ("Sequence tracing", test_sequence_tracing),
        ("List dependencies tracing", test_list_dependencies_tracing),
        ("Tree dependencies tracing", test_tree_dependencies_tracing),
        ("Matrix dependencies tracing", test_matrix_dependencies_tracing),
        ("Graph dependencies tracing", test_graph_dependencies_tracing),
        ("Complex nested tracing", test_complex_nested_tracing),
        ("Trace analysis", test_trace_analysis),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            test_func()
            print("   ✓ Passed!")
            passed += 1
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All tracing tests passed! 🎉")
    else:
        print("Some tests failed - this demonstrates the need for better error handling!")
