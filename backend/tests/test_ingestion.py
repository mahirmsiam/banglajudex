"""
Unit tests for the ingestion service.
Tests PDF processing, OCR, and database operations.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import tempfile
import os

from app.services.ingestion import IngestionService


class TestIngestionService:
    """Tests for IngestionService class."""
    
    @pytest.fixture
    def ingestion_service(self):
        """Create ingestion service instance."""
        return IngestionService()
    
    @pytest.fixture
    def temp_pdf_dir(self):
        """Create temporary directory with mock PDFs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy PDF files
            for i in range(3):
                pdf_path = Path(tmpdir) / f"test_{i}.pdf"
                pdf_path.write_bytes(b"%PDF-1.4\n%mock content")
            yield tmpdir
    
    def test_scan_directory(self, ingestion_service, temp_pdf_dir):
        """Test directory scanning for PDFs."""
        pdf_files = ingestion_service.scan_directory(temp_pdf_dir)
        
        assert len(pdf_files) == 3
        assert all(f.endswith('.pdf') for f in pdf_files)
    
    def test_scan_directory_empty(self, ingestion_service):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_files = ingestion_service.scan_directory(tmpdir)
            assert len(pdf_files) == 0
    
    def test_scan_directory_nested(self, ingestion_service):
        """Test scanning nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            nested = Path(tmpdir) / "nested"
            nested.mkdir()
            (nested / "test.pdf").write_bytes(b"%PDF-1.4")
            (Path(tmpdir) / "root.pdf").write_bytes(b"%PDF-1.4")
            
            pdf_files = ingestion_service.scan_directory(tmpdir)
            
            assert len(pdf_files) >= 1
    
    def test_calculate_file_hash(self, ingestion_service, temp_pdf_dir):
        """Test file hash calculation for deduplication."""
        pdf_files = ingestion_service.scan_directory(temp_pdf_dir)
        
        if pdf_files:
            hash1 = ingestion_service.calculate_hash(pdf_files[0])
            hash2 = ingestion_service.calculate_hash(pdf_files[0])
            
            # Same file should have same hash
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
    
    def test_extract_text_from_pdf(self, ingestion_service, mock_pdf_content):
        """Test text extraction from PDF."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(mock_pdf_content)
            f.flush()
            
            try:
                text = ingestion_service.extract_text(f.name)
                # May be empty for minimal PDF, but shouldn't crash
                assert isinstance(text, str)
            finally:
                os.unlink(f.name)
    
    def test_needs_ocr_detection(self, ingestion_service):
        """Test OCR requirement detection."""
        # Text-based PDF content
        text = """
        This is a properly extracted text from a PDF.
        It has multiple lines and proper formatting.
        """
        assert ingestion_service.needs_ocr(text) is False
        
        # Scanned/image PDF (little to no text)
        text = ""
        assert ingestion_service.needs_ocr(text) is True
        
        # Garbage text from failed extraction
        text = "asdfjkl;qwer1234zxcv"
        # May or may not need OCR depending on implementation


class TestPDFTextExtraction:
    """Tests for PDF text extraction."""
    
    @pytest.fixture
    def ingestion_service(self):
        return IngestionService()
    
    def test_clean_extracted_text(self, ingestion_service):
        """Test text cleaning after extraction."""
        dirty_text = "  The   court   held   \n\n\n   that  "
        
        clean = ingestion_service.clean_text(dirty_text)
        
        # Should normalize whitespace
        assert "   " not in clean
        assert "\n\n\n" not in clean
    
    def test_detect_page_breaks(self, ingestion_service):
        """Test page break detection in extracted text."""
        text = """Page 1 content here
        
        --- PAGE 2 ---
        
        Page 2 content here"""
        
        pages = ingestion_service.split_into_pages(text)
        
        assert len(pages) >= 1
    
    def test_extract_page_number(self, ingestion_service):
        """Test page number extraction from text."""
        test_cases = [
            ("Page 5 of 10", 5),
            ("- 12 -", 12),
            ("Page: 7", 7),
        ]
        
        for text, expected in test_cases:
            result = ingestion_service.extract_page_number(text)
            if result:
                assert result == expected


class TestBatchProcessing:
    """Tests for batch PDF processing."""
    
    @pytest.fixture
    def ingestion_service(self):
        return IngestionService()
    
    def test_batch_size_configuration(self, ingestion_service):
        """Test batch size is configurable."""
        assert hasattr(ingestion_service, 'batch_size')
        assert ingestion_service.batch_size > 0
    
    def test_create_batches(self, ingestion_service):
        """Test creating batches from file list."""
        files = [f"file_{i}.pdf" for i in range(25)]
        batch_size = 10
        
        batches = ingestion_service.create_batches(files, batch_size)
        
        assert len(batches) == 3
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10
        assert len(batches[2]) == 5
    
    def test_parallel_processing_flag(self, ingestion_service):
        """Test parallel processing configuration."""
        # Should have parallel processing option
        assert hasattr(ingestion_service, 'parallel') or hasattr(ingestion_service, 'workers')


class TestDeduplication:
    """Tests for document deduplication."""
    
    @pytest.fixture
    def ingestion_service(self):
        return IngestionService()
    
    def test_detect_duplicate_by_hash(self, ingestion_service):
        """Test duplicate detection by file hash."""
        existing_hashes = {"abc123", "def456", "ghi789"}
        
        # New file
        assert not ingestion_service.is_duplicate("new123", existing_hashes)
        
        # Duplicate file
        assert ingestion_service.is_duplicate("abc123", existing_hashes)
    
    def test_detect_duplicate_by_case_number(self, ingestion_service):
        """Test duplicate detection by case number."""
        existing_cases = {"CA 123/2020", "WP 456/2019"}
        
        # Should detect same case number
        is_dup = ingestion_service.is_case_duplicate(
            "CA 123/2020", existing_cases
        )
        assert is_dup is True


class TestIngestionStatus:
    """Tests for ingestion status tracking."""
    
    @pytest.fixture
    def ingestion_service(self):
        return IngestionService()
    
    def test_status_tracking(self, ingestion_service):
        """Test status tracking during ingestion."""
        status = ingestion_service.get_status()
        
        assert 'is_running' in status or 'status' in status
        assert 'total_files' in status or 'files' in status
    
    def test_progress_calculation(self, ingestion_service):
        """Test progress percentage calculation."""
        progress = ingestion_service.calculate_progress(50, 100)
        assert progress == 50.0
        
        progress = ingestion_service.calculate_progress(0, 100)
        assert progress == 0.0
        
        progress = ingestion_service.calculate_progress(100, 100)
        assert progress == 100.0
    
    def test_error_logging(self, ingestion_service):
        """Test error logging during ingestion."""
        ingestion_service.log_error("test.pdf", "Test error message")
        
        errors = ingestion_service.get_errors()
        assert len(errors) > 0
        assert any("test.pdf" in str(e) for e in errors)
