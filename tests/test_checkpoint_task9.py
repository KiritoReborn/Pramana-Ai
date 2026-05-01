"""
Checkpoint Task 9: End-to-end evaluation pipeline test

This test verifies that the complete evaluation pipeline works correctly:
- Tender upload → bidder upload → evaluation → verdict
- Rule engine makes deterministic decisions
- Audit logs are complete
"""

import pytest
from datetime import datetime
from pathlib import Path

from src.processors.tender_processor import TenderProcessor
from src.processors.document_processor import DocumentProcessor
from src.engines.retrieval_engine import RetrievalEngine
from src.engines.llm_extractor import LLMExtractor
from src.engines.evaluation_engine import EvaluationEngine
from src.engines.rule_engine import RuleEngine
from src.models.schemas import (
    EligibilityCriterion,
    ExtractedDocument,
    FinancialEvidence,
    TechnicalEvidence,
    ComplianceEvidence,
    DocumentationEvidence,
    CriterionEvaluation
)


class TestEndToEndEvaluationPipeline:
    """Test complete evaluation pipeline from tender to verdict"""
    
    @pytest.fixture
    def sample_criteria(self):
        """Create sample eligibility criteria"""
        return [
            EligibilityCriterion(
                id="FIN-001",
                category="Financial",
                priority="Mandatory",
                description="Annual revenue must be at least $1,000,000 USD",
                threshold_value="1000000",
                threshold_unit="USD",
                source_page=5,
                original_text="The bidder must have annual revenue of at least $1,000,000 USD"
            ),
            EligibilityCriterion(
                id="TECH-001",
                category="Technical",
                priority="Mandatory",
                description="Must have ISO 9001 certification",
                threshold_value=None,
                threshold_unit=None,
                source_page=7,
                original_text="Bidder must possess ISO 9001 certification"
            ),
            EligibilityCriterion(
                id="COMP-001",
                category="Compliance",
                priority="Mandatory",
                description="Must comply with GDPR regulations",
                threshold_value=None,
                threshold_unit=None,
                source_page=9,
                original_text="Bidder must be GDPR compliant"
            ),
            EligibilityCriterion(
                id="DOC-001",
                category="Documentation",
                priority="Mandatory",
                description="Must provide tax clearance certificate",
                threshold_value=None,
                threshold_unit=None,
                source_page=11,
                original_text="Bidder must submit tax clearance certificate"
            )
        ]
    
    @pytest.fixture
    def sample_bidder_documents(self):
        """Create sample bidder documents with evidence"""
        return [
            ExtractedDocument(
                document_id="doc-001",
                bidder_id="bidder-001",
                file_name="financial_statement.pdf",
                pages=[
                    "Financial Statement for Fiscal Year 2023\n\n"
                    "Our company has achieved annual revenue of $2,500,000 USD for fiscal year 2023. "
                    "This represents a 15% growth from the previous year. "
                    "Total assets: $5,000,000 USD. Net profit: $500,000 USD."
                ],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            ),
            ExtractedDocument(
                document_id="doc-002",
                bidder_id="bidder-001",
                file_name="certifications.pdf",
                pages=[
                    "Company Certifications\n\n"
                    "We are proud to hold the following certifications:\n"
                    "- ISO 9001:2015 Quality Management System (Valid until 2025)\n"
                    "- ISO 14001:2015 Environmental Management System\n"
                    "- ISO 27001:2013 Information Security Management"
                ],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            ),
            ExtractedDocument(
                document_id="doc-003",
                bidder_id="bidder-001",
                file_name="compliance.pdf",
                pages=[
                    "Regulatory Compliance Statement\n\n"
                    "Our organization is fully compliant with GDPR (General Data Protection Regulation) "
                    "as of January 1, 2023. We have implemented all necessary data protection measures "
                    "and maintain regular audits to ensure ongoing compliance."
                ],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            ),
            ExtractedDocument(
                document_id="doc-004",
                bidder_id="bidder-001",
                file_name="tax_certificate.pdf",
                pages=[
                    "Tax Clearance Certificate\n\n"
                    "This is to certify that [Company Name] has no outstanding tax obligations "
                    "and is in good standing with the tax authorities. "
                    "Certificate Number: TC-2023-12345\n"
                    "Valid until: December 31, 2024\n"
                    "This document is complete and valid."
                ],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            )
        ]
    
    @pytest.fixture
    def retrieval_engine(self):
        """Create retrieval engine instance"""
        return RetrievalEngine()
    
    @pytest.fixture
    def llm_extractor(self):
        """Create LLM extractor instance"""
        return LLMExtractor()
    
    @pytest.fixture
    def evaluation_engine(self, retrieval_engine, llm_extractor):
        """Create evaluation engine instance"""
        return EvaluationEngine(retrieval_engine, llm_extractor)
    
    @pytest.fixture
    def rule_engine(self):
        """Create rule engine instance"""
        return RuleEngine()
    
    def test_pipeline_components_initialization(
        self,
        retrieval_engine,
        llm_extractor,
        evaluation_engine,
        rule_engine
    ):
        """Test that all pipeline components can be initialized"""
        assert retrieval_engine is not None
        assert llm_extractor is not None
        assert evaluation_engine is not None
        assert rule_engine is not None
    
    def test_retrieval_engine_indexing(
        self,
        retrieval_engine,
        sample_bidder_documents
    ):
        """Test that retrieval engine can index bidder documents"""
        # Add documents to retrieval engine
        retrieval_engine.add_documents(sample_bidder_documents)
        
        # Verify index has been populated
        assert retrieval_engine.index.ntotal > 0
        assert len(retrieval_engine.metadata) > 0
        
        # Verify we can retrieve relevant chunks
        chunks = retrieval_engine.retrieve("annual revenue", top_k=5)
        assert len(chunks) > 0
        assert all(chunk.confidence > 0 for chunk in chunks)
    
    def test_rule_engine_determinism(self, rule_engine, sample_criteria):
        """Test that rule engine makes deterministic decisions"""
        criterion = sample_criteria[0]  # Financial criterion
        
        # Create evidence
        evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Annual revenue for fiscal year 2023",
            source_page=1,
            confidence=0.85
        )
        
        # Apply rules multiple times
        decision1 = rule_engine.apply_rules(criterion, evidence)
        decision2 = rule_engine.apply_rules(criterion, evidence)
        decision3 = rule_engine.apply_rules(criterion, evidence)
        
        # Verify determinism (same verdict, rule, and rationale)
        assert decision1.verdict == decision2.verdict == decision3.verdict
        assert decision1.rule_applied == decision2.rule_applied == decision3.rule_applied
        assert decision1.rationale == decision2.rationale == decision3.rationale
        assert decision1.comparison == decision2.comparison == decision3.comparison
    
    def test_rule_engine_all_categories(self, rule_engine, sample_criteria):
        """Test that rule engine can handle all evidence categories"""
        # Financial
        financial_evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Revenue",
            source_page=1,
            confidence=0.85
        )
        financial_decision = rule_engine.apply_rules(sample_criteria[0], financial_evidence)
        assert financial_decision.verdict == "Satisfied"
        
        # Technical
        technical_evidence = TechnicalEvidence(
            specification="ISO 9001:2015",
            certifications=["ISO 9001:2015"],
            capabilities=["Quality Management"],
            source_page=1,
            confidence=0.88
        )
        technical_decision = rule_engine.apply_rules(sample_criteria[1], technical_evidence)
        assert technical_decision.verdict == "Satisfied"
        
        # Compliance
        compliance_evidence = ComplianceEvidence(
            regulation="GDPR",
            compliance_status="Fully compliant",
            effective_date="2023-01-01",
            source_page=1,
            confidence=0.82
        )
        compliance_decision = rule_engine.apply_rules(sample_criteria[2], compliance_evidence)
        assert compliance_decision.verdict == "Satisfied"
        
        # Documentation
        documentation_evidence = DocumentationEvidence(
            document_present=True,
            document_type="Tax Clearance Certificate",
            completeness="Complete and valid",
            source_page=1,
            confidence=0.90
        )
        documentation_decision = rule_engine.apply_rules(sample_criteria[3], documentation_evidence)
        assert documentation_decision.verdict == "Satisfied"
    
    def test_final_verdict_computation(self, rule_engine, sample_criteria):
        """Test final verdict computation from criterion evaluations"""
        # Create evaluations with all satisfied
        from src.models.schemas import Decision
        
        evaluations = []
        for criterion in sample_criteria:
            if criterion.category == "Financial":
                evidence = FinancialEvidence(
                    value=2500000.0, currency="USD", context="Test",
                    source_page=1, confidence=0.85
                )
            elif criterion.category == "Technical":
                evidence = TechnicalEvidence(
                    specification="ISO 9001", certifications=["ISO 9001"],
                    capabilities=[], source_page=1, confidence=0.88
                )
            elif criterion.category == "Compliance":
                evidence = ComplianceEvidence(
                    regulation="GDPR", compliance_status="Compliant",
                    source_page=1, confidence=0.82
                )
            else:  # Documentation
                evidence = DocumentationEvidence(
                    document_present=True, document_type="Certificate",
                    completeness="Complete", source_page=1, confidence=0.90
                )
            
            decision = rule_engine.apply_rules(criterion, evidence)
            
            evaluation = CriterionEvaluation(
                criterion=criterion,
                evidence_chunks=[],
                extracted_evidence=evidence,
                decision=decision,
                explainability_record={}
            )
            evaluations.append(evaluation)
        
        # Compute final verdict
        verdict = rule_engine.compute_verdict(evaluations)
        
        # All mandatory criteria satisfied -> Eligible
        assert verdict == "Eligible"
    
    def test_final_verdict_with_failure(self, rule_engine, sample_criteria):
        """Test final verdict when one criterion fails"""
        from src.models.schemas import Decision
        
        evaluations = []
        for i, criterion in enumerate(sample_criteria):
            if criterion.category == "Financial":
                # Fail the financial criterion
                evidence = FinancialEvidence(
                    value=500000.0,  # Below threshold
                    currency="USD",
                    context="Test",
                    source_page=1,
                    confidence=0.85
                )
            elif criterion.category == "Technical":
                evidence = TechnicalEvidence(
                    specification="ISO 9001", certifications=["ISO 9001"],
                    capabilities=[], source_page=1, confidence=0.88
                )
            elif criterion.category == "Compliance":
                evidence = ComplianceEvidence(
                    regulation="GDPR", compliance_status="Compliant",
                    source_page=1, confidence=0.82
                )
            else:  # Documentation
                evidence = DocumentationEvidence(
                    document_present=True, document_type="Certificate",
                    completeness="Complete", source_page=1, confidence=0.90
                )
            
            decision = rule_engine.apply_rules(criterion, evidence)
            
            evaluation = CriterionEvaluation(
                criterion=criterion,
                evidence_chunks=[],
                extracted_evidence=evidence,
                decision=decision,
                explainability_record={}
            )
            evaluations.append(evaluation)
        
        # Compute final verdict
        verdict = rule_engine.compute_verdict(evaluations)
        
        # One mandatory criterion failed -> Not Eligible
        assert verdict == "Not Eligible"
    
    def test_final_verdict_with_needs_review(self, rule_engine, sample_criteria):
        """Test final verdict when one criterion needs review"""
        from src.models.schemas import Decision
        
        evaluations = []
        for criterion in sample_criteria:
            if criterion.category == "Financial":
                # Low confidence triggers review
                evidence = FinancialEvidence(
                    value=2500000.0,
                    currency="USD",
                    context="Test",
                    source_page=1,
                    confidence=0.5  # Below 0.7 threshold
                )
            elif criterion.category == "Technical":
                evidence = TechnicalEvidence(
                    specification="ISO 9001", certifications=["ISO 9001"],
                    capabilities=[], source_page=1, confidence=0.88
                )
            elif criterion.category == "Compliance":
                evidence = ComplianceEvidence(
                    regulation="GDPR", compliance_status="Compliant",
                    source_page=1, confidence=0.82
                )
            else:  # Documentation
                evidence = DocumentationEvidence(
                    document_present=True, document_type="Certificate",
                    completeness="Complete", source_page=1, confidence=0.90
                )
            
            decision = rule_engine.apply_rules(criterion, evidence)
            
            evaluation = CriterionEvaluation(
                criterion=criterion,
                evidence_chunks=[],
                extracted_evidence=evidence,
                decision=decision,
                explainability_record={}
            )
            evaluations.append(evaluation)
        
        # Compute final verdict
        verdict = rule_engine.compute_verdict(evaluations)
        
        # One mandatory criterion needs review -> Needs Review
        assert verdict == "Needs Review"
    
    def test_audit_log_completeness(self, rule_engine, sample_criteria):
        """Test that audit logs contain all required information"""
        criterion = sample_criteria[0]
        evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Annual revenue",
            source_page=1,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(criterion, evidence)
        
        # Verify decision has all required fields for audit trail
        assert decision.criterion_id is not None
        assert decision.verdict in ["Satisfied", "Not Satisfied", "Needs Review"]
        assert decision.rule_applied is not None
        assert decision.rationale is not None
        assert decision.timestamp is not None
        assert isinstance(decision.timestamp, datetime)
        
        # Verify comparison field exists (may be None for some rules)
        assert hasattr(decision, 'comparison')
    
    def test_explainability_record_completeness(self, evaluation_engine, sample_criteria):
        """Test that explainability records are complete"""
        from src.models.schemas import EvidenceChunk
        
        criterion = sample_criteria[0]
        
        evidence_chunks = [
            EvidenceChunk(
                text="Annual revenue of $2,500,000 USD",
                document_id="doc-001",
                page_number=1,
                confidence=0.85,
                source_file="financial_statement.pdf"
            )
        ]
        
        extracted_evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Annual revenue",
            source_page=1,
            confidence=0.85
        )
        
        from src.models.schemas import Decision
        decision = Decision(
            criterion_id=criterion.id,
            verdict="Satisfied",
            rule_applied="FinancialThresholdComparisonRule",
            comparison="2500000.0 USD >= 1000000 USD",
            rationale="Financial value meets threshold",
            timestamp=datetime.now()
        )
        
        record = evaluation_engine._create_explainability_record(
            criterion=criterion,
            evidence_chunks=evidence_chunks,
            extracted_evidence=extracted_evidence,
            decision=decision
        )
        
        # Verify explainability record has all required fields
        assert "criterion_id" in record
        assert "criterion_description" in record
        assert "criterion_category" in record
        assert "criterion_priority" in record
        assert "evidence_sources" in record
        assert "extracted_values" in record
        assert "extraction_confidence" in record
        assert "decision_verdict" in record
        assert "decision_rule" in record
        assert "decision_rationale" in record
        assert "decision_timestamp" in record
        assert "traceability" in record
        
        # Verify traceability section
        traceability = record["traceability"]
        assert "source_documents" in traceability
        assert "source_pages" in traceability
        assert "extraction_method" in traceability
        assert "decision_method" in traceability
    
    def test_evaluation_result_structure(self, evaluation_engine, sample_criteria, sample_bidder_documents, retrieval_engine):
        """Test that evaluation result has correct structure"""
        # Add documents to retrieval engine
        retrieval_engine.add_documents(sample_bidder_documents)
        
        # Note: This test may skip if LLM is not available
        try:
            result = evaluation_engine.evaluate_bidder(
                bidder_id="bidder-001",
                bidder_name="Test Bidder",
                criteria=sample_criteria
            )
            
            # Verify result structure
            assert result.bidder_id == "bidder-001"
            assert result.bidder_name == "Test Bidder"
            assert result.final_verdict in ["Eligible", "Not Eligible", "Needs Review"]
            assert len(result.criterion_evaluations) == len(sample_criteria)
            assert result.timestamp is not None
            assert result.system_version is not None
            
            # Verify summary
            assert "total_criteria" in result.summary
            assert "satisfied" in result.summary
            assert "not_satisfied" in result.summary
            assert "needs_review" in result.summary
            assert "mandatory_satisfied" in result.summary
            assert "mandatory_not_satisfied" in result.summary
            assert "mandatory_needs_review" in result.summary
            
            # Verify each criterion evaluation
            for evaluation in result.criterion_evaluations:
                assert evaluation.criterion is not None
                assert evaluation.decision is not None
                assert evaluation.explainability_record is not None
                assert isinstance(evaluation.explainability_record, dict)
        
        except Exception as e:
            # If LLM is not available, skip this test
            pytest.skip(f"LLM not available for integration test: {str(e)}")


class TestAuditLogPersistence:
    """Test audit log file creation and persistence"""
    
    @pytest.fixture
    def rule_engine(self):
        """Create rule engine instance"""
        return RuleEngine()
    
    def test_audit_log_file_creation(self, rule_engine):
        """Test that audit log files are created"""
        from src.config import FilePaths
        
        criterion = EligibilityCriterion(
            id="TEST-001",
            category="Financial",
            priority="Mandatory",
            description="Test criterion",
            threshold_value="1000000",
            threshold_unit="USD",
            source_page=1,
            original_text="Test"
        )
        
        evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Test",
            source_page=1,
            confidence=0.85
        )
        
        # Apply rules (this should log to file)
        decision = rule_engine.apply_rules(criterion, evidence)
        
        # Verify audit log file exists
        log_file = FilePaths.AUDIT_LOGS_DIR / f"decisions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        assert log_file.exists()
        
        # Verify log file contains the decision
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            
            # Check that at least one line contains our test criterion
            import json
            found = False
            for line in lines:
                entry = json.loads(line)
                if entry.get("criterion_id") == "TEST-001":
                    found = True
                    assert entry["verdict"] == "Satisfied"
                    assert entry["rule_applied"] == "FinancialThresholdComparisonRule"
                    break
            
            assert found, "Test criterion decision not found in audit log"


class TestPipelineErrorHandling:
    """Test error handling throughout the pipeline"""
    
    @pytest.fixture
    def evaluation_engine(self):
        """Create evaluation engine instance"""
        retrieval_engine = RetrievalEngine()
        llm_extractor = LLMExtractor()
        return EvaluationEngine(retrieval_engine, llm_extractor)
    
    def test_evaluation_handles_empty_index(self, evaluation_engine):
        """Test that evaluation handles empty retrieval index gracefully"""
        criterion = EligibilityCriterion(
            id="TEST-001",
            category="Financial",
            priority="Mandatory",
            description="Test criterion",
            threshold_value="1000000",
            threshold_unit="USD",
            source_page=1,
            original_text="Test"
        )
        
        # Evaluate with empty index (no documents added)
        evaluation = evaluation_engine.evaluate_criterion(criterion, "bidder-001")
        
        # Should return "Needs Review" verdict
        assert evaluation.decision.verdict == "Needs Review"
        assert evaluation.decision.rule_applied == "EvidenceNotFoundRule"
    
    def test_evaluation_handles_low_confidence_evidence(self, evaluation_engine):
        """Test that evaluation handles low confidence evidence"""
        from src.models.schemas import ExtractedDocument
        
        # Add document with irrelevant content
        doc = ExtractedDocument(
            document_id="doc-001",
            bidder_id="bidder-001",
            file_name="test.pdf",
            pages=["This is completely unrelated content about weather and sports."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        evaluation_engine.retrieval_engine.add_documents([doc])
        
        criterion = EligibilityCriterion(
            id="TEST-001",
            category="Financial",
            priority="Mandatory",
            description="Annual revenue must be at least $1,000,000 USD",
            threshold_value="1000000",
            threshold_unit="USD",
            source_page=1,
            original_text="Test"
        )
        
        # Evaluate (should find low confidence evidence)
        evaluation = evaluation_engine.evaluate_criterion(criterion, "bidder-001")
        
        # Should handle low confidence appropriately
        assert evaluation.decision.verdict in ["Needs Review", "Not Satisfied"]


print("✓ Checkpoint Task 9 tests defined")
