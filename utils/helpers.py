"""Shared utility functions."""
import uuid
import re
from datetime import datetime


def generate_prescription_id() -> str:
    """Return a short, unique prescription ID like RX-2024-A3F9."""
    suffix = uuid.uuid4().hex[:4].upper()
    year = datetime.now().year
    return f"RX-{year}-{suffix}"


def format_date(dt: datetime | None = None, fmt: str = "%d %b %Y, %I:%M %p") -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).title()


def validate_patient_data(data: dict) -> list[str]:
    """Return a list of validation error strings (empty = valid)."""
    errors = []
    if not data.get("name", "").strip():
        errors.append("Patient name is required.")
    age = data.get("age")
    if age is None or not (0 < int(age) < 130):
        errors.append("Age must be between 1 and 129.")
    weight = data.get("weight")
    if weight is None or not (1 < float(weight) < 500):
        errors.append("Weight must be between 1 and 500 kg.")
    if data.get("gender") not in ("Male", "Female", "Other"):
        errors.append("Gender must be Male, Female, or Other.")
    return errors


def symptom_display_name(symptom: str) -> str:
    """Convert snake_case symptom key to Title Case display string."""
    return symptom.replace("_", " ").title()
