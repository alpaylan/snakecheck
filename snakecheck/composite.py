"""
Composite strategies for SnakeCheck property-based testing.

This module provides a way to compose complex data types by drawing from multiple
strategies within a single test function, similar to Hypothesis's composite approach.
"""

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from .generators import Strategy
from .trace import GenerationTrace, TraceableDrawFn, create_traceable_draw

T = TypeVar("T")


class DrawFn(Protocol):
    """Protocol for draw functions that can generate values from strategies."""

    def __call__(self, strategy: Strategy[T]) -> T:
        """Draw a value from the given strategy."""
        ...


class CompositeStrategy(Strategy[T]):
    """Strategy that composes complex data types using a draw function."""

    def __init__(self, draw_fn: Callable[[DrawFn], T]):
        super().__init__()
        self.draw_fn = draw_fn

    def generate(self) -> T:
        """Generate a value using the composite draw function."""
        return self.draw_fn(self._draw)

    def _draw(self, strategy: Strategy[Any]) -> Any:
        """Internal draw function that generates values from strategies."""
        return strategy.generate()

    def generate_with_trace(self) -> tuple[T, GenerationTrace]:
        """Generate a value and return it along with the generation trace."""
        from .trace import create_traceable_draw

        draw_fn, trace = create_traceable_draw()
        result = self.draw_fn(draw_fn)
        return result, trace


def composite[T](draw_fn: Callable[[DrawFn], T]) -> CompositeStrategy[T]:
    """
    Create a composite strategy that composes complex data types.

    Args:
        draw_fn: A function that takes a DrawFn and returns a composed value.
                The DrawFn can be used to draw values from other strategies.

    Returns:
        A CompositeStrategy that generates values using the draw function.

    Example:
        @composite
        def point_strategy(draw):
            x = draw(integers(-100, 100))
            y = draw(integers(-100, 100))
            return Point(x, y)

        @given(point_strategy)
        def test_point_properties(point):
            assert point.x >= -100 and point.x <= 100
            assert point.y >= -100 and point.y <= 100
    """
    return CompositeStrategy(draw_fn)


# Convenience decorator for creating composite strategies
def composite_strategy[T](func: Callable[[DrawFn], T]) -> CompositeStrategy[T]:
    """
    Decorator for creating composite strategies.

    This is an alternative to the composite() function that can be used
    as a decorator for cleaner syntax.

    Example:
        @composite_strategy
        def user_strategy(draw):
            name = draw(strings(min_length=1, max_length=50))
            age = draw(integers(0, 120))
            email = draw(strings(min_length=5, max_length=100))
            return User(name, age, email)
    """
    return CompositeStrategy(func)


def traced_composite[T](func: Callable[[TraceableDrawFn], T]) -> CompositeStrategy[T]:
    """
    Create a composite strategy that records generation traces.

    This version provides a TraceableDrawFn that can record variable assignments
    and dependencies for dataflow-aware shrinking.

    Example:
        @traced_composite
        def sequence_strategy(draw):
            x = draw(integers(0, 10))
            draw.record_assignment("x", x)

            y = draw(integers(0, x))
            draw.record_assignment("y", y)

            return {"x": x, "y": y}
    """

    def wrapper(draw: DrawFn) -> T:
        # Convert regular draw to traceable draw if needed
        if isinstance(draw, TraceableDrawFn):
            return func(draw)
        else:
            # Create a new trace for this generation
            traceable_draw, _ = create_traceable_draw()
            return func(traceable_draw)

    return CompositeStrategy(wrapper)
