"""Entry point: load config -> run adapters -> match -> dedup -> write jobs.json."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from .adapters.base import HTTPClient
from .adapters.registry import KNOWN_ATS, get_adapter
from .config_loader import load_companies, load_roles, load_settings
from .dedup import dedup
from .location import is_us
from .matching import apply_matching
from .models import Company, Job
from .writer import merge_and_write

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("scraper")

ROOT = Path(__file__).resolve().parent.parent


def scrape_company(company: Company, client: HTTPClient) -> tuple[list[Job], dict]:
    """Fetch + normalize one company. Isolated: never raises on network errors."""
    status = {"company": company.name, "ats": company.ats, "ok": False, "count": 0, "error": None}
    try:
        adapter = get_adapter(company.ats, client)
        jobs = adapter.run(company)
        for job in jobs:
            job.priority = company.priority
        status["ok"] = True
        status["count"] = len(jobs)
        return jobs, status
    except Exception as exc:  # noqa: BLE001 - isolation: one company must not fail the run
        log.warning("Fetch failed for %s (%s): %s", company.name, company.ats, exc)
        status["error"] = f"{type(exc).__name__}: {exc}"
        return [], status


def run() -> int:
    settings = load_settings()
    companies = load_companies(valid_ats=KNOWN_ATS)
    umbrellas, levels = load_roles()

    client = HTTPClient(
        user_agent=settings.user_agent,
        timeout=settings.timeout_seconds,
        max_retries=settings.max_retries,
        backoff=settings.backoff_seconds,
        politeness_delay=settings.politeness_delay_seconds,
    )

    all_matched: list[Job] = []
    adapter_status: list[dict] = []
    retain_prefixes: set[str] = set()  # companies whose adapter failed -> keep prior jobs

    for company in companies:
        if company.ats == "getro" and not settings.getro_enabled:
            log.info("Skipping %s: getro adapter disabled", company.name)
            adapter_status.append(
                {
                    "company": company.name,
                    "ats": "getro",
                    "ok": True,
                    "count": 0,
                    "error": "disabled",
                }
            )
            continue

        raw_jobs, status = scrape_company(company, client)
        if not status["ok"]:
            retain_prefixes.add(f"{company.ats}:{company.identifier}:")
        matched = [j for j in (apply_matching(j, umbrellas, levels) for j in raw_jobs) if j]
        status["matched"] = len(matched)
        if settings.us_only:
            kept = [
                j for j in matched
                if is_us(j.location, include_unknown=settings.include_unknown_location)
            ]
            status["dropped_non_us"] = len(matched) - len(kept)
            matched = kept
        adapter_status.append(status)
        all_matched.extend(matched)
        log.info("%s: %d fetched, %d kept", company.name, status["count"], len(matched))

    deduped = dedup(all_matched)
    log.info("Total: %d kept, %d after dedup", len(all_matched), len(deduped))

    meta = {
        "companies": len(companies),
        "adapters": adapter_status,
        "any_failures": any(not s["ok"] for s in adapter_status),
        "us_only": settings.us_only,
        "dropped_non_us": sum(s.get("dropped_non_us", 0) for s in adapter_status),
    }
    result = merge_and_write(
        deduped,
        meta,
        jobs_path=ROOT / settings.jobs_path,
        meta_path=ROOT / settings.meta_path,
        stale_after_days=settings.stale_after_days,
        max_shrink_fraction=settings.max_shrink_fraction,
        retain_prefixes=retain_prefixes,
    )

    if result.get("shrink_blocked"):
        log.error(
            "Write blocked: fresh count %d shrank too far below prior %d; jobs.json NOT updated",
            result["fresh_job_count"],
            result["prior_job_count"],
        )
        return 1
    log.info("Wrote %d jobs to %s", result["total_job_count"], settings.jobs_path)
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
