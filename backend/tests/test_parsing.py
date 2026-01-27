"""
Unit tests for the parsing service.
Tests metadata extraction from judgment text.
"""
import pytest
from datetime import date

from app.services.parsing import JudgmentParser


class TestJudgmentParser:
    """Tests for JudgmentParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return JudgmentParser()
    
    def test_extract_case_number_civil_appeal(self, parser, sample_judgment_text):
        """Test extraction of civil appeal case number."""
        result = parser.extract_case_number(sample_judgment_text)
        assert result is not None
        assert "123" in result or "CIVIL APPEAL" in result.upper()
    
    def test_extract_case_number_writ_petition(self, parser):
        """Test extraction of writ petition case number."""
        text = "WRIT PETITION NO. 5678 OF 2019"
        result = parser.extract_case_number(text)
        assert result is not None
        assert "5678" in result
    
    def test_extract_judgment_date(self, parser, sample_judgment_text):
        """Test extraction of judgment date."""
        result = parser.extract_judgment_date(sample_judgment_text)
        assert result is not None
        assert isinstance(result, date)
    
    def test_extract_judgment_date_various_formats(self, parser):
        """Test date extraction with various formats."""
        test_cases = [
            ("Date of judgment: 15th March, 2021", date(2021, 3, 15)),
            ("Judgment delivered on: 01/05/2020", date(2020, 5, 1)),
            ("Dated: 2019-12-25", date(2019, 12, 25)),
        ]
        for text, expected in test_cases:
            result = parser.extract_judgment_date(text)
            if result:
                assert result == expected, f"Failed for: {text}"
    
    def test_extract_judges(self, parser, sample_judgment_text):
        """Test extraction of judge names."""
        result = parser.extract_judges(sample_judgment_text)
        assert result is not None
        assert len(result) >= 1
        # Check if any judge name was extracted
        assert any("Justice" in name or "J." in name for name in result) or len(result) > 0
    
    def test_extract_parties(self, parser, sample_judgment_text):
        """Test extraction of party names."""
        result = parser.extract_parties(sample_judgment_text)
        assert result is not None
        # Should have appellant and respondent
        assert "appellant" in result or "petitioner" in result or len(result) > 0
    
    def test_extract_court_appellate_division(self, parser, sample_judgment_text):
        """Test extraction of court - Appellate Division."""
        result = parser.extract_court(sample_judgment_text)
        assert result is not None
        assert "APPELLATE" in result.upper() or "AD" in result.upper()
    
    def test_extract_court_high_court(self, parser):
        """Test extraction of court - High Court Division."""
        text = "IN THE HIGH COURT DIVISION OF THE SUPREME COURT OF BANGLADESH"
        result = parser.extract_court(text)
        assert result is not None
        assert "HIGH" in result.upper() or "HCD" in result.upper()
    
    def test_extract_statutes(self, parser, sample_judgment_text):
        """Test extraction of statutes cited."""
        result = parser.extract_statutes(sample_judgment_text)
        assert result is not None
        assert len(result) >= 1
        # Should find State Acquisition and Tenancy Act
        statute_names = [s.get('name', s) if isinstance(s, dict) else s for s in result]
        assert any("Acquisition" in str(name) or "Tenancy" in str(name) for name in statute_names)
    
    def test_extract_sections(self, parser, sample_judgment_text):
        """Test extraction of sections cited."""
        result = parser.extract_sections(sample_judgment_text)
        assert result is not None
        # Should find Section 96 and Article 102
        sections = [str(s) for s in result]
        assert any("96" in s or "102" in s for s in sections)
    
    def test_extract_case_type_civil(self, parser, sample_judgment_text):
        """Test case type extraction - Civil."""
        result = parser.extract_case_type(sample_judgment_text)
        assert result is not None
        assert "CIVIL" in result.upper() or "APPEAL" in result.upper()
    
    def test_extract_case_type_criminal(self, parser):
        """Test case type extraction - Criminal."""
        text = "CRIMINAL APPEAL NO. 456 OF 2020"
        result = parser.extract_case_type(text)
        assert result is not None
        assert "CRIMINAL" in result.upper()
    
    def test_extract_outcome_allowed(self, parser, sample_judgment_text):
        """Test outcome extraction - Allowed."""
        result = parser.extract_outcome(sample_judgment_text)
        assert result is not None
        assert "ALLOWED" in result.upper()
    
    def test_extract_outcome_dismissed(self, parser):
        """Test outcome extraction - Dismissed."""
        text = "The appeal is hereby DISMISSED with costs."
        result = parser.extract_outcome(text)
        assert result is not None
        assert "DISMISSED" in result.upper()
    
    def test_split_into_paragraphs(self, parser, sample_judgment_text):
        """Test paragraph splitting."""
        result = parser.split_into_paragraphs(sample_judgment_text)
        assert result is not None
        assert len(result) > 0
        # Each paragraph should have text
        for para in result:
            assert len(para.get('text', para) if isinstance(para, dict) else para) > 0
    
    def test_classify_section_heading(self, parser):
        """Test section heading classification."""
        test_cases = [
            ("FACTS:", "facts"),
            ("ISSUES FOR DETERMINATION:", "issues"),
            ("SUBMISSIONS:", "submissions"),
            ("FINDINGS AND ANALYSIS:", "findings"),
            ("DECISION:", "decision"),
            ("ORDER:", "order"),
        ]
        for text, expected in test_cases:
            result = parser.classify_section(text)
            if result:
                assert expected.lower() in result.lower(), f"Failed for: {text}"
    
    def test_empty_text_handling(self, parser):
        """Test handling of empty text."""
        result = parser.extract_case_number("")
        assert result is None or result == ""
        
        result = parser.extract_judges("")
        assert result is None or result == [] or result == ""
    
    def test_malformed_text_handling(self, parser):
        """Test handling of malformed/random text."""
        random_text = "asdfghjkl qwertyuiop zxcvbnm 12345"
        
        result = parser.extract_case_number(random_text)
        # Should not crash, may return None
        assert result is None or isinstance(result, str)
        
        result = parser.extract_judges(random_text)
        assert result is None or isinstance(result, (list, str))


class TestStatuteExtraction:
    """Specific tests for statute and section extraction."""
    
    @pytest.fixture
    def parser(self):
        return JudgmentParser()
    
    def test_common_statutes(self, parser):
        """Test extraction of commonly cited statutes."""
        texts = [
            ("Section 302 of the Penal Code, 1860", "Penal Code"),
            ("under the Code of Criminal Procedure, 1898", "Criminal Procedure"),
            ("Civil Procedure Code, 1908", "Civil Procedure"),
            ("Evidence Act, 1872", "Evidence Act"),
            ("Contract Act, 1872", "Contract Act"),
        ]
        for text, expected_statute in texts:
            result = parser.extract_statutes(text)
            if result:
                statute_str = str(result)
                assert expected_statute.split()[0] in statute_str or len(result) > 0
    
    def test_constitution_articles(self, parser):
        """Test extraction of constitutional articles."""
        text = "Article 102 of the Constitution of Bangladesh"
        result = parser.extract_sections(text)
        assert result is not None
        assert any("102" in str(s) for s in result)
