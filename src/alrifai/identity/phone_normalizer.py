"""Canonical Bangladeshi phone-number normalization."""


def normalize_phone(raw: str) -> str:
    """Normalize supported Bangladesh mobile formats to the final 11 digits.

    Equivalent ``+880``, ``00880``, ``880``, and local representations return
    the same ``01XXXXXXXXX`` comparison value. Unsupported input is returned
    unchanged so callers can classify it as invalid without losing provenance.
    """
    if not isinstance(raw, str):
        return raw
    digits = "".join(character for character in raw if character.isdigit())
    if len(digits) == 11 and digits.startswith("0"):
        return digits
    if len(digits) == 13 and digits.startswith("880"):
        return "0" + digits[3:]
    if len(digits) == 15 and digits.startswith("00880"):
        return "0" + digits[5:]
    return raw
