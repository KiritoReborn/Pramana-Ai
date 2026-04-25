# Pramana AI - Tender Evaluator

**Evidence-grounded eligibility evaluation for government procurement tenders**

Pramana AI is an offline, explainable AI system that evaluates bidder submissions against tender eligibility criteria using local AI models combined with deterministic rule engines. Built for government compliance with full auditability and zero cloud dependencies.

## 🎯 Key Features

- **AI Extracts, Python Decides**: LLM extracts evidence, deterministic rules make final decisions
- **100% Offline**: Runs entirely on local hardware with no cloud dependencies
- **Full Explainability**: Complete audit trail from source documents to final verdict
- **Crash-Proof**: Pydantic validation with retry logic prevents system failures
- **Government Compliant**: Designed for regulatory compliance and archival
- **Fast Demo Performance**: Aggressive caching for instant demonstrations

## 🏗️ Architecture

```
┌─────────────────┐
│ Tender Document │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Document Processing    │
│  (PDF, OCR, Tables)     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  LLM Criteria Extraction│
│  (Pydantic Validated)   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Bidder Documents Upload │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  FAISS Vector Retrieval │
│  (Semantic Search)      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  LLM Evidence Extraction│
│  (Type-Specific Schemas)│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Rule Engine Decisions  │
│  (Deterministic Logic)  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Human Review Dashboard │
│  (Manual Overrides)     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  PDF Report Generation  │
│  (Government Compliant) │
└─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Ollama** with Llama 3.1 model
- **Tesseract OCR**
- **Ghostscript** (for camelot-py)

### Windows Installation

#### 1. Install Python
Download and install Python 3.9+ from [python.org](https://www.python.org/downloads/)

#### 2. Install Ollama
```bash
# Download from https://ollama.ai/download
# After installation, pull the Llama 3.1 model:
ollama pull llama3.1
```

#### 3. Install Tesseract OCR
```bash
# Download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Add Tesseract to PATH or set environment variable:
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

#### 4. Install Ghostscript
```bash
# Download from:
# https://www.ghostscript.com/download/gsdnld.html

# Install and add to PATH
```

#### 5. Clone Repository and Install Dependencies
```bash
git clone <repository-url>
cd pramana-ai-tender-evaluator

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Linux/Mac Installation

#### 1. Install Python
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.9 python3-pip python3-venv

# macOS (using Homebrew)
brew install python@3.9
```

#### 2. Install Ollama
```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# macOS
brew install ollama

# Pull Llama 3.1 model
ollama pull llama3.1
```

#### 3. Install Tesseract OCR
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

#### 4. Install Ghostscript
```bash
# Ubuntu/Debian
sudo apt-get install ghostscript

# macOS
brew install ghostscript
```

#### 5. Clone Repository and Install Dependencies
```bash
git clone <repository-url>
cd pramana-ai-tender-evaluator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🎮 Running the Application

### Start Ollama Server
```bash
# Make sure Ollama is running
ollama serve
```

### Launch Streamlit UI
```bash
streamlit run src/ui/app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### 1. Upload Tender Document
- Click "Upload tender PDF containing eligibility criteria"
- Select your tender document (PDF format)
- Click "Process Tender Document"
- Review extracted criteria organized by category

### 2. Add Bidder Documents
- Enter bidder name
- Upload bidder documents (PDF, PNG, JPG, JPEG)
- Click "Add Bidder Documents"
- Repeat for multiple bidders

### 3. Run Evaluation
- Select bidders to evaluate
- Click "Run Evaluation"
- Wait for processing (typically 60-90 seconds per bidder)
- Review results with detailed evidence and confidence scores

### 4. Human Review (Optional)
- Switch to "Review Dashboard" tab
- Review flagged evaluations with low confidence
- Apply manual overrides with justification
- System automatically recalculates final verdict

### 5. Download Reports
- Navigate to "Download Reports" section
- Download individual PDF reports per bidder
- Or download all reports as ZIP file
- Reports include complete audit trail

## 🔧 Configuration

### LLM Settings
Edit `src/config.py`:
```python
class LLMConfig:
    MODEL_NAME = "llama3.1"
    TEMPERATURE = 0.1  # Low for consistency
    MAX_TOKENS = 2048
    TIMEOUT = 30
    MAX_RETRIES = 3
```

### Performance Targets
```python
class PerformanceTargets:
    TENDER_PROCESSING_TIME = 60  # seconds
    BIDDER_EVALUATION_TIME = 90  # seconds
    CACHE_ENABLED = True
```

### Retrieval Settings
```python
class RetrievalConfig:
    TOP_K = 5  # Number of evidence chunks to retrieve
    MIN_CONFIDENCE = 0.5  # Minimum confidence threshold
    LOW_CONFIDENCE_THRESHOLD = 0.7  # Flags for review
```

## 📊 System Components

### Document Processing
- **Text Extraction**: pdfplumber for native PDFs
- **OCR**: Tesseract for scanned documents and images
- **Table Extraction**: camelot-py for structured data
- **Confidence Scoring**: OCR quality assessment

### Evidence Retrieval
- **Embeddings**: all-MiniLM-L6-v2 (384 dimensions)
- **Vector Store**: FAISS IndexFlatL2
- **Chunking**: 512 tokens with 50% overlap
- **Caching**: Disk-based for demo performance

### LLM Extraction
- **Model**: Llama 3.1 via Ollama
- **Validation**: Pydantic schemas with retry logic
- **Categories**: Financial, Technical, Compliance, Documentation
- **Crash Prevention**: Safe defaults on validation failure

### Rule Engine
- **Decision Logic**: 100% deterministic Python rules
- **Threshold Comparison**: Numeric and boolean checks
- **Verdict Computation**: Mandatory criteria drive final verdict
- **Audit Logging**: Complete decision trace to JSONL

### Human Review
- **Filtering**: Auto-display "Needs Review" verdicts
- **Explainability**: Full evidence trace with source pages
- **Manual Override**: Reviewer ID, timestamp, justification
- **Verdict Recalculation**: Automatic after overrides

### Report Generation
- **Format**: PDF via reportlab
- **Content**: Verdict, summary, detailed evaluations, overrides
- **Compliance**: Government archival format
- **Batch Export**: ZIP download for multiple bidders

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suites
```bash
# Schema validation
pytest tests/test_schema_validation.py -v

# Document processing
pytest tests/test_document_processing.py -v

# Retrieval engine
pytest tests/test_retrieval_engine.py -v

# Rule engine
pytest tests/test_rule_engine.py -v

# Integration tests
pytest tests/test_integration_document_pipeline.py -v

# Checkpoints
pytest tests/test_checkpoint_task5.py -v
pytest tests/test_checkpoint_task9.py -v
```

### Test Coverage
- **137 tests passing**
- Schema validation: 16 tests
- Document processing: 26 tests
- Retrieval system: 23 tests
- Rule engine: 30 tests
- Integration: 6 tests
- Checkpoints: 13 tests

## 📁 Project Structure

```
.
├── src/
│   ├── models/
│   │   └── schemas.py              # Pydantic schemas
│   ├── processors/
│   │   ├── text_extractor.py       # PDF text extraction
│   │   ├── table_extractor.py      # Table extraction
│   │   ├── ocr_engine.py           # OCR processing
│   │   ├── document_processor.py   # Document orchestrator
│   │   └── tender_processor.py     # Tender processor
│   ├── engines/
│   │   ├── llm_extractor.py        # LLM with validation
│   │   ├── prompts.py              # Prompt templates
│   │   ├── retrieval_engine.py     # FAISS retrieval
│   │   ├── evaluation_engine.py    # Evaluation orchestrator
│   │   ├── rule_engine.py          # Deterministic decisions
│   │   └── report_generator.py     # PDF report generation
│   ├── ui/
│   │   ├── app.py                  # Main Streamlit app
│   │   └── review_dashboard.py     # Review dashboard
│   ├── utils/
│   │   └── precompute_embeddings.py # Embedding cache utility
│   └── config.py                   # Configuration
├── tests/                          # Test suite
├── cache/                          # FAISS index cache
├── audit_logs/                     # Decision audit logs
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🎯 Performance Optimization

### Caching Strategy
1. **LLM Client**: `@st.cache_resource` for Ollama initialization
2. **FAISS Index**: `@st.cache_resource` for vector store
3. **Document Processing**: `@st.cache_data` for PDF extraction
4. **Embeddings**: Disk-based cache for demo documents

### Pre-computation for Demos
```bash
# Pre-compute embeddings for demo documents
python src/utils/precompute_embeddings.py
```

This creates cached FAISS index in `cache/` directory for instant demo loading.

## 🔒 Security & Compliance

### Data Privacy
- **100% Offline**: No data leaves local machine
- **No Cloud APIs**: All processing local
- **No Telemetry**: No usage tracking

### Audit Trail
- **Decision Logs**: JSONL format in `audit_logs/`
- **Manual Overrides**: Separate log with reviewer details
- **Explainability**: Source document references preserved
- **Timestamps**: All operations timestamped

### Deterministic Decisions
- **Rule-Based**: No AI judgment in final decisions
- **Reproducible**: Same input = same output
- **Transparent**: Complete decision trace
- **Legally Defensible**: Clear rationale for all verdicts

## 🐛 Troubleshooting

### Ollama Connection Error
```
Error: Could not connect to Ollama
```
**Solution**: Ensure Ollama is running with `ollama serve`

### Tesseract Not Found
```
Error: Tesseract not found
```
**Solution**: Install Tesseract and add to PATH, or set `TESSERACT_CMD` environment variable

### Ghostscript Error (camelot-py)
```
Error: Ghostscript not found
```
**Solution**: Install Ghostscript and add to PATH

### Low Memory Warning
```
Warning: High memory usage
```
**Solution**: Reduce batch size or process fewer bidders simultaneously

### Slow Performance
**Solutions**:
- Pre-compute embeddings with `precompute_embeddings.py`
- Enable caching in `src/config.py`
- Reduce `TOP_K` in retrieval config
- Use smaller document chunks

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📧 Contact

[Add contact information here]

## 🙏 Acknowledgments

- **Ollama**: Local LLM inference
- **LangChain**: LLM orchestration framework
- **FAISS**: Efficient vector similarity search
- **Streamlit**: Rapid UI development
- **Pydantic**: Data validation and settings management

---

**Built with ❤️ for transparent, explainable, and compliant government procurement**
