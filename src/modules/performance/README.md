# Performance Module

Модуль для оптимизации производительности и управления ресурсами системы.

## Структура

- `domain/`: Доменные модели и конфигурации.
- `services/`: Сервисы бизнес-логики.

## Компоненты

### 1. Weighted GPU Scheduler (`services/scheduler.py`)
Взвешенное распределение запросов между GPU на основе их загрузки и производительности.

### 2. SLO Tracker (`services/slo_tracker.py`)
Отслеживание Service Level Objectives (SLO) и Service Level Indicators (SLI), управление бюджетами ошибок.

### 3. Memory Aware Batcher (`services/batcher.py`)
Формирование батчей с учетом ограничений по памяти для предотвращения OOM (Out Of Memory).

### 4. Adaptive Quantizer (`services/quantizer.py`)
Адаптивная квантизация эмбеддингов с автоматической калибровкой на реальных данных.

### 5. Semantic Cache ANN (`services/cache.py`)
Семантический кэш с использованием приближенного поиска ближайших соседей (ANN).

### 6. Predictive Batch Optimizer (`services/optimizer.py`)
Предиктивная оптимизация размера батча на основе истории выполнения и ML-модели.

## Использование

```python
from src.modules.performance.services.scheduler import WeightedGPUScheduler
from src.modules.performance.services.slo_tracker import SLOTracker

# Инициализация планировщика
scheduler = WeightedGPUScheduler(gpu_devices=[0, 1])
gpu_id = scheduler.select_gpu()

# Отслеживание SLO
tracker = SLOTracker()
tracker.record_metric("latency_p95", 0.05)
```
