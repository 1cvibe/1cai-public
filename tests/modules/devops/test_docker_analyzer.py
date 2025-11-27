"""
Tests for DockerAnalyzer Service

Unit tests for Docker infrastructure analysis.
"""

import pytest
import tempfile
from pathlib import Path

from src.modules.devops.services.docker_analyzer import DockerAnalyzer


@pytest.fixture
def analyzer():
    """Fixture for DockerAnalyzer instance"""
    return DockerAnalyzer()


@pytest.fixture
def sample_compose_content():
    """Fixture for sample docker-compose.yml content"""
    return """
version: '3.8'

services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  
  app:
    image: myapp:1.0.0
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
"""


@pytest.fixture
def temp_compose_file(sample_compose_content):
    """Fixture for temporary docker-compose.yml file"""
    with tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.yml', prefix='docker-compose-'
    ) as f:
        f.write(sample_compose_content)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink()


class TestDockerAnalyzer:
    """Tests for DockerAnalyzer service"""

    @pytest.mark.asyncio
    async def test_analyze_compose_file(self, analyzer, temp_compose_file):
        """Test docker-compose.yml analysis"""
        result = await analyzer.analyze_compose_file(temp_compose_file)

        assert "service_count" in result
        assert "version" in result
        assert "services_analysis" in result
        assert "security_issues" in result
        assert "performance_issues" in result

    @pytest.mark.asyncio
    async def test_service_count(self, analyzer, temp_compose_file):
        """Test service count detection"""
        result = await analyzer.analyze_compose_file(temp_compose_file)

        assert result["service_count"] == 3  # web, app, postgres

    @pytest.mark.asyncio
    async def test_version_detection(self, analyzer, temp_compose_file):
        """Test compose version detection"""
        result = await analyzer.analyze_compose_file(temp_compose_file)

        assert result["version"] == "3.8"

    @pytest.mark.asyncio
    async def test_latest_tag_detection(self, analyzer, temp_compose_file):
        """Test detection of 'latest' tag usage"""
        result = await analyzer.analyze_compose_file(temp_compose_file)

        # Should detect nginx:latest
        latest_issues = [
            issue for issue in result["security_issues"]
            if "latest" in issue["message"].lower()
        ]
        assert len(latest_issues) > 0

    @pytest.mark.asyncio
    async def test_restart_policy_check(self, analyzer):
        """Test restart policy checking"""
        compose_content = """
version: '3.8'
services:
  web:
    image: nginx:1.21
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml') as f:
            f.write(compose_content)
            temp_path = f.name

        try:
            result = await analyzer.analyze_compose_file(temp_path)

            # Should detect missing restart policy
            restart_issues = [
                issue for issue in result["performance_issues"]
                if "restart" in issue["message"].lower()
            ]
            assert len(restart_issues) > 0
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_healthcheck_detection(self, analyzer):
        """Test healthcheck detection for critical services"""
        compose_content = """
version: '3.8'
services:
  postgres:
    image: postgres:15
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml') as f:
            f.write(compose_content)
            temp_path = f.name

        try:
            result = await analyzer.analyze_compose_file(temp_path)

            # Should detect missing healthcheck for postgres
            healthcheck_issues = [
                issue for issue in result["performance_issues"]
                if "healthcheck" in issue["message"].lower()
            ]
            assert len(healthcheck_issues) > 0
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_privileged_mode_detection(self, analyzer):
        """Test detection of privileged mode (security risk)"""
        compose_content = """
version: '3.8'
services:
  risky:
    image: myapp:1.0
    privileged: true
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml') as f:
            f.write(compose_content)
            temp_path = f.name

        try:
            result = await analyzer.analyze_compose_file(temp_path)

            # Should detect privileged mode
            privileged_issues = [
                issue for issue in result["security_issues"]
                if "privileged" in issue["message"].lower()
            ]
            assert len(privileged_issues) > 0
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_service_status_ok(self, analyzer, temp_compose_file):
        """Test service status when no issues"""
        result = await analyzer.analyze_compose_file(temp_compose_file)

        # App service should be OK (has restart policy and healthcheck)
        app_analysis = result["services_analysis"].get("app", {})
        assert app_analysis.get("status") == "ok"

    @pytest.mark.asyncio
    async def test_service_status_attention_needed(self, analyzer, temp_compose_file):
        """Test service status when issues exist"""
        result = await analyzer.analyze_compose_file(temp_compose_file)

        # Web service should need attention (uses latest tag, no restart policy)
        web_analysis = result["services_analysis"].get("web", {})
        assert web_analysis.get("status") == "attention_needed"

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, analyzer, temp_compose_file):
        """Test recommendations generation"""
        result = await analyzer.analyze_compose_file(temp_compose_file)

        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    @pytest.mark.asyncio
    async def test_check_runtime_status(self, analyzer):
        """Test runtime container status checking"""
        # Note: This test may fail if Docker is not running
        result = await analyzer.check_runtime_status()

        assert isinstance(result, list)
        # Each container should have required fields
        for container in result:
            assert "id" in container
            assert "name" in container
            assert "image" in container
            assert "status" in container

    @pytest.mark.asyncio
    async def test_analyze_infrastructure(self, analyzer, temp_compose_file):
        """Test full infrastructure analysis (static + runtime)"""
        result = await analyzer.analyze_infrastructure(temp_compose_file)

        assert "static_analysis" in result
        assert "runtime_containers" in result
        assert "services_status" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_infrastructure_summary(self, analyzer, temp_compose_file):
        """Test infrastructure analysis summary"""
        result = await analyzer.analyze_infrastructure(temp_compose_file)

        summary = result["summary"]
        assert "total_services" in summary
        assert "running_containers" in summary
        assert "security_issues_count" in summary
        assert "performance_issues_count" in summary

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, analyzer):
        """Test error handling for missing file"""
        with pytest.raises(Exception):  # Should raise DockerAnalysisError
            await analyzer.analyze_compose_file("nonexistent-file.yml")

    @pytest.mark.asyncio
    async def test_invalid_yaml_error(self, analyzer):
        """Test error handling for invalid YAML"""
        invalid_yaml = "invalid: yaml: content: [unclosed"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml') as f:
            f.write(invalid_yaml)
            temp_path = f.name

        try:
            with pytest.raises(Exception):  # Should raise DockerAnalysisError
                await analyzer.analyze_compose_file(temp_path)
        finally:
            Path(temp_path).unlink()
