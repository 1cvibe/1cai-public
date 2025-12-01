import logging
from typing import List, Dict
from src.modules.performance.domain.models import GPUStats

logger = logging.getLogger(__name__)


class WeightedGPUScheduler:
    """Взвешенное распределение запросов между GPU."""

    def __init__(self, gpu_devices: List[int]):
        self.gpu_devices = gpu_devices
        self.gpu_weights = {gpu_id: 1.0 for gpu_id in gpu_devices}
        self.gpu_load = {gpu_id: 0.0 for gpu_id in gpu_devices}
        self.gpu_performance = {gpu_id: 1.0 for gpu_id in gpu_devices}
        self.gpu_request_count = {gpu_id: 0 for gpu_id in gpu_devices}

    def select_gpu(self, estimated_time: float = 0.1) -> int:
        """Выбрать GPU на основе весов и загрузки.

        Args:
            estimated_time: Ожидаемое время выполнения запроса.

        Returns:
            ID выбранного GPU.
        """
        if not self.gpu_devices:
            return 0

        # Вычисляем score для каждого GPU
        scores = {}
        for gpu_id in self.gpu_devices:
            # Score = weight / (load + estimated_time + epsilon)
            # Чем больше weight и меньше load, тем выше score
            score = self.gpu_weights[gpu_id] / (self.gpu_load[gpu_id] + estimated_time + 0.1)
            scores[gpu_id] = score

        # Выбираем GPU с максимальным score
        selected_gpu = max(scores, key=scores.get)
        self.gpu_request_count[selected_gpu] += 1

        return selected_gpu

    def update_performance(self, gpu_id: int, actual_time: float, items_processed: int = 1):
        """Обновить метрики производительности GPU.

        Args:
            gpu_id: ID GPU.
            actual_time: Фактическое время выполнения.
            items_processed: Количество обработанных элементов.
        """
        if gpu_id not in self.gpu_devices:
            return

        # Обновляем загрузку (EMA)
        alpha = 0.2
        self.gpu_load[gpu_id] = alpha * actual_time + (1 - alpha) * self.gpu_load[gpu_id]

        # Обновляем вес на основе throughput (items/time)
        if actual_time > 0:
            throughput = items_processed / actual_time
            # EMA для веса (больше throughput = больше weight)
            self.gpu_weights[gpu_id] = alpha * throughput + (1 - alpha) * self.gpu_weights[gpu_id]

        self.gpu_performance[gpu_id] = 1.0 / max(actual_time, 0.001)

    def get_stats(self) -> GPUStats:
        """Получить статистику планировщика."""
        return GPUStats(
            gpu_weights=self.gpu_weights.copy(),
            gpu_load=self.gpu_load.copy(),
            gpu_performance=self.gpu_performance.copy(),
            gpu_request_count=self.gpu_request_count.copy(),
        )
