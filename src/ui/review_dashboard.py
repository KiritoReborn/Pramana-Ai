"""Human review dashboard for manual verification and overrides"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.models.schemas import (
    EvaluationResult,
    CriterionEvaluation,
    ManualOverride,
    Decision
)
from src.engines.rule_engine import RuleEngine
from src.config import RetrievalConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def render_review_dashboard(evaluation_results: Dict[str, EvaluationResult]):
    """
    Render human review dashboard for flagged evaluations.
    
    Implements Requirements 6.1, 6.2, 6.3
    
    Args:
        evaluation_results: Dictionary of bidder_id -> EvaluationResult
    """
    st.header("🔍 Human Review Dashboard")
    
    # Filter bidders that need review
    needs_review_results = {
        bidder_id: result
        for bidder_id, result in evaluation_results.items()
        if result.final_verdict == "Needs Review"
    }
    
    if not needs_review_results:
        st.success("✅ No evaluations require manual review!")
        return
    
    st.warning(f"⚠️ {len(needs_review_results)} bidder(s) require manual review")
    
    # Display each bidder that needs review
    for bidder_id, result in needs_review_results.items():
        render_bidder_review(bidder_id, result)


def render_bidder_review(bidder_id: str, result: EvaluationResult):
    """
    Render review interface for a single bidder.
    
    Implements Requirements 6.2, 6.3, 6.4
    
    Args:
        bidder_id: Unique bidder identifier
        result: Evaluation result for the bidder
    """
    with st.expander(f"📋 {result.bidder_name} - Review Required", expanded=True):
        st.markdown(f"**Bidder ID:** {bidder_id}")
        st.markdown(f"**Current Verdict:** {result.final_verdict}")
        st.markdown(f"**Evaluation Time:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary
        st.markdown("### Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Satisfied", result.summary['satisfied'])
        with col2:
            st.metric("Not Satisfied", result.summary['not_satisfied'])
        with col3:
            st.metric("Needs Review", result.summary['needs_review'])
        
        st.markdown("---")
        
        # Filter criteria that need review
        flagged_evaluations = [
            eval for eval in result.criterion_evaluations
            if eval.decision.verdict == "Needs Review"
        ]
        
        st.markdown(f"### Flagged Criteria ({len(flagged_evaluations)})")
        
        for eval in flagged_evaluations:
            render_criterion_review(bidder_id, eval, result)


def render_criterion_review(
    bidder_id: str,
    eval: CriterionEvaluation,
    result: EvaluationResult
):
    """
    Render review interface for a single criterion.
    
    Implements Requirements 6.2, 6.3, 6.4, 6.5, 6.6
    
    Args:
        bidder_id: Unique bidder identifier
        eval: Criterion evaluation to review
        result: Complete evaluation result
    """
    criterion = eval.criterion
    decision = eval.decision
    evidence = eval.extracted_evidence
    
    # Check if low confidence
    is_low_confidence = evidence.confidence < RetrievalConfig.LOW_CONFIDENCE_THRESHOLD
    
    with st.container():
        st.markdown(f"#### {criterion.id} - {criterion.description[:80]}...")
        
        # Highlight low confidence
        if is_low_confidence:
            st.markdown(
                f'<div style="background-color: #fff3cd; border-left: 4px solid #ffc107; '
                f'padding: 0.5rem; margin: 0.5rem 0;">'
                f'⚠️ Low Confidence: {evidence.confidence:.2f} '
                f'(below threshold {RetrievalConfig.LOW_CONFIDENCE_THRESHOLD})'
                f'</div>',
                unsafe_allow_html=True
            )
        
        # Create columns for criterion details and override controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display complete explainability record
            render_explainability_record(eval)
        
        with col2:
            # Manual override controls
            render_override_controls(bidder_id, criterion.id, eval, result)
        
        st.markdown("---")


def render_explainability_record(eval: CriterionEvaluation):
    """
    Display complete explainability record with evidence and decision trace.
    
    Implements Requirements 6.2, 6.3, 10.2, 10.7
    
    Args:
        eval: Criterion evaluation with explainability record
    """
    criterion = eval.criterion
    decision = eval.decision
    evidence = eval.extracted_evidence
    
    st.markdown("**Criterion Details**")
    st.write(f"Category: {criterion.category} | Priority: {criterion.priority}")
    st.write(f"Description: {criterion.description}")
    if criterion.threshold_value:
        st.write(f"Threshold: {criterion.threshold_value} {criterion.threshold_unit or ''}")
    st.write(f"Source: Page {criterion.source_page}")
    
    st.markdown("**Decision Details**")
    st.write(f"Verdict: {decision.verdict}")
    st.write(f"Rule Applied: {decision.rule_applied}")
    if decision.comparison:
        st.write(f"Comparison: {decision.comparison}")
    st.write(f"Rationale: {decision.rationale}")
    
    st.markdown("**Extracted Evidence**")
    st.write(f"Confidence: {evidence.confidence:.2f}")
    
    # Display evidence fields
    evidence_dict = evidence.dict()
    for key, value in evidence_dict.items():
        if key not in ['confidence', 'source_page']:
            st.write(f"{key.replace('_', ' ').title()}: {value}")
    
    st.write(f"Source Page: {evidence.source_page}")
    
    # Display evidence chunks with source documents
    if eval.evidence_chunks:
        st.markdown("**Retrieved Evidence Chunks**")
        for idx, chunk in enumerate(eval.evidence_chunks, 1):
            with st.expander(f"Chunk {idx} - Page {chunk.page_number} (Confidence: {chunk.confidence:.2f})"):
                st.text(chunk.text)
                st.caption(f"Source: {chunk.source_file}")


def render_override_controls(
    bidder_id: str,
    criterion_id: str,
    eval: CriterionEvaluation,
    result: EvaluationResult
):
    """
    Render manual override controls for criterion evaluation.
    
    Implements Requirements 6.4, 6.5, 6.7
    
    Args:
        bidder_id: Unique bidder identifier
        criterion_id: Criterion identifier
        eval: Criterion evaluation
        result: Complete evaluation result
    """
    st.markdown("**Manual Override**")
    
    # Check if already overridden
    override_key = f"override_{bidder_id}_{criterion_id}"
    if override_key in st.session_state:
        override = st.session_state[override_key]
        st.success(f"✅ Overridden to: {override['new_verdict']}")
        st.caption(f"By: {override['reviewer_id']}")
        st.caption(f"At: {override['timestamp']}")
        st.caption(f"Reason: {override['justification']}")
        
        if st.button("Clear Override", key=f"clear_{override_key}"):
            del st.session_state[override_key]
            st.rerun()
        return
    
    # Override form
    with st.form(key=f"override_form_{bidder_id}_{criterion_id}"):
        new_verdict = st.selectbox(
            "New Verdict",
            options=["Satisfied", "Not Satisfied", "Needs Review"],
            index=["Satisfied", "Not Satisfied", "Needs Review"].index(eval.decision.verdict),
            key=f"verdict_{bidder_id}_{criterion_id}"
        )
        
        reviewer_id = st.text_input(
            "Reviewer ID",
            placeholder="Enter your ID",
            key=f"reviewer_{bidder_id}_{criterion_id}"
        )
        
        justification = st.text_area(
            "Justification",
            placeholder="Explain the reason for this override",
            key=f"justification_{bidder_id}_{criterion_id}"
        )
        
        submitted = st.form_submit_button("Apply Override")
        
        if submitted:
            if not reviewer_id:
                st.error("Reviewer ID is required")
            elif not justification:
                st.error("Justification is required")
            elif new_verdict == eval.decision.verdict:
                st.warning("New verdict is the same as current verdict")
            else:
                apply_manual_override(
                    bidder_id=bidder_id,
                    criterion_id=criterion_id,
                    original_verdict=eval.decision.verdict,
                    new_verdict=new_verdict,
                    reviewer_id=reviewer_id,
                    justification=justification,
                    result=result
                )
                st.success("✅ Override applied successfully!")
                st.rerun()


def apply_manual_override(
    bidder_id: str,
    criterion_id: str,
    original_verdict: str,
    new_verdict: str,
    reviewer_id: str,
    justification: str,
    result: EvaluationResult
):
    """
    Apply manual override to criterion evaluation.
    
    Implements Requirements 6.4, 6.5, 6.7
    
    Args:
        bidder_id: Unique bidder identifier
        criterion_id: Criterion identifier
        original_verdict: Original verdict before override
        new_verdict: New verdict after override
        reviewer_id: ID of reviewer applying override
        justification: Reason for override
        result: Complete evaluation result to update
    """
    logger.info(
        f"Applying manual override for {bidder_id}/{criterion_id}: "
        f"{original_verdict} -> {new_verdict}"
    )
    
    # Create override record
    override = ManualOverride(
        criterion_id=criterion_id,
        original_verdict=original_verdict,
        new_verdict=new_verdict,
        reviewer_id=reviewer_id,
        justification=justification,
        timestamp=datetime.now()
    )
    
    # Store override in session state
    override_key = f"override_{bidder_id}_{criterion_id}"
    st.session_state[override_key] = override.dict()
    
    # Update criterion evaluation in result
    for eval in result.criterion_evaluations:
        if eval.criterion.id == criterion_id:
            # Update decision
            eval.decision = Decision(
                criterion_id=criterion_id,
                verdict=new_verdict,
                rule_applied="ManualOverride",
                comparison=f"Original: {original_verdict}, Override: {new_verdict}",
                rationale=f"Manual override by {reviewer_id}: {justification}",
                timestamp=datetime.now()
            )
            
            # Add override to explainability record
            eval.explainability_record['manual_override'] = override.dict()
            break
    
    # Recalculate final verdict
    rule_engine = RuleEngine()
    result.final_verdict = rule_engine.compute_verdict(result.criterion_evaluations)
    
    # Update summary
    result.summary = compute_summary(result.criterion_evaluations)
    
    # Log override to audit trail
    log_override_to_audit(override, bidder_id, result.bidder_name)
    
    logger.info(
        f"Override applied. New final verdict for {bidder_id}: {result.final_verdict}"
    )


def compute_summary(evaluations: List[CriterionEvaluation]) -> Dict:
    """
    Compute summary statistics from criterion evaluations.
    
    Args:
        evaluations: List of criterion evaluations
        
    Returns:
        Dictionary with summary counts
    """
    satisfied_count = 0
    not_satisfied_count = 0
    needs_review_count = 0
    
    mandatory_satisfied = 0
    mandatory_not_satisfied = 0
    mandatory_needs_review = 0
    
    for evaluation in evaluations:
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
    
    return {
        "total_criteria": len(evaluations),
        "satisfied": satisfied_count,
        "not_satisfied": not_satisfied_count,
        "needs_review": needs_review_count,
        "mandatory_satisfied": mandatory_satisfied,
        "mandatory_not_satisfied": mandatory_not_satisfied,
        "mandatory_needs_review": mandatory_needs_review
    }


def log_override_to_audit(override: ManualOverride, bidder_id: str, bidder_name: str):
    """
    Log manual override to audit trail.
    
    Implements Requirement 6.5
    
    Args:
        override: Manual override record
        bidder_id: Unique bidder identifier
        bidder_name: Bidder name
    """
    import json
    from src.config import FilePaths
    
    log_entry = {
        "timestamp": override.timestamp.isoformat(),
        "event_type": "manual_override",
        "bidder_id": bidder_id,
        "bidder_name": bidder_name,
        "criterion_id": override.criterion_id,
        "original_verdict": override.original_verdict,
        "new_verdict": override.new_verdict,
        "reviewer_id": override.reviewer_id,
        "justification": override.justification
    }
    
    log_file = FilePaths.AUDIT_LOGS_DIR / f"overrides_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        logger.info(f"Override logged to {log_file}")
    except Exception as e:
        logger.error(f"Failed to write override to audit log: {str(e)}")


def render_review_summary(evaluation_results: Dict[str, EvaluationResult]):
    """
    Render summary of review status across all bidders.
    
    Args:
        evaluation_results: Dictionary of bidder_id -> EvaluationResult
    """
    st.markdown("### Review Summary")
    
    total_bidders = len(evaluation_results)
    needs_review = sum(
        1 for result in evaluation_results.values()
        if result.final_verdict == "Needs Review"
    )
    eligible = sum(
        1 for result in evaluation_results.values()
        if result.final_verdict == "Eligible"
    )
    not_eligible = sum(
        1 for result in evaluation_results.values()
        if result.final_verdict == "Not Eligible"
    )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Bidders", total_bidders)
    with col2:
        st.metric("Eligible", eligible)
    with col3:
        st.metric("Not Eligible", not_eligible)
    with col4:
        st.metric("Needs Review", needs_review)
    
    # Count total overrides
    override_count = sum(
        1 for key in st.session_state.keys()
        if key.startswith("override_")
    )
    
    if override_count > 0:
        st.info(f"ℹ️ {override_count} manual override(s) have been applied")
