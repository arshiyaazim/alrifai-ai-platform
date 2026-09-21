"""
Phone normalization tests for AL-RIFAI platform.
Tests the canonical Bangladeshi phone normalization logic.
Provenance: Fazle-Core phone_normalizer module
"""

from src.alrifai.identity.phone_normalizer import normalize_phone


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


def test_unsupported_input_is_preserved():
    assert normalize_phone("not-a-phone") == "not-a-phone"
