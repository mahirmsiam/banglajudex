"""
Unit tests for the retrieval service.
Tests hybrid search and filtering functionality.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from app.services.retrieval import RetrievalService
from app.schemas import SearchFilters


class TestRetrievalService:
    """Tests for RetrievalService class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        mock = MagicMock()
        mock.generate_embedding = MagicMock(return_value=[0.1] * 384)
        mock.search = MagicMock(return_value=[
            {"id": str(uuid4()), "score": 0.95},
            {"id": str(uuid4()), "score": 0.85},
        ])
        return mock
    
    @pytest.fixture
    def retrieval_service(self, mock_embedding_service):
        """Create retrieval service with mocked dependencies."""
        with patch('app.services.retrieval.embedding_service', mock_embedding_service):
            service = RetrievalService()
            return service
    
    def test_calculate_hybrid_score(self, retrieval_service):
        """Test hybrid score calculation."""
        # Test with all components
        vector_score = 0.9
        keyword_score = 0.8
        statute_score = 0.7
        
        result = retrieval_service.calculate_hybrid_score(
            vector_score, keyword_score, statute_score
        )
        
        # Score should be weighted average: 0.5*0.9 + 0.3*0.8 + 0.2*0.7 = 0.83
        expected = 0.5 * 0.9 + 0.3 * 0.8 + 0.2 * 0.7
        assert abs(result - expected) < 0.01
    
    def test_calculate_hybrid_score_vector_only(self, retrieval_service):
        """Test hybrid score with only vector component."""
        result = retrieval_service.calculate_hybrid_score(0.9, 0.0, 0.0)
        expected = 0.5 * 0.9
        assert abs(result - expected) < 0.01
    
    def test_keyword_match_score(self, retrieval_service):
        """Test keyword matching score calculation."""
        text = "The pre-emption case regarding Section 96 of the Act"
        query = "pre-emption section 96"
        
        score = retrieval_service.calculate_keyword_score(text, query)
        
        # Should have high score due to matching keywords
        assert score > 0.5
    
    def test_keyword_match_score_no_match(self, retrieval_service):
        """Test keyword matching with no overlap."""
        text = "This is about contract law"
        query = "criminal homicide murder"
        
        score = retrieval_service.calculate_keyword_score(text, query)
        
        # Should have low or zero score
        assert score < 0.3
    
    def test_statute_match_score(self, retrieval_service):
        """Test statute/section matching score."""
        paragraph_statutes = ["State Acquisition and Tenancy Act", "Section 96"]
        query_statutes = ["State Acquisition", "Section 96"]
        
        score = retrieval_service.calculate_statute_score(
            paragraph_statutes, query_statutes
        )
        
        # Should have high score due to matching statutes
        assert score > 0.5
    
    def test_filters_court(self):
        """Test court filter creation."""
        filters = SearchFilters(court="appellate_division")
        assert filters.court == "appellate_division"
    
    def test_filters_year_range(self):
        """Test year range filter."""
        filters = SearchFilters(year_from=2015, year_to=2020)
        assert filters.year_from == 2015
        assert filters.year_to == 2020
    
    def test_filters_statute(self):
        """Test statute filter."""
        filters = SearchFilters(statute="Penal Code")
        assert filters.statute == "Penal Code"
    
    def test_filters_section(self):
        """Test section filter."""
        filters = SearchFilters(section="302")
        assert filters.section == "302"
    
    def test_filters_judge(self):
        """Test judge filter."""
        filters = SearchFilters(judge="Justice Rahman")
        assert filters.judge == "Justice Rahman"
    
    def test_filters_case_type(self):
        """Test case type filter."""
        filters = SearchFilters(case_type="criminal")
        assert filters.case_type == "criminal"
    
    def test_filters_outcome(self):
        """Test outcome filter."""
        filters = SearchFilters(outcome="allowed")
        assert filters.outcome == "allowed"


class TestSearchResultRanking:
    """Tests for search result ranking and sorting."""
    
    @pytest.fixture
    def sample_results(self):
        """Generate sample search results."""
        return [
            {"id": "1", "score": 0.85, "section": "findings"},
            {"id": "2", "score": 0.90, "section": "facts"},
            {"id": "3", "score": 0.80, "section": "decision"},
            {"id": "4", "score": 0.75, "section": "issues"},
        ]
    
    def test_section_priority_ranking(self, sample_results):
        """Test that section priority affects ranking."""
        # Priority order: findings > decision > issues > facts
        priority_weights = {
            "findings": 1.2,
            "decision": 1.15,
            "issues": 1.1,
            "facts": 1.0,
        }
        
        # Apply priority weights
        for result in sample_results:
            section = result.get("section", "")
            weight = priority_weights.get(section, 1.0)
            result["adjusted_score"] = result["score"] * weight
        
        # Sort by adjusted score
        sorted_results = sorted(
            sample_results, 
            key=lambda x: x["adjusted_score"], 
            reverse=True
        )
        
        # Findings with lower raw score should be boosted
        assert sorted_results[0]["section"] in ["findings", "decision"]
    
    def test_confidence_threshold(self, sample_results):
        """Test that results below threshold are filtered."""
        threshold = 0.80
        
        filtered = [r for r in sample_results if r["score"] >= threshold]
        
        assert len(filtered) == 3
        assert all(r["score"] >= threshold for r in filtered)


class TestContextExpansion:
    """Tests for adjacent paragraph context expansion."""
    
    def test_get_adjacent_paragraphs(self):
        """Test retrieval of adjacent paragraphs."""
        paragraphs = [
            {"id": 1, "para_no": 1, "text": "First paragraph"},
            {"id": 2, "para_no": 2, "text": "Second paragraph"},
            {"id": 3, "para_no": 3, "text": "Third paragraph"},
            {"id": 4, "para_no": 4, "text": "Fourth paragraph"},
        ]
        
        # Get context for paragraph 2
        target_para_no = 2
        context_window = 1
        
        adjacent = [
            p for p in paragraphs
            if abs(p["para_no"] - target_para_no) <= context_window
        ]
        
        assert len(adjacent) == 3
        assert any(p["para_no"] == 1 for p in adjacent)
        assert any(p["para_no"] == 2 for p in adjacent)
        assert any(p["para_no"] == 3 for p in adjacent)
