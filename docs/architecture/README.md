# 🏗️ Architecture Documentation

Актуальная документация архитектуры проекта 1C AI Stack.

---

## 📁 Файлы

### `ARCHITECTURE_DIAGRAM.md`

**Содержит:**
- Полная архитектурная диаграмма (Mermaid)
- Диаграммы потоков данных (Voice, OCR, Code Gen)
- Компонентная архитектура
- Security architecture
- Deployment architecture
- CI/CD pipeline
- Технологический стек

**Формат:** Mermaid diagrams (можно рендерить в GitHub, VSCode, mermaid.live)

---

## 🖼️ Генерация PNG диаграммы

### Вариант 1: Online (самый простой) ⭐

1. Открыть https://mermaid.live/
2. Скопировать код из раздела "High-Level Architecture" в `ARCHITECTURE_DIAGRAM.md`
3. Настроить тему: `dark` + `transparent background`
4. Экспортировать как PNG (2400x1800)
5. Сохранить как `../../Architecture_Connections_Diagram.png`

### Вариант 2: VS Code Extension

1. Установить расширение "Markdown Preview Mermaid Support"
2. Открыть `ARCHITECTURE_DIAGRAM.md` в VS Code
3. `Ctrl+Shift+P` → "Markdown: Open Preview"
4. Right-click на диаграмме → "Save Image As..."
5. Сохранить как `../../Architecture_Connections_Diagram.png`

### Вариант 3: CLI (для автоматизации)

**Linux/Mac:**
```bash
# Установить Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Запустить скрипт генерации
./scripts/generate_architecture_diagram.sh
```

**Windows (Git Bash):**
```bash
# Установить Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Запустить скрипт
bash scripts/generate_architecture_diagram.sh
```

**Windows (PowerShell):**
```powershell
# Установить Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Генерация вручную
mmdc -i docs/architecture/ARCHITECTURE_DIAGRAM.md `
     -o Architecture_Connections_Diagram.png `
     -t dark `
     -b transparent `
     -w 2400 `
     -H 1800
```

### Вариант 4: Python Script (если есть Python)

```bash
pip install mermaid-py
python scripts/generate_diagram.py
```

---

## 📊 Рекомендуемые настройки

**Для PNG диаграммы:**
- Ширина: 2400px
- Высота: 1800px (auto)
- Тема: dark
- Фон: transparent
- Формат: PNG

**Для документации:**
- Всегда обновлять `ARCHITECTURE_DIAGRAM.md` при изменениях
- После обновления - генерировать новый PNG
- Коммитить оба файла вместе

---

## 🔄 Workflow обновления

1. Редактировать `ARCHITECTURE_DIAGRAM.md`
2. Сгенерировать PNG (любым из способов выше)
3. Проверить что PNG актуален
4. Закоммитить:
```bash
git add docs/architecture/ARCHITECTURE_DIAGRAM.md
git add Architecture_Connections_Diagram.png
git commit -m "docs: update architecture diagram to v5.0"
git push
```

---

## 📝 Содержание диаграмм

### 1. High-Level Architecture
**Показывает:**
- 5 User Interfaces (Telegram, MCP, EDT, Web, API)
- AI Orchestrator + 8 AI Agents
- AI Services (OpenAI, Qwen, Chandra)
- Data Layer (PostgreSQL, Neo4j, Qdrant, Elasticsearch, Redis)
- Infrastructure (Docker, K8s, Monitoring)

### 2. Voice Query Flow
**Показывает:**
- Telegram Bot → Speech-to-Text (Whisper)
- Text processing → AI Orchestrator
- Response generation
- User notification

### 3. OCR Document Flow
**Показывает:**
- Photo/PDF upload → Chandra OCR
- Text extraction (83%+ accuracy)
- AI parsing → structured data
- Database save

### 4. Code Generation Flow
**Показывает:**
- User request → semantic search (Qdrant)
- Context retrieval → Qwen3-Coder
- Code generation → validation
- Response with documentation

### 5. Component Architecture
**Показывает:**
- User Interfaces (mobile, desktop, web)
- API Gateway
- Integration points

### 6. AI Services Integration
**Показывает:**
- External AI (OpenAI)
- Local AI (Ollama, Qwen, Chandra)
- Intelligent routing (cost + quality)

### 7. Data Storage
**Показывает:**
- 5 databases
- Sync between them
- Application layer integration

### 8. Security Architecture
**Показывает:**
- 6 security layers
- Firewall → Authentication → Authorization
- Encryption, Audit, Secrets

### 9. Deployment Architecture
**Показывает:**
- Development (Docker Compose)
- Production (Kubernetes)
- Load balancing
- Auto-scaling

### 10. Technology Stack
**Показывает:**
- Backend (Python, FastAPI)
- Databases (5 types)
- AI/ML (4 services)
- Frontend (React, TypeScript)
- Infrastructure (Docker, K8s, monitoring)

### 11. Scalability
**Показывает:**
- 1-100 users → Single Server
- 100-1K → Multi-Pod K8s
- 1K-10K → Auto-scaling
- 10K+ → Multi-Region

### 12. CI/CD Pipeline
**Показывает:**
- Git Push → GitHub Actions
- Linting, Testing, Security Scan
- Build → Registry → Deploy
- Dev → Staging → Production

---

## 🎯 Версии диаграмм

| Версия | Дата | Изменения |
|--------|------|-----------|
| 5.0 | 2024-11-05 | + Voice Queries, + OCR, + i18n, + Marketplace, + BSL Dataset |
| 4.0 | 2024-11-04 | + MCP Server, + EDT Plugin, + 8 AI Agents |
| 3.0 | 2024-11-03 | + Neo4j, + Qdrant, + Elasticsearch |
| 2.0 | 2024-11-02 | + Telegram Bot, + PostgreSQL |
| 1.0 | 2024-11-01 | Initial architecture |

**Текущая версия:** 5.0 (Production Ready)

---

## 🔗 Связанная документация

- [Technology Stack](TECHNOLOGY_STACK.md)
- [C4 Model](C4_MODEL_COMPLETE.md)
- [Project Summary](../02-architecture/PROJECT_SUMMARY.md)
- [Getting Started](../01-getting-started/)

---

**Обновлено:** 2024-11-05  
**Статус:** ✅ Актуально

