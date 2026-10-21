"""System-wide constants matching PROJECT.md specifications."""

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")

ROLES = ("admin", "staff", "requester")

REQUESTER_TYPES = ("hospital", "patient")

GENDERS = ("male", "female", "other")

URGENCIES = ("emergency", "routine")

REQUEST_STATUSES = ("pending", "approved", "issued", "rejected")

UNIT_STATUSES = ("available", "issued", "expired")

ACTIVITY_ACTIONS = ("create", "update", "delete", "approve", "reject", "issue")

ACTIVITY_ENTITY_TYPES = (
    "user",
    "staff",
    "requester",
    "donor",
    "blood_unit",
    "blood_request",
    "donation_camp",
    "prediction_run",
)

REPORT_TYPES = (
    "stock",
    "donations",
    "issues",
    "wastage",
    "donors",
    "requests",
    "predictions",
)
