import logging
from typing import List, Optional, Dict
from src.modules.performance.domain.models import BatcherStats

logger = logging.getLogger(__name__)


class MemoryAwareBatcher:
    """Память-осознанное формирование батчей."""

    def __init__(self, max_memory_mb: float = 1024):
        self.max_memory_mb = max_memory_mb
        self.current_batch = []
        self.current_memory = 0.0

    def add_text(self, text: str) -> Optional[List[str]]:
        """Добавить текст в батч, вернуть батч если готов.

        Args:
            text: Текст для добавления.

        Returns:
            Список строк (батч), если он готов, иначе None.
        """
        try:
            if not isinstance(text, str):
                logger.warning(f"Invalid text type: {type(text)}")
                return None

            if not text:
                logger.debug("Empty text provided to batcher")
                return None

            text_memory = self._estimate_memory(text)

            # Проверяем, поместится ли текст
            if self.current_memory + text_memory > self.max_memory_mb:
                # Батч готов, возвращаем его
                batch = self.current_batch.copy()
                self.current_batch = [text]
                self.current_memory = text_memory
                return batch

            # Добавляем в текущий батч
            self.current_batch.append(text)
            self.current_memory += text_memory
            return None
        except Exception as e:
            logger.error(f"Error adding text to batcher: {e}", exc_info=True)
            return None

    def flush(self) -> Optional[List[str]]:
        """Завершить текущий батч и вернуть его."""
        if self.current_batch:
            batch = self.current_batch.copy()
            self.current_batch = []
            self.current_memory = 0.0
            return batch
        return None

    def _estimate_memory(self, text: str) -> float:
        """Оценить потребление памяти для текста."""
        # Эмпирическая формула: ~1.5MB на embedding
        # + overhead токенизации
        base_memory = 0.0015  # MB
        token_overhead = len(text) * 0.000001  # ~1KB на 1000 символов
        return base_memory + token_overhead

    def get_stats(self) -> BatcherStats:
        """Получить статистику батчера."""
        return BatcherStats(
            current_batch_size=len(self.current_batch),
            current_memory_mb=self.current_memory,
            max_memory_mb=self.max_memory_mb,
        )
