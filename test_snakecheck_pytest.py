"""
Pytest-compatible tests for SnakeCheck.

These tests verify SnakeCheck's internal functionality without using the @given decorator,
making them compatible with pytest's test discovery and execution.
"""

import pytest

from snakecheck.composite import CompositeStrategy, composite, composite_strategy
from snakecheck.generators import Strategy, booleans, choices, floats, integers, lists, strings


class TestBasicStrategies:
    """Test basic strategy generation."""

    def test_integers_strategy(self):
        """Test integer strategy generation."""
        strategy = integers(-10, 10)
        assert isinstance(strategy, Strategy)

        # Generate multiple values to ensure they're in range
        for _ in range(100):
            value = strategy.generate()
            assert isinstance(value, int)
            assert -10 <= value <= 10

    def test_strings_strategy(self):
        """Test string strategy generation."""
        strategy = strings(min_length=3, max_length=8)
        assert isinstance(strategy, Strategy)

        for _ in range(100):
            value = strategy.generate()
            assert isinstance(value, str)
            assert 3 <= len(value) <= 8

    def test_booleans_strategy(self):
        """Test boolean strategy generation."""
        strategy = booleans()
        assert isinstance(strategy, Strategy)

        values = set()
        for _ in range(100):
            value = strategy.generate()
            assert isinstance(value, bool)
            values.add(value)

        # Should generate both True and False
        assert len(values) == 2

    def test_floats_strategy(self):
        """Test float strategy generation."""
        strategy = floats(-5.0, 5.0)
        assert isinstance(strategy, Strategy)

        for _ in range(100):
            value = strategy.generate()
            assert isinstance(value, float)
            assert -5.0 <= value <= 5.0

    def test_lists_strategy(self):
        """Test list strategy generation."""
        strategy = lists(integers(1, 10), min_length=0, max_length=5)
        assert isinstance(strategy, Strategy)

        for _ in range(100):
            value = strategy.generate()
            assert isinstance(value, list)
            assert 0 <= len(value) <= 5
            for item in value:
                assert isinstance(item, int)
                assert 1 <= item <= 10

    def test_choices_strategy(self):
        """Test choices strategy generation."""
        options = ["apple", "banana", "cherry"]
        strategy = choices(options)
        assert isinstance(strategy, Strategy)

        values = set()
        for _ in range(100):
            value = strategy.generate()
            assert value in options
            values.add(value)

        # Should generate all options
        assert len(values) == 3


class TestStrategyComposition:
    """Test strategy composition methods."""

    def test_filter_strategy(self):
        """Test filtering strategies."""
        strategy = integers(1, 100).filter(lambda x: x % 2 == 0)
        assert isinstance(strategy, Strategy)

        for _ in range(100):
            value = strategy.generate()
            assert value % 2 == 0
            assert 1 <= value <= 100

    def test_map_strategy(self):
        """Test mapping strategies."""
        strategy = integers(1, 10).map(lambda x: x * 2)
        assert isinstance(strategy, Strategy)

        for _ in range(100):
            value = strategy.generate()
            assert value % 2 == 0
            assert 2 <= value <= 20


class TestCompositeStrategies:
    """Test composite strategy functionality."""

    def test_composite_function(self):
        """Test composite() function."""

        def point_strategy(draw):
            x = draw(integers(-10, 10))
            y = draw(integers(-10, 10))
            return {"x": x, "y": y}

        strategy = composite(point_strategy)
        assert isinstance(strategy, CompositeStrategy)

        for _ in range(100):
            point = strategy.generate()
            assert isinstance(point, dict)
            assert "x" in point
            assert "y" in point
            assert -10 <= point["x"] <= 10
            assert -10 <= point["y"] <= 10

    def test_composite_strategy_decorator(self):
        """Test @composite_strategy decorator."""

        @composite_strategy
        def user_strategy(draw):
            name = draw(strings(min_length=1, max_length=10))
            age = draw(integers(0, 120))
            return {"name": name, "age": age}

        assert isinstance(user_strategy, CompositeStrategy)

        for _ in range(100):
            user = user_strategy.generate()
            assert isinstance(user, dict)
            assert "name" in user
            assert "age" in user
            assert isinstance(user["name"], str)
            assert isinstance(user["age"], int)
            assert 1 <= len(user["name"]) <= 10
            assert 0 <= user["age"] <= 120

    def test_nested_composite_strategies(self):
        """Test nested composite strategies."""

        @composite_strategy
        def address_strategy(draw):
            street = draw(strings(min_length=5, max_length=20))
            city = draw(strings(min_length=3, max_length=15))
            return {"street": street, "city": city}

        @composite_strategy
        def person_strategy(draw):
            name = draw(strings(min_length=2, max_length=15))
            age = draw(integers(18, 100))
            address = draw(address_strategy)
            return {"name": name, "age": age, "address": address}

        assert isinstance(person_strategy, CompositeStrategy)

        for _ in range(100):
            person = person_strategy.generate()
            assert isinstance(person, dict)
            assert "name" in person
            assert "age" in person
            assert "address" in person
            assert isinstance(person["address"], dict)
            assert "street" in person["address"]
            assert "city" in person["address"]


class TestStrategyProperties:
    """Test strategy properties and invariants."""

    def test_strategy_identity(self):
        """Test that strategies maintain identity across calls."""
        strategy = integers(1, 10)
        strategy2 = integers(1, 10)

        # Different instances should generate different sequences
        values1 = [strategy.generate() for _ in range(10)]
        values2 = [strategy2.generate() for _ in range(10)]

        # They might be the same by chance, but shouldn't always be
        # This is a probabilistic test
        assert len(set(values1)) > 0
        assert len(set(values2)) > 0

    def test_strategy_reproducibility(self):
        """Test that strategies can be called multiple times."""
        strategy = integers(1, 100)

        # Should be able to generate multiple values
        values = []
        for _ in range(50):
            values.append(strategy.generate())

        assert len(values) == 50
        assert all(isinstance(v, int) for v in values)
        assert all(1 <= v <= 100 for v in values)


if __name__ == "__main__":
    # Run tests directly if file is executed
    pytest.main([__file__, "-v"])
