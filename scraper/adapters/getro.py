"""Getro adapter (best-effort / stretch).

Getro's official network API requires an API key. This adapter is disabled by default
(see config/settings.yaml: adapters.getro.enabled) and is skipped at runtime when
GETRO_API_KEY is not set. It is included so Getro-powered boards (e.g. jobs.8vc.com) can be
enabled later without changing the pipeline.
"""

from __future__ import annotations

import os

from ..models import Company, Job
from .base import ATSAdapter

GETRO_API = "https://api.getro.com/api/v2"


class GetroAdapter(ATSAdapter):
    key = "getro"

    def fetch(self, company: Company) -> list[dict]:
        api_key = os.environ.get("GETRO_API_KEY")
        if not api_key:
            return []
        url = f"{GETRO_API}/collections/{company.identifier}/search/jobs"
        data = self.client.get_json(url, headers={"Authorization": f"Bearer {api_key}"})
        if isinstance(data, dict):
            return (data.get("results") or {}).get("jobs") or data.get("jobs") or []
        return []

    def normalize(self, raw: list[dict], company: Company) -> list[Job]:
        jobs: list[Job] = []
        for p in raw:
            source_id = str(p.get("id") or p.get("url", ""))
            org = p.get("organization") or {}
            jobs.append(
                Job(
                    id=f"getro:{company.identifier}:{source_id}",
                    title=(p.get("title") or "").strip(),
                    company=org.get("name") or company.name,
                    company_tier=company.tier,
                    industries=list(company.industry),
                    url=p.get("url") or p.get("apply_url", ""),
                    source_ats="getro",
                    location=p.get("location"),
                    remote=bool(p.get("remote")),
                    department=None,
                    description_html=p.get("description"),
                    description_available=bool(p.get("description")),
                    compensation=None,
                    posted_at=p.get("created_at"),
                )
            )
        return jobs
