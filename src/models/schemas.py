"""Pydantic schemas for Pramana AI Tender Evaluator"""

from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional, Union
from datetime import datetime


class EligibilityCriterion(BaseModel):
    """Extracted eligibility criterion from tender"""
    id: str = Field(description="Unique criterion identifier")
    category: Literal["Financial", "Technical", "Compliance", "Documentation"]
    priority: Literal["Mandatory", "Optional"]
    description: str = Field(description="Full criterion text")
    threshold_value: Optional[str] = Field(None, description="Numeric threshold if applicable")
    threshold_unit: Optional[str] = Field(None, description="Unit for threshold")
    source_page: int = Field(description="Page number in tender document")
    original_text: str = Field(description="Original text from document")


class ExtractedDocument(BaseModel):
    """Processed bidder document"""
    document_id: str
    bidder_id: str
    file_name: str
    pages: List[str] = Field(description="Text content per page")
    page_metadata: List[dict] = Field(description="Metadata per page")
    ocr_confidence: Optional[float] = Field(None, description="Average OCR confidence")
    extraction_method: Literal["pdfplumber", "tesseract"]


class EvidenceChunk(BaseModel):
    """Retrieved evidence chunk from FAISS"""
    text: str = Field(description="Extracted text chunk")
    document_id: str
    page_number: int
    confidence: float = Field(ge=0.0, le=1.0, description="Retrieval confidence")
    source_file: str


class FinancialEvidence(BaseModel):
    """Extracted financial evidence"""
    value: float = Field(description="Numeric value")
    currency: str = Field(description="Currency code")
    unit: Optional[str] = Field(None, description="Unit if applicable")
    context: str = Field(description="Surrounding context")
    source_page: int
    confidence: float = Field(ge=0.0, le=1.0)


class TechnicalEvidence(BaseModel):
    """Extracted technical evidence"""
    specification: str = Field(description="Technical specification")
    certifications: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    source_page: int
    confidence: float = Field(ge=0.0, le=1.0)


class ComplianceEvidence(BaseModel):
    """Extracted compliance evidence"""
    regulation: str = Field(description="Regulation or standard")
    compliance_status: str = Field(description="Compliance statement")
    effective_date: Optional[str] = Field(None, description="Date if mentioned")
    source_page: int
    confidence: float = Field(ge=0.0, le=1.0)


class DocumentationEvidence(BaseModel):
    """Extracted documentation evidence"""
    document_present: bool = Field(description="Whether document exists")
    document_type: str = Field(description="Type of document")
    completeness: str = Field(description="Completeness assessment")
    source_page: int
    confidence: float = Field(ge=0.0, le=1.0)


class Decision(BaseModel):
    """Rule engine decision"""
    criterion_id: str
    verdict: Literal["Satisfied", "Not Satisfied", "Needs Review"]
    rule_applied: str = Field(description="Name of rule that made decision")
    comparison: Optional[str] = Field(None, description="Threshold comparison details")
    rationale: str = Field(description="Human-readable explanation")
    timestamp: datetime


class CriterionEvaluation(BaseModel):
    """Complete evaluation of single criterion"""
    criterion: EligibilityCriterion
    evidence_chunks: List[EvidenceChunk]
    extracted_evidence: Union[FinancialEvidence, TechnicalEvidence, ComplianceEvidence, DocumentationEvidence] = Field(description="Type-specific evidence")
    decision: Decision
    explainability_record: dict = Field(description="Full audit trail")


class EvaluationResult(BaseModel):
    """Complete bidder evaluation result"""
    bidder_id: str
    bidder_name: str
    final_verdict: Literal["Eligible", "Not Eligible", "Needs Review"]
    criterion_evaluations: List[CriterionEvaluation]
    summary: dict = Field(description="Counts of satisfied/failed/reviewed")
    timestamp: datetime
    system_version: str


class ManualOverride(BaseModel):
    """Manual review override"""
    criterion_id: str
    original_verdict: str
    new_verdict: str
    reviewer_id: str
    justification: str
    timestamp: datetime
