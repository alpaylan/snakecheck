"""
Dataflow-aware shrinking examples for SnakeCheck property-based testing.

This demonstrates how the new tracing and shrinking system can intelligently
shrink failing examples while preserving dataflow relationships.
"""

from snakecheck import integers, traced_composite
from snakecheck.shrinking import shrink_with_dataflow


# Example 1: Simple sequence with clear dependencies
@traced_composite
def sequence_strategy(draw):
    """Generate a sequence where later values depend on earlier ones."""
    x = draw(integers(0, 100))
    draw.record_assignment("x", x)

    y = draw(integers(0, x))  # y depends on x
    draw.record_assignment("y", y)

    z = draw(integers(y, x + 10))  # z depends on both x and y
    draw.record_assignment("z", z)

    return {"x": x, "y": y, "z": z}


# Example 2: List generation with size dependencies
@traced_composite
def list_strategy(draw):
    """Generate a list where content depends on size."""
    size = draw(integers(1, 10))
    draw.record_assignment("size", size)

    elements = []
    for i in range(size):
        # Each element depends on size and position
        max_val = size * 5 + i
        element = draw(integers(0, max_val))
        draw.record_assignment(f"element_{i}", element)
        elements.append(element)

    return {"size": size, "elements": elements}


# Example 3: Matrix with row/column constraints
@traced_composite
def matrix_strategy(draw):
    """Generate a matrix with row sum constraints."""
    rows = draw(integers(2, 4))
    draw.record_assignment("rows", rows)

    cols = draw(integers(2, 4))
    draw.record_assignment("cols", cols)

    # Row sums depend on number of columns
    row_sums = []
    for i in range(rows):
        max_sum = cols * 8
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
                max_element = min(remaining_sum, 8)
                element = draw(integers(0, max_element))
                remaining_sum -= element

            draw.record_assignment(f"element_{i}_{j}", element)
            row.append(element)

        matrix.append(row)

    return {"rows": rows, "cols": cols, "row_sums": row_sums, "matrix": matrix}


# Example 4: Tree structure with parent-child relationships
@traced_composite
def tree_strategy(draw):
    """Generate a tree with parent-child dependencies."""
    root_value = draw(integers(10, 100))
    draw.record_assignment("root_value", root_value)

    # Number of children depends on root value
    child_count = draw(integers(0, min(5, root_value // 20)))
    draw.record_assignment("child_count", child_count)

    children = []
    for i in range(child_count):
        # Child values depend on parent value
        child_value = draw(integers(root_value - 30, root_value + 30))
        draw.record_assignment(f"child_{i}_value", child_value)

        # Child size depends on child value
        child_size = draw(integers(1, max(1, child_value // 10)))
        draw.record_assignment(f"child_{i}_size", child_size)

        children.append({"value": child_value, "size": child_size})

    return {"root_value": root_value, "child_count": child_count, "children": children}


# Test functions that will fail on certain inputs
def test_sequence_property(data):
    """Test that fails when x is large and y is close to x."""
    x, y, z = data["x"], data["y"], data["z"]

    # This will fail when x is large and y is close to x
    if x > 50 and y > x * 0.8:
        raise ValueError(f"Invalid sequence: x={x}, y={y}, z={z}")

    return True


def test_list_property(data):
    """Test that fails when size is large and elements are near their maximum."""
    size = data["size"]
    elements = data["elements"]

    # This will fail when size is large and elements are near max
    if size > 5:
        max_elements = [size * 5 + i for i in range(size)]
        if all(
            elem > max_elem * 0.8 for elem, max_elem in zip(elements, max_elements, strict=False)
        ):
            raise ValueError(f"Invalid list: size={size}, elements={elements}")

    return True


def test_matrix_property(data):
    """Test that fails when row sums are large."""
    row_sums = data["row_sums"]

    # This will fail when any row sum is too large
    if any(rs > 20 for rs in row_sums):
        raise ValueError(f"Invalid matrix: row_sums={row_sums}")

    return True


def test_tree_property(data):
    """Test that fails when root value is large and has many children."""
    root_value = data["root_value"]
    child_count = data["child_count"]

    # This will fail when root is large and has many children
    if root_value > 80 and child_count > 3:
        raise ValueError(f"Invalid tree: root={root_value}, children={child_count}")

    return True


def find_failing_example(strategy, test_func, max_attempts=100):
    """Find a failing example by generating multiple times."""
    for attempt in range(max_attempts):
        try:
            result, trace = strategy.generate_with_trace()
            test_func(result)
        except Exception as e:
            print(f"Found failing example on attempt {attempt + 1}: {e}")
            return result, trace

    print("No failing example found in max attempts")
    return None, None


def demonstrate_shrinking(strategy_name: str, strategy, test_func):
    """Demonstrate dataflow-aware shrinking for a strategy."""
    print(f"\n{'=' * 60}")
    print(f"Demonstrating shrinking for: {strategy_name}")
    print(f"{'=' * 60}")

    # Find a failing example
    print("Finding failing example...")
    result, trace = find_failing_example(strategy, test_func)

    if result is None:
        print("Could not find failing example, skipping shrinking demonstration")
        return

    print(f"Original failing example: {result}")
    print(f"Trace entries: {len(trace.entries)}")
    print(f"Variable assignments: {len(trace.variable_assignments)}")

    # Show dependency information
    print("\nDependency Analysis:")
    for var_name, _trace_id in trace.variable_assignments.items():
        deps = trace.get_variable_dependencies(var_name)
        dependents = trace.get_dependent_variables(var_name)
        print(f"  {var_name}: depends on {len(deps)} values, {len(dependents)} dependents")

    # Show connected components
    components = trace.get_connected_components()
    print(f"\nConnected components: {len(components)}")
    for i, component in enumerate(components):
        print(f"  Component {i}: {len(component)} nodes")

    # Now try to shrink
    print("\nShrinking...")
    try:
        shrunk_value, shrunk_trace = shrink_with_dataflow(trace, test_func)

        print(f"Shrunk result: {shrunk_value}")
        print(f"Shrunk trace entries: {len(shrunk_trace.entries)}")
        print(f"Shrunk variable assignments: {len(shrunk_trace.variable_assignments)}")

        # Show what changed
        original_vars = set(trace.variable_assignments.keys())
        shrunk_vars = set(shrunk_trace.variable_assignments.keys())

        removed_vars = original_vars - shrunk_vars
        if removed_vars:
            print(f"Removed variables: {removed_vars}")

        # Show dependency changes
        print("\nDependency changes:")
        for var_name in shrunk_vars:
            if var_name in trace.variable_assignments:
                orig_deps = trace.get_variable_dependencies(var_name)
                shrunk_deps = shrunk_trace.get_variable_dependencies(var_name)
                if orig_deps != shrunk_deps:
                    print(f"  {var_name}: {len(orig_deps)} -> {len(shrunk_deps)} dependencies")

    except Exception as e:
        print(f"Shrinking failed: {e}")


def demonstrate_trace_analysis():
    """Demonstrate various trace analysis capabilities."""
    print(f"\n{'=' * 60}")
    print("Trace Analysis Demonstration")
    print(f"{'=' * 60}")

    # Generate a trace
    result, trace = sequence_strategy.generate_with_trace()

    print(f"Generated sequence: {result}")
    print(f"Trace has {len(trace.entries)} entries")

    # Show dependency graph
    print("\nDependency Graph:")
    dependency_graph = trace.get_dependency_graph()
    for entry_id, deps in dependency_graph.items():
        print(f"  {entry_id}: depends on {deps}")

    # Show reverse dependencies
    print("\nReverse Dependencies:")
    reverse_deps = trace.get_reverse_dependencies()
    for entry_id, dependents in reverse_deps.items():
        print(f"  {entry_id}: {len(dependents)} dependents")

    # Show variable flow
    print("\nVariable Flow:")
    for var_name, trace_id in trace.variable_assignments.items():
        deps = trace.get_variable_dependencies(var_name)
        dependents = trace.get_dependent_variables(var_name)
        print(f"  {var_name} ({trace_id}):")
        print(f"    Dependencies: {deps}")
        print(f"    Dependents: {dependents}")

    # Show connected components
    print("\nConnected Components:")
    components = trace.get_connected_components()
    for i, component in enumerate(components):
        print(f"  Component {i}: {component}")
        if len(component) > 1:
            print(f"    Size: {len(component)}")
            print(
                f"    Root nodes: {[tid for tid in component if not dependency_graph.get(tid, set())]}"
            )


if __name__ == "__main__":
    print("Running SnakeCheck Dataflow-Aware Shrinking Examples...")

    # Demonstrate shrinking for different strategies
    strategies = [
        ("Sequence Strategy", sequence_strategy, test_sequence_property),
        ("List Strategy", list_strategy, test_list_property),
        ("Matrix Strategy", matrix_strategy, test_matrix_property),
        ("Tree Strategy", tree_strategy, test_tree_property),
    ]

    for name, strategy, test_func in strategies:
        try:
            demonstrate_shrinking(name, strategy, test_func)
        except Exception as e:
            print(f"Failed to demonstrate {name}: {e}")

    # Demonstrate trace analysis
    demonstrate_trace_analysis()

    print(f"\n{'=' * 60}")
    print("Dataflow-aware shrinking demonstration complete!")
    print(f"{'=' * 60}")
