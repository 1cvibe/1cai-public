"""
DevOps Domain Exceptions

Domain-specific исключения для DevOps модуля.
"""


class DevOpsAgentError(Exception):
    """Базовое исключение для DevOps Agent"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class PipelineOptimizationError(DevOpsAgentError):
    """Ошибка при оптимизации CI/CD pipeline"""
    pass


class LogAnalysisError(DevOpsAgentError):
    """Ошибка при анализе логов"""
    pass


class CostOptimizationError(DevOpsAgentError):
    """Ошибка при оптимизации затрат"""
    pass


class IaCGenerationError(DevOpsAgentError):
    """Ошибка при генерации Infrastructure as Code"""
    pass


class DockerAnalysisError(DevOpsAgentError):
    """Ошибка при анализе Docker инфраструктуры"""
    pass


__all__ = [
    "DevOpsAgentError",
    "PipelineOptimizationError",
    "LogAnalysisError",
    "CostOptimizationError",
    "IaCGenerationError",
    "DockerAnalysisError",
]
