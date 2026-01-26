"""
LLM Service - Extractive answering using local Ollama instance.
"""
import logging
from typing import List, Optional

import ollama

from app.config import get_settings
from app.schemas import SearchResult, Citation, ConversationMessage

settings = get_settings()
logger = logging.getLogger(__name__)


# Immutable system prompt as specified
SYSTEM_PROMPT = """You are a judicial text assistant for Bangladesh Supreme Court, Appellate Division, and High Court Division judgments.

STRICT RULES:
- You may ONLY use the text provided in the CONTEXT.
- You MUST NOT use prior knowledge or general legal principles.
- You MUST NOT provide legal advice or interpretation.
- You MUST NOT infer beyond what is explicitly written.
- Every answer MUST include citations in format: (Case Title, Case Number, Page X, Paragraph Y).
- If answer not explicitly stated in the provided text, respond exactly: "No explicit finding on this issue was located in the uploaded judgments."

OUTPUT RULES:
- Use formal legal language.
- Stay close to original wording.
- Do not fabricate citations.
- Do not merge cases unless explicitly asked.
- You are an extractive system, not an interpretive one."""


class LLMService:
    """Service for extractive LLM-based answering."""
    
    # Mandatory refusal response
    REFUSAL_RESPONSE = "No explicit finding on this issue was located in the uploaded judgments."
    
    def __init__(self):
        self.model = settings.llm_model
        self.client = ollama.Client(host=settings.ollama_host)
    
    def _format_context(self, results: List[SearchResult]) -> str:
        """Format retrieved paragraphs as context for the LLM."""
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            citation = result.citation
            context_parts.append(
                f"[{i}] Case: {citation.case_title}\n"
                f"Case Number: {citation.case_number}\n"
                f"Court: {citation.court.value.replace('_', ' ').title()}\n"
                f"Page {citation.page_no}, Paragraph {citation.para_no}:\n"
                f"\"{result.text}\"\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _format_filters(self, filters: Optional[dict]) -> str:
        """Format applied filters for display."""
        if not filters:
            return "None"
        
        parts = []
        for key, value in filters.items():
            if value is not None:
                if hasattr(value, 'value'):
                    parts.append(f"{key}: {value.value}")
                else:
                    parts.append(f"{key}: {value}")
        
        return ", ".join(parts) if parts else "None"
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        filters: Optional[dict] = None,
        conversation_history: Optional[List[ConversationMessage]] = None
    ) -> str:
        """Build the user prompt with context."""
        prompt_parts = [
            f"QUESTION: {query}",
            f"\nFILTERS APPLIED: {self._format_filters(filters)}",
            f"\nCONTEXT:\n{context}"
        ]
        
        if conversation_history:
            history_text = "\n".join([
                f"{msg.role.upper()}: {msg.content}" 
                for msg in conversation_history[-5:]  # Last 5 messages
            ])
            prompt_parts.insert(0, f"CONVERSATION HISTORY:\n{history_text}\n")
        
        return "\n".join(prompt_parts)
    
    async def generate_answer(
        self,
        query: str,
        results: List[SearchResult],
        filters: Optional[dict] = None,
        conversation_history: Optional[List[ConversationMessage]] = None
    ) -> str:
        """
        Generate an extractive answer based on retrieved paragraphs.
        
        Returns the refusal response if:
        - No results found
        - All results below confidence threshold
        - LLM generates a response not grounded in context
        """
        
        # Mandatory refusal if no results
        if not results:
            return self.REFUSAL_RESPONSE
        
        # Format context
        context = self._format_context(results)
        
        # Build prompt
        user_prompt = self._build_prompt(
            query=query,
            context=context,
            filters=filters,
            conversation_history=conversation_history
        )
        
        try:
            # Call Ollama
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,  # Low temperature for factual responses
                    "top_p": 0.9,
                    "num_predict": 1024,
                }
            )
            
            answer = response['message']['content'].strip()
            
            # Validate answer contains citations
            if not self._validate_answer(answer, results):
                logger.warning("LLM response failed validation, returning refusal")
                return self.REFUSAL_RESPONSE
            
            return answer
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return self.REFUSAL_RESPONSE
    
    def _validate_answer(self, answer: str, results: List[SearchResult]) -> bool:
        """
        Validate that the answer is grounded in the provided context.
        
        Checks:
        - Answer is not empty
        - Answer contains at least one citation reference
        - Answer doesn't contain obvious hallucination markers
        """
        if not answer or len(answer) < 10:
            return False
        
        # If it's the refusal response, it's valid
        if self.REFUSAL_RESPONSE in answer:
            return True
        
        # Check for citation markers
        citation_markers = [
            "(", "Page", "Paragraph", "Case"
        ]
        has_citation = any(marker in answer for marker in citation_markers)
        
        # Check for hallucination red flags
        hallucination_markers = [
            "I think", "In my opinion", "Generally speaking",
            "Based on my knowledge", "As I understand",
            "It is commonly known", "Legal principles suggest"
        ]
        has_hallucination = any(
            marker.lower() in answer.lower() 
            for marker in hallucination_markers
        )
        
        return has_citation and not has_hallucination
    
    def extract_citations(self, results: List[SearchResult]) -> List[Citation]:
        """Extract citations from search results."""
        return [r.citation for r in results]
    
    async def check_health(self) -> bool:
        """Check if Ollama is available."""
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False


# Singleton instance
llm_service = LLMService()
