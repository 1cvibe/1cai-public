# Alert & SLO Runbook

> Обновлено: 10 ноября 2025

## 1. Назначение

Runbook описывает действия при нарушении SLO/алертов (доступность API, MCP, Marketplace). Используется дежурным инженером/on-call.

## 2. Каналы оповещения

- GitHub Actions (workflow `dora-metrics`, `github-monitor`, `smoke-tests`).
- Slack/Telegram — TODO (создать канал `#alerts`).
- Email — резерв (см. `docs/SUPPORT.md`).

## 3. Общая схема реагирования

1. Подтвердите, что алерт не false positive (проверить smoke-tests, health-check вручную).
2. Зафиксируйте время старта инцидента.
3. Создайте issue `incident-YYYYMMDD` в репозитории (label `incident`).
4. Отметьте Error Budget (см. `docs/observability/SLO.md`).
5. Действуйте по чек-листу сервиса (см. ниже).

## 4. Graph API / FastAPI

- Проверить `/health` локально и через публичный endpoint.
- Просмотреть логи `app.log`, стек-трейсы.
- Перезапустить сервис (`make servers` или systemd). Если причина не ясна — не откатывать, сначала снять метрики.
- После восстановления зафиксировать MTTR в issue и DORA-отчёте.

## 5. MCP Server

- Smoke-tests включают compile/spec; если MCP недоступен — проверить логи `src/ai/mcp_server.py`.
- Проверить внешние MCP (`MCP_BSL_CONTEXT_BASE_URL`, `MCP_BSL_TEST_RUNNER_BASE_URL`).
- При необходимости — переключить на fallback (regex/локальные инструменты).

## 6. Marketplace API

- Проверить `marketplace_repo` (Redis, MinIO/S3, PostgreSQL).
- Выполнить `python scripts/monitoring/github_monitor.py` — убедиться, что нет зависимостей, требующих обновления.
- При инциденте с данными — следовать процедуре backup/restore (`scripts/backup-restore.sh`).

## 7. Postmortem

После устранения:
1. Обновить issue: причина, временные рамки, действия.
2. Обновить `docs/observability/SLO.md` (если нужны новые SLI/SLO).
3. Запланировать меры предотвращения (TODO/ADR).
4. Провести blameless postmortem; используйте шаблон [`docs/runbooks/postmortem_template.md`](docs/runbooks/postmortem_template.md) или создайте файл `docs/runbooks/postmortem/YYYY-MM-DD.md`.

## 8. Контакты

- On-call инженер — см. внутренний список (TODO: добавить в конституцию).
- Команда безопасности — `security@1c-ai-stack.local`.
- DevOps чат — `#dev-ops`.
