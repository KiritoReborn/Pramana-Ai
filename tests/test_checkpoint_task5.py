"""
Checkpoint Task 5: End-to-end document processing verification

This test suite verifies that all document processing components work together correctly:
- Tender PDF upload and criteria extraction
- Bidder document upload with various formats
- Pydantic validation catches malformed outputs
- All tests pass

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 9.1, 9.2, 9.3, 9.4**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.processors.tender_processor import TenderProcessor
from src.processors.document_processor import DocumentProcessor
from src.models.schemas import (
    EligibilityCriterion,
    CriteriaList,
    ExtractedDocument
)
from pydantic import ValidationError


class TestTenderProcessingEndToEnd:
    """Test tender PDF upload and criteria extraction"""
    
    def test_tender_processor_initialization(self):
        """Test that TenderProcessor initializes all components"""
        processor = TenderProcessor()
        
        assert processor is not None
        assert processor.text_extractor is not None
        assert processor.table_extractor is not None
        assert processor.llm_extractor is not None
    
    def test_tender_processor_handles_missing_file(self):
        """Test that tender processor handles missing files gracefully"""
        processor = TenderProcessor()
        result = processor.process_tender("nonexistent_tender.pdf")
        
        assert result["success"] is False
        assert result["needs_review"] is True
        assert "not found" in result["error"].lower()
        assert result["criteria"] == []
    
    @patch('src.processors.text_extractor.TextExtractor.extract_text')
    @patch('src.processors.table_extractor.TableExtractor.extract_tables')
    def test_extract_text_and_tables_integration(self, mock_tables, mock_text):
        """Test that text and table extraction work together"""
        # Mock text extraction
        mock_text.return_value = {
            "pages": ["Page 1 content", "Page 2 content"],
            "page_metadata": [
                {"page_number": 1, "has_text": True},
                {"page_number": 2, "has_text": True}
            ],
            "success": True,
            "error": None
        }
        
        # Mock table extraction
        mock_tables.return_value = {
            "tables": [
                {
                    "table_number": 1,
                    "page": 1,
                    "data": [["Header1", "Header2"], ["Value1", "Value2"]]
                }
            ],
            "success": True,
            "error": None,
            "fallback_used": False
        }
        
        processor = TenderProcessor()
        
        # Create a temporary file to pass validation
        test_file = Path("test_tender.pdf")
        test_file.touch()
        
        try:
            result = processor.extract_text_and_tables(str(test_file))
            
            assert result["success"] is True
            assert len(result["text_pages"]) == 2
            assert len(result["tables"]) == 1
            assert "Page 1 content" in result["combined_text"]
            assert "Page 2 content" in result["combined_text"]
            assert "Table 1" in result["combined_text"]
        finally:
            test_file.unlink()
    
    @patch('src.processors.text_extractor.TextExtractor.extract_text')
    def test_extract_text_and_tables_handles_text_failure(self, mock_text):
        """Test handling of text extraction failure"""
        mock_text.return_value = {
            "pages": [],
            "page_metadata": [],
            "success": False,
            "error": "PDF is corrupted"
        }
        
        processor = TenderProcessor()
        
        test_file = Path("test_tender.pdf")
        test_file.touch()
        
        try:
            result = processor.extract_text_and_tables(str(test_file))
            
            assert result["success"] is False
            assert "corrupted" in result["error"].lower()
        finally:
            test_file.unlink()
    
    def test_validate_criteria_with_valid_criteria(self):
        """Test criteria validation with valid criteria"""
        processor = TenderProcessor()
        
        criteria = [
            EligibilityCriterion(
                id="crit-001",
                category="Financial",
                priority="Mandatory",
                description="Minimum annual turnover of $1M",
                threshold_value="1000000",
                threshold_unit="USD",
                source_page=1,
                original_text="The bidder must have minimum annual turnover of $1M"
            ),
            EligibilityCriterion(
                id="crit-002",
                category="Technical",
                priority="Optional",
                description="ISO 9001 certification",
                source_page=2,
                original_text="ISO 9001 certification is preferred"
            )
        ]
        
        result = processor.validate_criteria(criteria)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
    
    def test_validate_criteria_with_invalid_category(self):
        """Test criteria validation catches invalid category"""
        processor = TenderProcessor()
        
        criteria = [
            EligibilityCriterion(
                id="crit-001",
                category="Financial",  # This will be changed after creation
                priority="Mandatory",
                description="Test criterion",
                source_page=1,
                original_text="Test text"
            )
        ]
        
        # Manually set invalid category (bypassing Pydantic validation for testing)
        criteria[0].__dict__["category"] = "InvalidCategory"
        
        result = processor.validate_criteria(criteria)
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert "Invalid category" in result["issues"][0]
    
    def test_validate_criteria_with_invalid_priority(self):
        """Test criteria validation catches invalid priority"""
        processor = TenderProcessor()
        
        criteria = [
            EligibilityCriterion(
                id="crit-001",
                category="Financial",
                priority="Mandatory",  # This will be changed after creation
                description="Test criterion",
                source_page=1,
                original_text="Test text"
            )
        ]
        
        # Manually set invalid priority
        criteria[0].__dict__["priority"] = "InvalidPriority"
        
        result = processor.validate_criteria(criteria)
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert "Invalid priority" in result["issues"][0]
    
    def test_validate_criteria_with_invalid_source_page(self):
        """Test criteria validation catches invalid source page"""
        processor = TenderProcessor()
        
        criteria = [
            EligibilityCriterion(
                id="crit-001",
                category="Financial",
                priority="Mandatory",
                description="Test criterion",
                source_page=1,  # This will be changed after creation
                original_text="Test text"
            )
        ]
        
        # Manually set invalid source page
        criteria[0].__dict__["source_page"] = 0
        
        result = processor.validate_criteria(criteria)
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert "Invalid source_page" in result["issues"][0]


class TestBidderDocumentProcessingEndToEnd:
    """Test bidder document upload with various formats"""
    
    def test_document_processor_initialization(self):
        """Test that DocumentProcessor initializes all components"""
        processor = DocumentProcessor()
        
        assert processor is not None
        assert processor.text_extractor is not None
        assert processor.ocr_engine is not None
    
    def test_file_type_detection_for_all_formats(self):
        """Test file type detection for PDF and image formats"""
        processor = DocumentProcessor()
        
        # Test PDF detection
        assert processor.detect_file_type("document.pdf") == "pdf"
        assert processor.detect_file_type("DOCUMENT.PDF") == "pdf"
        
        # Test image detection
        assert processor.detect_file_type("scan.png") == "image"
        assert processor.detect_file_type("scan.jpg") == "image"
        assert processor.detect_file_type("scan.jpeg") == "image"
        assert processor.detect_file_type("SCAN.PNG") == "image"
        
        # Test unsupported formats
        assert processor.detect_file_type("document.docx") is None
        assert processor.detect_file_type("document.txt") is None
    
    @patch('src.processors.document_processor.DocumentProcessor.is_scanned_pdf')
    @patch('src.processors.text_extractor.TextExtractor.extract_text')
    def test_process_document_pdf_format(self, mock_extract, mock_is_scanned):
        """Test processing PDF document"""
        # Mock is_scanned_pdf to return False (native PDF)
        mock_is_scanned.return_value = False
        
        mock_extract.return_value = {
            "pages": ["PDF page 1", "PDF page 2"],
            "page_metadata": [
                {"page_number": 1, "has_text": True},
                {"page_number": 2, "has_text": True}
            ],
            "success": True,
            "error": None
        }
        
        processor = DocumentProcessor()
        
        test_file = Path("test_bidder.pdf")
        test_file.touch()
        
        try:
            result = processor.process_document(str(test_file), "bidder_001")
            
            assert result is not None
            assert result.bidder_id == "bidder_001"
            assert result.extraction_method == "pdfplumber"
            assert len(result.pages) == 2
            assert result.ocr_confidence is None
        finally:
            test_file.unlink()
    
    @patch('src.processors.ocr_engine.OCREngine.process_image')
    def test_process_document_image_format(self, mock_ocr):
        """Test processing image document with OCR"""
        mock_ocr.return_value = {
            "pages": ["OCR extracted text"],
            "page_metadata": [
                {"page_number": 1, "ocr_confidence": 0.85, "needs_review": False}
            ],
            "ocr_confidence": 0.85,
            "success": True,
            "error": None,
            "needs_review": False
        }
        
        processor = DocumentProcessor()
        
        test_file = Path("test_scan.png")
        test_file.touch()
        
        try:
            result = processor.process_document(str(test_file), "bidder_002")
            
            assert result is not None
            assert result.bidder_id == "bidder_002"
            assert result.extraction_method == "tesseract"
            assert result.ocr_confidence == 0.85
            assert len(result.pages) == 1
        finally:
            test_file.unlink()
    
    @patch('src.processors.ocr_engine.OCREngine.process_image')
    def test_process_document_low_ocr_confidence(self, mock_ocr):
        """Test that low OCR confidence is flagged"""
        mock_ocr.return_value = {
            "pages": ["Low quality OCR text"],
            "page_metadata": [
                {"page_number": 1, "ocr_confidence": 0.5, "needs_review": True}
            ],
            "ocr_confidence": 0.5,
            "success": True,
            "error": None,
            "needs_review": True
        }
        
        processor = DocumentProcessor()
        
        test_file = Path("test_low_quality.png")
        test_file.touch()
        
        try:
            result = processor.process_document(str(test_file), "bidder_003")
            
            assert result is not None
            assert result.ocr_confidence == 0.5
            # Check that low confidence is flagged in metadata
            assert result.page_metadata[0]["needs_review"] is True
        finally:
            test_file.unlink()
    
    def test_process_submission_multiple_documents(self):
        """Test processing multiple documents for single bidder"""
        processor = DocumentProcessor()
        
        # Test with empty list
        result = processor.process_submission([], "bidder_001")
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('src.processors.document_processor.DocumentProcessor.is_scanned_pdf')
    @patch('src.processors.text_extractor.TextExtractor.extract_text')
    @patch('src.processors.ocr_engine.OCREngine.process_image')
    def test_process_submission_mixed_formats(self, mock_ocr, mock_pdf, mock_is_scanned):
        """Test processing submission with mixed PDF and image files"""
        # Mock is_scanned_pdf to return False (native PDF)
        mock_is_scanned.return_value = False
        
        mock_pdf.return_value = {
            "pages": ["PDF content"],
            "page_metadata": [{"page_number": 1, "has_text": True}],
            "success": True,
            "error": None
        }
        
        mock_ocr.return_value = {
            "pages": ["OCR content"],
            "page_metadata": [{"page_number": 1, "ocr_confidence": 0.9, "needs_review": False}],
            "ocr_confidence": 0.9,
            "success": True,
            "error": None,
            "needs_review": False
        }
        
        processor = DocumentProcessor()
        
        # Create test files
        pdf_file = Path("test1.pdf")
        img_file = Path("test2.png")
        pdf_file.touch()
        img_file.touch()
        
        try:
            result = processor.process_submission(
                [str(pdf_file), str(img_file)],
                "bidder_004"
            )
            
            assert len(result) == 2
            assert all(doc.bidder_id == "bidder_004" for doc in result)
            
            # Check that different extraction methods were used
            extraction_methods = {doc.extraction_method for doc in result}
            assert "pdfplumber" in extraction_methods
            assert "tesseract" in extraction_methods
        finally:
            pdf_file.unlink()
            img_file.unlink()


class TestPydanticValidationIntegration:
    """Test that Pydantic validation catches malformed outputs"""
    
    def test_eligibility_criterion_requires_all_fields(self):
        """Test that EligibilityCriterion requires all mandatory fields"""
        with pytest.raises(ValidationError):
            EligibilityCriterion()
    
    def test_eligibility_criterion_validates_category(self):
        """Test that invalid category raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            EligibilityCriterion(
                id="test-001",
                category="InvalidCategory",  # Invalid
                priority="Mandatory",
                description="Test",
                source_page=1,
                original_text="Test"
            )
        
        assert "category" in str(exc_info.value).lower()
    
    def test_eligibility_criterion_validates_priority(self):
        """Test that invalid priority raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            EligibilityCriterion(
                id="test-001",
                category="Financial",
                priority="InvalidPriority",  # Invalid
                description="Test",
                source_page=1,
                original_text="Test"
            )
        
        assert "priority" in str(exc_info.value).lower()
    
    def test_extracted_document_requires_all_fields(self):
        """Test that ExtractedDocument requires all mandatory fields"""
        with pytest.raises(ValidationError):
            ExtractedDocument()
    
    def test_extracted_document_validates_extraction_method(self):
        """Test that invalid extraction method raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            ExtractedDocument(
                document_id="doc-001",
                bidder_id="bidder-001",
                file_name="test.pdf",
                pages=["Page 1"],
                page_metadata=[{"page_number": 1}],
                extraction_method="invalid_method"  # Invalid
            )
        
        assert "extraction_method" in str(exc_info.value).lower()
    
    def test_criteria_list_schema_validation(self):
        """Test that CriteriaList validates correctly"""
        # Valid criteria list
        criteria_list = CriteriaList(
            criteria=[
                EligibilityCriterion(
                    id="crit-001",
                    category="Financial",
                    priority="Mandatory",
                    description="Test criterion",
                    source_page=1,
                    original_text="Test text"
                )
            ],
            extraction_failed=False
        )
        
        assert len(criteria_list.criteria) == 1
        assert criteria_list.extraction_failed is False
    
    def test_criteria_list_handles_extraction_failure(self):
        """Test that CriteriaList can flag extraction failures"""
        criteria_list = CriteriaList(
            criteria=[],
            extraction_failed=True,
            failure_reason="LLM timeout"
        )
        
        assert criteria_list.extraction_failed is True
        assert criteria_list.failure_reason == "LLM timeout"
        assert len(criteria_list.criteria) == 0
    
    def test_pydantic_validation_prevents_invalid_data_propagation(self):
        """Test that Pydantic validation prevents invalid data from reaching UI"""
        # This test verifies that malformed data cannot be created
        
        # Test 1: Invalid confidence score
        from src.models.schemas import FinancialEvidence
        
        with pytest.raises(ValidationError):
            FinancialEvidence(
                value=1000.0,
                currency="USD",
                context="Test",
                source_page=1,
                confidence=1.5  # Invalid: > 1.0
            )
        
        with pytest.raises(ValidationError):
            FinancialEvidence(
                value=1000.0,
                currency="USD",
                context="Test",
                source_page=1,
                confidence=-0.1  # Invalid: < 0.0
            )
        
        # Test 2: Valid confidence score
        evidence = FinancialEvidence(
            value=1000.0,
            currency="USD",
            context="Test",
            source_page=1,
            confidence=0.85  # Valid
        )
        
        assert 0.0 <= evidence.confidence <= 1.0


class TestEndToEndIntegration:
    """Test complete end-to-end integration"""
    
    def test_all_components_can_be_initialized(self):
        """Test that all document processing components can be initialized together"""
        tender_processor = TenderProcessor()
        document_processor = DocumentProcessor()
        
        assert tender_processor is not None
        assert document_processor is not None
        
        # Verify all sub-components are initialized
        assert tender_processor.text_extractor is not None
        assert tender_processor.table_extractor is not None
        assert tender_processor.llm_extractor is not None
        
        assert document_processor.text_extractor is not None
        assert document_processor.ocr_engine is not None
    
    def test_pydantic_schemas_are_compatible_across_components(self):
        """Test that Pydantic schemas work consistently across all components"""
        # Create a criterion
        criterion = EligibilityCriterion(
            id="test-001",
            category="Financial",
            priority="Mandatory",
            description="Test criterion",
            source_page=1,
            original_text="Test text"
        )
        
        # Create a document
        document = ExtractedDocument(
            document_id="doc-001",
            bidder_id="bidder-001",
            file_name="test.pdf",
            pages=["Page 1"],
            page_metadata=[{"page_number": 1}],
            extraction_method="pdfplumber"
        )
        
        # Verify they can be serialized and deserialized
        criterion_dict = criterion.model_dump()
        document_dict = document.model_dump()
        
        # Recreate from dict
        criterion_restored = EligibilityCriterion(**criterion_dict)
        document_restored = ExtractedDocument(**document_dict)
        
        assert criterion_restored.id == criterion.id
        assert document_restored.document_id == document.document_id
    
    @patch('src.processors.text_extractor.TextExtractor.extract_text')
    @patch('src.processors.table_extractor.TableExtractor.extract_tables')
    def test_error_handling_propagates_correctly(self, mock_tables, mock_text):
        """Test that errors are handled gracefully throughout the pipeline"""
        # Simulate text extraction failure
        mock_text.return_value = {
            "pages": [],
            "page_metadata": [],
            "success": False,
            "error": "Corrupted PDF file"
        }
        
        processor = TenderProcessor()
        
        test_file = Path("test_corrupted.pdf")
        test_file.touch()
        
        try:
            result = processor.process_tender(str(test_file))
            
            # Verify error is handled gracefully
            assert result["success"] is False
            assert result["needs_review"] is True
            assert "error" in result
            assert result["error"] is not None
            assert len(result["criteria"]) == 0
        finally:
            test_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
