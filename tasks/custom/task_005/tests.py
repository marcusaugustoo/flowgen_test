def check(candidate):
    # Simple flat list
    assert candidate([1, 2, 3]) == [1, 2, 3]
    # One level of nesting
    assert candidate([1, [2, 3], 4]) == [1, 2, 3, 4]
    # Deep nesting
    assert candidate([1, [2, [3, [4, [5]]]]]) == [1, 2, 3, 4, 5]
    # Mixed nesting levels
    assert candidate([1, [2, 3], [4, [5, 6]]]) == [1, 2, 3, 4, 5, 6]
    # Empty list
    assert candidate([]) == []
    # Nested empty lists
    assert candidate([[[], []], []]) == []
    # Mixed types preserved
    assert candidate([1, "hello", [None, [True]]]) == [1, "hello", None, True]
    # Strings are NOT iterated (not flattened into characters)
    assert candidate(["abc", ["def"]]) == ["abc", "def"]
    # Single element
    assert candidate([42]) == [42]
    # Single nested element
    assert candidate([[42]]) == [42]
    # Complex mixed
    assert candidate([1, [2], [[3]], [[[4]]]]) == [1, 2, 3, 4]
    # Large flat list
    assert candidate(list(range(10))) == list(range(10))
    # Zeros and negative numbers
    assert candidate([0, [-1, [-2]], 3]) == [0, -1, -2, 3]

check(flatten_nested)
