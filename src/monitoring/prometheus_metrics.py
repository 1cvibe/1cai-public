"""
Prometheus Metrics Export
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок

TIER 1 Improvement: Comprehensive monitoring
"""

import logging
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict
import psutil
import time
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


# ==================== REQUEST METRICS ====================

# Total requests
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Request duration
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Request size
http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

# Response size
http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)


# ==================== AI METRICS ====================

# AI queries
ai_queries_total = Counter(
    'ai_queries_total',
    'Total AI queries',
    ['agent_type', 'status', 'model']
)

# AI response time
ai_response_duration_seconds = Histogram(
    'ai_response_duration_seconds',
    'AI response duration',
    ['agent_type', 'model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

# AI tokens used
ai_tokens_used_total = Counter(
    'ai_tokens_used_total',
    'Total AI tokens consumed',
    ['agent_type', 'model', 'token_type']  # token_type: prompt, completion, total
)

# AI service availability
ai_service_available = Gauge(
    'ai_service_available',
    'AI service availability (1 = available, 0 = unavailable)',
    ['service', 'model']
)

# AI errors
ai_errors_total = Counter(
    'ai_errors_total',
    'Total AI errors',
    ['service', 'model', 'error_type']
)

# Kimi-K2-Thinking specific metrics
kimi_queries_total = Counter(
    'kimi_queries_total',
    'Total Kimi-K2-Thinking queries',
    ['mode', 'status']  # mode: api, local
)

kimi_response_duration_seconds = Histogram(
    'kimi_response_duration_seconds',
    'Kimi-K2-Thinking response duration',
    ['mode'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

kimi_tokens_used_total = Counter(
    'kimi_tokens_used_total',
    'Total Kimi-K2-Thinking tokens consumed',
    ['mode', 'token_type']
)

kimi_reasoning_steps = Histogram(
    'kimi_reasoning_steps',
    'Number of reasoning steps in Kimi responses',
    ['mode'],
    buckets=[1, 2, 5, 10, 20, 50, 100]
)

kimi_tool_calls_total = Counter(
    'kimi_tool_calls_total',
    'Total tool calls made by Kimi',
    ['mode', 'tool_name']
)

# AI Orchestrator metrics
orchestrator_queries_total = Counter(
    'orchestrator_queries_total',
    'Total orchestrator queries',
    ['query_type', 'selected_service']
)

orchestrator_fallback_total = Counter(
    'orchestrator_fallback_total',
    'Total fallback operations',
    ['from_service', 'to_service', 'reason']
)

orchestrator_cache_hits_total = Counter(
    'orchestrator_cache_hits_total',
    'Total cache hits in orchestrator'
)

orchestrator_cache_misses_total = Counter(
    'orchestrator_cache_misses_total',
    'Total cache misses in orchestrator'
)


# ==================== BUSINESS METRICS ====================

# Active users
active_users = Gauge(
    'active_users',
    'Currently active users'
)

# Active tenants
active_tenants = Gauge(
    'active_tenants',
    'Currently active tenants'
)

# Code reviews
code_reviews_total = Counter(
    'code_reviews_total',
    'Total code reviews',
    ['status', 'language']
)

# Tests generated
tests_generated_total = Counter(
    'tests_generated_total',
    'Total tests generated',
    ['language', 'framework']
)

# Projects
projects_total = Gauge(
    'projects_total',
    'Total projects',
    ['status']
)


# ==================== BA SESSION METRICS ====================

ba_ws_active_sessions = Gauge(
    'ba_ws_active_sessions',
    'Currently active BA websocket sessions'
)

ba_ws_active_participants = Gauge(
    'ba_ws_active_participants',
    'Currently active BA websocket participants'
)

ba_ws_events_total = Counter(
    'ba_ws_events_total',
    'Total BA websocket events',
    ['event_type']
)

ba_ws_disconnects_total = Counter(
    'ba_ws_disconnects_total',
    'Total BA websocket disconnects',
    ['reason']
)

ba_ws_audit_failures_total = Counter(
    'ba_ws_audit_failures_total',
    'Total BA session audit write failures'
)


# ==================== DATABASE METRICS ====================

# Database queries
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['database', 'operation']
)

# Database query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['database', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Connection pool
db_pool_size = Gauge(
    'db_pool_size',
    'Database connection pool size',
    ['database']
)

db_pool_available = Gauge(
    'db_pool_available_connections',
    'Available database connections',
    ['database']
)


# ==================== CACHE METRICS ====================

# Cache hits/misses
cache_operations_total = Counter(
    'cache_operations_total',
    'Cache operations',
    ['operation', 'layer', 'status']
)

# Cache size
cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['layer']
)


# ==================== SYSTEM METRICS ====================

# System info
system_info = Info('system', 'System information')

# CPU usage
system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent',
    'CPU usage percentage'
)

# Memory usage
system_memory_usage_percent = Gauge(
    'system_memory_usage_percent',
    'Memory usage percentage'
)

system_memory_available_bytes = Gauge(
    'system_memory_available_bytes',
    'Available memory in bytes'
)

# Disk usage
system_disk_usage_percent = Gauge(
    'system_disk_usage_percent',
    'Disk usage percentage'
)


# ==================== ERROR METRICS ====================

# Errors by type
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Circuit breaker state
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['service']
)


# ==================== HELPER FUNCTIONS ====================

def update_system_metrics():
    """
    Update system metrics (CPU, memory, disk)
    
    Best practices:
    - Graceful error handling (don't crash if psutil unavailable)
    - Safe disk path handling (works on Windows/Linux)
    - Structured logging
    """
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_usage_percent.set(cpu_percent)
        
        # Memory
        memory = psutil.virtual_memory()
        system_memory_usage_percent.set(memory.percent)
        system_memory_available_bytes.set(memory.available)
        
        # Disk (best practice: handle different OS paths)
        try:
            # Try root path (Linux/Mac)
            disk = psutil.disk_usage('/')
        except (OSError, PermissionError):
            # Fallback to current directory (Windows)
            import os
            disk = psutil.disk_usage(os.getcwd())
        
        system_disk_usage_percent.set(disk.percent)
        
    except ImportError:
        logger.warning(
            "psutil not available, system metrics disabled",
            extra={"module": "prometheus_metrics"}
        )
    except Exception as e:
        logger.error(
            f"Failed to update system metrics: {e}",
            exc_info=True,
            extra={"error_type": type(e).__name__}
        )


def track_request(method: str, endpoint: str, status_code: int, duration: float, size: int = 0):
    """Track HTTP request"""
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    if size > 0:
        http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(size)


def track_ai_query(agent_type: str, duration: float, status: str = 'success', tokens: int = 0):
    """Track AI query"""
    ai_queries_total.labels(agent_type=agent_type, status=status).inc()
    ai_response_duration_seconds.labels(agent_type=agent_type).observe(duration)
    
    if tokens > 0:
        ai_tokens_used_total.labels(agent_type=agent_type, model='gpt-4').inc(tokens)


def track_db_query(database: str, operation: str, duration: float):
    """Track database query"""
    db_queries_total.labels(database=database, operation=operation).inc()
    db_query_duration_seconds.labels(database=database, operation=operation).observe(duration)


def track_cache_operation(layer: str, operation: str, status: str):
    """Track cache operation"""
    cache_operations_total.labels(operation=operation, layer=layer, status=status).inc()


def track_ba_session_event(event_type: str) -> None:
    """Track BA websocket events such as join/leave/chat."""
    ba_ws_events_total.labels(event_type=event_type).inc()


def track_ba_session_disconnect(reason: str) -> None:
    """Track BA websocket disconnects."""
    ba_ws_disconnects_total.labels(reason=reason).inc()


def track_ba_session_audit_failure() -> None:
    """Track audit log failures for BA sessions."""
    ba_ws_audit_failures_total.inc()


def set_ba_session_counts(active_sessions: int, active_participants: int):
    """
    Update BA websocket session gauges atomically.
    """
    ba_ws_active_sessions.set(max(0, active_sessions))
    ba_ws_active_participants.set(max(0, active_participants))


# ==================== METRICS ENDPOINT ====================

async def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint
    
    Usage in FastAPI:
        from src.monitoring.prometheus_metrics import metrics_endpoint
        
        @app.get("/metrics")
        async def metrics():
            return await metrics_endpoint()
    """
    
    # Update system metrics before export
    update_system_metrics()
    
    # Generate metrics in Prometheus format
    metrics_output = generate_latest()
    
    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )


