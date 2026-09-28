import re

_LEADING_91 = re.compile(r"^91(?=\d{10}$)")


def normalize_phone(value: str) -> str:
    """Strip everything but digits, then drop a leading '91' country code
    when it's followed by exactly 10 digits. Mirrors the reference
    prototype's `formatPhone` in src/domain.ts."""
    if not value:
        return ""
    digits = re.sub(r"\D", "", value)
    return _LEADING_91.sub("", digits)


def make_lead_id(client_code: str, year: int, sequence: int) -> str:
    """Mirrors `makeLeadId` in src/domain.ts: SS-<CODE>-<YEAR>-<seq, zero-padded to 6>."""
    return f"SS-{client_code.upper()}-{year}-{sequence:06d}"
