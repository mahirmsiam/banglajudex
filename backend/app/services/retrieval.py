"""
Hybrid Retrieval Service - Combines vector search, keyword matching, and structured filtering.
"""
import logging
import re
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, extract
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models import Case, Paragraph, Judge, Statute, Court, CaseType, Outcome, SectionHeading
from app.services.embeddings import embedding_service
from app.schemas import SearchFilters, SearchResult, Citation

settings = get_settings()
logger = logging.getLogger(__name__)


class RetrievalService:
    """Hybrid retrieval combining vector search, keyword matching, and structured filters."""
    
    # Section priority for ranking (higher = more important)
    SECTION_PRIORITY = {
        SectionHeading.FINDINGS: 1.0,
        SectionHeading.DECISION: 0.9,
        SectionHeading.ISSUES: 0.7,
        SectionHeading.ORDER: 0.6,
        SectionHeading.SUBMISSIONS: 0.5,
        SectionHeading.FACTS: 0.4,
        SectionHeading.UNKNOWN: 0.3,
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Perform hybrid search with structured filtering.
        
        Scoring formula:
        final_score = 0.5 * vector_score + 0.3 * keyword_score + 0.2 * statute_score
        """
        
        # Step 1: Build metadata filter for ChromaDB
        chroma_filter = await self._build_chroma_filter(filters)
        
        # Step 2: Perform vector search
        vector_results = embedding_service.search(
            query=query,
            n_results=top_k * 3,  # Get more for re-ranking
            where=chroma_filter
        )
        
        if not vector_results["ids"]:
            return []
        
        # Step 3: Fetch full paragraph and case data
        paragraph_ids = [UUID(pid) for pid in vector_results["ids"]]
        paragraphs_data = await self._fetch_paragraphs_with_cases(paragraph_ids)
        
        # Step 4: Calculate hybrid scores
        results = []
        for i, para_id in enumerate(vector_results["ids"]):
            para_uuid = UUID(para_id)
            
            if para_uuid not in paragraphs_data:
                continue
            
            para, case = paragraphs_data[para_uuid]
            
            # Vector similarity score (1 - distance for cosine)
            vector_score = 1.0 - vector_results["distances"][i]
            
            # Keyword match score
            keyword_score = self._calculate_keyword_score(query, para.text)
            
            # Statute/section match score
            statute_score = self._calculate_statute_score(query, case, filters)
            
            # Section priority boost
            section_boost = self.SECTION_PRIORITY.get(para.section_heading, 0.3)
            
            # Combined score
            final_score = (
                settings.vector_weight * vector_score +
                settings.keyword_weight * keyword_score +
                settings.statute_weight * statute_score
            ) * (1 + 0.1 * section_boost)  # Small section boost
            
            # Create result
            results.append(SearchResult(
                paragraph_id=para.id,
                case_id=case.id,
                text=para.text,
                citation=Citation(
                    case_title=case.case_title,
                    case_number=case.case_number,
                    page_no=para.page_no,
                    para_no=para.para_no,
                    court=case.court
                ),
                score=final_score,
                section_heading=para.section_heading
            ))
        
        # Sort by score and apply confidence threshold
        results.sort(key=lambda x: x.score, reverse=True)
        results = [r for r in results if r.score >= settings.confidence_threshold]
        
        return results[:top_k]
    
    async def _build_chroma_filter(self, filters: Optional[SearchFilters]) -> Optional[dict]:
        """Build ChromaDB where clause from filters."""
        if not filters:
            return None
        
        conditions = []
        
        if filters.court:
            conditions.append({"court": filters.court.value})
        
        if filters.year_from:
            conditions.append({"year": {"$gte": filters.year_from}})
        
        if filters.year_to:
            conditions.append({"year": {"$lte": filters.year_to}})
        
        if filters.case_type:
            conditions.append({"case_type": filters.case_type.value})
        
        if filters.outcome:
            conditions.append({"outcome": filters.outcome.value})
        
        if len(conditions) == 0:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}
    
    async def _fetch_paragraphs_with_cases(
        self, 
        paragraph_ids: List[UUID]
    ) -> Dict[UUID, tuple]:
        """Fetch paragraphs with their associated cases."""
        result = await self.db.execute(
            select(Paragraph).options(
                selectinload(Paragraph.case).selectinload(Case.judges),
                selectinload(Paragraph.case).selectinload(Case.statutes)
            ).where(Paragraph.id.in_(paragraph_ids))
        )
        
        paragraphs = result.scalars().all()
        return {p.id: (p, p.case) for p in paragraphs}
    
    def _calculate_keyword_score(self, query: str, text: str) -> float:
        """Calculate keyword match score using simple term frequency."""
        query_terms = set(re.findall(r'\b\w+\b', query.lower()))
        text_terms = set(re.findall(r'\b\w+\b', text.lower()))
        
        if not query_terms:
            return 0.0
        
        matches = query_terms.intersection(text_terms)
        return len(matches) / len(query_terms)
    
    def _calculate_statute_score(
        self, 
        query: str, 
        case: Case, 
        filters: Optional[SearchFilters]
    ) -> float:
        """Calculate statute/section match score."""
        score = 0.0
        
        # Check if query mentions statutes
        statute_patterns = [
            r"section\s*(\d+)",
            r"sec\.?\s*(\d+)",
            r"article\s*(\d+)",
        ]
        
        query_lower = query.lower()
        for pattern in statute_patterns:
            match = re.search(pattern, query_lower)
            if match:
                section = match.group(1)
                # Check if case has this section
                for statute in case.statutes:
                    if statute.section and section in statute.section:
                        score += 0.5
                        break
        
        # Check filter-based statute match
        if filters:
            if filters.statute_name:
                for statute in case.statutes:
                    if filters.statute_name.lower() in statute.statute_name.lower():
                        score += 0.3
                        break
            
            if filters.section:
                for statute in case.statutes:
                    if statute.section and filters.section in statute.section:
                        score += 0.2
                        break
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def get_adjacent_paragraphs(
        self, 
        paragraph_id: UUID, 
        window: int = 1
    ) -> List[Paragraph]:
        """Get adjacent paragraphs for context expansion."""
        # Get the target paragraph first
        result = await self.db.execute(
            select(Paragraph).where(Paragraph.id == paragraph_id)
        )
        target = result.scalar_one_or_none()
        
        if not target:
            return []
        
        # Get paragraphs from same case within window
        result = await self.db.execute(
            select(Paragraph).where(
                and_(
                    Paragraph.case_id == target.case_id,
                    Paragraph.page_no == target.page_no,
                    Paragraph.para_no >= target.para_no - window,
                    Paragraph.para_no <= target.para_no + window,
                    Paragraph.id != paragraph_id
                )
            ).order_by(Paragraph.para_no)
        )
        
        return list(result.scalars().all())
    
    async def get_filter_options(self) -> dict:
        """Get available filter options from database."""
        # Courts
        courts = [c.value for c in Court]
        
        # Years
        result = await self.db.execute(
            select(func.extract('year', Case.judgment_date).distinct()).where(
                Case.judgment_date.isnot(None)
            ).order_by(func.extract('year', Case.judgment_date).desc())
        )
        years = [int(y) for y in result.scalars().all() if y]
        
        # Judges
        result = await self.db.execute(
            select(Judge.name).order_by(Judge.name)
        )
        judges = list(result.scalars().all())
        
        # Case types
        case_types = [ct.value for ct in CaseType]
        
        # Outcomes
        outcomes = [o.value for o in Outcome]
        
        # Statutes
        result = await self.db.execute(
            select(Statute.statute_name.distinct()).order_by(Statute.statute_name)
        )
        statutes = list(result.scalars().all())
        
        # Crime categories
        result = await self.db.execute(
            select(Case.crime_category.distinct()).where(
                Case.crime_category.isnot(None)
            ).order_by(Case.crime_category)
        )
        crime_categories = list(result.scalars().all())
        
        return {
            "courts": courts,
            "years": years,
            "judges": judges,
            "case_types": case_types,
            "outcomes": outcomes,
            "statutes": statutes,
            "crime_categories": crime_categories
        }
