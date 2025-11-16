"""
Run Scenario Playbook (experimental)
------------------------------------

Простой CLI-скрипт для dry-run YAML-плейбуков Scenario Hub.

Пример:

    python scripts/runbooks/run_playbook.py playbooks/ba_dev_qa_example.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ai.playbook_executor import dry_run_playbook_to_dict


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run Scenario Hub playbook (experimental)")
    parser.add_argument("path", type=str, help="Путь к YAML-плейбуку (например, playbooks/ba_dev_qa_example.yaml)")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.is_file():
        raise SystemExit(f"Playbook file not found: {path}")

    report = dry_run_playbook_to_dict(path)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


