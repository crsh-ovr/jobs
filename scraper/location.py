"""Classify a free-text job location as US / non-US / unknown.

Location strings vary a lot across ATSes ("US, Remote", "San Francisco, CA",
"London, UK", "Bengaluru, India", "Remote - EMEA", "Remote"). The goal is to keep a role
if it is hiring in the US (even when it also hires elsewhere) and drop clearly non-US
roles. US signals are checked FIRST so a multi-region role like "San Francisco, CA / London"
is kept.
"""

from __future__ import annotations

import re

# 50 states + DC + Puerto Rico. Matched only as uppercase codes after a comma ("City, CA")
# to avoid false positives from words like "in"/"or"/"ok" or country codes.
_STATE_ABBREV = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN",
    "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV",
    "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC", "PR",
}

_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming",
    "district of columbia", "puerto rico",
}

# Explicit US phrases (substring match on the lowercased string).
_US_PHRASES = (
    "united states", "u.s.a", "u.s.", "us-remote", "us remote", "remote - us",
    "remote-us", "remote, us", "remote (us", "remote us", "anywhere in the us",
    "anywhere in the u.s", "nationwide", "remote - united states", "remote, united states",
    "remote (united states", "washington, d.c", "washington dc",
)

# Clear non-US signals (country names / regions / major non-US hub cities). Substring match.
_NON_US = (
    # regions
    "emea", "apac", "latam", "europe", "european union", "middle east", "asia pacific",
    # countries
    "united kingdom", "england", "scotland", "wales", "northern ireland", "ireland",
    "canada", "mexico", "brazil", "brasil", "argentina", "chile", "colombia", "peru",
    "uruguay", "costa rica", "germany", "france", "spain", "portugal", "italy",
    "netherlands", "belgium", "switzerland", "austria", "sweden", "norway", "denmark",
    "finland", "poland", "czech", "slovakia", "romania", "bulgaria", "hungary", "greece",
    "ukraine", "serbia", "croatia", "lithuania", "latvia", "estonia", "iceland", "turkey",
    "israel", "united arab emirates", "saudi arabia", "qatar", "egypt", "south africa",
    "nigeria", "kenya", "morocco", "india", "pakistan", "bangladesh", "sri lanka",
    "china", "hong kong", "taiwan", "japan", "south korea", "singapore", "malaysia",
    "indonesia", "philippines", "vietnam", "thailand", "australia", "new zealand",
    # hub cities
    "london", "dublin", "manchester", "edinburgh", "berlin", "munich", "hamburg",
    "frankfurt", "paris", "lyon", "madrid", "barcelona", "lisbon", "porto", "amsterdam",
    "rotterdam", "brussels", "zurich", "geneva", "vienna", "stockholm", "oslo",
    "copenhagen", "helsinki", "warsaw", "krakow", "prague", "bucharest", "sofia",
    "budapest", "athens", "vilnius", "tallinn", "riga", "belgrade", "tel aviv", "dubai",
    "abu dhabi", "cairo", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai",
    "new delhi", "gurgaon", "gurugram", "noida", "chennai", "kolkata", "ahmedabad",
    "karachi", "lahore", "dhaka", "colombo", "beijing", "shanghai", "shenzhen",
    "tokyo", "osaka", "seoul", "taipei", "kuala lumpur", "jakarta", "manila",
    "ho chi minh", "bangkok", "sydney", "melbourne", "brisbane", "auckland",
    "toronto", "vancouver", "montreal", "ottawa", "calgary", "waterloo", "mexico city",
    "sao paulo", "são paulo", "buenos aires", "bogota", "bogotá", "santiago", "lima",
)

# "City, ST" — uppercase 2-letter code after a comma.
_CITY_STATE_RE = re.compile(r",\s*([A-Z]{2})(?=\b|\s|/|;|$)")
# Standalone US / USA token.
_US_TOKEN_RE = re.compile(r"\b(us|usa)\b")


def _has_us_signal(text: str, low: str) -> bool:
    if any(p in low for p in _US_PHRASES):
        return True
    if any(name in low for name in _STATE_NAMES):
        return True
    if _US_TOKEN_RE.search(low):
        return True
    if any(code in _STATE_ABBREV for code in _CITY_STATE_RE.findall(text)):
        return True
    return False


def classify(location: str | None) -> bool | None:
    """Return True (US), False (non-US), or None (unknown/ambiguous)."""
    text = (location or "").strip()
    if not text:
        return None
    low = text.lower()
    if _has_us_signal(text, low):
        return True
    if any(tok in low for tok in _NON_US):
        return False
    return None


def is_us(location: str | None, *, include_unknown: bool = True) -> bool:
    """Whether a role should be kept under a US-only filter.

    US signals win over non-US (a role hiring in the US stays even if also elsewhere).
    Ambiguous/blank locations fall back to `include_unknown` (most curated companies that
    post a bare "Remote" are US-based).
    """
    verdict = classify(location)
    if verdict is None:
        return include_unknown
    return verdict
