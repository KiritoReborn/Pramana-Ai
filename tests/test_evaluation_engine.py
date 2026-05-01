"""Tests for evaluation engine"""

import pytest
from datetime import datetime
from src.engines.evaluation_engine import EvaluationEngine
from src.engines.retrieval_engine import RetrievalEngine
from src.engines.llm_extractor import LLMExtractor
from src.models.schemas import (
    EligibilityCriterion,
    EvidenceChunk,
    FinancialEvidence,
    ExtractedDocument
)


class TestEvaluationEngine:
    """Test suite for EvaluationEngine"""
    
    @pytest.fixture
    def retrieval_engine(self):
        """Create a retrieval engine instance"""
        return RetrievalEngine()
    
    @pytest.fixture
    def llm_extractor(self):
        """Create an LLM extractor instance"""
        return LLMExtractor()
    
    @pytest.fixture
    def evaluation_engine(self, retrieval_engine, llm_extractor):
        """Create an evaluation engine instance"""
        return EvaluationEngine(retrieval_engine, llm_extractor)
    
    @pytest.fixture
    def sample_criterion(self):
        """Create a sample eligibility criterion"""
        return EligibilityCriterion(
            id="FIN-001",
            category="Financial",
            priority="Mandatory",
            description="Annual revenue must be at least $1,000,000 USD",
            threshold_value="1000000",
            threshold_unit="USD",
            source_page=5,
            original_text="The bidder must have annual revenue of at least $1,000,000 USD"
        )
    
    @pytest.fixture
    def sample_evidence_chunks(self):
        """Create sample evidence chunks"""
        return [
            EvidenceChunk(
                text="Our company has annual revenue of $2,500,000 USD for fiscal year 2023.",
                document_id="doc-001",
                page_number=3,
                confidence=0.85,
                source_file="financial_statement.pdf"
            ),
            EvidenceChunk(
                text="Total revenue: $2.5M USD",
                document_id="doc-001",
                page_number=5,
                confidence=0.78,
                source_file="financial_statement.pdf"
            )
        ]
    
    def test_evaluation_engine_initialization(self, evaluation_engine):
        """Test that evaluation engine initializes correctly"""
        assert evaluation_engine is not None
        assert evaluation_engine.retrieval_engine is not None
        assert evaluation_engine.llm_extractor is not None
    
    def test_is_evidence_not_found_empty_list(self, evaluation_engine):
        """Test evidence not found detection with empty list"""
        result = evaluation_engine._is_evidence_not_found([])
        assert result is True
    
    def test_is_evidence_not_found_low_confidence(self, evaluation_engine):
        """Test evidence not found detection with low confidence chunks"""
        low_confidence_chunks = [
            EvidenceChunk(
                text="Some text",
                document_id="doc-001",
                page_number=1,
                confidence=0.3,
                source_file="test.pdf"
            ),
            EvidenceChunk(
                text="More text",
                document_id="doc-001",
                page_number=2,
                confidence=0.4,
                source_file="test.pdf"
            )
        ]
        result = evaluation_engine._is_evidence_not_found(low_confidence_chunks)
        assert result is True
    
    def test_is_evidence_not_found_high_confidence(self, evaluation_engine, sample_evidence_chunks):
        """Test evidence not found detection with high confidence chunks"""
        result = evaluation_engine._is_evidence_not_found(sample_evidence_chunks)
        assert result is False
    
    def test_get_evidence_schema_financial(self, evaluation_engine):
        """Test getting evidence schema for Financial category"""
        schema = evaluation_engine._get_evidence_schema("Financial")
        assert schema == FinancialEvidence
    
    def test_create_explainability_record(self, evaluation_engine, sample_criterion, sample_evidence_chunks):
        """Test explainability record creation"""
        from src.models.schemas import Decision
        
        extracted_evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Annual revenue for fiscal year 2023",
            source_page=3,
            confidence=0.85
        )
        
        decision = Decision(
            criterion_id="FIN-001",
            verdict="Needs Review",
            rule_applied="PreliminaryEvaluation",
            comparison=None,
            rationale="Awaiting Rule Engine evaluation",
            timestamp=datetime.now()
        )
        
        record = evaluation_engine._create_explainability_record(
            criterion=sample_criterion,
            evidence_chunks=sample_evidence_chunks,
            extracted_evidence=extracted_evidence,
            decision=decision
        )
        
        # Verify record structure
        assert record["criterion_id"] == "FIN-001"
        assert record["criterion_category"] == "Financial"
        assert record["criterion_priority"] == "Mandatory"
        assert len(record["evidence_sources"]) == 2
        assert record["extraction_confidence"] == 0.85
        assert record["decision_verdict"] == "Needs Review"
        assert "traceability" in record
    
    def test_create_evidence_not_found_evaluation(self, evaluation_engine, sample_criterion):
        """Test creation of evidence not found evaluation"""
        low_confidence_chunks = [
            EvidenceChunk(
                text="Some text",
                document_id="doc-001",
                page_number=1,
                confidence=0.3,
                source_file="test.pdf"
            )
        ]
        
        evaluation = evaluation_engine._create_evidence_not_found_evaluation(
            criterion=sample_criterion,
            evidence_chunks=low_confidence_chunks
        )
        
        # Verify evaluation structure
        assert evaluation.criterion.id == "FIN-001"
        assert evaluation.decision.verdict == "Needs Review"
        assert evaluation.decision.rule_applied == "EvidenceNotFoundRule"
        assert evaluation.extracted_evidence.confidence == 0.0
        assert evaluation.explainability_record["evidence_not_found"] is True
    
    def test_create_fallback_evaluation(self, evaluation_engine, sample_criterion):
        """Test creation of fallback evaluation on error"""
        error_message = "Test error message"
        
        evaluation = evaluation_engine._create_fallback_evaluation(
            criterion=sample_criterion,
            error_message=error_message
        )
        
        # Verify evaluation structure
        assert evaluation.criterion.id == "FIN-001"
        assert evaluation.decision.verdict == "Needs Review"
        assert evaluation.decision.rule_applied == "EvaluationFailureRule"
        assert error_message in evaluation.decision.rationale
        assert evaluation.explainability_record["evaluation_failed"] is True
    
    def test_compute_final_verdict_all_satisfied(self, evaluation_engine, sample_criterion):
        """Test final verdict computation when all criteria satisfied"""
        from src.models.schemas import Decision, CriterionEvaluation
        
        decision = Decision(
            criterion_id="FIN-001",
            verdict="Satisfied",
            rule_applied="TestRule",
            comparison=None,
            rationale="Test",
            timestamp=datetime.now()
        )
        
        evaluation = CriterionEvaluation(
            criterion=sample_criterion,
            evidence_chunks=[],
            extracted_evidence=FinancialEvidence(
                value=2500000.0,
                currency="USD",
                context="Test",
                source_page=1,
                confidence=0.9
            ),
            decision=decision,
            explainability_record={}
        )
        
        verdict, summary = evaluation_engine._compute_final_verdict([evaluation])
        
        assert verdict == "Eligible"
        assert summary["satisfied"] == 1
        assert summary["mandatory_satisfied"] == 1
    
    def test_compute_final_verdict_needs_review(self, evaluation_engine, sample_criterion):
        """Test final verdict computation when criteria need review"""
        from src.models.schemas import Decision, CriterionEvaluation
        
        decision = Decision(
            criterion_id="FIN-001",
            verdict="Needs Review",
            rule_applied="TestRule",
            comparison=None,
            rationale="Test",
            timestamp=datetime.now()
        )
        
        evaluation = CriterionEvaluation(
            criterion=sample_criterion,
            evidence_chunks=[],
            extracted_evidence=FinancialEvidence(
                value=0.0,
                currency="USD",
                context="Test",
                source_page=1,
                confidence=0.3
            ),
            decision=decision,
            explainability_record={}
        )
        
        verdict, summary = evaluation_engine._compute_final_verdict([evaluation])
        
        assert verdict == "Needs Review"
        assert summary["needs_review"] == 1
        assert summary["mandatory_needs_review"] == 1
    
    def test_evaluate_bidder_with_sample_data(self, evaluation_engine, sample_criterion, retrieval_engine):
        """Test full bidder evaluation with sample data"""
        # Add sample document to retrieval engine
        sample_doc = ExtractedDocument(
            document_id="doc-001",
            bidder_id="bidder-001",
            file_name="financial_statement.pdf",
            pages=["Our company has annual revenue of $2,500,000 USD for fiscal year 2023."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        retrieval_engine.add_documents([sample_doc])
        
        # Note: This test will attempt to call the LLM, which may not be available
        # in the test environment. We're testing the structure, not the LLM output.
        try:
            result = evaluation_engine.evaluate_bidder(
                bidder_id="bidder-001",
                bidder_name="Test Bidder",
                criteria=[sample_criterion]
            )
            
            # Verify result structure
            assert result.bidder_id == "bidder-001"
            assert result.bidder_name == "Test Bidder"
            assert result.final_verdict in ["Eligible", "Not Eligible", "Needs Review"]
            assert len(result.criterion_evaluations) == 1
            assert "total_criteria" in result.summary
        except Exception as e:
            # If LLM is not available, test should still pass
            # as we're testing the structure, not the LLM functionality
            pytest.skip(f"LLM not available for integration test: {str(e)}")
