# SnakeCheck 🐍

A simple Hypothesis clone for property-based testing in Python.

> Note.  
> This entire repository is mostly AI generated, created for fast experimentation purposes, I do not
> suggest reading it for the sake of your time.

## Features

- **Property-Based Testing**: Use `@given` decorator to test properties across generated data
- **Data Generation Strategies**: Built-in strategies for common data types
- **Strategy Composition**: Combine and modify strategies with `.map()` and `.filter()`
- **Composite Strategies**: Create complex data types by composing simpler strategies
- **Stateful Testing**: Generate data where later values depend on earlier ones
- **Generation Tracing**: Track dataflow and dependencies between generated values
- **Dataflow-Aware Shrinking**: Intelligent shrinking that preserves data relationships
- **Flexible Test Control**: Use `forall` for granular control over test execution

## What is SnakeCheck?

SnakeCheck is a lightweight property-based testing library inspired by [Hypothesis](https://hypothesis.readthedocs.io/). It allows you to write tests that verify properties of your code by automatically generating test data and running your functions with many different inputs.

## Key Features

- **Property-based testing**: Test properties that should hold for all valid inputs
- **Automatic data generation**: Built-in strategies for common data types
- **Custom strategies**: Create your own data generators
- **Shrinking**: Automatically find minimal failing examples
- **Type hints**: Full support for Python type annotations
- **Simple API**: Easy to learn and use

## Installation

SnakeCheck is a pure Python package with no external dependencies. Simply clone the repository and you're ready to go!

```bash
git clone <repository-url>
cd snakecheck
```

## Quick Start

### Basic Usage

```python
from src import given, integers, strings

# Test that addition is commutative
@given(integers(), integers())
def test_addition_commutative(a: int, b: int):
    assert a + b == b + a

# Test string properties
@given(strings(min_length=1, max_length=10))
def test_string_length(s: str):
    assert len(s) > 0
    assert len(s) <= 10
```

### Running Tests

```python
# Run a test function
test_addition_commutative()

# Or run from command line
python examples/basic_usage.py
```

## Core Concepts

### 1. Strategies

Strategies are objects that generate test data. SnakeCheck comes with several built-in strategies:

```python
from src import integers, floats, strings, booleans, lists, choices

# Basic strategies
integers()                    # Random integers in [-1000, 1000]
integers(0, 100)            # Random integers in [0, 100]
floats(-10.0, 10.0)        # Random floats in [-10.0, 10.0]
strings(min_length=1, max_length=20)  # Random strings
booleans()                  # Random booleans

# Composite strategies
lists(integers(), min_length=0, max_length=5)  # Lists of integers
choices([1, 2, 3, 4, 5])   # Random choice from list
```

### 2. The @given Decorator

The `@given` decorator is the main way to write property-based tests:

```python
@given(integers(), integers())
def test_property(a: int, b: int):
    # This function will be called multiple times with different a, b values
    result = some_function(a, b)
    assert some_property_holds(result)
```

### 3. Custom Strategies

You can create your own strategies by inheriting from the `Strategy` base class:

```python
from src import Strategy
import random

class EmailStrategy(Strategy[str]):
    def generate(self) -> str:
        username = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))
        domain = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
        return f"{username}@{domain}.com"

# Use your custom strategy
@given(EmailStrategy())
def test_email_properties(email: str):
    assert '@' in email
    assert '.' in email
```

### 4. Composite Strategies

For complex data types, you can use composite strategies that compose multiple strategies together:

```python
from snakecheck import composite, composite_strategy, integers, strings

# Using the composite() function
def user_strategy(draw):
    name = draw(strings(min_length=1, max_length=50))
    age = draw(integers(0, 120))
    email = draw(strings(min_length=5, max_length=100))
    return {"name": name, "age": age, "email": email}

# Using the decorator syntax
@composite_strategy
def point_strategy(draw):
    x = draw(integers(-100, 100))
    y = draw(integers(-100, 100))
    return {"x": x, "y": y}

# Use composite strategies in tests
@given(composite(user_strategy))
def test_user_properties(user):
    assert 0 <= user["age"] <= 120
    assert len(user["name"]) > 0

@given(point_strategy)
def test_point_properties(point):
    assert -100 <= point["x"] <= 100
    assert -100 <= point["y"] <= 100
```

### 5. Strategy Composition

Strategies can be combined and modified:

```python
from snakecheck import integers, strings

# Filter strategies
positive_integers = integers(1, 1000)
even_integers = positive_integers.filter(lambda x: x % 2 == 0)

# Map strategies
doubled_integers = integers(-50, 50).map(lambda x: x * 2)

# Use composed strategies
@given(even_integers, doubled_integers)
def test_even_and_doubled(a: int, b: int):
    assert a % 2 == 0  # a is even
    assert b % 2 == 0  # b is doubled, so also even
```

### 6. Stateful Testing

Stateful testing allows you to generate data where later parts depend on earlier generated values:

```python
@composite_strategy
def linked_list_strategy(draw):
    """Generate a linked list where each value depends on the previous."""
    length = draw(integers(1, 10))
    nodes = []
    
    # First node has a random value
    first_value = draw(integers(-100, 100))
    nodes.append({"value": first_value, "next": None})
    
    # Subsequent nodes depend on previous values
    for i in range(1, length):
        prev_node = nodes[i - 1]
        # Value depends on previous: could be increment, decrement, or related
        dependency_type = draw(choices(["increment", "decrement", "double", "half", "same"]))
        
        if dependency_type == "increment":
            new_value = prev_node["value"] + draw(integers(1, 10))
        elif dependency_type == "decrement":
            new_value = prev_node["value"] - draw(integers(1, 10))
        elif dependency_type == "double":
            new_value = prev_node["value"] * 2
        elif dependency_type == "half":
            new_value = prev_node["value"] // 2
        else:  # same
            new_value = prev_node["value"]
        
        # Ensure the value stays within bounds
        new_value = max(-200, min(200, new_value))
        
        nodes.append({"value": new_value, "next": None})
        nodes[i - 1]["next"] = i  # Link to next node
    
    return nodes
```

This is useful for testing systems with dependencies, such as:
- Linked lists, BSTs, and other data structures
- Stack operations based on current size
- Database transactions maintaining balance consistency
- Graph generation with edge weights dependent on node properties

## 7. Generation Tracing and Dataflow-Aware Shrinking

SnakeCheck's advanced tracing system tracks how generated values depend on each other, enabling intelligent shrinking that preserves data relationships.

### Basic Tracing

```python
from snakecheck import traced_composite, integers
from snakecheck.trace import create_traceable_draw

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

# Generate with trace
result, trace = sequence_strategy.generate_with_trace()

# Analyze dependencies
x_deps = trace.get_variable_dependencies("x")
y_deps = trace.get_variable_dependencies("y")
z_deps = trace.get_variable_dependencies("z")

print(f"x dependencies: {x_deps}")
print(f"y dependencies: {y_deps}")
print(f"z dependencies: {z_deps}")
```

### Advanced Trace Analysis

```python
# Get dependency graph
dependency_graph = trace.get_dependency_graph()
reverse_deps = trace.get_reverse_dependencies()
components = trace.get_connected_components()

# Find what depends on a variable
dependents = trace.get_dependent_variables("x")

# Get all variables that depend on a given variable
dependencies = trace.get_variable_dependencies("z")
```

### Dataflow-Aware Shrinking

```python
from snakecheck.shrinking import shrink_with_dataflow

def test_sequence_property(data):
    """Test that fails when x is large and y is close to x."""
    x, y, z = data["x"], data["y"], data["z"]
    
    # This will fail when x is large and y is close to x
    if x > 50 and y > x * 0.8:
        raise ValueError(f"Invalid sequence: x={x}, y={y}, z={z}")
    
    return True

# Find a failing example and shrink it
result, trace = sequence_strategy.generate_with_trace()
try:
    test_sequence_property(result)
except Exception:
    # Shrink while preserving dataflow relationships
    shrunk_value, shrunk_trace = shrink_with_dataflow(trace, test_sequence_property)
    print(f"Shrunk from {result} to {shrunk_value}")
```

### Benefits of Dataflow-Aware Shrinking

1. **Preserves Relationships**: Shrinking maintains the logical connections between values
2. **Intelligent Reduction**: Understands which values can be reduced together
3. **Faster Debugging**: Smaller examples that still demonstrate the failure
4. **Better Insights**: Shows the minimal set of values needed to trigger the bug

### Use Cases

- **Complex Data Structures**: Trees, graphs, matrices with constraints
- **Business Logic**: Financial calculations, inventory management
- **API Testing**: Request/response sequences with dependencies
- **State Machines**: Workflows where actions depend on current state

## Advanced Features

### 1. The forall Function

For more control over test execution, use the `forall` function:

```python
from snakecheck import forall, integers

@forall(integers(-100, 100), integers(-100, 100), 
        max_examples=50, verbose=True, timeout=10.0)
def test_with_control(a: int, b: int):
    assert a + b == b + a
```

### 2. PropertyTest Class

For even more control, use the `PropertyTest` class directly:

```python
from snakecheck import PropertyTest, integers

test = PropertyTest(max_examples=200, timeout=30.0, seed=42)

@test.forall(integers(), integers())
def test_property(a: int, b: int):
    assert a + b == b + a
```

### 3. Shrinking

SnakeCheck automatically tries to find minimal failing examples:

```python
@given(integers(-1000, 1000))
def test_division_property(x: int):
    # This will fail for x = 0, and SnakeCheck will try to find that
    result = 100 / x
    assert result > 0
```

## Examples

See the `examples/` directory for comprehensive examples:

- **`basic_usage.py`** - Basic property testing with `@given`
- **`advanced_usage.py`** - Custom strategies and composition
- **`composite_usage.py`** - Composite strategy examples
- **`stateful_usage.py`** - Stateful testing with dependencies
- **`tracing_usage.py`** - Generation tracing and dependency analysis
- **`dataflow_shrinking.py`** - Dataflow-aware shrinking examples

## Configuration

You can configure SnakeCheck behavior globally or per-test:

```python
# Global configuration
@given(integers(), max_examples=500, seed=12345)

# Or use PropertyTest for more options
test = PropertyTest(
    max_examples=1000,
    timeout=60.0,
    seed=42,
    verbose=True
)
```

## Best Practices

1. **Write properties, not examples**: Focus on what should always be true
2. **Use appropriate strategies**: Choose strategies that generate valid data for your domain
3. **Keep tests fast**: Avoid expensive operations in property tests
4. **Use filtering wisely**: Filtered strategies can be slow if the predicate is rarely satisfied
5. **Test edge cases**: Property-based testing excels at finding edge cases automatically

## Comparison with Hypothesis

SnakeCheck is a simplified version of Hypothesis, designed for learning and simple use cases:

| Feature     | SnakeCheck | Hypothesis    |
| ----------- | ---------- | ------------- |
| Complexity  | Simple     | Advanced      |
| Performance | Basic      | Optimized     |
| Shrinking   | Basic      | Sophisticated |
| Database    | None       | Built-in      |
| Coverage    | Basic      | Advanced      |

## Contributing

Feel free to contribute improvements, bug fixes, or new features! Some areas that could use work:

- Better shrinking algorithms
- More sophisticated data generation
- Performance optimizations
- Additional strategy types
- Better error reporting

## License

This project is open source and available under the MIT License.

---

Happy testing! 🐍✨

## Testing

SnakeCheck supports two different testing approaches:

### 1. SnakeCheck Property Tests

Use SnakeCheck's `@given` decorator for property-based testing:

```python
from snakecheck import given, integers

@given(integers(), integers())
def test_addition_commutativity(a, b):
    assert a + b == b + a
```

**Run with**: `python3 examples/basic_usage.py`

### 2. Pytest Unit Tests

Use standard pytest for testing SnakeCheck's internal functionality:

```python
import pytest
from snakecheck.generators import integers

def test_integers_strategy():
    strategy = integers(-10, 10)
    value = strategy.generate()
    assert -10 <= value <= 10
```

**Run with**: `uv run pytest`

### Why Two Approaches?

- **SnakeCheck Tests**: Test your application logic with generated data
- **Pytest Tests**: Test SnakeCheck's internal functionality and ensure it works correctly

**Note**: Don't use `@given` decorators in pytest test files - they're not compatible with pytest's test discovery.

## Usage

### Running Examples

```bash
# Basic usage examples
python3 examples/basic_usage.py

# Advanced usage examples  
python3 examples/advanced_usage.py

# Composite strategy examples
python3 examples/composite_usage.py

# Stateful testing examples
python3 examples/stateful_usage.py
```

### Running Tests

```bash
# Run SnakeCheck's internal tests with pytest
uv run pytest

# Run specific test file
uv run pytest test_snakecheck_pytest.py

# Run with verbose output
uv run pytest -v
```
