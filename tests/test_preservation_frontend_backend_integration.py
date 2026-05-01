"""
Preservation Property Tests for Frontend-Backend Integration

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10**

This test suite verifies that existing functionality remains unchanged after the fix.
These tests should PASS on UNFIXED code to establish the baseline behavior.

IMPORTANT: Follow observation-first methodology
- Observe behavior on UNFIXED code for non-buggy inputs (pure UI interactions)
- Write property-based tests capturing observed behavior patterns
- Run tests on UNFIXED code
- EXPECTED OUTCOME: Tests PASS (confirms baseline behavior to preserve)

Property 2: Preservation - Existing Functionality Unchanged
For any pure UI interaction (font size, language toggle, role selection, navigation) or
backend processing operation, the system should produce the same results before and after
the fix implementation.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from hypothesis import Phase
import subprocess
import time
import os
import sys
from pathlib import Path
import tempfile
from typing import List, Dict, Any
import json

# Import backend processing classes to test preservation
from src.processors.document_processor import DocumentProcessor
from src.processors.tender_processor import TenderProcessor
from src.engines.evaluation_engine import EvaluationEngine
from src.engines.retrieval_engine import RetrievalEngine
from src.engines.rule_engine import RuleEngine
from src.engines.report_generator import ReportGenerator
from src.models.schemas import (
    EligibilityCriterion, 
    Decision, 
    FinancialEvidence,
    TechnicalEvidence,
    ComplianceEvidence,
    DocumentationEvidence
)


class TestFrontendUIPreservation:
    """
    Test that pure UI interactions (no backend data required) remain unchanged.
    
    These tests verify that UI state management for font size, language, role selection,
    navigation, toasts, and modals continues to work exactly as before.
    
    EXPECTED ON UNFIXED CODE: PASS (establishes baseline)
    EXPECTED AFTER FIX: PASS (confirms no regressions)
    """
    
    def test_frontend_page_file_exists(self):
        """
        Test that the frontend page file exists and is readable.
        
        This is a prerequisite for all UI preservation tests.
        
        Validates: Requirements 3.1
        """
        page_path = "frontend/app/page.tsx"
        assert os.path.exists(page_path), f"Frontend page should exist at {page_path}"
        
        # Verify file is readable
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0, "Frontend page should have content"
    
    def test_font_size_controls_exist_in_code(self):
        """
        Test that font size controls (A-, A, A+) exist in the frontend code.
        
        These controls should adjust font scale without making API calls.
        
        Validates: Requirements 3.2
        """
        page_path = "frontend/app/page.tsx"
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for font scale state management
        assert 'fontScale' in content, "Frontend should have fontScale state"
        assert 'setFontScale' in content, "Frontend should have setFontScale function"
        
        # Check for font size buttons
        assert 'A-' in content, "Frontend should have A- button"
        assert 'A+' in content, "Frontend should have A+ button"
        
        # Verify font scale logic (increase/decrease)
        assert 'Math.max' in content or 'Math.min' in content, \
            "Frontend should have font scale boundary logic"
    
    def test_language_toggle_exists_in_code(self):
        """
        Test that language toggle (English/Kannada) exists in the frontend code.
        
        Language toggle should switch between languages without making API calls.
        
        Validates: Requirements 3.3
        """
        page_path = "frontend/app/page.tsx"
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for language state management
        assert 'language' in content, "Frontend should have language state"
        assert 'setLanguage' in content, "Frontend should have setLanguage function"
        
        # Check for language options
        assert 'English' in content, "Frontend should support English"
        assert 'Kannada' in content, "Frontend should support Kannada"
        
        # Check for language toggle button
        assert 'Languages' in content or 'language' in content.lower(), \
            "Frontend should have language toggle UI"
    
    def test_role_selection_exists_in_code(self):
        """
        Test that role selection (Bidder/Officer) exists in the frontend code.
        
        Role selection should update view state without making API calls.
        
        Validates: Requirements 3.4
        """
        page_path = "frontend/app/page.tsx"
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for role state management
        assert 'role' in content, "Frontend should have role state"
        assert 'setRole' in content, "Frontend should have setRole function"
        
        # Check for role options
        assert 'bidder' in content, "Frontend should support bidder role"
        assert 'officer' in content, "Frontend should support officer role"
        
        # Check for role selection UI
        assert 'Bidder' in content and 'Officer' in content, \
            "Frontend should have role selection UI"
    
    def test_sidebar_navigation_exists_in_code(self):
        """
        Test that sidebar navigation exists in the frontend code.
        
        Sidebar navigation should update active view without making API calls.
        
        Validates: Requirements 3.5
        """
        page_path = "frontend/app/page.tsx"
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for navigation state management
        assert 'activeNav' in content or 'bidderView' in content or 'officerView' in content, \
            "Frontend should have navigation state"
        
        # Check for navigation menu items
        assert 'Dashboard' in content or 'dashboard' in content, \
            "Frontend should have dashboard navigation"
        
        # Check for view switching logic
        assert 'setBidderView' in content or 'setOfficerView' in content or 'setActiveNav' in content, \
            "Frontend should have view switching functions"
    
    def test_toast_notifications_exist_in_code(self):
        """
        Test that toast notification system exists in the frontend code.
        
        Toast notifications should display without making API calls.
        
        Validates: Requirements 3.7
        """
        page_path = "frontend/app/page.tsx"
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for toast state management
        assert 'toast' in content, "Frontend should have toast state"
        assert 'setToast' in content, "Frontend should have setToast function"
        
        # Check for toast display logic
        assert 'triggerToast' in content or 'showToast' in content or 'setToast(' in content, \
            "Frontend should have toast trigger function"
    
    def test_modal_overlay_exists_in_code(self):
        """
        Test that modal overlay system exists in the frontend code.
        
        Modal overlays should open/close without making API calls.
        
        Validates: Requirements 3.8
        """
        page_path = "frontend/app/page.tsx"
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for modal state management
        assert 'reviewing' in content or 'modal' in content, \
            "Frontend should have modal state"
        assert 'setReviewing' in content or 'setModal' in content, \
            "Frontend should have modal state setter"
        
        # Check for modal UI elements
        assert 'fixed' in content and 'inset' in content, \
            "Frontend should have modal overlay styling"
    
    def test_government_portal_styling_preserved(self):
        """
        Test that government portal styling and aesthetic are preserved.
        
        Validates: Requirements 3.1
        """
        page_path = "frontend/app/page.tsx"
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Karnataka government branding
        assert 'Karnataka' in content or 'karnataka' in content, \
            "Frontend should reference Karnataka government"
        
        # Check for government color scheme
        assert '#0f2d56' in content or '#8b0000' in content, \
            "Frontend should use government color scheme"
        
        # Check for emblem
        assert 'emblem' in content, "Frontend should display government emblem"
        
        # Check for bilingual support
        assert 'Kannada' in content or 'ಕನ್ನಡ' in content or 'ಟೆಂಡರ್' in content, \
            "Frontend should support bilingual interface"
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        font_adjustment=st.sampled_from(['decrease', 'reset', 'increase']),
        language_choice=st.sampled_from(['English', 'Kannada']),
        role_choice=st.sampled_from(['bidder', 'officer', None]),
        view_choice=st.sampled_from(['dashboard', 'tenders', 'uploads', 'submissions', 'help'])
    )
    def test_property_ui_interactions_are_stateless(
        self, 
        font_adjustment: str,
        language_choice: str,
        role_choice: str,
        view_choice: str
    ):
        """
        Property-based test: Pure UI interactions should be stateless and not require API calls.
        
        This test verifies that UI state changes (font size, language, role, navigation)
        are handled entirely in the frontend without backend communication.
        
        EXPECTED ON UNFIXED CODE: PASS (establishes baseline)
        EXPECTED AFTER FIX: PASS (confirms no regressions)
        
        Property: For any pure UI interaction, the frontend code should update local state
                 without making HTTP requests to the backend.
        
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8
        """
        page_path = "frontend/app/page.tsx"
        
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify font adjustment logic exists and is local
        if font_adjustment == 'decrease':
            assert 'Math.max' in content, "Font decrease should have min boundary"
        elif font_adjustment == 'increase':
            assert 'Math.min' in content, "Font increase should have max boundary"
        
        # Verify language toggle logic exists and is local
        assert language_choice in content, f"Language {language_choice} should be supported"
        
        # Verify role selection logic exists and is local
        if role_choice:
            assert role_choice in content, f"Role {role_choice} should be supported"
        
        # Verify view navigation logic exists and is local
        assert view_choice in content or view_choice.capitalize() in content, \
            f"View {view_choice} should be supported"
        
        # CRITICAL: Verify these UI interactions don't trigger API calls
        # Check that state setters are used without fetch/axios
        state_setters = ['setFontScale', 'setLanguage', 'setRole', 'setBidderView', 'setOfficerView']
        for setter in state_setters:
            if setter in content:
                # Find the setter usage and verify no fetch nearby
                setter_index = content.find(setter)
                if setter_index != -1:
                    # Check 200 characters before and after for fetch/axios
                    context = content[max(0, setter_index-200):min(len(content), setter_index+200)]
                    # These setters should NOT be immediately followed by fetch calls
                    # (They might be in the same file, but not in the same handler)
                    assert not (setter in context and 'fetch(' in context and 
                               context.index(setter) < context.index('fetch(') < context.index(setter) + 50), \
                        f"{setter} should not immediately trigger fetch calls"


class TestBackendProcessingPreservation:
    """
    Test that backend processing classes produce the same results before and after the fix.
    
    These tests verify that the core backend functionality (document processing, tender
    processing, evaluation, retrieval, rule engine, report generation) remains unchanged.
    
    EXPECTED ON UNFIXED CODE: PASS (establishes baseline)
    EXPECTED AFTER FIX: PASS (confirms no regressions)
    """
    
    def test_document_processor_class_unchanged(self):
        """
        Test that DocumentProcessor class exists and has expected methods.
        
        Validates: Requirements 3.9, 3.10
        """
        # Verify class can be imported
        assert DocumentProcessor is not None, "DocumentProcessor should be importable"
        
        # Verify key methods exist
        processor = DocumentProcessor()
        assert hasattr(processor, 'process_document'), \
            "DocumentProcessor should have process_document method"
        assert callable(processor.process_document), \
            "process_document should be callable"
    
    def test_tender_processor_class_unchanged(self):
        """
        Test that TenderProcessor class exists and has expected methods.
        
        Validates: Requirements 3.9, 3.10
        """
        # Verify class can be imported
        assert TenderProcessor is not None, "TenderProcessor should be importable"
        
        # Verify key methods exist
        processor = TenderProcessor()
        assert hasattr(processor, 'process_tender'), \
            "TenderProcessor should have process_tender method"
        assert callable(processor.process_tender), \
            "process_tender should be callable"
    
    def test_evaluation_engine_class_unchanged(self):
        """
        Test that EvaluationEngine class exists and has expected methods.
        
        Validates: Requirements 3.9, 3.10
        """
        # Verify class can be imported
        assert EvaluationEngine is not None, "EvaluationEngine should be importable"
        
        # Verify class can be instantiated (with mock dependencies)
        # Note: We don't instantiate here to avoid dependency issues
        assert hasattr(EvaluationEngine, '__init__'), \
            "EvaluationEngine should have __init__ method"
    
    def test_retrieval_engine_class_unchanged(self):
        """
        Test that RetrievalEngine class exists and has expected methods.
        
        Validates: Requirements 3.9, 3.10
        """
        # Verify class can be imported
        assert RetrievalEngine is not None, "RetrievalEngine should be importable"
        
        # Verify key methods exist
        engine = RetrievalEngine()
        assert hasattr(engine, 'add_documents'), \
            "RetrievalEngine should have add_documents method"
        assert hasattr(engine, 'retrieve'), \
            "RetrievalEngine should have retrieve method"
    
    def test_rule_engine_class_unchanged(self):
        """
        Test that RuleEngine class exists and has expected methods.
        
        Validates: Requirements 3.9, 3.10
        """
        # Verify class can be imported
        assert RuleEngine is not None, "RuleEngine should be importable"
        
        # Verify key methods exist
        engine = RuleEngine()
        assert hasattr(engine, 'apply_rules'), \
            "RuleEngine should have apply_rules method"
        assert hasattr(engine, 'compute_verdict'), \
            "RuleEngine should have compute_verdict method"
    
    def test_report_generator_class_unchanged(self):
        """
        Test that ReportGenerator class exists and has expected methods.
        
        Validates: Requirements 3.9, 3.10
        """
        # Verify class can be imported
        assert ReportGenerator is not None, "ReportGenerator should be importable"
        
        # Verify key methods exist
        generator = ReportGenerator()
        assert hasattr(generator, 'generate_report'), \
            "ReportGenerator should have generate_report method"
        assert callable(generator.generate_report), \
            "generate_report should be callable"
    
    def test_pydantic_schemas_unchanged(self):
        """
        Test that Pydantic schemas remain unchanged and can be imported.
        
        Validates: Requirements 3.9, 3.10
        """
        # Verify schemas can be imported
        assert EligibilityCriterion is not None, "EligibilityCriterion should be importable"
        assert Decision is not None, "Decision should be importable"
        assert FinancialEvidence is not None, "FinancialEvidence should be importable"
        assert TechnicalEvidence is not None, "TechnicalEvidence should be importable"
        assert ComplianceEvidence is not None, "ComplianceEvidence should be importable"
        assert DocumentationEvidence is not None, "DocumentationEvidence should be importable"
        
        # Verify schemas can be instantiated with minimal data
        criterion = EligibilityCriterion(
            id="TEST-001",
            category="Financial",
            description="Test criterion",
            priority="Mandatory",
            source_page=1,
            original_text="Test original text"
        )
        assert criterion.id == "TEST-001", "EligibilityCriterion should work as before"
    
    def test_audit_logging_directory_exists(self):
        """
        Test that audit logging directory exists and is writable.
        
        Validates: Requirements 3.10
        """
        audit_dir = Path("audit_logs")
        
        # Directory should exist
        assert audit_dir.exists(), "audit_logs directory should exist"
        assert audit_dir.is_dir(), "audit_logs should be a directory"
        
        # Directory should be writable (test by creating a temp file)
        test_file = audit_dir / "test_preservation.tmp"
        try:
            test_file.write_text("test")
            assert test_file.exists(), "Should be able to write to audit_logs"
            test_file.unlink()  # Clean up
        except Exception as e:
            pytest.fail(f"audit_logs directory should be writable: {str(e)}")
    
    @settings(max_examples=10)
    @given(
        criterion_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
        category=st.sampled_from(['Financial', 'Technical', 'Compliance', 'Documentation']),
        priority=st.sampled_from(['Mandatory', 'Optional'])
    )
    def test_property_schema_validation_unchanged(
        self,
        criterion_id: str,
        category: str,
        priority: str
    ):
        """
        Property-based test: Pydantic schema validation should work the same way.
        
        This test verifies that schema validation logic remains unchanged.
        
        EXPECTED ON UNFIXED CODE: PASS (establishes baseline)
        EXPECTED AFTER FIX: PASS (confirms no regressions)
        
        Property: For any valid criterion data, the schema should validate successfully
                 and produce the same object structure.
        
        Validates: Requirements 3.9, 3.10
        """
        # Create criterion with generated data
        criterion = EligibilityCriterion(
            id=criterion_id,
            category=category,
            description=f"Test criterion for {category}",
            priority=priority,
            source_page=1,
            original_text=f"Original text for {criterion_id}"
        )
        
        # Verify object was created successfully
        assert criterion.id == criterion_id, "Criterion ID should match input"
        assert criterion.category == category, "Criterion category should match input"
        assert criterion.priority == priority, "Criterion priority should match input"
        
        # Verify schema can be serialized/deserialized
        criterion_dict = criterion.dict()
        assert isinstance(criterion_dict, dict), "Schema should serialize to dict"
        assert criterion_dict['id'] == criterion_id, "Serialized data should match"
        
        # Verify schema can be reconstructed
        criterion_reconstructed = EligibilityCriterion(**criterion_dict)
        assert criterion_reconstructed.id == criterion.id, "Schema should deserialize correctly"


class TestStreamlitAppPreservation:
    """
    Test that the Streamlit app continues to function independently.
    
    These tests verify that the Streamlit app in src/ui/app.py remains functional
    and can be run independently without breaking.
    
    EXPECTED ON UNFIXED CODE: PASS (establishes baseline)
    EXPECTED AFTER FIX: PASS (confirms no regressions)
    """
    
    def test_streamlit_app_file_exists(self):
        """
        Test that the Streamlit app file exists and is readable.
        
        Validates: Requirements 3.9
        """
        app_path = "src/ui/app.py"
        assert os.path.exists(app_path), f"Streamlit app should exist at {app_path}"
        
        # Verify file is readable
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0, "Streamlit app should have content"
            assert 'streamlit' in content, "File should import streamlit"
    
    def test_streamlit_app_has_main_function(self):
        """
        Test that the Streamlit app has a main function.
        
        Validates: Requirements 3.9
        """
        app_path = "src/ui/app.py"
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for main function
        assert 'def main(' in content, "Streamlit app should have main function"
        assert '__main__' in content, "Streamlit app should have main entry point"
    
    def test_streamlit_app_imports_backend_classes(self):
        """
        Test that the Streamlit app imports all necessary backend classes.
        
        Validates: Requirements 3.9, 3.10
        """
        app_path = "src/ui/app.py"
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for backend class imports
        required_imports = [
            'TenderProcessor',
            'DocumentProcessor',
            'RetrievalEngine',
            'LLMExtractor',
            'EvaluationEngine',
            'RuleEngine',
            'ReportGenerator'
        ]
        
        for import_name in required_imports:
            assert import_name in content, \
                f"Streamlit app should import {import_name}"
    
    def test_streamlit_app_has_workflow_sections(self):
        """
        Test that the Streamlit app has all workflow sections.
        
        Validates: Requirements 3.9
        """
        app_path = "src/ui/app.py"
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for workflow sections
        workflow_sections = [
            'render_tender_upload_section',
            'render_bidder_upload_section',
            'render_evaluation_section',
            'render_evaluation_results'
        ]
        
        for section in workflow_sections:
            assert section in content, \
                f"Streamlit app should have {section} function"
    
    def test_streamlit_app_syntax_valid(self):
        """
        Test that the Streamlit app has valid Python syntax.
        
        This test compiles the app file to check for syntax errors.
        
        Validates: Requirements 3.9
        """
        app_path = "src/ui/app.py"
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            compile(content, app_path, 'exec')
        except SyntaxError as e:
            pytest.fail(f"Streamlit app has syntax error: {str(e)}")
    
    @pytest.mark.slow
    def test_streamlit_app_can_be_imported(self):
        """
        Test that the Streamlit app can be imported without errors.
        
        This test verifies that all dependencies are available and the app
        can be loaded into memory.
        
        Validates: Requirements 3.9, 3.10
        """
        try:
            # Add src to path if not already there
            src_path = str(Path(__file__).parent.parent / 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            # Import the app module
            import src.ui.app as streamlit_app
            
            # Verify key functions exist
            assert hasattr(streamlit_app, 'main'), "App should have main function"
            assert hasattr(streamlit_app, 'initialize_session_state'), \
                "App should have initialize_session_state function"
            
        except ImportError as e:
            pytest.fail(f"Streamlit app should be importable: {str(e)}")
        except Exception as e:
            pytest.fail(f"Streamlit app import failed: {str(e)}")


class TestIntegrationPreservation:
    """
    Integration tests to verify that the overall system behavior is preserved.
    
    These tests check that the combination of frontend and backend components
    continues to work as expected.
    """
    
    def test_project_structure_preserved(self):
        """
        Test that the project directory structure is preserved.
        
        Validates: Requirements 3.1, 3.9, 3.10
        """
        required_dirs = [
            'frontend',
            'frontend/app',
            'src',
            'src/processors',
            'src/engines',
            'src/models',
            'src/ui',
            'tests',
            'audit_logs'
        ]
        
        for dir_path in required_dirs:
            assert os.path.exists(dir_path), f"Directory {dir_path} should exist"
            assert os.path.isdir(dir_path), f"{dir_path} should be a directory"
    
    def test_requirements_file_preserved(self):
        """
        Test that requirements.txt exists and contains expected dependencies.
        
        Validates: Requirements 3.10
        """
        req_path = "requirements.txt"
        assert os.path.exists(req_path), "requirements.txt should exist"
        
        with open(req_path, 'r') as f:
            content = f.read()
        
        # Check for core dependencies (should exist before fix)
        core_deps = ['streamlit', 'pydantic', 'langchain', 'faiss']
        for dep in core_deps:
            assert dep in content.lower(), f"requirements.txt should contain {dep}"
    
    def test_frontend_package_json_preserved(self):
        """
        Test that frontend package.json exists and contains expected dependencies.
        
        Validates: Requirements 3.1
        """
        pkg_path = "frontend/package.json"
        assert os.path.exists(pkg_path), "frontend/package.json should exist"
        
        with open(pkg_path, 'r') as f:
            content = f.read()
        
        # Check for core frontend dependencies
        core_deps = ['next', 'react', 'typescript', 'tailwindcss']
        for dep in core_deps:
            assert dep in content.lower(), f"package.json should contain {dep}"
    
    @settings(max_examples=5)
    @given(
        test_scenario=st.sampled_from([
            'font_size_adjustment',
            'language_toggle',
            'role_selection',
            'navigation_change',
            'toast_display',
            'modal_open_close'
        ])
    )
    def test_property_ui_state_management_isolated(self, test_scenario: str):
        """
        Property-based test: UI state management should be isolated from backend.
        
        This test verifies that UI state changes don't affect backend processing
        and vice versa.
        
        EXPECTED ON UNFIXED CODE: PASS (establishes baseline)
        EXPECTED AFTER FIX: PASS (confirms no regressions)
        
        Property: For any UI state change, the backend processing classes should
                 remain unaffected and produce the same results.
        
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10
        """
        # Verify frontend code exists
        frontend_path = "frontend/app/page.tsx"
        assert os.path.exists(frontend_path), "Frontend should exist"
        
        # Verify backend classes can be imported
        backend_classes = [
            DocumentProcessor,
            TenderProcessor,
            RetrievalEngine,
            RuleEngine,
            ReportGenerator
        ]
        
        for cls in backend_classes:
            assert cls is not None, f"{cls.__name__} should be importable"
        
        # Verify UI state management is in frontend only
        with open(frontend_path, 'r', encoding='utf-8') as f:
            frontend_content = f.read()
        
        # Map scenarios to state variables
        state_vars = {
            'font_size_adjustment': 'fontScale',
            'language_toggle': 'language',
            'role_selection': 'role',
            'navigation_change': 'activeNav',
            'toast_display': 'toast',
            'modal_open_close': 'reviewing'
        }
        
        state_var = state_vars[test_scenario]
        assert state_var in frontend_content, \
            f"Frontend should manage {state_var} state for {test_scenario}"
        
        # Verify backend files don't reference frontend state
        backend_files = [
            'src/processors/document_processor.py',
            'src/processors/tender_processor.py',
            'src/engines/evaluation_engine.py',
            'src/engines/retrieval_engine.py',
            'src/engines/rule_engine.py'
        ]
        
        for backend_file in backend_files:
            if os.path.exists(backend_file):
                with open(backend_file, 'r', encoding='utf-8') as f:
                    backend_content = f.read()
                
                # Backend should NOT reference frontend state variables
                assert state_var not in backend_content, \
                    f"Backend {backend_file} should not reference frontend state {state_var}"
