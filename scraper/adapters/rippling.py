"""Rippling adapter.

GET https://ats.rippling.com/api/v2/board/{id}/jobs?page=0&pageSize=100

Rippling's board API returns titles/locations/departments but NO descriptions, so jobs are
matched on title and rendered with a "view on company site" note. Paginated.
"""

from __future__ import annotations

from ..models import Company, Job
from .base import ATSAdapter

_PAGE_SIZE = 100
_MAX_PAGES = 20  # safety bound


class RipplingAdapter(ATSAdapter):
    key = "rippling"

    def fetch(self, company: Company) -> list[dict]:
        items: list[dict] = []
        for page in range(_MAX_PAGES):
            url = (
                f"https://ats.rippling.com/api/v2/board/{company.identifier}/jobs"
                f"?page={page}&pageSize={_PAGE_SIZE}"
            )
            data = self.client.get_json(url)
            batch = data.get("items", []) if isinstance(data, dict) else []
            if not batch:
                break
            items.extend(batch)
            if len(batch) < _PAGE_SIZE:
                break
        return items

    def normalize(self, raw: list[dict], company: Company) -> list[Job]:
        jobs: list[Job] = []
        for p in raw:
            source_id = str(p.get("uuid") or p.get("id") or p.get("url", ""))
            location = p.get("location")
            if isinstance(location, dict):
                location = location.get("label") or location.get("name")
            jobs.append(
                Job(
                    id=f"rippling:{company.identifier}:{source_id}",
                    title=(p.get("name") or p.get("title") or "").strip(),
                    company=company.name,
                    company_tier=company.tier,
                    industries=list(company.industry),
                    url=p.get("url") or p.get("applicationUrl", ""),
                    source_ats="rippling",
                    location=location,
                    remote=bool(location and "remote" in str(location).lower()),
                    department=p.get("department"),
                    description_html=None,
                    description_available=False,
                    compensation=None,
                    posted_at=p.get("createdAt") or p.get("updatedAt"),
                )
            )
        return jobs
