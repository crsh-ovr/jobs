"""Adapters map recorded fixtures to the common Job schema (offline, deterministic)."""

from scraper.adapters.ashby import AshbyAdapter
from scraper.adapters.gem import GemAdapter
from scraper.adapters.greenhouse import GreenhouseAdapter
from scraper.adapters.lever import LeverAdapter
from scraper.adapters.rippling import RipplingAdapter
from scraper.models import Company


def _company(ats: str, identifier: str, tier: str = "standard") -> Company:
    return Company(
        name=identifier.title(),
        ats=ats,
        identifier=identifier,
        industry=["cybersecurity"],
        tier=tier,
    )


def test_ashby_normalize(load_fixture):
    company = _company("ashby", "horizon3ai", tier="featured")
    jobs = AshbyAdapter().normalize(load_fixture("ashby_sample.json")["jobs"], company)
    titles = [j.title for j in jobs]
    # Unlisted role dropped.
    assert "Hidden Role" not in titles
    fe = next(j for j in jobs if j.title == "Senior Frontend Engineer")
    assert fe.id == "ashby:horizon3ai:ash-1"
    assert fe.company_tier == "featured"
    assert fe.remote is True
    assert fe.compensation == "US$180k - US$220k"
    assert fe.description_available is True
    assert fe.url.endswith("/application")


def test_greenhouse_unescapes_content(load_fixture):
    jobs = GreenhouseAdapter().normalize(
        load_fixture("greenhouse_sample.json")["jobs"], _company("greenhouse", "wiz")
    )
    devops = next(j for j in jobs if j.title == "DevOps Engineer")
    assert devops.id == "greenhouse:wiz:101"
    assert devops.location == "Remote"
    assert devops.remote is True
    # Greenhouse escapes the HTML string once; one unescape restores real HTML
    # (the inner &amp; stays a valid HTML entity).
    assert devops.description_html == "<p>Run the pipelines &amp; infra.</p>"


def test_lever_flat_array(load_fixture):
    jobs = LeverAdapter().normalize(
        load_fixture("lever_sample.json"), _company("lever", "chainguard")
    )
    fs = next(j for j in jobs if j.title == "Staff Full Stack Engineer")
    assert fs.id == "lever:chainguard:lev-1"
    assert fs.remote is True
    assert fs.posted_at is not None  # epoch ms converted to ISO


def test_rippling_no_descriptions(load_fixture):
    jobs = RipplingAdapter().normalize(
        load_fixture("rippling_sample.json")["items"], _company("rippling", "acme")
    )
    principal = next(j for j in jobs if j.title == "Principal DevEx Engineer")
    assert principal.description_available is False
    assert principal.description_html is None
    assert principal.location == "Remote - US"


def test_gem_normalize(load_fixture):
    jobs = GemAdapter().normalize(
        load_fixture("gem_sample.json")["job_posts"], _company("gem", "acme")
    )
    ai = next(j for j in jobs if j.title.startswith("AI Engineer"))
    assert ai.id == "gem:acme:gem-1"
    assert ai.location == "Remote"
