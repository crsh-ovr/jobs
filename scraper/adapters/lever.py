"""Lever adapter. GET https://api.lever.co/v0/postings/{id}?mode=json"""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import Company, Job
from .base import ATSAdapter


def _iso_from_ms(ms) -> str | None:
    if not isinstance(ms, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return None


class LeverAdapter(ATSAdapter):
    key = "lever"

    def fetch(self, company: Company) -> list[dict]:
        url = f"https://api.lever.co/v0/postings/{company.identifier}?mode=json"
        data = self.client.get_json(url)
        return data if isinstance(data, list) else []

    def normalize(self, raw: list[dict], company: Company) -> list[Job]:
        jobs: list[Job] = []
        for p in raw:
            source_id = str(p.get("id") or p.get("hostedUrl", ""))
            categories = p.get("categories") or {}
            workplace = (p.get("workplaceType") or "").lower()
            location = categories.get("location")
            description = p.get("description") or p.get("descriptionPlain")
            jobs.append(
                Job(
                    id=f"lever:{company.identifier}:{source_id}",
                    title=p.get("text", "").strip(),
                    company=company.name,
                    company_tier=company.tier,
                    industries=list(company.industry),
                    url=p.get("hostedUrl") or p.get("applyUrl", ""),
                    source_ats="lever",
                    location=location,
                    remote=workplace == "remote"
                    or bool(location and "remote" in location.lower()),
                    department=categories.get("team") or categories.get("department"),
                    description_html=description,
                    description_available=bool(description),
                    compensation=categories.get("salaryRange"),
                    posted_at=_iso_from_ms(p.get("createdAt")),
                )
            )
        return jobs
