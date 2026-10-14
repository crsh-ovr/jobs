import json

from scraper.models import Job
from scraper.writer import merge_and_write


def _job(jid):
    return Job(
        id=jid, title="Frontend Engineer", company="Acme", company_tier="standard",
        industries=["cybersecurity"], url=f"https://e/{jid}", source_ats="greenhouse",
        roles=["frontend"], umbrellas=["engineering"], level="mid",
    )


def test_first_seen_preserved_last_seen_refreshed(tmp_path):
    jobs_path = tmp_path / "jobs.json"
    meta_path = tmp_path / "meta.json"
    merge_and_write([_job("a:1")], {}, jobs_path=jobs_path, meta_path=meta_path, today="2026-10-01")

    merge_and_write([_job("a:1")], {}, jobs_path=jobs_path, meta_path=meta_path, today="2026-10-14")
    data = json.loads(jobs_path.read_text())["jobs"]
    job = data[0]
    assert job["first_seen"] == "2026-10-01"
    assert job["last_seen"] == "2026-10-14"


def test_only_failed_company_jobs_retained(tmp_path):
    jobs_path = tmp_path / "jobs.json"
    meta_path = tmp_path / "meta.json"
    # Seed with two companies' jobs.
    merge_and_write(
        [_job("greenhouse:acme:1"), _job("ashby:oldco:2")], {},
        jobs_path=jobs_path, meta_path=meta_path, today="2026-10-01",
    )
    # Next run returns nothing. acme's adapter FAILED (retain), oldco's SUCCEEDED-empty or
    # was removed (drop). retain_prefixes carries only the failed company.
    merge_and_write(
        [], {}, jobs_path=jobs_path, meta_path=meta_path,
        retain_prefixes={"greenhouse:acme:"}, max_shrink_fraction=1.0, today="2026-10-02",
    )
    ids = {j["id"] for j in json.loads(jobs_path.read_text())["jobs"]}
    assert ids == {"greenhouse:acme:1"}  # acme retained (outage), oldco dropped


def test_filtered_jobs_not_resurrected_when_adapter_succeeds(tmp_path):
    jobs_path = tmp_path / "jobs.json"
    meta_path = tmp_path / "meta.json"
    merge_and_write(
        [_job("greenhouse:acme:1"), _job("greenhouse:acme:2")], {},
        jobs_path=jobs_path, meta_path=meta_path, today="2026-10-01",
    )
    # acme succeeds but now only returns job 1 (job 2 was filtered out, e.g. non-US).
    # retain_prefixes is empty (no failures) -> job 2 must not come back.
    merge_and_write(
        [_job("greenhouse:acme:1")], {}, jobs_path=jobs_path, meta_path=meta_path,
        retain_prefixes=set(), max_shrink_fraction=1.0, today="2026-10-02",
    )
    ids = {j["id"] for j in json.loads(jobs_path.read_text())["jobs"]}
    assert ids == {"greenhouse:acme:1"}


def test_shrink_guard_blocks_write(tmp_path):
    jobs_path = tmp_path / "jobs.json"
    meta_path = tmp_path / "meta.json"
    merge_and_write(
        [_job(f"a:{i}") for i in range(10)], {}, jobs_path=jobs_path, meta_path=meta_path,
        today="2026-10-01",
    )
    before = jobs_path.read_text()
    # Fresh run returns just 1 job (>80% drop) -> write blocked, file unchanged.
    meta = merge_and_write(
        [_job("a:0")], {}, jobs_path=jobs_path, meta_path=meta_path,
        max_shrink_fraction=0.8, today="2026-10-02",
    )
    assert meta["shrink_blocked"] is True
    assert jobs_path.read_text() == before
