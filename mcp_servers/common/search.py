from __future__ import annotations

import re
from datetime import date, datetime, time, timezone
from typing import Any, Iterable

from .errors import ToolInputError


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*", re.IGNORECASE)


def normalize_text(value: object) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        return " ".join(normalize_text(item) for item in value)

    if isinstance(value, dict):
        return " ".join(normalize_text(item) for item in value.values())

    return " ".join(str(value).lower().split())


def tokenize(query: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(query)]


def validate_limit(limit: int, *, max_limit: int = 50) -> int:
    if not isinstance(limit, int):
        raise ToolInputError("limit must be an integer.")

    if limit < 1:
        raise ToolInputError("limit must be greater than zero.")

    if limit > max_limit:
        raise ToolInputError(f"limit cannot exceed {max_limit}.")

    return limit


def ensure_query_or_filter(query: str, filters: Iterable[object]) -> None:
    if query.strip():
        return

    if any(value not in (None, "") for value in filters):
        return

    raise ToolInputError("Provide a query or at least one filter.")


def exact_optional(value: str, expected: str | None) -> bool:
    if expected is None or expected == "":
        return True

    return value.casefold() == expected.casefold()


def contains_optional(value: str, expected: str | None) -> bool:
    if expected is None or expected == "":
        return True

    return expected.casefold() in value.casefold()


def text_score(query: str, text: str) -> float:
    normalized_query = normalize_text(query)
    normalized_text = normalize_text(text)

    if not normalized_query:
        return 1.0

    query_tokens = tokenize(normalized_query)
    if not query_tokens:
        return 0.0

    unique_tokens = sorted(set(query_tokens))
    token_hits = sum(1 for token in unique_tokens if token in normalized_text)
    if token_hits == 0 and normalized_query not in normalized_text:
        return 0.0

    token_score = token_hits / len(unique_tokens)
    phrase_bonus = 0.35 if normalized_query in normalized_text else 0.0
    return round(token_score + phrase_bonus, 4)


def matched_fields(query: str, record: dict[str, Any], fields: Iterable[str]) -> list[str]:
    if not query.strip():
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    matches: list[str] = []
    for field in fields:
        value = normalize_text(record.get(field))
        if any(token in value for token in query_tokens):
            matches.append(field)

    return matches


def parse_datetime(value: str, *, field_name: str) -> datetime:
    try:
        if len(value) == 10:
            parsed_date = date.fromisoformat(value)
            return datetime.combine(parsed_date, time.min, tzinfo=timezone.utc)

        parsed_datetime = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ToolInputError(
            f"{field_name} must be an ISO date or datetime, got {value!r}."
        ) from exc

    if parsed_datetime.tzinfo is None:
        return parsed_datetime.replace(tzinfo=timezone.utc)

    return parsed_datetime.astimezone(timezone.utc)


def timestamp_in_range(
    timestamp: str,
    *,
    since: str | None = None,
    until: str | None = None,
) -> bool:
    current = parse_datetime(timestamp, field_name="timestamp")

    if since:
        since_dt = parse_datetime(since, field_name="since")
        if current < since_dt:
            return False

    if until:
        until_dt = parse_datetime(until, field_name="until")
        if current > until_dt:
            return False

    return True

