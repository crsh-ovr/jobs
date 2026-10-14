"""Role-umbrella keyword matching and level detection over job titles."""

from __future__ import annotations

import re

from .models import Job, RoleUmbrella


def normalize_title(title: str) -> str:
    """Lowercase and collapse whitespace; pad with spaces so token keywords like ' i '
    match whole words at the string edges too."""
    cleaned = re.sub(r"\s+", " ", (title or "").lower()).strip()
    return f" {cleaned} "


def match_roles(title: str, umbrellas: list[RoleUmbrella]) -> tuple[list[str], list[str]]:
    """Return (matched_umbrella_keys, matched_role_keys) for a title.

    A role matches when any include_keyword is present AND no exclude_keyword is.
    """
    norm = normalize_title(title)
    matched_umbrellas: list[str] = []
    matched_roles: list[str] = []
    for umb in umbrellas:
        umbrella_hit = False
        for role_key, role in umb.roles.items():
            includes = role.get("include_keywords") or []
            excludes = role.get("exclude_keywords") or []
            if any(kw.lower() in norm for kw in includes) and not any(
                kw.lower() in norm for kw in excludes
            ):
                matched_roles.append(role_key)
                umbrella_hit = True
        if umbrella_hit:
            matched_umbrellas.append(umb.key)
    return matched_umbrellas, matched_roles


def detect_level(title: str, levels: dict) -> str:
    """Detect the seniority level. Highest matched level in `order` wins."""
    norm = normalize_title(title)
    detection: dict[str, list[str]] = levels["detection"]
    order: list[str] = levels["order"]
    best: str | None = None
    best_rank = -1
    for level, keywords in detection.items():
        if level not in order:
            continue
        if any(kw.lower() in norm for kw in keywords):
            rank = order.index(level)
            if rank > best_rank:
                best_rank = rank
                best = level
    return best or levels.get("default", "mid")


def apply_matching(job: Job, umbrellas: list[RoleUmbrella], levels: dict) -> Job | None:
    """Tag a job with umbrellas/roles/level. Returns None if it matches no role."""
    umbs, roles = match_roles(job.title, umbrellas)
    if not roles:
        return None
    job.umbrellas = umbs
    job.roles = roles
    job.level = detect_level(job.title, levels)
    return job
