"""Rule engine for deterministic eligibility decisions"""

import logging
import json
from typing import Union, Dict, Any
from datetime import datetime
from pathlib import Path

from src.models.schemas import (
    EligibilityCriterion,
    FinancialEvidence,
    TechnicalEvidence,
    ComplianceEvidence,
    DocumentationEvidence,
    Decision
)
from src.config import RetrievalConfig, FilePaths

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Rule engine that makes deterministic eligibility decisions.
    
    This class implements the core principle: AI extracts, Python decides.
    All final eligibility determinations are made using deterministic
    Python-based logic, not AI judgment.
    
    Implements Requirements 5.1, 5.2, 5.3, 5.4, 5.7
    """
    
    def __init__(self):
        """Initialize rule engine."""
        logger.info("Initialized RuleEngine")
    
    def apply_rules(
        self,
        criterion: EligibilityCriterion,
        evidence: Union[FinancialEvidence, TechnicalEvidence, ComplianceEvidence, DocumentationEvidence]
    ) -> Decision:
        """
        Apply deterministic rules to make eligibility decision for a single criterion.
        
        This method routes to category-specific rule sets and ensures all decisions
        are made using deterministic logic, not AI judgment.
        
        Decision Logic:
        1. Check confidence score - if < 0.7, assign "Needs Review"
        2. Route to category-specific rule set (Financial, Technical, Compliance, Documentation)
        3. Apply threshold comparison logic for mandatory criteria
        4. Log all decisions with rule_applied, values_compared, rationale
        
        Implements Requirements 5.1, 5.2, 5.3, 5.4, 5.7
        
        Args:
            criterion: Eligibility criterion being evaluated
            evidence: Extracted evidence (type-specific)
            
        Returns:
            Decision object with verdict, rule applied, and rationale
        """
        logger.info(f"Applying rules for criterion {criterion.id} ({criterion.category})")
        
        # Requirement 5.4: Low confidence triggers review
        if evidence.confidence < RetrievalConfig.LOW_CONFIDENCE_THRESHOLD:
            decision = Decision(
                criterion_id=criterion.id,
                verdict="Needs Review",
                rule_applied="LowConfidenceReviewRule",
                comparison=f"Confidence {evidence.confidence:.2f} < {RetrievalConfig.LOW_CONFIDENCE_THRESHOLD}",
                rationale=(
                    f"Evidence confidence ({evidence.confidence:.2f}) is below threshold "
                    f"({RetrievalConfig.LOW_CONFIDENCE_THRESHOLD}). Manual review required."
                ),
                timestamp=datetime.now()
            )
            self.log_decision(decision)
            return decision
        
        # Route to category-specific rule set
        if criterion.category == "Financial":
            decision = self._apply_financial_rules(criterion, evidence)
        elif criterion.category == "Technical":
            decision = self._apply_technical_rules(criterion, evidence)
        elif criterion.category == "Compliance":
            decision = self._apply_compliance_rules(criterion, evidence)
        elif criterion.category == "Documentation":
            decision = self._apply_documentation_rules(criterion, evidence)
        else:
            # Fallback for unknown category
            decision = Decision(
                criterion_id=criterion.id,
                verdict="Needs Review",
                rule_applied="UnknownCategoryRule",
                comparison=None,
                rationale=f"Unknown criterion category: {criterion.category}. Manual review required.",
                timestamp=datetime.now()
            )
        
        # Log decision (Requirement 5.7)
        self.log_decision(decision)
        
        return decision
    
    def _apply_financial_rules(
        self,
        criterion: EligibilityCriterion,
        evidence: FinancialEvidence
    ) -> Decision:
        """
        Apply rules for Financial criteria.
        
        Financial criteria typically involve threshold comparisons:
        - Minimum turnover requirements
        - Minimum capital requirements
        - Financial ratios
        
        Implements Requirement 5.3: Threshold comparison logic
        
        Args:
            criterion: Financial eligibility criterion
            evidence: Extracted financial evidence
            
        Returns:
            Decision object
        """
        logger.info(f"Applying financial rules for criterion {criterion.id}")
        
        # Check if threshold is specified
        if criterion.threshold_value is None:
            # No threshold specified - check if evidence exists
            if evidence.value > 0:
                return Decision(
                    criterion_id=criterion.id,
                    verdict="Satisfied",
                    rule_applied="FinancialEvidencePresenceRule",
                    comparison=f"Value: {evidence.value} {evidence.currency}",
                    rationale=(
                        f"Financial evidence found: {evidence.value} {evidence.currency}. "
                        f"No threshold specified, evidence presence satisfies criterion."
                    ),
                    timestamp=datetime.now()
                )
            else:
                return Decision(
                    criterion_id=criterion.id,
                    verdict="Not Satisfied",
                    rule_applied="FinancialEvidenceAbsenceRule",
                    comparison=f"Value: {evidence.value}",
                    rationale="No valid financial evidence found (value = 0).",
                    timestamp=datetime.now()
                )
        
        # Parse threshold value
        try:
            threshold = float(criterion.threshold_value)
        except (ValueError, TypeError):
            return Decision(
                criterion_id=criterion.id,
                verdict="Needs Review",
                rule_applied="FinancialThresholdParseErrorRule",
                comparison=f"Threshold: {criterion.threshold_value}, Value: {evidence.value}",
                rationale=(
                    f"Could not parse threshold value '{criterion.threshold_value}'. "
                    "Manual review required."
                ),
                timestamp=datetime.now()
            )
        
        # Perform threshold comparison (Requirement 5.3)
        if evidence.value >= threshold:
            return Decision(
                criterion_id=criterion.id,
                verdict="Satisfied",
                rule_applied="FinancialThresholdComparisonRule",
                comparison=f"{evidence.value} {evidence.currency} >= {threshold} {criterion.threshold_unit or evidence.currency}",
                rationale=(
                    f"Financial value {evidence.value} {evidence.currency} meets or exceeds "
                    f"threshold {threshold} {criterion.threshold_unit or evidence.currency}."
                ),
                timestamp=datetime.now()
            )
        else:
            return Decision(
                criterion_id=criterion.id,
                verdict="Not Satisfied",
                rule_applied="FinancialThresholdComparisonRule",
                comparison=f"{evidence.value} {evidence.currency} < {threshold} {criterion.threshold_unit or evidence.currency}",
                rationale=(
                    f"Financial value {evidence.value} {evidence.currency} is below "
                    f"threshold {threshold} {criterion.threshold_unit or evidence.currency}."
                ),
                timestamp=datetime.now()
            )
    
    def _apply_technical_rules(
        self,
        criterion: EligibilityCriterion,
        evidence: TechnicalEvidence
    ) -> Decision:
        """
        Apply rules for Technical criteria.
        
        Technical criteria typically involve:
        - Presence of required certifications
        - Presence of required capabilities
        - Matching specifications
        
        Args:
            criterion: Technical eligibility criterion
            evidence: Extracted technical evidence
            
        Returns:
            Decision object
        """
        logger.info(f"Applying technical rules for criterion {criterion.id}")
        
        # Check if specification is present and non-empty
        if not evidence.specification or evidence.specification.strip() == "":
            return Decision(
                criterion_id=criterion.id,
                verdict="Not Satisfied",
                rule_applied="TechnicalSpecificationAbsenceRule",
                comparison="Specification: empty",
                rationale="No technical specification found in evidence.",
                timestamp=datetime.now()
            )
        
        # Check for threshold value (e.g., minimum number of certifications)
        if criterion.threshold_value:
            try:
                required_count = int(criterion.threshold_value)
                actual_count = len(evidence.certifications) + len(evidence.capabilities)
                
                if actual_count >= required_count:
                    return Decision(
                        criterion_id=criterion.id,
                        verdict="Satisfied",
                        rule_applied="TechnicalCountThresholdRule",
                        comparison=f"{actual_count} items >= {required_count} required",
                        rationale=(
                            f"Found {len(evidence.certifications)} certifications and "
                            f"{len(evidence.capabilities)} capabilities, meeting threshold of {required_count}."
                        ),
                        timestamp=datetime.now()
                    )
                else:
                    return Decision(
                        criterion_id=criterion.id,
                        verdict="Not Satisfied",
                        rule_applied="TechnicalCountThresholdRule",
                        comparison=f"{actual_count} items < {required_count} required",
                        rationale=(
                            f"Found only {len(evidence.certifications)} certifications and "
                            f"{len(evidence.capabilities)} capabilities, below threshold of {required_count}."
                        ),
                        timestamp=datetime.now()
                    )
            except (ValueError, TypeError):
                # Threshold not a number, fall through to presence check
                pass
        
        # Default: Check if technical evidence is present
        has_evidence = (
            evidence.specification.strip() != "" or
            len(evidence.certifications) > 0 or
            len(evidence.capabilities) > 0
        )
        
        if has_evidence:
            return Decision(
                criterion_id=criterion.id,
                verdict="Satisfied",
                rule_applied="TechnicalEvidencePresenceRule",
                comparison=(
                    f"Specification: present, "
                    f"Certifications: {len(evidence.certifications)}, "
                    f"Capabilities: {len(evidence.capabilities)}"
                ),
                rationale=(
                    f"Technical evidence found: specification present, "
                    f"{len(evidence.certifications)} certifications, "
                    f"{len(evidence.capabilities)} capabilities."
                ),
                timestamp=datetime.now()
            )
        else:
            return Decision(
                criterion_id=criterion.id,
                verdict="Not Satisfied",
                rule_applied="TechnicalEvidenceAbsenceRule",
                comparison="No technical evidence found",
                rationale="No technical specification, certifications, or capabilities found.",
                timestamp=datetime.now()
            )
    
    def _apply_compliance_rules(
        self,
        criterion: EligibilityCriterion,
        evidence: ComplianceEvidence
    ) -> Decision:
        """
        Apply rules for Compliance criteria.
        
        Compliance criteria typically involve:
        - Presence of compliance statements
        - Verification of regulatory compliance
        - Date validity checks
        
        Args:
            criterion: Compliance eligibility criterion
            evidence: Extracted compliance evidence
            
        Returns:
            Decision object
        """
        logger.info(f"Applying compliance rules for criterion {criterion.id}")
        
        # Check if regulation is identified
        if not evidence.regulation or evidence.regulation.strip() == "" or evidence.regulation == "UNKNOWN":
            return Decision(
                criterion_id=criterion.id,
                verdict="Not Satisfied",
                rule_applied="ComplianceRegulationAbsenceRule",
                comparison="Regulation: not identified",
                rationale="No regulation or standard identified in evidence.",
                timestamp=datetime.now()
            )
        
        # Check compliance status
        if not evidence.compliance_status or evidence.compliance_status.strip() == "":
            return Decision(
                criterion_id=criterion.id,
                verdict="Not Satisfied",
                rule_applied="ComplianceStatusAbsenceRule",
                comparison="Compliance status: empty",
                rationale="No compliance status statement found.",
                timestamp=datetime.now()
            )
        
        # Check for negative compliance indicators
        negative_indicators = ["non-compliant", "not compliant", "fails", "does not meet", "violation"]
        status_lower = evidence.compliance_status.lower()
        
        if any(indicator in status_lower for indicator in negative_indicators):
            return Decision(
                criterion_id=criterion.id,
                verdict="Not Satisfied",
                rule_applied="ComplianceNegativeIndicatorRule",
                comparison=f"Status: {evidence.compliance_status}",
                rationale=(
                    f"Compliance status indicates non-compliance: {evidence.compliance_status}"
                ),
                timestamp=datetime.now()
            )
        
        # Positive compliance found
        return Decision(
            criterion_id=criterion.id,
            verdict="Satisfied",
            rule_applied="ComplianceEvidencePresenceRule",
            comparison=f"Regulation: {evidence.regulation}, Status: {evidence.compliance_status}",
            rationale=(
                f"Compliance evidence found for {evidence.regulation}. "
                f"Status: {evidence.compliance_status}."
            ),
            timestamp=datetime.now()
        )
    
    def _apply_documentation_rules(
        self,
        criterion: EligibilityCriterion,
        evidence: DocumentationEvidence
    ) -> Decision:
        """
        Apply rules for Documentation criteria.
        
        Documentation criteria typically involve:
        - Presence of required documents
        - Completeness of documents
        
        Args:
            criterion: Documentation eligibility criterion
            evidence: Extracted documentation evidence
            
        Returns:
            Decision object
        """
        logger.info(f"Applying documentation rules for criterion {criterion.id}")
        
        # Check if document is present
        if not evidence.document_present:
            return Decision(
                criterion_id=criterion.id,
                verdict="Not Satisfied",
                rule_applied="DocumentationAbsenceRule",
                comparison="Document present: False",
                rationale=f"Required document not found: {evidence.document_type}",
                timestamp=datetime.now()
            )
        
        # Check completeness
        completeness_lower = evidence.completeness.lower()
        
        # Check for negative completeness indicators
        negative_indicators = ["incomplete", "missing", "partial", "not found"]
        if any(indicator in completeness_lower for indicator in negative_indicators):
            return Decision(
                criterion_id=criterion.id,
                verdict="Not Satisfied",
                rule_applied="DocumentationIncompletenessRule",
                comparison=f"Completeness: {evidence.completeness}",
                rationale=(
                    f"Document {evidence.document_type} is incomplete: {evidence.completeness}"
                ),
                timestamp=datetime.now()
            )
        
        # Document present and complete
        return Decision(
            criterion_id=criterion.id,
            verdict="Satisfied",
            rule_applied="DocumentationPresenceRule",
            comparison=f"Document: {evidence.document_type}, Present: True, Completeness: {evidence.completeness}",
            rationale=(
                f"Required document {evidence.document_type} is present and complete. "
                f"Completeness: {evidence.completeness}."
            ),
            timestamp=datetime.now()
        )
    
    def log_decision(self, decision: Decision) -> None:
        """
        Log decision to audit trail.
        
        Implements Requirement 5.7: Log all decisions with rule_applied,
        values_compared, and rationale.
        
        Args:
            decision: Decision object to log
        """
        log_entry = {
            "timestamp": decision.timestamp.isoformat(),
            "criterion_id": decision.criterion_id,
            "verdict": decision.verdict,
            "rule_applied": decision.rule_applied,
            "comparison": decision.comparison,
            "rationale": decision.rationale
        }
        
        # Log to console
        logger.info(
            f"Decision logged - Criterion: {decision.criterion_id}, "
            f"Verdict: {decision.verdict}, Rule: {decision.rule_applied}"
        )
        
        # Log to file
        log_file = FilePaths.AUDIT_LOGS_DIR / f"decisions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write decision to audit log: {str(e)}")
