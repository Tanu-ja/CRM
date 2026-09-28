import pytest

from apps.leads.utils import make_lead_id, normalize_phone


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("+91 98765 43210", "9876543210"),
        ("919876543210", "9876543210"),
        ("9876543210", "9876543210"),
        ("098765-43210", "098765-43210".replace("-", "")),  # no leading 91, kept as-is (11 digits)
        ("", ""),
        ("123", "123"),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_normalize_phone_does_not_strip_91_when_not_followed_by_exactly_10_digits():
    # 91 followed by only 9 digits: the '91' is part of the number, not a country code.
    assert normalize_phone("91123456789") == "91123456789"


def test_make_lead_id_format():
    assert make_lead_id("nurse", 2026, 7) == "SS-NURSE-2026-000007"
    assert make_lead_id("IT", 2026, 123456) == "SS-IT-2026-123456"
