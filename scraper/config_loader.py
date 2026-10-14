"""Load and validate the YAML config into typed objects. Fails loudly on bad config."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import INDUSTRY_VOCAB, RELATIONSHIPS, TIERS, Company, RoleUmbrella

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


class ConfigError(ValueError):
    """Raised when the config is structurally invalid."""


@dataclass
class Settings:
    timeout_seconds: float
    max_retries: int
    backoff_seconds: float
    politeness_delay_seconds: float
    user_agent: str
    getro_enabled: bool
    jobs_path: str
    meta_path: str
    stale_after_days: int
    max_shrink_fraction: float


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a mapping at the top of {path.name}")
    return data


def load_companies(path: Path | None = None, *, valid_ats: set[str] | None = None) -> list[Company]:
    path = path or CONFIG_DIR / "companies.yaml"
    data = _load_yaml(path)
    raw = data.get("companies")
    if not isinstance(raw, list) or not raw:
        raise ConfigError("companies.yaml must contain a non-empty 'companies' list")

    companies: list[Company] = []
    seen: set[tuple[str, str]] = set()
    for i, entry in enumerate(raw):
        where = f"companies[{i}]"
        if not isinstance(entry, dict):
            raise ConfigError(f"{where} must be a mapping")
        for required in ("name", "ats", "identifier", "industry"):
            if not entry.get(required):
                raise ConfigError(f"{where} is missing required field '{required}'")

        ats = str(entry["ats"]).strip().lower()
        if valid_ats is not None and ats not in valid_ats:
            raise ConfigError(f"{where} '{entry['name']}' has unknown ats '{ats}'")

        industry = entry["industry"]
        if isinstance(industry, str):
            industry = [industry]
        if not isinstance(industry, list) or not industry:
            raise ConfigError(f"{where} 'industry' must be a non-empty list")
        bad = [x for x in industry if x not in INDUSTRY_VOCAB]
        if bad:
            raise ConfigError(
                f"{where} has unknown industry {bad}; allowed: {sorted(INDUSTRY_VOCAB)}"
            )

        tier = str(entry.get("tier", "standard")).strip().lower()
        if tier not in TIERS:
            raise ConfigError(f"{where} has invalid tier '{tier}'; allowed: {sorted(TIERS)}")

        relationship = str(entry.get("relationship", "watchlist")).strip().lower()
        if relationship not in RELATIONSHIPS:
            raise ConfigError(
                f"{where} has invalid relationship '{relationship}'; "
                f"allowed: {sorted(RELATIONSHIPS)}"
            )

        key = (ats, str(entry["identifier"]).strip().lower())
        if key in seen:
            raise ConfigError(f"{where} duplicates an earlier company ({key[0]}:{key[1]})")
        seen.add(key)

        companies.append(
            Company(
                name=str(entry["name"]).strip(),
                ats=ats,
                identifier=str(entry["identifier"]).strip(),
                industry=list(industry),
                tier=tier,
                relationship=relationship,
                homepage=entry.get("homepage"),
            )
        )
    return companies


def load_roles(path: Path | None = None) -> tuple[list[RoleUmbrella], dict]:
    path = path or CONFIG_DIR / "roles.yaml"
    data = _load_yaml(path)
    raw_umbrellas = data.get("umbrellas")
    if not isinstance(raw_umbrellas, dict) or not raw_umbrellas:
        raise ConfigError("roles.yaml must contain a non-empty 'umbrellas' mapping")

    umbrellas: list[RoleUmbrella] = []
    for key, u in raw_umbrellas.items():
        if not isinstance(u, dict):
            raise ConfigError(f"umbrella '{key}' must be a mapping")
        umbrellas.append(
            RoleUmbrella(
                key=key,
                label=u.get("label", key),
                career_url=u.get("career_url", ""),
                roles=u.get("roles") or {},
            )
        )

    levels = data.get("levels")
    if not isinstance(levels, dict) or "detection" not in levels or "order" not in levels:
        raise ConfigError("roles.yaml must contain a 'levels' block with 'order' and 'detection'")
    return umbrellas, levels


def load_settings(path: Path | None = None) -> Settings:
    path = path or CONFIG_DIR / "settings.yaml"
    data = _load_yaml(path)
    http = data.get("http", {})
    output = data.get("output", {})
    getro = (data.get("adapters", {}) or {}).get("getro", {}) or {}
    return Settings(
        timeout_seconds=float(http.get("timeout_seconds", 15)),
        max_retries=int(http.get("max_retries", 2)),
        backoff_seconds=float(http.get("backoff_seconds", 2.0)),
        politeness_delay_seconds=float(http.get("politeness_delay_seconds", 1.0)),
        user_agent=str(http.get("user_agent", "shanes-jobs-bot/1.0")),
        getro_enabled=bool(getro.get("enabled", False)),
        jobs_path=str(output.get("jobs_path", "data/jobs.json")),
        meta_path=str(output.get("meta_path", "data/meta.json")),
        stale_after_days=int(output.get("stale_after_days", 30)),
        max_shrink_fraction=float(output.get("max_shrink_fraction", 0.8)),
    )
