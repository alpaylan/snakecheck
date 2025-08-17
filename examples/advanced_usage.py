"""
Advanced usage examples for SnakeCheck property-based testing.
"""

import random

from snakecheck import Strategy, choices, given, integers, strings


# Example 1: Custom strategy for email addresses
class EmailStrategy(Strategy[str]):
    """Generate simple email-like strings for testing."""

    def generate(self) -> str:
        username = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
        domain = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=6))
        return f"{username}@{domain}.com"


# Example 2: Custom strategy for sorted lists
class SortedListStrategy(Strategy[list[int]]):
    """Generate sorted lists of integers."""

    def __init__(self, min_length: int = 0, max_length: int = 10):
        super().__init__()
        self.min_length = min_length
        self.max_length = max_length

    def generate(self) -> list[int]:
        length = integers(self.min_length, self.max_length).generate()
        nums = [integers(-100, 100).generate() for _ in range(length)]
        return sorted(nums)


# Example 3: Strategy for valid Python identifiers
class IdentifierStrategy(Strategy[str]):
    """Generate valid Python identifiers."""

    def generate(self) -> str:
        # Start with letter or underscore
        first_char = random.choice("abcdefghijklmnopqrstuvwxyz_")
        # Rest can be letters, digits, or underscores
        rest_chars = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789_", k=7))
        return first_char + rest_chars


# Example 4: Test email validation (this will fail!)
@given(EmailStrategy())
def test_email_validation(email: str):
    """Test that all generated emails are valid (this will fail by design)."""
    # This is intentionally wrong to demonstrate failure detection
    assert "@" in email
    assert "." in email
    assert len(email) > 10
    # This will fail for some generated emails
    assert email.count("@") == 1


# Example 5: Test sorted list properties
@given(SortedListStrategy(min_length=1, max_length=20))
def test_sorted_list_properties(nums: list[int]):
    """Test properties of sorted lists."""
    # Test that list is actually sorted
    for i in range(len(nums) - 1):
        assert nums[i] <= nums[i + 1]

    # Test that sorting again doesn't change anything
    assert sorted(nums) == nums

    # Test that reversing and sorting gives the same result
    reversed_nums = list(reversed(nums))
    assert sorted(reversed_nums) == nums


# Example 6: Test binary search implementation
def binary_search(arr: list[int], target: int) -> int:
    """Simple binary search implementation (has a bug for edge cases)."""
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1


@given(SortedListStrategy(min_length=1, max_length=50), integers(-100, 100))
def test_binary_search_properties(arr: list[int], target: int):
    """Test properties of binary search."""
    result = binary_search(arr, target)

    if result != -1:
        # If found, verify it's correct
        assert 0 <= result < len(arr)
        assert arr[result] == target
    else:
        # If not found, verify it's really not in the array
        assert target not in arr


# Example 7: Test with filtered strategies
positive_evens = integers(2, 100).filter(lambda x: x % 2 == 0)


@given(positive_evens, positive_evens)
def test_even_number_properties(a: int, b: int):
    """Test properties of even numbers."""
    assert a % 2 == 0
    assert b % 2 == 0
    assert (a + b) % 2 == 0
    assert (a * b) % 2 == 0


# Example 8: Test string concatenation properties
@given(strings(min_length=1, max_length=20), strings(min_length=1, max_length=20))
def test_string_concatenation(s1: str, s2: str):
    """Test string concatenation properties."""
    combined = s1 + s2

    # Length should be sum of individual lengths
    assert len(combined) == len(s1) + len(s2)

    # Should start with first string
    assert combined.startswith(s1)

    # Should end with second string
    assert combined.endswith(s2)

    # Should contain both strings
    assert s1 in combined
    assert s2 in combined


# Example 9: Test with mapped strategies
doubled_integers = integers(-50, 50).map(lambda x: x * 2)


@given(doubled_integers)
def test_doubled_integer_properties(x: int):
    """Test properties of doubled integers."""
    assert x % 2 == 0  # All doubled integers are even
    assert x >= -100 and x <= 100  # Range constraints


# Example 10: Complex property test with multiple strategies
@given(SortedListStrategy(min_length=0, max_length=10), integers(-100, 100), choices([True, False]))
def test_list_insertion_properties(arr: list[int], value: int, at_end: bool):
    """Test properties of list insertion."""
    original_length = len(arr)

    if at_end:
        arr.append(value)
        assert len(arr) == original_length + 1
        assert arr[-1] == value
    else:
        arr.insert(0, value)
        assert len(arr) == original_length + 1
        assert arr[0] == value

    # Value should be in the list
    assert value in arr

    # Length should have increased by 1
    assert len(arr) == original_length + 1


if __name__ == "__main__":
    print("Running Advanced SnakeCheck examples...")
    print("=" * 60)

    tests = [
        ("Email validation (will fail)", test_email_validation),
        ("Sorted list properties", test_sorted_list_properties),
        ("Binary search properties", test_binary_search_properties),
        ("Even number properties", test_even_number_properties),
        ("String concatenation", test_string_concatenation),
        ("Doubled integer properties", test_doubled_integer_properties),
        ("List insertion properties", test_list_insertion_properties),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            test_func()
            print("   ✓ Passed!")
            passed += 1
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All tests passed! 🎉")
    else:
        print("Some tests failed - this demonstrates SnakeCheck's ability to find edge cases!")
