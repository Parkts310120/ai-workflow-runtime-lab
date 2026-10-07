from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime_lab.ledger import InMemoryEventLedger, JsonlEventLedger
from runtime_lab.scenario import run_scenario


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic bounded workflow scenario.")
    parser.add_argument("scenario", type=Path, help="Path to a synthetic scenario JSON file.")
    parser.add_argument("--ledger", type=Path, help="Optional append-only JSONL event ledger path.")
    args = parser.parse_args()

    ledger = JsonlEventLedger(args.ledger) if args.ledger else InMemoryEventLedger()
    summary = run_scenario(args.scenario, ledger=ledger)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["matches_expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
