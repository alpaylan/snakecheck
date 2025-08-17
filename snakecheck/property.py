"""
Property-based testing utilities for SnakeCheck.
"""

import time
from collections.abc import Callable
from typing import Any

from .generators import Strategy


class PropertyTest:
    """Class for running property-based tests with more control."""

    def __init__(
        self,
        max_examples: int = 100,
        timeout: float | None = None,
        seed: int | None = None,
        verbose: bool = True,
    ):
        self.max_examples = max_examples
        self.timeout = timeout
        self.seed = seed
        self.verbose = verbose
        self.examples_tried: int = 0
        self.examples_failed: int = 0
        self.start_time: float | None = None

    def forall(
        self, *strategies: Strategy[Any]
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for property-based testing with more control."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                self.start_time = time.time()
                self.examples_tried = 0
                self.examples_failed = 0

                if self.verbose:
                    print(f"Running property test with {self.max_examples} examples...")

                for i in range(self.max_examples):
                    # Check timeout
                    if (
                        self.timeout
                        and self.start_time
                        and time.time() - self.start_time > self.timeout
                    ):
                        if self.verbose:
                            print(f"Test timed out after {self.timeout} seconds")
                        break

                    try:
                        # Generate test data
                        test_data = [strat.generate() for strat in strategies]
                        self.examples_tried += 1

                        # Run the test
                        result = func(*test_data, *args, **kwargs)

                        if self.verbose and (i + 1) % 10 == 0:
                            print(f"  ✓ Example {i + 1}/{self.max_examples} passed")

                    except Exception as e:
                        self.examples_failed += 1
                        if self.verbose:
                            print(f"  ✗ Example {i + 1} failed: {test_data}")
                            print(f"    Error: {e}")

                        # Try to shrink the failing example
                        shrunk = self._shrink_example(func, test_data, args, kwargs, e)
                        if shrunk and self.verbose:
                            print(f"    Minimal failing example: {shrunk}")

                        # Decide whether to continue or stop
                        if self.verbose:
                            print("    Stopping after first failure")
                        break

                # Print summary
                if self.verbose:
                    self._print_summary()

                # Re-raise the last exception if any examples failed
                if self.examples_failed > 0:
                    raise RuntimeError(f"Property test failed on {self.examples_failed} examples")

                return result

            return wrapper

        return decorator

    def _shrink_example(
        self,
        func: Callable[..., Any],
        failing_data: list[Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        error: Exception,
    ) -> list[Any] | None:
        """Shrink a failing example to find a minimal case."""
        # This is a simplified shrinking algorithm
        # In a real implementation, you'd want more sophisticated shrinking

        shrunk_data = failing_data.copy()
        improved = True

        while improved:
            improved = False

            for i, value in enumerate(shrunk_data):
                if isinstance(value, int | float):
                    # Try smaller values
                    if isinstance(value, int) and value != 0:
                        test_value_int: int = value // 2
                        test_data = shrunk_data.copy()
                        test_data[i] = test_value_int
                    elif isinstance(value, float) and value != 0.0:
                        test_value_float: float = value / 2
                        test_data = shrunk_data.copy()
                        test_data[i] = test_value_float
                    else:
                        continue

                    try:
                        func(*test_data, *args, **kwargs)
                        # If this passes, we can't shrink further
                        continue
                    except Exception:
                        # This still fails, keep the smaller value
                        if isinstance(value, int):
                            shrunk_data[i] = test_value_int
                        else:
                            shrunk_data[i] = test_value_float
                        improved = True

        return shrunk_data if shrunk_data != failing_data else None

    def _print_summary(self) -> None:
        """Print a summary of the test run."""
        elapsed = time.time() - self.start_time if self.start_time else 0

        print("\nProperty Test Summary:")
        print(f"  Examples tried: {self.examples_tried}")
        print(f"  Examples failed: {self.examples_failed}")
        print(f"  Time elapsed: {elapsed:.2f}s")

        if self.examples_failed == 0:
            print("  ✓ All examples passed!")
        else:
            print(f"  ✗ {self.examples_failed} examples failed")


# Convenience function
def forall(
    *strategies: Strategy[Any], **kwargs: Any
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Convenience function for creating property tests."""
    test = PropertyTest(**kwargs)
    return test.forall(*strategies)
