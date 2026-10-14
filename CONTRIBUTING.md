# Contributing

This board is curated. The main way to contribute is to **add a vetted company** to the
allowlist. That is a single-file change to `config/companies.yaml`.

## Add a company

1. Find the company's job board and identify which ATS it uses and the board identifier:

   | ATS | Example board URL | `identifier` to use |
   |---|---|---|
   | `ashby` | `https://jobs.ashbyhq.com/horizon3ai` | `horizon3ai` |
   | `greenhouse` | `https://boards.greenhouse.io/wiz` | `wiz` |
   | `lever` | `https://jobs.lever.co/chainguard` | `chainguard` |
   | `rippling` | `https://ats.rippling.com/acme/jobs` | `acme` |
   | `gem` | `https://jobs.gem.com/acme` | `acme` |

   Workday is **not** supported.

2. Add an entry to `config/companies.yaml`:

   ```yaml
   - name: "Acme Security"
     ats: greenhouse
     identifier: "acme"
     industry: [cybersecurity, cspm]   # one or more of: cybersecurity, deftech, cspm, finops, grc
     tier: standard                     # "featured" is reserved; default to "standard"
     homepage: "https://acme.example"   # optional
   ```

3. Open a pull request. CI runs `ruff` and `pytest`; `tests/test_config.py` validates that
   your entry has a known `ats`, a controlled-vocabulary `industry`, a valid `tier`, and a
   non-empty `identifier`. Fix any failures and the next daily scrape picks it up.

## Add or tune a role

Roles and the keywords that match them live in `config/roles.yaml`. If a role you care about
is being missed (or a wrong title is matching), adjust `include_keywords` / `exclude_keywords`
and add a case to `tests/test_matching.py` so it stays correct.

## Add a new ATS adapter

1. Create `scraper/adapters/<ats>.py` subclassing `ATSAdapter` in `base.py` with `fetch()`
   and `normalize()`.
2. Register it in `scraper/adapters/registry.py`.
3. Add a recorded sample response to `tests/fixtures/<ats>_sample.json` and a test in
   `tests/test_adapters.py`.

## Local checks before a PR

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check .
pytest
```
