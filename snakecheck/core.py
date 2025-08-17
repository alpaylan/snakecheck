"""
Core functionality for SnakeCheck property-based testing.
"""

import functools
import random
from collections.abc import Callable
from typing import Any, TypeVar

from .generators import Strategy

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def strategy[F](func: F) -> F:
    """Decorator to mark a function as a strategy generator."""
    func._is_strategy = True  # type: ignore
    return func


def given(
    *strategies: Strategy[Any], max_examples: int = 100, seed: int | None = None
) -> Callable[[F], F]:
    """
    Decorator for property-based testing.

    Args:
        *strategies: Strategy objects to generate test data
        max_examples: Maximum number of test examples to try
        seed: Random seed for reproducible tests

    Returns:
        Decorated function that runs property tests
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if seed is not None:
                random.seed(seed)

            # Run the test multiple times with different generated values
            for i in range(max_examples):
                try:
                    # Generate test data from strategies
                    test_data = [strat.generate() for strat in strategies]

                    # Call the function with generated data
                    result = func(*test_data, *args, **kwargs)

                    # If we get here without exception, the test passed for this example

                except Exception as e:
                    # Test failed - try to shrink the failing example
                    print(f"Test failed on example {i + 1}: {test_data}")
                    print(f"Error: {e}")

                    # Simple shrinking: try with smaller values
                    shrunk_data = _shrink_failing_example(func, test_data, args, kwargs, e)
                    if shrunk_data:
                        print(f"Minimal failing example: {shrunk_data}")

                    raise e

            # If we get here, all examples passed
            return result

        return wrapper  # type: ignore

    return decorator


def _shrink_failing_example(
    func: Callable[..., Any],
    failing_data: list[Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    original_error: Exception,
) -> list[Any] | None:
    """Simple shrinking algorithm to find minimal failing examples."""
    shrunk_data = failing_data.copy()

    for i, value in enumerate(failing_data):
        if isinstance(value, int | float):
            # Try smaller values
            for attempt in range(10):
                if isinstance(value, int):
                    test_value = value // (2 ** (attempt + 1))
                else:
                    test_value = value / (2 ** (attempt + 1))

                test_data = shrunk_data.copy()
                test_data[i] = test_value

                try:
                    func(*test_data, *args, **kwargs)
                    # If this passes, we can't shrink further
                    break
                except Exception:
                    # This still fails, keep the smaller value
                    shrunk_data[i] = test_value
                    continue

    return shrunk_data if shrunk_data != failing_data else None
