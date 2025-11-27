"""
Tests for IaCGenerator Service

Unit tests for Infrastructure as Code generation.
"""

import pytest

from src.modules.devops.services.iac_generator import IaCGenerator


@pytest.fixture
def generator():
    """Fixture for IaCGenerator instance"""
    return IaCGenerator()


@pytest.fixture
def terraform_requirements():
    """Fixture for Terraform requirements"""
    return {
        "provider": "aws",
        "services": ["compute", "database", "cache"],
        "environment": "production"
    }


@pytest.fixture
def ansible_requirements():
    """Fixture for Ansible requirements"""
    return {
        "tasks": ["install_nginx", "setup_postgres"],
        "target_os": "ubuntu",
        "environment": "production"
    }


@pytest.fixture
def kubernetes_requirements():
    """Fixture for Kubernetes requirements"""
    return {
        "app_name": "my-app",
        "replicas": 3,
        "image": "my-app:1.0.0",
        "port": 8080
    }


class TestIaCGenerator:
    """Tests for IaCGenerator service"""

    @pytest.mark.asyncio
    async def test_generate_terraform(self, generator, terraform_requirements):
        """Test Terraform generation"""
        result = await generator.generate_terraform(terraform_requirements)

        assert isinstance(result, dict)
        assert "main.tf" in result
        assert "variables.tf" in result
        assert "outputs.tf" in result

    @pytest.mark.asyncio
    async def test_terraform_main_tf_structure(self, generator, terraform_requirements):
        """Test main.tf structure"""
        result = await generator.generate_terraform(terraform_requirements)
        main_tf = result["main.tf"]

        assert "terraform {" in main_tf
        assert "provider \"aws\"" in main_tf
        assert "required_version" in main_tf

    @pytest.mark.asyncio
    async def test_terraform_compute_service(self, generator):
        """Test Terraform with compute service"""
        requirements = {
            "provider": "aws",
            "services": ["compute"],
            "environment": "production"
        }

        result = await generator.generate_terraform(requirements)
        main_tf = result["main.tf"]

        assert "aws_instance" in main_tf
        assert "app_server" in main_tf

    @pytest.mark.asyncio
    async def test_terraform_database_service(self, generator):
        """Test Terraform with database service"""
        requirements = {
            "provider": "aws",
            "services": ["database"],
            "environment": "production"
        }

        result = await generator.generate_terraform(requirements)
        main_tf = result["main.tf"]

        assert "aws_db_instance" in main_tf
        assert "postgres" in main_tf

    @pytest.mark.asyncio
    async def test_terraform_cache_service(self, generator):
        """Test Terraform with cache service"""
        requirements = {
            "provider": "aws",
            "services": ["cache"],
            "environment": "production"
        }

        result = await generator.generate_terraform(requirements)
        main_tf = result["main.tf"]

        assert "aws_elasticache_cluster" in main_tf
        assert "redis" in main_tf

    @pytest.mark.asyncio
    async def test_terraform_variables_tf(self, generator, terraform_requirements):
        """Test variables.tf content"""
        result = await generator.generate_terraform(terraform_requirements)
        variables_tf = result["variables.tf"]

        assert "variable \"aws_region\"" in variables_tf
        assert "variable \"environment\"" in variables_tf
        assert "variable \"project_name\"" in variables_tf

    @pytest.mark.asyncio
    async def test_terraform_outputs_tf(self, generator):
        """Test outputs.tf content"""
        requirements = {
            "provider": "aws",
            "services": ["compute", "database"],
            "environment": "production"
        }

        result = await generator.generate_terraform(requirements)
        outputs_tf = result["outputs.tf"]

        assert "output \"instance_ids\"" in outputs_tf
        assert "output \"db_endpoint\"" in outputs_tf

    @pytest.mark.asyncio
    async def test_generate_ansible(self, generator, ansible_requirements):
        """Test Ansible generation"""
        result = await generator.generate_ansible(ansible_requirements)

        assert isinstance(result, dict)
        assert "playbook.yml" in result
        assert "inventory.ini" in result

    @pytest.mark.asyncio
    async def test_ansible_playbook_structure(self, generator, ansible_requirements):
        """Test Ansible playbook structure"""
        result = await generator.generate_ansible(ansible_requirements)
        playbook = result["playbook.yml"]

        assert "---" in playbook  # YAML start
        assert "hosts: all" in playbook
        assert "tasks:" in playbook

    @pytest.mark.asyncio
    async def test_ansible_nginx_task(self, generator):
        """Test Ansible with nginx installation"""
        requirements = {
            "tasks": ["install_nginx"],
            "target_os": "ubuntu",
            "environment": "production"
        }

        result = await generator.generate_ansible(requirements)
        playbook = result["playbook.yml"]

        assert "Install Nginx" in playbook
        assert "nginx" in playbook

    @pytest.mark.asyncio
    async def test_ansible_postgres_task(self, generator):
        """Test Ansible with PostgreSQL setup"""
        requirements = {
            "tasks": ["setup_postgres"],
            "target_os": "ubuntu",
            "environment": "production"
        }

        result = await generator.generate_ansible(requirements)
        playbook = result["playbook.yml"]

        assert "Install PostgreSQL" in playbook or "PostgreSQL" in playbook
        assert "postgresql" in playbook

    @pytest.mark.asyncio
    async def test_ansible_inventory(self, generator, ansible_requirements):
        """Test Ansible inventory file"""
        result = await generator.generate_ansible(ansible_requirements)
        inventory = result["inventory.ini"]

        assert "[webservers]" in inventory
        assert "[databases]" in inventory
        assert "ansible_user" in inventory

    @pytest.mark.asyncio
    async def test_generate_kubernetes(self, generator, kubernetes_requirements):
        """Test Kubernetes generation"""
        result = await generator.generate_kubernetes(kubernetes_requirements)

        assert isinstance(result, dict)
        assert "deployment.yaml" in result
        assert "service.yaml" in result
        assert "ingress.yaml" in result

    @pytest.mark.asyncio
    async def test_kubernetes_deployment(self, generator, kubernetes_requirements):
        """Test Kubernetes Deployment manifest"""
        result = await generator.generate_kubernetes(kubernetes_requirements)
        deployment = result["deployment.yaml"]

        assert "apiVersion: apps/v1" in deployment
        assert "kind: Deployment" in deployment
        assert "replicas: 3" in deployment
        assert "my-app:1.0.0" in deployment

    @pytest.mark.asyncio
    async def test_kubernetes_service(self, generator, kubernetes_requirements):
        """Test Kubernetes Service manifest"""
        result = await generator.generate_kubernetes(kubernetes_requirements)
        service = result["service.yaml"]

        assert "apiVersion: v1" in service
        assert "kind: Service" in service
        assert "type: LoadBalancer" in service

    @pytest.mark.asyncio
    async def test_kubernetes_ingress(self, generator, kubernetes_requirements):
        """Test Kubernetes Ingress manifest"""
        result = await generator.generate_kubernetes(kubernetes_requirements)
        ingress = result["ingress.yaml"]

        assert "apiVersion: networking.k8s.io/v1" in ingress
        assert "kind: Ingress" in ingress
        assert "my-app.example.com" in ingress

    @pytest.mark.asyncio
    async def test_kubernetes_health_checks(self, generator, kubernetes_requirements):
        """Test that Kubernetes deployment includes health checks"""
        result = await generator.generate_kubernetes(kubernetes_requirements)
        deployment = result["deployment.yaml"]

        assert "livenessProbe" in deployment
        assert "readinessProbe" in deployment

    @pytest.mark.asyncio
    async def test_kubernetes_resource_limits(self, generator, kubernetes_requirements):
        """Test that Kubernetes deployment includes resource limits"""
        result = await generator.generate_kubernetes(kubernetes_requirements)
        deployment = result["deployment.yaml"]

        assert "resources:" in deployment
        assert "requests:" in deployment
        assert "limits:" in deployment
