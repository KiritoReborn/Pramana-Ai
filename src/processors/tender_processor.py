"""Tender document processor for extracting eligibility criteria"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

from src.processors.text_extractor import TextExtractor
from src.processors.table_extractor import TableExtractor
from src.engines.llm_extractor import LLMExtractor
from src.engines.prompts import CRITERIA_EXTRACTION_PROMPT
from src.models.schemas import EligibilityCriterion, CriteriaList

logger = logging.getLogger(__name__)


class TenderProcessor:
    """
    Orchestrates tender document processing and criteria extraction.
    
    This class handles the complete workflow of processing tender PDFs:
    1. Extract text and tables from PDF
    2. Use LLM to extract structured eligibility criteria
    3. Validate extracted criteria
    4. Flag extraction failures for manual review
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
    """
    
    def __init__(self):
        """Initialize tender processor with required extractors"""
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor()
        self.llm_extractor = LLMExtractor()
        logger.info("Initialized TenderProcessor")
    
    def process_tender(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract eligibility criteria from tender PDF.
        
        This method orchestrates the complete tender processing workflow:
        - Extracts text and tables from the PDF
        - Uses LLM to identify and structure eligibility criteria
        - Validates criteria categories and priorities
        - Flags extraction failures for manual review
        
        Args:
            pdf_path: Path to tender PDF file
            
        Returns:
            Dictionary containing:
                - criteria: List of EligibilityCriterion objects
                - raw_content: Extracted text and tables
                - success: Boolean indicating success
                - needs_review: Boolean indicating if manual review needed
                - error: Error message if failed
                
        Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
        """
        logger.info(f"Processing tender document: {pdf_path}")
        
        # Validate file exists
        if not Path(pdf_path).exists():
            error_msg = f"Tender file not found: {pdf_path}"
            logger.error(error_msg)
            return {
                "criteria": [],
                "raw_content": None,
                "success": False,
                "needs_review": True,
                "error": error_msg
            }
        
        # Step 1: Extract text and tables
        raw_content = self.extract_text_and_tables(pdf_path)
        
        if not raw_content["success"]:
            logger.error(f"Failed to extract content from tender: {raw_content['error']}")
            return {
                "criteria": [],
                "raw_content": raw_content,
                "success": False,
                "needs_review": True,
                "error": raw_content["error"]
            }
        
        # Step 2: Extract criteria using LLM
        criteria_result = self.extract_criteria(raw_content)
        
        if not criteria_result["success"]:
            logger.error(f"Failed to extract criteria: {criteria_result['error']}")
            return {
                "criteria": [],
                "raw_content": raw_content,
                "success": False,
                "needs_review": True,
                "error": criteria_result["error"]
            }
        
        # Step 3: Validate extracted criteria
        validation_result = self.validate_criteria(criteria_result["criteria"])
        
        if not validation_result["valid"]:
            logger.warning(f"Criteria validation issues: {validation_result['issues']}")
        
        logger.info(f"Successfully processed tender with {len(criteria_result['criteria'])} criteria")
        
        return {
            "criteria": criteria_result["criteria"],
            "raw_content": raw_content,
            "success": True,
            "needs_review": criteria_result["needs_review"] or not validation_result["valid"],
            "validation_issues": validation_result.get("issues", []),
            "error": None
        }
    
    def extract_text_and_tables(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract raw content using pdfplumber and camelot.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing:
                - text_pages: List of text content per page
                - page_metadata: List of metadata per page
                - tables: List of extracted tables
                - combined_text: All text combined for LLM processing
                - success: Boolean indicating success
                - error: Error message if failed
                
        Validates: Requirements 1.1, 1.2
        """
        logger.info(f"Extracting text and tables from: {pdf_path}")
        
        # Extract text
        text_result = self.text_extractor.extract_text(pdf_path)
        
        if not text_result["success"]:
            return {
                "text_pages": [],
                "page_metadata": [],
                "tables": [],
                "combined_text": "",
                "success": False,
                "error": text_result["error"]
            }
        
        # Extract tables
        table_result = self.table_extractor.extract_tables(pdf_path)
        
        # Combine text from all pages
        combined_text = "\n\n".join([
            f"--- Page {i+1} ---\n{page_text}"
            for i, page_text in enumerate(text_result["pages"])
            if page_text.strip()
        ])
        
        # Add table information to combined text
        if table_result["success"] and table_result["tables"]:
            table_text = "\n\n--- Tables ---\n"
            for table in table_result["tables"]:
                table_text += f"\nTable {table['table_number']} (Page {table['page']}):\n"
                # Convert table data to text representation
                for row in table["data"]:
                    table_text += " | ".join(str(cell) for cell in row) + "\n"
            combined_text += table_text
        
        logger.info(f"Extracted {len(text_result['pages'])} pages and {len(table_result.get('tables', []))} tables")
        
        return {
            "text_pages": text_result["pages"],
            "page_metadata": text_result["page_metadata"],
            "tables": table_result.get("tables", []),
            "combined_text": combined_text,
            "success": True,
            "error": None
        }
    
    def extract_criteria(self, raw_content: Dict[str, any]) -> Dict[str, any]:
        """
        Use LLM to extract structured criteria from raw content.
        
        Args:
            raw_content: Dictionary containing extracted text and tables
            
        Returns:
            Dictionary containing:
                - criteria: List of EligibilityCriterion objects
                - success: Boolean indicating success
                - needs_review: Boolean indicating if manual review needed
                - error: Error message if failed
                
        Validates: Requirements 1.3, 1.4, 1.5, 1.6, 1.7
        """
        logger.info("Extracting criteria using LLM")
        
        combined_text = raw_content.get("combined_text", "")
        
        if not combined_text.strip():
            error_msg = "No text content available for criteria extraction"
            logger.error(error_msg)
            return {
                "criteria": [],
                "success": False,
                "needs_review": True,
                "error": error_msg
            }
        
        try:
            # Use LLM extractor with Pydantic validation
            criteria_list = self.llm_extractor.extract_with_validation(
                text=combined_text,
                schema=CriteriaList,
                prompt_template=CRITERIA_EXTRACTION_PROMPT,
                max_retries=3
            )
            
            # Check if extraction failed
            if criteria_list.extraction_failed:
                logger.warning(f"LLM flagged extraction failure: {criteria_list.failure_reason}")
                return {
                    "criteria": criteria_list.criteria,
                    "success": True,
                    "needs_review": True,
                    "error": criteria_list.failure_reason
                }
            
            # Check if any criteria were extracted
            if not criteria_list.criteria:
                logger.warning("No criteria extracted from tender document")
                return {
                    "criteria": [],
                    "success": True,
                    "needs_review": True,
                    "error": "No eligibility criteria found in document"
                }
            
            logger.info(f"Successfully extracted {len(criteria_list.criteria)} criteria")
            
            return {
                "criteria": criteria_list.criteria,
                "success": True,
                "needs_review": False,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Unexpected error during criteria extraction: {str(e)}"
            logger.error(error_msg)
            return {
                "criteria": [],
                "success": False,
                "needs_review": True,
                "error": error_msg
            }
    
    def validate_criteria(self, criteria: List[EligibilityCriterion]) -> Dict[str, any]:
        """
        Validate extracted criteria categories and priorities.
        
        Checks that:
        - All categories are valid (Financial, Technical, Compliance, Documentation)
        - All priorities are valid (Mandatory, Optional)
        - All required fields are populated
        - Source pages are valid
        
        Args:
            criteria: List of EligibilityCriterion objects
            
        Returns:
            Dictionary containing:
                - valid: Boolean indicating if all criteria are valid
                - issues: List of validation issues found
                
        Validates: Requirements 1.4, 1.5, 1.6
        """
        logger.info(f"Validating {len(criteria)} extracted criteria")
        
        valid_categories = {"Financial", "Technical", "Compliance", "Documentation"}
        valid_priorities = {"Mandatory", "Optional"}
        
        issues = []
        
        for i, criterion in enumerate(criteria):
            # Validate category
            if criterion.category not in valid_categories:
                issues.append(
                    f"Criterion {i+1} (ID: {criterion.id}): Invalid category '{criterion.category}'. "
                    f"Must be one of: {valid_categories}"
                )
            
            # Validate priority
            if criterion.priority not in valid_priorities:
                issues.append(
                    f"Criterion {i+1} (ID: {criterion.id}): Invalid priority '{criterion.priority}'. "
                    f"Must be one of: {valid_priorities}"
                )
            
            # Validate required fields
            if not criterion.description or not criterion.description.strip():
                issues.append(
                    f"Criterion {i+1} (ID: {criterion.id}): Missing or empty description"
                )
            
            if not criterion.original_text or not criterion.original_text.strip():
                issues.append(
                    f"Criterion {i+1} (ID: {criterion.id}): Missing or empty original_text"
                )
            
            # Validate source page
            if criterion.source_page < 1:
                issues.append(
                    f"Criterion {i+1} (ID: {criterion.id}): Invalid source_page {criterion.source_page}. "
                    f"Must be >= 1"
                )
        
        if issues:
            logger.warning(f"Found {len(issues)} validation issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("All criteria passed validation")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
