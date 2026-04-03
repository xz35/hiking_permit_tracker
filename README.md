# Mt. Whitney Permit Watcher

A small watcher for Mt. Whitney permit availability. It polls Recreation.gov data, writes static JSON snapshots, and powers a lightweight dashboard for monitoring changes over time.

This repository contains:

- a Python watcher
- a static dashboard
- a scheduled GitHub Actions workflow for polling and publishing data
The project is intended for monitoring and alerting only. It does not automate booking.

## Development

Python 3.11+ is required.

Example:

```powershell
python -m pip install -e .
python -m whitney_watcher.cli --output-dir build/pages
```

The dashboard is static and can be served from the `dashboard/` directory or deployed as a simple static site.
