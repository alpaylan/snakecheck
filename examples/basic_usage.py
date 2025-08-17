"""
Basic usage examples for SnakeCheck property-based testing.
"""

from snakecheck import forall, given, integers, lists, strings


# Example 1: Simple property test with @given decorator
@given(integers(), integers())
def test_addition_commutative(a: int, b: int):
    """Test that addition is commutative: a + b = b + a"""
    assert a + b == b + a


# Example 2: Test with multiple strategies
@given(integers(0, 100), integers(0, 100))
def test_positive_addition(a: int, b: int):
    """Test that adding positive numbers gives a positive result"""
    result = a + b
    assert result >= a
    assert result >= b


# Example 3: String properties
@given(strings(min_length=1, max_length=10))
def test_string_length(s: str):
    """Test that string length is always positive for non-empty strings"""
    assert len(s) > 0
    assert len(s) <= 10


# Example 4: List properties
@given(lists(integers(), min_length=0, max_length=5))
def test_list_operations(nums: list):
    """Test basic list properties"""
    # Test that reversing twice gives the original list
    reversed_once = list(reversed(nums))
    reversed_twice = list(reversed(reversed_once))
    assert reversed_twice == nums

    # Test that sorting is idempotent
    sorted_once = sorted(nums)
    sorted_twice = sorted(sorted_once)
    assert sorted_once == sorted_twice


# Example 5: Using forall for more control
@forall(integers(-100, 100), integers(-100, 100), max_examples=50, verbose=True)
def test_multiplication_distributive(a: int, b: int):
    """Test that multiplication distributes over addition: a * (b + c) = a*b + a*c"""
    c = a  # Use a as c for simplicity
    left = a * (b + c)
    right = a * b + a * c
    assert left == right


# Example 6: Custom strategy with filtering
positive_integers = integers(1, 1000)


@given(positive_integers, positive_integers)
def test_positive_division(a: int, b: int):
    """Test division with positive integers"""
    result = a / b
    assert result > 0
    assert result * b == a


if __name__ == "__main__":
    print("Running SnakeCheck examples...")
    print("=" * 50)

    try:
        print("1. Testing addition commutativity...")
        test_addition_commutative()
        print("   ✓ Passed!")

        print("\n2. Testing positive addition...")
        test_positive_addition()
        print("   ✓ Passed!")

        print("\n3. Testing string length properties...")
        test_string_length()
        print("   ✓ Passed!")

        print("\n4. Testing list operations...")
        test_list_operations()
        print("   ✓ Passed!")

        print("\n5. Testing multiplication distributivity...")
        test_multiplication_distributive()
        print("   ✓ Passed!")

        print("\n6. Testing positive division...")
        test_positive_division()
        print("   ✓ Passed!")

        print("\n" + "=" * 50)
        print("All tests passed! 🎉")

    except Exception as e:
        print(f"\nTest failed: {e}")
        print("This demonstrates SnakeCheck's ability to find failing examples!")
