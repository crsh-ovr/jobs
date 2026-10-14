# Shane's Cybersecurity Job List

A curated, community-run job board for cybersecurity and adjacent sectors. It tracks a
hand-picked allowlist of vetted companies and surfaces specific roles across all levels
(IC through VP) using the companies' own public job-board APIs. A scraper runs daily via
GitHub Actions and the site is served as static files from GitHub Pages.

> **Not affiliated with any employer.** This is a personal project by Shane Quinlan, run
> for the community. It is not affiliated with, endorsed by, or operated by Horizon3.ai or
> any company listed here. Horizon3.ai roles are featured because this is Shane's personal
> list, not because of any official relationship.

Companion career guide: **[shane-tips-for-jobs](https://shane-tips-for-jobs.lovable.app/)**

## What it tracks

**Role umbrellas** (mirrors the career guide):

- **Product** — Product Manager, Technical Program Manager
- **Design** — Product Designer
- **Engineering** — Full Stack, Frontend, DevOps / CI-CD / DevEx, Agentic / AI Engineer
- **GTM / Revenue** — Recruiter, Technical Recruiter

All levels are kept and tagged: intern, junior, mid, senior, staff, principal, lead,
manager, director, VP.

**Industries:** cybersecurity, deftech, cspm, finops, grc.

**Supported ATS platforms:** Ashby, Greenhouse, Lever, Rippling, Gem. (Getro is best-effort
and off by default; Workday is intentionally not supported.)

## How it works

```
config/*.yaml  →  python -m scraper.main  →  data/jobs.json  →  site/ (GitHub Pages)
   allowlist         daily GitHub Action        committed            static, no build
```

The scraper reads the company allowlist, fetches each company's public job-board JSON,
normalizes every posting to a common schema, keeps only postings that match a target role,
tags level/umbrella/industry, de-duplicates, and writes `data/jobs.json`. The static site
reads that file directly in the browser and filters client-side.

## Add a company

The whole point is curation, so adding a company is a one-file pull request. See
[CONTRIBUTING.md](CONTRIBUTING.md) — you edit `config/companies.yaml`, CI validates it, and
the next daily run picks it up.

## Run locally

```bash
pip install -r requirements.txt
python -m scraper.main            # writes data/jobs.json + data/meta.json
python -m http.server 8000        # then open http://localhost:8000/site/
```

## Develop

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

## License

[MIT](LICENSE).
