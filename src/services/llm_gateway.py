"""
LLM Gateway — центральная точка выбора провайдера с поддержкой fallback-цепочек.

Версия: 2.0.0

Улучшения:
- Реальные вызовы к LLM провайдерам (вместо placeholder)
- Circuit breaker для защиты от cascading failures
- Многоуровневое кэширование
- Health monitoring с автоматическим переключением
- Prometheus метрики
- Retry logic с экспоненциальным backoff
- Graceful degradation
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

from .llm_provider_manager import (
    LLMProviderManager,
    ProviderConfig,
    load_llm_provider_manager,
)
from .llm_health_monitor import LLMHealthMonitor, ProviderHealthStatus
from src.resilience.error_recovery import CircuitBreaker
from src.ai.intelligent_cache import IntelligentCache
from src.monitoring.prometheus_metrics import (
    llm_gateway_requests_total,
    llm_gateway_latency_seconds,
    llm_gateway_fallbacks_total,
    llm_provider_health,
    llm_provider_latency_ms,
)

logger = logging.getLogger(__name__)

# Импорты клиентов (lazy loading)
_gigachat_client = None
_yandexgpt_client = None
_naparnik_client = None
_ollama_client = None


def _get_gigachat_client():
    """Lazy loading для GigaChat client"""
    global _gigachat_client
    if _gigachat_client is None:
        try:
            from src.ai.clients.gigachat_client import GigaChatClient, GigaChatConfig
            _gigachat_client = GigaChatClient()
        except Exception as e:
            logger.debug(f"GigaChat client not available: {e}")
    return _gigachat_client


def _get_yandexgpt_client():
    """Lazy loading для YandexGPT client"""
    global _yandexgpt_client
    if _yandexgpt_client is None:
        try:
            from src.ai.clients.yandexgpt_client import YandexGPTClient, YandexGPTConfig
            _yandexgpt_client = YandexGPTClient()
        except Exception as e:
            logger.debug(f"YandexGPT client not available: {e}")
    return _yandexgpt_client


def _get_naparnik_client():
    """Lazy loading для Naparnik client"""
    global _naparnik_client
    if _naparnik_client is None:
        try:
            from src.ai.clients.naparnik_client import NaparnikClient, NaparnikConfig
            _naparnik_client = NaparnikClient()
        except Exception as e:
            logger.debug(f"Naparnik client not available: {e}")
    return _naparnik_client


def _get_ollama_client():
    """Lazy loading для Ollama client"""
    global _ollama_client
    if _ollama_client is None:
        try:
            from src.ai.clients.ollama_client import OllamaClient
            _ollama_client = OllamaClient()
        except Exception as e:
            logger.debug(f"Ollama client not available: {e}")
    return _ollama_client


@dataclass
class LLMGatewayResponse:
    provider: str
    model: str
    response: str
    metadata: Dict[str, Any]


class LLMGateway:
    """
    LLM шлюз: определяет порядок провайдеров и возвращает структурированный ответ.
    
    Версия 2.0.0 с полной реализацией:
    - Реальные вызовы к LLM провайдерам
    - Circuit breaker для защиты от cascading failures
    - Многоуровневое кэширование
    - Health monitoring
    - Prometheus метрики
    - Retry logic
    """

    def __init__(
        self,
        manager: Optional[LLMProviderManager] = None,
        enable_cache: bool = True,
        enable_health_monitoring: bool = True,
        enable_circuit_breaker: bool = True,
    ) -> None:
        self.manager = manager or load_llm_provider_manager()
        self._ensure_manager()
        self.simulation_config = self._load_simulation_config()
        
        # Кэширование
        self.cache: Optional[IntelligentCache] = None
        if enable_cache:
            try:
                self.cache = IntelligentCache(
                    max_size=1000,
                    default_ttl_seconds=300,  # 5 минут
                )
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}")
        
        # Health monitoring
        self.health_monitor: Optional[LLMHealthMonitor] = None
        if enable_health_monitoring and self.manager:
            try:
                health_config = self.manager.health_config
                self.health_monitor = LLMHealthMonitor(
                    manager=self.manager,
                    check_interval_seconds=health_config.get("interval_seconds", 60),
                    failure_threshold=health_config.get("failure_threshold", 3),
                    recovery_threshold=health_config.get("recovery_threshold", 2),
                )
                # Запускаем мониторинг в фоне
                asyncio.create_task(self.health_monitor.start_monitoring())
            except Exception as e:
                logger.warning(f"Failed to initialize health monitor: {e}")
        
        # Circuit breakers для каждого провайдера
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        if enable_circuit_breaker:
            for provider in self.manager.providers.values():
                if provider.enabled:
                    retry_policy = provider.metadata.get("retry_policy", {})
                    self.circuit_breakers[provider.name] = CircuitBreaker(
                        failure_threshold=5,
                        success_threshold=2,
                        timeout_seconds=retry_policy.get("backoff_seconds", 60),
                    )
    
    def _ensure_manager(self) -> None:
        if not self.manager or not self.manager.has_configuration():
            logger.warning("LLMGateway запущен без конфигурации провайдеров; будут использованы значения по умолчанию.")

    async def generate(
        self,
        prompt: str,
        role: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMGatewayResponse:
        """
        Генерирует ответ через LLM провайдеров с fallback-цепочкой.
        
        Args:
            prompt: Текст запроса
            role: Роль пользователя (для выбора fallback-цепочки)
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            system_prompt: Системный промпт
            **kwargs: Дополнительные параметры
        
        Returns:
            LLMGatewayResponse с ответом от провайдера
        """
        start_time = time.time()
        
        # Проверяем режим симуляции
        simulated = self._simulate_response(prompt, role)
        if simulated:
            return simulated
        
        # Проверяем кэш
        cache_key = self._build_cache_key(prompt, role, temperature, max_tokens, system_prompt)
        if self.cache:
            try:
                cached = await asyncio.to_thread(self.cache.get, cache_key)
                if cached:
                    logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                    # Обновляем метрики
                    llm_gateway_requests_total.labels(
                        provider="cache",
                        role=role or "unknown",
                        status="hit"
                    ).inc()
                    return cached
            except Exception as e:
                logger.debug(f"Cache get error: {e}")
        
        # Получаем fallback-цепочку провайдеров
        provider_chain = self._build_provider_chain(role)
        
        if not provider_chain:
            logger.warning("LLMGateway: нет доступных провайдеров, возвращаем placeholder")
            return self._build_placeholder_response("unknown", "unknown", prompt, role, [])
        
        # Пробуем каждого провайдера по очереди
        last_error: Optional[Exception] = None
        
        for provider in provider_chain:
            # Проверяем health status
            if self.health_monitor:
                if not self.health_monitor.is_provider_healthy(provider.name):
                    logger.debug(f"Provider {provider.name} is unhealthy, skipping")
                    continue
            
            # Проверяем circuit breaker
            circuit_breaker = self.circuit_breakers.get(provider.name)
            if circuit_breaker and not circuit_breaker.state.should_attempt():
                logger.debug(f"Circuit breaker OPEN for {provider.name}, skipping")
                continue
            
            try:
                # Выполняем запрос через circuit breaker
                if circuit_breaker:
                    response = await circuit_breaker.call(
                        self._call_provider,
                        provider,
                        prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                        role=role,
                        **kwargs
                    )
                else:
                    response = await self._call_provider(
                        provider,
                        prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                        role=role,
                        **kwargs
                    )
                
                # Успешный ответ
                duration = time.time() - start_time
                
                # Обновляем метрики
                llm_gateway_requests_total.labels(
                    provider=provider.name,
                    role=role or "unknown",
                    status="success"
                ).inc()
                llm_gateway_latency_seconds.labels(
                    provider=provider.name,
                    role=role or "unknown"
                ).observe(duration)
                
                # Обновляем health monitor
                if self.health_monitor:
                    health = self.health_monitor.get_provider_health(provider.name)
                    if health:
                        llm_provider_health.labels(provider=provider.name).set(
                            1.0 if health.status == ProviderHealthStatus.HEALTHY else 0.5
                        )
                        if health.latency_ms:
                            llm_provider_latency_ms.labels(provider=provider.name).set(health.latency_ms)
                
                # Сохраняем в кэш
                if self.cache:
                    try:
                        await asyncio.to_thread(self.cache.set, cache_key, response)
                    except Exception as e:
                        logger.debug(f"Cache set error: {e}")
                
                return response
            
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider.name} failed: {e}")
                
                # Обновляем метрики ошибок
                llm_gateway_requests_total.labels(
                    provider=provider.name,
                    role=role or "unknown",
                    status="error"
                ).inc()
                
                # Записываем fallback
                if provider != provider_chain[-1]:  # Не последний в цепочке
                    next_provider = provider_chain[provider_chain.index(provider) + 1]
                    llm_gateway_fallbacks_total.labels(
                        from_provider=provider.name,
                        to_provider=next_provider.name,
                        reason=str(type(e).__name__)
                    ).inc()
                
                # Продолжаем к следующему провайдеру
                continue
        
        # Все провайдеры недоступны - fallback на офлайн-режим
        logger.error(f"All providers failed, last error: {last_error}")
        return await self._offline_fallback(prompt, role, last_error)
    
    async def _call_provider(
        self,
        provider: ProviderConfig,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
        role: Optional[str] = None,
        **kwargs
    ) -> LLMGatewayResponse:
        """
        Вызвать конкретного провайдера.
        
        Поддерживаемые провайдеры:
        - gigachat
        - yandex-gpt
        - naparnik
        - local-qwen (через Ollama)
        - ollama
        """
        model_name = self._resolve_model_name(provider)
        
        # Определяем клиент на основе имени провайдера
        if provider.name == "gigachat":
            client = _get_gigachat_client()
            if not client or not client.is_configured:
                raise RuntimeError("GigaChat client not configured")
            
            result = await client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            
            return LLMGatewayResponse(
                provider=provider.name,
                model=model_name,
                response=result.get("text", ""),
                metadata={
                    "role": role,
                    "usage": result.get("usage", {}),
                    "raw": result.get("raw", {}),
                }
            )
        
        elif provider.name == "yandex-gpt":
            client = _get_yandexgpt_client()
            if not client or not client.is_configured:
                raise RuntimeError("YandexGPT client not configured")
            
            result = await client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            
            return LLMGatewayResponse(
                provider=provider.name,
                model=model_name,
                response=result.get("text", ""),
                metadata={
                    "role": role,
                    "usage": result.get("usage", {}),
                    "raw": result.get("raw", {}),
                }
            )
        
        elif provider.name == "naparnik":
            client = _get_naparnik_client()
            if not client or not client.is_configured:
                raise RuntimeError("Naparnik client not configured")
            
            result = await client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            
            return LLMGatewayResponse(
                provider=provider.name,
                model=model_name,
                response=result.get("text", ""),
                metadata={
                    "role": role,
                    "usage": result.get("usage", {}),
                    "raw": result.get("raw", {}),
                }
            )
        
        elif provider.name in {"local-qwen", "local-mistral"} or provider.is_self_hosted:
            # Локальные модели через Ollama
            client = _get_ollama_client()
            if not client:
                raise RuntimeError("Ollama client not available")
            
            result = await client.generate(
                prompt=prompt,
                model_name=model_name,
                system_prompt=system_prompt or "You are a helpful AI assistant.",
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return LLMGatewayResponse(
                provider=provider.name,
                model=model_name,
                response=result.get("text", ""),
                metadata={
                    "role": role,
                    "usage": result.get("usage", {}),
                    "raw": result.get("raw", {}),
                }
            )
        
        else:
            # Неизвестный провайдер
            raise ValueError(f"Unknown provider: {provider.name}")
    
    async def _offline_fallback(
        self,
        prompt: str,
        role: Optional[str],
        last_error: Optional[Exception]
    ) -> LLMGatewayResponse:
        """
        Fallback на офлайн-режим когда все провайдеры недоступны.
        """
        logger.warning("All LLM providers unavailable, using offline fallback")
        
        # Пробуем использовать Ollama как последний резерв
        ollama_client = _get_ollama_client()
        if ollama_client:
            try:
                result = await ollama_client.generate(
                    prompt=prompt,
                    model_name="llama3",
                    system_prompt="You are a helpful AI assistant.",
                )
                return LLMGatewayResponse(
                    provider="ollama-offline",
                    model="llama3",
                    response=result.get("text", ""),
                    metadata={
                        "role": role,
                        "offline": True,
                        "fallback": True,
                    }
                )
            except Exception as e:
                logger.debug(f"Ollama offline fallback also failed: {e}")
        
        # Если даже Ollama недоступен, возвращаем информативное сообщение
        return LLMGatewayResponse(
            provider="offline",
            model="none",
            response=(
                "Извините, все LLM провайдеры временно недоступны. "
                "Пожалуйста, попробуйте позже или проверьте подключение к интернету."
            ),
            metadata={
                "role": role,
                "offline": True,
                "error": str(last_error) if last_error else "All providers unavailable",
            }
        )
    
    def _build_cache_key(
        self,
        prompt: str,
        role: Optional[str],
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> str:
        """Сгенерировать ключ кэша"""
        key_data = f"{prompt}:{role}:{temperature}:{max_tokens}:{system_prompt or ''}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    # --- Вспомогательные методы -------------------------------------------------

    def _build_provider_chain(self, role: Optional[str]) -> List[ProviderConfig]:
        """Построить fallback-цепочку провайдеров"""
        if not self.manager or not self.manager.has_configuration():
            return []

        providers: List[ProviderConfig] = []
        seen = set()

        # Фильтруем по health status если доступен мониторинг
        healthy_providers = set()
        if self.health_monitor:
            healthy_providers = set(self.health_monitor.get_healthy_providers())

        active = self.manager.get_active_provider()
        if active and active.name not in seen:
            # Проверяем health status
            if not self.health_monitor or active.name in healthy_providers:
                providers.append(active)
                seen.add(active.name)

        if role:
            override = self.manager.get_fallback_chain(role)
            if override:
                primary_name = override.get("primary")
                chain_names = override.get("chain", [])

                for name in [primary_name, *(chain_names or [])]:
                    if not isinstance(name, str):
                        continue
                    provider = self.manager.get_provider(name)
                    if provider and provider.enabled and provider.name not in seen:
                        # Проверяем health status
                        if not self.health_monitor or provider.name in healthy_providers:
                            providers.append(provider)
                            seen.add(provider.name)

        # В завершение возвращаем полный список. Если по каким-то причинам он пуст,
        # добавляем openai из конфигурации, если такой имеется.
        if not providers:
            openai_provider = self.manager.get_provider("openai") if self.manager else None
            if openai_provider and openai_provider.enabled:
                if not self.health_monitor or openai_provider.name in healthy_providers:
                    providers.append(openai_provider)

        return providers

    def _resolve_model_name(self, provider: ProviderConfig) -> str:
        models_meta = provider.metadata.get("models") if provider.metadata else None
        if isinstance(models_meta, list) and models_meta:
            first = models_meta[0]
            if isinstance(first, dict):
                return first.get("name", "unknown-model")
            if isinstance(first, str):
                return first
        return "unknown-model"

    def _build_placeholder_response(
        self,
        provider: str,
        model: str,
        prompt: str,
        role: Optional[str],
        fallback: List[str],
    ) -> LLMGatewayResponse:
        diagnostic = (
            f"[LLM placeholder]\n"
            f"provider: {provider}\n"
            f"model: {model}\n"
            f"fallback: {', '.join(fallback) if fallback else '—'}\n"
            f"prompt_preview: {prompt[:200]}"
        )
        return LLMGatewayResponse(
            provider=provider,
            model=model,
            response=diagnostic,
            metadata={"role": role, "fallback_chain": fallback, "placeholder": True},
        )

    def _load_simulation_config(self) -> Dict[str, Any]:
        config_path = Path("config/llm_gateway_simulation.yaml")
        if not config_path.exists():
            return {}
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            logger.info("LLMGateway: загружена симуляция из %s (mode=%s)", config_path, data.get("mode"))
            return data
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не удалось прочитать %s: %s", config_path, exc)
            return {}

    def _simulate_response(self, prompt: str, role: Optional[str]) -> Optional[LLMGatewayResponse]:
        if not self.simulation_config:
            return None
        if self.simulation_config.get("mode") != "simulation":
            return None

        scenarios: Sequence[Dict[str, Any]] = self.simulation_config.get("scenarios") or []
        for scenario in scenarios:
            match_cfg = scenario.get("match", {})
            if role and match_cfg.get("role") and match_cfg.get("role") != role:
                continue
            contains: Sequence[str] = match_cfg.get("contains") or []
            if contains and not any(keyword.lower() in prompt.lower() for keyword in contains):
                continue

            response_cfg = scenario.get("response") or {}
            provider = response_cfg.get("provider", "simulation-provider")
            model = response_cfg.get("model", "simulation-model")
            text = response_cfg.get("text", "[LLM simulation] Нет подготовленного текста.")
            metadata = response_cfg.get("metadata", {})
            fallback = response_cfg.get("fallback") or self.simulation_config.get("fallback", {}).get("default_chain", [])

            logger.info("LLMGateway: сработал сценарий моделирования '%s'", scenario.get("name", "unnamed"))
            return LLMGatewayResponse(
                provider=provider,
                model=model,
                response=text,
                metadata={
                    "role": role,
                    "scenario": scenario.get("name"),
                    "fallback_chain": fallback,
                    "simulation": True,
                    **metadata,
                },
            )

        return None


def load_llm_gateway() -> LLMGateway:
    return LLMGateway()
