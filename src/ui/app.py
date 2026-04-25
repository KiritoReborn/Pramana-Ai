"""Streamlit UI for Pramana AI Tender Evaluator"""

import streamlit as st
import logging
from pathlib import Path
from typing import Dict, List, Optional
import tempfile
import os
from io import BytesIO
from datetime import datetime

from src.processors.tender_processor import TenderProcessor
from src.processors.document_processor import DocumentProcessor
from src.engines.retrieval_engine import RetrievalEngine
from src.engines.llm_extractor import LLMExtractor
from src.engines.evaluation_engine import EvaluationEngine
from src.engines.rule_engine import RuleEngine
from src.models.schemas import EligibilityCriterion, EvaluationResult
from src.config import SystemConfig, RetrievalConfig
from src.ui.review_dashboard import render_review_dashboard, render_review_summary
from src.engines.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Pramana AI - Tender Evaluator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .verdict-eligible {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
    }
    .verdict-not-eligible {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
    }
    .verdict-needs-review {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
    }
    .low-confidence {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_llm_client():
    """Initialize LLM extractor with caching."""
    logger.info("Initializing LLM client")
    return LLMExtractor()


@st.cache_resource
def initialize_retrieval_engine():
    """Initialize FAISS retrieval engine with caching."""
    logger.info("Initializing retrieval engine")
    return RetrievalEngine()


@st.cache_resource
def initialize_rule_engine():
    """Initialize rule engine with caching."""
    logger.info("Initializing rule engine")
    return RuleEngine()


def initialize_session_state():
    """Initialize session state variables."""
    if 'tender_processed' not in st.session_state:
        st.session_state.tender_processed = False
    if 'criteria' not in st.session_state:
        st.session_state.criteria = []
    if 'tender_content' not in st.session_state:
        st.session_state.tender_content = None
    if 'bidder_documents' not in st.session_state:
        st.session_state.bidder_documents = {}
    if 'evaluation_results' not in st.session_state:
        st.session_state.evaluation_results = {}


def render_header():
    """Render application header."""
    st.markdown('<div class="main-header">📋 Pramana AI - Tender Evaluator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Evidence-grounded eligibility evaluation for government procurement</div>',
        unsafe_allow_html=True
    )
    st.markdown("---")


def render_tender_upload_section():
    """Render tender document upload section."""
    st.header("1️⃣ Upload Tender Document")
    
    tender_file = st.file_uploader(
        "Upload tender PDF containing eligibility criteria",
        type=['pdf'],
        key='tender_uploader',
        help="Upload the government tender document with eligibility requirements"
    )
    
    if tender_file and not st.session_state.tender_processed:
        if st.button("Process Tender Document", type="primary"):
            with st.spinner("Processing tender document..."):
                process_tender_document(tender_file)
    
    if st.session_state.tender_processed:
        st.success(f"✅ Tender processed successfully! Found {len(st.session_state.criteria)} eligibility criteria.")
        
        if st.button("Reset Tender"):
            st.session_state.tender_processed = False
            st.session_state.criteria = []
            st.session_state.tender_content = None
            st.session_state.bidder_documents = {}
            st.session_state.evaluation_results = {}
            st.rerun()


@st.cache_data
def process_tender_document_cached(file_path: str):
    """Process tender document with caching."""
    tender_processor = TenderProcessor()
    return tender_processor.process_tender(file_path)


def process_tender_document(tender_file):
    """Process uploaded tender document."""
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(tender_file.read())
            tmp_path = tmp_file.name
        
        # Process tender
        result = process_tender_document_cached(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if result['success']:
            st.session_state.criteria = result['criteria']
            st.session_state.tender_content = result['raw_content']
            st.session_state.tender_processed = True
            
            if result.get('needs_review'):
                st.warning(f"⚠️ Manual review recommended: {result.get('error', 'Some criteria may need verification')}")
        else:
            st.error(f"❌ Failed to process tender: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        logger.error(f"Error processing tender: {str(e)}")
        st.error(f"❌ Error processing tender: {str(e)}")


def render_criteria_display():
    """Display extracted eligibility criteria."""
    if not st.session_state.tender_processed:
        return
    
    st.header("2️⃣ Extracted Eligibility Criteria")
    
    criteria = st.session_state.criteria
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Criteria", len(criteria))
    with col2:
        mandatory_count = sum(1 for c in criteria if c.priority == "Mandatory")
        st.metric("Mandatory", mandatory_count)
    with col3:
        optional_count = sum(1 for c in criteria if c.priority == "Optional")
        st.metric("Optional", optional_count)
    with col4:
        categories = set(c.category for c in criteria)
        st.metric("Categories", len(categories))
    
    # Display criteria by category
    for category in ["Financial", "Technical", "Compliance", "Documentation"]:
        category_criteria = [c for c in criteria if c.category == category]
        if category_criteria:
            with st.expander(f"📂 {category} Criteria ({len(category_criteria)})", expanded=False):
                for criterion in category_criteria:
                    priority_badge = "🔴 Mandatory" if criterion.priority == "Mandatory" else "🟢 Optional"
                    st.markdown(f"**{criterion.id}** - {priority_badge}")
                    st.write(f"**Description:** {criterion.description}")
                    if criterion.threshold_value:
                        st.write(f"**Threshold:** {criterion.threshold_value} {criterion.threshold_unit or ''}")
                    st.write(f"**Source:** Page {criterion.source_page}")
                    st.markdown("---")


def render_bidder_upload_section():
    """Render bidder document upload section."""
    if not st.session_state.tender_processed:
        st.info("👆 Please upload and process a tender document first")
        return
    
    st.header("3️⃣ Upload Bidder Documents")
    
    bidder_name = st.text_input(
        "Bidder Name",
        key='bidder_name_input',
        placeholder="Enter bidder company name"
    )
    
    bidder_files = st.file_uploader(
        "Upload bidder documents (PDF, images)",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        key='bidder_uploader',
        help="Upload all documents submitted by the bidder"
    )
    
    if bidder_name and bidder_files:
        if st.button("Add Bidder Documents", type="primary"):
            with st.spinner(f"Processing documents for {bidder_name}..."):
                process_bidder_documents(bidder_name, bidder_files)
    
    # Display added bidders
    if st.session_state.bidder_documents:
        st.subheader("Added Bidders")
        for bidder_id, bidder_info in st.session_state.bidder_documents.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{bidder_info['name']}**")
            with col2:
                st.write(f"{len(bidder_info['documents'])} documents")
            with col3:
                if st.button("Remove", key=f"remove_{bidder_id}"):
                    del st.session_state.bidder_documents[bidder_id]
                    if bidder_id in st.session_state.evaluation_results:
                        del st.session_state.evaluation_results[bidder_id]
                    st.rerun()


@st.cache_data
def process_bidder_documents_cached(bidder_id: str, file_paths: List[str]):
    """Process bidder documents with caching."""
    doc_processor = DocumentProcessor()
    documents = []
    
    for file_path in file_paths:
        result = doc_processor.process_document(file_path, bidder_id)
        if result['success']:
            documents.append(result['document'])
    
    return documents


def process_bidder_documents(bidder_name: str, bidder_files):
    """Process uploaded bidder documents."""
    try:
        bidder_id = bidder_name.lower().replace(' ', '_')
        
        # Save files to temporary location
        temp_paths = []
        for uploaded_file in bidder_files:
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_paths.append(tmp_file.name)
        
        # Process documents
        documents = process_bidder_documents_cached(bidder_id, temp_paths)
        
        # Clean up temp files
        for path in temp_paths:
            os.unlink(path)
        
        # Store in session state
        st.session_state.bidder_documents[bidder_id] = {
            'name': bidder_name,
            'documents': documents
        }
        
        st.success(f"✅ Processed {len(documents)} documents for {bidder_name}")
        
        # Index documents in FAISS
        retrieval_engine = initialize_retrieval_engine()
        for doc in documents:
            retrieval_engine.add_documents([doc])
        
    except Exception as e:
        logger.error(f"Error processing bidder documents: {str(e)}")
        st.error(f"❌ Error processing documents: {str(e)}")


def render_evaluation_section():
    """Render evaluation trigger and results section."""
    if not st.session_state.bidder_documents:
        st.info("👆 Please add bidder documents first")
        return
    
    st.header("4️⃣ Evaluate Bidders")
    
    # Select bidders to evaluate
    bidder_options = {
        bidder_id: info['name']
        for bidder_id, info in st.session_state.bidder_documents.items()
    }
    
    selected_bidders = st.multiselect(
        "Select bidders to evaluate",
        options=list(bidder_options.keys()),
        format_func=lambda x: bidder_options[x],
        default=list(bidder_options.keys())
    )
    
    if selected_bidders:
        if st.button("🚀 Run Evaluation", type="primary"):
            run_evaluation(selected_bidders)
    
    # Display evaluation results
    if st.session_state.evaluation_results:
        st.markdown("---")
        render_evaluation_results()


def run_evaluation(bidder_ids: List[str]):
    """Run evaluation for selected bidders."""
    llm_extractor = initialize_llm_client()
    retrieval_engine = initialize_retrieval_engine()
    rule_engine = initialize_rule_engine()
    
    evaluation_engine = EvaluationEngine(retrieval_engine, llm_extractor)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, bidder_id in enumerate(bidder_ids):
        bidder_info = st.session_state.bidder_documents[bidder_id]
        status_text.text(f"Evaluating {bidder_info['name']}...")
        
        try:
            # Run evaluation
            result = evaluation_engine.evaluate_bidder(
                bidder_id=bidder_id,
                bidder_name=bidder_info['name'],
                criteria=st.session_state.criteria
            )
            
            # Apply rule engine to finalize decisions
            for eval in result.criterion_evaluations:
                eval.decision = rule_engine.apply_rules(
                    eval.criterion,
                    eval.extracted_evidence
                )
            
            # Recompute final verdict
            result.final_verdict = rule_engine.compute_verdict(result.criterion_evaluations)
            
            # Store result
            st.session_state.evaluation_results[bidder_id] = result
            
        except Exception as e:
            logger.error(f"Error evaluating {bidder_info['name']}: {str(e)}")
            st.error(f"❌ Error evaluating {bidder_info['name']}: {str(e)}")
        
        progress_bar.progress((idx + 1) / len(bidder_ids))
    
    status_text.text("✅ Evaluation complete!")
    st.success("Evaluation completed successfully!")


def render_evaluation_results():
    """Display evaluation results for all bidders."""
    st.subheader("📊 Evaluation Results")
    
    for bidder_id, result in st.session_state.evaluation_results.items():
        render_bidder_result(result)
    
    # Add download reports section
    st.markdown("---")
    st.subheader("📥 Download Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download individual reports
        st.markdown("**Individual Reports**")
        for bidder_id, result in st.session_state.evaluation_results.items():
            if st.button(f"Download Report - {result.bidder_name}", key=f"download_{bidder_id}"):
                download_report(result)
    
    with col2:
        # Download all reports
        st.markdown("**Batch Download**")
        if len(st.session_state.evaluation_results) > 1:
            if st.button("Download All Reports (ZIP)", key="download_all"):
                download_all_reports(st.session_state.evaluation_results)


def download_report(result: EvaluationResult):
    """Generate and download PDF report for a bidder."""
    try:
        report_generator = ReportGenerator()
        pdf_buffer = report_generator.generate_report(result)
        
        st.download_button(
            label=f"📄 {result.bidder_name}_Report.pdf",
            data=pdf_buffer,
            file_name=f"{result.bidder_name.replace(' ', '_')}_Evaluation_Report.pdf",
            mime="application/pdf",
            key=f"dl_btn_{result.bidder_id}"
        )
        
        st.success(f"✅ Report generated for {result.bidder_name}")
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        st.error(f"❌ Error generating report: {str(e)}")


def download_all_reports(evaluation_results: Dict[str, EvaluationResult]):
    """Generate and download all reports as a ZIP file."""
    import zipfile
    
    try:
        report_generator = ReportGenerator()
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for bidder_id, result in evaluation_results.items():
                pdf_buffer = report_generator.generate_report(result)
                file_name = f"{result.bidder_name.replace(' ', '_')}_Evaluation_Report.pdf"
                zip_file.writestr(file_name, pdf_buffer.getvalue())
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📦 Download All Reports (ZIP)",
            data=zip_buffer,
            file_name=f"Evaluation_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            key="dl_all_btn"
        )
        
        st.success(f"✅ Generated {len(evaluation_results)} reports")
    
    except Exception as e:
        logger.error(f"Error generating reports: {str(e)}")
        st.error(f"❌ Error generating reports: {str(e)}")


def render_bidder_result(result: EvaluationResult):
    """Render evaluation result for a single bidder."""
    with st.expander(f"📄 {result.bidder_name} - {result.final_verdict}", expanded=True):
        # Verdict display
        verdict_class = {
            "Eligible": "verdict-eligible",
            "Not Eligible": "verdict-not-eligible",
            "Needs Review": "verdict-needs-review"
        }[result.final_verdict]
        
        st.markdown(f'<div class="{verdict_class}">{result.final_verdict}</div>', unsafe_allow_html=True)
        
        # Summary statistics
        st.markdown("### Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Satisfied", result.summary['satisfied'])
        with col2:
            st.metric("Not Satisfied", result.summary['not_satisfied'])
        with col3:
            st.metric("Needs Review", result.summary['needs_review'])
        
        # Criterion evaluations
        st.markdown("### Criterion Evaluations")
        
        for eval in result.criterion_evaluations:
            render_criterion_evaluation(eval)


def render_criterion_evaluation(eval):
    """Render single criterion evaluation with explainability."""
    criterion = eval.criterion
    decision = eval.decision
    evidence = eval.extracted_evidence
    
    # Determine if low confidence
    is_low_confidence = evidence.confidence < RetrievalConfig.LOW_CONFIDENCE_THRESHOLD
    
    with st.expander(
        f"{criterion.id} - {decision.verdict} {'⚠️' if is_low_confidence else ''}",
        expanded=False
    ):
        # Criterion details
        st.markdown(f"**Category:** {criterion.category} | **Priority:** {criterion.priority}")
        st.markdown(f"**Description:** {criterion.description}")
        
        if criterion.threshold_value:
            st.markdown(f"**Threshold:** {criterion.threshold_value} {criterion.threshold_unit or ''}")
        
        st.markdown("---")
        
        # Decision details
        st.markdown("### Decision")
        st.markdown(f"**Verdict:** {decision.verdict}")
        st.markdown(f"**Rule Applied:** {decision.rule_applied}")
        if decision.comparison:
            st.markdown(f"**Comparison:** {decision.comparison}")
        st.markdown(f"**Rationale:** {decision.rationale}")
        
        st.markdown("---")
        
        # Evidence details
        st.markdown("### Extracted Evidence")
        
        # Display confidence with warning if low
        if is_low_confidence:
            st.markdown(
                f'<div class="low-confidence">⚠️ Low Confidence: {evidence.confidence:.2f} '
                f'(below threshold {RetrievalConfig.LOW_CONFIDENCE_THRESHOLD})</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"**Confidence:** {evidence.confidence:.2f}")
        
        # Display evidence based on type
        evidence_dict = evidence.dict()
        for key, value in evidence_dict.items():
            if key not in ['confidence', 'source_page']:
                st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
        
        st.markdown(f"**Source Page:** {evidence.source_page}")
        
        # Evidence chunks
        if eval.evidence_chunks:
            st.markdown("### Retrieved Evidence Chunks")
            for idx, chunk in enumerate(eval.evidence_chunks[:3], 1):  # Show top 3
                st.markdown(f"**Chunk {idx}** (Page {chunk.page_number}, Confidence: {chunk.confidence:.2f})")
                st.text(chunk.text[:300] + "..." if len(chunk.text) > 300 else chunk.text)
                st.markdown(f"*Source: {chunk.source_file}*")


def main():
    """Main application entry point."""
    initialize_session_state()
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### System Information")
        st.write(f"**Version:** {SystemConfig.VERSION}")
        st.write(f"**System:** {SystemConfig.NAME}")
        st.markdown("---")
        st.markdown("### About")
        st.write("Pramana AI uses local AI models combined with deterministic rule engines to evaluate tender submissions.")
        st.write("**Architecture:** AI extracts, Python decides")
        st.markdown("---")
        st.markdown("### Status")
        if st.session_state.tender_processed:
            st.success("✅ Tender loaded")
        else:
            st.info("⏳ No tender loaded")
        
        if st.session_state.bidder_documents:
            st.success(f"✅ {len(st.session_state.bidder_documents)} bidder(s) added")
        else:
            st.info("⏳ No bidders added")
    
    # Main content
    # Create tabs for main workflow and review dashboard
    tab1, tab2 = st.tabs(["📋 Evaluation Workflow", "🔍 Review Dashboard"])
    
    with tab1:
        render_tender_upload_section()
        st.markdown("---")
        render_criteria_display()
        st.markdown("---")
        render_bidder_upload_section()
        st.markdown("---")
        render_evaluation_section()
    
    with tab2:
        if st.session_state.evaluation_results:
            render_review_summary(st.session_state.evaluation_results)
            st.markdown("---")
            render_review_dashboard(st.session_state.evaluation_results)
        else:
            st.info("👆 Please run evaluations first to access the review dashboard")


if __name__ == "__main__":
    main()
