"""Integration tests for document processing pipeline"""

import pytest
from src.processors.document_processor import DocumentProcessor
from src.models.schemas import ExtractedDocument


class TestDocumentProcessingIntegration:
    """Integration tests for the complete document processing pipeline"""
    
    def test_document_processor_components_integration(self):
        """Test that all components work together"""
        processor = DocumentProcessor()
        
        # Verify all components are initialized
        assert processor.text_extractor is not None
        assert processor.ocr_engine is not None
        
        # Verify OCR engine has correct threshold from config
        assert processor.ocr_engine.confidence_threshold == 0.7
    
    def test_file_type_routing(self):
        """Test that file types are correctly routed"""
        processor = DocumentProcessor()
        
        # Test PDF detection
        assert processor.detect_file_type("test.pdf") == "pdf"
        
        # Test image detection
        assert processor.detect_file_type("test.png") == "image"
        assert processor.detect_file_type("test.jpg") == "image"
        assert processor.detect_file_type("test.jpeg") == "image"
        
        # Test unsupported types
        assert processor.detect_file_type("test.docx") is None
        assert processor.detect_file_type("test.txt") is None
    
    def test_process_document_with_invalid_file(self):
        """Test processing with invalid file returns None"""
        processor = DocumentProcessor()
        result = processor.process_document("nonexistent.pdf", "bidder_001")
        
        # Should return None for failed processing
        assert result is None
    
    def test_process_submission_with_invalid_files(self):
        """Test processing submission with invalid files"""
        processor = DocumentProcessor()
        
        # Process multiple non-existent files
        results = processor.process_submission(
            ["file1.pdf", "file2.pdf", "file3.png"],
            "bidder_001"
        )
        
        # Should return empty list since all files are invalid
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_extracted_document_schema_compatibility(self):
        """Test that ExtractedDocument schema is compatible with processor output"""
        # Create a sample ExtractedDocument to verify schema
        doc = ExtractedDocument(
            document_id="test-123",
            bidder_id="bidder-001",
            file_name="test.pdf",
            pages=["Page 1 text", "Page 2 text"],
            page_metadata=[
                {"page_number": 1, "has_text": True},
                {"page_number": 2, "has_text": True}
            ],
            ocr_confidence=None,
            extraction_method="pdfplumber"
        )
        
        assert doc.document_id == "test-123"
        assert doc.bidder_id == "bidder-001"
        assert doc.extraction_method == "pdfplumber"
        assert len(doc.pages) == 2
    
    def test_extracted_document_with_ocr(self):
        """Test ExtractedDocument schema with OCR data"""
        doc = ExtractedDocument(
            document_id="test-456",
            bidder_id="bidder-002",
            file_name="scanned.pdf",
            pages=["OCR extracted text"],
            page_metadata=[
                {"page_number": 1, "ocr_confidence": 0.85, "needs_review": False}
            ],
            ocr_confidence=0.85,
            extraction_method="tesseract"
        )
        
        assert doc.ocr_confidence == 0.85
        assert doc.extraction_method == "tesseract"
        assert doc.page_metadata[0]["needs_review"] is False
