"""De-duplicate normalized jobs."""

from __future__ import annotations

import re

from .models import Job


def _fuzzy_key(job: Job) -> str:
    title = re.sub(r"\s+", " ", (job.title or "").lower()).strip()
    loc = re.sub(r"\s+", " ", (job.location or "").lower()).strip()
    return f"{job.company.lower()}|{title}|{loc}"


def dedup(jobs: list[Job]) -> list[Job]:
    """Collapse exact-id duplicates, then collapse near-duplicates that share a
    company+title+location key (e.g. the same role posted on two boards).

    Order is preserved; the first occurrence wins.
    """
    by_id: dict[str, Job] = {}
    for job in jobs:
        by_id.setdefault(job.id, job)

    result: list[Job] = []
    seen_fuzzy: set[str] = set()
    for job in by_id.values():
        key = _fuzzy_key(job)
        if key in seen_fuzzy:
            continue
        seen_fuzzy.add(key)
        result.append(job)
    return result
