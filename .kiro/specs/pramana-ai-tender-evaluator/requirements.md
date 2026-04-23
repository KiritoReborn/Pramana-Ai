# Requirements Document

## Introduction

Pramana AI is an evidence-grounded eligibility evaluator for government procurement tenders. The system evaluates bidder submissions against tender eligibility criteria using local AI models combined with deterministic rule engines. It provides full explainability and auditability for government compliance, running entirely offline on standard hardware without cloud dependencies.

## Glossary

- **Tender_Document**: A PDF file containing government procurement requirements and eligibility criteria
- **Eligibility_Criterion**: A specific requirement that bidders must meet, classified as Financial, Technical, Compliance, or Documentation
- **Bidder_Submission**: Collection of documents (PDFs, scanned PDFs, images) submitted by a bidder
- **Evidence**: Extracted text, values, or data from bidder documents that supports evaluation of a criterion
- **Evaluation_Engine**: The system component that assesses bidder submissions against criteria
- **Rule_Engine**: Deterministic Python-based decision logic that makes final eligibility determinations
- **LLM_Extractor**: Local language model (Llama 3.1 via Ollama) that extracts structured information
- **Confidence_Score**: Numerical value (0-1) indicating the system's certainty in extracted evidence
- **Verdict**: Final evaluation result: Eligible, Not Eligible, or Needs Review
- **Explainability_Record**: Detailed trace showing evidence source, page numbers, extracted values, and decision rationale
- **Human_Review_Dashboard**: Interface for manual verification of flagged evaluations
- **Evaluation_Report**: Downloadable document containing complete evaluation results and audit trail

## Requirements

### Requirement 1: Tender Document Processing

**User Story:** As a procurement officer, I want to upload tender documents and automatically extract eligibility criteria, so that I can quickly set up evaluation parameters without manual data entry.

#### Acceptance Criteria

1. WHEN a tender PDF is uploaded, THE Tender_Processor SHALL extract all text content using pdfplumber
2. WHEN the tender contains tables, THE Tender_Processor SHALL extract tabular data using camelot-py
3. WHEN text extraction is complete, THE LLM_Extractor SHALL identify all eligibility criteria using structured output (Pydantic)
4. THE LLM_Extractor SHALL classify each criterion into exactly one category: Financial, Technical, Compliance, or Documentation
5. THE LLM_Extractor SHALL mark each criterion as Mandatory or Optional
6. THE System SHALL store extracted criteria with their original text and page numbers
7. WHEN extraction fails for any section, THE System SHALL flag it for manual review rather than proceeding with incomplete data

### Requirement 2: Bidder Document Ingestion

**User Story:** As a procurement officer, I want to upload multiple bidder documents in various formats, so that I can evaluate submissions regardless of document format.

#### Acceptance Criteria

1. THE Document_Uploader SHALL accept PDF files, scanned PDF files, and image files (PNG, JPG, JPEG)
2. WHEN a scanned document or image is uploaded, THE OCR_Engine SHALL extract text using Tesseract OCR
3. WHEN a native PDF is uploaded, THE Document_Processor SHALL extract text using pdfplumber
4. THE System SHALL preserve page numbers and document metadata for all uploaded files
5. THE System SHALL process multiple documents per bidder as a single submission package
6. WHEN OCR confidence is below 0.6 for any page, THE System SHALL flag that page for manual verification
7. THE System SHALL store all extracted text in a structured format with document source references

### Requirement 3: Evidence Extraction and Retrieval

**User Story:** As an evaluation system, I want to retrieve relevant evidence from bidder documents for each criterion, so that I can perform accurate evaluations.

#### Acceptance Criteria

1. THE System SHALL create vector embeddings for all extracted bidder text using all-MiniLM-L6-v2 local model
2. THE System SHALL store embeddings in FAISS vector database for efficient retrieval
3. WHEN evaluating a criterion, THE Retrieval_Engine SHALL query FAISS for the top 5 most relevant text chunks
4. THE LLM_Extractor SHALL extract structured evidence from retrieved chunks using Pydantic schemas
5. THE System SHALL record the source document, page number, and confidence score for each extracted evidence
6. WHEN no relevant evidence is found with confidence above 0.5, THE System SHALL mark the criterion as "Evidence Not Found"
7. THE System SHALL cache all embeddings to optimize demo performance

### Requirement 4: Criterion-by-Criterion Evaluation

**User Story:** As a procurement officer, I want the system to evaluate each bidder against every criterion with clear evidence, so that I can understand the basis for each decision.

#### Acceptance Criteria

1. THE Evaluation_Engine SHALL process each criterion independently for each bidder
2. WHEN evaluating a Financial criterion, THE LLM_Extractor SHALL extract numerical values with units and currency
3. WHEN evaluating a Technical criterion, THE LLM_Extractor SHALL extract specifications, certifications, and capabilities
4. WHEN evaluating a Compliance criterion, THE LLM_Extractor SHALL extract regulatory compliance evidence and dates
5. WHEN evaluating a Documentation criterion, THE LLM_Extractor SHALL verify document presence and completeness
6. THE System SHALL create an Explainability_Record for each criterion evaluation containing: evidence text, source page, extracted values, and confidence score
7. THE System SHALL never allow LLM hallucinations to crash the evaluation process by enforcing Pydantic type validation

### Requirement 5: Deterministic Decision Logic

**User Story:** As a government auditor, I want final eligibility decisions to be made by deterministic rules rather than AI judgment, so that decisions are consistent, explainable, and legally defensible.

#### Acceptance Criteria

1. THE Rule_Engine SHALL make all final eligibility determinations using Python-based deterministic logic
2. THE LLM_Extractor SHALL only extract evidence and SHALL NOT make threshold-based decisions
3. WHEN a Mandatory criterion has extracted evidence, THE Rule_Engine SHALL compare extracted values against threshold requirements
4. WHEN a Mandatory criterion lacks sufficient evidence (confidence < 0.7), THE Rule_Engine SHALL assign verdict "Needs Review"
5. WHEN all Mandatory criteria are satisfied, THE Rule_Engine SHALL assign verdict "Eligible"
6. WHEN any Mandatory criterion fails threshold comparison, THE Rule_Engine SHALL assign verdict "Not Eligible"
7. THE Rule_Engine SHALL log all decision steps with the specific rule applied and values compared

### Requirement 6: Human Review Interface

**User Story:** As a procurement officer, I want to review flagged evaluations and override decisions when necessary, so that I can ensure accuracy before finalizing results.

#### Acceptance Criteria

1. THE Human_Review_Dashboard SHALL display all bidders with verdict "Needs Review"
2. THE Human_Review_Dashboard SHALL show the complete Explainability_Record for each flagged criterion
3. THE Human_Review_Dashboard SHALL display extracted evidence alongside original document pages
4. THE Human_Review_Dashboard SHALL allow manual override of criterion evaluation results
5. WHEN a manual override is applied, THE System SHALL record the reviewer identity, timestamp, and justification
6. THE Human_Review_Dashboard SHALL highlight low-confidence extractions (confidence < 0.7) in a distinct color
7. THE System SHALL update the final verdict automatically when criterion evaluations are manually modified

### Requirement 7: Final Report Generation

**User Story:** As a procurement officer, I want to download a comprehensive evaluation report, so that I can document decisions and maintain an audit trail.

#### Acceptance Criteria

1. THE Report_Generator SHALL create a downloadable PDF report for each bidder evaluation
2. THE Evaluation_Report SHALL include: bidder name, final verdict, evaluation timestamp, and system version
3. THE Evaluation_Report SHALL list all criteria with their evaluation results, evidence, and confidence scores
4. THE Evaluation_Report SHALL include page references to source documents for all evidence
5. THE Evaluation_Report SHALL document all manual overrides with reviewer details and justifications
6. THE Evaluation_Report SHALL include a summary section showing counts of satisfied, failed, and reviewed criteria
7. THE Evaluation_Report SHALL be formatted for government compliance and archival purposes

### Requirement 8: Local Deployment and Performance

**User Story:** As a hackathon participant, I want the system to run entirely locally on standard hardware with fast demo performance, so that I can demonstrate it effectively without internet dependency.

#### Acceptance Criteria

1. THE System SHALL run all AI models locally using Ollama with Llama 3.1
2. THE System SHALL operate without any cloud API calls or internet connectivity
3. THE System SHALL run on Windows laptop with 16GB RAM and CPU/limited GPU
4. THE System SHALL use Streamlit with aggressive caching for UI responsiveness
5. WHEN processing a tender document, THE System SHALL complete extraction within 60 seconds
6. WHEN evaluating a single bidder, THE System SHALL complete evaluation within 90 seconds
7. THE System SHALL pre-compute and cache embeddings to optimize live demonstration performance

### Requirement 9: Structured Output Validation

**User Story:** As a system developer, I want all LLM outputs to be validated against strict schemas, so that the UI never crashes due to malformed or hallucinated data.

#### Acceptance Criteria

1. THE System SHALL define Pydantic schemas for all LLM extraction tasks
2. THE LLM_Extractor SHALL use LangChain structured output chains with Pydantic validation
3. WHEN LLM output fails Pydantic validation, THE System SHALL retry extraction with simplified prompt
4. WHEN retry fails after 3 attempts, THE System SHALL return a default safe value and flag for manual review
5. THE System SHALL never propagate unvalidated LLM output to the UI layer
6. THE System SHALL log all validation failures with the malformed output for debugging
7. THE System SHALL enforce type safety for all numerical extractions (amounts, dates, percentages)

### Requirement 10: Explainability and Auditability

**User Story:** As a government auditor, I want complete transparency into how each decision was made, so that I can verify compliance with procurement regulations.

#### Acceptance Criteria

1. THE System SHALL maintain a complete audit log of all operations with timestamps
2. THE Explainability_Record SHALL trace each decision back to specific evidence in source documents
3. THE System SHALL display confidence scores for all AI-extracted information
4. THE System SHALL distinguish between AI-extracted evidence and rule-based decisions in all outputs
5. THE System SHALL preserve original document pages alongside extracted evidence for verification
6. THE System SHALL record the specific rule or threshold that determined each criterion result
7. THE System SHALL make all audit logs and explainability records available in the Human_Review_Dashboard and Evaluation_Report

