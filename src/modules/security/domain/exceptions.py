"""
Security Domain Exceptions

Custom exceptions для Security модуля.
"""


class SecurityError(Exception):
    """Базовое исключение для Security модуля"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class VulnerabilityScanError(SecurityError):
    """Ошибка при сканировании уязвимостей"""
    pass


class DependencyAuditError(SecurityError):
    """Ошибка при аудите зависимостей"""
    pass


class SecretDetectionError(SecurityError):
    """Ошибка при детекции секретов"""
    pass


class ComplianceCheckError(SecurityError):
    """Ошибка при проверке compliance"""
    pass


__all__ = [
    "SecurityError",
    "VulnerabilityScanError",
    "DependencyAuditError",
    "SecretDetectionError",
    "ComplianceCheckError",
]
