"""Document processor orchestrator for routing to appropriate extraction methods"""

import os
from pathlib import Path
from typing import List, Optional
import logging
import uuid

from src.models.schemas import ExtractedDocument
from src.processors.text_extractor import TextExtractor
from src.processors.ocr_engine import OCREngine
from src.config import RetrievalConfig

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates document processing with file type detection and routing"""
    
    def __init__(self):
        """Initialize document processor with extractors"""
        self.text_extractor = TextExtractor()
        self.ocr_engine = OCREngine(confidence_threshold=RetrievalConfig.LOW_CONFIDENCE_THRESHOLD)
    
    def detect_file_type(self, file_path: str) -> Optional[str]:
        """
        Detect file type from extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            File type: 'pdf', 'image', or None if unsupported
            
        Validates: Requirements 2.1
        """
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.png', '.jpg', '.jpeg']:
            return 'image'
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return None
    
    def is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        Heuristic to detect if PDF is scanned (image-based).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF appears to be scanned, False otherwise
        """
        # Try text extraction first
        result = self.text_extractor.extract_text(pdf_path)
        
        if not result["success"]:
            return True  # Assume scanned if extraction fails
        
        # Check if extracted text is minimal (likely scanned)
        total_text = " ".join(result["pages"])
        word_count = len(total_text.split())
        
        # If very few words extracted, likely scanned
        if word_count < 50:
            logger.info(f"PDF appears to be scanned (only {word_count} words extracted)")
            return True
        
        return False
    
    def process_document(
        self, 
        file_path: str, 
        bidder_id: str
    ) -> Optional[ExtractedDocument]:
        """
        Process a single document with appropriate extraction method.
        
        Args:
            file_path: Path to document file
            bidder_id: Identifier for the bidder
            
        Returns:
            ExtractedDocument object or None if processing failed
            
        Validates: Requirements 2.1, 2.5, 2.7
        """
        # Detect file type
        file_type = self.detect_file_type(file_path)
        
        if file_type is None:
            logger.error(f"Unsupported file type for {file_path}")
            return None
        
        file_name = Path(file_path).name
        document_id = str(uuid.uuid4())
        
        # Route to appropriate extraction method
        if file_type == 'image':
            # Use OCR for images
            result = self.ocr_engine.process_image(file_path)
            extraction_method = "tesseract"
            
        elif file_type == 'pdf':
            # Check if PDF is scanned
            if self.is_scanned_pdf(file_path):
                # Use OCR for scanned PDFs
                logger.info(f"Using OCR for scanned PDF: {file_name}")
                result = self.ocr_engine.process_scanned_pdf(file_path)
                extraction_method = "tesseract"
            else:
                # Use pdfplumber for native PDFs
                logger.info(f"Using pdfplumber for native PDF: {file_name}")
                result = self.text_extractor.extract_text(file_path)
                extraction_method = "pdfplumber"
        
        # Check if extraction was successful
        if not result["success"]:
            logger.error(f"Failed to process document {file_name}: {result['error']}")
            return None
        
        # Create ExtractedDocument object
        try:
            extracted_doc = ExtractedDocument(
                document_id=document_id,
                bidder_id=bidder_id,
                file_name=file_name,
                pages=result["pages"],
                page_metadata=result["page_metadata"],
                ocr_confidence=result.get("ocr_confidence"),
                extraction_method=extraction_method
            )
            
            logger.info(f"Successfully processed document {file_name} for bidder {bidder_id}")
            return extracted_doc
            
        except Exception as e:
            logger.error(f"Failed to create ExtractedDocument for {file_name}: {str(e)}")
            return None
    
    def process_submission(
        self, 
        file_paths: List[str], 
        bidder_id: str
    ) -> List[ExtractedDocument]:
        """
        Process multiple documents for a single bidder.
        
        Args:
            file_paths: List of paths to document files
            bidder_id: Identifier for the bidder
            
        Returns:
            List of ExtractedDocument objects (may be empty if all failed)
            
        Validates: Requirements 2.5, 2.7
        """
        extracted_documents = []
        
        for file_path in file_paths:
            doc = self.process_document(file_path, bidder_id)
            if doc is not None:
                extracted_documents.append(doc)
        
        logger.info(
            f"Processed {len(extracted_documents)}/{len(file_paths)} documents "
            f"for bidder {bidder_id}"
        )
        
        return extracted_documents
