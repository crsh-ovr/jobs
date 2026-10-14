"""Write jobs.json/meta.json, preserving first_seen/last_seen and guarding writes."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .models import RELATIONSHIP_RANK, Job


def _load_prior(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("jobs", []) if isinstance(data, dict) else []
    except (json.JSONDecodeError, OSError):
        return []


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=False)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def merge_and_write(
    jobs: list[Job],
    meta: dict,
    *,
    jobs_path: Path,
    meta_path: Path,
    stale_after_days: int = 30,
    max_shrink_fraction: float = 0.8,
    active_prefixes: set[str] | None = None,
    today: str | None = None,
) -> dict:
    """Merge first_seen/last_seen from the prior file, age out stale jobs, and write.

    Returns the meta dict (augmented with write status). If the fresh job count shrinks
    by more than max_shrink_fraction versus the prior file, the jobs file is NOT written
    (guards against mass upstream failure); meta is still written with a flag.
    """
    today = today or date.today().isoformat()
    prior = _load_prior(jobs_path)
    prior_by_id = {j["id"]: j for j in prior if "id" in j}

    # Current run's jobs: carry forward first_seen, refresh last_seen.
    current: dict[str, dict] = {}
    for job in jobs:
        d = job.to_dict()
        was = prior_by_id.get(job.id)
        d["first_seen"] = (was.get("first_seen") if was else None) or today
        d["last_seen"] = today
        current[job.id] = d

    # Retain recently-seen prior jobs whose source failed this run, so a one-day outage
    # does not wipe a company. Only retain jobs whose company is STILL in the allowlist
    # (so removing a company drops its jobs immediately, not after the staleness window).
    # Drop anything past the staleness window.
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=stale_after_days)).isoformat()
    for jid, old in prior_by_id.items():
        if jid in current:
            continue
        if active_prefixes is not None and not any(jid.startswith(p) for p in active_prefixes):
            continue  # company no longer in the allowlist
        last_seen = old.get("last_seen") or old.get("first_seen") or "1970-01-01"
        if last_seen >= cutoff:
            current[jid] = old  # keep as-is; last_seen not refreshed

    merged = list(current.values())
    # featured first, then worked > known > watchlist, then company/title.
    merged.sort(
        key=lambda j: (
            j.get("company_tier") != "featured",
            RELATIONSHIP_RANK.get(j.get("company_relationship", "watchlist"), 2),
            j.get("company", ""),
            j.get("title", ""),
        )
    )

    prior_count = len(prior)
    fresh_count = len(jobs)
    shrink_blocked = (
        prior_count > 0 and fresh_count < prior_count * (1 - max_shrink_fraction)
    )

    meta = dict(meta)
    meta["generated_at"] = datetime.now(timezone.utc).isoformat()
    meta["prior_job_count"] = prior_count
    meta["fresh_job_count"] = fresh_count
    meta["total_job_count"] = len(merged)
    meta["shrink_blocked"] = shrink_blocked

    if shrink_blocked:
        _atomic_write(meta_path, meta)
        return meta

    _atomic_write(jobs_path, {"generated_at": meta["generated_at"], "jobs": merged})
    _atomic_write(meta_path, meta)
    return meta
