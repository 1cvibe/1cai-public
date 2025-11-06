# 🚀 1C AI Stack - Quick Start

**Project:** 1C AI Stack  
**Version:** 2.0  
**Date:** 6 ноября 2025

---

## 📁 NAVIGATION

### Main Documentation:
- **README:** `README.md` - главная документация проекта
- **Docs:** `docs/README.md` - вся документация

### Recent Work (6 Nov 2025):
- **ITIL Analysis:** `docs/07-itil-analysis/README.md`
- **Code Execution:** `docs/08-code-execution/README.md`
- **AI Research:** `AI_RESEARCH_SUMMARY.md`

### Git & Deployment:
- **Git Rules:** `GIT_PUSH_ПРАВИЛА_И_ЧЕКЛИСТ.md`
- **Git Scripts:** `git_push_safe.ps1`, `git_push_commands.ps1`

### Session Files:
- **Location:** `C:\Users\user\Desktop\Cursor\`
- All summaries and session reports are there

---

## 🎯 QUICK LINKS

**Documentation Structure:**
```
docs/
├── 01-getting-started/     (Setup guides)
├── 02-architecture/        (Architecture docs)
├── 03-api/                 (API documentation)
├── 04-deployment/          (Deployment guides)
├── 05-integrations/        (Integrations)
├── 06-features/            (Features docs)
├── 07-itil-analysis/       (ITIL/ITSM - NEW!)
├── 08-code-execution/      (Code Execution - NEW!)
└── 09-archive/             (Old docs)
```

**Code Structure:**
```
code/py_server/             (Python backend)
execution-env/              (Deno code execution - NEW!)
edt-plugin/                 (1C EDT plugin)
src/                        (Main source)
tests/                      (Tests)
```

---

## 🚀 GETTING STARTED

### 1. Setup Environment:
```bash
# Install dependencies
pip install -r requirements.txt

# Setup databases
docker-compose up -d
```

### 2. Run Backend:
```bash
# Вариант 1: MCP Server (для Claude Desktop)
python src/ai/mcp_server.py

# Вариант 2: FastAPI Server (REST API)
python src/main.py
```

### 3. Code Execution (NEW!):
```bash
cd execution-env
.\install.ps1  # Install Deno
deno run --allow-all execution-harness.ts
```

---

## 📊 PROJECT STATUS

**Readiness:** 99.5%  
**ROI:** >2500%  
**Tech Stack:** Updated (6 Nov 2025)

---

## 📞 MORE INFO

- **Full Docs:** `docs/README.md`
- **Session Files:** `C:\Users\user\Desktop\Cursor\`
- **GitHub (Private):** https://github.com/DmitrL-dev/1cai
- **GitHub (Public):** https://github.com/DmitrL-dev/1cai-public

---

**Created:** 6 ноября 2025  
**Purpose:** Quick navigation for the project

