import pytest
from app.services.compatibility import COMPATIBILITY, get_compatible_donor_groups, is_compatible


def test_compatibility_exact_matrix():
    expected = {
        "O-": ["O-"],
        "O+": ["O+", "O-"],
        "A-": ["A-", "O-"],
        "A+": ["A+", "A-", "O+", "O-"],
        "B-": ["B-", "O-"],
        "B+": ["B+", "B-", "O+", "O-"],
        "AB-": ["AB-", "A-", "B-", "O-"],
        "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],
    }
    assert COMPATIBILITY == expected


def test_universal_donor_and_recipient():
    # O- can be given to all 8 blood groups
    for group in COMPATIBILITY.keys():
        assert is_compatible(recipient_group=group, donor_group="O-") is True

    # AB+ can receive from all 8 blood groups
    for group in COMPATIBILITY.keys():
        assert is_compatible(recipient_group="AB+", donor_group=group) is True

    # O- can only receive from O-
    assert get_compatible_donor_groups("O-") == ["O-"]


def test_invalid_blood_group():
    with pytest.raises(ValueError, match="Invalid blood group"):
        get_compatible_donor_groups("XYZ")
