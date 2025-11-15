## Стратегия версионирования API

### 1. Цели
- Гарантировать обратную совместимость при дальнейших изменениях контрактов.
- Чётко отделить стабильные маршруты (`v1`) от экспериментальных (`v2-beta`), синхронизируя FastAPI маршруты, документацию и клиентские SDK.
- Упростить выпуск будущих breaking changes за счёт единых правил версионирования.

### 2. Область охвата
- **FastAPI приложения**: `src/main.py` (основные REST/endpoints), `src/api/gateway.py`, специализированные сервисы (`src/api/graph_api.py`, `src/api/code_review.py`, `src/api/marketplace.py`, `src/api/copilot.py`, `src/api/test_generation.py`, `src/api/ml_api.py`, `src/api/assistants.py` и т. д.).
- **Документация**: `README.md`, `IMPROVEMENTS_PROGRESS.md`, `docs/` (особенно `docs/06-features` и API гайды), `docs/api/*.md`.
- **Клиенты и SDK**: `src/clients/*`, `frontend`/`frontend-portal`, `integrations/`, `supabase/`, любые внешние скрипты (например, `scripts/api_clients/*.py`), Terraform/Helm values для ingress.
- **CI/CD**: workflows/Makefile, чтобы гонять smoke-тесты для каждой версии.

### 3. Технические принципы
1. **URL-пути**: префикс `/api/v1/...` для текущего стабильного API. Новые несовместимые изменения — под `/api/v2/...`.
2. **Версия по заголовкам**: поддерживать `X-API-Version` для клиентов, где неудобно менять URL (например, gateway). Заголовок мапится на конкретный router.
3. **Семантика**:
   - `v1` — все существующие публичные эндпойнты, freeze контрактов. Изменения только additive/patch.
   - `v1.1` (minor) допускает новые поля, не ломая существующих. Отражается в `openapi.info.version`.
   - `v2-beta` — площадка для крупных переписанных фич (например, Copilot Perfect, Gateway proxy). Включаем флагом `ENABLE_V2_BETA`.
4. **Документация**: каждая секция README `### Feature X` → ссылка в `docs/06-features/FEATURE_X_GUIDE.md` с актуальной версией API. Внутри docs указывать таблицу соответствия (endpoint, версия, deprecation date).
5. **Депрецкация**: для устаревших эндпойнтов добавлять `Deprecation` header + поле в ответе (`"deprecated": true`). В `SECURITY.md` и `TECH_DEBT_PROGRESS.md` фиксировать сроки отключения.
6. **Testing**: все новые версии проходят unit + integration + e2e. Для `pytest` добавить маркировку `@pytest.mark.api_v1` и `@pytest.mark.api_v2`.

### 4. План внедрения
1. **Инвентаризация** (день 0):
   - Пройтись по `src/api/*.py`, `src/services/*` и `tests/` с помощью скрипта (можно использовать `check_readme_vs_code.py`) и собрать список всех публичных маршрутов.
   - Сверить с документацией: убедиться, что каждый маршрут задокументирован и упомянут в `docs/`.
2. **Генерация routers** (день 1-2):
   - В `src/main.py` создать `APIRouter(prefix="/api/v1")` и последовательно подключить текущие routers. Для сервисов, уже имеющих префиксы (например, marketplace `/marketplace`), добавить wrapper `include_router(marketplace_router, prefix="/api/v1")`.
   - Для gateway/graph API: либо вставить версию в `FastAPI(title=..., version="1.0.0")`, либо оборачивать в отдельный router `/graph/v1`.
   - Ввод `VersionedFastAPI` (можно использовать библиотеку `fastapi-versioning`, если одобрено) либо собственный middleware, который переключает маршруты по заголовку.
3. **Документация и OpenAPI** (день 2-3):
   - Обновить `openapi.info.version` в каждом приложении.
   - В `docs/api/` добавить разделы `v1`/`v2`, примеры запросов, таблицу миграции.
   - README: добавить раздел "API версии" с инструкциями, как выбирать версию (URL vs header). Добиться, чтобы `check_readme_vs_code.py` проходил.
4. **Клиенты и SDK** (день 3-4):
   - В `src/clients/*` добавить поддержку указания версии (аргумент конструктора или env `API_VERSION`).
   - Обновить фронтенд (например, `frontend-portal`) и интеграции так, чтобы дефолт `v1`, но конфигурируемый через `.env`.
   - Документировать в `integrations/README.md`.
5. **Testing & CI** (день 4-5):
   - Обновить `tests/system/test_e2e_flows.py` и `tests/integration/*` на использование `/api/v1/...`.
   - Добавить smoke job в CI (`.github/workflows/...` или `Makefile`): `make test-api-v1` и `make test-api-v2`.
   - Проверить `check_security_comprehensive.py`, `check_all_links.py`, `make render-uml` (если диаграммы затрагивают маршруты).
6. **Коммуникация и релиз** (день 5):
   - В `RELEASE_NOTES.md` и `CHANGELOG.md` описать введение версий.
   - Подготовить скрипт уведомления (например, рассылка/Slack) для разработчиков и внешних пользователей.

### 5. Риски и меры
- **Рассыпанные маршруты**: часть эндпойнтов объявлена напрямую в `app`. План — вынести в routers перед версионированием.
- **Legacy клиенты**: на время перехода поддерживать редиректы `/api/... -> /api/v1/...` через middleware, логируя обращения без версии.
- **Документация**: риск застойных ссылок. Использовать `check_all_links.py` + ручную выборочную проверку (но скрипты обязательно).

### 6. Следующие шаги
1. Реализовать шаги 1-2 (инвентаризация и routers) и обновить тесты.
2. Переписать документацию/README, синхронизировать с `docs/`.
3. Подготовить выпуск с описанием версионности и провести smoke-тест для обоих наборов маршрутов.

