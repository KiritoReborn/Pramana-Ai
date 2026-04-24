"""Text extraction from PDF documents using pdfplumber"""

import pdfplumber
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """Handles PDF text extraction with page preservation"""
    
    def extract_text(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text from PDF using pdfplumber with page preservation.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing:
                - pages: List of text content per page
                - page_metadata: List of metadata per page
                - success: Boolean indicating success
                - error: Error message if failed
                
        Validates: Requirements 1.1, 2.3, 2.4
        """
        try:
            pages_text = []
            pages_metadata = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        # Extract text from page
                        text = page.extract_text()
                        
                        if text is None:
                            text = ""
                            logger.warning(f"No text extracted from page {page_num}")
                        
                        pages_text.append(text)
                        
                        # Store page metadata
                        metadata = {
                            "page_number": page_num,
                            "width": page.width,
                            "height": page.height,
                            "has_text": bool(text.strip())
                        }
                        pages_metadata.append(metadata)
                        
                    except Exception as e:
                        logger.error(f"Error extracting text from page {page_num}: {str(e)}")
                        pages_text.append("")
                        pages_metadata.append({
                            "page_number": page_num,
                            "error": str(e),
                            "has_text": False
                        })
            
            return {
                "pages": pages_text,
                "page_metadata": pages_metadata,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {str(e)}")
            return {
                "pages": [],
                "page_metadata": [],
                "success": False,
                "error": f"PDF extraction failed: {str(e)}"
            }
