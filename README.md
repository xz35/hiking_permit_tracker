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


