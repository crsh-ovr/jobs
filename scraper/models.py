"""Common data models shared across adapters and the pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

INDUSTRY_VOCAB = {"cybersecurity", "deftech", "cspm", "finops", "grc", "healthtech"}
TIERS = {"featured", "standard"}
# Shane's affinity buckets; drives secondary ordering and a display badge.
RELATIONSHIPS = {"worked", "known", "watchlist"}
# Lower rank sorts first.
RELATIONSHIP_RANK = {"worked": 0, "known": 1, "watchlist": 2}


@dataclass
class Company:
    """One vetted company from the allowlist."""

    name: str
    ats: str
    identifier: str
    industry: list[str]
    tier: str = "standard"
    relationship: str = "watchlist"
    homepage: str | None = None


@dataclass
class RoleUmbrella:
    """A role grouping that mirrors the career guide taxonomy."""

    key: str
    label: str
    career_url: str
    # role_key -> {"label", "include_keywords", "exclude_keywords"}
    roles: dict[str, dict]


@dataclass
class Job:
    """A normalized job posting. Every adapter emits this shape."""

    id: str
    title: str
    company: str
    company_tier: str
    industries: list[str]
    url: str
    source_ats: str
    # Set from the company after normalization (see main.scrape_company).
    company_relationship: str = "watchlist"
    # Filled in by matching.py
    umbrellas: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    level: str = "mid"
    # Best-effort fields; may be None/empty depending on the ATS.
    location: str | None = None
    remote: bool = False
    department: str | None = None
    description_html: str | None = None
    description_available: bool = True
    compensation: str | None = None
    posted_at: str | None = None
    # Maintained by writer.py across runs.
    first_seen: str | None = None
    last_seen: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
