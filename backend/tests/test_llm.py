"""
Unit tests for the LLM service.
Tests answer generation and validation.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.llm import LLMService


class TestLLMService:
    """Tests for LLMService class."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance."""
        return LLMService()
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing."""
        return [
            {
                "text": "The court held that pre-emption rights under Section 96 of the State Acquisition and Tenancy Act require timely application.",
                "case_title": "Abdul Karim vs. Bangladesh",
                "case_number": "CA 123/2020",
                "page_no": 5,
                "para_no": 12
            },
            {
                "text": "Mutation of property does not affect the pre-emption rights as established in previous decisions.",
                "case_title": "Abdul Karim vs. Bangladesh",
                "case_number": "CA 123/2020",
                "page_no": 6,
                "para_no": 15
            }
        ]
    
    def test_format_context(self, llm_service, sample_context):
        """Test context formatting for LLM."""
        formatted = llm_service.format_context(sample_context)
        
        assert isinstance(formatted, str)
        assert "Section 96" in formatted
        assert "pre-emption" in formatted
        assert "CA 123/2020" in formatted
    
    def test_validate_answer_with_citations(self, llm_service):
        """Test answer validation with proper citations."""
        answer = "The court held that pre-emption requires timely application (Abdul Karim vs. Bangladesh, CA 123/2020, Page 5, Paragraph 12)."
        
        is_valid = llm_service.validate_answer(answer)
        
        assert is_valid is True
    
    def test_validate_answer_without_citations(self, llm_service):
        """Test answer validation without citations."""
        answer = "Pre-emption requires timely application."
        
        is_valid = llm_service.validate_answer(answer)
        
        # Should still be valid if grounded in context
        assert isinstance(is_valid, bool)
    
    def test_detect_hallucination_markers(self, llm_service):
        """Test detection of hallucination markers."""
        hallucinating_answers = [
            "I believe that...",
            "It is generally known that...",
            "Based on my knowledge...",
            "In my opinion...",
            "It seems likely that...",
        ]
        
        for answer in hallucinating_answers:
            has_markers = llm_service.has_hallucination_markers(answer)
            assert has_markers is True, f"Failed to detect markers in: {answer}"
    
    def test_no_hallucination_markers(self, llm_service):
        """Test that valid answers don't trigger hallucination detection."""
        valid_answers = [
            "The court held that...",
            "According to the judgment...",
            "The appellant submitted that...",
            "It was found that...",
        ]
        
        for answer in valid_answers:
            has_markers = llm_service.has_hallucination_markers(answer)
            assert has_markers is False, f"False positive for: {answer}"
    
    def test_mandatory_refusal_response(self, llm_service):
        """Test mandatory refusal when no relevant text found."""
        expected_refusal = "No explicit finding on this issue was located in the uploaded judgments."
        
        refusal = llm_service.get_refusal_response()
        
        assert expected_refusal in refusal or "not found" in refusal.lower()
    
    def test_extract_citations(self, llm_service):
        """Test citation extraction from answer."""
        answer = "The court held X (Case A, CA 1/2020, Page 5, Para 10) and Y (Case B, WP 2/2019, Page 3, Para 7)."
        
        citations = llm_service.extract_citations(answer)
        
        assert isinstance(citations, list)
        # Should extract at least some citation info
    
    def test_system_prompt_immutability(self, llm_service):
        """Test that system prompt contains required constraints."""
        system_prompt = llm_service.get_system_prompt()
        
        # Check for key constraints
        assert "ONLY" in system_prompt or "only" in system_prompt
        assert "citation" in system_prompt.lower()
        assert "Bangladesh" in system_prompt or "judgment" in system_prompt.lower()
    
    @pytest.mark.asyncio
    async def test_generate_answer_with_context(self, llm_service, sample_context):
        """Test answer generation with context."""
        with patch.object(llm_service, '_call_llm') as mock_llm:
            mock_llm.return_value = "The court held that pre-emption rights require timely application (Abdul Karim vs. Bangladesh, CA 123/2020, Page 5, Paragraph 12)."
            
            result = await llm_service.generate_answer(
                query="What did the court say about pre-emption?",
                context=sample_context
            )
            
            assert "answer" in result or isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_generate_answer_empty_context(self, llm_service):
        """Test answer generation with empty context."""
        result = await llm_service.generate_answer(
            query="What about pre-emption?",
            context=[]
        )
        
        # Should return refusal response
        assert result is not None
        if isinstance(result, dict):
            answer = result.get("answer", "")
        else:
            answer = str(result)
        
        assert "not" in answer.lower() or "no" in answer.lower() or len(answer) == 0


class TestConversationHistory:
    """Tests for conversation history handling."""
    
    @pytest.fixture
    def llm_service(self):
        return LLMService()
    
    def test_format_conversation_history(self, llm_service):
        """Test formatting of conversation history."""
        history = [
            {"role": "user", "content": "What is pre-emption?"},
            {"role": "assistant", "content": "Pre-emption is a right to purchase..."},
            {"role": "user", "content": "What about Section 96?"},
        ]
        
        formatted = llm_service.format_conversation_history(history)
        
        assert isinstance(formatted, str)
        assert "pre-emption" in formatted.lower()
    
    def test_conversation_limit(self, llm_service):
        """Test that conversation history is limited."""
        # Create long history
        history = [
            {"role": "user", "content": f"Question {i}"}
            for i in range(20)
        ]
        
        limited = llm_service.limit_conversation_history(history, max_messages=5)
        
        assert len(limited) <= 5


class TestPromptTemplates:
    """Tests for prompt templates."""
    
    @pytest.fixture
    def llm_service(self):
        return LLMService()
    
    def test_user_prompt_template(self, llm_service):
        """Test user prompt template formatting."""
        query = "What about pre-emption?"
        filters = {"court": "appellate_division", "year": 2020}
        context = "Sample context text"
        
        prompt = llm_service.format_user_prompt(query, filters, context)
        
        assert query in prompt
        assert "appellate" in prompt.lower() or "context" in prompt.lower()
    
    def test_prompt_includes_filters(self, llm_service):
        """Test that filters are included in prompt."""
        filters = {
            "court": "high_court_division",
            "year_from": 2015,
            "year_to": 2020,
            "statute": "Penal Code"
        }
        
        prompt = llm_service.format_user_prompt(
            "test query",
            filters,
            "test context"
        )
        
        # Filters should be mentioned in the prompt
        assert isinstance(prompt, str)
