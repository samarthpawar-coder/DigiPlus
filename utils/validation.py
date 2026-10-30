
from datetime import date


def validate_required(value, field_name):
    """Check whether a required field is empty."""

    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} is required.")

    return str(value).strip()


def validate_email(email):
    """Basic email validation."""

    email = validate_required(email, "Email")

    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Please enter a valid email address.")

    return email.lower()


def validate_due_date(due_date):
    """Validate task due date."""

    if not due_date:
        return None

    if isinstance(due_date, date):
        return due_date.isoformat()

    raise ValueError("Invalid due date.")


def validate_status(status):
    """Validate action item status."""

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Completed",
        "Blocked"
    ]

    if status not in allowed_statuses:
        raise ValueError("Invalid action item status.")

    return status


def validate_participants(participants):
    """Validate meeting participants."""

    if not participants:
        raise ValueError("At least one participant is required.")

    cleaned = [
        str(person).strip()
        for person in participants
        if str(person).strip()
    ]

    if not cleaned:
        raise ValueError("Participant list cannot be empty.")

    return cleaned
