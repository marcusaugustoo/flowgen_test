def check(candidate):
    # Basic anagrams
    assert candidate("listen", "silent") == True
    assert candidate("triangle", "integral") == True
    # Not anagrams
    assert candidate("hello", "world") == False
    assert candidate("abc", "abcd") == False
    # Case insensitive
    assert candidate("Listen", "Silent") == True
    assert candidate("ABC", "cba") == True
    # Spaces ignored
    assert candidate("astronomer", "moon starer") == True
    assert candidate("the eyes", "they see") == True
    # Empty strings
    assert candidate("", "") == True
    # Single character
    assert candidate("a", "a") == True
    assert candidate("a", "b") == False
    # Different lengths (after removing spaces)
    assert candidate("ab", "abc") == False
    # Same characters different counts
    assert candidate("aab", "abb") == False

check(is_anagram)
