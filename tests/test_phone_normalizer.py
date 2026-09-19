"""
Phone normalization tests for AL-RIFAI platform.
Tests the canonical Bangladeshi phone normalization logic.
Provenance: Fazle-Core phone_normalizer module
"""

def normalize_phone(raw: str) -> str:
    """Normalize Bangladeshi phone to +880XXXXXXXXX format."""
    digits = ''.join(c for c in raw if c.isdigit())
    if len(digits) == 11 and digits.startswith('0'):
        return '+88' + digits  # +880XXXXXXXXX
    elif len(digits) == 12 and digits.startswith('880'):
        return '+' + digits
    elif len(digits) == 13 and digits.startswith('+880'):
        return '+' + digits[1:]
    return raw


def test_normalize_with_leading_zero():
    assert normalize_phone("01712345678") == "+8801712345678"


def test_normalize_with_country_code():
    assert normalize_phone("8801712345678") == "+8801712345678"


def test_normalize_already_formatted():
    assert normalize_phone("+8801712345678") == "+8801712345678"


def test_preserves_raw():
    """Raw value preserved alongside normalized."""
    raw = "01712345678"
    assert normalize_phone(raw) == "+8801712345678"


def test_whitespace_stripped():
    assert normalize_phone(" 01712345678 ") == "+8801712345678"


def test_dashes_stripped():
    assert normalize_phone("017-1234-5678") == "+8801712345678"
