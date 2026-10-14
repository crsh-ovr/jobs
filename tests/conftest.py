import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    def _load(name: str):
        with (FIXTURES / name).open(encoding="utf-8") as fh:
            return json.load(fh)

    return _load
