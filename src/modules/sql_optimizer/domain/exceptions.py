"""
SQL Optimizer Domain Exceptions

Custom exceptions для SQL Optimizer модуля.
"""


class SQLOptimizerError(Exception):
    """Базовое исключение для SQL Optimizer модуля"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class QueryAnalysisError(SQLOptimizerError):
    """Ошибка при анализе запроса"""
    pass


class QueryOptimizationError(SQLOptimizerError):
    """Ошибка при оптимизации запроса"""
    pass


class InvalidQueryError(SQLOptimizerError):
    """Невалидный SQL запрос"""
    pass


__all__ = [
    "SQLOptimizerError",
    "QueryAnalysisError",
    "QueryOptimizationError",
    "InvalidQueryError",
]
