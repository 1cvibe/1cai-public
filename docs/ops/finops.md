# FinOps & Cost Monitoring

## 1. Цели
- Контроль затрат в AWS/Cloud (ежедневные отчёты, бюджет).

## 2. Инструменты
- `scripts/finops/aws_cost_report.py` — использует AWS Cost Explorer API, показывает ежедневные затраты за 7 дней.
- Планируется поддержка Azure Cost Management / GCP Billing (TODO).

## 3. Требования
```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
python scripts/finops/aws_cost_report.py
```

## 4. Roadmap
- Интеграция с Terraform outputs (tags cost center).
- Автоматический отчёт в Slack/Teams.
- Budget alerts (AWS Budgets API).
