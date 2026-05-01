"""Tests for document processing pipeline"""

import pytest
from pathlib import Path
from src.processors.text_extractor import TextExtractor
from src.processors.table_extractor import TableExtractor
from src.processors.ocr_engine import OCREngine
from src.processors.document_processor import DocumentProcessor


class TestTextExtractor:
    """Test text extraction functionality"""
    
    def test_text_extractor_initialization(self):
        """Test that TextExtractor can be instantiated"""
        extractor = TextExtractor()
        assert extractor is not None
    
    def test_extract_text_returns_dict(self):
        """Test that extract_text returns expected structure"""
        extractor = TextExtractor()
        # Test with non-existent file to check error handling
        result = extractor.extract_text("nonexistent.pdf")
        
        assert isinstance(result, dict)
        assert "pages" in result
        assert "page_metadata" in result
        assert "success" in result
        assert "error" in result
        assert result["success"] is False  # Should fail for non-existent file


class TestTableExtractor:
    """Test table extraction functionality"""
    
    def test_table_extractor_initialization(self):
        """Test that TableExtractor can be instantiated"""
        extractor = TableExtractor()
        assert extractor is not None
    
    def test_extract_tables_returns_dict(self):
        """Test that extract_tables returns expected structure"""
        extractor = TableExtractor()
        # Test with non-existent file to check error handling
        result = extractor.extract_tables("nonexistent.pdf")
        
        assert isinstance(result, dict)
        assert "tables" in result
        assert "success" in result
        assert "error" in result
        assert "fallback_used" in result


class TestOCREngine:
    """Test OCR engine functionality"""
    
    def test_ocr_engine_initialization(self):
        """Test that OCREngine can be instantiated"""
        engine = OCREngine()
        assert engine is not None
        assert engine.confidence_threshold == 0.6
    
    def test_ocr_engine_custom_threshold(self):
        """Test OCREngine with custom threshold"""
        engine = OCREngine(confidence_threshold=0.8)
        assert engine.confidence_threshold == 0.8
    
    def test_process_image_returns_dict(self):
        """Test that process_image returns expected structure"""
        engine = OCREngine()
        # Test with non-existent file to check error handling
        result = engine.process_image("nonexistent.png")
        
        assert isinstance(result, dict)
        assert "pages" in result
        assert "page_metadata" in result
        assert "ocr_confidence" in result
        assert "success" in result
        assert "error" in result
        assert "needs_review" in result


class TestDocumentProcessor:
    """Test document processor orchestrator"""
    
    def test_document_processor_initialization(self):
        """Test that DocumentProcessor can be instantiated"""
        processor = DocumentProcessor()
        assert processor is not None
        assert processor.text_extractor is not None
        assert processor.ocr_engine is not None
    
    def test_detect_file_type_pdf(self):
        """Test file type detection for PDF"""
        processor = DocumentProcessor()
        assert processor.detect_file_type("document.pdf") == "pdf"
        assert processor.detect_file_type("document.PDF") == "pdf"
    
    def test_detect_file_type_images(self):
        """Test file type detection for images"""
        processor = DocumentProcessor()
        assert processor.detect_file_type("image.png") == "image"
        assert processor.detect_file_type("image.jpg") == "image"
        assert processor.detect_file_type("image.jpeg") == "image"
        assert processor.detect_file_type("image.PNG") == "image"
    
    def test_detect_file_type_unsupported(self):
        """Test file type detection for unsupported types"""
        processor = DocumentProcessor()
        assert processor.detect_file_type("document.docx") is None
        assert processor.detect_file_type("document.txt") is None
    
    def test_process_submission_empty_list(self):
        """Test processing empty submission"""
        processor = DocumentProcessor()
        result = processor.process_submission([], "bidder_001")
        assert isinstance(result, list)
        assert len(result) == 0
