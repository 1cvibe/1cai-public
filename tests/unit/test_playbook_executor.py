"""
Tests for playbook_executor (experimental).
"""

from pathlib import Path

from src.ai.playbook_executor import (
    dry_run_playbook,
    dry_run_playbook_to_dict,
    load_playbook,
)
from src.ai.scenario_hub import ScenarioPlan


def test_load_playbook_ba_dev_qa(tmp_path: Path) -> None:
    """YAML-плейбук BA→Dev→QA должен загружаться в ScenarioPlan."""
    # Используем реальный файл из playbooks
    playbook_path = Path("playbooks/ba_dev_qa_example.yaml")
    plan = load_playbook(playbook_path)

    assert isinstance(plan, ScenarioPlan)
    assert plan.goal.title.startswith("BA → Dev → QA")
    assert len(plan.steps) == 3


def test_dry_run_playbook_returns_report_dict() -> None:
    """dry_run_playbook_to_dict должен возвращать dict с ключевыми полями."""
    playbook_path = Path("playbooks/dr_vault_example.yaml")
    report_dict = dry_run_playbook_to_dict(playbook_path)

    assert isinstance(report_dict, dict)
    assert report_dict.get("scenario_id") == "plan-dr-vault"
    assert "summary" in report_dict
    assert "timeline" in report_dict


