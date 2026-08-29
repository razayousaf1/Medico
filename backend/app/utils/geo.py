"""Geo distance and strength-normalisation helpers."""

import math
import re

_NUMBER_UNIT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|%|)?", re.IGNORECASE)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two coordinates in kilometres."""
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _parse_strength(value: str | None) -> tuple[float, str] | None:
    """Extract (number, unit) from strings like '625 mg', '0.5g', '5ml'."""
    if not value:
        return None
    match = _NUMBER_UNIT_RE.search(value.strip())
    if not match:
        return None
    number = float(match.group(1))
    unit = (match.group(2) or "").lower()
    # Normalise grams to milligrams so "0.5 g" == "500 mg"
    if unit == "g":
        number *= 1000.0
        unit = "mg"
    return number, unit


def strengths_match(a: str | None, b: str | None) -> bool | None:
    """Compare two strength strings loosely. Returns None when either is unknown."""
    if not a or not b:
        return None
    parsed_a = _parse_strength(a)
    parsed_b = _parse_strength(b)
    if parsed_a is None or parsed_b is None:
        # Fall back to character-level comparison ("625mg" vs "625 mg")
        normalise = lambda s: re.sub(r"[\s]", "", s.lower())  # noqa: E731
        return normalise(a) == normalise(b)
    num_a, unit_a = parsed_a
    num_b, unit_b = parsed_b
    if unit_a == unit_b:
        return abs(num_a - num_b) < 0.001
    # One side has no unit — compare numbers only
    if not unit_a or not unit_b:
        return abs(num_a - num_b) < 0.001
    return False
