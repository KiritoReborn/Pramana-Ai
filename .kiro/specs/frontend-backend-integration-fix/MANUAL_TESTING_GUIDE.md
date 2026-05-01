# Manual Testing Guide - Frontend-Backend Integration

## Overview

This guide provides step-by-step instructions for manually testing the frontend-backend integration fix. Follow these procedures to verify that all functionality works correctly and no regressions were introduced.

## Prerequisites

### Environment Setup

1. **Backend Server Running**
   ```bash
   # Start the FastAPI backend server
   python -m uvicorn src.api.server:app --reload --port 8000
   ```
   - Verify server starts without errors
   - Check console output shows: "Application startup complete"
   - Backend should be accessible at: http://localhost:8000

2. **Frontend Server Running**
   ```bash
   # Navigate to frontend directory
   cd frontend
   
   # Start the Next.js development server
   npm run dev
   ```
   - Verify server starts without errors
   - Frontend should be accessible at: http://localhost:3000

3. **Browser Developer Tools**
   - Open browser DevTools (F12)
   - Keep Network tab open to monitor API requests
   - Keep Console tab visible to check for errors

4. **Test Data Preparation**
   - Prepare sample bidder documents (PDF, PNG, JPG files)
   - Prepare a sample tender document (PDF)
   - Have multiple test files ready for concurrent upload testing

---

## Test Suite 1: Bug Condition Verification (Expected Behavior)

### Test 1.1: Bidder Document Upload

**Objective**: Verify files are uploaded to backend and processed correctly

**Steps**:
1. Open frontend at http://localhost:3000
2. Select "Bidder" role
3. Navigate to "Document Upload Portal"
4. Click "Choose Files" button
5. Select 2-3 PDF/image files from your test data
6. Click "Start Upload" button

**Expected Results**:
- ✅ File picker opens and allows selection
- ✅ Network tab shows POST request to `http://localhost:8000/api/bidder/upload`
- ✅ Request includes multipart form data with files
- ✅ Response status: 200 OK
- ✅ Toast notification shows "Upload successful" or processing status
- ✅ Backend console logs show DocumentProcessor activity
- ✅ Files are processed through OCR and text extraction
- ✅ FAISS index is updated (check `cache/faiss_index.bin` timestamp)

**Failure Indicators**:
- ❌ No network request made
- ❌ CORS error in console
- ❌ 500 Internal Server Error
- ❌ Files not processed by backend
- ❌ Toast shows error message

---

### Test 1.2: Tender Document Upload

**Objective**: Verify tender PDF is uploaded and criteria are extracted

**Steps**:
1. Select "Officer" role
2. Navigate to "Tender Configuration"
3. Click "Upload Master Document"
4. Select a tender PDF file
5. Click upload/submit button

**Expected Results**:
- ✅ Network tab shows POST request to `http://localhost:8000/api/tender/upload`
- ✅ Response status: 200 OK
- ✅ Response body contains extracted eligibility criteria
- ✅ UI updates to display extracted criteria (not mock data)
- ✅ Backend console shows TenderProcessor activity
- ✅ LLM extraction occurs (check for API calls to LLM service)

**Failure Indicators**:
- ❌ No network request made
- ❌ UI still shows hardcoded mock criteria
- ❌ TenderProcessor not invoked
- ❌ No LLM extraction activity

---

### Test 1.3: Evaluation Trigger

**Objective**: Verify evaluation workflow runs and returns real results

**Steps**:
1. Ensure bidder documents and tender are uploaded (Tests 1.1 and 1.2)
2. Navigate to "Evaluation Matrix" view
3. Click "Run Evaluation" button (or equivalent trigger)
4. Wait for evaluation to complete

**Expected Results**:
- ✅ Network tab shows POST request to `http://localhost:8000/api/evaluation/run`
- ✅ Request body includes bidder IDs and criteria
- ✅ Response status: 200 OK
- ✅ Backend console shows EvaluationEngine activity
- ✅ Retrieval engine performs FAISS searches
- ✅ LLM extraction occurs for each criterion
- ✅ Rule engine calculates verdicts
- ✅ UI updates with real evaluation results (not mock data)
- ✅ Bidder statuses show: "Eligible", "Ineligible", or "Needs Review"

**Failure Indicators**:
- ❌ No network request made
- ❌ UI still shows mock data
- ❌ EvaluationEngine not invoked
- ❌ No retrieval or LLM activity

---

### Test 1.4: Review Modal with Real Evidence

**Objective**: Verify review modal fetches actual evidence from backend

**Steps**:
1. Complete evaluation (Test 1.3)
2. Identify a bidder with "Needs Review" status
3. Click "Review Case" button for that bidder
4. Observe modal content

**Expected Results**:
- ✅ Network tab shows GET request to `http://localhost:8000/api/review/evidence/{bidder_id}/{criterion_id}`
- ✅ Response status: 200 OK
- ✅ Response contains evidence chunks, extracted text, confidence scores
- ✅ Modal displays real evidence (not hardcoded mock text)
- ✅ Evidence chunks match actual document content
- ✅ Confidence scores are realistic (0.0 - 1.0 range)

**Failure Indicators**:
- ❌ No network request made
- ❌ Modal shows hardcoded mock evidence
- ❌ Evidence doesn't match uploaded documents
- ❌ RetrievalEngine not invoked

---

### Test 1.5: Manual Override Submission

**Objective**: Verify overrides are persisted to backend audit logs

**Steps**:
1. Open review modal (Test 1.4)
2. Select override verdict (e.g., "Eligible" or "Ineligible")
3. Enter justification text
4. Click "Confirm Override" button

**Expected Results**:
- ✅ Network tab shows POST request to `http://localhost:8000/api/review/override`
- ✅ Request body includes bidder_id, criterion_id, verdict, justification
- ✅ Response status: 200 OK
- ✅ Backend writes to audit log file in `audit_logs/` directory
- ✅ Check `audit_logs/decisions_YYYYMMDD.jsonl` for new entry
- ✅ Final verdict is recalculated based on override
- ✅ UI updates to reflect new verdict

**Failure Indicators**:
- ❌ No network request made
- ❌ Override only stored in local React state
- ❌ No audit log entry created
- ❌ Verdict not recalculated

---

### Test 1.6: PDF Report Generation

**Objective**: Verify real PDF reports are generated and downloaded

**Steps**:
1. Complete evaluation (Test 1.3)
2. Navigate to "Reports" view
3. Click "Export Final PDF Report" for a bidder
4. Observe download behavior

**Expected Results**:
- ✅ Network tab shows GET request to `http://localhost:8000/api/reports/generate/{bidder_id}`
- ✅ Response status: 200 OK
- ✅ Response Content-Type: `application/pdf`
- ✅ Browser downloads a PDF file (not a text file)
- ✅ Backend console shows ReportGenerator activity
- ✅ Open downloaded PDF and verify:
  - Contains bidder information
  - Shows evaluation results
  - Includes evidence summaries
  - Has proper formatting (not mock text)

**Failure Indicators**:
- ❌ No network request made
- ❌ Downloads a text file instead of PDF
- ❌ PDF is empty or corrupted
- ❌ ReportGenerator not invoked

---

### Test 1.7: Batch Report Generation

**Objective**: Verify multiple PDFs can be generated as ZIP

**Steps**:
1. Complete evaluation for multiple bidders
2. Navigate to "Reports" view
3. Select multiple bidders
4. Click "Generate Batch Reports" or equivalent
5. Observe download behavior

**Expected Results**:
- ✅ Network tab shows GET request to `http://localhost:8000/api/reports/batch`
- ✅ Request includes multiple bidder IDs
- ✅ Response status: 200 OK
- ✅ Response Content-Type: `application/zip`
- ✅ Browser downloads a ZIP file
- ✅ Extract ZIP and verify:
  - Contains multiple PDF files
  - Each PDF corresponds to a bidder
  - All PDFs are valid and complete

**Failure Indicators**:
- ❌ No network request made
- ❌ Downloads individual files instead of ZIP
- ❌ ZIP is corrupted or empty

---

### Test 1.8: Application Startup Health Check

**Objective**: Verify frontend establishes connection to backend on startup

**Steps**:
1. Stop frontend server
2. Clear browser cache
3. Restart frontend server
4. Open http://localhost:3000 in browser
5. Observe initial page load

**Expected Results**:
- ✅ Network tab shows GET request to `http://localhost:8000/api/health`
- ✅ Response status: 200 OK
- ✅ Response body contains API version and status
- ✅ No console errors about backend unavailability
- ✅ UI displays normally (not in error state)

**Failure Indicators**:
- ❌ No health check request made
- ❌ Console shows "Failed to connect to backend"
- ❌ UI shows error banner

---

## Test Suite 2: Preservation Verification (No Regressions)

### Test 2.1: Font Size Controls

**Objective**: Verify font controls work without API calls

**Steps**:
1. Open frontend
2. Click "A-" button (decrease font)
3. Click "A" button (normal font)
4. Click "A+" button (increase font)
5. Monitor Network tab

**Expected Results**:
- ✅ Font size changes immediately
- ✅ NO network requests made to backend
- ✅ Changes are purely client-side
- ✅ Font scale applies to all text elements

**Failure Indicators**:
- ❌ Font size doesn't change
- ❌ Unexpected API calls made
- ❌ UI breaks or errors occur

---

### Test 2.2: Language Toggle

**Objective**: Verify language toggle works without API calls

**Steps**:
1. Open frontend
2. Click language toggle button
3. Switch between English and Kannada
4. Monitor Network tab

**Expected Results**:
- ✅ Language changes immediately
- ✅ NO network requests made to backend
- ✅ UI text updates to selected language
- ✅ Language preference persists across page navigation

**Failure Indicators**:
- ❌ Language doesn't change
- ❌ Unexpected API calls made
- ❌ Some text remains in wrong language

---

### Test 2.3: Role Selection

**Objective**: Verify role selection works without API calls

**Steps**:
1. Open frontend at role selection page
2. Click "Bidder" role
3. Verify bidder menu appears
4. Go back to role selection
5. Click "Officer" role
6. Verify officer menu appears
7. Monitor Network tab

**Expected Results**:
- ✅ Role selection updates immediately
- ✅ NO network requests made to backend
- ✅ Correct menu displays for each role
- ✅ Role-specific views are accessible

**Failure Indicators**:
- ❌ Role doesn't change
- ❌ Wrong menu displays
- ❌ Unexpected API calls made

---

### Test 2.4: Sidebar Navigation

**Objective**: Verify sidebar navigation works without breaking

**Steps**:
1. Select a role (Bidder or Officer)
2. Click each menu item in sidebar
3. Verify each view loads correctly
4. Monitor for errors

**Expected Results**:
- ✅ All menu items are clickable
- ✅ Each view loads without errors
- ✅ Active menu item is highlighted
- ✅ Navigation is smooth and responsive

**Failure Indicators**:
- ❌ Menu items don't respond to clicks
- ❌ Views fail to load
- ❌ Console errors appear
- ❌ Active state doesn't update

---

### Test 2.5: Toast Notifications

**Objective**: Verify toast notifications display correctly

**Steps**:
1. Trigger various actions that show toasts:
   - Upload files
   - Submit forms
   - Trigger errors (e.g., upload without selecting files)
2. Observe toast behavior

**Expected Results**:
- ✅ Toasts appear at bottom of screen
- ✅ Toasts auto-dismiss after timeout
- ✅ Multiple toasts stack correctly
- ✅ Toast styling matches design

**Failure Indicators**:
- ❌ Toasts don't appear
- ❌ Toasts don't dismiss
- ❌ Toasts overlap incorrectly
- ❌ Styling is broken

---

### Test 2.6: Modal Overlays

**Objective**: Verify modals open and close correctly

**Steps**:
1. Open review modal (click "Review Case")
2. Verify modal displays with overlay
3. Click outside modal or close button
4. Verify modal closes
5. Test with different modal types

**Expected Results**:
- ✅ Modal opens with dark overlay
- ✅ Modal content is centered
- ✅ Modal closes on outside click or close button
- ✅ Scrolling is disabled when modal is open
- ✅ Modal styling matches design

**Failure Indicators**:
- ❌ Modal doesn't open
- ❌ Modal doesn't close
- ❌ Overlay is missing or broken
- ❌ Page scrolls behind modal

---

### Test 2.7: Streamlit App Independence

**Objective**: Verify Streamlit app continues working independently

**Steps**:
1. Keep FastAPI server running
2. Start Streamlit app:
   ```bash
   streamlit run src/ui/app.py
   ```
3. Open Streamlit app at http://localhost:8501
4. Test all Streamlit functionality:
   - Upload documents
   - Upload tender
   - Run evaluation
   - View results
   - Generate reports

**Expected Results**:
- ✅ Streamlit app starts without errors
- ✅ All Streamlit features work as before
- ✅ Document processing works
- ✅ Evaluation engine works
- ✅ Report generation works
- ✅ No interference from FastAPI server

**Failure Indicators**:
- ❌ Streamlit app fails to start
- ❌ Features are broken
- ❌ Errors about port conflicts
- ❌ Processing fails

---

### Test 2.8: Backend Processing Direct Calls

**Objective**: Verify backend classes work when called directly (not via API)

**Steps**:
1. Open Python REPL or create test script
2. Import and test backend classes directly:
   ```python
   from src.processors.document_processor import DocumentProcessor
   from src.processors.tender_processor import TenderProcessor
   from src.engines.evaluation_engine import EvaluationEngine
   
   # Test DocumentProcessor
   processor = DocumentProcessor()
   result = processor.process_document("path/to/test.pdf")
   
   # Test TenderProcessor
   tender_proc = TenderProcessor()
   criteria = tender_proc.extract_criteria("path/to/tender.pdf")
   
   # Test EvaluationEngine
   eval_engine = EvaluationEngine()
   results = eval_engine.evaluate(bidder_id, criteria)
   ```

**Expected Results**:
- ✅ All classes import without errors
- ✅ All methods work as before
- ✅ Results match expected output
- ✅ No API-related dependencies break direct usage

**Failure Indicators**:
- ❌ Import errors
- ❌ Methods fail or return different results
- ❌ Classes require API context to work

---

## Test Suite 3: Integration & Edge Cases

### Test 3.1: Full Bidder Workflow

**Objective**: Test complete bidder journey end-to-end

**Steps**:
1. Select "Bidder" role
2. Navigate to "Available Tenders"
3. Click "Apply" on a tender
4. Navigate to "Document Upload Portal"
5. Upload required documents
6. Navigate to "My Submissions"
7. Verify submission appears
8. Wait for evaluation to complete (or trigger manually)
9. Check evaluation status

**Expected Results**:
- ✅ All steps complete without errors
- ✅ Documents are uploaded and processed
- ✅ Submission appears in list
- ✅ Evaluation results are displayed
- ✅ Status updates correctly (Pending → Evaluated)

**Failure Indicators**:
- ❌ Any step fails
- ❌ Data doesn't persist between views
- ❌ Evaluation doesn't run

---

### Test 3.2: Full Officer Workflow

**Objective**: Test complete officer journey end-to-end

**Steps**:
1. Select "Officer" role
2. Navigate to "Tender Configuration"
3. Upload tender document
4. Verify criteria extraction
5. Navigate to "Evaluation Matrix"
6. Trigger evaluation for all bidders
7. Wait for evaluation to complete
8. Review "Needs Review" cases
9. Submit overrides where needed
10. Navigate to "Reports"
11. Generate individual and batch reports

**Expected Results**:
- ✅ All steps complete without errors
- ✅ Tender is processed correctly
- ✅ Evaluation runs successfully
- ✅ Review workflow functions properly
- ✅ Overrides are persisted
- ✅ Reports are generated correctly

**Failure Indicators**:
- ❌ Any step fails
- ❌ Evaluation doesn't complete
- ❌ Overrides are lost
- ❌ Reports are invalid

---

### Test 3.3: Concurrent File Uploads

**Objective**: Test multiple users uploading simultaneously

**Steps**:
1. Open frontend in 2-3 different browser windows/tabs
2. In each window, select "Bidder" role with different bidder IDs
3. Simultaneously upload files in all windows
4. Monitor backend console and network requests

**Expected Results**:
- ✅ All uploads succeed
- ✅ No race conditions or conflicts
- ✅ Each bidder's files are processed separately
- ✅ FAISS index updates correctly for all
- ✅ No data corruption

**Failure Indicators**:
- ❌ Some uploads fail
- ❌ Files get mixed between bidders
- ❌ Backend crashes or errors
- ❌ FAISS index corruption

---

### Test 3.4: Session Isolation

**Objective**: Verify different users see different data

**Steps**:
1. Open frontend in 2 browser windows (use incognito for second)
2. Window 1: Upload documents as Bidder A
3. Window 2: Upload documents as Bidder B
4. Verify each window shows only its own data
5. Check session IDs in network requests

**Expected Results**:
- ✅ Each window has unique session ID
- ✅ Bidder A sees only their documents
- ✅ Bidder B sees only their documents
- ✅ No data leakage between sessions

**Failure Indicators**:
- ❌ Same session ID in both windows
- ❌ Users see each other's data
- ❌ Data gets mixed between sessions

---

### Test 3.5: API Server Restart

**Objective**: Verify stateless behavior on server restart

**Steps**:
1. Upload documents and run evaluation
2. Stop FastAPI server (Ctrl+C)
3. Restart FastAPI server
4. Refresh frontend
5. Try to access previous data

**Expected Results**:
- ✅ Server restarts without errors
- ✅ Session data is lost (expected - in-memory storage)
- ✅ FAISS index persists (file-based cache)
- ✅ Audit logs persist (file-based)
- ✅ Frontend handles missing session gracefully

**Failure Indicators**:
- ❌ Server fails to restart
- ❌ FAISS index is corrupted
- ❌ Audit logs are lost
- ❌ Frontend crashes on missing data

---

### Test 3.6: CORS Configuration

**Objective**: Verify CORS allows frontend to call backend

**Steps**:
1. Open frontend at http://localhost:3000
2. Make any API call (e.g., upload file)
3. Check browser console for CORS errors
4. Verify Network tab shows successful requests

**Expected Results**:
- ✅ No CORS errors in console
- ✅ Requests complete successfully
- ✅ Response headers include:
  - `Access-Control-Allow-Origin: http://localhost:3000`
  - `Access-Control-Allow-Credentials: true`

**Failure Indicators**:
- ❌ CORS error in console
- ❌ Requests are blocked
- ❌ Missing CORS headers

---

### Test 3.7: Error Handling - Network Failure

**Objective**: Verify graceful handling of network errors

**Steps**:
1. Start frontend
2. Stop backend server
3. Try to upload files or trigger evaluation
4. Observe error handling

**Expected Results**:
- ✅ Frontend shows user-friendly error message
- ✅ Toast notification displays error
- ✅ No console crashes or unhandled exceptions
- ✅ UI remains functional (can retry)

**Failure Indicators**:
- ❌ Frontend crashes
- ❌ No error message shown
- ❌ Unhandled promise rejections in console
- ❌ UI becomes unresponsive

---

### Test 3.8: Error Handling - Backend Processing Failure

**Objective**: Verify graceful handling of backend errors

**Steps**:
1. Upload a corrupted or invalid file
2. Upload a file that causes processing to fail
3. Observe error handling

**Expected Results**:
- ✅ Backend returns appropriate error status (400 or 500)
- ✅ Error response includes descriptive message
- ✅ Frontend displays error to user
- ✅ No backend crash
- ✅ Subsequent requests still work

**Failure Indicators**:
- ❌ Backend crashes
- ❌ No error message returned
- ❌ Frontend doesn't handle error
- ❌ System becomes unusable

---

### Test 3.9: Large File Upload

**Objective**: Test handling of large files

**Steps**:
1. Prepare a large PDF file (10+ MB)
2. Upload via frontend
3. Monitor upload progress and processing

**Expected Results**:
- ✅ Upload completes successfully
- ✅ Progress indicator shows upload status
- ✅ Backend processes file without timeout
- ✅ FAISS indexing completes
- ✅ No memory issues

**Failure Indicators**:
- ❌ Upload times out
- ❌ Backend runs out of memory
- ❌ Processing fails
- ❌ No progress indication

---

### Test 3.10: Multiple File Types

**Objective**: Verify all supported file types work

**Steps**:
1. Upload PDF file
2. Upload PNG image
3. Upload JPG image
4. Upload JPEG image
5. Try uploading unsupported type (e.g., .txt)

**Expected Results**:
- ✅ PDF, PNG, JPG, JPEG all process successfully
- ✅ OCR works on images
- ✅ Text extraction works on PDFs
- ✅ Unsupported types are rejected with clear error

**Failure Indicators**:
- ❌ Some file types fail to process
- ❌ OCR doesn't work on images
- ❌ Unsupported types are accepted

---

## Test Suite 4: Performance & Reliability

### Test 4.1: Response Time

**Objective**: Verify API responses are reasonably fast

**Steps**:
1. Upload small file (< 1 MB)
2. Check Network tab for response time
3. Repeat for different endpoints

**Expected Results**:
- ✅ File upload: < 5 seconds
- ✅ Evaluation trigger: < 10 seconds (depends on complexity)
- ✅ Report generation: < 3 seconds
- ✅ Evidence retrieval: < 2 seconds

**Failure Indicators**:
- ❌ Requests take excessively long
- ❌ Timeouts occur
- ❌ UI becomes unresponsive

---

### Test 4.2: Memory Usage

**Objective**: Verify no memory leaks

**Steps**:
1. Monitor backend process memory usage
2. Upload multiple files
3. Run evaluations multiple times
4. Check memory usage over time

**Expected Results**:
- ✅ Memory usage stays relatively stable
- ✅ No continuous memory growth
- ✅ Garbage collection works properly

**Failure Indicators**:
- ❌ Memory usage continuously increases
- ❌ Backend crashes with out-of-memory error
- ❌ System becomes slow over time

---

## Checklist Summary

Use this checklist to track your manual testing progress:

### Bug Condition Tests (Expected Behavior)
- [ ] 1.1 Bidder Document Upload
- [ ] 1.2 Tender Document Upload
- [ ] 1.3 Evaluation Trigger
- [ ] 1.4 Review Modal with Real Evidence
- [ ] 1.5 Manual Override Submission
- [ ] 1.6 PDF Report Generation
- [ ] 1.7 Batch Report Generation
- [ ] 1.8 Application Startup Health Check

### Preservation Tests (No Regressions)
- [ ] 2.1 Font Size Controls
- [ ] 2.2 Language Toggle
- [ ] 2.3 Role Selection
- [ ] 2.4 Sidebar Navigation
- [ ] 2.5 Toast Notifications
- [ ] 2.6 Modal Overlays
- [ ] 2.7 Streamlit App Independence
- [ ] 2.8 Backend Processing Direct Calls

### Integration & Edge Cases
- [ ] 3.1 Full Bidder Workflow
- [ ] 3.2 Full Officer Workflow
- [ ] 3.3 Concurrent File Uploads
- [ ] 3.4 Session Isolation
- [ ] 3.5 API Server Restart
- [ ] 3.6 CORS Configuration
- [ ] 3.7 Error Handling - Network Failure
- [ ] 3.8 Error Handling - Backend Processing Failure
- [ ] 3.9 Large File Upload
- [ ] 3.10 Multiple File Types

### Performance & Reliability
- [ ] 4.1 Response Time
- [ ] 4.2 Memory Usage

---

## Reporting Issues

When you find an issue during manual testing, document it with:

1. **Test Case**: Which test case failed
2. **Steps to Reproduce**: Exact steps that caused the issue
3. **Expected Result**: What should have happened
4. **Actual Result**: What actually happened
5. **Screenshots**: Browser console, network tab, error messages
6. **Environment**: Browser version, OS, server versions
7. **Severity**: Critical, High, Medium, Low

---

## Notes

- Run automated tests first before manual testing
- Manual testing should focus on user experience and edge cases
- Test in multiple browsers (Chrome, Firefox, Safari, Edge)
- Test on different screen sizes (desktop, tablet, mobile)
- Keep detailed notes of any unexpected behavior
- Retest after fixes are applied
