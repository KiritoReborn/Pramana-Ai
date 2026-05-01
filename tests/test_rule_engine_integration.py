"""Integration tests for rule engine with evaluation engine"""

import pytest
from src.engines.rule_engine import RuleEngine
from src.models.schemas import (
    EligibilityCriterion,
    FinancialEvidence,
    TechnicalEvidence,
    ComplianceEvidence,
    DocumentationEvidence
)


class TestRuleEngineIntegration:
    """Integration tests for RuleEngine"""
    
    @pytest.fixture
    def rule_engine(self):
        """Create a rule engine instance"""
        return RuleEngine()
    
    def test_end_to_end_financial_evaluation(self, rule_engine):
        """Test end-to-end financial criterion evaluation"""
        # Create criterion
        criterion = EligibilityCriterion(
            id="FIN-001",
            category="Financial",
            priority="Mandatory",
            description="Annual revenue must be at least $1,000,000 USD",
            threshold_value="1000000",
            threshold_unit="USD",
            source_page=5,
            original_text="The bidder must have annual revenue of at least $1,000,000 USD"
        )
        
        # Create evidence (satisfies criterion)
        evidence = FinancialEvidence(
            value=2500000.0,
            currency="USD",
            context="Annual revenue for fiscal year 2023",
            source_page=3,
            confidence=0.85
        )
        
        # Apply rules
        decision = rule_engine.apply_rules(criterion, evidence)
        
        # Verify decision
        assert decision.criterion_id == "FIN-001"
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "FinancialThresholdComparisonRule"
        assert decision.comparison is not None
        assert "2500000.0" in decision.comparison
        assert decision.rationale is not None
        assert decision.timestamp is not None
    
    def test_end_to_end_technical_evaluation(self, rule_engine):
        """Test end-to-end technical criterion evaluation"""
        criterion = EligibilityCriterion(
            id="TECH-001",
            category="Technical",
            priority="Mandatory",
            description="Must have ISO 9001 certification",
            threshold_value=None,
            threshold_unit=None,
            source_page=7,
            original_text="Bidder must possess ISO 9001 certification"
        )
        
        evidence = TechnicalEvidence(
            specification="ISO 9001:2015 Quality Management System",
            certifications=["ISO 9001:2015"],
            capabilities=["Quality Management"],
            source_page=4,
            confidence=0.88
        )
        
        decision = rule_engine.apply_rules(criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "TechnicalEvidencePresenceRule"
    
    def test_end_to_end_compliance_evaluation(self, rule_engine):
        """Test end-to-end compliance criterion evaluation"""
        criterion = EligibilityCriterion(
            id="COMP-001",
            category="Compliance",
            priority="Mandatory",
            description="Must comply with GDPR regulations",
            threshold_value=None,
            threshold_unit=None,
            source_page=9,
            original_text="Bidder must be GDPR compliant"
        )
        
        evidence = ComplianceEvidence(
            regulation="GDPR",
            compliance_status="Fully compliant with GDPR requirements",
            effective_date="2023-01-01",
            source_page=6,
            confidence=0.82
        )
        
        decision = rule_engine.apply_rules(criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "ComplianceEvidencePresenceRule"
    
    def test_end_to_end_documentation_evaluation(self, rule_engine):
        """Test end-to-end documentation criterion evaluation"""
        criterion = EligibilityCriterion(
            id="DOC-001",
            category="Documentation",
            priority="Mandatory",
            description="Must provide tax clearance certificate",
            threshold_value=None,
            threshold_unit=None,
            source_page=11,
            original_text="Bidder must submit tax clearance certificate"
        )
        
        evidence = DocumentationEvidence(
            document_present=True,
            document_type="Tax Clearance Certificate",
            completeness="Complete and valid",
            source_page=8,
            confidence=0.90
        )
        
        decision = rule_engine.apply_rules(criterion, evidence)
        
        assert decision.verdict == "Satisfied"
        assert decision.rule_applied == "DocumentationPresenceRule"
    
    def test_multiple_criteria_evaluation(self, rule_engine):
        """Test evaluation of multiple criteria"""
        criteria = [
            EligibilityCriterion(
                id="FIN-001",
                category="Financial",
                priority="Mandatory",
                description="Annual revenue >= $1M",
                threshold_value="1000000",
                threshold_unit="USD",
                source_page=5,
                original_text="Revenue requirement"
            ),
            EligibilityCriterion(
                id="TECH-001",
                category="Technical",
                priority="Mandatory",
                description="ISO 9001 certification",
                threshold_value=None,
                threshold_unit=None,
                source_page=7,
                original_text="Certification requirement"
            )
        ]
        
        evidences = [
            FinancialEvidence(
                value=2500000.0,
                currency="USD",
                context="Revenue",
                source_page=3,
                confidence=0.85
            ),
            TechnicalEvidence(
                specification="ISO 9001:2015",
                certifications=["ISO 9001:2015"],
                capabilities=[],
                source_page=4,
                confidence=0.88
            )
        ]
        
        decisions = []
        for criterion, evidence in zip(criteria, evidences):
            decision = rule_engine.apply_rules(criterion, evidence)
            decisions.append(decision)
        
        # Verify all decisions
        assert len(decisions) == 2
        assert all(d.verdict == "Satisfied" for d in decisions)
        assert decisions[0].rule_applied == "FinancialThresholdComparisonRule"
        assert decisions[1].rule_applied == "TechnicalEvidencePresenceRule"
    
    def test_mixed_verdicts(self, rule_engine):
        """Test evaluation with mixed verdicts (satisfied, not satisfied, needs review)"""
        criteria = [
            EligibilityCriterion(
                id="FIN-001",
                category="Financial",
                priority="Mandatory",
                description="Revenue >= $1M",
                threshold_value="1000000",
                threshold_unit="USD",
                source_page=5,
                original_text="Revenue requirement"
            ),
            EligibilityCriterion(
                id="TECH-001",
                category="Technical",
                priority="Mandatory",
                description="ISO certification",
                threshold_value=None,
                threshold_unit=None,
                source_page=7,
                original_text="Certification requirement"
            ),
            EligibilityCriterion(
                id="DOC-001",
                category="Documentation",
                priority="Mandatory",
                description="Tax certificate",
                threshold_value=None,
                threshold_unit=None,
                source_page=9,
                original_text="Document requirement"
            )
        ]
        
        evidences = [
            FinancialEvidence(
                value=2500000.0,
                currency="USD",
                context="Revenue",
                source_page=3,
                confidence=0.85
            ),
            TechnicalEvidence(
                specification="",
                certifications=[],
                capabilities=[],
                source_page=4,
                confidence=0.88
            ),
            DocumentationEvidence(
                document_present=True,
                document_type="Tax Certificate",
                completeness="Complete",
                source_page=8,
                confidence=0.60  # Low confidence
            )
        ]
        
        decisions = []
        for criterion, evidence in zip(criteria, evidences):
            decision = rule_engine.apply_rules(criterion, evidence)
            decisions.append(decision)
        
        # Verify mixed verdicts
        assert decisions[0].verdict == "Satisfied"
        assert decisions[1].verdict == "Not Satisfied"
        assert decisions[2].verdict == "Needs Review"
