"""Gem adapter. GET https://api.gem.com/job_board/v0/{id}/job_posts/"""

from __future__ import annotations

from ..models import Company, Job
from .base import ATSAdapter


def _location(p: dict) -> str | None:
    loc = p.get("location")
    if isinstance(loc, dict):
        return loc.get("name") or loc.get("display_name")
    if isinstance(loc, list) and loc:
        first = loc[0]
        return first.get("name") if isinstance(first, dict) else str(first)
    return loc if isinstance(loc, str) else None


class GemAdapter(ATSAdapter):
    key = "gem"

    def fetch(self, company: Company) -> list[dict]:
        url = f"https://api.gem.com/job_board/v0/{company.identifier}/job_posts/"
        data = self.client.get_json(url)
        if isinstance(data, dict):
            return data.get("job_posts") or data.get("results") or []
        return data if isinstance(data, list) else []

    def normalize(self, raw: list[dict], company: Company) -> list[Job]:
        jobs: list[Job] = []
        for p in raw:
            source_id = str(p.get("id") or p.get("url", ""))
            location = _location(p)
            description = p.get("description") or p.get("content")
            jobs.append(
                Job(
                    id=f"gem:{company.identifier}:{source_id}",
                    title=(p.get("title") or p.get("name") or "").strip(),
                    company=company.name,
                    company_tier=company.tier,
                    industries=list(company.industry),
                    url=p.get("url") or p.get("apply_url", ""),
                    source_ats="gem",
                    location=location,
                    remote=bool(location and "remote" in location.lower()),
                    department=p.get("department"),
                    description_html=description,
                    description_available=bool(description),
                    compensation=None,
                    posted_at=p.get("updated_at") or p.get("created_at"),
                )
            )
        return jobs
