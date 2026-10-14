"""Map the config `ats:` string to an adapter class."""

from __future__ import annotations

from .ashby import AshbyAdapter
from .base import ATSAdapter, HTTPClient
from .gem import GemAdapter
from .getro import GetroAdapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .rippling import RipplingAdapter

ADAPTERS: dict[str, type[ATSAdapter]] = {
    AshbyAdapter.key: AshbyAdapter,
    GreenhouseAdapter.key: GreenhouseAdapter,
    LeverAdapter.key: LeverAdapter,
    RipplingAdapter.key: RipplingAdapter,
    GemAdapter.key: GemAdapter,
    GetroAdapter.key: GetroAdapter,
}

KNOWN_ATS = set(ADAPTERS)


def get_adapter(ats: str, client: HTTPClient) -> ATSAdapter:
    try:
        return ADAPTERS[ats](client)
    except KeyError as exc:
        raise KeyError(f"No adapter registered for ats '{ats}'") from exc
