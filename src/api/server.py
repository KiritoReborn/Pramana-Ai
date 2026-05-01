"""FastAPI server for frontend-backend integration"""

import logging
import uuid
import tempfile
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from src.processors.document_processor import DocumentProcessor
from src.processors.tender_processor import TenderProcessor
from src.engines.evaluation_engine import EvaluationEngine
from src.engines.retrieval_engine import RetrievalEngine
from src.engines.llm_extractor import LLMExtractor
from src.engines.report_generator import ReportGenerator
from src.models.schemas import (
    EligibilityCriterion,
    EvaluationResult,
    ManualOverride
)
from src.config import SystemConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Pramana AI Tender Evaluator API",
    version=SystemConfig.VERSION,
    description="REST API for tender evaluation system"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
sessions: Dict[str, Dict] = {}

# Initialize backend components
document_processor = DocumentProcessor()
tender_processor = TenderProcessor()
retrieval_engine = RetrievalEngine()
llm_extractor = LLMExtractor()
evaluation_engine = EvaluationEngine(retrieval_engine, llm_extractor)
report_generator = ReportGenerator()

logger.info("FastAPI server initialized")


# Pydantic models for request/response
class UploadResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    bidder_id: Optional[str] = None
    documents_processed: Optional[int] = None


class TenderUploadResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    criteria_count: Optional[int] = None
    needs_review: bool = False
    criteria: Optional[List[Dict]] = None


class EvaluationRequest(BaseModel):
    bidder_ids: List[str]
    session_id: str


class EvaluationResponse(BaseModel):
    success: bool
    message: str
    results_count: int


class OverrideRequest(BaseModel):
    session_id: str
    bidder_id: str
    criterion_id: str
    original_verdict: str
    new_verdict: str
    reviewer_id: str
    justification: str


class OverrideResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create new one"""
    if session_id and session_id in sessions:
        return session_id
    
    new_session_id = str(uuid.uuid4())
    sessions[new_session_id] = {
        "created_at": datetime.now(),
        "uploaded_documents": {},
        "tender_criteria": [],
        "evaluation_results": {},
        "temp_files": []
    }
    logger.info(f"Created new session: {new_session_id}")
    return new_session_id


@app.post("/api/bidder/upload", response_model=UploadResponse)
async def upload_bidder_documents(
    files: List[UploadFile] = File(...),
    bidder_id: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """
    Upload bidder documents for processing.
    
    Validates: Requirements 2.1, 2.2, 2.11
    """
    try:
        # Get or create session
        session_id = get_or_create_session(session_id)
        session = sessions[session_id]
        
        logger.info(f"Processing {len(files)} files for bidder {bidder_id}")
        
        # Save uploaded files to temporary directory
        temp_dir = tempfile.mkdtemp()
        session["temp_files"].append(temp_dir)
        
        file_paths = []
        for file in files:
            file_path = Path(temp_dir) / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            file_paths.append(str(file_path))
        
        # Process documents through DocumentProcessor
        extracted_documents = document_processor.process_submission(
            file_paths=file_paths,
            bidder_id=bidder_id
        )
        
        if not extracted_documents:
            raise HTTPException(
                status_code=400,
                detail="Failed to process any documents"
            )
        
        # Index documents in FAISS
        retrieval_engine.add_documents(extracted_documents)
        
        # Store in session
        if bidder_id not in session["uploaded_documents"]:
            session["uploaded_documents"][bidder_id] = []
        session["uploaded_documents"][bidder_id].extend(extracted_documents)
        
        logger.info(
            f"Successfully processed {len(extracted_documents)} documents "
            f"for bidder {bidder_id}"
        )
        
        return UploadResponse(
            success=True,
            message=f"Successfully processed {len(extracted_documents)} documents",
            session_id=session_id,
            bidder_id=bidder_id,
            documents_processed=len(extracted_documents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading bidder documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tender/upload", response_model=TenderUploadResponse)
async def upload_tender_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Upload tender document and extract eligibility criteria.
    
    Validates: Requirements 2.4
    """
    try:
        # Get or create session
        session_id = get_or_create_session(session_id)
        session = sessions[session_id]
        
        logger.info(f"Processing tender document: {file.filename}")
        
        # Save uploaded file to temporary directory
        temp_dir = tempfile.mkdtemp()
        session["temp_files"].append(temp_dir)
        
        file_path = Path(temp_dir) / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process tender through TenderProcessor
        result = tender_processor.process_tender(str(file_path))
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process tender: {result['error']}"
            )
        
        # Store criteria in session
        session["tender_criteria"] = result["criteria"]
        
        # Convert criteria to dict for response
        criteria_dicts = [
            {
                "id": c.id,
                "category": c.category,
                "priority": c.priority,
                "description": c.description,
                "threshold_value": c.threshold_value,
                "threshold_unit": c.threshold_unit,
                "source_page": c.source_page,
                "original_text": c.original_text
            }
            for c in result["criteria"]
        ]
        
        logger.info(
            f"Successfully extracted {len(result['criteria'])} criteria "
            f"from tender document"
        )
        
        return TenderUploadResponse(
            success=True,
            message=f"Successfully extracted {len(result['criteria'])} criteria",
            session_id=session_id,
            criteria_count=len(result["criteria"]),
            needs_review=result.get("needs_review", False),
            criteria=criteria_dicts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading tender document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluation/run", response_model=EvaluationResponse)
async def run_evaluation(request: EvaluationRequest):
    """
    Trigger evaluation workflow for specified bidders.
    
    Validates: Requirements 2.5, 2.12
    """
    try:
        session_id = request.session_id
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        if not session["tender_criteria"]:
            raise HTTPException(
                status_code=400,
                detail="No tender criteria available. Upload tender document first."
            )
        
        logger.info(f"Running evaluation for {len(request.bidder_ids)} bidders")
        
        results_count = 0
        for bidder_id in request.bidder_ids:
            if bidder_id not in session["uploaded_documents"]:
                logger.warning(f"No documents found for bidder {bidder_id}, skipping")
                continue
            
            # Get bidder name (use bidder_id as name for now)
            bidder_name = f"Bidder {bidder_id}"
            
            # Run evaluation
            evaluation_result = evaluation_engine.evaluate_bidder(
                bidder_id=bidder_id,
                bidder_name=bidder_name,
                criteria=session["tender_criteria"]
            )
            
            # Store result in session
            session["evaluation_results"][bidder_id] = evaluation_result
            results_count += 1
            
            logger.info(
                f"Completed evaluation for bidder {bidder_id}. "
                f"Verdict: {evaluation_result.final_verdict}"
            )
        
        return EvaluationResponse(
            success=True,
            message=f"Successfully evaluated {results_count} bidders",
            results_count=results_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/evaluation/results/{bidder_id}")
async def get_evaluation_results(bidder_id: str, session_id: str):
    """
    Retrieve evaluation results for a bidder.
    
    Validates: Requirements 2.5
    """
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        if bidder_id not in session["evaluation_results"]:
            raise HTTPException(
                status_code=404,
                detail=f"No evaluation results found for bidder {bidder_id}"
            )
        
        result = session["evaluation_results"][bidder_id]
        
        # Convert to dict for JSON response
        return {
            "bidder_id": result.bidder_id,
            "bidder_name": result.bidder_name,
            "final_verdict": result.final_verdict,
            "summary": result.summary,
            "timestamp": result.timestamp.isoformat(),
            "system_version": result.system_version,
            "criterion_evaluations": [
                {
                    "criterion": {
                        "id": eval.criterion.id,
                        "category": eval.criterion.category,
                        "priority": eval.criterion.priority,
                        "description": eval.criterion.description,
                        "threshold_value": eval.criterion.threshold_value,
                        "threshold_unit": eval.criterion.threshold_unit,
                        "source_page": eval.criterion.source_page
                    },
                    "decision": {
                        "verdict": eval.decision.verdict,
                        "rule_applied": eval.decision.rule_applied,
                        "comparison": eval.decision.comparison,
                        "rationale": eval.decision.rationale,
                        "timestamp": eval.decision.timestamp.isoformat()
                    },
                    "evidence_chunks_count": len(eval.evidence_chunks),
                    "extraction_confidence": eval.extracted_evidence.confidence
                }
                for eval in result.criterion_evaluations
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving evaluation results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/review/evidence/{bidder_id}/{criterion_id}")
async def get_review_evidence(
    bidder_id: str,
    criterion_id: str,
    session_id: str
):
    """
    Fetch evidence chunks for review modal.
    
    Validates: Requirements 2.6
    """
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        if bidder_id not in session["evaluation_results"]:
            raise HTTPException(
                status_code=404,
                detail=f"No evaluation results found for bidder {bidder_id}"
            )
        
        result = session["evaluation_results"][bidder_id]
        
        # Find criterion evaluation
        criterion_eval = None
        for eval in result.criterion_evaluations:
            if eval.criterion.id == criterion_id:
                criterion_eval = eval
                break
        
        if not criterion_eval:
            raise HTTPException(
                status_code=404,
                detail=f"Criterion {criterion_id} not found in evaluation"
            )
        
        # Return evidence chunks and extracted evidence
        return {
            "criterion": {
                "id": criterion_eval.criterion.id,
                "category": criterion_eval.criterion.category,
                "priority": criterion_eval.criterion.priority,
                "description": criterion_eval.criterion.description,
                "threshold_value": criterion_eval.criterion.threshold_value,
                "threshold_unit": criterion_eval.criterion.threshold_unit
            },
            "evidence_chunks": [
                {
                    "text": chunk.text,
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number,
                    "confidence": chunk.confidence,
                    "source_file": chunk.source_file
                }
                for chunk in criterion_eval.evidence_chunks
            ],
            "extracted_evidence": criterion_eval.extracted_evidence.dict(),
            "decision": {
                "verdict": criterion_eval.decision.verdict,
                "rule_applied": criterion_eval.decision.rule_applied,
                "comparison": criterion_eval.decision.comparison,
                "rationale": criterion_eval.decision.rationale
            },
            "explainability_record": criterion_eval.explainability_record
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review evidence: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/review/override", response_model=OverrideResponse)
async def submit_override(request: OverrideRequest):
    """
    Submit manual override for criterion evaluation.
    
    Validates: Requirements 2.7
    """
    try:
        session_id = request.session_id
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        if request.bidder_id not in session["evaluation_results"]:
            raise HTTPException(
                status_code=404,
                detail=f"No evaluation results found for bidder {request.bidder_id}"
            )
        
        result = session["evaluation_results"][request.bidder_id]
        
        # Find criterion evaluation
        criterion_eval = None
        for eval in result.criterion_evaluations:
            if eval.criterion.id == request.criterion_id:
                criterion_eval = eval
                break
        
        if not criterion_eval:
            raise HTTPException(
                status_code=404,
                detail=f"Criterion {request.criterion_id} not found"
            )
        
        # Create manual override record
        override = ManualOverride(
            criterion_id=request.criterion_id,
            original_verdict=request.original_verdict,
            new_verdict=request.new_verdict,
            reviewer_id=request.reviewer_id,
            justification=request.justification,
            timestamp=datetime.now()
        )
        
        # Update decision verdict
        criterion_eval.decision.verdict = request.new_verdict
        
        # Add override to explainability record
        criterion_eval.explainability_record["manual_override"] = {
            "original_verdict": request.original_verdict,
            "new_verdict": request.new_verdict,
            "reviewer_id": request.reviewer_id,
            "justification": request.justification,
            "timestamp": override.timestamp.isoformat()
        }
        
        # Write to audit log
        audit_log_dir = Path("audit_logs")
        audit_log_dir.mkdir(exist_ok=True)
        
        audit_file = audit_log_dir / f"decisions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(audit_file, "a") as f:
            import json
            f.write(json.dumps({
                "type": "manual_override",
                "bidder_id": request.bidder_id,
                "criterion_id": request.criterion_id,
                "original_verdict": request.original_verdict,
                "new_verdict": request.new_verdict,
                "reviewer_id": request.reviewer_id,
                "justification": request.justification,
                "timestamp": override.timestamp.isoformat()
            }) + "\n")
        
        # Recalculate final verdict
        _, summary = evaluation_engine._compute_final_verdict(
            result.criterion_evaluations
        )
        result.summary = summary
        
        # Determine new final verdict
        if summary["mandatory_not_satisfied"] > 0:
            result.final_verdict = "Not Eligible"
        elif summary["mandatory_needs_review"] > 0:
            result.final_verdict = "Needs Review"
        else:
            result.final_verdict = "Eligible"
        
        logger.info(
            f"Override applied for bidder {request.bidder_id}, "
            f"criterion {request.criterion_id}. "
            f"New verdict: {request.new_verdict}"
        )
        
        return OverrideResponse(
            success=True,
            message="Override applied successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting override: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/generate/{bidder_id}")
async def generate_report(bidder_id: str, session_id: str):
    """
    Generate PDF report for a bidder.
    
    Validates: Requirements 2.8
    """
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        if bidder_id not in session["evaluation_results"]:
            raise HTTPException(
                status_code=404,
                detail=f"No evaluation results found for bidder {bidder_id}"
            )
        
        result = session["evaluation_results"][bidder_id]
        
        # Generate PDF report
        pdf_buffer = report_generator.generate_report(result)
        
        logger.info(f"Generated PDF report for bidder {bidder_id}")
        
        # Return PDF as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_{bidder_id}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/batch")
async def generate_batch_reports(bidder_ids: str, session_id: str):
    """
    Generate multiple PDF reports as ZIP file.
    
    Validates: Requirements 2.8
    """
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        # Parse bidder_ids (comma-separated)
        bidder_id_list = [bid.strip() for bid in bidder_ids.split(",")]
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for bidder_id in bidder_id_list:
                if bidder_id not in session["evaluation_results"]:
                    logger.warning(f"No results for bidder {bidder_id}, skipping")
                    continue
                
                result = session["evaluation_results"][bidder_id]
                
                # Generate PDF
                pdf_buffer = report_generator.generate_report(result)
                
                # Add to ZIP
                zip_file.writestr(
                    f"report_{bidder_id}.pdf",
                    pdf_buffer.getvalue()
                )
        
        zip_buffer.seek(0)
        
        logger.info(f"Generated batch reports for {len(bidder_id_list)} bidders")
        
        # Return ZIP as streaming response
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=reports_batch.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating batch reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Validates: Requirements 2.10
    """
    return HealthResponse(
        status="healthy",
        version=SystemConfig.VERSION,
        timestamp=datetime.now().isoformat()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
