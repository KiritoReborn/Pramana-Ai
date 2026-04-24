"""Evaluation engine for criterion-by-criterion bidder evaluation"""

import logging
from typing import List, Dict, Type, Union
from datetime import datetime
from pydantic import BaseModel

from src.models.schemas import (
    EligibilityCriterion,
    EvidenceChunk,
    FinancialEvidence,
    TechnicalEvidence,
    ComplianceEvidence,
    DocumentationEvidence,
    Decision,
    CriterionEvaluation,
    EvaluationResult
)
from src.engines.retrieval_engine import RetrievalEngine
from src.engines.llm_extractor import LLMExtractor
from src.engines.prompts import get_evidence_prompt
from src.config import RetrievalConfig, SystemConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationEngine:
    """
    Evaluation engine that orchestrates criterion-by-criterion evaluation.
    
    This class coordinates the retrieval of relevant evidence chunks from FAISS
    and extraction of structured evidence using the LLM, creating complete
    explainability records for each criterion.
    
    Implements Requirements 4.1, 4.6, 3.6
    """
    
    def __init__(self, retrieval_engine: RetrievalEngine, llm_extractor: LLMExtractor):
        """
        Initialize evaluation engine with retrieval and extraction components.
        
        Args:
            retrieval_engine: FAISS-based retrieval engine for semantic search
            llm_extractor: LLM extractor for structured evidence extraction
        """
        self.retrieval_engine = retrieval_engine
        self.llm_extractor = llm_extractor
        logger.info("Initialized EvaluationEngine")
    
    def evaluate_bidder(
        self,
        bidder_id: str,
        bidder_name: str,
        criteria: List[EligibilityCriterion]
    ) -> EvaluationResult:
        """
        Orchestrate full evaluation of a bidder against all criteria.
        
        Evaluates each criterion independently and aggregates results into
        a complete evaluation result with summary statistics.
        
        Implements Requirement 4.1: Process each criterion independently
        
        Args:
            bidder_id: Unique identifier for the bidder
            bidder_name: Name of the bidder
            criteria: List of eligibility criteria to evaluate against
            
        Returns:
            EvaluationResult with all criterion evaluations and final verdict
        """
        logger.info(f"Starting evaluation for bidder: {bidder_name} (ID: {bidder_id})")
        
        criterion_evaluations = []
        
        # Evaluate each criterion independently
        for criterion in criteria:
            logger.info(f"Evaluating criterion: {criterion.id} - {criterion.description[:50]}...")
            
            try:
                evaluation = self.evaluate_criterion(criterion, bidder_id)
                criterion_evaluations.append(evaluation)
            except Exception as e:
                logger.error(f"Failed to evaluate criterion {criterion.id}: {str(e)}")
                # Create a fallback evaluation with "Needs Review" verdict
                evaluation = self._create_fallback_evaluation(criterion, str(e))
                criterion_evaluations.append(evaluation)
        
        # Compute final verdict and summary
        final_verdict, summary = self._compute_final_verdict(criterion_evaluations)
        
        # Create evaluation result
        result = EvaluationResult(
            bidder_id=bidder_id,
            bidder_name=bidder_name,
            final_verdict=final_verdict,
            criterion_evaluations=criterion_evaluations,
            summary=summary,
            timestamp=datetime.now(),
            system_version=SystemConfig.VERSION
        )
        
        logger.info(
            f"Completed evaluation for {bidder_name}. "
            f"Final verdict: {final_verdict}. "
            f"Summary: {summary}"
        )
        
        return result
    
    def evaluate_criterion(
        self,
        criterion: EligibilityCriterion,
        bidder_id: str
    ) -> CriterionEvaluation:
        """
        Evaluate a single criterion for a bidder.
        
        Process:
        1. Retrieve top 5 relevant chunks from FAISS using criterion description
        2. Extract structured evidence using LLM with category-specific schema
        3. Create explainability record with evidence, sources, and confidence
        4. Handle "Evidence Not Found" case (all confidence <= 0.5)
        
        Implements Requirements 4.1, 4.6, 3.6
        
        Args:
            criterion: Eligibility criterion to evaluate
            bidder_id: Unique identifier for the bidder
            
        Returns:
            CriterionEvaluation with evidence, decision, and explainability record
        """
        logger.info(f"Evaluating criterion {criterion.id} for bidder {bidder_id}")
        
        # Step 1: Retrieve top 5 relevant chunks from FAISS
        evidence_chunks = self.retrieval_engine.retrieve(
            query=criterion.description,
            top_k=RetrievalConfig.TOP_K
        )
        
        logger.info(f"Retrieved {len(evidence_chunks)} evidence chunks for criterion {criterion.id}")
        
        # Step 2: Check for "Evidence Not Found" case
        # Requirement 3.6: When all confidence <= 0.5, mark as "Evidence Not Found"
        if self._is_evidence_not_found(evidence_chunks):
            logger.warning(
                f"Evidence not found for criterion {criterion.id}. "
                f"All chunks have confidence <= {RetrievalConfig.MIN_CONFIDENCE}"
            )
            return self._create_evidence_not_found_evaluation(criterion, evidence_chunks)
        
        # Step 3: Extract structured evidence using LLM with category-specific schema
        extracted_evidence = self._extract_evidence(criterion, evidence_chunks)
        
        # Step 4: Create preliminary decision (will be finalized by Rule Engine)
        decision = self._create_preliminary_decision(criterion, extracted_evidence)
        
        # Step 5: Create explainability record
        explainability_record = self._create_explainability_record(
            criterion=criterion,
            evidence_chunks=evidence_chunks,
            extracted_evidence=extracted_evidence,
            decision=decision
        )
        
        # Create criterion evaluation
        evaluation = CriterionEvaluation(
            criterion=criterion,
            evidence_chunks=evidence_chunks,
            extracted_evidence=extracted_evidence,
            decision=decision,
            explainability_record=explainability_record
        )
        
        logger.info(
            f"Completed evaluation for criterion {criterion.id}. "
            f"Decision: {decision.verdict}"
        )
        
        return evaluation
    
    def _is_evidence_not_found(self, evidence_chunks: List[EvidenceChunk]) -> bool:
        """
        Check if evidence is not found (all confidence <= 0.5).
        
        Implements Requirement 3.6: Handle "Evidence Not Found" case
        
        Args:
            evidence_chunks: List of retrieved evidence chunks
            
        Returns:
            True if all chunks have confidence <= 0.5 or no chunks found
        """
        if not evidence_chunks:
            return True
        
        return all(
            chunk.confidence <= RetrievalConfig.MIN_CONFIDENCE
            for chunk in evidence_chunks
        )
    
    def _extract_evidence(
        self,
        criterion: EligibilityCriterion,
        evidence_chunks: List[EvidenceChunk]
    ) -> Union[FinancialEvidence, TechnicalEvidence, ComplianceEvidence, DocumentationEvidence]:
        """
        Extract structured evidence using LLM with category-specific schema.
        
        Implements Requirements 4.2, 4.3, 4.4, 4.5
        
        Args:
            criterion: Eligibility criterion being evaluated
            evidence_chunks: Retrieved evidence chunks from FAISS
            
        Returns:
            Type-specific evidence object (Financial, Technical, Compliance, or Documentation)
        """
        # Get category-specific schema and prompt
        evidence_schema = self._get_evidence_schema(criterion.category)
        prompt_template = get_evidence_prompt(criterion.category)
        
        # Combine chunks into text for LLM
        chunks_text = "\n\n---\n\n".join([
            f"[Page {chunk.page_number}, {chunk.source_file}]\n{chunk.text}"
            for chunk in evidence_chunks
        ])
        
        # Extract structured evidence with validation
        extracted_evidence = self.llm_extractor.extract_with_validation(
            text=chunks_text,
            schema=evidence_schema,
            prompt_template=prompt_template,
            criterion_description=criterion.description,
            chunks=chunks_text
        )
        
        return extracted_evidence
    
    def _get_evidence_schema(
        self,
        category: str
    ) -> Type[Union[FinancialEvidence, TechnicalEvidence, ComplianceEvidence, DocumentationEvidence]]:
        """
        Get the appropriate evidence schema for a criterion category.
        
        Args:
            category: Criterion category
            
        Returns:
            Pydantic schema class for the category
        """
        schema_map = {
            "Financial": FinancialEvidence,
            "Technical": TechnicalEvidence,
            "Compliance": ComplianceEvidence,
            "Documentation": DocumentationEvidence
        }
        
        return schema_map[category]
    
    def _create_preliminary_decision(
        self,
        criterion: EligibilityCriterion,
        extracted_evidence: BaseModel
    ) -> Decision:
        """
        Create preliminary decision based on extracted evidence.
        
        Note: This is a placeholder decision. The actual decision logic
        will be implemented by the Rule Engine in a later task.
        
        For now, we check confidence and flag low-confidence extractions
        for review (Requirement 5.4).
        
        Args:
            criterion: Eligibility criterion
            extracted_evidence: Extracted evidence object
            
        Returns:
            Preliminary Decision object
        """
        confidence = extracted_evidence.confidence
        
        # Requirement 5.4: Low confidence triggers review
        if confidence < RetrievalConfig.LOW_CONFIDENCE_THRESHOLD:
            verdict = "Needs Review"
            rationale = (
                f"Evidence confidence ({confidence:.2f}) is below threshold "
                f"({RetrievalConfig.LOW_CONFIDENCE_THRESHOLD}). Manual review required."
            )
            rule_applied = "LowConfidenceReviewRule"
        else:
            # Placeholder verdict - will be determined by Rule Engine
            verdict = "Needs Review"
            rationale = "Awaiting Rule Engine evaluation"
            rule_applied = "PreliminaryEvaluation"
        
        return Decision(
            criterion_id=criterion.id,
            verdict=verdict,
            rule_applied=rule_applied,
            comparison=None,
            rationale=rationale,
            timestamp=datetime.now()
        )
    
    def _create_explainability_record(
        self,
        criterion: EligibilityCriterion,
        evidence_chunks: List[EvidenceChunk],
        extracted_evidence: BaseModel,
        decision: Decision
    ) -> Dict:
        """
        Create explainability record with complete audit trail.
        
        Implements Requirements 4.6, 10.2, 10.7
        
        Args:
            criterion: Eligibility criterion
            evidence_chunks: Retrieved evidence chunks
            extracted_evidence: Extracted structured evidence
            decision: Decision object
            
        Returns:
            Dictionary containing complete explainability information
        """
        return {
            "criterion_id": criterion.id,
            "criterion_description": criterion.description,
            "criterion_category": criterion.category,
            "criterion_priority": criterion.priority,
            "evidence_sources": [
                {
                    "text": chunk.text,
                    "source_file": chunk.source_file,
                    "page_number": chunk.page_number,
                    "retrieval_confidence": chunk.confidence
                }
                for chunk in evidence_chunks
            ],
            "extracted_values": extracted_evidence.dict(),
            "extraction_confidence": extracted_evidence.confidence,
            "decision_verdict": decision.verdict,
            "decision_rule": decision.rule_applied,
            "decision_rationale": decision.rationale,
            "decision_timestamp": decision.timestamp.isoformat(),
            "traceability": {
                "source_documents": list(set(chunk.source_file for chunk in evidence_chunks)),
                "source_pages": list(set(chunk.page_number for chunk in evidence_chunks)),
                "extraction_method": "LLM with Pydantic validation",
                "decision_method": "Rule Engine (deterministic)"
            }
        }
    
    def _create_evidence_not_found_evaluation(
        self,
        criterion: EligibilityCriterion,
        evidence_chunks: List[EvidenceChunk]
    ) -> CriterionEvaluation:
        """
        Create evaluation for "Evidence Not Found" case.
        
        Implements Requirement 3.6: Handle case where all confidence <= 0.5
        
        Args:
            criterion: Eligibility criterion
            evidence_chunks: Retrieved evidence chunks (all low confidence)
            
        Returns:
            CriterionEvaluation with "Needs Review" verdict
        """
        # Create safe default evidence based on category
        evidence_schema = self._get_evidence_schema(criterion.category)
        
        # Create evidence with confidence 0.0
        if criterion.category == "Financial":
            extracted_evidence = FinancialEvidence(
                value=0.0,
                currency="UNKNOWN",
                context="Evidence not found - all retrieved chunks have low confidence",
                source_page=0,
                confidence=0.0
            )
        elif criterion.category == "Technical":
            extracted_evidence = TechnicalEvidence(
                specification="Evidence not found - all retrieved chunks have low confidence",
                certifications=[],
                capabilities=[],
                source_page=0,
                confidence=0.0
            )
        elif criterion.category == "Compliance":
            extracted_evidence = ComplianceEvidence(
                regulation="UNKNOWN",
                compliance_status="Evidence not found - all retrieved chunks have low confidence",
                source_page=0,
                confidence=0.0
            )
        else:  # Documentation
            extracted_evidence = DocumentationEvidence(
                document_present=False,
                document_type="UNKNOWN",
                completeness="Evidence not found - all retrieved chunks have low confidence",
                source_page=0,
                confidence=0.0
            )
        
        # Create decision
        decision = Decision(
            criterion_id=criterion.id,
            verdict="Needs Review",
            rule_applied="EvidenceNotFoundRule",
            comparison=None,
            rationale=(
                "No relevant evidence found with sufficient confidence. "
                f"All retrieved chunks have confidence <= {RetrievalConfig.MIN_CONFIDENCE}. "
                "Manual review required."
            ),
            timestamp=datetime.now()
        )
        
        # Create explainability record
        explainability_record = {
            "criterion_id": criterion.id,
            "criterion_description": criterion.description,
            "criterion_category": criterion.category,
            "criterion_priority": criterion.priority,
            "evidence_sources": [
                {
                    "text": chunk.text,
                    "source_file": chunk.source_file,
                    "page_number": chunk.page_number,
                    "retrieval_confidence": chunk.confidence
                }
                for chunk in evidence_chunks
            ],
            "extracted_values": extracted_evidence.dict(),
            "extraction_confidence": 0.0,
            "decision_verdict": "Needs Review",
            "decision_rule": "EvidenceNotFoundRule",
            "decision_rationale": decision.rationale,
            "decision_timestamp": decision.timestamp.isoformat(),
            "evidence_not_found": True,
            "traceability": {
                "source_documents": [],
                "source_pages": [],
                "extraction_method": "N/A - Evidence not found",
                "decision_method": "Rule Engine (deterministic)"
            }
        }
        
        return CriterionEvaluation(
            criterion=criterion,
            evidence_chunks=evidence_chunks,
            extracted_evidence=extracted_evidence,
            decision=decision,
            explainability_record=explainability_record
        )
    
    def _create_fallback_evaluation(
        self,
        criterion: EligibilityCriterion,
        error_message: str
    ) -> CriterionEvaluation:
        """
        Create fallback evaluation when criterion evaluation fails.
        
        Args:
            criterion: Eligibility criterion
            error_message: Error message describing the failure
            
        Returns:
            CriterionEvaluation with "Needs Review" verdict
        """
        # Create safe default evidence
        if criterion.category == "Financial":
            extracted_evidence = FinancialEvidence(
                value=0.0,
                currency="UNKNOWN",
                context=f"Evaluation failed: {error_message}",
                source_page=0,
                confidence=0.0
            )
        elif criterion.category == "Technical":
            extracted_evidence = TechnicalEvidence(
                specification=f"Evaluation failed: {error_message}",
                certifications=[],
                capabilities=[],
                source_page=0,
                confidence=0.0
            )
        elif criterion.category == "Compliance":
            extracted_evidence = ComplianceEvidence(
                regulation="UNKNOWN",
                compliance_status=f"Evaluation failed: {error_message}",
                source_page=0,
                confidence=0.0
            )
        else:  # Documentation
            extracted_evidence = DocumentationEvidence(
                document_present=False,
                document_type="UNKNOWN",
                completeness=f"Evaluation failed: {error_message}",
                source_page=0,
                confidence=0.0
            )
        
        # Create decision
        decision = Decision(
            criterion_id=criterion.id,
            verdict="Needs Review",
            rule_applied="EvaluationFailureRule",
            comparison=None,
            rationale=f"Evaluation failed with error: {error_message}. Manual review required.",
            timestamp=datetime.now()
        )
        
        # Create explainability record
        explainability_record = {
            "criterion_id": criterion.id,
            "criterion_description": criterion.description,
            "criterion_category": criterion.category,
            "criterion_priority": criterion.priority,
            "evidence_sources": [],
            "extracted_values": extracted_evidence.dict(),
            "extraction_confidence": 0.0,
            "decision_verdict": "Needs Review",
            "decision_rule": "EvaluationFailureRule",
            "decision_rationale": decision.rationale,
            "decision_timestamp": decision.timestamp.isoformat(),
            "evaluation_failed": True,
            "error_message": error_message,
            "traceability": {
                "source_documents": [],
                "source_pages": [],
                "extraction_method": "N/A - Evaluation failed",
                "decision_method": "Rule Engine (deterministic)"
            }
        }
        
        return CriterionEvaluation(
            criterion=criterion,
            evidence_chunks=[],
            extracted_evidence=extracted_evidence,
            decision=decision,
            explainability_record=explainability_record
        )
    
    def _compute_final_verdict(
        self,
        criterion_evaluations: List[CriterionEvaluation]
    ) -> tuple[str, Dict]:
        """
        Compute final verdict and summary from criterion evaluations.
        
        Note: This is a placeholder implementation. The actual verdict logic
        will be implemented by the Rule Engine in a later task.
        
        For now, we use simple logic:
        - If any mandatory criterion is "Not Satisfied" -> "Not Eligible"
        - If all mandatory criteria are "Satisfied" -> "Eligible"
        - Otherwise -> "Needs Review"
        
        Args:
            criterion_evaluations: List of criterion evaluations
            
        Returns:
            Tuple of (final_verdict, summary_dict)
        """
        satisfied_count = 0
        not_satisfied_count = 0
        needs_review_count = 0
        
        mandatory_satisfied = 0
        mandatory_not_satisfied = 0
        mandatory_needs_review = 0
        
        for evaluation in criterion_evaluations:
            verdict = evaluation.decision.verdict
            is_mandatory = evaluation.criterion.priority == "Mandatory"
            
            if verdict == "Satisfied":
                satisfied_count += 1
                if is_mandatory:
                    mandatory_satisfied += 1
            elif verdict == "Not Satisfied":
                not_satisfied_count += 1
                if is_mandatory:
                    mandatory_not_satisfied += 1
            else:  # Needs Review
                needs_review_count += 1
                if is_mandatory:
                    mandatory_needs_review += 1
        
        # Compute final verdict
        if mandatory_not_satisfied > 0:
            final_verdict = "Not Eligible"
        elif mandatory_needs_review > 0:
            final_verdict = "Needs Review"
        else:
            # All mandatory criteria satisfied (or no mandatory criteria)
            final_verdict = "Eligible"
        
        # Create summary
        summary = {
            "total_criteria": len(criterion_evaluations),
            "satisfied": satisfied_count,
            "not_satisfied": not_satisfied_count,
            "needs_review": needs_review_count,
            "mandatory_satisfied": mandatory_satisfied,
            "mandatory_not_satisfied": mandatory_not_satisfied,
            "mandatory_needs_review": mandatory_needs_review
        }
        
        return final_verdict, summary
