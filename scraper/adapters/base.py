"""Adapter contract shared by every ATS implementation."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import requests

from ..models import Company, Job


class HTTPClient:
    """Small requests wrapper with a shared UA, timeout, retries, and politeness delay."""

    def __init__(
        self,
        *,
        user_agent: str,
        timeout: float = 15.0,
        max_retries: int = 2,
        backoff: float = 2.0,
        politeness_delay: float = 1.0,
        sleep=time.sleep,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.politeness_delay = politeness_delay
        self._sleep = sleep
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})

    def get_json(self, url: str, **kwargs) -> Any:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout, **kwargs)
                resp.raise_for_status()
                data = resp.json()
                if self.politeness_delay:
                    self._sleep(self.politeness_delay)
                return data
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    self._sleep(self.backoff * (attempt + 1))
        raise last_exc  # type: ignore[misc]


class ATSAdapter(ABC):
    """Fetch raw postings for a company and normalize them to Job objects."""

    key: str = ""

    def __init__(self, client: HTTPClient | None = None):
        self.client = client

    @abstractmethod
    def fetch(self, company: Company) -> list[dict]:
        """Return the raw list of posting dicts from the ATS."""

    @abstractmethod
    def normalize(self, raw: list[dict], company: Company) -> list[Job]:
        """Map raw postings to the common Job schema (no role filtering here)."""

    def run(self, company: Company) -> list[Job]:
        return self.normalize(self.fetch(company), company)


def industries_for(company: Company) -> list[str]:
    return list(company.industry)
