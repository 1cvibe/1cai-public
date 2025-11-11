# Linkerd Service Mesh (Blueprint)

## 1. Установка
1. Установите CLI: `curl -sL https://run.linkerd.io/install | sh` и добавьте в `$PATH`.
2. Проверка: `linkerd check --pre`.
3. Установка control plane:
   ```bash
   linkerd install | kubectl apply -f -
   linkerd viz install | kubectl apply -f -
   ```
4. Включить sidecar для `1cai`:
   ```bash
   kubectl annotate ns 1cai linkerd.io/inject=enabled
   kubectl rollout restart deploy -n 1cai
   ```

## 2. Сравнение с Istio
- Быстрая установка, минимальный overhead.
- Подходит для strict mTLS, observability (viz dashboard).
- Нет встроенного ingress (используйте Nginx/Voyager).

## 3. Roadmap
- Helm chart для Linkerd (todo).
- Политики Linkerd AuthorizationPolicy.
- Интеграция с chaos (fault injection).
