"""
Dataflow-aware shrinking for SnakeCheck property-based testing.

This module implements shrinking algorithms that understand the relationships
between generated values, enabling more intelligent shrinking strategies.
"""

from collections.abc import Callable
from typing import Any

from .trace import GenerationTrace, TraceEntry


class DataflowAwareShrinker:
    """A shrinking algorithm that understands dataflow dependencies."""

    def __init__(self, trace: GenerationTrace):
        self.trace = trace
        self.dependency_graph = trace.get_dependency_graph()
        self.reverse_dependencies = trace.get_reverse_dependencies()

    def shrink_failing_example(
        self, test_func: Callable[[Any], bool]
    ) -> tuple[Any, GenerationTrace]:
        """
        Shrink a failing example while preserving dataflow relationships.

        Args:
            test_func: Function that tests if a value is valid (returns True for valid)

        Returns:
            Tuple of (shrunk_value, shrunk_trace)
        """
        current_trace = self.trace
        current_value = self._reconstruct_value(current_trace)

        # Try to shrink by reducing individual values
        shrunk_trace = self._shrink_individual_values(current_trace, test_func)
        if shrunk_trace:
            current_trace = shrunk_trace
            current_value = self._reconstruct_value(current_trace)

        # Try to shrink by reducing dependency chains
        shrunk_trace = self._shrink_dependency_chains(current_trace, test_func)
        if shrunk_trace:
            current_trace = shrunk_trace
            current_value = self._reconstruct_value(current_trace)

        # Try to shrink by removing optional dependencies
        shrunk_trace = self._shrink_optional_dependencies(current_trace, test_func)
        if shrunk_trace:
            current_trace = shrunk_trace
            current_value = self._reconstruct_value(current_trace)

        return current_value, current_trace

    def _reconstruct_value(self, trace: GenerationTrace) -> Any:
        """Reconstruct the original value from a trace."""
        # This is a simplified reconstruction - in practice, you'd need
        # to store the original structure and reconstruct it
        return {entry.id: entry.value for entry in trace.entries}

    def _shrink_individual_values(
        self, trace: GenerationTrace, test_func: Callable[[Any], bool]
    ) -> GenerationTrace | None:
        """Try to shrink individual values while preserving dependencies."""
        shrunk_trace = trace

        # Sort entries by dependency depth (leaves first)
        sorted_entries = self._sort_by_dependency_depth(trace.entries)

        for entry in sorted_entries:
            # Try to shrink this value
            shrunk_value = self._try_shrink_value(entry.value, entry.strategy)
            if shrunk_value != entry.value:
                # Create new trace with shrunk value
                new_trace = self._create_modified_trace(trace, entry.id, shrunk_value)

                # Test if the shrunk value still fails
                if self._test_trace(new_trace, test_func):
                    shrunk_trace = new_trace
                    print(f"    Shrunk {entry.id} from {entry.value} to {shrunk_value}")
                    break

        return shrunk_trace if shrunk_trace != trace else None

    def _shrink_dependency_chains(
        self, trace: GenerationTrace, test_func: Callable[[Any], bool]
    ) -> GenerationTrace | None:
        """Try to shrink by reducing dependency chains."""
        # Find connected components
        components = trace.get_connected_components()

        for component in components:
            if len(component) > 1:
                # Try to shrink this component
                shrunk_trace = self._shrink_component(trace, component, test_func)
                if shrunk_trace:
                    return shrunk_trace

        return None

    def _shrink_component(
        self, trace: GenerationTrace, component: set[str], test_func: Callable[[Any], bool]
    ) -> GenerationTrace | None:
        """Try to shrink a connected component."""
        # Find the root of this component (entry with no dependencies)
        root_ids = [tid for tid in component if not self.dependency_graph.get(tid, set())]

        if not root_ids:
            return None

        # Try to shrink the root values
        for root_id in root_ids:
            entry = next(e for e in trace.entries if e.id == root_id)
            shrunk_value = self._try_shrink_value(entry.value, entry.strategy)

            if shrunk_value != entry.value:
                new_trace = self._create_modified_trace(trace, root_id, shrunk_value)
                if self._test_trace(new_trace, test_func):
                    print(
                        f"    Shrunk component root {root_id} from {entry.value} to {shrunk_value}"
                    )
                    return new_trace

        return None

    def _shrink_optional_dependencies(
        self, trace: GenerationTrace, test_func: Callable[[Any], bool]
    ) -> GenerationTrace | None:
        """Try to shrink by removing optional dependencies."""
        # Find entries that might be optional (have many dependents but few dependencies)
        for entry in trace.entries:
            dependents = self.reverse_dependencies.get(entry.id, set())

            if len(dependents) > 1 and len(entry.dependencies) <= 1:
                # This might be optional - try removing it
                new_trace = self._remove_entry(trace, entry.id)
                if new_trace and self._test_trace(new_trace, test_func):
                    print(f"    Removed optional entry {entry.id} with value {entry.value}")
                    return new_trace

        return None

    def _try_shrink_value(self, value: Any, strategy: Any) -> Any:
        """Try to shrink a single value."""
        if isinstance(value, int):
            return self._try_shrink_int(value)
        elif isinstance(value, str):
            return self._try_shrink_str(value)
        elif isinstance(value, list):
            return self._try_shrink_list(value)

        return value

    def _try_shrink_int(self, value: int) -> int:
        """Try to shrink an integer value."""
        if value > 0:
            # Try to reduce by half, but ensure we don't go below 0
            shrunk_value = max(0, value // 2)
            if shrunk_value != value:
                return shrunk_value
        elif value < 0:
            # Try to reduce negative values by half
            shrunk_value = value // 2
            if shrunk_value != value:
                return shrunk_value

        return value

    def _try_shrink_str(self, value: str) -> str:
        """Try to shrink a string value."""
        if len(value) > 1:
            shrunk_value = value[: len(value) // 2]
            if shrunk_value != value:
                return shrunk_value

        return value

    def _try_shrink_list(self, value: list[Any]) -> list[Any]:
        """Try to shrink a list value."""
        if len(value) > 1:
            shrunk_value = value[: len(value) // 2]
            if shrunk_value != value:
                return shrunk_value

        return value

    def _sort_by_dependency_depth(self, entries: list[TraceEntry]) -> list[TraceEntry]:
        """Sort entries by dependency depth (leaves first)."""

        def get_depth(entry_id: str, visited: set[str] | None = None) -> int:
            if visited is None:
                visited = set()

            if entry_id in visited:
                return 0

            visited.add(entry_id)
            deps = self.dependency_graph.get(entry_id, set())

            if not deps:
                return 0

            return 1 + max(get_depth(dep, visited) for dep in deps)

        return sorted(entries, key=lambda e: get_depth(e.id))

    def _create_modified_trace(
        self, trace: GenerationTrace, entry_id: str, new_value: Any
    ) -> GenerationTrace:
        """Create a new trace with a modified entry value."""
        from copy import deepcopy

        new_trace = deepcopy(trace)

        # Update the entry value
        for entry in new_trace.entries:
            if entry.id == entry_id:
                entry.value = new_value
                break

        return new_trace

    def _remove_entry(self, trace: GenerationTrace, entry_id: str) -> GenerationTrace | None:
        """Remove an entry from the trace."""
        from copy import deepcopy

        new_trace = deepcopy(trace)

        # Remove the entry
        new_trace.entries = [e for e in new_trace.entries if e.id != entry_id]

        # Remove from variable assignments
        new_trace.variable_assignments = {
            var: tid for var, tid in new_trace.variable_assignments.items() if tid != entry_id
        }

        # Update dependencies
        for entry in new_trace.entries:
            entry.dependencies = [dep for dep in entry.dependencies if dep != entry_id]

        return new_trace

    def _test_trace(self, trace: GenerationTrace, test_func: Callable[[Any], bool]) -> bool:
        """Test if a trace still produces a failing example."""
        try:
            value = self._reconstruct_value(trace)
            # We want the test to FAIL (raise an exception) for shrinking to work
            test_func(value)
            return False  # Test passed, so this is not a failing example
        except Exception:
            return True  # Test failed, so this is still a failing example


def shrink_with_dataflow(
    trace: GenerationTrace, test_func: Callable[[Any], bool]
) -> tuple[Any, GenerationTrace]:
    """
    Shrink a failing example using dataflow-aware shrinking.

    Args:
        trace: The generation trace to shrink
        test_func: Function that tests if a value is valid

    Returns:
        Tuple of (shrunk_value, shrunk_trace)
    """
    shrinker = DataflowAwareShrinker(trace)
    return shrinker.shrink_failing_example(test_func)
