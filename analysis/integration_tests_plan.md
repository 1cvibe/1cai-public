## План интеграционных тестов (Graph, Hybrid Search, Marketplace, Gateway)

### 1. Цели
- Подтвердить, что цепочки Graph API → Neo4j/Qdrant/Postgres и Hybrid Search (`src/services/hybrid_search.py`) работают end-to-end при реальных/мок‑зависимостях.
- Расширить существующие marketplace E2E (`tests/integration/test_marketplace_e2e.py`) сценариями загрузки/жалоб/ролей.
- Зафиксировать проверки Gateway (`src/api/gateway.py`) с `AuthenticationMiddleware` и проксированием до вспомогательных сервисов.

### 2. Тестовое окружение
- **Docker compose (dev)**: Postgres (enterprise_1c_ai), Neo4j, Qdrant, Redis, Elasticsearch. При отсутствии — используем контекстные моки, но health-check тесты помечаем `pytest.skip`.
- **Secrets**: использовать `.env.test` без реальных ключей; убедиться, что `GATEWAY_API_KEYS` задан в env перед запуском.
- **Фикстуры**: единые async фикстуры для клиентов (напр. `neo4j_driver`, `qdrant_client`, `es_client`) и `TestClient` с LifespanManager для отдельных FastAPI приложений (Graph API отдельно от `src/main.py`).

### 3. Покрытие по подсистемам

#### 3.1 Graph API (`src/api/graph_api.py`)
- **Startup/Shutdown**: проверить, что при недоступной зависимости приложение логирует предупреждение и продолжает работать (`startup_event` и `shutdown_event`).
- **`POST /api/graph/query`**:
  - Успешный путь с мок‑Neo4j: убеждаемся, что `MATCH` запрос выполняется, и результат сериализуется.
  - Отказ при `DELETE/CREATE` (валидация `dangerous_patterns`).
  - 503, если `neo4j_client` отсутствует (эмуляция отсутствия подключения).
- **`POST /api/graph/function-dependencies`**:
  - Успешный путь: возвращает связи между функциями.
  - 404/422: недопустимые имена или отсутствие узлов.
- **`POST /api/graph/semantic-search`**:
  - Комбинация EmbeddingService + Qdrant (`EmbeddingService.encode` → `QdrantClient.search`), включая ограничение `MAX_SEMANTIC_QUERY_LENGTH`.
  - Проверить graceful fallback, если EmbeddingService бросает исключение.
- **Health**: `/health` возвращает доступность всех трёх бэкендов.
- **Инструменты**: использовать `pytest.mark.asyncio` + `TestClient(app)` (подключая `graph_api.app` напрямую).

#### 3.2 Hybrid Search Service (`src/services/hybrid_search.py`)
- Создать интеграционный тест, который поднимает временные мок‑qdrant/elasticsearch клиенты:
  - **Полный путь**: обе ветки возвращают результаты, проверяем RRF и лимиты (`limit`, `rrf_k`).
  - **Fallback**: отсутствие EmbeddingService → пропуск vector-поиска с предупреждением.
  - **Timeout**: форсируем `asyncio.TimeoutError`, убеждаемся, что сервис возвращает частичные результаты.
  - **Input validation**: слишком длинный запрос обрезается до `MAX_QUERY_LENGTH`.

#### 3.3 Marketplace (FastAPI `src.api.marketplace`)
- Расширить `tests/integration/test_marketplace_e2e.py`:
  - **Загрузка артефакта**: тест `POST /marketplace/plugins/{id}/upload` с S3/mock storage, проверка limiter (`Response` + headers).
  - **Жалобы**: `POST /marketplace/plugins/{id}/complaints` с проверкой ролей.
  - **Публикация/апдейт**: `PATCH /marketplace/plugins/{id}` с валидацией полей (версия, семантика статусов).
  - **Auth overrides**: использовать `CurrentUser` для разных ролей (developer/reviewer/admin).

#### 3.4 Gateway (`src/api/gateway.py`)
- Выделить отдельный `TestClient` для gateway-приложения:
  - **AuthenticationMiddleware**: запросы без ключа, с длинным ключом, с корректным `X-API-Key`.
  - **`POST /api/gateway/proxy`** (или аналогичный маршрут проксирования):
    - Мок `httpx.AsyncClient` для backends (`SERVICES_CONFIG`), проверка переноса заголовков и таймаутов.
    - Rate limiting: использовать `slowapi` тестовую стратегию (2 запроса→429).
  - **Health endpoints**: `/api/gateway/health` и `/api/gateway/services/{name}` (успех + недоступность сервиса).
  - **Metrics**: подтвердить, что счётчики обновляются после цепочки запросов.

### 4. Реализация
1. Создать общий модуль фикстур `tests/integration/conftest_graph.py` (или расширить существующий) с фабриками клиентов и тонкой настройкой env.
2. Для Graph API и Gateway — запускать отдельные FastAPI приложения через `async with LifespanManager(app)` чтобы корректно поднимать/гасить ресурсы.
3. Моки внешних сервисов:
   - Neo4j/Qdrant: `pytest` monkeypatch методов `Neo4jClient.run_query`, `QdrantClient.search`.
   - Elasticsearch: упрощённый клиент, который возвращает заранее подготовленный `hits`.
   - `httpx.AsyncClient`: `AsyncMock` с контролем `status_code`, `json`.
4. Добавить маркировки `@pytest.mark.integration` + обновить `pytest.ini`, если нужно, чтобы можно было запускать `pytest -m integration`.
5. Добавить инструкции в `IMPROVEMENTS_PROGRESS.md` и `docs/testing/` по запуску новых интеграционных тестов.

### 5. Вывод
После реализации матрицы тестов можно автоматизировать проверку в CI (job `integration-tests`), а также использовать её как основу для smoke-тестов перед деплоем.

### 6. Регламент запуска
- После каждой доработки и любой новой интеграции обязателен полный цикл проверок: `make lint`, unit + integration + e2e тесты и `python run_full_audit.py --stop-on-failure`.
- Если изменения затрагивают внешние зависимости или конфигурацию, дополнительно запускаем `make render-uml` и проверку ссылок, чтобы соблюсти требования к документации.

