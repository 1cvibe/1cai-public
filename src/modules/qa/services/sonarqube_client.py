import logging
import httpx
from typing import Dict, Any, List, Optional
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

class SonarQubeClient:
    """Клиент для взаимодействия с SonarQube API."""

    def __init__(self, base_url: str, token: str):
        """Инициализация клиента SonarQube.
        
        Args:
            base_url: URL сервера SonarQube (например, http://localhost:9000).
            token: Токен доступа пользователя.
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.auth = (token, "")

    async def get_project_status(self, project_key: str) -> Dict[str, Any]:
        """Получить статус Quality Gate проекта.
        
        Args:
            project_key: Ключ проекта в SonarQube.
            
        Returns:
            Словарь со статусом Quality Gate.
        """
        url = f"{self.base_url}/api/qualitygates/project_status"
        params = {"projectKey": project_key}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, auth=self.auth, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get project status for {project_key}: {e}")
            return {"status": "ERROR", "error": str(e)}

    async def get_issues(self, project_key: str, severities: str = "CRITICAL,BLOCKER") -> List[Dict[str, Any]]:
        """Получить список проблем проекта.
        
        Args:
            project_key: Ключ проекта.
            severities: Уровни критичности через запятую.
            
        Returns:
            Список найденных проблем.
        """
        url = f"{self.base_url}/api/issues/search"
        params = {
            "componentKeys": project_key,
            "severities": severities,
            "statuses": "OPEN,REOPENED"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, auth=self.auth, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("issues", [])
        except Exception as e:
            logger.error(f"Failed to get issues for {project_key}: {e}")
            return []

    async def create_project(self, project_key: str, project_name: str) -> bool:
        """Создать новый проект.
        
        Args:
            project_key: Ключ проекта.
            project_name: Имя проекта.
            
        Returns:
            True, если успешно, иначе False.
        """
        url = f"{self.base_url}/api/projects/create"
        params = {
            "project": project_key,
            "name": project_name
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, auth=self.auth, params=params)
                response.raise_for_status()
                logger.info(f"Created SonarQube project: {project_key}")
                return True
        except Exception as e:
            logger.error(f"Failed to create project {project_key}: {e}")
            return False
