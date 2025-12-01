import logging
import numpy as np
from collections import deque
from typing import List, Optional, Dict
from src.modules.performance.domain.models import OptimizationFeatures

logger = logging.getLogger(__name__)

class PredictiveBatchOptimizer:
    """Предиктивная оптимизация размера батча на основе истории."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.model = None
        self.model_trained = False

    def predict_optimal_batch_size(
        self,
        text_length: int,
        available_memory: float,
        historical_pattern: Optional[Dict] = None,
    ) -> int:
        """Предсказать оптимальный размер батча.
        
        Args:
            text_length: Длина текста.
            available_memory: Доступная память (MB).
            historical_pattern: Исторический паттерн (опционально).
            
        Returns:
            Оптимальный размер батча.
        """
        try:
            # Валидация входных данных
            if not isinstance(text_length, int) or text_length < 0:
                logger.warning("Invalid text_length: %s", text_length)
                text_length = 1000  # Default

            if not isinstance(available_memory, (int, float)) or available_memory <= 0:
                logger.warning("Invalid available_memory: %s", available_memory)
                available_memory = 1024.0  # Default MB

            # Если есть обученная модель, используем её
            if self.model_trained and self.model and len(self.history) > 50:
                try:
                    features = self._extract_features(text_length, available_memory)
                    predicted = self.model.predict([features])[0]
                    optimal_batch = int(np.clip(predicted, 8, 256))
                    return optimal_batch
                except Exception as e:
                    logger.debug(
                        f"Error in model prediction: {e}, falling back to empirical formula"
                    )

            # Иначе используем эмпирическую формулу
            return self._empirical_formula(text_length, available_memory)
        except Exception as e:
            logger.error(f"Error predicting optimal batch size: {e}", exc_info=True)
            # Fallback: возвращаем безопасное значение
            return 32

    def _extract_features(
        self, text_length: int, available_memory: float
    ) -> List[float]:
        """Извлечь признаки для ML модели."""
        # Базовые признаки
        features = [
            text_length,
            available_memory,
            text_length / max(available_memory, 0.1),  # Плотность
            np.log1p(text_length),  # Логарифм длины (для нормализации)
            np.log1p(available_memory),  # Логарифм памяти
        ]

        # Статистика из истории
        if len(self.history) > 0:
            recent = list(self.history)[-50:]  # Последние 50 записей
            avg_time = np.mean([h["actual_time"] for h in recent])
            avg_efficiency = np.mean([h["efficiency"] for h in recent])
            std_time = (
                np.std([h["actual_time"] for h in recent]) if len(recent) > 1 else 0.0
            )
            std_efficiency = (
                np.std([h["efficiency"] for h in recent]) if len(recent) > 1 else 0.0
            )
            features.extend([avg_time, avg_efficiency, std_time, std_efficiency])
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])

        return features

    def _empirical_formula(self, text_length: int, available_memory: float) -> int:
        """Эмпирическая формула для размера батча."""
        # Базовый расчёт: ~1.5MB на embedding + overhead
        estimated_memory_per_item = 0.0015 + (text_length * 0.000001)  # MB

        # Оставляем 20% памяти в резерве
        available_memory_mb = available_memory * 0.8

        # Вычисляем оптимальный batch size
        optimal_batch = int(available_memory_mb / estimated_memory_per_item)

        # Ограничиваем разумными пределами
        optimal_batch = max(8, min(optimal_batch, 256))

        return optimal_batch

    def update_model(
        self, text_length: int, batch_size: int, actual_time: float, memory_used: float
    ):
        """Обновить модель на основе результатов.
        
        Args:
            text_length: Длина текста.
            batch_size: Размер батча.
            actual_time: Фактическое время выполнения.
            memory_used: Использованная память.
        """
        efficiency = batch_size / max(actual_time, 0.001)  # throughput

        self.history.append(
            {
                "text_length": text_length,
                "batch_size": batch_size,
                "actual_time": actual_time,
                "memory_used": memory_used,
                "efficiency": efficiency,
            }
        )

        # Переобучаем модель каждые 100 записей
        if len(self.history) % 100 == 0 and len(self.history) >= 50:
            self._retrain_model()

    def _retrain_model(self):
        """Переобучить ML модель."""
        try:
            # Пробуем разные модели в порядке приоритета
            models_to_try = []

            # 1. XGBoost (если доступен)
            try:
                import xgboost as xgb

                models_to_try.append(
                    (
                        "xgboost",
                        xgb.XGBRegressor(
                            n_estimators=50,
                            max_depth=6,
                            learning_rate=0.1,
                            random_state=42,
                        ),
                    )
                )
            except ImportError:
                pass

            # 2. LightGBM (если доступен)
            try:
                import lightgbm as lgb

                models_to_try.append(
                    (
                        "lightgbm",
                        lgb.LGBMRegressor(
                            n_estimators=50,
                            max_depth=6,
                            learning_rate=0.1,
                            random_state=42,
                            verbose=-1,
                        ),
                    )
                )
            except ImportError:
                pass

            # 3. Scikit-learn (fallback)
            try:
                from sklearn.ensemble import RandomForestRegressor

                models_to_try.append(
                    (
                        "random_forest",
                        RandomForestRegressor(
                            n_estimators=50, max_depth=6, random_state=42
                        ),
                    )
                )
            except ImportError:
                pass

            if not models_to_try:
                logger.warning("No ML libraries available for retraining")
                return

            # Подготовка данных
            X = []
            y = []
            for h in self.history:
                # Восстанавливаем признаки (приблизительно, т.к. available_memory не сохраняем)
                # Используем среднее значение памяти для восстановления признаков
                avg_mem = 1024.0  # Assumption
                features = self._extract_features(h["text_length"], avg_mem)
                X.append(features)
                y.append(h["batch_size"])  # Целевая переменная - какой batch size был эффективным?
                # На самом деле, мы хотим предсказывать оптимальный batch size.
                # Но здесь мы просто учимся аппроксимировать текущую стратегию.
                # Для реальной оптимизации нужно Reinforcement Learning или более сложная логика.
                # Пока оставим как есть (аппроксимация).

            X = np.array(X)
            y = np.array(y)

            # Обучение
            best_score = -float("inf")
            best_model = None

            for name, model in models_to_try:
                try:
                    model.fit(X, y)
                    score = model.score(X, y)  # R^2 score
                    if score > best_score:
                        best_score = score
                        best_model = model
                except Exception as e:
                    logger.debug(f"Error training {name}: {e}")

            if best_model:
                self.model = best_model
                self.model_trained = True
                logger.info(f"Model retrained successfully. Best score: {best_score:.4f}")

        except Exception as e:
            logger.error(f"Error retraining model: {e}", exc_info=True)
