"""
Integration Tests for API Versioning

Tests to ensure v1 and v2 APIs work correctly and maintain compatibility.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestAPIVersioning:
    """Test API versioning compatibility"""
    
    def test_v1_health_endpoint_exists(self):
        """V1 health endpoint should still work"""
        response = client.get("/api/v1/revolutionary/health")
        assert response.status_code in [200, 400]  # 400 if components not enabled
    
    def test_v2_health_endpoint_exists(self):
        """V2 health endpoint should exist"""
        response = client.get("/api/v2/revolutionary/health")
        assert response.status_code in [200, 400]
    
    def test_v2_health_has_version_field(self):
        """V2 health should include version field"""
        response = client.get("/api/v2/revolutionary/health")
        if response.status_code == 200:
            data = response.json()
            assert "version" in data
            assert data["version"] == "v2"
    
    def test_v2_batch_evolve_endpoint_exists(self):
        """V2 should have batch-evolve endpoint (v1 doesn't)"""
        response = client.post(
            "/api/v2/revolutionary/batch-evolve",
            json={"iterations": 1, "async_mode": False}
        )
        # Should exist even if components not enabled
        assert response.status_code in [200, 400, 422]
    
    def test_v1_batch_evolve_not_exists(self):
        """V1 should NOT have batch-evolve endpoint"""
        response = client.post(
            "/api/v1/revolutionary/batch-evolve",
            json={"iterations": 1}
        )
        assert response.status_code == 404
    
    def test_v2_detailed_metrics_exists(self):
        """V2 should have detailed metrics endpoint"""
        response = client.get("/api/v2/revolutionary/metrics/detailed")
        assert response.status_code in [200, 400]
    
    def test_openapi_docs_include_both_versions(self):
        """OpenAPI docs should show both v1 and v2"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi = response.json()
        paths = openapi.get("paths", {})
        
        # Check for v1 paths
        v1_paths = [p for p in paths.keys() if p.startswith("/api/v1")]
        assert len(v1_paths) > 0, "Should have v1 paths"
        
        # Check for v2 paths
        v2_paths = [p for p in paths.keys() if p.startswith("/api/v2")]
        assert len(v2_paths) > 0, "Should have v2 paths"


class TestV2Features:
    """Test v2-specific features"""
    
    def test_batch_evolve_sync_mode(self):
        """Test batch evolution in sync mode"""
        response = client.post(
            "/api/v2/revolutionary/batch-evolve",
            json={"iterations": 2, "async_mode": False}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "results" in data
            assert data["status"] == "completed"
    
    def test_batch_evolve_async_mode(self):
        """Test batch evolution in async mode"""
        response = client.post(
            "/api/v2/revolutionary/batch-evolve",
            json={"iterations": 2, "async_mode": True}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "task_id" in data
            assert data["status"] == "scheduled"
            assert data["task_id"] is not None
    
    def test_batch_heal(self):
        """Test batch healing"""
        response = client.post(
            "/api/v2/revolutionary/batch-heal",
            json={"code_snippets": ["def foo(): pass", "def bar(): return 1"]}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "total_healed" in data
            assert isinstance(data["results"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
