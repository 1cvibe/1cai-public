import logging
import time
import numpy as np
from typing import Dict, List, Optional
from src.modules.performance.domain.models import SLOConfig, SLIStatus

logger = logging.getLogger(__name__)


class SLOTracker:
    """Отслеживание SLO/SLI и Error Budgets."""

    def __init__(self):
        self.slos: Dict[str, SLOConfig] = {
            "latency_p95": SLOConfig(target=0.1, window=3600),  # 100ms за час
            "error_rate": SLOConfig(target=0.001, window=3600),  # 0.1% за час
            "availability": SLOConfig(target=0.999, window=86400),  # 99.9% за день
            "cache_hit_rate": SLOConfig(target=0.7, window=3600),  # 70% за час
        }

        self.error_budgets = {slo: 0.0 for slo in self.slos}
        self.sli_history = {slo: [] for slo in self.slos}

    def record_metric(self, slo_name: str, value: float, timestamp: float = None):
        """Записать метрику для SLO.

        Args:
            slo_name: Имя SLO.
            value: Значение метрики.
            timestamp: Временная метка (опционально).
        """
        try:
            if timestamp is None:
                timestamp = time.time()

            if slo_name not in self.slos:
                logger.debug("Unknown SLO name: %s", slo_name)
                return

            # Валидация значения
            if not isinstance(value, (int, float)):
                logger.warning(f"Invalid metric value type for {slo_name}: {type(value)}")
                return

            if value < 0:
                logger.warning(f"Negative metric value for {slo_name}: {value}")
                return

            self.sli_history[slo_name].append({"value": float(value), "timestamp": float(timestamp)})

            # Очищаем старые записи
            window = self.slos[slo_name].window
            cutoff = timestamp - window
            self.sli_history[slo_name] = [h for h in self.sli_history[slo_name] if h["timestamp"] > cutoff]

            # Вычисляем текущий SLI
            current_sli = self._calculate_sli(slo_name)

            # Обновляем error budget
            target = self.slos[slo_name].target
            if slo_name == "availability":
                # Для availability: budget = 1 - SLI
                self.error_budgets[slo_name] = 1.0 - current_sli
            else:
                # Для других: budget = target - SLI
                self.error_budgets[slo_name] = target - current_sli
        except Exception as e:
            logger.error(f"Error recording SLO metric {slo_name}: {e}", exc_info=True)

    def _calculate_sli(self, slo_name: str) -> float:
        """Вычислить текущий SLI."""
        history = self.sli_history[slo_name]
        if not history:
            return 1.0

        values = [h["value"] for h in history]

        if slo_name == "latency_p95":
            return float(np.percentile(values, 95)) if values else 0.0
        elif slo_name == "error_rate":
            # Процент ошибок
            total = len(history)
            errors = sum(1 for h in history if h["value"] > 0)
            return errors / total if total > 0 else 0.0
        elif slo_name == "availability":
            # Процент успешных запросов
            total = len(history)
            successful = sum(1 for h in history if h["value"] == 1)
            return successful / total if total > 0 else 1.0
        elif slo_name == "cache_hit_rate":
            # Средний hit rate
            return float(np.mean(values)) if values else 0.0

        return 0.0

    def check_slo_violation(self) -> Dict[str, bool]:
        """Проверить нарушения SLO.

        Returns:
            Словарь {slo_name: is_violated}.
        """
        violations = {}
        for slo_name, config in self.slos.items():
            current_sli = self._calculate_sli(slo_name)
            target = config.target

            if slo_name == "availability":
                violation = current_sli < target
            else:
                violation = current_sli > target

            violations[slo_name] = violation

        return violations

    def get_error_budgets(self) -> Dict[str, float]:
        """Получить текущие бюджеты ошибок."""
        return self.error_budgets.copy()

    def get_sli_status(self) -> Dict[str, SLIStatus]:
        """Получить статус всех SLI."""
        status = {}
        for slo_name in self.slos:
            current_sli = self._calculate_sli(slo_name)
            target = self.slos[slo_name].target
            budget = self.error_budgets[slo_name]

            status[slo_name] = SLIStatus(
                sli=current_sli,
                target=target,
                error_budget=budget,
                violation=(current_sli < target if slo_name == "availability" else current_sli > target),
            )

        return status
