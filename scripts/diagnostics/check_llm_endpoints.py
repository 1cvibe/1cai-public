#!/usr/bin/env python3
"""
Быстрая диагностика доступности LLM-провайдеров.

Использование:
    python scripts/diagnostics/check_llm_endpoints.py --config config/llm_providers.yaml
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from typing import Dict

import requests
import yaml

EXPECTED_AUTH_ERRORS = {401, 403}


@dataclass
class Provider:
    name: str
    base_url: str
    enabled: bool
    provider_type: str


def load_providers(path: str) -> Dict[str, Provider]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    providers = {}
    for name, cfg in data.get("providers", {}).items():
        providers[name] = Provider(
            name=name,
            base_url=cfg.get("base_url", ""),
            enabled=bool(cfg.get("enabled", True)),
            provider_type=cfg.get("type", "remote"),
        )
    return providers


def check_endpoint(provider: Provider, timeout: float) -> Dict[str, str]:
    if not provider.enabled:
        return {"status": "skipped", "message": "disabled in config"}

    try:
        response = requests.get(provider.base_url, timeout=timeout)
        code = response.status_code
        if code == 200:
            status = "ok"
            message = "HTTP 200"
        elif code in EXPECTED_AUTH_ERRORS:
            status = "reachable"
            message = f"auth error ({code}) — сеть доступна"
        else:
            status = "warning"
            message = f"HTTP {code}"
    except requests.exceptions.RequestException as exc:
        status = "error"
        message = str(exc)
    return {"status": status, "message": message}


def main() -> None:
    parser = argparse.ArgumentParser(description="Проверка доступности LLM-провайдеров")
    parser.add_argument("--config", default="config/llm_providers.yaml", help="Путь к YAML с провайдерами")
    parser.add_argument("--timeout", type=float, default=10.0, help="Тайм-аут запроса (сек)")
    parser.add_argument("--verbose", action="store_true", help="Включить подробный лог")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    providers = load_providers(args.config)
    if not providers:
        logging.error("Не найдено провайдеров в %s", args.config)
        raise SystemExit(1)

    logging.info("Проверяю %s провайдеров (тайм-аут %.1f c)", len(providers), args.timeout)
    results = {}
    for provider in providers.values():
        result = check_endpoint(provider, args.timeout)
        results[provider.name] = result
        logging.info("[%s] %s — %s", provider.name, result["status"], result["message"])

    # Выводим компактный отчёт пригодный для CI
    print("RESULTS_START")
    for name, result in results.items():
        print(f"{name}: {result['status']} ({result['message']})")
    print("RESULTS_END")

    # Завершаем с кодом 0, если нет критических ошибок
    failed = [name for name, res in results.items() if res["status"] == "error"]
    if failed:
        logging.error("Недоступны провайдеры: %s", ", ".join(failed))
        raise SystemExit(2)


if __name__ == "__main__":
    main()

