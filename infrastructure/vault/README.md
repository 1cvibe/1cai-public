# Vault Configuration

## 1. Политики
- `policies/1cai-app.hcl` — доступ к KV `secret/data/1cai/*` (read/list) + управление lease.

## 2. Скрипт настройки
- `scripts/configure.sh` — включает KV v2, настраивает Kubernetes auth, создаёт роль `1cai-app`.

### Переменные окружения
- `VAULT_ADDR`, `VAULT_TOKEN` — адрес и токен администратора.
- `KUBERNETES_HOST`, `KUBERNETES_REVIEWER_JWT` (опционально) — данные API сервера и JWT service account.

### Запуск
```bash
cd infrastructure/vault/scripts
VAULT_ADDR=https://vault.example.com \
VAULT_TOKEN=... \
KUBERNETES_HOST=https://<cluster-endpoint> \
KUBERNETES_REVIEWER_JWT=$(cat token.jwt) \
./configure.sh
```

## 3. Динамические секреты
- Используйте `vault kv put secret/1cai/database url=... user=...`.
- В Kubernetes: sidecar Vault Agent или env-injection (TODO).

## 4. Kubernetes CSI Driver
- Пример `infrastructure/vault/csi/secret-provider-class.yaml` — маппит `secret/data/1cai/database` в Kubernetes Secret `db-credentials`.
- Требуется Secrets Store CSI Driver + Vault provider (см. https://secrets-store-csi-driver.sigs.k8s.io/).
- Deployment: добавить volume `csi` и env из secret (TODO).

## 5. AWS/Azure Secret Manager
- AWS: Terraform пример (см. `infrastructure/terraform/aws-eks`) + IAM policy для чтения `secretsmanager:GetSecretValue` (TODO).
- Azure: добавить Key Vault (Terraform) и Managed Identity (TODO).

## 6. Best Practices
