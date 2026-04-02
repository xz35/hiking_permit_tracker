# Mt. Whitney Permit Watcher

A personal Mt. Whitney permit watcher built around the live Recreation.gov availability API for Whitney permits. It polls for July/August 2026 availability, highlights your preferred overnight dates, sends Gmail alerts when `2+` overnight permits open on target days, and publishes JSON for a lightweight dashboard.

## What this includes

- Python watcher with:
  - live fetch from the official Whitney availability endpoint
  - normalization into a stable JSON schema
  - match detection for overnight permits on Thursday/Friday/Saturday in July/August 2026
  - deduplicated email alerts when capacity crosses to `2+`
  - static JSON outputs for dashboard consumption
- Static dashboard for Vercel:
  - calendar view for July and August 2026
  - overnight/day-use filtering
  - visual emphasis for `2+` overnight matches
  - no build step required
- GitHub Actions workflow:
  - runs every 5 minutes
  - publishes generated JSON to GitHub Pages
  - optionally sends Gmail alerts

## Verified live API shape

The implementation uses the official Recreation.gov Whitney availability endpoint:

`https://www.recreation.gov/api/permitinyo/445860/availability?start_date=2026-07-01&end_date=2026-07-31&commercial_acct=false`

The live API currently returns a JSON payload keyed by date, then by permit code. The watcher maps permit codes using the official quota counts on the Whitney permit page:

- `166` -> `overnight` (quota 60)
- `406` -> `day_use` (quota 100)

This mapping is an inference based on the live endpoint totals matching the official Mt. Whitney quota description on Recreation.gov.

## Repository layout

- `src/whitney_watcher/`: backend watcher code
- `tests/`: unit tests
- `dashboard/`: static frontend for Vercel
- `.github/workflows/poll_whitney.yml`: scheduled polling and publish workflow

## Local backend usage

You will need Python 3.11+ installed locally to run the watcher on your machine.

Example:

```powershell
python -m pip install -e .
python -m whitney_watcher.cli --output-dir build/pages
```

Useful environment variables:

- `WHITNEY_MONTHS=2026-07,2026-08`
- `WHITNEY_ALERT_THRESHOLD=2`
- `WHITNEY_EMAIL_ENABLED=true`
- `WHITNEY_GMAIL_USERNAME=youraddress@gmail.com`
- `WHITNEY_GMAIL_APP_PASSWORD=your-16-char-app-password`
- `WHITNEY_EMAIL_TO=youraddress@gmail.com`
- `WHITNEY_PREVIOUS_SNAPSHOT_URL=https://<user>.github.io/<repo>/latest.json`
- `WHITNEY_PREVIOUS_HISTORY_URL=https://<user>.github.io/<repo>/history.json`
- `WHITNEY_DATA_PUBLIC_URL=https://<user>.github.io/<repo>/latest.json`

You can start from `.env.example` when you wire up credentials later.

## Dashboard usage

The dashboard is a static site with no framework build step. For local preview it reads `dashboard/sample-data/latest.json`.

For production, set `dashboard/config.js` to point at your GitHub Pages JSON, for example:

```js
window.WHITNEY_CONFIG = {
  dataUrl: "https://<user>.github.io/<repo>/latest.json",
  statusUrl: "https://<user>.github.io/<repo>/status.json",
};
```

Then deploy the `dashboard/` directory to Vercel as a static site.

## GitHub setup after code is in place

You can do the code first and accounts later. When you are ready to deploy:

1. Create a GitHub repository and push this project.
2. Enable GitHub Pages using GitHub Actions as the source.
3. Add repository secrets:
   - `WHITNEY_GMAIL_USERNAME`
   - `WHITNEY_GMAIL_APP_PASSWORD`
   - `WHITNEY_EMAIL_TO`
4. Optionally add repository variables if you want to override defaults.
5. Let the `poll_whitney` workflow publish `latest.json`, `history.json`, and `status.json` to GitHub Pages.

## Gmail setup

The alerting implementation assumes Gmail SMTP with an app password.

1. Enable 2-Step Verification on your Google account.
2. Generate an App Password for Mail.
3. Store that value in `WHITNEY_GMAIL_APP_PASSWORD`.

## Vercel setup

You can do this after the code is finished.

1. Create a Vercel project pointing at this repository.
2. Set the root directory to `dashboard`.
3. Configure `config.js` to read from your GitHub Pages JSON URL.
4. Deploy. The site can remain unlisted with an obscure URL.

## Notes

- The backend is intentionally stdlib-first so the scheduled job stays simple.
- The dashboard is intentionally static to avoid needing Node locally.
- Auto-booking is not implemented in V1.
- I could not run the tests locally in this workspace because Python is not installed on this machine yet.
