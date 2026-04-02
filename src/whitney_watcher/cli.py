from __future__ import annotations

import argparse
import json

from .config import Settings
from .pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Mt. Whitney permit watcher.")
    parser.add_argument(
        "--output-dir",
        help="Directory to write latest.json, history.json, and status.json",
    )
    args = parser.parse_args()

    settings = Settings.from_env(output_dir=args.output_dir)
    result = run_pipeline(settings)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
