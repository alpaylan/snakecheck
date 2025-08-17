"""
Generation tracing for SnakeCheck property-based testing.

This module provides a way to trace the generation of values and their dependencies,
enabling dataflow-aware shrinking algorithms.
"""

from dataclasses import dataclass, field
from typing import Any

from .generators import Strategy


@dataclass
class TraceEntry:
    """A single entry in the generation trace."""

    id: str
    strategy: Strategy[Any]
    value: Any
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationTrace:
    """A complete trace of value generation with dependencies."""

    entries: list[TraceEntry] = field(default_factory=list)
    variable_assignments: dict[str, str] = field(default_factory=dict)  # var_name -> trace_id
    _next_id: int = 0

    def add_entry(
        self, strategy: Strategy[Any], value: Any, dependencies: list[str] | None = None
    ) -> str:
        """Add a new trace entry and return its ID."""
        trace_id = f"t{self._next_id}"
        self._next_id += 1

        entry = TraceEntry(
            id=trace_id, strategy=strategy, value=value, dependencies=dependencies or []
        )

        self.entries.append(entry)
        return trace_id

    def assign_variable(self, var_name: str, trace_id: str) -> None:
        """Record a variable assignment."""
        self.variable_assignments[var_name] = trace_id

    def get_dependency_graph(self) -> dict[str, set[str]]:
        """Build a dependency graph from the trace."""
        graph = {}

        for entry in self.entries:
            graph[entry.id] = set(entry.dependencies)

        return graph

    def get_reverse_dependencies(self) -> dict[str, set[str]]:
        """Get reverse dependencies (what depends on each value)."""
        reverse: dict[str, set[str]] = {}

        for entry in self.entries:
            for dep_id in entry.dependencies:
                if dep_id not in reverse:
                    reverse[dep_id] = set()
                reverse[dep_id].add(entry.id)

        return reverse

    def get_connected_components(self) -> list[set[str]]:
        """Find connected components in the dependency graph."""
        visited = set()
        components = []

        def dfs(node_id: str, component: set[str]) -> None:
            if node_id in visited:
                return

            visited.add(node_id)
            component.add(node_id)

            # Find the entry for this node
            entry = next((e for e in self.entries if e.id == node_id), None)
            if entry:
                # Visit dependencies
                for dep_id in entry.dependencies:
                    dfs(dep_id, component)

                # Visit reverse dependencies
                reverse_deps = self.get_reverse_dependencies()
                for rev_dep_id in reverse_deps.get(node_id, []):
                    dfs(rev_dep_id, component)

        for entry in self.entries:
            if entry.id not in visited:
                component: set[str] = set()
                dfs(entry.id, component)
                components.append(component)

        return components

    def get_variable_dependencies(self, var_name: str) -> set[str]:
        """Get all trace IDs that a variable depends on."""
        if var_name not in self.variable_assignments:
            return set()

        trace_id = self.variable_assignments[var_name]
        dependencies = set()

        def collect_deps(node_id: str) -> None:
            if node_id in dependencies:
                return

            dependencies.add(node_id)
            entry = next((e for e in self.entries if e.id == node_id), None)
            if entry:
                for dep_id in entry.dependencies:
                    collect_deps(dep_id)

        collect_deps(trace_id)
        return dependencies

    def get_dependent_variables(self, var_name: str) -> set[str]:
        """Get all variables that depend on a given variable."""
        if var_name not in self.variable_assignments:
            return set()

        trace_id = self.variable_assignments[var_name]
        dependent_vars = set()

        reverse_deps = self.get_reverse_dependencies()

        def collect_dependents(node_id: str) -> None:
            for dep_id in reverse_deps.get(node_id, []):
                # Find which variable this trace ID belongs to
                for var, tid in self.variable_assignments.items():
                    if tid == dep_id:
                        dependent_vars.add(var)
                        collect_dependents(dep_id)

        collect_dependents(trace_id)
        return dependent_vars


class TraceableDrawFn:
    """A draw function that records generation traces."""

    def __init__(self, trace: GenerationTrace):
        self.trace = trace
        self._current_dependencies: list[str] = []
        self._dependency_stack: list[list[str]] = []

    def __call__(self, strategy: Strategy[Any]) -> Any:
        """Draw a value from a strategy and record it in the trace."""
        value = strategy.generate()

        # Record the trace entry with current dependencies
        trace_id = self.trace.add_entry(
            strategy=strategy, value=value, dependencies=self._current_dependencies.copy()
        )

        # Add this trace ID to current dependencies for future draws
        self._current_dependencies.append(trace_id)

        return value

    def with_dependencies(self, dependencies: list[str]) -> "TraceableDrawFn":
        """Create a new draw function with specific dependencies."""
        new_draw = TraceableDrawFn(self.trace)
        new_draw._current_dependencies = dependencies.copy()
        new_draw._dependency_stack = self._dependency_stack.copy()
        return new_draw

    def push_dependencies(self) -> None:
        """Push current dependencies onto the stack."""
        self._dependency_stack.append(self._current_dependencies.copy())

    def pop_dependencies(self) -> None:
        """Pop dependencies from the stack."""
        if self._dependency_stack:
            self._current_dependencies = self._dependency_stack.pop()

    def record_assignment(self, var_name: str, value: Any) -> None:
        """Record a variable assignment in the trace."""
        # Find the most recent trace entry for this value
        for entry in reversed(self.trace.entries):
            if entry.value == value:
                self.trace.assign_variable(var_name, entry.id)
                break


def create_traceable_draw() -> tuple[TraceableDrawFn, GenerationTrace]:
    """Create a traceable draw function and its associated trace."""
    trace = GenerationTrace()
    draw_fn = TraceableDrawFn(trace)
    return draw_fn, trace
