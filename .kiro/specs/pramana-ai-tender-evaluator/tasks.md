# Implementation Plan: Pramana AI Tender Evaluator

## Overview

This implementation plan follows the "AI extracts, Python decides" architecture. We'll build incrementally starting with core infrastructure (Pydantic schemas, LLM validation), then document processing, retrieval system, evaluation engine, rule engine, UI, and finally optimizations for demo performance. Each task builds on previous work and includes validation through code execution.

## Tasks

- [x] 1. Set up project structure and core Pydantic schemas
  - Create directory structure: `src/`, `src/models/`, `src/processors/`, `src/engines/`, `src/ui/`, `tests/`
  - Create `requirements.txt` with dependencies: langchain, langchain-community, pydantic, streamlit, faiss-cpu, sentence-transformers, pdfplumber, camelot-py[cv], pytesseract, Pillow, reportlab
  - Define all Pydantic schemas in `src/models/schemas.py`: EligibilityCriterion, ExtractedDocument, EvidenceChunk, FinancialEvidence, TechnicalEvidence, ComplianceEvidence, DocumentationEvidence, Decision, CriterionEvaluation, EvaluationResult, ManualOverride
  - Create configuration file `src/config.py` with LLM settings, performance targets, and file paths
  - _Requirements: 9.1, 9.7_

- [x] 1.1 Write property test for Pydantic schema validation
  - **Property 3: Criteria Extraction Returns Valid Schema**
  - **Property 17: Evidence Schema Validation**
  - **Validates: Requirements 1.3, 3.4, 9.1**

- [x] 2. Implement LLM extractor with Pydantic validation and retry logic
  - [x] 2.1 Create `src/engines/llm_extractor.py` with LLMExtractor class
    - Implement Ollama client initialization with langchain-community
    - Implement `extract_with_validation()` method with PydanticOutputParser
    - Implement retry logic (max 3 attempts) with simplified prompts on validation failure
    - Implement safe default fallback when retries exhausted
    - Add validation failure logging
    - _Requirements: 9.2, 9.3, 9.4, 9.6_
  
  - [ ]* 2.2 Write property test for validation retry logic
    - **Property 23: Pydantic Validation Prevents Crashes**
    - **Property 43: Validation Failure Retry Logic**
    - **Property 44: Retry Exhaustion Fallback**
    - **Validates: Requirements 4.7, 9.3, 9.4**
  
  - [x] 2.3 Create prompt templates in `src/engines/prompts.py`
    - Define criteria extraction prompt template
    - Define evidence extraction prompts for each category (Financial, Technical, Compliance, Documentation)
    - Include format instructions placeholders for Pydantic schemas
    - _Requirements: 1.3, 4.2, 4.3, 4.4, 4.5_

- [x] 3. Implement document processing pipeline
  - [x] 3.1 Create `src/processors/text_extractor.py` for PDF text extraction
    - Implement pdfplumber-based text extraction with page preservation
    - Add error handling for corrupted PDFs
    - Return structured text with page metadata
    - _Requirements: 1.1, 2.3, 2.4_
  
  - [ ]* 3.2 Write property test for text extraction
    - **Property 1: Text Extraction Preserves Content**
    - **Validates: Requirements 1.1**
  
  - [x] 3.3 Create `src/processors/table_extractor.py` for table extraction
    - Implement camelot-py table extraction
    - Add fallback to text-only extraction on failure
    - Preserve table structure and page numbers
    - _Requirements: 1.2_
  
  - [ ]* 3.4 Write property test for table extraction
    - **Property 2: Table Structure Preservation**
    - **Validates: Requirements 1.2**
  
  - [x] 3.5 Create `src/processors/ocr_engine.py` for OCR processing
    - Implement Tesseract OCR for scanned PDFs and images
    - Calculate and return OCR confidence scores per page
    - Flag pages with confidence < 0.6 for manual review
    - _Requirements: 2.2, 2.6_
  
  - [x] 3.6 Create `src/processors/document_processor.py` as orchestrator
    - Implement file type detection (.pdf, .png, .jpg, .jpeg)
    - Route to appropriate extraction method (pdfplumber vs OCR)
    - Return ExtractedDocument Pydantic objects
    - Handle multiple documents per bidder with bidder_id grouping
    - _Requirements: 2.1, 2.5, 2.7_
  
  - [ ]* 3.7 Write property tests for document processing
    - **Property 8: File Type Acceptance**
    - **Property 9: OCR for Image Files**
    - **Property 10: PDFPlumber for Native PDFs**
    - **Property 11: Multi-Document Aggregation**
    - **Property 12: OCR Confidence Flagging**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 2.6**

- [x] 4. Implement tender processor
  - [x] 4.1 Create `src/processors/tender_processor.py`
    - Implement `process_tender()` method using TextExtractor and TableExtractor
    - Call LLMExtractor to extract criteria with CriteriaList schema
    - Validate extracted criteria categories and priorities
    - Store criteria with original text and page numbers
    - Flag extraction failures for manual review
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  
  - [ ]* 4.2 Write property tests for tender processing
    - **Property 4: Criterion Category Validity**
    - **Property 5: Criterion Priority Validity**
    - **Property 6: Metadata Completeness**
    - **Property 7: Extraction Failure Handling**
    - **Validates: Requirements 1.4, 1.5, 1.6, 1.7**

- [x] 5. Checkpoint - Ensure document processing works end-to-end
  - Test tender PDF upload and criteria extraction
  - Test bidder document upload with various formats
  - Verify Pydantic validation catches malformed outputs
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement retrieval system with FAISS
  - [x] 6.1 Create `src/engines/retrieval_engine.py`
    - Initialize sentence-transformers model (all-MiniLM-L6-v2)
    - Create FAISS IndexFlatL2 with dimension 384
    - Implement text chunking with 512 token chunks and 50% overlap
    - Implement `add_documents()` to embed and index document chunks
    - Store metadata mapping (index → document_id, page_number, text, source_file)
    - _Requirements: 3.1, 3.2_
  
  - [x] 6.2 Implement retrieval query method
    - Implement `retrieve()` method for top-k semantic search (k=5)
    - Convert L2 distances to confidence scores
    - Return EvidenceChunk Pydantic objects with metadata
    - Handle case where fewer than k chunks exist
    - _Requirements: 3.3, 3.5_
  
  - [ ]* 6.3 Write property tests for retrieval
    - **Property 14: Embedding Dimension Consistency**
    - **Property 15: FAISS Index Growth**
    - **Property 16: Top-K Retrieval**
    - **Property 19: Embedding Cache Reuse**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.7**
  
  - [x] 6.4 Implement embedding caching
    - Add cache for embeddings in session state
    - Implement save/load for FAISS index to disk
    - Pre-compute embeddings for demo documents
    - _Requirements: 3.7, 8.7_

- [x] 7. Implement evaluation engine
  - [x] 7.1 Create `src/engines/evaluation_engine.py`
    - Implement `evaluate_bidder()` to orchestrate full evaluation
    - Implement `evaluate_criterion()` for single criterion evaluation
    - Call RetrievalEngine to get top 5 relevant chunks per criterion
    - Call LLMExtractor with category-specific evidence schemas
    - Create explainability records with evidence, source pages, confidence
    - Handle "Evidence Not Found" case (all confidence <= 0.5)
    - _Requirements: 4.1, 4.6, 3.6_
  
  - [ ]* 7.2 Write property tests for evaluation engine
    - **Property 18: Low Confidence Evidence Flagging**
    - **Property 20: Criterion Independence**
    - **Property 21: Type-Specific Evidence Schema Completeness**
    - **Property 22: Explainability Record Completeness**
    - **Validates: Requirements 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

- [x] 8. Implement rule engine for deterministic decisions
  - [x] 8.1 Create `src/engines/rule_engine.py` with RuleEngine class
    - Implement `apply_rules()` method for single criterion decision
    - Create rule sets for Financial, Technical, Compliance, Documentation categories
    - Implement threshold comparison logic for mandatory criteria
    - Assign "Needs Review" verdict when confidence < 0.7
    - Log all decisions with rule_applied, values_compared, rationale
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.7_
  
  - [x] 8.2 Implement final verdict computation
    - Implement `compute_verdict()` method
    - Apply logic: all mandatory satisfied → "Eligible"
    - Apply logic: any mandatory failed → "Not Eligible"
    - Apply logic: any mandatory needs review → "Needs Review"
    - _Requirements: 5.5, 5.6_
  
  - [ ]* 8.3 Write property tests for rule engine
    - **Property 24: Rule Engine Determinism**
    - **Property 25: LLM Extraction Scope Limitation**
    - **Property 26: Mandatory Criterion Threshold Comparison**
    - **Property 27: Low Confidence Triggers Review**
    - **Property 28: All Satisfied Means Eligible**
    - **Property 29: Any Failed Means Not Eligible**
    - **Property 30: Comprehensive Audit Logging**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**

- [~] 9. Checkpoint - Ensure evaluation pipeline works end-to-end
  - Test full evaluation flow: tender upload → bidder upload → evaluation → verdict
  - Verify rule engine makes deterministic decisions
  - Verify audit logs are complete
  - Ensure all tests pass, ask the user if questions arise.

- [~] 10. Implement Streamlit UI with caching
  - [~] 10.1 Create `src/ui/app.py` main Streamlit application
    - Set up page configuration and session state initialization
    - Implement tender upload section with file uploader
    - Display extracted criteria in expandable sections
    - Implement bidder upload section (multi-file uploader)
    - Add evaluation trigger button
    - Display evaluation results with verdict and criterion details
    - _Requirements: 8.4_
  
  - [~] 10.2 Add aggressive caching decorators
    - Apply `@st.cache_resource` to LLM client initialization
    - Apply `@st.cache_resource` to FAISS index loading
    - Apply `@st.cache_data` to document processing functions
    - Apply `@st.cache_data` to embedding generation
    - Cache LLM responses by prompt hash in session state
    - _Requirements: 8.4, 8.7_
  
  - [~] 10.3 Implement explainability display
    - Show evidence chunks with source document and page number
    - Display confidence scores for all extracted evidence
    - Show rule applied and decision rationale
    - Highlight low-confidence extractions (< 0.7) in distinct color
    - _Requirements: 6.2, 6.3, 6.6, 10.3, 10.4_

- [~] 11. Implement human review dashboard
  - [~] 11.1 Create `src/ui/review_dashboard.py`
    - Filter and display bidders with verdict "Needs Review"
    - Show complete explainability records for flagged criteria
    - Display original document pages alongside extracted evidence
    - _Requirements: 6.1, 6.2, 6.3, 10.5_
  
  - [~] 11.2 Implement manual override functionality
    - Add UI controls for verdict override per criterion
    - Capture reviewer identity, timestamp, and justification
    - Update criterion evaluation with override
    - Automatically recalculate final verdict after override
    - Log override to audit trail
    - _Requirements: 6.4, 6.5, 6.7_
  
  - [ ]* 11.3 Write property tests for review dashboard
    - **Property 31: Review Dashboard Filtering**
    - **Property 32: Flagged Criterion Explainability Display**
    - **Property 33: Manual Override Functionality**
    - **Property 34: Override Audit Trail**
    - **Property 35: Verdict Recomputation After Override**
    - **Validates: Requirements 6.1, 6.2, 6.4, 6.5, 6.7**

- [~] 12. Implement report generation
  - [~] 12.1 Create `src/engines/report_generator.py`
    - Implement PDF report generation using reportlab
    - Include bidder name, final verdict, timestamp, system version
    - List all criteria with results, evidence, confidence scores
    - Include page references for all evidence
    - Document manual overrides with reviewer details
    - Add summary section with counts (satisfied/failed/reviewed)
    - Format for government compliance
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
  
  - [ ]* 12.2 Write property tests for report generation
    - **Property 36: PDF Report Generation**
    - **Property 37: Report Completeness**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**
  
  - [~] 12.3 Add report download to Streamlit UI
    - Add download button in UI for PDF report
    - Generate report on-demand with caching
    - _Requirements: 7.1_

- [~] 13. Implement audit logging system
  - [~] 13.1 Create `src/utils/audit_logger.py`
    - Implement JSON-based audit log structure
    - Log all operations with timestamps
    - Log criterion evaluations with evidence and decisions
    - Log manual overrides
    - Store logs in `audit_logs/` directory
    - _Requirements: 5.7, 10.1, 10.6_
  
  - [ ]* 13.2 Write property tests for audit logging
    - **Property 30: Comprehensive Audit Logging**
    - **Property 46: AI vs Rule Distinction**
    - **Validates: Requirements 5.7, 10.1, 10.4, 10.6**

- [~] 14. Create mock data generator for demo
  - [~] 14.1 Create `src/utils/mock_data_generator.py`
    - Generate sample tender PDF with eligibility criteria
    - Generate sample bidder documents (compliant and non-compliant)
    - Include various document types (native PDF, scanned PDF, images)
    - Create documents with clear pass/fail scenarios
    - Store in `demo_data/` directory
    - _Requirements: 8.3_
  
  - [~] 14.2 Pre-compute demo embeddings and cache
    - Run document processing on all demo documents
    - Generate and save FAISS index to disk
    - Cache LLM extractions for demo tender
    - Store in `cache/` directory for instant demo loading
    - _Requirements: 8.7_

- [~] 15. Implement performance optimizations
  - [~] 15.1 Add performance monitoring
    - Add timing decorators to key functions
    - Log processing times for tender and bidder evaluation
    - Verify tender processing < 60s target
    - Verify bidder evaluation < 90s target
    - _Requirements: 8.5, 8.6_
  
  - [~] 15.2 Optimize for Windows deployment
    - Add Windows-specific setup instructions for Tesseract
    - Add Windows-specific setup instructions for Ghostscript (camelot dependency)
    - Test on 16GB RAM Windows laptop
    - Document Ollama installation and model loading
    - _Requirements: 8.3_
  
  - [ ]* 15.3 Write property tests for performance and deployment
    - **Property 38: Local-Only Execution**
    - **Property 39: Cache Utilization**
    - **Property 40: Tender Processing Performance**
    - **Property 41: Bidder Evaluation Performance**
    - **Validates: Requirements 8.1, 8.2, 8.4, 8.5, 8.6**

- [~] 16. Implement error handling across all modules
  - [~] 16.1 Add error handling to document processors
    - Handle corrupted PDF errors with user feedback
    - Handle OCR failures with low-quality scan warnings
    - Handle table extraction failures with fallback
    - _Requirements: 1.7, 2.6_
  
  - [~] 16.2 Add error handling to LLM extractor
    - Handle Ollama connection failures with clear error message
    - Handle timeout errors with retry logic
    - Prevent system crashes from LLM failures
    - _Requirements: 9.3, 9.4_
  
  - [~] 16.3 Add error handling to FAISS retrieval
    - Handle corrupted index errors
    - Handle empty index queries
    - Provide graceful degradation
    - _Requirements: 3.6_

- [~] 17. Create comprehensive README and setup documentation
  - [~] 17.1 Write `README.md`
    - Document system architecture and design principles
    - Provide Windows installation instructions (Python, Ollama, Tesseract, Ghostscript)
    - Document how to run the demo
    - Include performance targets and optimization notes
    - _Requirements: 8.2, 8.3_
  
  - [~] 17.2 Create `DEMO_GUIDE.md`
    - Step-by-step demo walkthrough
    - Explain pre-cached data for performance
    - Document expected outputs and timings
    - _Requirements: 8.4, 8.7_

- [~] 18. Final integration and testing
  - [~] 18.1 Integration testing with demo data
    - Run full workflow with demo tender and bidders
    - Verify all verdicts are correct
    - Verify all audit logs are complete
    - Verify reports generate correctly
    - _Requirements: All_
  
  - [~] 18.2 Verify all correctness properties
    - Review property test results
    - Ensure no crashes or validation failures
    - Verify explainability and auditability
    - _Requirements: 10.1, 10.2, 10.7_
  
  - [~] 18.3 Performance validation
    - Measure tender processing time
    - Measure bidder evaluation time
    - Verify cache hit rates
    - Optimize bottlenecks if needed
    - _Requirements: 8.5, 8.6, 8.7_

- [~] 19. Final checkpoint - System ready for demo
  - Ensure all tests pass
  - Verify demo runs smoothly with pre-cached data
  - Confirm all documentation is complete
  - Ask the user if questions arise before considering implementation complete.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties from the design document
- The implementation follows strict "AI extracts, Python decides" architecture
- All LLM outputs use Pydantic validation to prevent crashes
- Aggressive caching is critical for demo performance targets
