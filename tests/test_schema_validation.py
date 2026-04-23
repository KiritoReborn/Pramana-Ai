"""Property tests for Pydantic schema validation

**Validates: Requirements 1.3, 3.4, 9.1**
"""

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError
from datetime import datetime

from src.models.schemas import (
    EligibilityCriterion,
    ExtractedDocument,
    EvidenceChunk,
    FinancialEvidence,
    TechnicalEvidence,
    ComplianceEvidence,
    DocumentationEvidence,
    Decision,
    CriterionEvaluation,
    EvaluationResult,
    ManualOverride
)


# Strategy generators for valid data
@st.composite
def valid_criterion_data(draw):
    """Generate valid EligibilityCriterion data"""
    return {
        "id": draw(st.text(min_size=1, max_size=50)),
        "category": draw(st.sampled_from(["Financial", "Technical", "Compliance", "Documentation"])),
        "priority": draw(st.sampled_from(["Mandatory", "Optional"])),
        "description": draw(st.text(min_size=1, max_size=500)),
        "threshold_value": draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        "threshold_unit": draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        "source_page": draw(st.integers(min_value=1, max_value=1000)),
        "original_text": draw(st.text(min_size=1, max_size=500))
    }


@st.composite
def valid_financial_evidence_data(draw):
    """Generate valid FinancialEvidence data"""
    return {
        "value": draw(st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False)),
        "currency": draw(st.text(min_size=3, max_size=3, alphabet=st.characters(whitelist_categories=('Lu',)))),
        "unit": draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        "context": draw(st.text(min_size=1, max_size=500)),
        "source_page": draw(st.integers(min_value=1, max_value=1000)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0))
    }


@st.composite
def valid_technical_evidence_data(draw):
    """Generate valid TechnicalEvidence data"""
    return {
        "specification": draw(st.text(min_size=1, max_size=500)),
        "certifications": draw(st.lists(st.text(min_size=1, max_size=100), max_size=10)),
        "capabilities": draw(st.lists(st.text(min_size=1, max_size=100), max_size=10)),
        "source_page": draw(st.integers(min_value=1, max_value=1000)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0))
    }


@st.composite
def valid_compliance_evidence_data(draw):
    """Generate valid ComplianceEvidence data"""
    return {
        "regulation": draw(st.text(min_size=1, max_size=200)),
        "compliance_status": draw(st.text(min_size=1, max_size=200)),
        "effective_date": draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        "source_page": draw(st.integers(min_value=1, max_value=1000)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0))
    }


@st.composite
def valid_documentation_evidence_data(draw):
    """Generate valid DocumentationEvidence data"""
    return {
        "document_present": draw(st.booleans()),
        "document_type": draw(st.text(min_size=1, max_size=100)),
        "completeness": draw(st.text(min_size=1, max_size=200)),
        "source_page": draw(st.integers(min_value=1, max_value=1000)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0))
    }


@st.composite
def valid_evidence_chunk_data(draw):
    """Generate valid EvidenceChunk data"""
    return {
        "text": draw(st.text(min_size=1, max_size=1000)),
        "document_id": draw(st.text(min_size=1, max_size=50)),
        "page_number": draw(st.integers(min_value=1, max_value=1000)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0)),
        "source_file": draw(st.text(min_size=1, max_size=100))
    }


# Property 3: Criteria Extraction Returns Valid Schema
class TestProperty3CriteriaExtractionReturnsValidSchema:
    """**Property 3: Criteria Extraction Returns Valid Schema**
    
    For any tender text processed by the LLM_Extractor, the output should be 
    a valid Pydantic CriteriaList object with all required fields populated.
    
    **Validates: Requirements 1.3**
    """
    
    @given(valid_criterion_data())
    def test_valid_criterion_data_creates_valid_schema(self, criterion_data):
        """Valid criterion data should always create a valid EligibilityCriterion object"""
        criterion = EligibilityCriterion(**criterion_data)
        
        # Verify all required fields are present
        assert criterion.id == criterion_data["id"]
        assert criterion.category in ["Financial", "Technical", "Compliance", "Documentation"]
        assert criterion.priority in ["Mandatory", "Optional"]
        assert criterion.description == criterion_data["description"]
        assert criterion.source_page >= 1
        assert criterion.original_text == criterion_data["original_text"]
    
    @given(
        st.text(min_size=1),
        st.sampled_from(["Financial", "Technical", "Compliance", "Documentation"]),
        st.sampled_from(["Mandatory", "Optional"]),
        st.text(min_size=1),
        st.integers(min_value=1),
        st.text(min_size=1)
    )
    def test_criterion_with_minimal_fields(self, id, category, priority, description, source_page, original_text):
        """Criterion should be valid with only required fields"""
        criterion = EligibilityCriterion(
            id=id,
            category=category,
            priority=priority,
            description=description,
            source_page=source_page,
            original_text=original_text
        )
        
        assert criterion.id == id
        assert criterion.category == category
        assert criterion.priority == priority
        assert criterion.threshold_value is None
        assert criterion.threshold_unit is None
    
    @given(valid_criterion_data())
    def test_invalid_category_raises_validation_error(self, criterion_data):
        """Invalid category should raise ValidationError"""
        criterion_data["category"] = "InvalidCategory"
        
        with pytest.raises(ValidationError):
            EligibilityCriterion(**criterion_data)
    
    @given(valid_criterion_data())
    def test_invalid_priority_raises_validation_error(self, criterion_data):
        """Invalid priority should raise ValidationError"""
        criterion_data["priority"] = "InvalidPriority"
        
        with pytest.raises(ValidationError):
            EligibilityCriterion(**criterion_data)


# Property 17: Evidence Schema Validation
class TestProperty17EvidenceSchemaValidation:
    """**Property 17: Evidence Schema Validation**
    
    For any evidence extracted by LLM_Extractor, the output should be a valid 
    Pydantic evidence object (FinancialEvidence, TechnicalEvidence, 
    ComplianceEvidence, or DocumentationEvidence) with all required fields.
    
    **Validates: Requirements 3.4**
    """
    
    @given(valid_financial_evidence_data())
    def test_valid_financial_evidence_creates_valid_schema(self, evidence_data):
        """Valid financial evidence data should create valid FinancialEvidence object"""
        evidence = FinancialEvidence(**evidence_data)
        
        assert evidence.value >= 0.0
        assert len(evidence.currency) >= 1
        assert evidence.source_page >= 1
        assert 0.0 <= evidence.confidence <= 1.0
        assert evidence.context == evidence_data["context"]
    
    @given(valid_technical_evidence_data())
    def test_valid_technical_evidence_creates_valid_schema(self, evidence_data):
        """Valid technical evidence data should create valid TechnicalEvidence object"""
        evidence = TechnicalEvidence(**evidence_data)
        
        assert evidence.specification == evidence_data["specification"]
        assert evidence.certifications == evidence_data["certifications"]
        assert evidence.capabilities == evidence_data["capabilities"]
        assert evidence.source_page >= 1
        assert 0.0 <= evidence.confidence <= 1.0
    
    @given(valid_compliance_evidence_data())
    def test_valid_compliance_evidence_creates_valid_schema(self, evidence_data):
        """Valid compliance evidence data should create valid ComplianceEvidence object"""
        evidence = ComplianceEvidence(**evidence_data)
        
        assert evidence.regulation == evidence_data["regulation"]
        assert evidence.compliance_status == evidence_data["compliance_status"]
        assert evidence.source_page >= 1
        assert 0.0 <= evidence.confidence <= 1.0
    
    @given(valid_documentation_evidence_data())
    def test_valid_documentation_evidence_creates_valid_schema(self, evidence_data):
        """Valid documentation evidence data should create valid DocumentationEvidence object"""
        evidence = DocumentationEvidence(**evidence_data)
        
        assert isinstance(evidence.document_present, bool)
        assert evidence.document_type == evidence_data["document_type"]
        assert evidence.completeness == evidence_data["completeness"]
        assert evidence.source_page >= 1
        assert 0.0 <= evidence.confidence <= 1.0
    
    @given(valid_financial_evidence_data())
    def test_confidence_out_of_range_raises_validation_error(self, evidence_data):
        """Confidence score outside [0, 1] should raise ValidationError"""
        evidence_data["confidence"] = 1.5
        
        with pytest.raises(ValidationError):
            FinancialEvidence(**evidence_data)
    
    @given(valid_financial_evidence_data())
    def test_negative_confidence_raises_validation_error(self, evidence_data):
        """Negative confidence score should raise ValidationError"""
        evidence_data["confidence"] = -0.1
        
        with pytest.raises(ValidationError):
            FinancialEvidence(**evidence_data)
    
    @given(valid_evidence_chunk_data())
    def test_evidence_chunk_validation(self, chunk_data):
        """EvidenceChunk should validate correctly with all required fields"""
        chunk = EvidenceChunk(**chunk_data)
        
        assert chunk.text == chunk_data["text"]
        assert chunk.document_id == chunk_data["document_id"]
        assert chunk.page_number >= 1
        assert 0.0 <= chunk.confidence <= 1.0
        assert chunk.source_file == chunk_data["source_file"]
    
    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.text(min_size=1, max_size=500),
        st.integers(min_value=1, max_value=1000)
    )
    def test_all_evidence_types_have_confidence_and_source_page(self, confidence, context, source_page):
        """All evidence types must have confidence and source_page fields"""
        # Financial
        fin_evidence = FinancialEvidence(
            value=100.0,
            currency="USD",
            context=context,
            source_page=source_page,
            confidence=confidence
        )
        assert 0.0 <= fin_evidence.confidence <= 1.0
        assert fin_evidence.source_page >= 1
        
        # Technical
        tech_evidence = TechnicalEvidence(
            specification=context,
            source_page=source_page,
            confidence=confidence
        )
        assert 0.0 <= tech_evidence.confidence <= 1.0
        assert tech_evidence.source_page >= 1
        
        # Compliance
        comp_evidence = ComplianceEvidence(
            regulation=context,
            compliance_status="Compliant",
            source_page=source_page,
            confidence=confidence
        )
        assert 0.0 <= comp_evidence.confidence <= 1.0
        assert comp_evidence.source_page >= 1
        
        # Documentation
        doc_evidence = DocumentationEvidence(
            document_present=True,
            document_type="Certificate",
            completeness="Complete",
            source_page=source_page,
            confidence=confidence
        )
        assert 0.0 <= doc_evidence.confidence <= 1.0
        assert doc_evidence.source_page >= 1


# Additional schema validation tests
class TestSchemaValidationCompleteness:
    """Test that all schemas enforce required fields and constraints"""
    
    def test_extracted_document_requires_all_fields(self):
        """ExtractedDocument should require all mandatory fields"""
        with pytest.raises(ValidationError):
            ExtractedDocument()
    
    def test_decision_requires_all_fields(self):
        """Decision should require all mandatory fields"""
        with pytest.raises(ValidationError):
            Decision()
    
    def test_manual_override_requires_all_fields(self):
        """ManualOverride should require all mandatory fields"""
        with pytest.raises(ValidationError):
            ManualOverride()
    
    @given(
        st.text(min_size=1),
        st.text(min_size=1),
        st.sampled_from(["Satisfied", "Not Satisfied", "Needs Review"]),
        st.text(min_size=1),
        st.text(min_size=1)
    )
    def test_decision_verdict_must_be_valid_literal(self, criterion_id, rule_applied, verdict, rationale, comparison):
        """Decision verdict must be one of the allowed literals"""
        decision = Decision(
            criterion_id=criterion_id,
            verdict=verdict,
            rule_applied=rule_applied,
            rationale=rationale,
            comparison=comparison,
            timestamp=datetime.now()
        )
        
        assert decision.verdict in ["Satisfied", "Not Satisfied", "Needs Review"]
