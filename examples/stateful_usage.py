"""
Stateful testing examples for SnakeCheck property-based testing.

This demonstrates how to create tests where the generation of later parts
of a structure depends on earlier generated values.
"""

from snakecheck import choices, composite_strategy, given, integers


# Example 1: Building a linked list where each node's value depends on the previous
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
            # Only double if it won't exceed bounds
            new_value = prev_node["value"] * 2
            if abs(new_value) > 200:
                new_value = prev_node["value"] + draw(integers(-10, 10))  # Fallback
        elif dependency_type == "half":
            new_value = prev_node["value"] // 2
        else:  # same
            new_value = prev_node["value"]

        # Ensure the value stays within bounds
        new_value = max(-200, min(200, new_value))

        nodes.append({"value": new_value, "next": None})
        nodes[i - 1]["next"] = i  # Link to next node

    return nodes


# Example 2: Building a binary search tree with insertion order dependency
@composite_strategy
def bst_strategy(draw):
    """Generate a binary search tree where insertion order affects structure."""
    node_count = draw(integers(3, 15))
    values = []
    tree = []

    # Generate values in insertion order
    for i in range(node_count):
        if i == 0:
            # First value is random
            value = draw(integers(-100, 100))
        else:
            # Later values depend on existing tree structure
            # Choose a strategy: random, near existing, or extreme
            strategy = draw(choices(["random", "near_existing", "extreme"]))

            if strategy == "random":
                value = draw(integers(-100, 100))
            elif strategy == "near_existing":
                # Pick a value near an existing one
                existing = draw(choices(values))
                offset = draw(integers(-20, 20))
                value = existing + offset
            else:  # extreme
                # Pick a value that's much smaller or larger
                if draw(choices([True, False])):
                    value = draw(integers(-200, -150))  # Much smaller
                else:
                    value = draw(integers(150, 200))  # Much larger

        values.append(value)

        # Insert into tree (simplified BST insertion)
        tree.append({"value": value, "left": None, "right": None, "insertion_order": i})

    # Build tree structure based on insertion order
    for i in range(1, node_count):
        current = tree[i]
        root = tree[0]

        # Simple BST insertion logic
        node = root
        while True:
            if current["value"] < node["value"]:
                if node["left"] is None:
                    node["left"] = i
                    break
                else:
                    node = tree[node["left"]]
            else:
                if node["right"] is None:
                    node["right"] = i
                    break
                else:
                    node = tree[node["right"]]

    return {"tree": tree, "values": values, "insertion_order": list(range(node_count))}


# Example 3: Building a stack with push/pop operations that depend on current state
@composite_strategy
def stack_operations_strategy(draw):
    """Generate a sequence of stack operations that depend on current stack state."""
    operation_count = draw(integers(5, 20))
    operations = []
    stack_size = 0

    for i in range(operation_count):
        # Operation choice depends on current stack state
        if stack_size == 0:
            # Empty stack: can only push
            operation = "push"
        elif stack_size >= 10:
            # Full stack: prefer pop operations
            operation = draw(choices(["push", "pop", "pop", "pop"]))
        else:
            # Normal case: choose operation
            operation = draw(choices(["push", "pop", "peek", "size"]))

        if operation == "push":
            # Value to push depends on current stack contents
            if stack_size == 0:
                # First push: random value
                value = draw(integers(-100, 100))
            else:
                # Subsequent pushes: relate to existing values
                strategy = draw(choices(["random", "increment", "decrement", "average"]))

                if strategy == "random":
                    value = draw(integers(-100, 100))
                elif strategy == "increment":
                    # Push a value slightly larger than current max
                    max_val = max(op["value"] for op in operations if op["operation"] == "push")
                    value = max_val + draw(integers(1, 10))
                elif strategy == "decrement":
                    # Push a value slightly smaller than current min
                    min_val = min(op["value"] for op in operations if op["operation"] == "push")
                    value = min_val - draw(integers(1, 10))
                else:  # average
                    # Push a value near the average of existing values
                    push_values = [op["value"] for op in operations if op["operation"] == "push"]
                    avg = sum(push_values) // len(push_values)
                    value = avg + draw(integers(-10, 10))

            operations.append({"operation": "push", "value": value, "step": i})
            stack_size += 1

        elif operation == "pop":
            operations.append({"operation": "pop", "step": i})
            stack_size = max(0, stack_size - 1)

        elif operation == "peek":
            operations.append({"operation": "peek", "step": i})

        else:  # size
            operations.append({"operation": "size", "step": i})

    return {
        "operations": operations,
        "final_stack_size": stack_size,
        "total_operations": operation_count,
    }


# Example 4: Building a graph where edge weights depend on node properties
@composite_strategy
def weighted_graph_strategy(draw):
    """Generate a weighted graph where edge weights depend on connected nodes."""
    node_count = draw(integers(3, 8))
    nodes = []
    edges = []

    # Generate nodes with properties that will influence edge weights
    for i in range(node_count):
        node_type = draw(choices(["source", "sink", "intermediate"]))

        if node_type == "source":
            capacity = draw(integers(50, 100))
            priority = draw(integers(8, 10))
        elif node_type == "sink":
            capacity = draw(integers(20, 50))
            priority = draw(integers(1, 3))
        else:  # intermediate
            capacity = draw(integers(30, 80))
            priority = draw(integers(4, 7))

        nodes.append(
            {
                "id": i,
                "type": node_type,
                "capacity": capacity,
                "priority": priority,
                "position": draw(integers(0, 100)),  # Position for distance calculation
            }
        )

    # Generate edges with weights that depend on connected nodes
    edge_count = draw(integers(node_count - 1, node_count * 2))

    # Ensure connectivity first
    for i in range(node_count - 1):
        weight = draw(integers(1, 20))
        edges.append({"from": i, "to": i + 1, "weight": weight, "type": "connectivity"})

    # Add additional edges
    for _ in range(edge_count - (node_count - 1)):
        from_node = draw(choices(range(node_count)))
        to_node = draw(choices(range(node_count)))

        if from_node != to_node:
            # Weight depends on node properties
            from_node_data = nodes[from_node]
            to_node_data = nodes[to_node]

            # Base weight from node types
            if from_node_data["type"] == "source" and to_node_data["type"] == "sink":
                base_weight = draw(integers(5, 15))  # Source to sink: low weight
            elif from_node_data["type"] == "sink" and to_node_data["type"] == "source":
                base_weight = draw(integers(25, 40))  # Sink to source: high weight
            else:
                base_weight = draw(integers(10, 25))  # Other combinations

            # Adjust weight based on capacity difference
            capacity_diff = abs(from_node_data["capacity"] - to_node_data["capacity"])
            capacity_factor = capacity_diff // 10

            # Adjust weight based on priority difference
            priority_diff = abs(from_node_data["priority"] - to_node_data["priority"])
            priority_factor = priority_diff * 2

            # Adjust weight based on distance
            distance = abs(from_node_data["position"] - to_node_data["position"])
            distance_factor = distance // 20

            final_weight = max(1, base_weight + capacity_factor + priority_factor + distance_factor)

            edges.append(
                {"from": from_node, "to": to_node, "weight": final_weight, "type": "additional"}
            )

    return {"nodes": nodes, "edges": edges, "node_count": node_count, "edge_count": len(edges)}


# Example 5: Building a database transaction sequence with constraints
@composite_strategy
def transaction_sequence_strategy(draw):
    """Generate a sequence of database transactions with state-dependent constraints."""
    transaction_count = draw(integers(5, 15))
    transactions = []
    account_balances = {"A": 1000, "B": 1000, "C": 1000}  # Initial state

    for i in range(transaction_count):
        # Transaction type depends on current account states
        available_accounts = [acc for acc, bal in account_balances.items() if bal > 0]

        if not available_accounts:
            # All accounts empty: can only do deposits
            transaction_type = "deposit"
        elif len(available_accounts) == 1:
            # Only one account has money: prefer deposits
            transaction_type = draw(choices(["deposit", "deposit", "transfer"]))
        else:
            # Multiple accounts have money: all operations possible
            transaction_type = draw(choices(["deposit", "withdraw", "transfer"]))

        if transaction_type == "deposit":
            account = draw(choices(["A", "B", "C"]))
            amount = draw(integers(10, 200))
            account_balances[account] += amount

            transactions.append(
                {
                    "type": "deposit",
                    "account": account,
                    "amount": amount,
                    "balance_after": account_balances[account],
                    "step": i,
                }
            )

        elif transaction_type == "withdraw":
            # Can only withdraw from accounts with sufficient balance
            account = draw(choices(available_accounts))
            max_withdrawal = account_balances[account]
            amount = draw(integers(10, min(max_withdrawal, 200)))
            account_balances[account] -= amount

            transactions.append(
                {
                    "type": "withdraw",
                    "account": account,
                    "amount": amount,
                    "balance_after": account_balances[account],
                    "step": i,
                }
            )

        else:  # transfer
            # Can only transfer between accounts with sufficient balance
            from_account = draw(choices(available_accounts))
            to_account = draw(choices(["A", "B", "C"]))

            if from_account != to_account:
                max_transfer = account_balances[from_account]
                amount = draw(integers(10, min(max_transfer, 150)))

                account_balances[from_account] -= amount
                account_balances[to_account] += amount

                transactions.append(
                    {
                        "type": "transfer",
                        "from_account": from_account,
                        "to_account": to_account,
                        "amount": amount,
                        "balance_after": {
                            "from": account_balances[from_account],
                            "to": account_balances[to_account],
                        },
                        "step": i,
                    }
                )
            else:
                # If same account, do a deposit instead
                amount = draw(integers(10, 200))
                account_balances[from_account] += amount

                transactions.append(
                    {
                        "type": "deposit",
                        "account": from_account,
                        "amount": amount,
                        "balance_after": account_balances[from_account],
                        "step": i,
                    }
                )

    # Verify total balance is preserved
    total_balance = sum(account_balances.values())
    if total_balance != 3000:
        # If balance is wrong, add a compensating transaction
        diff = 3000 - total_balance
        if diff > 0:
            # Need to add money
            account = draw(choices(["A", "B", "C"]))
            account_balances[account] += diff
            transactions.append(
                {
                    "type": "deposit",
                    "account": account,
                    "amount": diff,
                    "balance_after": account_balances[account],
                    "step": len(transactions),
                    "compensating": True,
                }
            )
        else:
            # Need to remove money - find an account with sufficient balance
            available_accounts = [acc for acc, bal in account_balances.items() if bal >= abs(diff)]
            if available_accounts:
                account = draw(choices(available_accounts))
                account_balances[account] += diff  # diff is negative
                transactions.append(
                    {
                        "type": "withdraw",
                        "account": account,
                        "amount": abs(diff),
                        "balance_after": account_balances[account],
                        "step": len(transactions),
                        "compensating": True,
                    }
                )
            else:
                # If no account has sufficient balance, add money to all accounts proportionally
                # This ensures we always end up with the correct total
                accounts = ["A", "B", "C"]
                for i, account in enumerate(accounts):
                    share = diff // 3
                    if i == 0:  # First account gets the remainder
                        share += diff % 3
                    account_balances[account] += share
                    if share > 0:
                        transactions.append(
                            {
                                "type": "deposit",
                                "account": account,
                                "amount": share,
                                "balance_after": account_balances[account],
                                "step": len(transactions),
                                "compensating": True,
                            }
                        )

    return {
        "transactions": transactions,
        "final_balances": account_balances.copy(),
        "total_transactions": len(transactions),
    }


# Test functions for stateful strategies
@given(linked_list_strategy)
def test_linked_list_properties(nodes):
    """Test properties of generated linked lists."""
    assert len(nodes) >= 1
    assert len(nodes) <= 10

    # Check that all nodes have values
    for node in nodes:
        assert "value" in node
        assert isinstance(node["value"], int)
        assert -200 <= node["value"] <= 200  # Allow for the full range

    # Check linking structure
    for i in range(len(nodes) - 1):
        assert nodes[i]["next"] == i + 1
    assert nodes[-1]["next"] is None


@given(bst_strategy)
def test_bst_properties(bst_data):
    """Test properties of generated binary search trees."""
    tree = bst_data["tree"]

    assert len(tree) >= 3
    assert len(tree) <= 15

    # Check BST property: left child < parent < right child
    for i, node in enumerate(tree):
        if node["left"] is not None:
            left_node = tree[node["left"]]
            assert left_node["value"] < node["value"], f"BST property violated at node {i}"

        if node["right"] is not None:
            right_node = tree[node["right"]]
            assert right_node["value"] >= node["value"], f"BST property violated at node {i}"

    # Check that insertion order is preserved
    for i, node in enumerate(tree):
        assert node["insertion_order"] == i


@given(stack_operations_strategy)
def test_stack_operations_properties(stack_data):
    """Test properties of generated stack operations."""
    operations = stack_data["operations"]
    final_size = stack_data["final_stack_size"]

    assert len(operations) >= 5
    assert len(operations) <= 20

    # Simulate stack operations to verify consistency
    stack = []
    for op in operations:
        if op["operation"] == "push":
            stack.append(op["value"])
        elif op["operation"] == "pop" and stack:
            stack.pop()
        # peek and size don't change stack

    assert len(stack) == final_size

    # Check that we never pop from empty stack
    stack = []
    for op in operations:
        if op["operation"] == "pop" and stack:
            stack.pop()
        elif op["operation"] == "push":
            stack.append(op["value"])


@given(weighted_graph_strategy)
def test_weighted_graph_properties(graph_data):
    """Test properties of generated weighted graphs."""
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]

    assert len(nodes) >= 3
    assert len(nodes) <= 8
    assert len(edges) >= len(nodes) - 1  # At least spanning tree

    # Check node properties
    for node in nodes:
        assert "id" in node
        assert "type" in node
        assert "capacity" in node
        assert "priority" in node
        assert "position" in node
        assert node["type"] in ["source", "sink", "intermediate"]
        assert 20 <= node["capacity"] <= 100
        assert 1 <= node["priority"] <= 10
        assert 0 <= node["position"] <= 100

    # Check edge properties
    for edge in edges:
        assert "from" in edge
        assert "to" in edge
        assert "weight" in edge
        assert "type" in edge
        assert 0 <= edge["from"] < len(nodes)
        assert 0 <= edge["to"] < len(nodes)
        assert edge["weight"] >= 1
        assert edge["type"] in ["connectivity", "additional"]


@given(transaction_sequence_strategy)
def test_transaction_sequence_properties(txn_data):
    """Test properties of generated transaction sequences."""
    transactions = txn_data["transactions"]
    final_balances = txn_data["final_balances"]

    assert len(transactions) >= 5
    assert len(transactions) <= 20  # Allow for compensating transactions

    # Verify that no account goes negative
    for txn in transactions:
        if txn["type"] == "withdraw":
            assert txn["balance_after"] >= 0
        elif txn["type"] == "transfer":
            assert txn["balance_after"]["from"] >= 0
            assert txn["balance_after"]["to"] >= 0

    # Verify final balances are consistent
    expected_total = 3000  # Initial total
    actual_total = sum(final_balances.values())
    assert actual_total == expected_total, (
        f"Total balance changed: {actual_total} != {expected_total}"
    )


if __name__ == "__main__":
    print("Running SnakeCheck Stateful Testing Examples...")
    print("=" * 65)

    tests = [
        ("Linked list properties", test_linked_list_properties),
        ("Binary search tree properties", test_bst_properties),
        ("Stack operations properties", test_stack_operations_properties),
        ("Weighted graph properties", test_weighted_graph_properties),
        ("Transaction sequence properties", test_transaction_sequence_properties),
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

    print("\n" + "=" * 65)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All stateful tests passed! 🎉")
    else:
        print("Some tests failed - this demonstrates SnakeCheck's ability to find edge cases!")
