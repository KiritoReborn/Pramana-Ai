"""Prompt templates for LLM extraction tasks"""

# Criteria Extraction Prompt Template
CRITERIA_EXTRACTION_PROMPT = """You are extracting eligibility criteria from a government tender document.

Extract all eligibility requirements and classify them.

For each criterion, identify:
- id: A unique identifier (e.g., "FIN-001", "TECH-001", "COMP-001", "DOC-001")
- category: Must be exactly one of: "Financial", "Technical", "Compliance", or "Documentation"
- priority: Must be exactly one of: "Mandatory" or "Optional"
- description: Full text of the requirement
- threshold_value: Any numeric threshold mentioned (as string, e.g., "1000000")
- threshold_unit: Unit for the threshold (e.g., "USD", "years", "certifications")
- source_page: Page number where the criterion appears (as integer)
- original_text: The exact original text from the document

Text:
{text}

{format_instructions}
"""


# Financial Evidence Extraction Prompt Template
FINANCIAL_EVIDENCE_PROMPT = """You are extracting financial evidence from bidder documents.

Criterion: {criterion_description}

Find evidence related to this financial criterion in the following text chunks.

Extract:
- value: Numeric value (as float, e.g., 1000000.0)
- currency: Currency code (e.g., "USD", "EUR", "INR")
- unit: Unit if applicable (e.g., "per year", "total", "annual")
- context: Surrounding text that provides context (1-2 sentences)
- source_page: Page number where evidence was found (as integer)
- confidence: Your confidence in this extraction from 0.0 to 1.0 (as float)

Text chunks:
{chunks}

{format_instructions}
"""


# Technical Evidence Extraction Prompt Template
TECHNICAL_EVIDENCE_PROMPT = """You are extracting technical evidence from bidder documents.

Criterion: {criterion_description}

Find evidence related to this technical criterion in the following text chunks.

Extract:
- specification: The technical specification or capability mentioned
- certifications: List of certifications mentioned (e.g., ["ISO 9001", "ISO 27001"])
- capabilities: List of technical capabilities mentioned (e.g., ["cloud deployment", "API integration"])
- source_page: Page number where evidence was found (as integer)
- confidence: Your confidence in this extraction from 0.0 to 1.0 (as float)

Text chunks:
{chunks}

{format_instructions}
"""


# Compliance Evidence Extraction Prompt Template
COMPLIANCE_EVIDENCE_PROMPT = """You are extracting compliance evidence from bidder documents.

Criterion: {criterion_description}

Find evidence related to this compliance criterion in the following text chunks.

Extract:
- regulation: The regulation or standard being addressed (e.g., "GDPR", "ISO 27001")
- compliance_status: Statement about compliance (e.g., "fully compliant", "certified", "in process")
- effective_date: Date mentioned if any (as string, e.g., "2023-01-15")
- source_page: Page number where evidence was found (as integer)
- confidence: Your confidence in this extraction from 0.0 to 1.0 (as float)

Text chunks:
{chunks}

{format_instructions}
"""


# Documentation Evidence Extraction Prompt Template
DOCUMENTATION_EVIDENCE_PROMPT = """You are extracting documentation evidence from bidder documents.

Criterion: {criterion_description}

Find evidence related to this documentation criterion in the following text chunks.

Extract:
- document_present: Whether the required document exists (true or false)
- document_type: Type of document (e.g., "financial statement", "tax certificate", "registration")
- completeness: Assessment of completeness (e.g., "complete", "partial", "missing sections")
- source_page: Page number where evidence was found (as integer)
- confidence: Your confidence in this extraction from 0.0 to 1.0 (as float)

Text chunks:
{chunks}

{format_instructions}
"""


# Mapping of criterion categories to their prompt templates
EVIDENCE_PROMPT_MAP = {
    "Financial": FINANCIAL_EVIDENCE_PROMPT,
    "Technical": TECHNICAL_EVIDENCE_PROMPT,
    "Compliance": COMPLIANCE_EVIDENCE_PROMPT,
    "Documentation": DOCUMENTATION_EVIDENCE_PROMPT
}


def get_evidence_prompt(category: str) -> str:
    """
    Get the appropriate evidence extraction prompt for a criterion category.
    
    Args:
        category: Criterion category ("Financial", "Technical", "Compliance", "Documentation")
        
    Returns:
        Prompt template string
        
    Raises:
        ValueError: If category is not recognized
    """
    if category not in EVIDENCE_PROMPT_MAP:
        raise ValueError(
            f"Unknown criterion category: {category}. "
            f"Must be one of: {list(EVIDENCE_PROMPT_MAP.keys())}"
        )
    
    return EVIDENCE_PROMPT_MAP[category]
