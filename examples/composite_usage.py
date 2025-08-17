"""
Composite strategy examples for SnakeCheck property-based testing.

This demonstrates how to compose complex data types by drawing from multiple
strategies within a single test function.
"""

from snakecheck import composite, composite_strategy, given, integers, strings


# Example 1: Simple composite strategy using the composite() function
def point_strategy(draw):
    """Generate a 2D point by drawing x and y coordinates."""
    x = draw(integers(-100, 100))
    y = draw(integers(-100, 100))
    return {"x": x, "y": y}


# Example 2: Composite strategy using the decorator syntax
@composite_strategy
def user_strategy(draw):
    """Generate a user by drawing name, age, and email."""
    name = draw(strings(min_length=1, max_length=50))
    age = draw(integers(0, 120))
    email = draw(strings(min_length=5, max_length=100))
    return {"name": name, "age": age, "email": email}


# Example 3: Composite strategy for a rectangle
@composite_strategy
def rectangle_strategy(draw):
    """Generate a rectangle by drawing width and height."""
    width = draw(integers(1, 100))
    height = draw(integers(1, 100))
    return {"width": width, "height": height, "area": width * height}


# Example 4: Composite strategy for a list of users
@composite_strategy
def user_list_strategy(draw):
    """Generate a list of users."""
    count = draw(integers(0, 5))
    users = []
    for _ in range(count):
        users.append(user_strategy.generate())
    return users


# Example 5: Nested composite strategies
@composite_strategy
def complex_shape_strategy(draw):
    """Generate a complex shape with multiple properties."""
    shape_type = draw(integers(0, 2))  # 0=circle, 1=rectangle, 2=triangle

    if shape_type == 0:  # Circle
        radius = draw(integers(1, 50))
        return {
            "type": "circle",
            "radius": radius,
            "area": 3.14159 * radius * radius,
            "perimeter": 2 * 3.14159 * radius,
        }
    elif shape_type == 1:  # Rectangle
        rect = draw(rectangle_strategy)
        return {
            "type": "rectangle",
            "width": rect["width"],
            "height": rect["height"],
            "area": rect["area"],
            "perimeter": 2 * (rect["width"] + rect["height"]),
        }
    else:  # Triangle
        a = draw(integers(1, 50))
        b = draw(integers(1, 50))
        c = draw(integers(1, 50))
        # Ensure triangle inequality
        if a + b > c and a + c > b and b + c > a:
            return {"type": "triangle", "sides": [a, b, c], "perimeter": a + b + c}
        else:
            # Fallback to valid triangle
            return {"type": "triangle", "sides": [3, 4, 5], "perimeter": 12}


# Example 6: Composite strategy with filtering
@composite_strategy
def valid_triangle_strategy(draw):
    """Generate a valid triangle that satisfies triangle inequality."""
    while True:
        a = draw(integers(1, 50))
        b = draw(integers(1, 50))
        c = draw(integers(1, 50))

        # Check triangle inequality
        if a + b > c and a + c > b and b + c > a:
            return {"a": a, "b": b, "c": c}


# Example 7: Composite strategy for a binary tree node
@composite_strategy
def binary_tree_strategy(draw):
    """Generate a binary tree node structure with limited depth."""
    value = draw(integers(-100, 100))

    # Simple approach: just generate leaf nodes for now
    # This avoids recursion issues while still demonstrating the concept
    return {"value": value, "left": None, "right": None}


# Alternative: Generate a list of tree nodes that can be assembled later
@composite_strategy
def tree_node_list_strategy(draw):
    """Generate a list of tree nodes that can be assembled into a tree."""
    node_count = draw(integers(1, 10))
    nodes = []

    for i in range(node_count):
        value = draw(integers(-100, 100))
        nodes.append(
            {
                "id": i,
                "value": value,
                "left_child": draw(integers(-1, node_count - 1)) if i < node_count - 1 else -1,
                "right_child": draw(integers(-1, node_count - 1)) if i < node_count - 1 else -1,
            }
        )

    return nodes


# Example 8: Composite strategy for a shopping cart
@composite_strategy
def shopping_cart_strategy(draw):
    """Generate a shopping cart with items."""
    item_count = draw(integers(0, 10))
    items = []
    total = 0

    for _ in range(item_count):
        name = draw(strings(min_length=3, max_length=20))
        price = draw(integers(1, 1000))
        quantity = draw(integers(1, 5))

        item = {"name": name, "price": price, "quantity": quantity, "subtotal": price * quantity}
        items.append(item)
        total += item["subtotal"]

    return {"items": items, "item_count": item_count, "total": total}


# Test functions using composite strategies
@given(composite(point_strategy))
def test_point_properties(point):
    """Test properties of generated points."""
    assert "x" in point
    assert "y" in point
    assert isinstance(point["x"], int)
    assert isinstance(point["y"], int)
    assert -100 <= point["x"] <= 100
    assert -100 <= point["y"] <= 100


@given(user_strategy)
def test_user_properties(user):
    """Test properties of generated users."""
    assert "name" in user
    assert "age" in user
    assert "email" in user
    assert isinstance(user["name"], str)
    assert isinstance(user["age"], int)
    assert isinstance(user["email"], str)
    assert 1 <= len(user["name"]) <= 50
    assert 0 <= user["age"] <= 120
    assert 5 <= len(user["email"]) <= 100


@given(rectangle_strategy)
def test_rectangle_properties(rect):
    """Test properties of generated rectangles."""
    assert "width" in rect
    assert "height" in rect
    assert "area" in rect
    assert rect["width"] > 0
    assert rect["height"] > 0
    assert rect["area"] == rect["width"] * rect["height"]


@given(user_list_strategy)
def test_user_list_properties(users):
    """Test properties of generated user lists."""
    assert isinstance(users, list)
    assert len(users) <= 5
    for user in users:
        assert "name" in user
        assert "age" in user
        assert "email" in user


@given(complex_shape_strategy)
def test_complex_shape_properties(shape):
    """Test properties of generated complex shapes."""
    assert "type" in shape
    assert shape["type"] in ["circle", "rectangle", "triangle"]

    if shape["type"] == "circle":
        assert "radius" in shape
        assert "area" in shape
        assert "perimeter" in shape
        assert shape["radius"] > 0
    elif shape["type"] == "rectangle":
        assert "width" in shape
        assert "height" in shape
        assert "area" in shape
        assert "perimeter" in shape
        assert shape["width"] > 0
        assert shape["height"] > 0
    else:  # triangle
        assert "sides" in shape
        assert "perimeter" in shape
        assert len(shape["sides"]) == 3


@given(valid_triangle_strategy)
def test_valid_triangle_properties(triangle):
    """Test properties of generated valid triangles."""
    a, b, c = triangle["a"], triangle["b"], triangle["c"]
    assert a + b > c
    assert a + c > b
    assert b + c > a
    assert a > 0 and b > 0 and c > 0


@given(binary_tree_strategy)
def test_binary_tree_properties(node):
    """Test properties of generated binary tree nodes."""
    assert "value" in node
    assert isinstance(node["value"], int)
    assert -100 <= node["value"] <= 100
    assert node["left"] is None
    assert node["right"] is None


@given(tree_node_list_strategy)
def test_tree_node_list_properties(nodes):
    """Test properties of generated tree node lists."""
    assert isinstance(nodes, list)
    assert 1 <= len(nodes) <= 10

    for i, node in enumerate(nodes):
        assert "id" in node
        assert "value" in node
        assert "left_child" in node
        assert "right_child" in node
        assert node["id"] == i
        assert isinstance(node["value"], int)
        assert -100 <= node["value"] <= 100
        assert isinstance(node["left_child"], int)
        assert isinstance(node["right_child"], int)
        assert -1 <= node["left_child"] < len(nodes)
        assert -1 <= node["right_child"] < len(nodes)


@given(shopping_cart_strategy)
def test_shopping_cart_properties(cart):
    """Test properties of generated shopping carts."""
    assert "items" in cart
    assert "item_count" in cart
    assert "total" in cart
    assert isinstance(cart["items"], list)
    assert len(cart["items"]) == cart["item_count"]

    calculated_total = sum(item["subtotal"] for item in cart["items"])
    assert cart["total"] == calculated_total

    for item in cart["items"]:
        assert "name" in item
        assert "price" in item
        assert "quantity" in item
        assert "subtotal" in item
        assert item["subtotal"] == item["price"] * item["quantity"]


if __name__ == "__main__":
    print("Running SnakeCheck Composite Examples...")
    print("=" * 60)

    tests = [
        ("Point properties", test_point_properties),
        ("User properties", test_user_properties),
        ("Rectangle properties", test_rectangle_properties),
        ("User list properties", test_user_list_properties),
        ("Complex shape properties", test_complex_shape_properties),
        ("Valid triangle properties", test_valid_triangle_properties),
        ("Binary tree properties", test_binary_tree_properties),
        ("Tree node list properties", test_tree_node_list_properties),
        ("Shopping cart properties", test_shopping_cart_properties),
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
        print("All composite tests passed! 🎉")
    else:
        print("Some tests failed - this demonstrates SnakeCheck's ability to find edge cases!")
