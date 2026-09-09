def check(candidate):
    # Basic frequency grouping with strings
    result = candidate(["a", "b", "a", "c", "b", "a"])
    assert result == {3: ["a"], 2: ["b"], 1: ["c"]}
    # With integers
    assert candidate([1, 1, 2, 2, 3]) == {2: [1, 2], 1: [3]}
    # Empty list
    assert candidate([]) == {}
    # All same frequency
    assert candidate([1, 2, 3]) == {1: [1, 2, 3]}
    # All same element
    assert candidate(["x", "x", "x"]) == {3: ["x"]}
    # Single element
    assert candidate([42]) == {1: [42]}
    # Preserves first-appearance order
    result = candidate(["c", "a", "b", "a", "c"])
    assert result == {2: ["c", "a"], 1: ["b"]}
    # Mixed types should work independently
    assert candidate([1, "a", 1, "a", 2]) == {2: [1, "a"], 1: [2]}
    # Larger example
    result = candidate([5, 5, 5, 3, 3, 1])
    assert result == {3: [5], 2: [3], 1: [1]}

check(group_by_frequency)
