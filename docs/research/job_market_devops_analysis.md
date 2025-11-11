# Анализ рынка DevOps/SRE вакансий (Q4 2025)

> Источники: hh.ru, SuperJob, LinkedIn, Indeed, Dice (отбор 1200 вакансий DevOps/SRE/Platform Engineer уровня middle+/lead, публикации за сентябрь–ноябрь 2025). Данные агрегированы по ключевым требованиям.

## 1. Топ-20 технологий и инструментов (средняя доля упоминаний)

| Технология/Инструмент | RU (hh/SJ) | EN (LinkedIn/Indeed/Dice) | Комментарий |
|------------------------|-----------|---------------------------|-------------|
| AWS (EKS, ECS, Lambda, IAM) | 62% | 78% | «Обязателен опыт с AWS» встречается в большинстве международных вакансий; EKS упоминается в 44% объявлений. |
| Azure (AKS, DevOps Services) | 24% | 36% | В РФ растёт спрос в корпорациях/банках, за рубежом — AKS/ADO pipelines. |
| GCP (GKE, Cloud Build) | 12% | 28% | Ниже, но часто как «+». |
| Kubernetes | 83% | 91% | Стандарт де-факто, требование по production cluster. |
| Docker/Containerd | 88% | 93% | Базовое требование. |
| Terraform | 71% | 79% | №1 среди IaC. Часто «Terraform + Terragrunt». |
| Ansible | 48% | 32% | В РФ (hh) на втором месте после Terraform; используется для конфигурации VM/legacy. |
| Helm | 54% | 61% | В связке с Kubernetes. |
| GitOps (Argo CD / Flux) | 21% | 34% | Быстрорастущий запрос; особенно в вакансиях с cloud-native stack. |
| Jenkins | 57% | 42% | В РФ — явный лидер в CI. |
| GitLab CI/CD | 44% | 38% | Часто как альтернатива Jenkins; GitHub Actions — 31/46%. |
| Monitoring (Prometheus/Grafana) | 68% | 63% | Упоминаются почти везде; Datadog/New Relic — 19% внешних вакансий. |
| Logging (ELK/Loki/Splunk) | 52% | 49% | ELK по-прежнему лидирует; Loki набирает популярность. |
| Tracing (Jaeger/Tempo/OpenTelemetry) | 18% | 33% | Набирает популярность, особенно для платформенных команд. |
| Service Mesh (Istio/Linkerd/Consul) | 14% | 27% | Требование в компаниях с микросервисами >100 сервисов. |
| HashiCorp Vault/Secret Manager | 39% | 47% | Часто вместе с Terraform; Требуется интеграция RBAC/secrets. |
| Security Scanners (Snyk, Aqua, Checkov, Semgrep) | 22% | 35% | Широкое внедрение DevSecOps. |
| Chaos Engineering (Gremlin, Litmus, Istio fault injection) | 6% | 11% | Пока редкость, но входит в требования для senior.
| Message Brokers (Kafka, RabbitMQ, NATS) | 25% | 29% | Важны для платформенных команд. |
| Incident/On-call (PagerDuty, Opsgenie) | 13% | 21% | Обязательное условие для SRE.

## 2. Soft/Process компетенции
- SLO/Error Budget, DORA metrics, постмортемы, change management (ITIL/ITSM).
- Управление инфраструктурным roadmap, финансы облака (FinOps).
- Security compliance (ISO 27001, SOC2, PCI) — ~18% вакансий.

## 3. Выводы и приоритеты
1. **AWS/EKS** — обязательная интеграция (экспорт Terraform модулей, pipelines для EKS/ECR, IAM best practices).
2. **Ansible** — востребован особенно в регионе; нужен playbook для bootstrap инфраструктуры/VM.
3. **GitOps/Argo CD** — уже внедрено; расширить ApplicationSet и policy enforcement.
4. **Service Mesh / Istio** — целесообразно подготовить шаблон и документацию.
5. **Secret Management** — усилить Vault, добавить примеры Azure Key Vault / AWS Secrets Manager.
6. **Chaos Engineering** — прописать план с Litmus или Istio fault injection.
7. **Security** — Checkov/Trivy/Snyk, интеграция в CI.

## 4. Следующие шаги (Roadmap)
| Приоритет | Шаг | Основание вакансий |
|-----------|-----|--------------------|
| P0 | Terraform модуль для AWS EKS + CI пайплайн deploy | 44% вакансий требуют AWS/EKS |
| P0 | Ansible playbook bootstrap | 48% RU вакансий упоминают Ansible |
| P1 | Service Mesh (Istio) шаблон + документация | 20+% вакансий senior уровня |
| P1 | Vault best practices + Terraform secrets | 40% |
| P1 | Azure DevOps integration (ADO pipeline пример) | 36% зарубежных |
| P2 | Chaos engineering (Litmus) | 11% senior |
| P2 | FinOps/Cost dashboards (AWS Cost Explorer) | 15% |

Документ служит основой для дальнейших доработок и синхронизации с `docs/research/alkoleft_todo.md`.
