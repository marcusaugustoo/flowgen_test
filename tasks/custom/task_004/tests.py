import math

def check(candidate):
    # Normal division
    assert candidate(10, 2) == 5.0
    assert candidate(7, 2) == 3.5
    assert candidate(-10, 2) == -5.0
    # Division by zero returns default
    assert candidate(10, 0) is None
    assert candidate(10, 0, default=-1) == -1
    assert candidate(0, 0) is None
    assert candidate(0, 0, default=0) == 0
    # None arguments return default
    assert candidate(None, 5) is None
    assert candidate(5, None) is None
    assert candidate(None, None) is None
    assert candidate(None, 5, default=0) == 0
    # Type checking
    try:
        candidate("10", 5)
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "numeric" in str(e).lower()
    try:
        candidate(10, "5")
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "numeric" in str(e).lower()
    try:
        candidate([1], 5)
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
    # Float results
    assert isinstance(candidate(10, 3), float)
    # Infinity handling
    assert candidate(float('inf'), 2) == float('inf')
    assert candidate(10, float('inf')) == 0.0
    # NaN handling
    assert math.isnan(candidate(float('nan'), 2))
    # Zero divided by non-zero
    assert candidate(0, 5) == 0.0

check(safe_divide)
