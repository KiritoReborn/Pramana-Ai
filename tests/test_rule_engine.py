"""Tests for rule engine"""

import pytest
from datetime import datetime
from src.engines.rule_engine import RuleEngine
from src.models.schemas import (
    EligibilityCriterion,
    FinancialEvidence,
    TechnicalEvidence,
    ComplianceEvidence,
    DocumentationEvidence,
    Decision
)


class TestRuleEngine:
    """Test suite for RuleEngine"""
    
    @pytest.fixture
    def rule_engine(self):
        """Create a rule engine instance"""
        return RuleEngine()
    
    @pytest.fixture
    def financial_criterion(self):
        """Create a sample financial criterion"""
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
    def technical_criterion(self):
        """Create a sample technical criterion"""
        return EligibilityCriterion(
            id="TECH-001",
            category="Technical",
            priority="Mandatory",
            description="Must have ISO 9001 certification",
            threshold_value=None,
            threshold_unit=None,
            source_page=7,
            original_text="Bidder must possess ISO 9001 certification"
        )
    
    @pytest.fixture
    def compliance_criterion(self):
        """Create a sample compliance criterion"""
        return EligibilityCriterion(
            id="COMP-001",
            category="Compliance",
            priority="Mandatory",
            description="Must comply with GDPR regulations",
            threshold_value=None,
            threshold_unit=None,
            source_page=9,
            original_text="Bidder must be GDPR compliant"
        )
    
    @pytest.fixture
    def documentation_criterion(self):
        """Create a sample documentation criterion"""
        return EligibilityCriterion(
            id="DOC-001",
            category="Documentation",
            priority="Mandatory",
            description="Must provide tax clearance certificate",
            threshold_value=None,
            threshold_unit=None,
            source_page=11,
            original_text="Bidder must submit tax clearance certificate"
        )
    
    def test_rule_engine_initialization(self, rule_engine):
        """Test that rule engine initializes correctly"""
        assert rule_engine is not None
    
    def test_low_confidence_triggers_review(self, rule_engine, financial_criterion):
        """Test that low confidence evidence triggers 'Needs Review' verdict"""
        low_confidence_evidence = FinancialEvidence(
            value=2000000.0,
            currency="USD",
            context="Annual revenue",
            source_page=3,
            confidence=0.5  # Below 0.7 threshold
        )
        
        decision = rule_engine.apply_rules(financial_criterion, low_confidence_evidence)
        
        assert decision.verdict == "Needs Review"
        assert decision.rule_applied == "LowConfidenceReviewRule"
        assert "0.50" in decision.comparison
        assert "0.7" in decision.comparison
    
    def test_financial_threshold_satisfied(self, rule_engine, financial_criterion):
        """Test financial criterion satisfied when value meets threshold"""
        evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Annual revenue for fiscal year 2023",
            source_page=3,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(financial_criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "FinancialThresholdComparisonRule"
        assert "2500000.0" in decision.comparison
        assert ">=" in decision.comparison
    
    def test_financial_threshold_not_satisfied(self, rule_engine, financial_criterion):
        """Test financial criterion not satisfied when value below threshold"""
        evidence = FinancialEvidence(
            value=500000.0,
            currency="USD",
            context="Annual revenue",
            source_page=3,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(financial_criterion, evidence)
        
        assert decision.verdict == "Not Satisfied"
        assert decision.rule_applied == "FinancialThresholdComparisonRule"
        assert "500000.0" in decision.comparison
        assert "<" in decision.comparison
    
    def test_financial_no_threshold_with_evidence(self, rule_engine):
        """Test financial criterion with no threshold but evidence present"""
        criterion = EligibilityCriterion(
            id="FIN-002",
            category="Financial",
            priority="Mandatory",
            description="Must provide financial statements",
            threshold_value=None,
            threshold_unit=None,
            source_page=5,
            original_text="Bidder must provide financial statements"
        )
        
        evidence = FinancialEvidence(
            value=1000000.0,
            currency="USD",
            context="Financial statement",
            source_page=3,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "FinancialEvidencePresenceRule"
    
    def test_technical_evidence_present(self, rule_engine, technical_criterion):
        """Test technical criterion satisfied when evidence present"""
        evidence = TechnicalEvidence(
            specification="ISO 9001:2015 Quality Management System",
            certifications=["ISO 9001:2015"],
            capabilities=["Quality Management"],
            source_page=4,
            confidence=0.88
        )
        
        decision = rule_engine.apply_rules(technical_criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "TechnicalEvidencePresenceRule"
    
    def test_technical_evidence_absent(self, rule_engine, technical_criterion):
        """Test technical criterion not satisfied when evidence absent"""
        evidence = TechnicalEvidence(
            specification="",
            certifications=[],
            capabilities=[],
            source_page=4,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(technical_criterion, evidence)
        
        assert decision.verdict == "Not Satisfied"
        assert decision.rule_applied == "TechnicalSpecificationAbsenceRule"
    
    def test_technical_count_threshold(self, rule_engine):
        """Test technical criterion with count threshold"""
        criterion = EligibilityCriterion(
            id="TECH-002",
            category="Technical",
            priority="Mandatory",
            description="Must have at least 3 certifications",
            threshold_value="3",
            threshold_unit="certifications",
            source_page=7,
            original_text="Bidder must have at least 3 certifications"
        )
        
        evidence = TechnicalEvidence(
            specification="Multiple certifications",
            certifications=["ISO 9001", "ISO 14001"],
            capabilities=["Quality", "Environment"],
            source_page=4,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "TechnicalCountThresholdRule"
        assert "4 items >= 3" in decision.comparison
    
    def test_compliance_evidence_present(self, rule_engine, compliance_criterion):
        """Test compliance criterion satisfied when evidence present"""
        evidence = ComplianceEvidence(
            regulation="GDPR",
            compliance_status="Fully compliant with GDPR requirements",
            effective_date="2023-01-01",
            source_page=6,
            confidence=0.82
        )
        
        decision = rule_engine.apply_rules(compliance_criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "ComplianceEvidencePresenceRule"
    
    def test_compliance_negative_indicator(self, rule_engine, compliance_criterion):
        """Test compliance criterion not satisfied with negative indicator"""
        evidence = ComplianceEvidence(
            regulation="GDPR",
            compliance_status="Not compliant with GDPR",
            effective_date=None,
            source_page=6,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(compliance_criterion, evidence)
        
        assert decision.verdict == "Not Satisfied"
        assert decision.rule_applied == "ComplianceNegativeIndicatorRule"
    
    def test_compliance_regulation_absent(self, rule_engine, compliance_criterion):
        """Test compliance criterion not satisfied when regulation not identified"""
        evidence = ComplianceEvidence(
            regulation="UNKNOWN",
            compliance_status="Some status",
            effective_date=None,
            source_page=6,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(compliance_criterion, evidence)
        
        assert decision.verdict == "Not Satisfied"
        assert decision.rule_applied == "ComplianceRegulationAbsenceRule"
    
    def test_documentation_present_and_complete(self, rule_engine, documentation_criterion):
        """Test documentation criterion satisfied when document present and complete"""
        evidence = DocumentationEvidence(
            document_present=True,
            document_type="Tax Clearance Certificate",
            completeness="Complete and valid",
            source_page=8,
            confidence=0.90
        )
        
        decision = rule_engine.apply_rules(documentation_criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "DocumentationPresenceRule"
    
    def test_documentation_absent(self, rule_engine, documentation_criterion):
        """Test documentation criterion not satisfied when document absent"""
        evidence = DocumentationEvidence(
            document_present=False,
            document_type="Tax Clearance Certificate",
            completeness="Not found",
            source_page=8,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(documentation_criterion, evidence)
        
        assert decision.verdict == "Not Satisfied"
        assert decision.rule_applied == "DocumentationAbsenceRule"
    
    def test_documentation_incomplete(self, rule_engine, documentation_criterion):
        """Test documentation criterion not satisfied when document incomplete"""
        evidence = DocumentationEvidence(
            document_present=True,
            document_type="Tax Clearance Certificate",
            completeness="Incomplete - missing signature",
            source_page=8,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(documentation_criterion, evidence)
        
        assert decision.verdict == "Not Satisfied"
        assert decision.rule_applied == "DocumentationIncompletenessRule"
    
    def test_decision_logging(self, rule_engine, financial_criterion):
        """Test that decisions are logged"""
        evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Annual revenue",
            source_page=3,
            confidence=0.85
        )
        
        decision = rule_engine.apply_rules(financial_criterion, evidence)
        
        # Verify decision object has all required fields
        assert decision.criterion_id == "FIN-001"
        assert decision.verdict in ["Satisfied", "Not Satisfied", "Needs Review"]
        assert decision.rule_applied is not None
        assert decision.rationale is not None
        assert decision.timestamp is not None
    
    def test_determinism(self, rule_engine, financial_criterion):
        """Test that rule engine is deterministic - same input produces same output"""
        evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Annual revenue",
            source_page=3,
            confidence=0.85
        )
        
        decision1 = rule_engine.apply_rules(financial_criterion, evidence)
        decision2 = rule_engine.apply_rules(financial_criterion, evidence)
        
        # Verify same verdict and rule applied (timestamps will differ)
        assert decision1.verdict == decision2.verdict
        assert decision1.rule_applied == decision2.rule_applied
        assert decision1.rationale == decision2.rationale
        assert decision1.comparison == decision2.comparison


class TestComputeVerdict:
    """Test suite for compute_verdict method"""
    
    @pytest.fixture
    def rule_engine(self):
        """Create a rule engine instance"""
        return RuleEngine()
    
    def create_criterion_evaluation(
        self,
        criterion_id: str,
        priority: str,
        verdict: str
    ):
        """Helper to create a CriterionEvaluation for testing"""
        from src.models.schemas import CriterionEvaluation, EvidenceChunk
        
        criterion = EligibilityCriterion(
            id=criterion_id,
            category="Financial",
            priority=priority,
            description=f"Test criterion {criterion_id}",
            threshold_value=None,
            threshold_unit=None,
            source_page=1,
            original_text=f"Test criterion {criterion_id}"
        )
        
        evidence = FinancialEvidence(
            value=1000000.0,
            currency="USD",
            context="Test context",
            source_page=1,
            confidence=0.85
        )
        
        decision = Decision(
            criterion_id=criterion_id,
            verdict=verdict,
            rule_applied="TestRule",
            comparison="Test comparison",
            rationale="Test rationale",
            timestamp=datetime.now()
        )
        
        return CriterionEvaluation(
            criterion=criterion,
            evidence_chunks=[],
            extracted_evidence=evidence,
            decision=decision,
            explainability_record={}
        )
    
    def test_all_mandatory_satisfied_returns_eligible(self, rule_engine):
        """Test that all mandatory criteria satisfied returns 'Eligible'"""
        evaluations = [
            self.create_criterion_evaluation("M1", "Mandatory", "Satisfied"),
            self.create_criterion_evaluation("M2", "Mandatory", "Satisfied"),
            self.create_criterion_evaluation("M3", "Mandatory", "Satisfied"),
        ]
        
        verdict = rule_engine.compute_verdict(evaluations)
        
        assert verdict == "Eligible"
    
    def test_any_mandatory_not_satisfied_returns_not_eligible(self, rule_engine):
        """Test that any mandatory criterion not satisfied returns 'Not Eligible'"""
        evaluations = [
            self.create_criterion_evaluation("M1", "Mandatory", "Satisfied"),
            self.create_criterion_evaluation("M2", "Mandatory", "Not Satisfied"),
            self.create_criterion_evaluation("M3", "Mandatory", "Satisfied"),
        ]
        
        verdict = rule_engine.compute_verdict(evaluations)
        
        assert verdict == "Not Eligible"
    
    def test_any_mandatory_needs_review_returns_needs_review(self, rule_engine):
        """Test that any mandatory criterion needs review returns 'Needs Review'"""
        evaluations = [
            self.create_criterion_evaluation("M1", "Mandatory", "Satisfied"),
            self.create_criterion_evaluation("M2", "Mandatory", "Needs Review"),
            self.create_criterion_evaluation("M3", "Mandatory", "Satisfied"),
        ]
        
        verdict = rule_engine.compute_verdict(evaluations)
        
        assert verdict == "Needs Review"
    
    def test_not_satisfied_takes_precedence_over_needs_review(self, rule_engine):
        """Test that 'Not Satisfied' takes precedence over 'Needs Review'"""
        evaluations = [
            self.create_criterion_evaluation("M1", "Mandatory", "Not Satisfied"),
            self.create_criterion_evaluation("M2", "Mandatory", "Needs Review"),
            self.create_criterion_evaluation("M3", "Mandatory", "Satisfied"),
        ]
        
        verdict = rule_engine.compute_verdict(evaluations)
        
        assert verdict == "Not Eligible"
    
    def test_optional_criteria_do_not_affect_verdict(self, rule_engine):
        """Test that optional criteria do not affect the final verdict"""
        evaluations = [
            self.create_criterion_evaluation("M1", "Mandatory", "Satisfied"),
            self.create_criterion_evaluation("M2", "Mandatory", "Satisfied"),
            self.create_criterion_evaluation("O1", "Optional", "Not Satisfied"),
            self.create_criterion_evaluation("O2", "Optional", "Needs Review"),
        ]
        
        verdict = rule_engine.compute_verdict(evaluations)
        
        assert verdict == "Eligible"
    
    def test_no_mandatory_criteria_returns_needs_review(self, rule_engine):
        """Test that no mandatory criteria returns 'Needs Review'"""
        evaluations = [
            self.create_criterion_evaluation("O1", "Optional", "Satisfied"),
            self.create_criterion_evaluation("O2", "Optional", "Satisfied"),
        ]
        
        verdict = rule_engine.compute_verdict(evaluations)
        
        assert verdict == "Needs Review"
    
    def test_empty_evaluations_returns_needs_review(self, rule_engine):
        """Test that empty evaluations list returns 'Needs Review'"""
        evaluations = []
        
        verdict = rule_engine.compute_verdict(evaluations)
        
        assert verdict == "Needs Review"
    
    def test_mixed_mandatory_and_optional_with_all_mandatory_satisfied(self, rule_engine):
        """Test mixed mandatory and optional criteria with all mandatory satisfied"""
        evaluations = [
            self.create_criterion_evaluation("M1", "Mandatory", "Satisfied"),
            self.create_criterion_evaluation("O1", "Optional", "Not Satisfied"),
            self.create_criterion_evaluation("M2", "Mandatory", "Satisfied"),
            self.create_criterion_evaluation("O2", "Optional", "Needs Review"),
        ]
        
        verdict = rule_engine.compute_verdict(evaluations)
        
        assert verdict == "Eligible"
