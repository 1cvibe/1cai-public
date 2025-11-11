# Vault & Secret Management

## 1. Цели
- Централизованное управление секретами 1C AI Stack (Kubernetes/EKS/AKS).
- Минимальный доступ (least privilege), audit trail, короткие lease.

## 2. Файлы
- `infrastructure/vault/policies/1cai-app.hcl` — политика доступа к `secret/data/1cai/*`.
- `infrastructure/vault/scripts/configure.sh` — включает KV v2, Kubernetes auth, роль `1cai-app`.

## 3. Kubernetes интеграция
1. Настроить `vault auth enable kubernetes` (скрипт выше).
2. Создать service account `1cai-app` в namespace `1cai`.
3. В Deployment добавить sidecar Vault Agent или CSI driver (TODO).

## 4. AWS Secrets Manager / Azure Key Vault
- AWS: Terraform пример (см. `infrastructure/terraform/aws-eks`) + IAM policy для чтения `secretsmanager:GetSecretValue` (TODO).
- Azure: добавить Key Vault (Terraform) и Managed Identity (TODO).

## 5. Best Practices
- Политики только на нужные пути (`secret/data/1cai/*`).
- Короткие TTL, регулярный `vault lease renew` через sidecar.
- Audit log включен (`vault audit enable file file_path=/var/log/vault_audit.log`).
- Secrets никогда не коммитятся, только через Terraform/Vault CLI.

## 6. Roadmap
- CSI driver манифесты для K8s.
- Динамические секреты (PostgreSQL, Redis).
- Автоматический sync AWS Secrets → Vault.
