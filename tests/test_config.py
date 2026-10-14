"""Validate the live config — this is the guardrail for community 'add a company' PRs."""

import pytest

from scraper.adapters.registry import KNOWN_ATS
from scraper.config_loader import (
    ConfigError,
    load_companies,
    load_roles,
    load_settings,
)
from scraper.models import INDUSTRY_VOCAB, TIERS


def test_live_companies_valid():
    companies = load_companies(valid_ats=KNOWN_ATS)
    assert companies, "companies.yaml must list at least one company"
    for c in companies:
        assert c.ats in KNOWN_ATS
        assert c.identifier
        assert set(c.industry) <= INDUSTRY_VOCAB
        assert c.tier in TIERS


def test_exactly_one_featured_is_horizon3():
    featured = [c for c in load_companies(valid_ats=KNOWN_ATS) if c.tier == "featured"]
    assert any("horizon3" in c.name.lower() for c in featured)


def test_live_roles_and_settings_load():
    umbrellas, levels = load_roles()
    assert umbrellas
    assert "order" in levels and "detection" in levels
    settings = load_settings()
    assert settings.user_agent
    assert 0 < settings.max_shrink_fraction <= 1


def test_unknown_ats_rejected(tmp_path):
    bad = tmp_path / "companies.yaml"
    bad.write_text(
        "companies:\n  - name: X\n    ats: workday\n    identifier: x\n    industry: [grc]\n"
    )
    with pytest.raises(ConfigError):
        load_companies(path=bad, valid_ats=KNOWN_ATS)


def test_unknown_industry_rejected(tmp_path):
    bad = tmp_path / "companies.yaml"
    bad.write_text(
        "companies:\n  - name: X\n    ats: ashby\n    identifier: x\n    industry: [crypto]\n"
    )
    with pytest.raises(ConfigError):
        load_companies(path=bad, valid_ats=KNOWN_ATS)
