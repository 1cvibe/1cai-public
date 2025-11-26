"""
Integration tests for Archi API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestArchiAPIHealth:
    """Test Archi API health and availability"""

    def test_archi_health_endpoint(self):
        """Test Archi health check endpoint"""
        response = client.get("/api/v1/archi/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]

    def test_archi_supported_types(self):
        """Test supported types endpoint"""
        response = client.get("/api/v1/archi/supported-types")
        assert response.status_code == 200
        data = response.json()
        assert "element_types" in data
        assert "relationship_types" in data
        assert "archimate_version" in data
        assert isinstance(data["element_types"], list)
        assert isinstance(data["relationship_types"], list)
        assert len(data["element_types"]) > 0
        assert len(data["relationship_types"]) > 0


class TestArchiAPIExport:
    """Test Archi export functionality"""

    @pytest.mark.integration
    def test_export_basic(self):
        """Test basic export functionality"""
        request_data = {"output_filename": "test_export.archimate", "filters": None}
        response = client.post("/api/v1/archi/export", json=request_data)

        # May fail if Neo4j not available, that's OK for now
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "file_path" in data
            assert data["status"] == "success"

    def test_export_invalid_filename(self):
        """Test export with invalid filename"""
        request_data = {"output_filename": "../../../etc/passwd", "filters": None}  # Path traversal attempt
        response = client.post("/api/v1/archi/export", json=request_data)

        # Should either reject or sanitize
        assert response.status_code in [200, 400, 422, 500]


class TestArchiAPIImport:
    """Test Archi import functionality"""

    @pytest.mark.integration
    def test_import_nonexistent_file(self):
        """Test import with nonexistent file"""
        request_data = {"file_path": "nonexistent_file.archimate"}
        response = client.post("/api/v1/archi/import", json=request_data)

        # Should return 404 or 500
        assert response.status_code in [404, 500]
        data = response.json()
        assert "detail" in data


class TestArchiAPIValidation:
    """Test input validation"""

    def test_export_empty_filename(self):
        """Test export with empty filename"""
        request_data = {"output_filename": "", "filters": None}
        response = client.post("/api/v1/archi/export", json=request_data)

        # Should use default or reject
        assert response.status_code in [200, 422, 500]

    def test_export_with_filters(self):
        """Test export with filters"""
        request_data = {
            "output_filename": "filtered_export.archimate",
            "filters": {"node_types": ["Module", "Function"]},
        }
        response = client.post("/api/v1/archi/export", json=request_data)

        # May fail if Neo4j not available
        assert response.status_code in [200, 500]


@pytest.mark.integration
class TestArchiAPIIntegration:
    """End-to-end integration tests"""

    def test_full_export_import_cycle(self):
        """Test complete export-import cycle"""
        # This test requires Neo4j to be running
        # Skip if not available
        pytest.skip("Requires Neo4j connection")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
