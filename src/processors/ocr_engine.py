"""OCR processing for scanned PDFs and images using Tesseract"""

import pytesseract
from PIL import Image
from typing import List, Dict, Optional
import logging
import os

# Try to import pdf2image, but make it optional
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logging.warning("pdf2image not available. Scanned PDF processing will be limited.")

logger = logging.getLogger(__name__)


class OCREngine:
    """Handles OCR processing for scanned documents and images"""
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize OCR engine.
        
        Args:
            confidence_threshold: Minimum confidence for automatic acceptance (default 0.6)
        """
        self.confidence_threshold = confidence_threshold
    
    def process_image(self, image_path: str) -> Dict[str, any]:
        """
        Process a single image file with OCR.
        
        Args:
            image_path: Path to image file (PNG, JPG, JPEG)
            
        Returns:
            Dictionary containing:
                - pages: List with single page text
                - page_metadata: List with single page metadata
                - ocr_confidence: Average confidence score
                - success: Boolean indicating success
                - error: Error message if failed
                - needs_review: Boolean indicating if manual review needed
                
        Validates: Requirements 2.2, 2.6
        """
        try:
            # Open and process image
            image = Image.open(image_path)
            
            # Get OCR data with confidence scores
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Calculate confidence score
            confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            # Flag for manual review if confidence is low
            needs_review = avg_confidence < self.confidence_threshold
            
            if needs_review:
                logger.warning(f"Low OCR confidence ({avg_confidence:.2f}) for {image_path}")
            
            return {
                "pages": [text],
                "page_metadata": [{
                    "page_number": 1,
                    "ocr_confidence": avg_confidence,
                    "needs_review": needs_review,
                    "word_count": len(text.split())
                }],
                "ocr_confidence": avg_confidence,
                "success": True,
                "error": None,
                "needs_review": needs_review
            }
            
        except Exception as e:
            logger.error(f"OCR failed for image {image_path}: {str(e)}")
            return {
                "pages": [],
                "page_metadata": [],
                "ocr_confidence": 0.0,
                "success": False,
                "error": f"OCR processing failed: {str(e)}",
                "needs_review": True
            }
    
    def process_scanned_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Process a scanned PDF with OCR.
        
        Args:
            pdf_path: Path to scanned PDF file
            
        Returns:
            Dictionary containing:
                - pages: List of text content per page
                - page_metadata: List of metadata per page
                - ocr_confidence: Average confidence score across all pages
                - success: Boolean indicating success
                - error: Error message if failed
                - needs_review: Boolean indicating if any page needs manual review
                
        Validates: Requirements 2.2, 2.6
        """
        if not PDF2IMAGE_AVAILABLE:
            logger.error("pdf2image library not available for scanned PDF processing")
            return {
                "pages": [],
                "page_metadata": [],
                "ocr_confidence": 0.0,
                "success": False,
                "error": "pdf2image library not installed",
                "needs_review": True
            }
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path)
            
            pages_text = []
            pages_metadata = []
            all_confidences = []
            any_needs_review = False
            
            for page_num, image in enumerate(images, start=1):
                try:
                    # Get OCR data with confidence scores
                    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                    
                    # Extract text
                    text = pytesseract.image_to_string(image)
                    pages_text.append(text)
                    
                    # Calculate confidence score for this page
                    confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
                    page_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
                    all_confidences.append(page_confidence)
                    
                    # Flag page for manual review if confidence is low
                    needs_review = page_confidence < self.confidence_threshold
                    if needs_review:
                        any_needs_review = True
                        logger.warning(f"Low OCR confidence ({page_confidence:.2f}) on page {page_num}")
                    
                    pages_metadata.append({
                        "page_number": page_num,
                        "ocr_confidence": page_confidence,
                        "needs_review": needs_review,
                        "word_count": len(text.split())
                    })
                    
                except Exception as e:
                    logger.error(f"OCR failed for page {page_num}: {str(e)}")
                    pages_text.append("")
                    pages_metadata.append({
                        "page_number": page_num,
                        "ocr_confidence": 0.0,
                        "needs_review": True,
                        "error": str(e)
                    })
                    any_needs_review = True
            
            # Calculate average confidence across all pages
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            return {
                "pages": pages_text,
                "page_metadata": pages_metadata,
                "ocr_confidence": avg_confidence,
                "success": True,
                "error": None,
                "needs_review": any_needs_review
            }
            
        except Exception as e:
            logger.error(f"OCR failed for scanned PDF {pdf_path}: {str(e)}")
            return {
                "pages": [],
                "page_metadata": [],
                "ocr_confidence": 0.0,
                "success": False,
                "error": f"Scanned PDF OCR failed: {str(e)}",
                "needs_review": True
            }
