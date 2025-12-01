import logging
import time
import numpy as np
from typing import List, Tuple

logger = logging.getLogger(__name__)

class AdaptiveQuantizer:
    """Адаптивная квантизация с калибровкой на реальных данных."""

    def __init__(
        self,
        dtype: str = "int8",
        auto_recalibrate: bool = True,
        recalibrate_interval: int = 1000,
    ):
        self.dtype = dtype
        self.scale = 1.0
        self.calibrated = False
        self.calibration_data = []
        self.max_calibration_samples = 1000
        self.auto_recalibrate = auto_recalibrate
        self.recalibrate_interval = recalibrate_interval
        self.samples_since_calibration = 0
        self.last_calibration_time = time.time()

    def calibrate(
        self, embeddings: List[List[float]], percentile: float = 99.9
    ) -> float:
        """Калибровка на основе реальных данных.
        
        Args:
            embeddings: Список эмбеддингов для калибровки.
            percentile: Перцентиль для определения максимума.
            
        Returns:
            Вычисленный масштаб (scale).
        """
        if not embeddings:
            return self.scale

        # Собираем статистику
        all_values = []
        for emb in embeddings:
            all_values.extend(emb)

        if not all_values:
            return self.scale

        # Определяем scale на основе percentile
        all_values_array = np.array(all_values, dtype=np.float32)
        max_val = np.percentile(np.abs(all_values_array), percentile)

        if self.dtype == "int8":
            self.scale = 127.0 / max_val if max_val > 0 else 1.0
        elif self.dtype == "int16":
            self.scale = 32767.0 / max_val if max_val > 0 else 1.0
        else:
            self.scale = 1.0

        self.calibrated = True
        logger.info(
            f"Adaptive quantization calibrated: scale={self.scale:.6f}, dtype={self.dtype}"
        )

        return self.scale

    def quantize(self, embedding: List[float]) -> Tuple[List[int], float]:
        """Квантизировать embedding с калиброванным scale.
        
        Args:
            embedding: Исходный эмбеддинг.
            
        Returns:
            Кортеж (квантизированный эмбеддинг, масштаб).
        """
        try:
            if not embedding:
                logger.warning("Empty embedding provided for quantization")
                return [], self.scale

            if not isinstance(embedding, list):
                logger.warning(f"Invalid embedding type: {type(embedding)}")
                return [], self.scale

            # Автоматическая перекалибровка
            if self.auto_recalibrate and self.calibrated:
                self.samples_since_calibration += 1
                # Сохраняем embedding для перекалибровки
                if len(self.calibration_data) < self.max_calibration_samples:
                    self.calibration_data.append(embedding)

                # Перекалибровка каждые N образцов или через интервал времени
                should_recalibrate = (
                    self.samples_since_calibration >= self.recalibrate_interval
                    or (time.time() - self.last_calibration_time) > 3600  # Каждый час
                )

                if should_recalibrate and len(self.calibration_data) >= 10:
                    try:
                        self.calibrate(self.calibration_data)
                        self.samples_since_calibration = 0
                        self.last_calibration_time = time.time()
                        # Очищаем старые данные, оставляем последние 100
                        self.calibration_data = self.calibration_data[-100:]
                        logger.info(
                            f"Auto-recalibrated quantizer on {len(self.calibration_data)} samples"
                        )
                    except Exception as e:
                        logger.debug("Error in auto-recalibration: %s", e)

            if not self.calibrated:
                # Используем простую квантизацию без калибровки
                return self._simple_quantize(embedding)

            arr = np.array(embedding, dtype=np.float32)
            if arr.size == 0:
                logger.warning("Empty embedding array")
                return [], self.scale

            scaled = arr * self.scale

            if self.dtype == "int8":
                quantized = np.clip(scaled, -128, 127).astype(np.int8)
            elif self.dtype == "int16":
                quantized = np.clip(scaled, -32768, 32767).astype(np.int16)
            else:
                quantized = arr.astype(np.int32)

            return quantized.tolist(), self.scale
        except Exception as e:
            logger.error(f"Error quantizing embedding: {e}", exc_info=True)
            # Fallback: возвращаем пустой список и scale
            return [], self.scale

    def _simple_quantize(self, embedding: List[float]) -> Tuple[List[int], float]:
        """Простая квантизация без калибровки."""
        arr = np.array(embedding, dtype=np.float32)
        max_val = np.max(np.abs(arr))

        if self.dtype == "int8":
            scale = 127.0 / max_val if max_val > 0 else 1.0
            quantized = (arr * scale).astype(np.int8)
        elif self.dtype == "int16":
            scale = 32767.0 / max_val if max_val > 0 else 1.0
            quantized = (arr * scale).astype(np.int16)
        else:
            scale = 1.0
            quantized = arr.astype(np.int32)

        return quantized.tolist(), scale

    def dequantize(self, quantized: List[int], scale: float) -> List[float]:
        """Де-квантизировать embedding.
        
        Args:
            quantized: Квантизированный эмбеддинг.
            scale: Масштаб.
            
        Returns:
            Восстановленный эмбеддинг.
        """
        try:
            if not quantized:
                logger.warning("Empty quantized embedding provided")
                return []

            if not isinstance(quantized, list):
                logger.warning(f"Invalid quantized type: {type(quantized)}")
                return []

            if scale <= 0:
                logger.warning("Invalid scale for dequantization: %s", scale)
                scale = 1.0

            arr = np.array(
                quantized, dtype=np.int8 if self.dtype == "int8" else np.int16
            )
            if arr.size == 0:
                return []

            dequantized = arr.astype(np.float32) / scale
            return dequantized.tolist()
        except Exception as e:
            logger.error(f"Error dequantizing embedding: {e}", exc_info=True)
            return []
