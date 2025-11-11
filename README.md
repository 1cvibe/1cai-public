# 🤖 1C AI Stack

> Платформа DevOps + AI tooling для 1C:Enterprise: от парсинга конфигураций и MCP-интеграций до полноценных CI/CD, FinOps и процессов эксплуатации.

| Что внутри | Где смотреть |
|------------|--------------|
| **Dev & AI tooling** — MCP сервер, bsl-language-server, spec-driven workflow | `src/`, `docs/06-features/`, `scripts/research/`, `templates/` |
| **Инфраструктура** — Kubernetes/Helm, Argo CD, Linkerd, Vault, Terraform | `infrastructure/`, `docs/ops/**`, `scripts/service_mesh/linkerd/` |
| **Надёжность** — on-call, DR rehearsal, chaos, runbooks, SLO | `docs/process/`, `docs/runbooks/`, `observability/`, GitHub Actions |
| **Security & FinOps** — Rego policies, секреты, фоновые отчёты | `policy/`, `scripts/security/`, `scripts/secrets/`, `scripts/finops/` |
| **Документация** — архитектура, ADR, исследования, TODO | `docs/architecture/`, `docs/research/`, `CHANGELOG.md`, `docs/README.md` |

**Быстрые ссылки**
- 📚 [Docs index](docs/README.md) — навигация по документации
- 🧭 [Roadmap / TODO](docs/research/alkoleft_todo.md) · [Constitution](docs/research/constitution.md)
- 🔁 [Runbooks & DR](docs/runbooks/dr_rehearsal_plan.md) · [On-call](docs/process/oncall_rotations.md)
- ✅ [Changelog](CHANGELOG.md) · [Recent commits](https://github.com/DmitrL-dev/1cai/commits/main)

---

## 🚀 Быстрый старт

### Локальное окружение
1. Установите Python 3.11, Docker, Docker Compose → см. [`docs/setup/python_311.md`](docs/setup/python_311.md).  
2. Проверьте окружение: `make check-runtime`.
3. Поднимите стэк:
   ```bash
   make docker-up          # базы данных, брокеры, Neo4j, Qdrant
   make migrate            # первичная миграция данных
   make servers            # Graph API + MCP server
   make bsl-ls-up          # bsl-language-server (AST)
   make bsl-ls-check       # health-check AST сервиса
   ```
   > На Windows используйте аналогичные скрипты из `scripts/windows/`.
4. Подключите IDE:
   - MCP: Cursor / VS Code → `http://localhost:6001/mcp`
   - EDT плагин: сборка в `edt-plugin/`, инструкции внутри каталога.

### Облако и GitOps
- `make gitops-apply` — применить Argo CD манифесты (1cai-stack, observability, linkerd).
- `make vault-csi-apply` — настроить Vault + CSI.
- `make linkerd-install`, `make linkerd-rotate-certs` — сервис-меш и ротация сертификатов.
- `make finops-slack` — разовая отправка FinOps отчётов (Slack/Teams).
- Подробный план — `docs/ops/devops_platform.md`, `docs/ops/gitops.md`.

---

## 🌟 Feature Highlights

### Конфигурационный анализ
- EDT-parser: статистика объектов, граф зависимостей, best practices.
- Документация из парсинга: [`scripts/analysis/generate_documentation.py`](scripts/analysis/generate_documentation.py).
- Гайды: [`docs/06-features/EDT_PARSER_GUIDE.md`](docs/06-features/EDT_PARSER_GUIDE.md), [`docs/06-features/ML_DATASET_GENERATOR_GUIDE.md`](docs/06-features/ML_DATASET_GENERATOR_GUIDE.md).

### Автоматизация и оркестрация
- MCP-сервер (`src/ai/mcp_server.py`) с инструментами для поиска метаданных, генерации кода, запуска тестов.
- Интеграция с внешними MCP (platform context, тест-раннеры).
- Workflow запуска анализа: `make docker-up` → `make migrate` → `make generate-docs`.

### Документация и архитектура
- Structurizr DSL + PlantUML (C4, динамика, операции, безопасность).
- ADR-реестр (`docs/architecture/adr/`).
- Автоматический рендер диаграмм (`make render-uml`, GitHub Actions).

### AI & MCP tooling
- MCP server, bsl-language-server, spec-driven workflow (см. ниже).
- Создание задач и планов на основе спецификаций (совместимо с GitHub Spec Kit — см. анализ).

---

## 🤖 AI Tooling & Automation
- **bsl-language-server**: сервис AST, make-таргеты `bsl-ls-*`, health-check, fallback в `BSLASTParser`.
  - План интеграции: [`docs/research/bsl_language_server_plan.md`](docs/research/bsl_language_server_plan.md).
  - Детальный гайд: [`docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`](docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md).
- **Spec-driven development** (по мотивам [github/spec-kit](https://github.com/github/spec-kit)):
  - Анализ и предложения: [`docs/research/spec_kit_analysis.md`](docs/research/spec_kit_analysis.md).
  - Конституция правил проверки: [`docs/research/constitution.md`](docs/research/constitution.md).
  - Шаблоны и CLI: `templates/`, `scripts/research/init_feature.py`, make-таргеты `feature-init` и `feature-validate`.
- **MCP инструменты**: поиск метаданных, генерация кода, запуск тестов.
- **Automation scripts**: `scripts/context/export_platform_context.py`, `scripts/context/generate_docs.py`, `scripts/docs/create_adr.py`.
- **Monitoring automation**: `scripts/monitoring/github_monitor.py` + workflow `github-monitor.yml` — ежедневный snapshot зависимостей.
- **Release automation**: `scripts/release/create_release.py`, make `release-*`, workflow `release.yml` — генерация заметок, тегов, публикация релизов.
- **Quality metrics**: `scripts/metrics/collect_dora.py`, workflow `dora-metrics.yml` — еженедельные DORA-показатели.

---

## 🏛 Architecture & Documentation
- **High-Level Design**: [`docs/architecture/01-high-level-design.md`](docs/architecture/01-high-level-design.md)
- **Structurizr DSL**: [`docs/architecture/c4/workspace.dsl`](docs/architecture/c4/workspace.dsl)
- **Диаграммы (PNG)**: `docs/architecture/uml/**` (C4, data, dynamics, operations, security)
- **ADR**: `docs/architecture/adr/`, см. `ADR-0001… ADR-0005`
- **Automated render**: `make render-uml`, workflow `.github/workflows/uml-render-check.yml`

---

## ✅ Testing & Quality
- **YAxUnit + EDT runner** (в планах расширения через репозитории BIA: yaxunit, edt-test-runner).
- `make test-bsl` (см. `scripts/tests/run_bsl_tests.py`).
- Статический анализ, best practices, проверка зависимостей.
- Сторожевые скрипты: `scripts/audit/*`, `scripts/analysis/*`.
- Справочник по тестам: [`docs/06-features/TESTING_GUIDE.md`](docs/06-features/TESTING_GUIDE.md).
- Smoke проверки: `make smoke-tests`, CI job `smoke-tests`, артефакты pytest (`output/test-results`).
- Наблюдаемость: `/metrics` (Prometheus), SLO/Runbooks (`docs/observability/SLO.md`, `docs/runbooks/alert_slo_runbook.md`), автоматические отчёты DORA.
- **Secret scanning & Security**
  - Workflows `secret-scan.yml` (Gitleaks) и `trufflehog.yml` (Trufflehog) — регулярное сканирование репозитория на утечки токенов.
  - Policy-as-code: `policy/` (Rego) + `scripts/security/run_policy_checks.sh` (Conftest Kubernetes + Terraform, Semgrep, Checkov/Trivy) → `make policy-check` / CI стадии.
  - Infrastructure scanners: `scripts/security/run_checkov.sh` (Checkov + Trivy) подключён в Jenkins/GitLab/Azure pipeline.
  - GitOps: `infrastructure/argocd/`, `scripts/gitops/*.sh`, make `gitops-apply`, `gitops-sync`.
  - Cloud readiness: `infrastructure/terraform/aws-eks/`, `infrastructure/terraform/azure-aks/`, Ansible bootstrap (`infrastructure/ansible/`).
  - Secrets: `scripts/secrets/aws_sync_to_vault.py`, `scripts/secrets/azure_sync_to_vault.py`, `scripts/secrets/apply_vault_csi.sh`.
  - Self-control: `scripts/checklists/preflight.sh`, make `preflight`.
- **FinOps**
  - Скрипты `scripts/finops/aws_cost_*`, `scripts/finops/azure_cost_to_slack.py`, `scripts/finops/aws_budget_check.py`, `scripts/finops/azure_budget_check.py`, `scripts/finops/teams_notify.py` — отчёты, бюджеты и Slack/Teams уведомления; дашборд `observability/grafana/dashboards/finops_cost.json`.
  - Workflow `.github/workflows/finops-report.yml` — ежедневный отчёт.
  - DR rehearsal: `docs/runbooks/dr_rehearsal_plan.md`, script `scripts/runbooks/dr_rehearsal_runner.py`, workflow `dr-rehearsal.yml`.

---

## 🔗 Integrations
- **IDE**: MCP сервер (Cursor/VS Code), EDT плагин (`edt-plugin/`).
- **Внешние инструменты**: alkoleft платформенные сервисы, yaxunit, GitHub Spec Kit (в работе).
- **ITS Scraper**: асинхронный сбор статей, версионирование (`integrations/its_scraper`).
- **Telegram / n8n / OCR**: дополнительные модули в `src/` и `integrations/`.

---

## 📚 Documentation Hub

Полный индекс: [`docs/README.md`](docs/README.md). Ключевые разделы:
- **Setup & Runtime**
  - [`docs/setup/python_311.md`](docs/setup/python_311.md) — установка Python 3.11 и проверка среды.
  - `scripts/setup/check_runtime.py` + `make check-runtime` — автоматическая проверка версии Python.
- **Infrastructure & DevOps**
  - [`docs/ops/devops_platform.md`](docs/ops/devops_platform.md) — стратегия DevOps-платформы.
  - [`docs/ops/gitops.md`](docs/ops/gitops.md) — GitOps с Argo CD.
  - [`docs/ops/ansible.md`](docs/ops/ansible.md) — bootstrap инфраструктуры Ansible.
  - [`docs/ops/service_mesh.md`](docs/ops/service_mesh.md) — Istio blueprint.
  - [`infrastructure/service-mesh/linkerd`](infrastructure/service-mesh/linkerd) — альтернативный service mesh.
  - [`docs/ops/chaos_engineering.md`](docs/ops/chaos_engineering.md) — Litmus chaos сценарии.
  - [`docs/ops/vault.md`](docs/ops/vault.md) — Vault & secret management.
  - [`docs/ops/azure_devops.md`](docs/ops/azure_devops.md) — Azure DevOps pipeline.
  - [`docs/ops/finops.md`](docs/ops/finops.md) — FinOps и контроль затрат (`make finops-slack`, workflow `finops-report.yml`).
  - [`docs/ops/self_control.md`](docs/ops/self_control.md) — самоконтроль инженера (`make preflight`).
  - `infrastructure/kind/cluster.yaml` — локальный Kubernetes.
  - `infrastructure/helm/1cai-stack` — Helm chart приложения.
  - `infrastructure/helm/observability-stack` — Prometheus/Loki/Tempo/Grafana/OTEL.
  - `infrastructure/service-mesh/istio` — IstioOperator профиль.
  - `infrastructure/chaos/litmus` — Litmus Chaos эксперименты.
  - `infrastructure/argocd/` — manifests для Argo CD (GitOps, Linkerd ApplicationSet).
  - `infrastructure/terraform` — Terraform конфигурация для Helm релиза.
  - `infrastructure/terraform/aws-eks` — Terraform модуль EKS (AWS).
  - `infrastructure/terraform/azure-aks` — Terraform модуль AKS (Azure).
  - `infrastructure/terraform/azure-keyvault` — Terraform модуль Key Vault.
  - `scripts/service_mesh/linkerd/bootstrap_certs.sh` — генерация trust anchors/issuer.
  - `scripts/service_mesh/linkerd/` — bootstrap/rotate certs, managed identity, CI smoke (`linkerd-smoke.yml`).
  - Make: `linkerd-install`, `linkerd-rotate-certs`, `linkerd-smoke`.
  - `infrastructure/azure/azure-pipelines.yml` — Azure DevOps pipeline.
  - `infrastructure/vault/` — политики, скрипты, SecretProviderClass для Vault (`make vault-csi-apply`, sync скрипты).
  - `scripts/secrets/aws_sync_to_vault.py` — синхронизация AWS Secrets Manager → Vault.
  - `infrastructure/jenkins/Jenkinsfile`, `infrastructure/gitlab/.gitlab-ci.yml` — многостадийные pipeline.
  - [`docs/security/policy_as_code.md`](docs/security/policy_as_code.md) — Rego-политики, Conftest, Semgrep.
- **Feature Guides**
  - [`docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`](docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md) — запуск и диагностика bsl-language-server, fallback сценарии.
  - [`docs/06-features/MCP_SERVER_GUIDE.md`](docs/06-features/MCP_SERVER_GUIDE.md) — эндпоинты MCP, переменные окружения, troubleshooting.
  - [`docs/06-features/TESTING_GUIDE.md`](docs/06-features/TESTING_GUIDE.md) — матрица тестов, команды pytest/k6, CI-джобы.
  - [`docs/06-features/EDT_PARSER_GUIDE.md`](docs/06-features/EDT_PARSER_GUIDE.md) — разбор EDT XML, метрики и сценарии анализа.
  - [`docs/06-features/ML_DATASET_GENERATOR_GUIDE.md`](docs/06-features/ML_DATASET_GENERATOR_GUIDE.md) — подготовка ML датасетов и пайплайн обучения.
- **Operations & Tooling**
  - [`docs/scripts/README.md`](docs/scripts/README.md) — карта CLI/скриптов, spec-driven workflow, Windows альтернативы, release tooling.
- **Observability**
  - [`docs/observability/SLO.md`](docs/observability/SLO.md) — целевые показатели доступности и латентности.
  - [`docs/runbooks/alert_slo_runbook.md`](docs/runbooks/alert_slo_runbook.md) — действия при нарушении SLO.
  - [`docs/status/dora_history.md`](docs/status/dora_history.md) — автоматическая история DORA метрик (weekly).
  - Workflow `observability.yml` — напоминание об интеграции SLO/метрик.
  - `make observability-up` → локальный Prometheus/Grafana/Alertmanager стек (см. `observability/docker-compose.observability.yml`), проверяется CI (`observability-test.yml`).
  - `make helm-observability` → установка Kubernetes-стека наблюдаемости (Prometheus + Loki + Tempo + Grafana + OTEL) из `infrastructure/helm/observability-stack`.
  - Alertmanager конфигурация: `observability/alertmanager.yml` + правила `observability/alerts.yml` (Telegram; требуются `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
  - Telegram оповещения: workflow `telegram-alert.yaml` (требует `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
- **Architecture**
  - [`docs/architecture/README.md`](docs/architecture/README.md) — обзор C4, операции и ссылки на ADR.
  - [`docs/architecture/adr/`](docs/architecture/adr/) — реестр решений, статусы и история изменений.
  - [`docs/architecture/uml/`](docs/architecture/uml/) — PlantUML диаграммы (структура, потоки, безопасность).
- **Parsers & Documentation**
  - [`docs/06-features/EDT_PARSER_GUIDE.md`](docs/06-features/EDT_PARSER_GUIDE.md) — парсинг конфигураций, метаданные.
  - [`docs/06-features/ML_DATASET_GENERATOR_GUIDE.md`](docs/06-features/ML_DATASET_GENERATOR_GUIDE.md) — генерация обучающих наборов.
  - [`docs/06-features/ITS_SCRAPER.md`](docs/03-integrations/ITS_SCRAPER.md) — сбор данных ITS и обновление базы знаний.
- **Research & Plans**
  - [`docs/research/README_LOCAL.md`](docs/research/README_LOCAL.md) — ежедневные статусы и подготовка публикации.
  - [`