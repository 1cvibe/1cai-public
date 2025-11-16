"""
Scenario Examples (experimental)
--------------------------------

Готовые примеры ScenarioPlan, показывающие, как использовать
типы из src/ai/scenario_hub.py для типовых сценариев:
- BA → Dev → QA поток для одной фичи;
- DR rehearsal для сервиса (например, vault).

Эти функции не подключены к API и нужны как reference/пример
для дальнейшей интеграции.
"""

from __future__ import annotations

from typing import List

from src.ai.scenario_hub import (
    AutonomyLevel,
    ScenarioExecutionReport,
    ScenarioGoal,
    ScenarioPlan,
    ScenarioRiskLevel,
    ScenarioStep,
    TrustScore,
)


def example_ba_dev_qa_scenario(feature_id: str) -> ScenarioPlan:
    """
    Пример сценария BA → Dev → QA для одной фичи.

    feature_id используется для привязки к артефактам (Jira/Confluence и т.д.).
    """

    goal = ScenarioGoal(
        id=f"ba-dev-qa-{feature_id}",
        title=f"BA → Dev → QA для фичи {feature_id}",
        description="Согласовать требования, реализовать фичу и покрыть её тестами.",
        constraints={"environment": "staging"},
        success_criteria=[
            "BA-спецификация согласована",
            "Изменения в конфигурации применены на staging",
            "Автотесты по фиче зелёные",
        ],
    )

    steps: List[ScenarioStep] = [
        ScenarioStep(
            id="ba-spec",
            title="Уточнение и фиксация требований BA",
            description="BA-агент готовит и согласует спецификацию по фиче.",
            risk_level=ScenarioRiskLevel.READ_ONLY,
            autonomy_required=AutonomyLevel.A1_SAFE_AUTOMATION,
            checks=[
                "BA-спецификация сохранена в Wiki/Docflow",
                "Есть явное согласие ответственного BA/PO",
            ],
            executor="agent:BA",
            metadata={"feature_id": feature_id},
        ),
        ScenarioStep(
            id="dev-impl",
            title="Реализация изменений разработчиком",
            description="Dev-агент предлагает изменения в конфигурации/коде.",
            risk_level=ScenarioRiskLevel.NON_PROD_CHANGE,
            autonomy_required=AutonomyLevel.A2_NON_PROD_CHANGES,
            checks=[
                "Все изменения применены только на test/staging",
                "Проверка статических анализаторов зелёная",
            ],
            executor="agent:Dev",
            metadata={"feature_id": feature_id},
        ),
        ScenarioStep(
            id="qa-coverage",
            title="Покрытие тестами и прогон E2E",
            description="QA-агент генерирует/обновляет тесты и запускает E2E.",
            risk_level=ScenarioRiskLevel.NON_PROD_CHANGE,
            autonomy_required=AutonomyLevel.A2_NON_PROD_CHANGES,
            checks=[
                "Все релевантные тесты по фиче зелёные",
                "E2E по критическим путям (API → AI → Response) прошли",
            ],
            executor="agent:QA",
            metadata={"feature_id": feature_id},
        ),
    ]

    return ScenarioPlan(
        id=f"plan-ba-dev-qa-{feature_id}",
        goal=goal,
        steps=steps,
        required_autonomy=AutonomyLevel.A2_NON_PROD_CHANGES,
        overall_risk=ScenarioRiskLevel.NON_PROD_CHANGE,
        context={"kind": "ba-dev-qa", "feature_id": feature_id},
    )


def example_dr_rehearsal_scenario(service_name: str) -> ScenarioPlan:
    """
    Пример сценария DR rehearsal для сервиса (например, vault).
    """

    goal = ScenarioGoal(
        id=f"dr-{service_name}",
        title=f"DR rehearsal для сервиса {service_name}",
        description="Отработать сценарий отказа и восстановления сервиса.",
        constraints={"environment": "staging"},
        success_criteria=[
            "DR-плейбук выполнен без критических ошибок",
            "Постмортем-черновик создан и заполнен",
        ],
    )

    steps: List[ScenarioStep] = [
        ScenarioStep(
            id="dr-plan-validate",
            title="Проверка актуальности DR-плана",
            description="Проверить, что DR-план и артефакты для сервиса актуальны.",
            risk_level=ScenarioRiskLevel.READ_ONLY,
            autonomy_required=AutonomyLevel.A1_SAFE_AUTOMATION,
            checks=[
                "DR-план найден для сервиса",
                "Последний DR-отчёт учтён в плане",
            ],
            executor="agent:DevOps",
            metadata={"service": service_name},
        ),
        ScenarioStep(
            id="dr-simulate",
            title="Симуляция отказа и восстановления",
            description="Выполнить DR rehearsal в staging по плейбуку.",
            risk_level=ScenarioRiskLevel.NON_PROD_CHANGE,
            autonomy_required=AutonomyLevel.A2_NON_PROD_CHANGES,
            checks=[
                "Все шаги DR-плейбука выполнены в staging",
                "Мониторинг/алерты сработали ожидаемым образом",
            ],
            executor="playbook:dr",
            metadata={"service": service_name},
        ),
        ScenarioStep(
            id="dr-postmortem",
            title="Генерация и доработка постмортема",
            description="Сгенерировать черновик постмортема и доработать его.",
            risk_level=ScenarioRiskLevel.READ_ONLY,
            autonomy_required=AutonomyLevel.A1_SAFE_AUTOMATION,
            checks=[
                "Постмортем-черновик создан",
                "Ключевые выводы и follow-up задачи зафиксированы",
            ],
            executor="agent:DR",
            metadata={"service": service_name},
        ),
    ]

    return ScenarioPlan(
        id=f"plan-dr-{service_name}",
        goal=goal,
        steps=steps,
        required_autonomy=AutonomyLevel.A2_NON_PROD_CHANGES,
        overall_risk=ScenarioRiskLevel.NON_PROD_CHANGE,
        context={"kind": "dr-rehearsal", "service": service_name},
    )


def example_empty_execution_report(plan: ScenarioPlan) -> ScenarioExecutionReport:
    """
    Пример "пустого" отчёта о выполнении сценария с базовым trust-score.

    Нужен как reference того, что пользователь увидит в будущем.
    """

    trust = TrustScore(score=0.5, level="medium", reasons=["Пример-заглушка, без реальных метрик"])

    return ScenarioExecutionReport(
        scenario_id=plan.id,
        goal=plan.goal,
        trust_before=trust,
        trust_after=trust,
        summary="Пример отчёта: здесь будет краткое резюме выполнения сценария.",
        timeline=["Сценарий ещё не был выполнен (пример-заглушка)."],
        artifacts={},
    )


