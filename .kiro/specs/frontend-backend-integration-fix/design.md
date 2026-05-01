# Frontend-Backend Integration Bugfix Design

## Overview

The Next.js frontend is currently a non-functional UI mockup completely disconnected from the Python backend. This design addresses the complete integration by creating a REST API layer that exposes all backend functionality (document processing, tender processing, evaluation engine, retrieval engine, report generation) to the frontend. The fix implements a FastAPI server that bridges the Next.js frontend with the existing Python backend components while preserving the Streamlit app's independent functionality.

The integration enables bidders to upload documents for processing, officers to configure tenders and run evaluations, and both roles to access real-time evaluation results and PDF reports. All file uploads, processing status, and data retrieval will flow through well-defined API endpoints with proper error handling and session management.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when frontend UI interactions (button clicks, file uploads, navigation) fail to communicate with the Python backend
- **Property (P)**: The desired behavior when frontend interactions occur - data should flow to/from backend via REST API endpoints
- **Preservation**: Existing Streamlit app functionality and backend processing logic that must remain unchanged
- **DocumentProcessor**: The class in `src/processors/document_processor.py` that handles PDF/image processing with OCR and text extraction
- **TenderProcessor**: The class in `src/processors/tender_processor.py` that extracts eligibility criteria from tender PDFs using LLM
- **EvaluationEngine**: The class in `src/engines/evaluation_engine.py` that orchestrates criterion-by-criterion evaluation using retrieval and LLM extraction
- **RetrievalEngine**: The class in `src/engines/retrieval_engine.py` that performs FAISS-based semantic search over bidder documents
- **ReportGenerator**: The class in `src/engines/report_generator.py` that generates PDF reports using ReportLab
- **FastAPI**: Python web framework for building REST APIs with automatic OpenAPI documentation
- **Multipart Form Data**: HTTP encoding for file uploads in web forms
- **Session State**: Server-side storage of user-specific data (uploaded files, evaluation results) across multiple API requests
- **CORS**: Cross-Origin Resource Sharing - mechanism to allow frontend (port 3000) to call backend API (port 8000)

## Bug Details

### Bug Condition

The bug manifests when users interact with any frontend UI element that should trigger backend processing. The Next.js frontend has no API client, no endpoint configuration, and no data fetching logic. All button clicks only update local React state without making HTTP requests to the Python backend.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type UserInteraction (button click, file upload, navigation)
  OUTPUT: boolean
  
  RETURN input.type IN ['file_upload', 'button_click', 'navigation', 'form_submit']
         AND input.requiresBackendData = true
         AND NOT apiRequestMade(input)
         AND NOT backendDataFetched(input)
END FUNCTION
```

### Examples

- **Bidder Document Upload**: User clicks "Choose Files" and "Start Upload" → Files are selected but never sent to DocumentProcessor → No OCR processing occurs → No FAISS indexing happens
- **Tender Configuration**: Officer clicks "Upload Master Document" → File is selected but never sent to TenderProcessor → No criteria extraction occurs → Evaluation Matrix shows hardcoded mock data
- **Evaluation Trigger**: Officer clicks "Run Evaluation" → No API call to EvaluationEngine → Evaluation Matrix continues showing mock data instead of real results
- **Review Workflow**: Officer clicks "Review Case" → Modal opens with hardcoded mock evidence instead of fetching actual evidence chunks from RetrievalEngine
- **Manual Override**: Officer clicks "Confirm Override" → Override is stored in local state but never persisted to backend audit logs
- **PDF Report Download**: Officer clicks "Export Final PDF Report" → Downloads mock text file instead of calling ReportGenerator to create real PDF
- **Navigation**: User switches between pages → Only local view state changes, no data fetching from backend for the new view
- **Application Startup**: Frontend loads → No connection established to backend API → No health check or availability verification

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Streamlit app in `src/ui/app.py` must continue to function independently without breaking
- All backend processing classes (DocumentProcessor, TenderProcessor, EvaluationEngine, RetrievalEngine, RuleEngine, ReportGenerator) must remain unchanged
- Existing Pydantic schemas in `src/models/schemas.py` must be reused without modification
- FAISS index caching and embedding precomputation must continue working
- Audit logging to `audit_logs/` directory must continue functioning
- Frontend UI styling, government portal aesthetic, and bilingual support must remain unchanged
- Font size controls and language toggle must continue working
- Role selection page and role-based views must remain unchanged
- Toast notifications and modal overlays must continue displaying as currently implemented

**Scope:**
All inputs that do NOT involve backend data (pure UI interactions like font size adjustment, language toggle, role selection, sidebar navigation state) should be completely unaffected by this fix. This includes:
- Font scale controls (A-, A, A+)
- Language toggle (English/Kannada)
- Role selection (Bidder vs Officer)
- Sidebar menu state changes
- Modal open/close state
- Toast notification display
- CSS styling and visual design

## Hypothesized Root Cause

Based on the bug description, the root causes are:

1. **Missing API Layer**: No REST API server exists to expose backend functionality
   - Frontend has no endpoints to call
   - Backend classes are designed for direct Python usage, not HTTP requests
   - No FastAPI or Flask server implementation

2. **No API Client in Frontend**: Frontend has no HTTP client configuration
   - No fetch() or axios calls in frontend code
   - No API base URL configuration
   - No error handling for network requests

3. **File Upload Not Implemented**: No multipart form data handling
   - Frontend file input doesn't send files to backend
   - Backend has no endpoint to receive uploaded files
   - No temporary file storage for processing

4. **Session Management Missing**: No way to track user-specific data across requests
   - Uploaded documents need to be associated with bidders
   - Evaluation results need to be stored per session
   - No session ID or authentication mechanism

5. **CORS Not Configured**: Frontend (localhost:3000) cannot call backend (localhost:8000)
   - Browser blocks cross-origin requests by default
   - No CORS middleware configured in backend

## Correctness Properties

Property 1: Bug Condition - Frontend-Backend Communication

_For any_ user interaction where backend data is required (file upload, evaluation trigger, report generation), the fixed system SHALL make an HTTP request to the appropriate REST API endpoint, receive a response from the Python backend, and update the UI with real data from backend processing.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12**

Property 2: Preservation - Existing Backend Functionality

_For any_ backend processing operation (document processing, tender processing, evaluation, report generation), the fixed system SHALL produce exactly the same results as the original backend code, preserving all existing functionality for the Streamlit app and maintaining all processing logic, schemas, and audit logging.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `src/api/server.py` (NEW FILE)

**Purpose**: FastAPI server that exposes backend functionality via REST endpoints

**Specific Changes**:
1. **Create FastAPI Application**: Initialize FastAPI app with CORS middleware to allow frontend (localhost:3000) to make requests
   - Configure CORS to allow origins: ["http://localhost:3000"]
   - Enable credentials, all methods, all headers

2. **Implement File Upload Endpoints**:
   - `POST /api/bidder/upload` - Accept multipart form data with files and bidder_id, process through DocumentProcessor, index in FAISS, return processing status
   - `POST /api/tender/upload` - Accept tender PDF, process through TenderProcessor, return extracted criteria

3. **Implement Evaluation Endpoints**:
   - `POST /api/evaluation/run` - Accept bidder_id and criteria, run EvaluationEngine, return evaluation results
   - `GET /api/evaluation/results/{bidder_id}` - Retrieve stored evaluation results for a bidder

4. **Implement Review Endpoints**:
   - `GET /api/review/evidence/{bidder_id}/{criterion_id}` - Fetch evidence chunks from RetrievalEngine for review modal
   - `POST /api/review/override` - Accept manual override data, persist to audit logs, recalculate verdict

5. **Implement Report Endpoints**:
   - `GET /api/reports/generate/{bidder_id}` - Generate PDF using ReportGenerator, return PDF file
   - `GET /api/reports/batch` - Generate multiple PDFs, return ZIP file

6. **Implement Session Management**:
   - Use in-memory dictionary to store session data (uploaded documents, evaluation results) keyed by session_id
   - Generate session_id on first request, return in response headers
   - Accept session_id in request headers for subsequent requests

7. **Implement Health Check**:
   - `GET /api/health` - Return API status and version information

**File**: `frontend/lib/api.ts` (NEW FILE)

**Purpose**: API client for frontend to call backend endpoints

**Specific Changes**:
1. **Configure API Base URL**: Set base URL to `http://localhost:8000`

2. **Implement File Upload Functions**:
   - `uploadBidderDocuments(files: File[], bidderId: string)` - Send files to `/api/bidder/upload`
   - `uploadTenderDocument(file: File)` - Send tender PDF to `/api/tender/upload`

3. **Implement Evaluation Functions**:
   - `runEvaluation(bidderIds: string[], criteria: any[])` - Call `/api/evaluation/run`
   - `getEvaluationResults(bidderId: string)` - Call `/api/evaluation/results/{bidder_id}`

4. **Implement Review Functions**:
   - `getReviewEvidence(bidderId: string, criterionId: string)` - Call `/api/review/evidence/{bidder_id}/{criterion_id}`
   - `submitOverride(data: OverrideData)` - Call `/api/review/override`

5. **Implement Report Functions**:
   - `generateReport(bidderId: string)` - Call `/api/reports/generate/{bidder_id}`, handle PDF download
   - `generateBatchReports(bidderIds: string[])` - Call `/api/reports/batch`, handle ZIP download

6. **Implement Error Handling**: Wrap all API calls in try-catch, handle network errors, parse error responses

**File**: `frontend/app/page.tsx` (MODIFY)

**Purpose**: Replace mock data and local state with real API calls

**Specific Changes**:
1. **Replace File Upload Logic**: In "Choose Files" and "Start Upload" buttons, call `uploadBidderDocuments()` instead of just showing toast

2. **Replace Tender Upload Logic**: In "Upload Master Document" button, call `uploadTenderDocument()` and update extractedCriteria state with real data

3. **Replace Evaluation Trigger**: In "Run Evaluation" button (implied in matrix view), call `runEvaluation()` and update bidderMatrix state with real results

4. **Replace Review Modal Data**: In "Review Case" button, call `getReviewEvidence()` and populate modal with real evidence chunks

5. **Replace Override Logic**: In "Confirm Override" button, call `submitOverride()` instead of just updating local state

6. **Replace Report Download**: In "Export Final PDF Report" button, call `generateReport()` and trigger browser download of real PDF

7. **Add Loading States**: Show spinners/progress indicators during API calls

8. **Add Error Handling**: Display error messages from API in toast notifications

**File**: `requirements.txt` (MODIFY)

**Purpose**: Add FastAPI dependencies

**Specific Changes**:
1. Add `fastapi>=0.104.0`
2. Add `uvicorn[standard]>=0.24.0`
3. Add `python-multipart>=0.0.6` (for file uploads)

**File**: `frontend/package.json` (MODIFY)

**Purpose**: Add API client dependencies if needed

**Specific Changes**:
1. No new dependencies needed - use native fetch() API

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate frontend interactions and verify that NO API requests are made and NO backend processing occurs. Run these tests on the UNFIXED code to observe failures and understand the root cause.

**Test Cases**:
1. **File Upload Test**: Simulate clicking "Start Upload" with files selected (will fail on unfixed code - no API request made)
2. **Tender Upload Test**: Simulate clicking "Upload Master Document" (will fail on unfixed code - no criteria extracted)
3. **Evaluation Test**: Simulate clicking evaluation trigger (will fail on unfixed code - mock data remains)
4. **Review Modal Test**: Simulate clicking "Review Case" (will fail on unfixed code - shows hardcoded evidence)
5. **Override Test**: Simulate clicking "Confirm Override" (will fail on unfixed code - not persisted to audit logs)
6. **Report Download Test**: Simulate clicking "Export Final PDF Report" (will fail on unfixed code - downloads text file)

**Expected Counterexamples**:
- No HTTP requests are made when buttons are clicked
- Possible causes: no API client, no endpoints, no fetch() calls in frontend code

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := handleUserInteraction_fixed(input)
  ASSERT apiRequestMade(result)
  ASSERT backendDataFetched(result)
  ASSERT uiUpdatedWithRealData(result)
END FOR
```

**Test Plan**: After implementing the fix, verify that all frontend interactions make API requests and receive real backend data.

**Test Cases**:
1. **File Upload Integration Test**: Upload files via frontend → Verify API request to `/api/bidder/upload` → Verify DocumentProcessor called → Verify FAISS indexing occurs
2. **Tender Upload Integration Test**: Upload tender PDF → Verify API request to `/api/tender/upload` → Verify TenderProcessor called → Verify criteria extracted
3. **Evaluation Integration Test**: Trigger evaluation → Verify API request to `/api/evaluation/run` → Verify EvaluationEngine called → Verify real results returned
4. **Review Integration Test**: Open review modal → Verify API request to `/api/review/evidence` → Verify RetrievalEngine called → Verify real evidence displayed
5. **Override Integration Test**: Submit override → Verify API request to `/api/review/override` → Verify audit log written → Verify verdict recalculated
6. **Report Integration Test**: Download report → Verify API request to `/api/reports/generate` → Verify ReportGenerator called → Verify real PDF downloaded

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT frontendUIBehavior_original(input) = frontendUIBehavior_fixed(input)
  ASSERT backendProcessing_original(input) = backendProcessing_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for pure UI interactions and backend processing, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Font Size Preservation**: Verify clicking A-, A, A+ continues to adjust font scale without API calls
2. **Language Toggle Preservation**: Verify language toggle continues to work without API calls
3. **Role Selection Preservation**: Verify role selection continues to work without API calls
4. **Streamlit App Preservation**: Run Streamlit app independently, verify all functionality works unchanged
5. **Backend Processing Preservation**: Call backend classes directly (not via API), verify same results as before
6. **Schema Preservation**: Verify all Pydantic schemas remain unchanged and validation works
7. **Audit Logging Preservation**: Verify audit logs continue writing to `audit_logs/` directory

### Unit Tests

- Test FastAPI endpoints with mock backend classes
- Test API client functions with mock fetch responses
- Test file upload multipart encoding
- Test session management (session ID generation, storage, retrieval)
- Test CORS configuration
- Test error handling for network failures
- Test error handling for backend processing failures

### Property-Based Tests

- Generate random file uploads and verify all are processed correctly
- Generate random evaluation requests and verify all return valid results
- Generate random override submissions and verify all are persisted
- Test that all pure UI interactions continue working across many scenarios
- Test that backend processing produces same results when called directly vs via API

### Integration Tests

- Test full bidder workflow: upload documents → view in submissions → wait for evaluation
- Test full officer workflow: upload tender → extract criteria → run evaluation → review cases → download reports
- Test concurrent access: multiple users uploading files simultaneously
- Test session isolation: different users see different data
- Test Streamlit app continues working while API server is running
- Test API server restart preserves no state (stateless except session data)
