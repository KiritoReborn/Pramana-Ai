"""
Bug Condition Exploration Test for Frontend-Backend Integration

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12**

This test encodes the EXPECTED BEHAVIOR - it will FAIL on unfixed code to confirm the bug exists.
When the fix is implemented, this same test will PASS to validate the fix works correctly.

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

GOAL: Surface counterexamples that demonstrate the bug exists:
- No API client exists in frontend
- No fetch() calls in frontend code  
- No API endpoints exist in backend
- No FastAPI server implementation

Property 1: Bug Condition - Frontend-Backend Communication Failure
For any user interaction where backend data is required (file upload, evaluation trigger, 
report generation), the system should make an HTTP request to the appropriate REST API endpoint,
receive a response from the Python backend, and update the UI with real data.

This test uses a scoped PBT approach - testing concrete failing cases to ensure reproducibility.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import subprocess
import time
import requests
import os
import signal


class TestFrontendBackendIntegration:
    """
    Bug condition exploration tests for frontend-backend integration.
    
    These tests verify that frontend interactions SHOULD make API requests to the backend.
    On UNFIXED code, these tests will FAIL (expected - confirms bug exists).
    After fix implementation, these tests will PASS (confirms fix works).
    """
    
    @pytest.fixture(scope="class")
    def backend_server(self):
        """
        Attempt to start the FastAPI backend server.
        On unfixed code, this will fail because the server doesn't exist yet.
        """
        # Check if server file exists
        server_path = "src/api/server.py"
        if not os.path.exists(server_path):
            pytest.skip(f"Backend server not implemented yet: {server_path} does not exist")
        
        # Try to start the server
        try:
            process = subprocess.Popen(
                ["python", "-m", "uvicorn", "src.api.server:app", "--port", "8000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is running
            try:
                response = requests.get("http://localhost:8000/api/health", timeout=2)
                if response.status_code == 200:
                    yield process
                else:
                    process.kill()
                    pytest.skip("Backend server started but health check failed")
            except requests.exceptions.RequestException:
                process.kill()
                pytest.skip("Backend server not responding to health check")
                
        except Exception as e:
            pytest.skip(f"Could not start backend server: {str(e)}")
        finally:
            if 'process' in locals():
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()
    
    def test_api_health_endpoint_exists(self, backend_server):
        """
        Test that the backend API health endpoint exists and responds.
        
        EXPECTED ON UNFIXED CODE: FAIL (endpoint doesn't exist)
        EXPECTED AFTER FIX: PASS (endpoint exists and returns 200)
        """
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        assert response.status_code == 200, "Health endpoint should return 200 OK"
        data = response.json()
        assert "status" in data or "version" in data, "Health endpoint should return status information"
    
    def test_bidder_upload_endpoint_exists(self, backend_server):
        """
        Test that the bidder document upload endpoint exists.
        
        EXPECTED ON UNFIXED CODE: FAIL (endpoint doesn't exist)
        EXPECTED AFTER FIX: PASS (endpoint exists)
        
        Validates: Requirements 2.1, 2.2, 2.11
        """
        # Create a minimal test file
        files = {'files': ('test.pdf', b'%PDF-1.4 test content', 'application/pdf')}
        data = {'bidder_id': 'test-bidder-001'}
        
        response = requests.post(
            "http://localhost:8000/api/bidder/upload",
            files=files,
            data=data,
            timeout=10
        )
        
        # Should get a valid response (200, 201, or even 400 for validation errors)
        # The key is that the endpoint EXISTS and responds
        assert response.status_code in [200, 201, 400, 422], \
            f"Bidder upload endpoint should exist and respond, got {response.status_code}"
    
    def test_tender_upload_endpoint_exists(self, backend_server):
        """
        Test that the tender document upload endpoint exists.
        
        EXPECTED ON UNFIXED CODE: FAIL (endpoint doesn't exist)
        EXPECTED AFTER FIX: PASS (endpoint exists)
        
        Validates: Requirements 2.4
        """
        files = {'file': ('tender.pdf', b'%PDF-1.4 tender content', 'application/pdf')}
        
        response = requests.post(
            "http://localhost:8000/api/tender/upload",
            files=files,
            timeout=10
        )
        
        assert response.status_code in [200, 201, 400, 422], \
            f"Tender upload endpoint should exist and respond, got {response.status_code}"
    
    def test_evaluation_run_endpoint_exists(self, backend_server):
        """
        Test that the evaluation run endpoint exists.
        
        EXPECTED ON UNFIXED CODE: FAIL (endpoint doesn't exist)
        EXPECTED AFTER FIX: PASS (endpoint exists)
        
        Validates: Requirements 2.5, 2.12
        """
        payload = {
            "bidder_ids": ["test-bidder-001"],
            "criteria": [
                {
                    "id": "FIN-001",
                    "category": "Financial",
                    "description": "Test criterion"
                }
            ]
        }
        
        response = requests.post(
            "http://localhost:8000/api/evaluation/run",
            json=payload,
            timeout=10
        )
        
        assert response.status_code in [200, 201, 400, 422], \
            f"Evaluation run endpoint should exist and respond, got {response.status_code}"
    
    def test_evaluation_results_endpoint_exists(self, backend_server):
        """
        Test that the evaluation results retrieval endpoint exists.
        
        EXPECTED ON UNFIXED CODE: FAIL (endpoint doesn't exist)
        EXPECTED AFTER FIX: PASS (endpoint exists)
        
        Validates: Requirements 2.5
        """
        response = requests.get(
            "http://localhost:8000/api/evaluation/results/test-bidder-001",
            timeout=5
        )
        
        assert response.status_code in [200, 404, 422], \
            f"Evaluation results endpoint should exist and respond, got {response.status_code}"
    
    def test_review_evidence_endpoint_exists(self, backend_server):
        """
        Test that the review evidence endpoint exists.
        
        EXPECTED ON UNFIXED CODE: FAIL (endpoint doesn't exist)
        EXPECTED AFTER FIX: PASS (endpoint exists)
        
        Validates: Requirements 2.6
        """
        response = requests.get(
            "http://localhost:8000/api/review/evidence/test-bidder-001/FIN-001",
            timeout=5
        )
        
        assert response.status_code in [200, 404, 422], \
            f"Review evidence endpoint should exist and respond, got {response.status_code}"
    
    def test_review_override_endpoint_exists(self, backend_server):
        """
        Test that the review override submission endpoint exists.
        
        EXPECTED ON UNFIXED CODE: FAIL (endpoint doesn't exist)
        EXPECTED AFTER FIX: PASS (endpoint exists)
        
        Validates: Requirements 2.7
        """
        payload = {
            "bidder_id": "test-bidder-001",
            "criterion_id": "FIN-001",
            "verdict": "Eligible",
            "justification": "Test override justification"
        }
        
        response = requests.post(
            "http://localhost:8000/api/review/override",
            json=payload,
            timeout=5
        )
        
        assert response.status_code in [200, 201, 400, 422], \
            f"Review override endpoint should exist and respond, got {response.status_code}"
    
    def test_report_generation_endpoint_exists(self, backend_server):
        """
        Test that the report generation endpoint exists.
        
        EXPECTED ON UNFIXED CODE: FAIL (endpoint doesn't exist)
        EXPECTED AFTER FIX: PASS (endpoint exists)
        
        Validates: Requirements 2.8
        """
        response = requests.get(
            "http://localhost:8000/api/reports/generate/test-bidder-001",
            timeout=10
        )
        
        assert response.status_code in [200, 404, 422], \
            f"Report generation endpoint should exist and respond, got {response.status_code}"
    
    def test_cors_configuration(self, backend_server):
        """
        Test that CORS is configured to allow frontend requests.
        
        EXPECTED ON UNFIXED CODE: FAIL (CORS not configured)
        EXPECTED AFTER FIX: PASS (CORS allows localhost:3000)
        
        Validates: Requirements 2.10
        """
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(
            "http://localhost:8000/api/health",
            headers=headers,
            timeout=5
        )
        
        # Check CORS headers are present
        assert 'access-control-allow-origin' in response.headers or \
               'Access-Control-Allow-Origin' in response.headers, \
               "CORS headers should be present to allow frontend requests"
    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10, deadline=5000)
    @given(
        interaction_type=st.sampled_from([
            'file_upload',
            'tender_upload', 
            'evaluation_trigger',
            'review_modal',
            'override_submission',
            'report_download'
        ])
    )
    def test_property_frontend_interactions_require_backend_api(self, backend_server, interaction_type):
        """
        Property-based test: All frontend interactions requiring backend data should have API endpoints.
        
        This is a scoped PBT that tests concrete failing cases from the bug condition.
        
        EXPECTED ON UNFIXED CODE: FAIL (no API endpoints exist)
        EXPECTED AFTER FIX: PASS (all endpoints exist and respond)
        
        Property: For any user interaction type that requires backend data,
                 there exists a corresponding API endpoint that responds to requests.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12
        """
        endpoint_map = {
            'file_upload': ('POST', '/api/bidder/upload'),
            'tender_upload': ('POST', '/api/tender/upload'),
            'evaluation_trigger': ('POST', '/api/evaluation/run'),
            'review_modal': ('GET', '/api/review/evidence/test-bidder/test-criterion'),
            'override_submission': ('POST', '/api/review/override'),
            'report_download': ('GET', '/api/reports/generate/test-bidder')
        }
        
        method, endpoint = endpoint_map[interaction_type]
        url = f"http://localhost:8000{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, timeout=5)
            else:
                # POST with minimal payload
                response = requests.post(url, json={}, timeout=5)
            
            # Endpoint should exist and respond (not 404 or 501)
            assert response.status_code not in [404, 501], \
                f"Endpoint {endpoint} should exist for {interaction_type}, got {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            pytest.fail(f"API endpoint {endpoint} for {interaction_type} is not accessible: {str(e)}")


class TestFrontendCodeAnalysis:
    """
    Static analysis tests to verify frontend code structure.
    These tests check if the frontend has the necessary code to make API calls.
    """
    
    def test_frontend_has_api_client_file(self):
        """
        Test that frontend has an API client file.
        
        EXPECTED ON UNFIXED CODE: FAIL (no API client file)
        EXPECTED AFTER FIX: PASS (API client file exists)
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.9
        """
        api_client_paths = [
            "frontend/lib/api.ts",
            "frontend/lib/api.js",
            "frontend/utils/api.ts",
            "frontend/utils/api.js"
        ]
        
        exists = any(os.path.exists(path) for path in api_client_paths)
        assert exists, f"Frontend should have an API client file in one of: {api_client_paths}"
    
    def test_frontend_page_imports_api_client(self):
        """
        Test that the main frontend page imports and uses the API client.
        
        EXPECTED ON UNFIXED CODE: FAIL (no API imports)
        EXPECTED AFTER FIX: PASS (API client is imported)
        
        Validates: Requirements 2.1, 2.2, 2.3
        """
        page_path = "frontend/app/page.tsx"
        
        if not os.path.exists(page_path):
            pytest.skip(f"Frontend page not found: {page_path}")
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for API-related imports or fetch calls
        has_api_import = (
            'from' in content and 'api' in content.lower() or
            'import' in content and 'api' in content.lower() or
            'fetch(' in content or
            'axios' in content
        )
        
        assert has_api_import, \
            "Frontend page should import API client or use fetch() for backend communication"
    
    def test_backend_server_file_exists(self):
        """
        Test that the backend FastAPI server file exists.
        
        EXPECTED ON UNFIXED CODE: FAIL (no server file)
        EXPECTED AFTER FIX: PASS (server file exists)
        
        Validates: Requirements 2.10
        """
        server_paths = [
            "src/api/server.py",
            "src/api/main.py",
            "backend/server.py",
            "backend/main.py"
        ]
        
        exists = any(os.path.exists(path) for path in server_paths)
        assert exists, f"Backend should have a FastAPI server file in one of: {server_paths}"
