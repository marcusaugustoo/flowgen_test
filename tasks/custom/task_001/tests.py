def check(candidate):
    # Basic merge
    assert candidate([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]
    # Empty first array
    assert candidate([], [1, 2, 3]) == [1, 2, 3]
    # Empty second array
    assert candidate([1, 2, 3], []) == [1, 2, 3]
    # Both empty
    assert candidate([], []) == []
    # Single elements
    assert candidate([1], [2]) == [1, 2]
    assert candidate([2], [1]) == [1, 2]
    # Duplicates across arrays
    assert candidate([1, 3, 5], [1, 3, 5]) == [1, 1, 3, 3, 5, 5]
    # Different lengths
    assert candidate([1], [2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    # Negative numbers
    assert candidate([-5, -1, 0], [-3, 2, 4]) == [-5, -3, -1, 0, 2, 4]
    # Already interleaved
    assert candidate([1, 2, 3], [4, 5, 6]) == [1, 2, 3, 4, 5, 6]

check(merge_sorted_arrays)
