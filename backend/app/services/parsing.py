"""
Judgment Parsing Service - Extracts metadata from judgment text.
"""
import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Judge, Statute, Case, CaseType, Outcome, Court, SectionHeading

logger = logging.getLogger(__name__)


class JudgmentParsingService:
    """Service for parsing judgment metadata from text."""
    
    # Common Bangladesh statute patterns
    STATUTE_PATTERNS = [
        # General pattern: Section X of Act Name
        r"(?:Section|Sec\.?|S\.?)\s*(\d+(?:\s*\(\d+\))?(?:\s*[a-zA-Z])?)\s+of\s+(?:the\s+)?([A-Z][A-Za-z\s]+(?:Act|Code|Ordinance|Rules?|Regulation))\s*,?\s*(\d{4})?",
        # Pattern with article
        r"(?:Article)\s*(\d+(?:\s*\(\d+\))?)\s+of\s+(?:the\s+)?([A-Z][A-Za-z\s]+(?:Constitution))",
        # Code sections
        r"(?:Section|Sec\.?|S\.?)\s*(\d+(?:\s*[A-Z])?)\s+(?:of\s+)?(?:the\s+)?(Penal Code|Criminal Procedure Code|Civil Procedure Code|Evidence Act)",
    ]
    
    # Case type patterns
    CASE_TYPE_PATTERNS = {
        CaseType.CIVIL: [r"civil\s*appeal", r"civil\s*revision", r"civil\s*petition", r"C\.A\.", r"C\.P\."],
        CaseType.CRIMINAL: [r"criminal\s*appeal", r"criminal\s*revision", r"Crl\.", r"Cr\."],
        CaseType.REVISION: [r"revision", r"C\.R\.P\.", r"Crl\.R\.P\."],
        CaseType.APPEAL: [r"appeal", r"first\s*appeal"],
        CaseType.WRIT: [r"writ\s*petition", r"W\.P\."],
        CaseType.CONTEMPT: [r"contempt", r"Con\.P\."],
        CaseType.REVIEW: [r"review\s*petition"],
    }
    
    # Outcome patterns
    OUTCOME_PATTERNS = {
        Outcome.ALLOWED: [r"\ballowed\b", r"\bgranted\b", r"\baccepted\b"],
        Outcome.DISMISSED: [r"\bdismissed\b", r"\brejected\b"],
        Outcome.REMANDED: [r"\bremanded\b", r"\bsent\s+back\b"],
        Outcome.CONFIRMED: [r"\bconfirmed\b", r"\bupheld\b", r"\baffirmed\b"],
        Outcome.DISPOSED: [r"\bdisposed\s+of\b"],
        Outcome.DISCHARGED: [r"\bdischarged\b"],
    }
    
    # Judge name patterns
    JUDGE_PATTERNS = [
        r"(?:Hon['']?ble|Honourable)\s+(?:Mr\.?\s+)?Justice\s+([A-Z][a-zA-Z\.\s]+?)(?=,|\s+and|\s+JJ|\s+J\.|$)",
        r"([A-Z][a-zA-Z\.\s]+?),?\s*(?:C\.?J\.?|J\.)",
        r"PRESENT:\s*([A-Z][A-Za-z\.\s,]+?)(?:\n|$)",
        r"BENCH:\s*([A-Z][A-Za-z\.\s,]+?)(?:\n|$)",
    ]
    
    # Section heading keywords
    SECTION_KEYWORDS = {
        SectionHeading.FACTS: ["facts", "factual background", "brief facts", "case history"],
        SectionHeading.ISSUES: ["issues", "questions", "points for determination", "framed"],
        SectionHeading.SUBMISSIONS: ["submissions", "arguments", "contentions", "learned counsel"],
        SectionHeading.FINDINGS: ["findings", "consideration", "discussion", "analysis", "observed"],
        SectionHeading.DECISION: ["decision", "held", "conclude", "judgment"],
        SectionHeading.ORDER: ["order", "decree", "disposed", "accordingly", "result"],
    }
    
    def parse_judgment(self, text: str, filename: str, court: Court) -> Dict[str, Any]:
        """Parse judgment text and extract metadata."""
        metadata = {
            "case_title": self._extract_case_title(text, filename),
            "case_number": self._extract_case_number(text, filename),
            "judgment_date": self._extract_date(text),
            "case_type": self._extract_case_type(text, filename),
            "outcome": self._extract_outcome(text),
            "parties": self._extract_parties(text),
            "crime_category": self._extract_crime_category(text),
            "judges": self._extract_judges(text),
            "statutes": self._extract_statutes(text),
        }
        
        return metadata
    
    def _extract_case_title(self, text: str, filename: str) -> str:
        """Extract case title (parties names)."""
        # Try common patterns first
        patterns = [
            r"([A-Z][A-Za-z\s\.]+)\s+(?:Vs?\.?|versus|v\.)\s+([A-Z][A-Za-z\s\.]+)",
            r"^([A-Z][A-Za-z\s\.]+)\s*\n\s*(?:Appellant|Petitioner)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE | re.MULTILINE)
            if match:
                if len(match.groups()) >= 2:
                    return f"{match.group(1).strip()} vs. {match.group(2).strip()}"
                return match.group(1).strip()
        
        # Fallback to filename
        return filename.replace(".pdf", "").replace("_", " ")
    
    def _extract_case_number(self, text: str, filename: str) -> str:
        """Extract case number."""
        patterns = [
            r"(C\.?A\.?\s*No\.?\s*\d+(?:\s*[-/]\s*\d+)*\s*(?:of)?\s*\d{4})",
            r"(C\.?P\.?\s*No\.?\s*\d+(?:\s*[-/]\s*\d+)*\s*(?:of)?\s*\d{4})",
            r"(Crl\.?\s*(?:A|P|R\.?P)\.?\s*No\.?\s*\d+(?:\s*[-/]\s*\d+)*\s*(?:of)?\s*\d{4})",
            r"(Civil\s+(?:Appeal|Petition|Revision)\s+No\.?\s*\d+\s*(?:of)?\s*\d{4})",
            r"(Criminal\s+(?:Appeal|Petition|Revision)\s+No\.?\s*\d+\s*(?:of)?\s*\d{4})",
            r"(Writ\s+Petition\s+No\.?\s*\d+\s*(?:of)?\s*\d{4})",
            r"(W\.?P\.?\s*No\.?\s*\d+\s*(?:of)?\s*\d{4})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:3000], re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Extract from filename
        return self._extract_case_number_from_filename(filename)
    
    def _extract_case_number_from_filename(self, filename: str) -> str:
        """Extract case number from filename."""
        # Remove extension
        name = filename.replace(".pdf", "")
        
        # Try to parse common patterns
        patterns = [
            r"(C\.?A\.?\s*No\.?\s*\d+(?:_|\s*of\s*)\d{4})",
            r"(C\.?P\.?\s*No\.?\s*\d+(?:_|\s*of\s*)\d{4})",
            r"(\d+[_-]\d{4})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1).replace("_", " of ")
        
        return name
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract judgment date."""
        patterns = [
            r"(?:Judgment|Delivered|Dated?|Date of (?:Judgment|Order))[:\s]+(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})",
            r"(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+(\d{4})",
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?[,\s]+(\d{4})",
        ]
        
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        for pattern in patterns:
            match = re.search(pattern, text[:5000], re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    if groups[1].lower() in months:
                        # Day Month Year format
                        day = int(groups[0])
                        month = months[groups[1].lower()]
                        year = int(groups[2])
                    elif groups[0].lower() in months:
                        # Month Day Year format
                        month = months[groups[0].lower()]
                        day = int(groups[1])
                        year = int(groups[2])
                    else:
                        # DD/MM/YYYY format
                        day = int(groups[0])
                        month = int(groups[1])
                        year = int(groups[2])
                    
                    return datetime(year, month, day)
                except (ValueError, KeyError):
                    continue
        
        return None
    
    def _extract_case_type(self, text: str, filename: str) -> Optional[CaseType]:
        """Extract case type."""
        combined = f"{filename.lower()} {text[:2000].lower()}"
        
        for case_type, patterns in self.CASE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return case_type
        
        return CaseType.OTHER
    
    def _extract_outcome(self, text: str) -> Optional[Outcome]:
        """Extract case outcome."""
        # Look in the last 2000 characters (usually conclusion)
        ending = text[-2000:].lower()
        
        for outcome, patterns in self.OUTCOME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, ending, re.IGNORECASE):
                    return outcome
        
        return Outcome.OTHER
    
    def _extract_parties(self, text: str) -> Optional[str]:
        """Extract party names."""
        patterns = [
            r"([A-Z][A-Za-z\s\.]+?)\s*[\.\:\-]+\s*(?:Appellant|Petitioner)",
            r"(?:Appellant|Petitioner)[:\s]+([A-Z][A-Za-z\s\.]+)",
            r"([A-Z][A-Za-z\s\.]+?)\s*[\.\:\-]+\s*(?:Respondent|Opposite Party)",
        ]
        
        parties = []
        for pattern in patterns:
            matches = re.findall(pattern, text[:3000], re.IGNORECASE)
            parties.extend([m.strip() for m in matches if len(m.strip()) > 3])
        
        if parties:
            return " | ".join(parties[:4])  # Max 4 parties
        return None
    
    def _extract_crime_category(self, text: str) -> Optional[str]:
        """Extract crime category for criminal cases."""
        crime_keywords = [
            "murder", "culpable homicide", "rape", "robbery", "theft",
            "cheating", "forgery", "corruption", "dowry", "assault",
            "kidnapping", "abduction", "extortion", "defamation",
            "narcotics", "arms act", "explosive", "terrorism"
        ]
        
        text_lower = text.lower()
        for crime in crime_keywords:
            if crime in text_lower:
                return crime.title()
        
        return None
    
    def _extract_judges(self, text: str) -> List[str]:
        """Extract judge names."""
        judges = set()
        
        for pattern in self.JUDGE_PATTERNS:
            matches = re.findall(pattern, text[:3000], re.IGNORECASE)
            for match in matches:
                # Clean up judge names
                name = match.strip()
                name = re.sub(r"\s+", " ", name)
                name = re.sub(r"[,\s]+$", "", name)
                
                # Filter out too short or too long names
                if 5 < len(name) < 100:
                    judges.add(name)
        
        return list(judges)[:5]  # Max 5 judges
    
    def _extract_statutes(self, text: str) -> List[Dict[str, str]]:
        """Extract statute citations."""
        statutes = []
        seen = set()
        
        for pattern in self.STATUTE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                section = groups[0].strip() if len(groups) > 0 else None
                name = groups[1].strip() if len(groups) > 1 else None
                year = groups[2] if len(groups) > 2 else None
                
                if name and year:
                    full_name = f"{name}, {year}"
                elif name:
                    full_name = name
                else:
                    continue
                
                key = f"{full_name}|{section}"
                if key not in seen:
                    seen.add(key)
                    statutes.append({
                        "name": full_name,
                        "section": section
                    })
        
        return statutes[:20]  # Max 20 statutes
    
    def classify_section(self, text: str) -> Optional[SectionHeading]:
        """Classify paragraph into logical section."""
        text_lower = text.lower()[:200]  # Check first 200 chars
        
        for section, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return section
        
        return SectionHeading.UNKNOWN
    
    async def add_judge_to_case(
        self, 
        db: AsyncSession, 
        case: Case, 
        judge_name: str
    ) -> Judge:
        """Add a judge to a case, creating if necessary."""
        # Check if judge exists
        result = await db.execute(
            select(Judge).where(Judge.name == judge_name)
        )
        judge = result.scalar_one_or_none()
        
        if not judge:
            judge = Judge(name=judge_name)
            db.add(judge)
            await db.flush()
        
        case.judges.append(judge)
        return judge
    
    async def add_statute_to_case(
        self, 
        db: AsyncSession, 
        case: Case, 
        statute_name: str, 
        section: Optional[str] = None
    ) -> Statute:
        """Add a statute to a case, creating if necessary."""
        # Check if statute exists
        result = await db.execute(
            select(Statute).where(
                Statute.statute_name == statute_name,
                Statute.section == section
            )
        )
        statute = result.scalar_one_or_none()
        
        if not statute:
            statute = Statute(statute_name=statute_name, section=section)
            db.add(statute)
            await db.flush()
        
        case.statutes.append(statute)
        return statute
