from scraper.dedup import dedup
from scraper.models import Job


def _job(jid, title="Frontend Engineer", company="Acme", location="Remote"):
    return Job(
        id=jid,
        title=title,
        company=company,
        company_tier="standard",
        industries=["cybersecurity"],
        url=f"https://example.com/{jid}",
        source_ats="greenhouse",
        location=location,
    )


def test_exact_id_duplicates_collapse():
    jobs = [_job("a:1"), _job("a:1"), _job("b:2", title="Backend Engineer")]
    assert len(dedup(jobs)) == 2


def test_fuzzy_same_role_two_boards_collapse():
    # Same company/title/location posted on two different ATSes -> one survivor.
    jobs = [
        _job("greenhouse:acme:1"),
        _job("lever:acme:9"),
    ]
    result = dedup(jobs)
    assert len(result) == 1
    assert result[0].id == "greenhouse:acme:1"  # first wins


def test_distinct_locations_kept():
    jobs = [_job("a:1", location="Remote"), _job("a:2", location="NYC")]
    assert len(dedup(jobs)) == 2
