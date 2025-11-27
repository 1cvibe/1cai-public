"""
Unit tests for DevOps Agent Enhanced

Tests cover:
- Log analysis
- CI/CD optimization
- Kubernetes deployment stub
- Auto-scaling logic
"""

import pytest
from unittest.mock import AsyncMock
from src.ai.agents.devops_agent_enhanced import DevOpsAgentEnhanced


@pytest.fixture
def devops_agent():
    """Create DevOps Agent instance"""
    return DevOpsAgentEnhanced()


@pytest.fixture
def mock_llm():
    """Mock LLM Selector"""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value={
        "response": '{"errors": [], "warnings": [], "recommendations": []}',
        "model": "qwen-test"
    })
    return mock


class TestLogAnalysis:
    """Test log analysis"""
    
    @pytest.mark.asyncio
    async def test_analyze_logs(self, devops_agent, mock_llm):
        """Test log analysis"""
        devops_agent.llm_selector = mock_llm
        
        logs = [
            "INFO: Application started",
            "ERROR: Connection failed",
            "WARN: High memory usage"
        ]
        
        result = await devops_agent.analyze_logs(
            logs=logs,
            source="application"
        )
        
        assert result["status"] == "completed"
        assert "analysis" in result
    
    @pytest.mark.asyncio
    async def test_analyze_logs_no_llm(self, devops_agent):
        """Test analysis without LLM"""
        devops_agent.llm_selector = None
        
        result = await devops_agent.analyze_logs(
            logs=["test log"],
            source="test"
        )
        
        assert result["status"] == "llm_not_available"


class TestCICDOptimization:
    """Test CI/CD optimization"""
    
    @pytest.mark.asyncio
    async def test_optimize_cicd(self, devops_agent, mock_llm):
        """Test CI/CD optimization"""
        devops_agent.llm_selector = mock_llm
        
        result = await devops_agent.optimize_cicd(
            pipeline_config="stages: [build, test, deploy]"
        )
        
        assert result["status"] == "completed"
        assert "recommendations" in result


class TestKubernetesDeployment:
    """Test Kubernetes deployment"""
    
    @pytest.mark.asyncio
    async def test_deploy_kubernetes_stub(self, devops_agent):
        """Test K8s deployment stub"""
        result = await devops_agent.deploy_kubernetes(
            app_name="test-app",
            image="test:latest",
            replicas=3
        )
        
        assert result["status"] == "k8s_not_configured"


class TestAutoScaling:
    """Test auto-scaling"""
    
    @pytest.mark.asyncio
    async def test_auto_scale(self, devops_agent, mock_llm):
        """Test auto-scaling decision"""
        mock_llm.generate.return_value = {
            "response": '{"action": "scale_up", "replicas": 5, "reasoning": "High CPU"}',
            "model": "qwen-test"
        }
        devops_agent.llm_selector = mock_llm
        
        result = await devops_agent.auto_scale(
            app_name="test-app",
            metrics={"cpu": 85, "memory": 70, "rps": 1000}
        )
        
        assert result["status"] == "completed"
        assert "decision" in result


class TestNewModularMethods:
    """Integration tests for new modular service methods"""

    @pytest.mark.asyncio
    async def test_optimize_pipeline(self, devops_agent):
        """Test pipeline optimization using PipelineOptimizer service"""
        pipeline_config = {
            "name": "test-pipeline",
            "platform": "github_actions",
            "config_yaml": "name: CI\non: [push]",
            "stages": ["build", "test", "deploy"]
        }
        metrics = {
            "total_duration": 1500,
            "build_time": 300,
            "test_time": 900,
            "deploy_time": 300
        }

        result = await devops_agent.optimize_pipeline(pipeline_config, metrics)

        assert result["status"] == "completed"
        assert "analysis" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    @pytest.mark.asyncio
    async def test_analyze_logs_enhanced(self, devops_agent, tmp_path):
        """Test enhanced log analysis using LogAnalyzer service"""
        # Create temp log file
        log_file = tmp_path / "test.log"
        log_file.write_text("""
ERROR OutOfMemoryError: heap space
ERROR Connection refused
INFO Application started
""")

        result = await devops_agent.analyze_logs_enhanced(
            str(log_file), "application"
        )

        assert result["status"] == "completed"
        assert "service_analysis" in result

    @pytest.mark.asyncio
    async def test_optimize_infrastructure_costs(self, devops_agent):
        """Test cost optimization using CostOptimizer service"""
        current_setup = {
            "provider": "aws",
            "instance_type": "m5.2xlarge",
            "instance_count": 3,
            "pricing_model": "on_demand"
        }
        usage_metrics = {
            "cpu_avg": 30.0,
            "memory_avg": 40.0
        }

        result = await devops_agent.optimize_infrastructure_costs(
            current_setup, usage_metrics
        )

        assert result["status"] == "completed"
        assert "optimization_result" in result

    @pytest.mark.asyncio
    async def test_generate_terraform(self, devops_agent):
        """Test Terraform generation using IaCGenerator service"""
        requirements = {
            "provider": "aws",
            "services": ["compute", "database"],
            "environment": "production"
        }

        result = await devops_agent.generate_infrastructure_code(
            "terraform", requirements
        )

        assert result["status"] == "completed"
        assert result["iac_type"] == "terraform"
        assert "files" in result
        assert "main.tf" in result["files"]

    @pytest.mark.asyncio
    async def test_generate_kubernetes(self, devops_agent):
        """Test Kubernetes generation using IaCGenerator service"""
        requirements = {
            "app_name": "test-app",
            "replicas": 3,
            "image": "test:1.0.0",
            "port": 8080
        }

        result = await devops_agent.generate_infrastructure_code(
            "kubernetes", requirements
        )

        assert result["status"] == "completed"
        assert result["iac_type"] == "kubernetes"
        assert "deployment.yaml" in result["files"]

    @pytest.mark.asyncio
    async def test_analyze_docker_infrastructure(self, devops_agent, tmp_path):
        """Test Docker infrastructure analysis using DockerAnalyzer"""
        # Create temp docker-compose.yml
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("""
version: '3.8'
services:
  web:
    image: nginx:1.21
    ports:
      - "80:80"
""")

        result = await devops_agent.analyze_docker_infrastructure(
            str(compose_file)
        )

        assert result["status"] == "completed"
        assert "infrastructure_analysis" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

