# [NEXUS IDENTITY] ID: -1234567890123456789 | DATE: 2025-01-XX

"""
DevOps & AI Evolution API
==========================

API endpoints для:
- DevOps Agent (анализ инфраструктуры)
- Self-Evolving AI (автоматическое улучшение системы)
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.ai.agents.devops_agent_extended import DevOpsAgentExtended
from src.ai.llm_provider_abstraction import LLMProviderAbstraction
from src.ai.self_evolving_ai import SelfEvolvingAI
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(tags=["DevOps & AI Evolution"])

# Глобальные экземпляры (lazy initialization)
_devops_agent: Optional[DevOpsAgentExtended] = None
_self_evolving_ai: Optional[SelfEvolvingAI] = None


def get_devops_agent() -> DevOpsAgentExtended:
    """Получить экземпляр DevOps Agent (singleton)"""
    global _devops_agent
    if _devops_agent is None:
        _devops_agent = DevOpsAgentExtended()
    return _devops_agent


def get_self_evolving_ai() -> SelfEvolvingAI:
    """Получить экземпляр Self-Evolving AI (singleton)"""
    global _self_evolving_ai
    if _self_evolving_ai is None:
        # Пока используем None, так как LLMProviderAbstraction не имеет метода generate()
        # TODO: Реализовать метод generate() в LLMProviderAbstraction
        _self_evolving_ai = SelfEvolvingAI(llm_provider=None)
    return _self_evolving_ai


# Request/Response Models
class InfrastructureAnalysisResponse(BaseModel):
    """Ответ анализа инфраструктуры"""
    status: str
    static_analysis: Dict[str, Any]
    runtime_status: list
    services_status: Dict[str, Any]
    recommendations: list


class EvolutionRequest(BaseModel):
    """Запрос на эволюцию AI"""
    force: bool = Field(default=False, description="Принудительный запуск даже если система здорова")


class EvolutionResponse(BaseModel):
    """Ответ эволюции AI"""
    status: str
    stage: str
    metrics: Optional[Dict[str, Any]] = None
    improvements: list = []
    message: str


# DevOps Endpoints
@router.post("/devops/infrastructure/analyze", response_model=InfrastructureAnalysisResponse)
async def analyze_infrastructure(
    compose_file: Optional[str] = Query(
        None,
        description="Путь к docker-compose.yml (по умолчанию ищется в корне проекта)"
    )
) -> InfrastructureAnalysisResponse:
    """
    Анализ Docker инфраструктуры
    
    Выполняет:
    - Статический анализ docker-compose.yml (best practices, проблемы безопасности)
    - Проверку реального статуса контейнеров (docker ps)
    - Корреляцию между конфигурацией и runtime
    - Генерацию рекомендаций
    """
    try:
        agent = get_devops_agent()
        
        # Определяем путь к compose файлу
        if not compose_file:
            # Ищем в корне проекта
            project_root = Path.cwd()
            possible_paths = [
                project_root / "docker-compose.yml",
                project_root / "docker-compose.mvp.yml",
                project_root / "docker-compose.yaml",
            ]
            
            compose_file = None
            for path in possible_paths:
                if path.exists():
                    compose_file = str(path)
                    break
            
            if not compose_file:
                raise HTTPException(
                    status_code=404,
                    detail="docker-compose.yml not found. Please specify compose_file parameter."
                )
        
        # Проверяем существование файла
        if not Path(compose_file).exists():
            raise HTTPException(status_code=404, detail=f"File not found: {compose_file}")
        
        # Выполняем анализ
        result = await agent.analyze_local_infrastructure(compose_file_path=compose_file)
        
        logger.info(
            "Infrastructure analysis completed",
            extra={
                "compose_file": compose_file,
                "services_count": result.get("service_count", 0),
                "issues_count": len(result.get("security_issues", [])) + len(result.get("performance_issues", []))
            }
        )
        
        return InfrastructureAnalysisResponse(
            status="success",
            static_analysis=result.get("static_analysis", {}),
            runtime_status=result.get("runtime_containers", []),
            services_status=result.get("services_status", {}),
            recommendations=result.get("recommendations", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Infrastructure analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/devops/infrastructure/status")
async def get_infrastructure_status() -> Dict[str, Any]:
    """
    Быстрая проверка статуса контейнеров (без анализа compose файла)
    """
    try:
        agent = get_devops_agent()
        containers = await agent.docker_analyzer.check_runtime_status()
        
        return {
            "status": "success",
            "containers": containers,
            "count": len(containers)
        }
    except Exception as e:
        logger.error(f"Failed to get infrastructure status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Self-Evolving AI Endpoints
@router.post("/ai/evolve", response_model=EvolutionResponse)
async def evolve_ai(request: Optional[EvolutionRequest] = None) -> EvolutionResponse:
    """
    Запуск цикла эволюции Self-Evolving AI
    
    Self-Evolving AI:
    1. Анализирует производительность системы
    2. Генерирует улучшения
    3. Тестирует улучшения
    4. Внедряет успешные изменения
    
    Args:
        force: Если True, запускает эволюцию даже если система здорова
    """
    try:
        if request is None:
            request = EvolutionRequest()
        
        evo_ai = get_self_evolving_ai()
        
        # Проверяем, не запущена ли уже эволюция
        if evo_ai._is_evolving:
            return EvolutionResponse(
                status="in_progress",
                stage=evo_ai._evolution_stage.value,
                message="Evolution already in progress"
            )
        
        # Проверяем доступность LLM
        if evo_ai.llm_provider is None:
            # Если LLM недоступен, возвращаем только метрики (без генерации улучшений)
            metrics = await evo_ai._analyze_performance()
            return EvolutionResponse(
                status="partial",
                stage="analyzing",
                metrics={
                    "accuracy": metrics.accuracy,
                    "error_rate": metrics.error_rate,
                    "latency_ms": metrics.latency_ms,
                    "throughput": metrics.throughput,
                    "user_satisfaction": metrics.user_satisfaction,
                },
                improvements=[],
                message="LLM provider not configured. Only performance analysis available."
            )
        
        # Запускаем эволюцию
        result = await evo_ai.evolve()
        
        logger.info(
            "AI evolution completed",
            extra={
                "status": result.get("status"),
                "improvements_count": len(result.get("improvements", []))
            }
        )
        
        return EvolutionResponse(
            status=result.get("status", "completed"),
            stage=result.get("stage", "completed"),
            metrics=result.get("metrics"),
            improvements=result.get("improvements", []),
            message=result.get("message", "Evolution completed successfully")
        )
        
    except Exception as e:
        logger.error(f"AI evolution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evolution failed: {str(e)}")


@router.get("/ai/evolve/status")
async def get_evolution_status() -> Dict[str, Any]:
    """
    Получить текущий статус Self-Evolving AI
    """
    try:
        evo_ai = get_self_evolving_ai()
        
        # Получаем последние метрики производительности
        latest_metrics = None
        if evo_ai._performance_history:
            latest = evo_ai._performance_history[-1]
            latest_metrics = {
                "accuracy": latest.accuracy,
                "error_rate": latest.error_rate,
                "latency_ms": latest.latency_ms,
                "throughput": latest.throughput,
                "user_satisfaction": latest.user_satisfaction,
            }
        
        return {
            "is_evolving": evo_ai._is_evolving,
            "current_stage": evo_ai._evolution_stage.value,
            "performance_history_count": len(evo_ai._performance_history),
            "improvements_count": len(evo_ai._improvements),
            "latest_metrics": latest_metrics
        }
    except Exception as e:
        logger.error(f"Failed to get evolution status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/evolve/metrics")
async def get_evolution_metrics() -> Dict[str, Any]:
    """
    Получить историю метрик производительности
    """
    try:
        evo_ai = get_self_evolving_ai()
        
        metrics_history = []
        for metrics in evo_ai._performance_history:
            metrics_history.append({
                "accuracy": metrics.accuracy,
                "error_rate": metrics.error_rate,
                "latency_ms": metrics.latency_ms,
                "throughput": metrics.throughput,
                "user_satisfaction": metrics.user_satisfaction,
            })
        
        return {
            "count": len(metrics_history),
            "history": metrics_history
        }
    except Exception as e:
        logger.error(f"Failed to get evolution metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

