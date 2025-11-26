# Обратная совместимость - реэкспорт из нового расположения
from src.infrastructure.monitoring.opentelemetry_setup import (
    setup_opentelemetry,
    instrument_fastapi_app,
    instrument_asyncpg,
    instrument_httpx,
    instrument_redis,
    get_tracer,
    get_meter,
    OPENTELEMETRY_AVAILABLE,
)

__all__ = [
    "setup_opentelemetry",
    "instrument_fastapi_app",
    "instrument_asyncpg",
    "instrument_httpx",
    "instrument_redis",
    "get_tracer",
    "get_meter",
    "OPENTELEMETRY_AVAILABLE",
]
