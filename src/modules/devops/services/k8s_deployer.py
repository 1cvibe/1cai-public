import logging
import yaml
from typing import Dict, Any, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

class KubernetesDeployer:
    """Сервис для развертывания приложений в Kubernetes."""

    def __init__(self, kubeconfig_path: Optional[str] = None):
        """Инициализация клиента Kubernetes.
        
        Args:
            kubeconfig_path: Путь к файлу конфигурации kubeconfig. 
                             Если None, используется конфигурация по умолчанию.
        """
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                # Пытаемся загрузить in-cluster config, если не вышло - локальный
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()
            
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            self.connected = True
        except Exception as e:
            logger.warning(f"Failed to initialize Kubernetes client: {e}")
            self.connected = False

    async def apply_deployment(self, deployment_yaml: str, namespace: str = "default") -> bool:
        """Применить Deployment manifest.
        
        Args:
            deployment_yaml: YAML строка с описанием Deployment.
            namespace: Пространство имен Kubernetes.
            
        Returns:
            True, если успешно, иначе False.
        """
        if not self.connected:
            logger.error("Kubernetes client not connected")
            return False

        try:
            deployment = yaml.safe_load(deployment_yaml)
            name = deployment["metadata"]["name"]
            
            try:
                # Пытаемся обновить существующий
                existing = self.apps_v1.read_namespaced_deployment(name, namespace)
                self.apps_v1.patch_namespaced_deployment(name, namespace, deployment)
                logger.info(f"Updated deployment {name} in {namespace}")
            except ApiException as e:
                if e.status == 404:
                    # Создаем новый
                    self.apps_v1.create_namespaced_deployment(namespace, deployment)
                    logger.info(f"Created deployment {name} in {namespace}")
                else:
                    raise e
            return True
        except Exception as e:
            logger.error(f"Failed to apply deployment: {e}", exc_info=True)
            return False

    async def apply_service(self, service_yaml: str, namespace: str = "default") -> bool:
        """Применить Service manifest.
        
        Args:
            service_yaml: YAML строка с описанием Service.
            namespace: Пространство имен Kubernetes.
            
        Returns:
            True, если успешно, иначе False.
        """
        if not self.connected:
            logger.error("Kubernetes client not connected")
            return False

        try:
            service = yaml.safe_load(service_yaml)
            name = service["metadata"]["name"]
            
            try:
                # Пытаемся обновить существующий
                existing = self.core_v1.read_namespaced_service(name, namespace)
                # Для сервисов patch может быть сложнее из-за immutable полей (clusterIP)
                # Поэтому часто проще использовать resource_version или пересоздать, если нужно
                # Здесь используем patch
                service["metadata"]["resourceVersion"] = existing.metadata.resource_version
                self.core_v1.patch_namespaced_service(name, namespace, service)
                logger.info(f"Updated service {name} in {namespace}")
            except ApiException as e:
                if e.status == 404:
                    # Создаем новый
                    self.core_v1.create_namespaced_service(namespace, service)
                    logger.info(f"Created service {name} in {namespace}")
                else:
                    raise e
            return True
        except Exception as e:
            logger.error(f"Failed to apply service: {e}", exc_info=True)
            return False

    async def get_deployment_status(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        """Получить статус Deployment.
        
        Args:
            name: Имя Deployment.
            namespace: Пространство имен.
            
        Returns:
            Словарь со статусом (replicas, available, ready).
        """
        if not self.connected:
            return {"error": "Not connected"}

        try:
            deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
            return {
                "replicas": deployment.status.replicas,
                "available_replicas": deployment.status.available_replicas,
                "ready_replicas": deployment.status.ready_replicas,
                "updated_replicas": deployment.status.updated_replicas,
            }
        except ApiException as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {"error": str(e)}
