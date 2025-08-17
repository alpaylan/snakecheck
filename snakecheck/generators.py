"""
Data generators for SnakeCheck property-based testing.
"""

import random
import string
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Strategy[T](ABC):
    """Base class for data generation strategies."""

    def __init__(self, min_value: Any | None = None, max_value: Any | None = None):
        self.min_value = min_value
        self.max_value = max_value

    @abstractmethod
    def generate(self) -> T:
        """Generate a value according to this strategy."""
        pass

    def map(self, func: Callable[[T], Any]) -> "Strategy[Any]":
        """Apply a function to generated values."""
        return MappedStrategy(self, func)

    def filter(self, predicate: Callable[[T], bool]) -> "Strategy[T]":
        """Filter generated values based on a predicate."""
        return FilteredStrategy(self, predicate)


class MappedStrategy(Strategy[Any]):
    """Strategy that applies a function to generated values."""

    def __init__(self, base_strategy: Strategy[Any], func: Callable[[Any], Any]):
        super().__init__()
        self.base_strategy = base_strategy
        self.func = func

    def generate(self) -> Any:
        return self.func(self.base_strategy.generate())


class FilteredStrategy(Strategy[T]):
    """Strategy that filters generated values."""

    def __init__(self, base_strategy: Strategy[T], predicate: Callable[[T], bool]):
        super().__init__()
        self.base_strategy = base_strategy
        self.predicate = predicate

    def generate(self) -> T:
        # Try up to 100 times to find a value that passes the predicate
        for _ in range(100):
            value = self.base_strategy.generate()
            if self.predicate(value):
                return value
        raise ValueError("Could not generate value satisfying predicate")


class IntegerStrategy(Strategy[int]):
    """Strategy for generating integers."""

    def __init__(self, min_value: int | None = None, max_value: int | None = None):
        super().__init__(min_value, max_value)
        self.min_value: int = min_value if min_value is not None else -1000
        self.max_value: int = max_value if max_value is not None else 1000

    def generate(self) -> int:
        return random.randint(self.min_value, self.max_value)


class FloatStrategy(Strategy[float]):
    """Strategy for generating floats."""

    def __init__(self, min_value: float | None = None, max_value: float | None = None):
        super().__init__(min_value, max_value)
        self.min_value: float = min_value if min_value is not None else -1000.0
        self.max_value: float = max_value if max_value is not None else 1000.0

    def generate(self) -> float:
        return random.uniform(self.min_value, self.max_value)


class StringStrategy(Strategy[str]):
    """Strategy for generating strings."""

    def __init__(self, min_length: int = 0, max_length: int = 100, alphabet: str | None = None):
        super().__init__()
        self.min_length = min_length
        self.max_length = max_length
        self.alphabet = alphabet or string.ascii_letters + string.digits + string.punctuation

    def generate(self) -> str:
        length = random.randint(self.min_length, self.max_length)
        return "".join(random.choices(self.alphabet, k=length))


class BooleanStrategy(Strategy[bool]):
    """Strategy for generating booleans."""

    def generate(self) -> bool:
        return random.choice([True, False])


class ListStrategy(Strategy[list[Any]]):
    """Strategy for generating lists."""

    def __init__(self, element_strategy: Strategy[Any], min_length: int = 0, max_length: int = 10):
        super().__init__()
        self.element_strategy = element_strategy
        self.min_length = min_length
        self.max_length = max_length

    def generate(self) -> list[Any]:
        length = random.randint(self.min_length, self.max_length)
        return [self.element_strategy.generate() for _ in range(length)]


class ChoiceStrategy(Strategy[Any]):
    """Strategy for choosing from a set of values."""

    def __init__(self, choices: list[Any]):
        super().__init__()
        self.choices = choices

    def generate(self) -> Any:
        return random.choice(self.choices)


# Convenience functions for creating strategies
def integers(min_value: int | None = None, max_value: int | None = None) -> IntegerStrategy:
    """Create an integer strategy."""
    return IntegerStrategy(min_value, max_value)


def floats(min_value: float | None = None, max_value: float | None = None) -> FloatStrategy:
    """Create a float strategy."""
    return FloatStrategy(min_value, max_value)


def strings(
    min_length: int = 0, max_length: int = 100, alphabet: str | None = None
) -> StringStrategy:
    """Create a string strategy."""
    return StringStrategy(min_length, max_length, alphabet)


def booleans() -> BooleanStrategy:
    """Create a boolean strategy."""
    return BooleanStrategy()


def lists(
    element_strategy: Strategy[Any], min_length: int = 0, max_length: int = 10
) -> ListStrategy:
    """Create a list strategy."""
    return ListStrategy(element_strategy, min_length, max_length)


def choices(choices: list[Any]) -> ChoiceStrategy:
    """Create a choice strategy."""
    return ChoiceStrategy(choices)
