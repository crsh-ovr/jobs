"""Greenhouse adapter. GET https://boards-api.greenhouse.io/v1/boards/{id}/jobs?content=true"""

from __future__ import annotations

import html

from ..models import Company, Job
from .base import ATSAdapter


class GreenhouseAdapter(ATSAdapter):
    key = "greenhouse"

    def fetch(self, company: Company) -> list[dict]:
        url = (
            f"https://boards-api.greenhouse.io/v1/boards/{company.identifier}/jobs?content=true"
        )
        data = self.client.get_json(url)
        return data.get("jobs", []) if isinstance(data, dict) else []

    def normalize(self, raw: list[dict], company: Company) -> list[Job]:
        jobs: list[Job] = []
        for p in raw:
            source_id = str(p.get("id") or p.get("absolute_url", ""))
            content = p.get("content")
            # Greenhouse returns HTML-escaped content when content=true.
            description = html.unescape(content) if isinstance(content, str) else None
            location = (p.get("location") or {}).get("name") if p.get("location") else None
            departments = p.get("departments") or []
            dept = departments[0].get("name") if departments else None
            jobs.append(
                Job(
                    id=f"greenhouse:{company.identifier}:{source_id}",
                    title=p.get("title", "").strip(),
                    company=company.name,
                    company_tier=company.tier,
                    industries=list(company.industry),
                    url=p.get("absolute_url", ""),
                    source_ats="greenhouse",
                    location=location,
                    remote=bool(location and "remote" in location.lower()),
                    department=dept,
                    description_html=description,
                    description_available=bool(description),
                    compensation=None,
                    posted_at=p.get("updated_at") or p.get("first_published"),
                )
            )
        return jobs
