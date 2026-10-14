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


def test_removed_company_jobs_evicted(tmp_path):
    jobs_path = tmp_path / "jobs.json"
    meta_path = tmp_path / "meta.json"
    # Seed with two companies' jobs.
    merge_and_write(
        [_job("greenhouse:acme:1"), _job("ashby:oldco:2")], {},
        jobs_path=jobs_path, meta_path=meta_path, today="2026-10-01",
    )
    # Next run: oldco removed from allowlist; acme's board returns nothing this run.
    merge_and_write(
        [], {}, jobs_path=jobs_path, meta_path=meta_path,
        active_prefixes={"greenhouse:acme:"}, max_shrink_fraction=1.0, today="2026-10-02",
    )
    ids = {j["id"] for j in json.loads(jobs_path.read_text())["jobs"]}
    assert ids == {"greenhouse:acme:1"}  # acme retained (outage), oldco evicted (removed)


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
