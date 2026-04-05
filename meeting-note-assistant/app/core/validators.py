from datetime import date

from app.core.exceptions import ValidationError


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("Date must use ISO format YYYY-MM-DD.") from exc


def require_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if cleaned:
        return cleaned

    raise ValidationError(f"{field_name} cannot be empty.")
