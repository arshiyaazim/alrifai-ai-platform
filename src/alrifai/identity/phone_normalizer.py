"""Canonical Bangladeshi phone-number normalization."""


def normalize_phone(raw: str) -> str:
    """Normalize supported Bangladeshi phone formats to ``+880XXXXXXXXX``.

    Inputs that do not match the established 11-digit local or 13-digit
    country-code format are returned unchanged.
    """
    digits = "".join(character for character in raw if character.isdigit())
    if len(digits) == 11 and digits.startswith("0"):
        return "+88" + digits
    if len(digits) == 13 and digits.startswith("880"):
        return "+" + digits
    return raw
