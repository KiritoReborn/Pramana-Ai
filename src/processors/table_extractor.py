"""Table extraction from PDF documents using camelot-py"""

import camelot
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TableExtractor:
    """Handles table extraction from PDFs with fallback to text-only"""
    
    def extract_tables(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract tables from PDF using camelot-py with fallback.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing:
                - tables: List of extracted tables with structure
                - success: Boolean indicating success
                - error: Error message if failed
                - fallback_used: Boolean indicating if fallback was used
                
        Validates: Requirements 1.2
        """
        try:
            # Try to extract tables using camelot
            tables_data = []
            
            # Use 'lattice' method for tables with visible borders
            try:
                tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
                
                # If no tables found with lattice, try stream method
                if len(tables) == 0:
                    logger.info("No tables found with lattice method, trying stream method")
                    tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
                
                # Process extracted tables
                for table_num, table in enumerate(tables, start=1):
                    table_dict = {
                        "table_number": table_num,
                        "page": table.page,
                        "data": table.df.values.tolist(),  # Convert DataFrame to list
                        "columns": table.df.columns.tolist(),
                        "rows": len(table.df),
                        "cols": len(table.df.columns),
                        "accuracy": table.accuracy if hasattr(table, 'accuracy') else None
                    }
                    tables_data.append(table_dict)
                
                if len(tables_data) > 0:
                    logger.info(f"Successfully extracted {len(tables_data)} tables from {pdf_path}")
                    return {
                        "tables": tables_data,
                        "success": True,
                        "error": None,
                        "fallback_used": False
                    }
                else:
                    logger.warning(f"No tables detected in {pdf_path}")
                    return {
                        "tables": [],
                        "success": True,
                        "error": None,
                        "fallback_used": True
                    }
                    
            except Exception as e:
                logger.warning(f"Camelot extraction failed: {str(e)}, falling back to text-only")
                return {
                    "tables": [],
                    "success": True,
                    "error": None,
                    "fallback_used": True
                }
                
        except Exception as e:
            logger.error(f"Failed to extract tables from PDF {pdf_path}: {str(e)}")
            return {
                "tables": [],
                "success": False,
                "error": f"Table extraction failed: {str(e)}",
                "fallback_used": True
            }
