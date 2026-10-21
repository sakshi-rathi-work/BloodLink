"""Canonical blood group compatibility matrix and helper functions."""
from typing import Dict, List
from app.core.constants import BLOOD_GROUPS

# Canonical Whole Blood / Red Cell Compatibility Matrix (Section 6.3)
# Key: Requested (recipient) blood group
# Value: Compatible donor blood groups that are safe to issue
COMPATIBILITY: Dict[str, List[str]] = {
    "O-": ["O-"],
    "O+": ["O+", "O-"],
    "A-": ["A-", "O-"],
    "A+": ["A+", "A-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],
}


def get_compatible_donor_groups(requested_group: str) -> List[str]:
    """Return the list of donor blood groups compatible with the recipient blood group."""
    if requested_group not in COMPATIBILITY:
        raise ValueError(
            f"Invalid blood group '{requested_group}'. Allowed values: {', '.join(BLOOD_GROUPS)}"
        )
    return COMPATIBILITY[requested_group]


def is_compatible(recipient_group: str, donor_group: str) -> bool:
    """Check if donor group can safely be given to recipient group."""
    compatible_groups = get_compatible_donor_groups(recipient_group)
    return donor_group in compatible_groups
