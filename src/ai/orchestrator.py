"""
AI Orchestrator - Intelligent routing of queries to AI services
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation
"""

import re
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, Query, Body, Form
from src.utils.structured_logging import StructuredLogger
from src.ai.scenario_hub import AutonomyLevel, ScenarioRiskLevel
from src.ai.scenario_policy import assess_plan_execution
from src.monitoring.prometheus_metrics import scenario_requests_total

logger = StructuredLogger(__name__).logger


app = FastAPI(title="AI Orchestrator API")


@app.get("/api/scenarios/examples")
async def get_scenario_examples(
    autonomy: Optional[str] = Query(
        default=None,
        description="Опциональный уровень автономности (A0_propose_only/A1_safe_automation/A2_non_prod_changes/A3_restricted_prod) для оценки шагов через Scenario Policy.",
    ),
) -> Dict[str, Any]:
    """
    Экспериментальный read-only endpoint, возвращающий
    примерные сценарии ScenarioPlan для BA→Dev→QA и DR rehearsal.

    Нужен как витрина для Scenario Hub, не влияет на основной
    routing process_query / AI-контур.
    """
    # Metrics: track Scenario Hub example requests
    scenario_requests_total.labels(
        endpoint="/api/scenarios/examples",
        autonomy_provided=autonomy or "none",
    ).inc()

    try:
        from src.ai.scenario_examples import (
            example_ba_dev_qa_scenario,
            example_dr_rehearsal_scenario,
            example_code_review_scenario,
        )
    except Exception as e:  # pragma: no cover - защитный fallback
        logger.warning(
            "Scenario examples not available",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(status_code=500, detail="Scenario examples not available")

    ba_plan = example_ba_dev_qa_scenario("DEMO_FEATURE")
    dr_plan = example_dr_rehearsal_scenario("vault")
    cr_plan = example_code_review_scenario("DEMO_FEATURE")

    autonomy_level: Optional[AutonomyLevel] = None
    if autonomy:
        mapping = {
            "A0_propose_only": AutonomyLevel.A0_PROPOSE_ONLY,
            "A1_safe_automation": AutonomyLevel.A1_SAFE_AUTOMATION,
            "A2_non_prod_changes": AutonomyLevel.A2_NON_PROD_CHANGES,
            "A3_restricted_prod": AutonomyLevel.A3_RESTRICTED_PROD,
        }
        autonomy_level = mapping.get(autonomy)

    scenarios_payload: List[Dict[str, Any]] = []
    for plan in (ba_plan, dr_plan, cr_plan):
        payload = asdict(plan)
        # Простейшее извлечение graph_refs из шагов для витрины Unified Change Graph
        graph_nodes = []
        for step in plan.steps:
            meta = step.metadata or {}
            for ref in meta.get("graph_refs", []):
                if ref not in graph_nodes:
                    graph_nodes.append(ref)
        if graph_nodes:
            payload["_graph_nodes_touched"] = graph_nodes
        if autonomy_level is not None:
            decisions = assess_plan_execution(plan, autonomy_level)
            payload["policy_decisions"] = {
                step_id: decision.value for step_id, decision in decisions.items()
            }
            payload["autonomy_evaluated"] = autonomy_level.value
        scenarios_payload.append(payload)

    return {"scenarios": scenarios_payload}


@app.get("/api/scenarios/dry-run")
async def dry_run_playbook_endpoint(
    path: str = Query(
        ...,
        description="Путь до YAML-плейбука (по умолчанию ожидается внутри playbooks/).",
    ),
    autonomy: Optional[str] = Query(
        default=None,
        description="Уровень автономности для применения Scenario Policy (например, A1_safe_automation).",
    ),
) -> Dict[str, Any]:
    """
    Экспериментальный endpoint для dry-run YAML-плейбуков Scenario Hub.

    Не выполняет реальных действий, только:
    - загружает плейбук;
    - применяет Scenario Policy (если указан autonomy);
    - возвращает отчёт в формате ScenarioExecutionReport as dict.
    """
    # Metrics: track Scenario Hub dry-run requests
    scenario_requests_total.labels(
        endpoint="/api/scenarios/dry-run",
        autonomy_provided=autonomy or "none",
    ).inc()

    try:
        from src.ai.playbook_executor import dry_run_playbook_to_dict
    except Exception as e:  # pragma: no cover - защитный fallback
        logger.warning(
            "Playbook executor not available",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(status_code=500, detail="Playbook executor not available")

    try:
        report = dry_run_playbook_to_dict(path, autonomy=autonomy)
        # Если плейбук содержит graph_refs, dry_run_playbook_to_dict уже включает их
        # в структуру плана; здесь лишь гарантируем наличие поля-обёртки.
        if "graph_nodes_touched" not in report:
            # Не раздуваем отчёт, просто оставляем поле пустым,
            # чтобы формат был стабильным.
            report.setdefault("graph_nodes_touched", [])
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Playbook not found: {path}")
    except Exception as e:  # pragma: no cover - защитный fallback
        logger.warning(
            "Playbook dry-run failed",
            extra={"error": str(e), "error_type": type(e).__name__, "path": path},
        )
        raise HTTPException(status_code=500, detail="Playbook dry-run failed")

    return {"report": report}


@app.get("/api/tools/registry/examples")
async def get_tool_registry_examples() -> Dict[str, Any]:
    """
    Экспериментальный read-only endpoint, возвращающий
    примерное содержимое ToolRegistry (несколько инструментов).
    """
    try:
        from src.ai.tool_registry_examples import list_example_tools
    except Exception as e:  # pragma: no cover - защитный fallback
        logger.warning(
            "Tool registry examples not available",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=500, detail="Tool registry examples not available"
        )

    tools = [asdict(t) for t in list_example_tools()]
    return {"tools": tools}


@app.post("/api/code-graph/1c/build")
async def build_1c_code_graph(
    module_code: str = Body(..., description="BSL код модуля"),
    module_path: str = Body(
        ..., description="Путь модуля (например, 'ОбщийМодуль.Имя')"
    ),
    export_json: bool = Body(default=False, description="Экспортировать граф в JSON"),
) -> Dict[str, Any]:
    """
    Построить Unified Change Graph из кода 1С (BSL модуль).

    Использует BSL парсеры для извлечения структуры (функции, процедуры, зависимости)
    и автоматически создаёт узлы и рёбра в Unified Change Graph.

    Это ключевая фича для "де-факто" стандарта: автоматическое построение графа
    изменений из кода 1С без ручной настройки.
    """
    try:
        from src.ai.code_graph import InMemoryCodeGraphBackend
        from src.ai.code_graph_1c_builder import OneCCodeGraphBuilder
    except Exception as e:  # pragma: no cover - защитный fallback
        logger.warning(
            "1C Code Graph Builder not available",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=500, detail="1C Code Graph Builder not available"
        )

    try:
        backend = InMemoryCodeGraphBackend()
        builder = OneCCodeGraphBuilder(backend, use_ast_parser=True)

        stats = await builder.build_from_module(
            module_path,
            module_code,
            module_metadata={"source": "api", "owner": "unknown"},
        )

        result: Dict[str, Any] = {
            "status": "success",
            "stats": stats,
        }

        if export_json:
            graph_export = await builder.export_graph()
            result["graph"] = graph_export

        return result

    except Exception as e:  # pragma: no cover - защитный fallback
        logger.warning(
            "Failed to build 1C code graph",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "module_path": module_path,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to build graph: {str(e)}")


class QueryType(Enum):
    """Types of queries"""

    STANDARD_1C = "standard_1c"
    GRAPH_QUERY = "graph_query"
    CODE_GENERATION = "code_generation"
    SEMANTIC_SEARCH = "semantic_search"
    ARCHITECTURE = "architecture"
    OPTIMIZATION = "optimization"
    UNKNOWN = "unknown"


class AIService(Enum):
    """Available AI services"""

    EXTERNAL_AI = "external_ai"
    QWEN_CODER = "qwen_coder"
    NEO4J = "neo4j"
    QDRANT = "qdrant"
    GIGACHAT = "gigachat"
    OPENAI = "openai"
    NAPARNIK = "naparnik"
    KIMI_K2 = "kimi_k2"  # Kimi-K2-Thinking for complex reasoning and tool orchestration
    TABNINE = "tabnine"  # Tabnine AI code completion and generation


@dataclass
class QueryIntent:
    """Query intent analysis result"""

    query_type: QueryType
    confidence: float
    keywords: List[str]
    context_type: Optional[str]
    preferred_services: List[AIService]
    # Экспериментальное поле: список id инструментов/skills, которые могут быть полезны
    suggested_tools: List[str]


class QueryClassifier:
    """Classifies user queries to determine routing"""

    def __init__(self):
        """Инициализация QueryClassifier с поддержкой LLM Provider Abstraction."""
        self.llm_abstraction = None
        try:
            from src.ai.llm_provider_abstraction import LLMProviderAbstraction

            self.llm_abstraction = LLMProviderAbstraction()
            logger.info("LLM Provider Abstraction initialized")
        except Exception as e:
            logger.debug("LLM Provider Abstraction not available: %s", e)

    # Classification rules
    RULES = {
        QueryType.STANDARD_1C: {
            "keywords": [
                "типовая",
                "типовой",
                "стандартн",
                "в УТ",
                "в ERP",
                "в ЗУП",
                "в БУХ",
                "как сделано",
                "как реализовано",
            ],
            "patterns": [
                r"как\s+(сделано|реализовано)\s+в\s+(УТ|ERP|ЗУП|БУХ)",
                r"типов(ая|ой|ое|ые)\s+",
                r"стандартн(ый|ая|ое|ые)\s+",
            ],
            "services": [
                AIService.NAPARNIK,
                AIService.EXTERNAL_AI,
                AIService.QWEN_CODER,
            ],
        },
        QueryType.UNKNOWN: {
            "keywords": [],
            "patterns": [],
            "services": [AIService.NAPARNIK],
        },
        QueryType.GRAPH_QUERY: {
            "keywords": [
                "зависимости",
                "связи",
                "где используется",
                "кто вызывает",
                "граф",
                "иерархия",
                "найди все связи",
            ],
            "patterns": [
                r"где\s+использу(ется|ют|ется)",
                r"кто\s+вызывает",
                r"найди\s+(все\s+)?(связи|зависимости)",
                r"граф\s+вызовов",
            ],
            "services": [AIService.NEO4J],
        },
        QueryType.CODE_GENERATION: {
            "keywords": [
                "создай",
                "напиши",
                "сгенерируй",
                "добавь",
                "реализуй",
                "функция",
                "процедура",
                "метод",
            ],
            "patterns": [
                r"(создай|напиши|сгенерируй)\s+(функци|процедур)",
                r"реализуй\s+",
                r"добавь\s+(функци|процедур|метод)",
            ],
            "services": [AIService.QWEN_CODER, AIService.TABNINE, AIService.EXTERNAL_AI],
        },
        QueryType.SEMANTIC_SEARCH: {
            "keywords": [
                "похожий",
                "похожая",
                "подобн",
                "аналогичный",
                "есть ли",
                "найди код",
            ],
            "patterns": [
                r"найди\s+похож",
                r"есть\s+ли\s+(похож|аналог)",
                r"покажи\s+(похож|аналог)",
            ],
            "services": [AIService.QDRANT, AIService.NEO4J],
        },
        QueryType.OPTIMIZATION: {
            "keywords": [
                "оптимизируй",
                "ускорь",
                "улучш",
                "рефакторинг",
                "производительность",
            ],
            "patterns": [
                r"(оптимизируй|улучш|ускор)",
                r"рефакторинг",
                r"как\s+улучшить",
            ],
            "services": [AIService.QWEN_CODER, AIService.NEO4J],
        },
    }

    def classify(self, query: str, context: Dict[str, Any] = None) -> QueryIntent:
        """
        Classify query with input validation

        Args:
            query: User query string
            context: Optional context dictionary

        Returns:
            QueryIntent with classification result
        """
        # Input validation
        if not query or not isinstance(query, str):
            logger.warning(
                "Invalid query in classify",
                extra={"query_type": type(query).__name__ if query else None},
            )
            # Return default intent for invalid query
            return QueryIntent(
                query_type=QueryType.UNKNOWN,
                confidence=0.0,
                keywords=[],
                context_type=None,
                preferred_services=[AIService.NAPARNIK],
                suggested_tools=[],
            )

        # Validate query length
        max_query_length = 10000
        if len(query) > max_query_length:
            logger.warning(
                "Query too long in classify",
                extra={"query_length": len(query), "max_length": max_query_length},
            )
            query = query[:max_query_length]  # Truncate

        if context is None:
            context = {}
        elif not isinstance(context, dict):
            logger.warning(
                "Invalid context type in classify",
                extra={"context_type": type(context).__name__},
            )
            context = {}

        query_lower = query.lower()
        scores: Dict[QueryType, float] = {}
        matched_keywords: List[str] = []

        # Score each query type
        for query_type, rules in self.RULES.items():
            score = 0.0

            # Check keywords
            for keyword in rules["keywords"]:
                if keyword.lower() in query_lower:
                    score += 1.0
                    matched_keywords.append(keyword)

            # Check patterns
            for pattern in rules["patterns"]:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 2.0

            scores[query_type] = score

        # Determine best match
        if scores:
            best_type = max(scores, key=scores.get)
            confidence = min(scores[best_type] / 5.0, 1.0)  # Normalize to 0-1
        else:
            best_type = QueryType.UNKNOWN
            confidence = 0.0

        # Get preferred services
        preferred_services = []
        if best_type != QueryType.UNKNOWN:
            preferred_services = self.RULES[best_type]["services"]
        else:
            preferred_services = self.RULES.get(QueryType.UNKNOWN, {}).get(
                "services", []
            )

        # Экспериментально подбираем подходящие инструменты из ToolRegistry
        suggested_tools: List[str] = []
        try:  # не ломаем основной flow при ошибках примеров
            from src.ai.tool_registry_examples import build_example_tool_registry

            registry = build_example_tool_registry()
            if (
                best_type == QueryType.STANDARD_1C
                or best_type == QueryType.ARCHITECTURE
            ):
                suggested_tools = ["ba_requirements_extract"]
            elif best_type == QueryType.CODE_GENERATION:
                # Низкорисковые/неprod-инструменты
                tools = registry.list_tools(risk=ScenarioRiskLevel.NON_PROD_CHANGE)
                suggested_tools = [t.id for t in tools]
            elif best_type == QueryType.OPTIMIZATION:
                suggested_tools = ["security_audit"]
            elif best_type == QueryType.GRAPH_QUERY:
                suggested_tools = ["scenario_ba_dev_qa"]

            # Добавить LLM провайдеры в suggested_tools через ToolRegistry
            if self.llm_abstraction:
                try:
                    llm_tools = self.llm_abstraction.to_tool_registry_format()
                    suggested_tools.extend([tool["id"] for tool in llm_tools])
                except Exception as e:
                    logger.debug("Failed to add LLM tools to suggestions: %s", e)
        except Exception as e:  # pragma: no cover - чисто защитный лог
            logger.warning(
                "Tool suggestions failed",
                extra={"error": str(e), "error_type": type(e).__name__},
            )

        return QueryIntent(
            query_type=best_type,
            confidence=confidence,
            keywords=matched_keywords,
            context_type=context.get("type") if context else None,
            preferred_services=preferred_services,
            suggested_tools=suggested_tools,
        )


class AIOrchestrator:
    """Main AI orchestrator - routes queries to appropriate services"""

    def __init__(self):
        self.classifier = QueryClassifier()
        self.clients = {}
        # Инициализация интеллектуального кэша
        try:
            from src.ai.intelligent_cache import IntelligentCache

            self.cache = IntelligentCache(max_size=1000, default_ttl_seconds=300)
            logger.info("Intelligent cache initialized")
        except Exception as e:
            logger.warning(
                "Failed to initialize intelligent cache, using simple dict",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            self.cache = {}  # Fallback to simple dict
        # Unified Change Graph query helper (опционально, если backend доступен)
        self.graph_helper = None
        try:
            from src.ai.code_graph import InMemoryCodeGraphBackend
            from src.ai.code_graph_query_helper import GraphQueryHelper

            # Используем InMemoryCodeGraphBackend по умолчанию
            # В будущем можно заменить на Neo4j или другой персистентный backend
            graph_backend = InMemoryCodeGraphBackend()
            self.graph_helper = GraphQueryHelper(graph_backend)
            logger.info("GraphQueryHelper initialized (InMemoryCodeGraphBackend)")
        except Exception as e:
            logger.debug(
                "GraphQueryHelper not available",
                extra={"error": str(e), "error_type": type(e).__name__},
            )

        # Initialize Qwen client
        try:
            from src.ai.qwen_client import QwenCoderClient

            self.qwen_client = QwenCoderClient()
            logger.info("✓ Qwen3-Coder client initialized")
        except Exception as e:
            logger.warning(
                "Qwen client not available",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            self.qwen_client = None

        # Initialize Kimi client
        try:
            from src.ai.clients.kimi_client import KimiClient, KimiConfig

            kimi_config = KimiConfig()
            self.kimi_client = KimiClient(config=kimi_config)
            if self.kimi_client.is_configured:
                logger.info(
                    "Kimi-K2-Thinking client initialized",
                    extra={"mode": self.kimi_client._mode},
                )
            else:
                logger.warning(
                    "Kimi-K2-Thinking client not configured. Check KIMI_API_KEY or KIMI_OLLAMA_URL.",
                    extra={"mode": self.kimi_client._mode},
                )
                self.kimi_client = None
        except Exception as e:
            logger.warning(
                "Kimi-K2-Thinking client not available",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            self.kimi_client = None

        # Initialize GigaChat client
        try:
            from src.ai.clients.gigachat_client import GigaChatClient, GigaChatConfig

            gigachat_config = GigaChatConfig()
            self.gigachat_client = GigaChatClient(config=gigachat_config)
            if self.gigachat_client.is_configured:
                logger.info("GigaChat client initialized")
            else:
                logger.warning(
                    "GigaChat client not configured. Check GIGACHAT_CLIENT_ID/GIGACHAT_CLIENT_SECRET or GIGACHAT_ACCESS_TOKEN."
                )
                self.gigachat_client = None
        except Exception as e:
            logger.warning(
                "GigaChat client not available",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            self.gigachat_client = None

        # Initialize YandexGPT client
        try:
            from src.ai.clients.yandexgpt_client import YandexGPTClient, YandexGPTConfig

            yandexgpt_config = YandexGPTConfig()
            self.yandexgpt_client = YandexGPTClient(config=yandexgpt_config)
            if self.yandexgpt_client.is_configured:
                logger.info("YandexGPT client initialized")
            else:
                logger.warning(
                    "YandexGPT client not configured. Check YANDEXGPT_API_KEY and YANDEXGPT_FOLDER_ID."
                )
                self.yandexgpt_client = None
        except Exception as e:
            logger.warning(
                "YandexGPT client not available",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            self.yandexgpt_client = None

        # Initialize 1C:Напарник client
        try:
            from src.ai.clients.naparnik_client import NaparnikClient, NaparnikConfig

            naparnik_config = NaparnikConfig()
            self.naparnik_client = NaparnikClient(config=naparnik_config)
            if self.naparnik_client.is_configured:
                logger.info("1C:Напарник client initialized")
            else:
                logger.warning(
                    "1C:Напарник client not configured. Check NAPARNIK_API_KEY."
                )
                self.naparnik_client = None
        except Exception as e:
            logger.warning(
                "1C:Напарник client not available",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            self.naparnik_client = None

        # Initialize Ollama client (universal local models)
        try:
            from src.ai.clients.ollama_client import OllamaClient, OllamaConfig

            ollama_config = OllamaConfig()
            self.ollama_client = OllamaClient(config=ollama_config)
            if self.ollama_client.is_configured:
                logger.info(
                    "Ollama client initialized",
                    extra={
                        "base_url": ollama_config.base_url,
                        "model": ollama_config.model_name,
                    },
                )
            else:
                logger.debug(
                    "Ollama client not configured. Check OLLAMA_HOST environment variable."
                )
                self.ollama_client = None
        except Exception as e:
            logger.debug(
                "Ollama client not available",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            self.ollama_client = None

        # Initialize Tabnine client
        try:
            from src.ai.clients.tabnine_client import TabnineClient, TabnineConfig

            tabnine_config = TabnineConfig()
            self.tabnine_client = TabnineClient(config=tabnine_config)
            if self.tabnine_client.is_configured:
                logger.info("Tabnine client initialized")
            else:
                logger.warning(
                    "Tabnine client not configured. Check TABNINE_AUTH_TOKEN environment variable."
                )
                self.tabnine_client = None
        except Exception as e:
            logger.warning(
                "Tabnine client not available",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            self.tabnine_client = None

    def register_client(self, service: AIService, client: Any):
        """Register AI service client"""
        self.clients[service] = client
        logger.info("Registered client", extra={"service": service.value})

    async def process_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query and return response

        Args:
            query: User query string
            context: Optional context dictionary

        Returns:
            Response dictionary with results
        """
        # Input validation
        if not query or not isinstance(query, str):
            logger.warning(
                f"Invalid query provided: {query}",
                extra={"query_type": type(query).__name__},
            )
            raise ValueError("Query must be a non-empty string")

        # Validate query length (prevent DoS)
        max_query_length = 10000  # 10KB max
        if len(query) > max_query_length:
            logger.warning(
                f"Query too long: {len(query)} characters",
                extra={"query_length": len(query), "max_length": max_query_length},
            )
            raise ValueError(
                f"Query too long. Maximum length: {max_query_length} characters"
            )

        if context is None:
            context = {}
        elif not isinstance(context, dict):
            logger.warning(
                f"Invalid context type: {type(context)}",
                extra={"context_type": type(context).__name__},
            )
            context = {}

        try:
            # Check cache (поддержка как IntelligentCache, так и простого dict)
            cached_value = None
            if isinstance(self.cache, dict):
                # Простой dict кэш (fallback)
                cache_key = f"{query}:{context}"
                cached_value = self.cache.get(cache_key)
            else:
                # IntelligentCache
                cached_value = self.cache.get(query, context)

            if cached_value is not None:
                # Track cache hit
                try:
                    from src.monitoring.prometheus_metrics import (
                        orchestrator_cache_hits_total,
                    )

                    orchestrator_cache_hits_total.inc()
                except ImportError:
                    pass

                logger.info("Cache hit", extra={"query_length": len(query)})
                return cached_value

            # Track cache miss
            try:
                from src.monitoring.prometheus_metrics import (
                    orchestrator_cache_misses_total,
                )

                orchestrator_cache_misses_total.inc()
            except ImportError:
                pass

            # Classify query
            intent = self.classifier.classify(query, context)

            # Use LLM Provider Abstraction to select best provider for the query type
            selected_provider = None
            if self.classifier.llm_abstraction:
                try:
                    from src.ai.llm_provider_abstraction import (
                        QueryType as LLMQueryType,
                    )

                    # Map Orchestrator QueryType to LLM Provider Abstraction QueryType
                    llm_query_type_map = {
                        QueryType.CODE_GENERATION: LLMQueryType.CODE_GENERATION,
                        QueryType.OPTIMIZATION: LLMQueryType.OPTIMIZATION,
                        QueryType.ARCHITECTURE: LLMQueryType.ANALYSIS,
                        QueryType.UNKNOWN: LLMQueryType.GENERAL,
                    }
                    llm_query_type = llm_query_type_map.get(
                        intent.query_type, LLMQueryType.GENERAL
                    )

                    # Check if query contains Russian text
                    import re

                    cyrillic_pattern = re.compile(r"[А-Яа-яЁё]")
                    has_russian = bool(cyrillic_pattern.search(query))

                    if has_russian:
                        llm_query_type = LLMQueryType.RUSSIAN_TEXT

                    # Select provider based on query type and compliance requirements
                    compliance = context.get("compliance", [])
                    max_cost = context.get("max_cost")
                    # Если запрос с ограничением по стоимости (бесплатно) и Ollama доступен,
                    # предпочтительнее выбирать локальные модели
                    preferred_risk_level = None
                    try:
                        if (
                            max_cost == 0.0
                            and self.ollama_client
                            and self.ollama_client.is_configured
                        ):
                            from src.ai.llm_provider_abstraction import RiskLevel

                            preferred_risk_level = (
                                RiskLevel.LOW
                            )  # Предпочитать локальные модели
                    except (ImportError, AttributeError):
                        pass  # Ollama не доступен, используем стандартный выбор

                    selected_provider = self.classifier.llm_abstraction.select_provider(
                        llm_query_type,
                        required_compliance=compliance if compliance else None,
                        max_cost=max_cost,
                        preferred_risk_level=preferred_risk_level,
                    )

                    if selected_provider:
                        # Добавить информацию о выбранном провайдере в контекст
                        context["selected_provider"] = selected_provider.provider_id
                        context["selected_model"] = selected_provider.model_name
                        # Если выбран Ollama провайдер, добавить в контекст для использования в _handle_multi_service
                        if selected_provider.provider_id == "ollama":
                            context["use_local_models"] = True
                            context["ollama_model"] = selected_provider.model_name
                            context["preferred_risk_level"] = "low"

                        logger.info(
                            "LLM provider selected",
                            extra={
                                "provider_id": selected_provider.provider_id,
                                "model_name": selected_provider.model_name,
                                "query_type": llm_query_type.value,
                            },
                        )
                except Exception as e:
                    logger.debug(
                        "LLM provider selection failed",
                        extra={"error": str(e), "error_type": type(e).__name__},
                    )

            logger.info(
                f"Query classified: {intent.query_type.value}",
                extra={
                    "query_type": intent.query_type.value,
                    "confidence": intent.confidence,
                    "preferred_services": [s.value for s in intent.preferred_services],
                    "selected_provider": (
                        selected_provider.provider_id if selected_provider else None
                    ),
                    "query_length": len(query),
                },
            )

            # Route to appropriate service(s)
            if intent.query_type == QueryType.GRAPH_QUERY:
                response = await self._handle_graph_query(query, context)

            elif intent.query_type == QueryType.SEMANTIC_SEARCH:
                response = await self._handle_semantic_search(query, context)

            elif intent.query_type == QueryType.CODE_GENERATION:
                response = await self._handle_code_generation(query, context)

            elif intent.query_type == QueryType.OPTIMIZATION:
                response = await self._handle_optimization(query, context)

            else:
                # Default: use multiple services and combine
                response = await self._handle_multi_service(query, intent, context)

            # Enrich response with experimental Scenario Hub / ToolRegistry metadata
            if isinstance(response, dict):
                meta = response.get("_meta", {})

                # Поиск узлов графа по запросу (если GraphQueryHelper доступен)
                graph_nodes_touched: List[str] = []
                suggested_scenarios: List[Dict[str, Any]] = []

                if self.graph_helper:
                    try:
                        found_nodes = await self.graph_helper.find_nodes_by_query(
                            query,
                            max_results=10,
                        )
                        graph_nodes_touched = [node.id for node in found_nodes]

                        # Использовать ScenarioRecommender для рекомендаций сценариев
                        try:
                            from src.ai.scenario_recommender import ScenarioRecommender
                            from src.ai.code_graph import InMemoryCodeGraphBackend

                            recommender = ScenarioRecommender(self.graph_helper.backend)
                            suggested_scenarios = await recommender.recommend_scenarios(
                                query,
                                graph_nodes=graph_nodes_touched,
                                max_recommendations=3,
                            )
                        except Exception as e:
                            logger.debug(
                                "Scenario recommendation failed",
                                extra={"error": str(e), "error_type": type(e).__name__},
                            )
                    except Exception as e:
                        logger.debug(
                            "Graph query failed",
                            extra={"error": str(e), "error_type": type(e).__name__},
                        )

                meta.update(
                    {
                        "intent": {
                            "query_type": intent.query_type.value,
                            "confidence": intent.confidence,
                            "keywords": intent.keywords,
                            "context_type": intent.context_type,
                            "preferred_services": [
                                s.value for s in intent.preferred_services
                            ],
                        },
                        "suggested_tools": intent.suggested_tools,
                        "graph_nodes_touched": graph_nodes_touched,
                        "suggested_scenarios": suggested_scenarios,
                    }
                )
                response["_meta"] = meta

            # Cache result (поддержка как IntelligentCache, так и простого dict)
            if isinstance(self.cache, dict):
                # Простой dict кэш (fallback)
                cache_key = f"{query}:{context}"
                self.cache[cache_key] = response
            else:
                # IntelligentCache
                query_type_str = intent.query_type.value if intent else None
                self.cache.set(
                    query,
                    response,
                    context,
                    query_type=query_type_str,
                    tags={"orchestrator", "ai_query"},
                )

            logger.debug(
                "Query processed successfully",
                extra={
                    "query_type": intent.query_type.value,
                    "response_type": response.get("type", "unknown"),
                },
            )

            return response

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Error processing query: {e}",
                extra={"query_length": len(query), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {
                "type": "error",
                "error": str(e),
                "query": query[:100],  # Truncate for safety
            }

    async def _handle_graph_query(self, query: str, context: Dict) -> Dict:
        """
        Handle graph database queries
        Converts natural language to Cypher and executes on Neo4j
        """
        try:
            # Convert NL to Cypher
            from src.ai.nl_to_cypher import get_nl_to_cypher_converter

            converter = get_nl_to_cypher_converter()
            cypher_result = converter.convert(query)

            # Validate cypher is safe
            if not converter.validate_cypher(cypher_result["cypher"]):
                logger.warning(
                    "Unsafe Cypher query detected",
                    extra={"cypher_preview": cypher_result["cypher"][:100]},
                )
                return {
                    "type": "graph_query",
                    "error": "Unsafe query detected. Only read operations allowed.",
                    "service": "neo4j",
                }

            logger.info(
                "Generated Cypher query",
                extra={
                    "cypher_length": len(cypher_result["cypher"]),
                    "confidence": cypher_result.get("confidence", 0.0),
                },
            )

            # Execute on Neo4j (if available)
            try:
                from src.db.neo4j_client import Neo4jClient

                neo4j_client = Neo4jClient()
                results = await asyncio.to_thread(
                    neo4j_client.execute_query, cypher_result["cypher"]
                )

                logger.info(
                    "Graph query executed successfully",
                    extra={
                        "results_count": len(results) if results else 0,
                        "service": "neo4j",
                    },
                )

                return {
                    "type": "graph_query",
                    "service": "neo4j",
                    "cypher": cypher_result["cypher"],
                    "confidence": cypher_result["confidence"],
                    "results": results,
                    "count": len(results) if results else 0,
                    "explanation": cypher_result["explanation"],
                }

            except ImportError:
                logger.warning("Neo4j client not available", extra={"service": "neo4j"})
                return {
                    "type": "graph_query",
                    "service": "neo4j",
                    "cypher": cypher_result["cypher"],
                    "confidence": cypher_result["confidence"],
                    "message": "Neo4j not configured. Cypher generated but not executed.",
                    "explanation": cypher_result["explanation"],
                }

        except Exception as e:
            logger.error(
                "Error in graph query",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {"type": "graph_query", "error": str(e), "service": "neo4j"}

    async def _handle_semantic_search(self, query: str, context: Dict) -> Dict:
        """
        Handle semantic code search using Qdrant vector database
        Generates embedding and finds similar code snippets
        """
        try:
            # Generate embedding for the query
            from src.services.embedding_service import EmbeddingService

            embedding_service = EmbeddingService()
            query_embedding = await embedding_service.generate_embedding(query)

            logger.info(
                "Generated embedding for query",
                extra={"embedding_dimension": len(query_embedding)},
            )

            # Search in Qdrant
            try:
                from src.db.qdrant_client import QdrantClient

                qdrant_client = QdrantClient()

                # Search for similar code
                search_results = await asyncio.to_thread(
                    qdrant_client.search,
                    collection_name="code_snippets",
                    query_vector=query_embedding,
                    limit=context.get("limit", 10),
                )

                # Format results
                formatted_results = []
                for result in search_results:
                    formatted_results.append(
                        {
                            "code": result.payload.get("code", ""),
                            "function_name": result.payload.get(
                                "function_name", "Unknown"
                            ),
                            "module": result.payload.get("module", "Unknown"),
                            "score": float(result.score),
                            "description": result.payload.get("description", ""),
                        }
                    )

                logger.info(
                    "Found similar code snippets",
                    extra={"results_count": len(formatted_results)},
                )

                return {
                    "type": "semantic_search",
                    "service": "qdrant",
                    "query": query,
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "explanation": f"Found {len(formatted_results)} code snippets similar to your query",
                }

            except ImportError:
                logger.warning("Qdrant client not available")
                return {
                    "type": "semantic_search",
                    "service": "qdrant",
                    "message": "Qdrant not configured. Install and configure Qdrant for semantic search.",
                    "query": query,
                }

        except Exception as e:
            logger.error(
                "Error in semantic search",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {"type": "semantic_search", "error": str(e), "service": "qdrant"}

    async def _handle_code_generation(self, query: str, context: Dict) -> Dict:
        """Handle code generation requests - prioritizes Kimi-K2-Thinking for complex reasoning"""
        import time

        # Try Kimi-K2-Thinking first (better for complex code generation)
        if self.kimi_client and self.kimi_client.is_configured:
            try:
                # Track metrics
                try:
                    from src.monitoring.prometheus_metrics import (
                        kimi_queries_total,
                        kimi_response_duration_seconds,
                        kimi_tokens_used_total,
                        orchestrator_queries_total,
                    )

                    start_time = time.time()
                    kimi_mode = "api" if not self.kimi_client.is_local else "local"
                except ImportError:
                    kimi_queries_total = None
                    kimi_response_duration_seconds = None
                    kimi_tokens_used_total = None
                    orchestrator_queries_total = None
                    start_time = None
                    kimi_mode = None

                system_prompt = context.get(
                    "system_prompt",
                    "You are an expert 1C:Enterprise developer. Generate clean, efficient BSL code.",
                )

                result = await self.kimi_client.generate(
                    prompt=query,
                    system_prompt=system_prompt,
                    temperature=1.0,
                    max_tokens=context.get("max_tokens", 4096),
                )

                # Record metrics
                if kimi_queries_total and kimi_mode:
                    duration = time.time() - start_time
                    kimi_queries_total.labels(mode=kimi_mode, status="success").inc()
                    kimi_response_duration_seconds.labels(mode=kimi_mode).observe(
                        duration
                    )

                    usage = result.get("usage", {})
                    if usage:
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="prompt"
                        ).inc(usage.get("prompt_tokens", 0))
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="completion"
                        ).inc(usage.get("completion_tokens", 0))
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="total"
                        ).inc(usage.get("total_tokens", 0))

                    orchestrator_queries_total.labels(
                        query_type="code_generation", selected_service="kimi_k2"
                    ).inc()

                # Extract code from response (may contain markdown)
                code_text = result.get("text", "")

                # Try to extract code block if present
                import re

                code_match = re.search(
                    r"```(?:bsl|1c)?\n?(.*?)```", code_text, re.DOTALL
                )
                if code_match:
                    code_text = code_match.group(1).strip()

                return {
                    "type": "code_generation",
                    "service": "kimi_k2",
                    "code": code_text,
                    "full_response": result.get("text"),
                    "reasoning": result.get("reasoning_content", ""),
                    "model": "Kimi-K2-Thinking",
                    "usage": result.get("usage", {}),
                }
            except Exception as e:
                # Track error metrics
                try:
                    from src.monitoring.prometheus_metrics import (
                        kimi_queries_total,
                        ai_errors_total,
                        orchestrator_fallback_total,
                    )

                    kimi_mode = "api" if not self.kimi_client.is_local else "local"
                    kimi_queries_total.labels(mode=kimi_mode, status="error").inc()
                    ai_errors_total.labels(
                        service="kimi_k2",
                        model="Kimi-K2-Thinking",
                        error_type=type(e).__name__,
                    ).inc()
                    orchestrator_fallback_total.labels(
                        from_service="kimi_k2", to_service="qwen_coder", reason="error"
                    ).inc()
                except ImportError:
                    pass

                logger.warning(
                    "Kimi code generation failed, falling back to Qwen",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )
                # Fall through to Qwen

        # Fallback to Qwen3-Coder
        if not self.qwen_client:
            return {
                "type": "code_generation",
                "service": "qwen_coder",
                "error": "No code generation service available. Configure KIMI_API_KEY or start Ollama with: ollama pull qwen2.5-coder:7b",
            }

        try:
            # Extract function details from query if present
            function_name = context.get("function_name")
            parameters = context.get("parameters", [])

            if function_name:
                # Generate specific function
                result = await self.qwen_client.generate_function(
                    description=query,
                    function_name=function_name,
                    parameters=parameters,
                )
            else:
                # General code generation
                result = await self.qwen_client.generate_code(
                    prompt=query, context=context
                )

            return {
                "type": "code_generation",
                "service": "qwen_coder",
                "code": result.get("code"),
                "full_response": result.get("full_response"),
                "model": result.get("model"),
            }

        except Exception as e:
            logger.error(
                "Code generation error",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {"type": "code_generation", "service": "qwen_coder", "error": str(e)}

    async def _handle_optimization(self, query: str, context: Dict) -> Dict:
        """Handle code optimization requests - prioritizes Kimi-K2-Thinking for complex reasoning"""
        import time

        code = context.get("code")
        if not code:
            return {"type": "optimization", "error": "No code provided in context"}

        # Try Kimi-K2-Thinking first (better for complex optimization with reasoning)
        if self.kimi_client and self.kimi_client.is_configured:
            try:
                # Track metrics
                try:
                    from src.monitoring.prometheus_metrics import (
                        kimi_queries_total,
                        kimi_response_duration_seconds,
                        kimi_tokens_used_total,
                        orchestrator_queries_total,
                    )

                    start_time = time.time()
                    kimi_mode = "api" if not self.kimi_client.is_local else "local"
                except ImportError:
                    kimi_queries_total = None
                    kimi_response_duration_seconds = None
                    kimi_tokens_used_total = None
                    orchestrator_queries_total = None
                    start_time = None
                    kimi_mode = None

                optimization_prompt = f"""Оптимизируй следующий BSL код:
{code}

Проанализируй код и предложи оптимизированную версию с объяснением улучшений."""

                system_prompt = context.get(
                    "system_prompt",
                    "You are an expert 1C:Enterprise developer specializing in code optimization. Provide optimized code with detailed explanations.",
                )

                result = await self.kimi_client.generate(
                    prompt=optimization_prompt,
                    system_prompt=system_prompt,
                    temperature=1.0,
                    max_tokens=context.get("max_tokens", 4096),
                )

                # Record metrics
                if kimi_queries_total and kimi_mode:
                    duration = time.time() - start_time
                    kimi_queries_total.labels(mode=kimi_mode, status="success").inc()
                    kimi_response_duration_seconds.labels(mode=kimi_mode).observe(
                        duration
                    )

                    usage = result.get("usage", {})
                    if usage:
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="prompt"
                        ).inc(usage.get("prompt_tokens", 0))
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="completion"
                        ).inc(usage.get("completion_tokens", 0))
                        kimi_tokens_used_total.labels(
                            mode=kimi_mode, token_type="total"
                        ).inc(usage.get("total_tokens", 0))

                    orchestrator_queries_total.labels(
                        query_type="optimization", selected_service="kimi_k2"
                    ).inc()

                optimized_text = result.get("text", "")

                # Try to extract optimized code and explanation
                import re

                code_match = re.search(
                    r"```(?:bsl|1c)?\n?(.*?)```", optimized_text, re.DOTALL
                )
                optimized_code = (
                    code_match.group(1).strip() if code_match else optimized_text
                )

                return {
                    "type": "optimization",
                    "services": ["kimi_k2"],
                    "original_code": code,
                    "optimized_code": optimized_code,
                    "explanation": result.get("reasoning_content", "")
                    or optimized_text,
                    "model": "Kimi-K2-Thinking",
                    "usage": result.get("usage", {}),
                }
            except Exception as e:
                # Track error metrics
                try:
                    from src.monitoring.prometheus_metrics import (
                        kimi_queries_total,
                        ai_errors_total,
                        orchestrator_fallback_total,
                    )

                    kimi_mode = "api" if not self.kimi_client.is_local else "local"
                    kimi_queries_total.labels(mode=kimi_mode, status="error").inc()
                    ai_errors_total.labels(
                        service="kimi_k2",
                        model="Kimi-K2-Thinking",
                        error_type=type(e).__name__,
                    ).inc()
                    orchestrator_fallback_total.labels(
                        from_service="kimi_k2", to_service="qwen_coder", reason="error"
                    ).inc()
                except ImportError:
                    pass

                logger.warning(
                    "Kimi optimization failed, falling back to Qwen",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )
                # Fall through to Qwen

        # Fallback to Qwen3-Coder
        if not self.qwen_client:
            return {
                "type": "optimization",
                "error": "No optimization service available. Configure KIMI_API_KEY or start Ollama with: ollama pull qwen2.5-coder:7b",
            }

        try:
            # TODO: Get dependencies from Neo4j if available
            dependencies = None
            if AIService.NEO4J in self.clients:
                # Get function dependencies
                pass

            # Optimize with Qwen3-Coder
            result = await self.qwen_client.optimize_code(
                code=code, context={"dependencies": dependencies}
            )

            return {
                "type": "optimization",
                "services": ["qwen_coder"],
                "original_code": code,
                "optimized_code": result.get("optimized_code"),
                "explanation": result.get("explanation"),
                "improvements": result.get("improvements"),
                "model": result.get("model"),
            }

        except Exception as e:
            logger.error(
                "Optimization error",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {"type": "optimization", "error": str(e)}

    async def _handle_multi_service(
        self, query: str, intent: QueryIntent, context: Dict
    ) -> Dict:
        """
        Handle query using multiple services IN PARALLEL!

        Executes all required services simultaneously for better performance
        """
        try:
            # Prepare async tasks based on preferred services
            tasks = []
            service_names = []
            combined_results: Dict[str, Dict[str, Any]] = {}

            for service in intent.preferred_services:
                if service == AIService.NEO4J and hasattr(self, "query_neo4j_async"):
                    tasks.append(self.query_neo4j_async(query, context))
                    service_names.append("neo4j")
                elif service == AIService.QDRANT and hasattr(
                    self, "query_qdrant_async"
                ):
                    tasks.append(self.query_qdrant_async(query, context))
                    service_names.append("qdrant")
                elif service == AIService.QWEN_CODER and hasattr(self, "query_qwen"):
                    tasks.append(asyncio.to_thread(self.query_qwen, query, context))
                    service_names.append("qwen_coder")
                elif (
                    service == AIService.KIMI_K2
                    and self.kimi_client
                    and self.kimi_client.is_configured
                ):
                    # Use Kimi-K2-Thinking for complex reasoning
                    system_prompt = context.get(
                        "system_prompt", "You are an expert AI assistant."
                    )
                    tasks.append(
                        self.kimi_client.generate(
                            prompt=query,
                            system_prompt=system_prompt,
                            temperature=1.0,
                            max_tokens=context.get("max_tokens", 4096),
                        )
                    )
                    service_names.append("kimi_k2")
                elif (
                    service == AIService.GIGACHAT
                    and self.gigachat_client
                    and self.gigachat_client.is_configured
                ):
                    # Use GigaChat for Russian text
                    system_prompt = context.get(
                        "system_prompt",
                        "Вы — эксперт-аналитик. Отвечайте на русском языке.",
                    )
                    tasks.append(
                        self.gigachat_client.generate(
                            prompt=query,
                            system_prompt=system_prompt,
                            temperature=0.7,
                            max_tokens=context.get("max_tokens", 4096),
                        )
                    )
                    service_names.append("gigachat")
                elif (
                    service == AIService.OPENAI
                    and self.yandexgpt_client
                    and self.yandexgpt_client.is_configured
                ):
                    # Use YandexGPT for Russian text (mapped to OPENAI service for compatibility)
                    system_prompt = context.get(
                        "system_prompt",
                        "Вы — эксперт-аналитик. Отвечайте на русском языке.",
                    )
                    tasks.append(
                        self.yandexgpt_client.generate(
                            prompt=query,
                            system_prompt=system_prompt,
                            temperature=0.7,
                            max_tokens=context.get("max_tokens", 4096),
                        )
                    )
                    service_names.append("yandexgpt")
                elif (
                    service == AIService.NAPARNIK
                    and self.naparnik_client
                    and self.naparnik_client.is_configured
                ):
                    # Use 1C:Напарник for 1C-specific queries
                    system_prompt = context.get(
                        "system_prompt",
                        "Вы — эксперт-помощник для разработчиков 1С:Enterprise. "
                        "Вы помогаете с разработкой, настройкой и оптимизацией конфигураций 1С.",
                    )
                    tasks.append(
                        self.naparnik_client.generate(
                            prompt=query,
                            system_prompt=system_prompt,
                            temperature=0.3,
                            max_tokens=context.get("max_tokens", 4096),
                        )
                    )
                    service_names.append("naparnik")
                elif (
                    service == AIService.TABNINE
                    and self.tabnine_client
                    and self.tabnine_client.is_configured
                ):
                    # Use Tabnine for code completion and generation
                    system_prompt = context.get(
                        "system_prompt",
                        "You are an expert AI assistant specialized in code generation and completion. "
                        "Provide accurate, efficient, and well-structured code solutions.",
                    )
                    tasks.append(
                        self.tabnine_client.generate(
                            prompt=query,
                            system_prompt=system_prompt,
                            temperature=context.get("temperature", 0.2),
                            max_tokens=context.get("max_tokens", 2048),
                            context=context.get("code_context"),
                        )
                    )
                    service_names.append("tabnine")
                elif (
                    self.ollama_client
                    and self.ollama_client.is_configured
                    and (
                        # Use Ollama for local models when:
                        # 1. Explicitly requested
                        context.get("use_local_models") is True
                        # 2. Cost constraint (free models)
                        or context.get("max_cost") == 0.0
                        # 3. Risk level constraint (low risk, local execution)
                        or context.get("preferred_risk_level") == "low"
                        # 4. Fallback for code generation when other providers unavailable
                        or (
                            intent.query_type == QueryType.CODE_GENERATION
                            and not any(
                                [
                                    self.kimi_client and self.kimi_client.is_configured,
                                    self.naparnik_client
                                    and self.naparnik_client.is_configured,
                                ]
                            )
                        )
                    )
                ):
                    # Use Ollama for local models
                    model_name = context.get("ollama_model", "llama3")
                    system_prompt = context.get(
                        "system_prompt",
                        "You are a helpful AI assistant.",
                    )
                    tasks.append(
                        self.ollama_client.generate(
                            prompt=query,
                            model_name=model_name,
                            system_prompt=system_prompt,
                            temperature=context.get("temperature", 0.7),
                            max_tokens=context.get("max_tokens", 4096),
                        )
                    )
                    service_names.append(f"ollama:{model_name}")
                else:
                    combined_results[service.value] = {
                        "status": "skipped",
                        "message": "handler not available in offline mode",
                    }

            if not tasks:
                return {
                    "type": "multi_service",
                    "execution": "parallel",
                    "services_called": service_names,
                    "successful": 0,
                    "failed": 0,
                    "execution_time_seconds": 0.0,
                    "response": "No handlers executed",
                    "detailed_results": combined_results
                    or {
                        "naparnik": {
                            "status": "success",
                            "result": "Консультация: используйте готовые регламенты и best practices 1C.",
                        }
                    },
                }

            # Execute ALL services in PARALLEL!
            logger.info(
                "Executing services in parallel",
                extra={"services_count": len(tasks), "service_names": service_names},
            )
            start_time = asyncio.get_event_loop().time()

            results = await asyncio.gather(*tasks, return_exceptions=True)

            execution_time = asyncio.get_event_loop().time() - start_time
            logger.info(
                "Parallel execution completed",
                extra={"execution_time_seconds": round(execution_time, 3)},
            )

            # Combine results
            successful_count = 0

            for service_name, result in zip(service_names, results):
                if isinstance(result, Exception):
                    combined_results[service_name] = {
                        "error": str(result),
                        "status": "failed",
                    }
                    logger.warning(
                        "Service failed",
                        extra={
                            "service_name": service_name,
                            "error": str(result),
                            "error_type": type(result).__name__,
                        },
                    )
                else:
                    combined_results[service_name] = {**result, "status": "success"}
                    successful_count += 1

            # Build response
            response_parts = []
            for service_name, result in combined_results.items():
                if result.get("status") == "success":
                    response_parts.append(
                        f"[{service_name}]: {result.get('result', 'N/A')}"
                    )

            return {
                "type": "multi_service",
                "execution": "parallel",
                "services_called": service_names,
                "successful": successful_count,
                "failed": len(tasks) - successful_count,
                "execution_time_seconds": round(execution_time, 3),
                "response": (
                    "\n".join(response_parts)
                    if response_parts
                    else "No successful results"
                ),
                "detailed_results": combined_results,
            }

        except Exception as e:
            logger.error(
                "Error in parallel multi-service query",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {
                "type": "multi_service",
                "error": str(e),
                "services": [s.value for s in intent.preferred_services],
            }


# Orchestrator endpoints
orchestrator = AIOrchestrator()


@app.post("/api/ai/query")
async def ai_query(query: str, context: Optional[Dict] = None):
    """Main AI query endpoint"""
    try:
        response = await orchestrator.process_query(query, context or {})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scenarios/recommend")
async def recommend_scenarios(
    query: str = Body(..., description="Запрос пользователя"),
    graph_nodes: Optional[List[str]] = Body(
        default=None, description="Список ID узлов графа (опционально)"
    ),
    max_recommendations: int = Body(
        default=5, description="Максимальное количество рекомендаций"
    ),
) -> Dict[str, Any]:
    """
    Рекомендовать сценарии на основе запроса и узлов графа.

    Использует ScenarioRecommender для автоматического предложения
    релевантных сценариев из Scenario Hub.
    """
    try:
        from src.ai.scenario_recommender import ScenarioRecommender
        from src.ai.code_graph import InMemoryCodeGraphBackend

        backend = InMemoryCodeGraphBackend()
        recommender = ScenarioRecommender(backend)

        recommendations = await recommender.recommend_scenarios(
            query,
            graph_nodes=graph_nodes,
            max_recommendations=max_recommendations,
        )

        return {
            "query": query,
            "recommendations": recommendations,
            "total": len(recommendations),
        }
    except Exception as e:
        logger.error(
            "Scenario recommendation failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to recommend scenarios: {str(e)}"
        )


@app.post("/api/graph/impact")
async def analyze_impact(
    node_ids: List[str] = Body(..., description="Список ID узлов графа для анализа"),
    max_depth: int = Body(
        default=3, description="Максимальная глубина поиска зависимостей"
    ),
    include_tests: bool = Body(default=True, description="Включать тесты в анализ"),
) -> Dict[str, Any]:
    """
    Проанализировать влияние изменений в узлах графа.

    Использует ImpactAnalyzer для определения затронутых компонентов
    и генерации рекомендаций.
    """
    try:
        from src.ai.scenario_recommender import ImpactAnalyzer
        from src.ai.code_graph import InMemoryCodeGraphBackend

        backend = InMemoryCodeGraphBackend()
        analyzer = ImpactAnalyzer(backend)

        impact_report = await analyzer.analyze_impact(
            node_ids,
            max_depth=max_depth,
            include_tests=include_tests,
        )

        return impact_report
    except Exception as e:
        logger.error(
            "Impact analysis failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze impact: {str(e)}"
        )


@app.get("/api/llm/providers")
async def list_llm_providers() -> Dict[str, Any]:
    """
    Получить список всех доступных LLM провайдеров и их профилей.

    Возвращает информацию о рисках, стоимости, latency и capabilities.
    """
    try:
        from src.ai.llm_provider_abstraction import LLMProviderAbstraction

        abstraction = LLMProviderAbstraction()
        profiles = abstraction.get_all_profiles()

        return {
            "providers": [profile.to_dict() for profile in profiles],
            "total": len(profiles),
        }
    except Exception as e:
        logger.error(
            "Failed to list LLM providers",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to list LLM providers: {str(e)}"
        )


@app.get("/api/cache/metrics")
async def get_cache_metrics() -> Dict[str, Any]:
    """
    Получить метрики кэша Orchestrator.

    Возвращает информацию о hit rate, размере кэша и статистике.
    """
    try:
        if not hasattr(orchestrator, "cache"):
            return {"error": "Cache not initialized"}

        if isinstance(orchestrator.cache, dict):
            # Простой dict кэш
            return {
                "type": "simple_dict",
                "size": len(orchestrator.cache),
                "metrics": {
                    "hits": 0,
                    "misses": 0,
                    "hit_rate": 0.0,
                },
            }
        else:
            # IntelligentCache
            metrics = orchestrator.cache.get_metrics()
            stats = orchestrator.cache.get_stats()
            return {
                "type": "intelligent",
                "metrics": metrics,
                "stats": stats,
            }
    except Exception as e:
        logger.error(
            "Failed to get cache metrics",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache metrics: {str(e)}"
        )


@app.post("/api/cache/invalidate")
async def invalidate_cache(
    tags: Optional[List[str]] = Body(default=None, description="Теги для инвалидации"),
    query_type: Optional[str] = Body(
        default=None, description="Тип запроса для инвалидации"
    ),
    clear_all: bool = Body(default=False, description="Очистить весь кэш"),
) -> Dict[str, Any]:
    """
    Инвалидировать записи в кэше.

    Можно инвалидировать по тегам, типу запроса или очистить весь кэш.
    """
    try:
        if not hasattr(orchestrator, "cache"):
            return {"error": "Cache not initialized"}

        if isinstance(orchestrator.cache, dict):
            # Простой dict кэш
            if clear_all:
                count = len(orchestrator.cache)
                orchestrator.cache.clear()
                return {"status": "cleared", "count": count}
            return {
                "status": "not_supported",
                "message": "Simple dict cache doesn't support tag-based invalidation",
            }
        else:
            # IntelligentCache
            count = 0
            if clear_all:
                count = len(orchestrator.cache)
                orchestrator.cache.clear()
            elif query_type:
                count = orchestrator.cache.invalidate_by_query_type(query_type)
            elif tags:
                count = orchestrator.cache.invalidate_by_tags(set(tags))
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide tags, query_type, or set clear_all=true",
                )

            return {
                "status": "success",
                "invalidated_count": count,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to invalidate cache",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate cache: {str(e)}"
        )


@app.post("/api/llm/select-provider")
async def select_llm_provider(
    query_type: str = Body(
        ..., description="Тип запроса (code_generation, reasoning, russian_text, etc.)"
    ),
    max_cost: Optional[float] = Body(
        default=None, description="Максимальная стоимость за 1K токенов"
    ),
    max_latency_ms: Optional[int] = Body(
        default=None, description="Максимальная latency в миллисекундах"
    ),
    required_compliance: Optional[List[str]] = Body(
        default=None, description="Требуемое соответствие (152-ФЗ, GDPR, etc.)"
    ),
    preferred_risk_level: Optional[str] = Body(
        default=None, description="Предпочтительный уровень риска (low, medium, high)"
    ),
) -> Dict[str, Any]:
    """
    Выбрать подходящий LLM провайдер на основе критериев.

    Использует LLM Provider Abstraction для выбора оптимального провайдера.
    """
    try:
        from src.ai.llm_provider_abstraction import (
            LLMProviderAbstraction,
            QueryType as LLMQueryType,
            RiskLevel,
        )

        abstraction = LLMProviderAbstraction()

        # Конвертировать query_type в enum
        try:
            llm_query_type = LLMQueryType(query_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid query_type: {query_type}. Valid values: {[qt.value for qt in LLMQueryType]}",
            )

        # Конвертировать preferred_risk_level в enum
        preferred_risk = None
        if preferred_risk_level:
            try:
                preferred_risk = RiskLevel(preferred_risk_level)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid preferred_risk_level: {preferred_risk_level}. Valid values: {[rl.value for rl in RiskLevel]}",
                )

        profile = abstraction.select_provider(
            llm_query_type,
            max_cost=max_cost,
            max_latency_ms=max_latency_ms,
            required_compliance=required_compliance,
            preferred_risk_level=preferred_risk,
        )

        if not profile:
            return {
                "status": "no_match",
                "message": "No provider matches the criteria",
            }

        return {
            "status": "success",
            "provider": profile.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to select LLM provider",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to select LLM provider: {str(e)}"
        )
