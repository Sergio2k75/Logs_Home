# Logs Home — Playwright e2e tests

End-to-end browser tests for the Logs Home UI, plus shared helpers used to capture the README screenshot. Tests use **Python Playwright** via **pytest** and **pytest-playwright** (no Node.js).

## Purpose

- Verify the SPA loads and shows the app version
- Cover source add / select / delete flows
- Cover log tailing, line-count control, and highlight/presets
- Share server + screenshot logic with `scripts/capture_screenshot.py`

## Prerequisites

From the repo root, with a virtualenv activated:

```bash
pip install -r requirements-dev.txt
playwright install chromium
```

Runtime deps (FastAPI / uvicorn) are pulled in via `requirements-dev.txt`.

## How to run

```bash
# All e2e tests (default; screenshot marker is excluded)
pytest

# One file
pytest tests/e2e/test_sources.py

# One test
pytest tests/e2e/test_viewer.py::test_highlight_err_lines

# Headed browser
pytest --headed

# Playwright inspector / debug
PWDEBUG=1 pytest tests/e2e/test_smoke.py --headed
```

Failed runs keep a Playwright trace (`--tracing retain-on-failure` in `pytest.ini`). Open a trace with:

```bash
playwright show-trace test-results/**/trace.zip
```

## How fixtures work

| Fixture | Scope | Role |
|---------|-------|------|
| `app_server` | session | Starts uvicorn with a temp `LOGS_HOME_DATA_DIR` on a free port |
| `base_url` | session | `http://127.0.0.1:<port>` for that server |
| `clear_sources` | autouse (e2e) | Deletes all sources via the API before/after each test |
| `home` | function | `HomePage` helper bound to the Playwright `page` |
| `sample_log_path` | session | Absolute path to `docs/fixtures/sample.log` |
| `browser_context_args` | session | Viewport `1280x800` (matches README screenshot) |

The live server is **isolated** from your real `data/sources.json`. Do not point tests at production log paths.

## Layout

```
tests/
  README.md                 # this file
  conftest.py               # fixtures
  helpers/
    server.py               # start/stop uvicorn
    screenshot.py           # README PNG + marker update
    home.py                 # HomePage helpers (add/select/delete/highlight)
  e2e/
    test_smoke.py
    test_sources.py
    test_viewer.py
  screenshots/
    test_readme_screenshot.py   # optional; deselected by default
```

## README screenshots

Preferred CLI (also used by the git pre-commit hook):

```bash
python scripts/capture_screenshot.py
```

That script calls `tests.helpers.screenshot.capture_readme_screenshot()`, which:

1. Starts uvicorn on port **8765** with `docs/fixtures/.screenshot-data/`
2. Seeds a source from `docs/fixtures/sample.log`
3. Opens Chromium, enables ERR highlighting, writes `docs/screenshot.png`
4. Refreshes the `<!-- APP_SCREENSHOT -->` block in the root README

Optional pytest entrypoint (deselected by default via `-m "not screenshot"`):

```bash
pytest -m screenshot
```

## What is not covered

- **Native file picker** (`#browse-btn` / `POST /api/pick-file`) — requires a desktop OS dialog; unsuitable for headless CI/local e2e
- Backend unit tests for `tail.py` / `sources_store.py` (out of scope for this suite)

## Conventions

- Prefer stable DOM ids already in the UI (`#source-form`, `#log-output`, …)
- Use `HomePage` helpers for repeated flows; keep assertions in the test
- Prefer Playwright `expect(...)` over fixed sleeps
- Mark new browser tests with `@pytest.mark.e2e`
- Put new UI flows under `tests/e2e/`; keep capture logic in `tests/helpers/`
- Name tests `test_<behavior>` so failures read clearly in the report
