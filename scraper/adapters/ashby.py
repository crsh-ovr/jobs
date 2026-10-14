"""Ashby adapter. GET https://api.ashbyhq.com/posting-api/job-board/{id}?includeCompensation=true"""

from __future__ import annotations

from ..models import Company, Job
from .base import ATSAdapter


def _compensation(posting: dict) -> str | None:
    comp = posting.get("compensation")
    if isinstance(comp, dict):
        summary = comp.get("compensationTierSummary") or comp.get("summaryComponents")
        if isinstance(summary, str):
            return summary
    return None


class AshbyAdapter(ATSAdapter):
    key = "ashby"

    def fetch(self, company: Company) -> list[dict]:
        url = (
            f"https://api.ashbyhq.com/posting-api/job-board/{company.identifier}"
            "?includeCompensation=true"
        )
        data = self.client.get_json(url)
        return data.get("jobs", []) if isinstance(data, dict) else []

    def normalize(self, raw: list[dict], company: Company) -> list[Job]:
        jobs: list[Job] = []
        for p in raw:
            if p.get("isListed") is False:
                continue
            source_id = str(p.get("id") or p.get("jobUrl") or p.get("title", ""))
            jobs.append(
                Job(
                    id=f"ashby:{company.identifier}:{source_id}",
                    title=p.get("title", "").strip(),
                    company=company.name,
                    company_tier=company.tier,
                    industries=list(company.industry),
                    url=p.get("applyUrl") or p.get("jobUrl", ""),
                    source_ats="ashby",
                    location=p.get("location") or (p.get("address") or {}).get("postalAddress"),
                    remote=bool(p.get("isRemote")),
                    department=p.get("department") or p.get("team"),
                    description_html=p.get("descriptionHtml"),
                    description_available=bool(p.get("descriptionHtml")),
                    compensation=_compensation(p),
                    posted_at=p.get("publishedAt") or p.get("publishedDate"),
                )
            )
        return jobs
