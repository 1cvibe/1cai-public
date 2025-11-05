"""
OCR Service for 1C Documents
Интеграция Chandra OCR для распознавания документов
"""

import logging
import os
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class OCRProvider(str, Enum):
    """Провайдеры OCR"""
    CHANDRA_HF = "chandra_hf"  # Chandra with HuggingFace
    CHANDRA_VLLM = "chandra_vllm"  # Chandra with vLLM (faster)
    TESSERACT = "tesseract"  # Fallback для простых случаев


class DocumentType(str, Enum):
    """Типы документов 1С"""
    AUTO = "auto"  # Автоопределение
    CONTRACT = "contract"  # Договор
    ACT = "act"  # Акт
    INVOICE = "invoice"  # Счет
    WAYBILL = "waybill"  # Накладная
    FORM = "form"  # Бланк/форма
    TABLE = "table"  # Таблица
    OTHER = "other"


class OCRResult:
    """Результат OCR распознавания"""
    
    def __init__(
        self,
        text: str,
        confidence: float = 0.0,
        document_type: DocumentType = DocumentType.OTHER,
        metadata: Optional[Dict] = None,
        structured_data: Optional[Dict] = None
    ):
        self.text = text
        self.confidence = confidence
        self.document_type = document_type
        self.metadata = metadata or {}
        self.structured_data = structured_data or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "document_type": self.document_type.value,
            "metadata": self.metadata,
            "structured_data": self.structured_data,
            "timestamp": self.timestamp.isoformat()
        }


class OCRService:
    """Сервис OCR для документов 1С"""
    
    def __init__(
        self,
        provider: OCRProvider = OCRProvider.CHANDRA_HF,
        enable_ai_parsing: bool = True
    ):
        """
        Инициализация OCR сервиса
        
        Args:
            provider: Провайдер OCR
            enable_ai_parsing: Использовать AI для парсинга структуры
        """
        self.provider = provider
        self.enable_ai_parsing = enable_ai_parsing
        
        # Инициализация провайдера
        if provider == OCRProvider.CHANDRA_HF or provider == OCRProvider.CHANDRA_VLLM:
            self._init_chandra()
        elif provider == OCRProvider.TESSERACT:
            self._init_tesseract()
    
    def _init_chandra(self):
        """Инициализация Chandra OCR"""
        try:
            # Проверяем установлен ли chandra
            import chandra
            
            self.chandra_available = True
            logger.info("Chandra OCR initialized")
            
        except ImportError:
            logger.error(
                "Chandra OCR not installed. "
                "Install: pip install chandra-ocr"
            )
            self.chandra_available = False
            raise
    
    def _init_tesseract(self):
        """Инициализация Tesseract (fallback)"""
        try:
            import pytesseract
            from PIL import Image
            
            # Проверяем доступен ли tesseract
            pytesseract.get_tesseract_version()
            
            self.tesseract_available = True
            logger.info("Tesseract OCR initialized")
            
        except Exception as e:
            logger.error(f"Tesseract not available: {e}")
            self.tesseract_available = False
            raise
    
    async def process_image(
        self,
        image_path: str,
        document_type: DocumentType = DocumentType.AUTO,
        **kwargs
    ) -> OCRResult:
        """
        Обработка изображения с OCR
        
        Args:
            image_path: Путь к изображению
            document_type: Тип документа (для AI парсинга)
            **kwargs: Дополнительные параметры
        
        Returns:
            OCRResult с распознанным текстом и структурой
        """
        logger.info(f"Processing image: {image_path}")
        
        try:
            # OCR распознавание
            if self.provider in [OCRProvider.CHANDRA_HF, OCRProvider.CHANDRA_VLLM]:
                raw_result = await self._chandra_ocr(image_path, **kwargs)
            elif self.provider == OCRProvider.TESSERACT:
                raw_result = await self._tesseract_ocr(image_path)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
            
            # Создаем результат
            result = OCRResult(
                text=raw_result.get("text", ""),
                confidence=raw_result.get("confidence", 0.0),
                document_type=document_type,
                metadata={
                    "provider": self.provider.value,
                    "image_path": image_path,
                    **raw_result.get("metadata", {})
                }
            )
            
            # AI парсинг структуры (если включен)
            if self.enable_ai_parsing and result.text:
                result.structured_data = await self._parse_structure_with_ai(
                    result.text,
                    document_type
                )
            
            logger.info(
                f"OCR completed: {len(result.text)} chars, "
                f"confidence: {result.confidence:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            raise
    
    async def _chandra_ocr(
        self,
        image_path: str,
        max_tokens: int = 8192,
        include_images: bool = False
    ) -> Dict[str, Any]:
        """Распознавание через Chandra"""
        
        if not self.chandra_available:
            raise RuntimeError("Chandra not available")
        
        try:
            from chandra import process_document
            
            # Создаем временную выходную директорию
            with tempfile.TemporaryDirectory() as output_dir:
                
                # Параметры для Chandra
                method = "hf" if self.provider == OCRProvider.CHANDRA_HF else "vllm"
                
                # Вызов Chandra (синхронный - оборачиваем в async)
                import asyncio
                
                def _sync_process():
                    return process_document(
                        input_path=image_path,
                        output_dir=output_dir,
                        method=method,
                        max_output_tokens=max_tokens,
                        include_images=include_images,
                        include_headers_footers=False  # Для 1С не нужны
                    )
                
                # Запускаем в executor (чтобы не блокировать async)
                loop = asyncio.get_event_loop()
                chandra_result = await loop.run_in_executor(None, _sync_process)
                
                # Читаем результат
                output_file = Path(output_dir) / f"{Path(image_path).stem}.md"
                
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    text = ""
                
                return {
                    "text": text,
                    "confidence": 0.85,  # Chandra не возвращает confidence, используем fixed
                    "metadata": {
                        "method": method,
                        "max_tokens": max_tokens
                    }
                }
        
        except Exception as e:
            logger.error(f"Chandra OCR error: {e}")
            raise
    
    async def _tesseract_ocr(self, image_path: str) -> Dict[str, Any]:
        """Распознавание через Tesseract (fallback)"""
        
        if not self.tesseract_available:
            raise RuntimeError("Tesseract not available")
        
        try:
            import pytesseract
            from PIL import Image
            
            # Открываем изображение
            image = Image.open(image_path)
            
            # OCR
            data = pytesseract.image_to_data(
                image,
                lang='rus+eng',
                output_type=pytesseract.Output.DICT
            )
            
            # Извлекаем текст и confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:  # Только уверенные результаты
                    text = data['text'][i]
                    if text.strip():
                        text_parts.append(text)
                        confidences.append(int(conf))
            
            full_text = " ".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "text": full_text,
                "confidence": avg_confidence / 100,  # Normalize to 0-1
                "metadata": {
                    "method": "tesseract",
                    "words_count": len(text_parts)
                }
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            raise
    
    async def _parse_structure_with_ai(
        self,
        text: str,
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """
        Парсинг структуры документа с помощью AI
        
        Извлекает:
        - Номер документа
        - Дата
        - Контрагент
        - Сумма
        - Табличная часть (для накладных)
        """
        
        # Импортируем только если нужен AI парсинг
        try:
            from src.ai.orchestrator import AIOrchestrator
            
            orchestrator = AIOrchestrator()
            
            # Формируем промпт в зависимости от типа документа
            if document_type == DocumentType.CONTRACT:
                prompt = f"""
Распознанный текст договора:

{text}

Извлеки из текста:
- Номер договора
- Дата договора
- Наименование организации (контрагент)
- Предмет договора (кратко)
- Сумма (если указана)

Верни в формате JSON.
"""
            elif document_type == DocumentType.INVOICE:
                prompt = f"""
Распознанный текст счета:

{text}

Извлеки из текста:
- Номер счета
- Дата счета
- Поставщик (название организации)
- Покупатель (название организации)
- Сумма итого
- НДС (если есть)
- Таблица товаров (наименование, количество, цена, сумма)

Верни в формате JSON.
"""
            elif document_type == DocumentType.WAYBILL:
                prompt = f"""
Распознанный текст накладной:

{text}

Извлеки из текста:
- Номер накладной
- Дата
- Отправитель
- Получатель
- Таблица товаров (наименование, количество, цена)

Верни в формате JSON.
"""
            else:
                # Общий парсинг
                prompt = f"""
Распознанный текст документа:

{text}

Извлеки основные реквизиты:
- Номер документа (если есть)
- Дата (если есть)
- Организации/контрагенты (если есть)
- Суммы (если есть)

Верни в формате JSON.
"""
            
            # Вызываем AI
            result = await orchestrator.process_query(
                prompt,
                context={
                    "type": "document_parsing",
                    "document_type": document_type.value
                }
            )
            
            # Парсим JSON из ответа
            import json
            import re
            
            # Пытаемся извлечь JSON из ответа
            response_text = result.get("answer", "")
            
            # Ищем JSON блок
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    return parsed
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from AI response")
            
            return {"raw_response": response_text}
            
        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            return {}
    
    async def process_from_bytes(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        **kwargs
    ) -> OCRResult:
        """
        Обработка изображения из bytes
        
        Args:
            image_bytes: Данные изображения
            filename: Имя файла (для определения формата)
            **kwargs: Параметры для process_image
        
        Returns:
            OCRResult
        """
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(filename).suffix
        ) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Обрабатываем
            result = await self.process_image(tmp_path, **kwargs)
            return result
            
        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {tmp_path}: {e}")
    
    def get_supported_formats(self) -> List[str]:
        """Получить список поддерживаемых форматов"""
        
        if self.provider in [OCRProvider.CHANDRA_HF, OCRProvider.CHANDRA_VLLM]:
            return ["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"]
        elif self.provider == OCRProvider.TESSERACT:
            return ["png", "jpg", "jpeg", "tiff", "bmp"]
        
        return []
    
    async def is_supported_format(self, filename: str) -> bool:
        """Проверка поддержки формата файла"""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in self.get_supported_formats()
    
    async def batch_process(
        self,
        file_paths: List[str],
        **kwargs
    ) -> List[OCRResult]:
        """
        Пакетная обработка документов
        
        Args:
            file_paths: Список путей к файлам
            **kwargs: Параметры для process_image
        
        Returns:
            Список OCRResult
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = await self.process_image(file_path, **kwargs)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch processing error for {file_path}: {e}")
                # Продолжаем обработку остальных
                results.append(OCRResult(
                    text="",
                    confidence=0.0,
                    metadata={"error": str(e), "file": file_path}
                ))
        
        logger.info(f"Batch processed {len(results)} documents")
        return results
    
    def estimate_processing_time(self, file_path: str) -> int:
        """
        Оценка времени обработки (в секундах)
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            Примерное время в секундах
        """
        file_size = os.path.getsize(file_path)
        
        # Оценки на основе бенчмарков
        if self.provider == OCRProvider.CHANDRA_HF:
            # HuggingFace: ~2-5 сек на страницу (CPU/GPU)
            base_time = 3
        elif self.provider == OCRProvider.CHANDRA_VLLM:
            # vLLM: ~1-2 сек на страницу (GPU)
            base_time = 1.5
        else:
            # Tesseract: ~1 сек на страницу
            base_time = 1
        
        # Приблизительный расчет страниц по размеру файла
        estimated_pages = max(1, file_size // (1024 * 500))  # ~500KB на страницу
        
        return int(base_time * estimated_pages)


# Singleton instance
_ocr_service: Optional[OCRService] = None


def get_ocr_service(
    provider: Optional[OCRProvider] = None,
    enable_ai_parsing: bool = True
) -> OCRService:
    """Получить глобальный экземпляр OCR сервиса"""
    global _ocr_service
    
    if _ocr_service is None or provider is not None:
        # Определяем провайдера из env
        if provider is None:
            provider_str = os.getenv("OCR_PROVIDER", "chandra_hf")
            provider = OCRProvider(provider_str)
        
        _ocr_service = OCRService(
            provider=provider,
            enable_ai_parsing=enable_ai_parsing
        )
    
    return _ocr_service


# Utility functions
async def quick_ocr(image_path: str) -> str:
    """
    Быстрое OCR - только текст без парсинга
    
    Args:
        image_path: Путь к изображению
    
    Returns:
        Распознанный текст
    """
    service = get_ocr_service(enable_ai_parsing=False)
    result = await service.process_image(image_path)
    return result.text


async def ocr_with_structure(
    image_path: str,
    document_type: DocumentType = DocumentType.AUTO
) -> Dict[str, Any]:
    """
    OCR с извлечением структуры
    
    Args:
        image_path: Путь к изображению
        document_type: Тип документа
    
    Returns:
        Dict с текстом и структурированными данными
    """
    service = get_ocr_service(enable_ai_parsing=True)
    result = await service.process_image(image_path, document_type=document_type)
    return result.to_dict()

