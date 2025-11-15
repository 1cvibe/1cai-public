"""
LLM Gateway — центральная точка выбора провайдера с поддержкой fallback-цепочек.

Функция генерации пока возвращает диагностическое сообщение без обращения к
сетевым API. Это позволяет протестировать маршрутизацию и интеграции. Когда
появятся реальные self-hosted или удалённые модели, внутренняя реализация
может быть расширена для выполнения фактических запросов.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

from .llm_provider_manager import (
    LLMProviderManager,
    ProviderConfig,
    load_llm_provider_manager,
)

logger = logging.getLogger(__name__)


@dataclass
class LLMGatewayResponse:
    provider: str
    model: str
    response: str
    metadata: Dict[str, Any]


class LLMGateway:
    """
    LLM шлюз: определяет порядок провайдеров и возвращает структурированный ответ.

    Ключевые механизмы:
    - чтение fallback-цепочек из `config/llm_providers.yaml`;
    - поддержка активного провайдера (из `output/current_llm_backend.json`);
    - формирование детального ответа, который можно использовать в логике агентов.
    """

    def __init__(self, manager: Optional[LLMProviderManager] = None) -> None:
        self.manager = manager or load_llm_provider_manager()
        self._ensure_manager()
        self.simulation_config = self._load_simulation_config()

    def _ensure_manager(self) -> None:
        if not self.manager or not self.manager.has_configuration():
            logger.warning("LLMGateway запущен без конфигурации провайдеров; будут использованы значения по умолчанию.")

    def generate(self, prompt: str, role: Optional[str] = None) -> LLMGatewayResponse:
        """
        Возвращает диагностический ответ, описывающий выбранного провайдера и fallback-цепочку.
        """
        simulated = self._simulate_response(prompt, role)
        if simulated:
            return simulated

        provider_chain = self._build_provider_chain(role)

        if not provider_chain:
            # По умолчанию считаем, что используем openai/gpt-4o
            logger.info("LLMGateway: нет конфигурации провайдеров, используем openai/gpt-4o (заглушка)")
            return self._build_placeholder_response("openai", "gpt-4o", prompt, role, [])

        # Текущий выбранный провайдер — первый в цепочке
        active_provider = provider_chain[0]
        model_name = self._resolve_model_name(active_provider)
        fallback_names = [provider.name for provider in provider_chain[1:]]

        logger.info(
            "LLMGateway: активный провайдер=%s, модель=%s, fallback=%s",
            active_provider.name,
            model_name,
            ", ".join(fallback_names) if fallback_names else "—",
        )

        return self._build_placeholder_response(
            provider=active_provider.name,
            model=model_name,
            prompt=prompt,
            role=role,
            fallback=fallback_names,
        )

    # --- Вспомогательные методы -------------------------------------------------

    def _build_provider_chain(self, role: Optional[str]) -> List[ProviderConfig]:
        if not self.manager or not self.manager.has_configuration():
            return []

        providers: List[ProviderConfig] = []
        seen = set()

        active = self.manager.get_active_provider()
        if active and active.name not in seen:
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
                        providers.append(provider)
                        seen.add(provider.name)

        # В завершение возвращаем полный список. Если по каким-то причинам он пуст,
        # добавляем openai из конфигурации, если такой имеется.
        if not providers:
            openai_provider = self.manager.get_provider("openai") if self.manager else None
            if openai_provider and openai_provider.enabled:
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

