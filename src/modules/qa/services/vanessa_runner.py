import logging
import subprocess
import os
from typing import List, Dict, Any, Optional
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

class VanessaRunner:
    """Сервис для запуска тестов Vanessa Automation."""

    def __init__(self, vanessa_path: str = "tools/vanessa-automation/vanessa-automation.epf"):
        """Инициализация раннера.
        
        Args:
            vanessa_path: Путь к обработке Vanessa Automation.
        """
        self.vanessa_path = vanessa_path

    async def run_tests(
        self, 
        features_path: str, 
        ib_connection_string: str, 
        report_path: str = "reports/allure"
    ) -> Dict[str, Any]:
        """Запустить тесты Vanessa Automation.
        
        Args:
            features_path: Путь к каталогу с feature-файлами.
            ib_connection_string: Строка подключения к информационной базе 1С.
            report_path: Путь для сохранения отчетов Allure.
            
        Returns:
            Результат выполнения тестов.
        """
        # Формируем команду запуска 1С
        # Пример: 1cv8.exe /IBConnectionString ... /Execute ... /C ...
        
        # В реальном сценарии нужно определить путь к 1cv8.exe
        onec_path = os.getenv("ONEC_PATH", "C:\\Program Files\\1cv8\\8.3.22.1709\\bin\\1cv8.exe")
        
        if not os.path.exists(onec_path):
            logger.error(f"1C:Enterprise executable not found at {onec_path}")
            return {"status": "ERROR", "message": "1C executable not found"}

        # Параметры запуска Vanessa
        vanessa_params = {
            "RootFeatureDirectory": features_path,
            "AllureReportPath": report_path,
            "QuitAfterExecute": True
        }
        
        # Преобразуем параметры в JSON строку для передачи в /C
        # В реальности Vanessa принимает параметры через JSON файл или спец. формат
        # Для упрощения здесь используем псевдо-код формирования командной строки
        
        cmd = [
            onec_path,
            "/IBConnectionString", ib_connection_string,
            "/Execute", self.vanessa_path,
            "/C", f"StartFeaturePlayer;RootFeatureDirectory={features_path};AllureReportPath={report_path}"
        ]
        
        logger.info(f"Starting Vanessa Automation tests: {features_path}")
        
        try:
            # Запускаем процесс
            process = await self._run_process(cmd)
            
            if process.returncode == 0:
                logger.info("Vanessa tests completed successfully")
                return {"status": "SUCCESS", "report_path": report_path}
            else:
                logger.warning(f"Vanessa tests failed with code {process.returncode}")
                return {"status": "FAILURE", "code": process.returncode}
                
        except Exception as e:
            logger.error(f"Failed to run Vanessa tests: {e}", exc_info=True)
            return {"status": "ERROR", "error": str(e)}

    async def _run_process(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Асинхронный запуск процесса (обертка)."""
        # В Python < 3.9 asyncio.create_subprocess_exec предпочтительнее
        # Здесь используем синхронный subprocess для простоты, 
        # но в продакшене лучше использовать asyncio
        import asyncio
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if stdout:
            logger.debug(f"Vanessa stdout: {stdout.decode('cp1251', errors='ignore')}")
        if stderr:
            logger.error(f"Vanessa stderr: {stderr.decode('cp1251', errors='ignore')}")
            
        return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)
