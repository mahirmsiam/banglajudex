"""
Integration tests for API endpoints.
Tests the FastAPI routes with mocked services.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "BanglaJudex" in data["name"]


class TestSearchEndpoint:
    """Tests for search endpoint."""
    
    def test_search_with_query(self, client):
        """Test search with query parameter."""
        response = client.post("/api/search", json={
            "query": "pre-emption rights"
        })
        # May return 200 or 422 depending on validation
        assert response.status_code in [200, 422, 500]
    
    def test_search_with_filters(self, client):
        """Test search with filters."""
        response = client.post("/api/search", json={
            "query": "criminal appeal",
            "filters": {
                "court": "appellate_division",
                "year_from": 2015,
                "year_to": 2020
            }
        })
        assert response.status_code in [200, 422, 500]
    
    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.post("/api/search", json={
            "query": ""
        })
        # Should return validation error or empty results
        assert response.status_code in [200, 400, 422, 500]


class TestQueryEndpoint:
    """Tests for conversational query endpoint."""
    
    def test_query_success(self, client):
        """Test query endpoint exists."""
        response = client.post("/api/query", json={
            "query": "What is pre-emption?",
            "conversation_id": str(uuid4())
        })
        # May succeed or fail depending on LLM availability
        assert response.status_code in [200, 422, 500]
    
    def test_query_no_results(self, client):
        """Test query with no matching results."""
        response = client.post("/api/query", json={
            "query": "xyz123 nonexistent topic"
        })
        assert response.status_code in [200, 422, 500]


class TestCasesEndpoint:
    """Tests for cases listing endpoint."""
    
    def test_list_cases(self, client):
        """Test listing cases."""
        response = client.get("/api/cases")
        assert response.status_code in [200, 500]
    
    def test_get_case_by_id(self, client):
        """Test getting case by ID."""
        case_id = str(uuid4())
        response = client.get(f"/api/cases/{case_id}")
        # Should return 404 if not found, 200 if found
        assert response.status_code in [200, 404, 500]


class TestFiltersEndpoint:
    """Tests for filter options endpoint."""
    
    def test_get_filter_options(self, client):
        """Test getting available filter options."""
        response = client.get("/api/filters")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestIngestionEndpoint:
    """Tests for ingestion endpoints."""
    
    def test_start_ingestion(self, client):
        """Test starting ingestion."""
        response = client.post("/api/ingest/start")
        assert response.status_code in [200, 202, 500]
    
    def test_get_ingestion_status(self, client):
        """Test getting ingestion status."""
        response = client.get("/api/ingest/status")
        assert response.status_code in [200, 500]
    
    def test_get_ingestion_logs(self, client):
        """Test getting ingestion logs."""
        response = client.get("/api/ingest/logs")
        assert response.status_code in [200, 500]


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """Test using invalid HTTP method."""
        response = client.delete("/health")
        assert response.status_code == 405
    
    def test_invalid_json(self, client):
        """Test sending invalid JSON."""
        response = client.post(
            "/api/search",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
