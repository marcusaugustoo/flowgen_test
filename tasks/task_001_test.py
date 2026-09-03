def check(candidate):
    assert candidate(2) == True
    assert candidate(3) == True
    assert candidate(4) == False
    assert candidate(5) == True
    assert candidate(1) == False
    assert candidate(0) == False
    assert candidate(17) == True
    assert candidate(20) == False
    assert candidate(97) == True

check(is_prime)
