# Pramana AI - Demo Guide

**Step-by-step walkthrough for demonstrating the Tender Evaluator**

This guide provides a complete demonstration script with expected outputs and timings for showcasing Pramana AI's capabilities.

## 🎯 Demo Objectives

By the end of this demo, you will have shown:
1. ✅ Automated tender criteria extraction
2. ✅ Multi-format bidder document processing
3. ✅ Evidence-based evaluation with explainability
4. ✅ Deterministic rule-based decisions
5. ✅ Human review and manual override capability
6. ✅ Government-compliant PDF report generation

## ⏱️ Demo Timeline

- **Setup**: 2 minutes
- **Tender Processing**: 1 minute
- **Bidder Upload**: 2 minutes
- **Evaluation**: 3 minutes
- **Review & Override**: 2 minutes
- **Report Generation**: 1 minute
- **Total**: ~11 minutes

## 🚀 Pre-Demo Setup (Do This First!)

### 1. Start Ollama Server
```bash
ollama serve
```
**Verify**: Check that Ollama is running at `http://localhost:11434`

### 2. Pre-compute Embeddings (Optional but Recommended)
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Pre-compute embeddings for instant demo
python src/utils/precompute_embeddings.py
```
**Expected Output**: 
```
✅ Embeddings cached to cache/faiss_index.bin
✅ Metadata cached to cache/faiss_metadata.pkl
```

### 3. Launch Streamlit App
```bash
streamlit run src/ui/app.py
```
**Expected**: Browser opens at `http://localhost:8501`

### 4. Prepare Demo Documents
Have these ready:
- **Tender PDF**: Government procurement tender with eligibility criteria
- **Bidder 1 Documents**: Compliant bidder (should pass)
- **Bidder 2 Documents**: Non-compliant bidder (should fail)
- **Bidder 3 Documents**: Borderline bidder (needs review)

## 📋 Demo Script

### Part 1: Introduction (30 seconds)

**Script**:
> "Pramana AI is an evidence-grounded tender evaluation system built for government procurement. It combines local AI models with deterministic rule engines to provide transparent, explainable, and auditable eligibility decisions. Everything runs offline on standard hardware with zero cloud dependencies."

**Key Points**:
- 100% offline operation
- AI extracts, Python decides
- Full explainability and audit trail
- Government compliance ready

---

### Part 2: Tender Document Processing (2 minutes)

**Action**: Upload tender PDF

**Script**:
> "First, we upload the government tender document. The system will extract text using pdfplumber, identify tables with camelot, and use our local Llama 3.1 model to extract structured eligibility criteria."

**Steps**:
1. Click "Upload tender PDF containing eligibility criteria"
2. Select tender document
3. Click "Process Tender Document"
4. Wait for processing (~30-60 seconds)

**Expected Output**:
```
✅ Tender processed successfully! Found X eligibility criteria.
```

**Show**:
- Expand "Extracted Eligibility Criteria" section
- Point out categories: Financial, Technical, Compliance, Documentation
- Highlight mandatory vs optional criteria
- Show threshold values where applicable

**Script**:
> "Notice how the system has automatically categorized criteria and identified mandatory requirements. Each criterion includes the source page number for traceability."

---

### Part 3: Bidder Document Upload (2 minutes)

**Action**: Add multiple bidders

**Script**:
> "Now we'll add bidder submissions. The system accepts PDFs, scanned PDFs, and images. It uses Tesseract OCR for scanned documents and tracks confidence scores."

**Steps for Each Bidder**:
1. Enter bidder name (e.g., "Acme Corporation")
2. Upload bidder documents (multiple files supported)
3. Click "Add Bidder Documents"
4. Repeat for 2-3 bidders

**Expected Output** (per bidder):
```
✅ Processed X documents for [Bidder Name]
```

**Show**:
- Multiple document types being processed
- Document count per bidder
- Quick processing time

---

### Part 4: Evaluation Execution (3 minutes)

**Action**: Run evaluation

**Script**:
> "The evaluation engine retrieves relevant evidence using FAISS semantic search, extracts structured information with our LLM, and applies deterministic rules to make final decisions. Let's evaluate all bidders."

**Steps**:
1. Select all bidders in multiselect
2. Click "Run Evaluation"
3. Watch progress bar

**Expected Timing**:
- ~60-90 seconds per bidder
- Progress bar updates in real-time

**Expected Output**:
```
✅ Evaluation complete!
```

**Show Results**:
1. Expand first bidder (compliant)
   - **Verdict**: Eligible (green)
   - **Summary**: All mandatory criteria satisfied
   - Expand a criterion to show:
     - Evidence chunks with source pages
     - Confidence scores
     - Rule applied and rationale

2. Expand second bidder (non-compliant)
   - **Verdict**: Not Eligible (red)
   - **Summary**: X mandatory criteria not satisfied
   - Show failed criterion with comparison

3. Expand third bidder (needs review)
   - **Verdict**: Needs Review (yellow)
   - **Summary**: Low confidence on some criteria
   - Show low-confidence warning

**Script**:
> "Notice the complete explainability - every decision traces back to specific evidence in source documents with page numbers. The confidence scores help identify where human review is needed."

---

### Part 5: Human Review Dashboard (2 minutes)

**Action**: Switch to Review Dashboard tab

**Script**:
> "For evaluations flagged as 'Needs Review', procurement officers can use the review dashboard to examine evidence and apply manual overrides when necessary."

**Steps**:
1. Click "Review Dashboard" tab
2. Show review summary statistics
3. Expand a bidder that needs review
4. Show flagged criterion with low confidence
5. Demonstrate manual override:
   - Select new verdict
   - Enter reviewer ID
   - Provide justification
   - Click "Apply Override"

**Expected Output**:
```
✅ Override applied successfully!
```

**Show**:
- Final verdict automatically recalculated
- Override logged with timestamp and reviewer
- Complete audit trail preserved

**Script**:
> "All manual overrides are logged with reviewer identity, timestamp, and justification. The system automatically recalculates the final verdict based on updated criterion evaluations."

---

### Part 6: Report Generation (1 minute)

**Action**: Download PDF reports

**Script**:
> "Finally, we can generate government-compliant PDF reports with complete audit trails for archival and compliance purposes."

**Steps**:
1. Scroll to "Download Reports" section
2. Click "Download Report - [Bidder Name]"
3. Open downloaded PDF

**Show in PDF**:
- Professional formatting
- Final verdict with color coding
- Summary statistics
- Detailed criterion evaluations with evidence
- Manual overrides section (if any)
- Source page references
- System version and timestamp
- Compliance footer

**Script**:
> "The report includes everything needed for government compliance - complete evidence trail, decision rationale, manual overrides, and source references. It's formatted for archival and legal defensibility."

---

### Part 7: Architecture Deep Dive (Optional, 2 minutes)

**Script**:
> "Let me quickly explain the architecture that makes this possible."

**Key Points**:
1. **AI Extracts, Python Decides**
   - LLM only extracts evidence (no judgment)
   - Deterministic Python rules make final decisions
   - Same input always produces same output

2. **Crash Prevention**
   - Pydantic validation on all LLM outputs
   - Retry logic with simplified prompts
   - Safe defaults on validation failure
   - System never crashes from malformed AI output

3. **Performance Optimization**
   - Aggressive caching with Streamlit decorators
   - Pre-computed embeddings for demos
   - FAISS for efficient semantic search
   - Meets 60s tender / 90s bidder targets

4. **Offline Operation**
   - Ollama for local LLM inference
   - No cloud API calls
   - No internet dependency
   - Complete data privacy

---

## 🎬 Demo Tips

### Before Demo
- [ ] Test Ollama connection: `ollama list`
- [ ] Pre-compute embeddings for instant loading
- [ ] Prepare 3 bidder scenarios (pass/fail/review)
- [ ] Close unnecessary browser tabs
- [ ] Test audio/video if presenting remotely

### During Demo
- **Pace**: Speak slowly and clearly
- **Pause**: Let processing complete before moving on
- **Highlight**: Point out confidence scores and source pages
- **Interact**: Expand/collapse sections to show detail
- **Explain**: Emphasize explainability and audit trail

### Common Questions & Answers

**Q: How accurate is the system?**
> A: The system extracts evidence with confidence scores. Low confidence triggers human review. Final decisions are made by deterministic rules, not AI judgment, ensuring consistency and legal defensibility.

**Q: What if the AI makes a mistake?**
> A: The review dashboard allows procurement officers to override any decision with justification. All overrides are logged and the verdict is automatically recalculated.

**Q: Can this run on my laptop?**
> A: Yes! It runs on standard hardware - 16GB RAM, CPU/limited GPU. Everything is local with no cloud dependencies.

**Q: How long does evaluation take?**
> A: Tender processing: ~60 seconds. Bidder evaluation: ~90 seconds. With pre-computed embeddings, demo startup is instant.

**Q: Is this compliant with government regulations?**
> A: Yes. The system provides complete audit trails, deterministic decisions, and archival-ready PDF reports. All decisions trace back to source documents with page numbers.

**Q: What document formats are supported?**
> A: Native PDFs (pdfplumber), scanned PDFs (Tesseract OCR), and images (PNG, JPG, JPEG). OCR confidence is tracked and low-quality scans are flagged.

---

## 📊 Expected Performance Metrics

### Processing Times (with caching)
- **Tender Upload**: 30-60 seconds
- **Bidder Upload**: 10-20 seconds per document
- **Evaluation**: 60-90 seconds per bidder
- **Report Generation**: 2-5 seconds

### Accuracy Indicators
- **High Confidence**: ≥ 0.7 (auto-accept)
- **Medium Confidence**: 0.5-0.7 (review recommended)
- **Low Confidence**: < 0.5 (manual review required)

### System Resources
- **Memory**: ~2-4 GB during evaluation
- **CPU**: Moderate usage during LLM calls
- **Disk**: ~100 MB for cached embeddings

---

## 🐛 Demo Troubleshooting

### Issue: Ollama Connection Error
**Symptom**: "Could not connect to Ollama"
**Fix**: 
```bash
ollama serve
# Verify at http://localhost:11434
```

### Issue: Slow Processing
**Symptom**: Evaluation takes > 2 minutes per bidder
**Fix**:
```bash
# Pre-compute embeddings
python src/utils/precompute_embeddings.py
```

### Issue: OCR Confidence Low
**Symptom**: Many criteria flagged for review
**Fix**: Use higher quality scans or native PDFs

### Issue: Streamlit Caching Warning
**Symptom**: "Cached function modified"
**Fix**: Clear cache with Ctrl+C in terminal and restart

---

## 🎯 Demo Success Criteria

By the end of the demo, audience should understand:
- ✅ How tender criteria are automatically extracted
- ✅ How evidence is retrieved and evaluated
- ✅ Why decisions are deterministic and explainable
- ✅ How human review and overrides work
- ✅ How reports provide complete audit trails
- ✅ Why offline operation matters for government

---

## 📝 Post-Demo Follow-Up

### Materials to Share
- [ ] README.md with installation instructions
- [ ] Sample PDF reports
- [ ] Architecture diagram
- [ ] Performance benchmarks
- [ ] Test coverage report

### Next Steps
1. Schedule technical deep-dive session
2. Provide access to demo environment
3. Share documentation and code repository
4. Discuss customization requirements
5. Plan pilot deployment

---

**Good luck with your demo! 🚀**

For questions or issues, refer to the main README.md or contact [your contact info].
