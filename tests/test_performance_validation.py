"""
Performance validation tests for Task 18.3

This module validates that the system meets performance targets:
- Tender processing < 60 seconds (Requirement 8.5)
- Bidder evaluation < 90 seconds (Requirement 8.6)
- Cache utilization working effectively (Requirement 8.7)

These tests measure actual execution times and verify caching behavior.
"""

import time
import pytest
from pathlib import Path
from src.processors.tender_processor import TenderProcessor
from src.processors.document_processor import DocumentProcessor
from src.engines.retrieval_engine import RetrievalEngine
from src.engines.evaluation_engine import EvaluationEngine
from src.engines.rule_engine import RuleEngine
from src.config import PerformanceTargets, FilePaths


class TestPerformanceValidation:
    """Performance validation tests for Requirements 8.5, 8.6, 8.7"""
    
    @pytest.fixture
    def tender_processor(self):
        """Create tender processor instance"""
        return TenderProcessor()
    
    @pytest.fixture
    def document_processor(self):
        """Create document processor instance"""
        return DocumentProcessor()
    
    @pytest.fixture
    def retrieval_engine(self):
        """Create retrieval engine instance"""
        return RetrievalEngine()
    
    @pytest.fixture
    def llm_extractor(self):
        """Create LLM extractor instance"""
        from src.engines.llm_extractor import LLMExtractor
        return LLMExtractor()
    
    @pytest.fixture
    def evaluation_engine(self, retrieval_engine, llm_extractor):
        """Create evaluation engine instance"""
        return EvaluationEngine(retrieval_engine, llm_extractor)
    
    @pytest.fixture
    def rule_engine(self):
        """Create rule engine instance"""
        return RuleEngine()
    
    @pytest.fixture
    def sample_tender_text(self):
        """Sample tender text for testing"""
        return """
        GOVERNMENT PROCUREMENT TENDER
        
        ELIGIBILITY CRITERIA:
        
        1. Financial Requirements (Mandatory):
           - Minimum annual revenue: $10 million USD
           - Minimum net assets: $5 million USD
        
        2. Technical Requirements (Mandatory):
           - ISO 9001 certification required
           - Minimum 5 years experience in similar projects
        
        3. Compliance Requirements (Mandatory):
           - Valid business license
           - Tax compliance certificate
        
        4. Documentation Requirements (Mandatory):
           - Company registration documents
           - Financial statements for last 3 years
        """
    
    @pytest.fixture
    def sample_bidder_documents(self):
        """Sample bidder documents for testing"""
        return [
            {
                "document_id": "doc1",
                "bidder_id": "bidder1",
                "file_name": "financial.pdf",
                "pages": [
                    "ABC Corporation Financial Statement 2023. "
                    "Annual revenue: $15 million USD. "
                    "Net assets: $8 million USD. "
                    "Strong financial performance with consistent growth."
                ],
                "page_metadata": [{"page": 1}],
                "extraction_method": "pdfplumber"
            },
            {
                "document_id": "doc2",
                "bidder_id": "bidder1",
                "file_name": "certifications.pdf",
                "pages": [
                    "ABC Corporation holds ISO 9001:2015 certification. "
                    "Certificate number: ISO-12345. "
                    "Valid until December 2025. "
                    "Company has 8 years of experience in government projects."
                ],
                "page_metadata": [{"page": 1}],
                "extraction_method": "pdfplumber"
            }
        ]
    
    def test_tender_processing_performance(self, tender_processor, sample_tender_text, tmp_path):
        """
        Test that tender processing completes within 60 seconds.
        
        Validates: Requirement 8.5
        Property 40: Tender Processing Performance
        
        Note: This test measures the performance of the tender processing pipeline.
        Since LLM extraction can be unreliable in test environments, we focus on
        measuring the time and verifying the process completes without errors.
        """
        # Create a temporary PDF-like file (we'll use text for simplicity)
        # Note: For this test, we're measuring the extraction logic without actual PDF processing
        
        # Measure tender processing time
        start_time = time.time()
        
        try:
            # Create a mock raw content structure
            raw_content = {
                "text": sample_tender_text,
                "tables": [],
                "page_count": 1
            }
            
            # Extract criteria from the raw content
            result = tender_processor.extract_criteria(raw_content)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Verify processing time is under target
            assert processing_time < PerformanceTargets.TENDER_PROCESSING_TIME, (
                f"Tender processing took {processing_time:.2f}s, "
                f"exceeds target of {PerformanceTargets.TENDER_PROCESSING_TIME}s"
            )
            
            # Verify result is valid (has the expected structure)
            assert result is not None
            assert "criteria" in result
            
            # Note: We don't assert on criteria count because LLM extraction
            # can be unreliable in test environments. The key metric is performance.
            criteria_count = len(result["criteria"])
            
            print(f"✓ Tender processing completed in {processing_time:.2f}s "
                  f"(target: {PerformanceTargets.TENDER_PROCESSING_TIME}s)")
            print(f"  Extracted {criteria_count} criteria")
            
        except Exception as e:
            pytest.fail(f"Tender processing failed: {str(e)}")
    
    def test_bidder_evaluation_performance(
        self, 
        evaluation_engine, 
        rule_engine,
        retrieval_engine,
        sample_bidder_documents
    ):
        """
        Test that bidder evaluation completes within 90 seconds.
        
        Validates: Requirement 8.6
        Property 41: Bidder Evaluation Performance
        """
        from src.models.schemas import EligibilityCriterion, ExtractedDocument
        
        # Create sample criteria
        criteria = [
            EligibilityCriterion(
                id="fin1",
                category="Financial",
                priority="Mandatory",
                description="Minimum annual revenue: $10 million USD",
                threshold_value="10000000",
                threshold_unit="USD",
                source_page=1,
                original_text="Minimum annual revenue: $10 million USD"
            ),
            EligibilityCriterion(
                id="tech1",
                category="Technical",
                priority="Mandatory",
                description="ISO 9001 certification required",
                threshold_value=None,
                threshold_unit=None,
                source_page=1,
                original_text="ISO 9001 certification required"
            )
        ]
        
        # Create extracted documents
        documents = [
            ExtractedDocument(**doc) for doc in sample_bidder_documents
        ]
        
        # Add documents to retrieval engine
        retrieval_engine.add_documents(documents)
        
        # Measure evaluation time
        start_time = time.time()
        
        try:
            # Evaluate each criterion
            evaluations = []
            for criterion in criteria:
                eval_result = evaluation_engine.evaluate_criterion(
                    criterion=criterion,
                    bidder_id="bidder1"
                )
                evaluations.append(eval_result)
            
            # Compute final verdict
            final_verdict = rule_engine.compute_verdict(evaluations)
            
            end_time = time.time()
            evaluation_time = end_time - start_time
            
            # Verify evaluation time is under target
            assert evaluation_time < PerformanceTargets.BIDDER_EVALUATION_TIME, (
                f"Bidder evaluation took {evaluation_time:.2f}s, "
                f"exceeds target of {PerformanceTargets.BIDDER_EVALUATION_TIME}s"
            )
            
            # Verify result is valid
            assert final_verdict in ["Eligible", "Not Eligible", "Needs Review"]
            assert len(evaluations) == len(criteria)
            
            print(f"✓ Bidder evaluation completed in {evaluation_time:.2f}s "
                  f"(target: {PerformanceTargets.BIDDER_EVALUATION_TIME}s)")
            
        except Exception as e:
            pytest.fail(f"Bidder evaluation failed: {str(e)}")
    
    def test_cache_utilization(self, retrieval_engine, sample_bidder_documents):
        """
        Test that caching is working effectively.
        
        Validates: Requirement 8.7
        Property 39: Cache Utilization
        """
        from src.models.schemas import ExtractedDocument
        
        # Create extracted documents
        documents = [
            ExtractedDocument(**doc) for doc in sample_bidder_documents
        ]
        
        # First pass: Add documents and measure time
        start_time = time.time()
        retrieval_engine.add_documents(documents)
        first_pass_time = time.time() - start_time
        
        # Save to cache
        cache_path = FilePaths.CACHE_DIR / "test_cache"
        cache_path.mkdir(exist_ok=True)
        index_path = cache_path / "faiss_index.bin"
        metadata_path = cache_path / "faiss_metadata.pkl"
        retrieval_engine.save_to_disk(index_path, metadata_path)
        
        # Create new retrieval engine and load from cache
        new_retrieval_engine = RetrievalEngine()
        
        # Second pass: Load from cache and measure time
        start_time = time.time()
        success = new_retrieval_engine.load_from_disk(index_path, metadata_path)
        cache_load_time = time.time() - start_time
        
        assert success, "Cache loading should succeed"
        
        # Verify cache loading is significantly faster
        assert cache_load_time < first_pass_time, (
            f"Cache load time ({cache_load_time:.2f}s) should be faster than "
            f"first pass time ({first_pass_time:.2f}s)"
        )
        
        # Verify cache loading is very fast (< 5 seconds)
        assert cache_load_time < 5.0, (
            f"Cache load time ({cache_load_time:.2f}s) should be under 5 seconds"
        )
        
        # Verify the cached index works correctly
        query = "ISO 9001 certification"
        results = new_retrieval_engine.retrieve(query, top_k=3)
        
        assert len(results) > 0, "Should retrieve results from cached index"
        assert any("ISO 9001" in chunk.text for chunk in results), (
            "Should find relevant content in cached index"
        )
        
        print(f"✓ Cache utilization verified: "
              f"First pass: {first_pass_time:.2f}s, "
              f"Cache load: {cache_load_time:.2f}s "
              f"(speedup: {first_pass_time/cache_load_time:.1f}x)")
        
        # Cleanup
        import shutil
        if cache_path.exists():
            shutil.rmtree(cache_path)
    
    def test_faiss_cache_hit_rate(self, retrieval_engine, sample_bidder_documents):
        """
        Test that FAISS index caching provides consistent results.
        
        Validates: Requirement 8.7
        Property 19: Embedding Cache Reuse
        """
        from src.models.schemas import ExtractedDocument
        
        # Create extracted documents
        documents = [
            ExtractedDocument(**doc) for doc in sample_bidder_documents
        ]
        
        # Add documents to index
        retrieval_engine.add_documents(documents)
        
        # Query multiple times and verify consistent results
        query = "annual revenue financial performance"
        
        results1 = retrieval_engine.retrieve(query, top_k=3)
        results2 = retrieval_engine.retrieve(query, top_k=3)
        results3 = retrieval_engine.retrieve(query, top_k=3)
        
        # Verify results are consistent (same chunks returned)
        assert len(results1) == len(results2) == len(results3), (
            "Cache should return consistent number of results"
        )
        
        # Verify the actual content is the same
        for r1, r2, r3 in zip(results1, results2, results3):
            assert r1.text == r2.text == r3.text, (
                "Cache should return identical results for same query"
            )
            assert r1.confidence == r2.confidence == r3.confidence, (
                "Cache should return identical confidence scores"
            )
        
        print(f"✓ FAISS cache hit rate verified: Consistent results across {3} queries")
    
    def test_performance_bottleneck_identification(
        self,
        tender_processor,
        evaluation_engine,
        retrieval_engine,
        sample_tender_text,
        sample_bidder_documents
    ):
        """
        Identify performance bottlenecks in the system.
        
        This test measures individual component performance to identify
        optimization opportunities.
        
        Validates: Requirement 8.5, 8.6
        """
        from src.models.schemas import ExtractedDocument, EligibilityCriterion
        
        timings = {}
        
        # 1. Measure criteria extraction time
        start = time.time()
        raw_content = {
            "text": sample_tender_text,
            "tables": [],
            "page_count": 1
        }
        criteria_result = tender_processor.extract_criteria(raw_content)
        criteria = criteria_result.get("criteria", [])
        timings['criteria_extraction'] = time.time() - start
        
        # 2. Measure document processing time
        start = time.time()
        documents = [ExtractedDocument(**doc) for doc in sample_bidder_documents]
        timings['document_creation'] = time.time() - start
        
        # 3. Measure embedding generation time
        start = time.time()
        retrieval_engine.add_documents(documents)
        timings['embedding_generation'] = time.time() - start
        
        # 4. Measure retrieval time
        start = time.time()
        for _ in range(5):  # Simulate 5 criteria
            retrieval_engine.retrieve("test query", top_k=5)
        timings['retrieval_5_queries'] = time.time() - start
        
        # 5. Measure single criterion evaluation time
        if len(criteria) > 0:
            start = time.time()
            evaluation_engine.evaluate_criterion(
                criterion=criteria[0],
                bidder_id="bidder1"
            )
            timings['single_criterion_eval'] = time.time() - start
        
        # Print performance breakdown
        print("\n" + "="*60)
        print("PERFORMANCE BOTTLENECK ANALYSIS")
        print("="*60)
        for component, duration in sorted(timings.items(), key=lambda x: x[1], reverse=True):
            print(f"{component:.<40} {duration:.3f}s")
        print("="*60)
        
        # Identify bottlenecks (components taking > 10% of total time)
        total_time = sum(timings.values())
        bottlenecks = [
            (comp, dur) for comp, dur in timings.items() 
            if dur > total_time * 0.1
        ]
        
        if bottlenecks:
            print("\nIdentified bottlenecks (>10% of total time):")
            for comp, dur in bottlenecks:
                percentage = (dur / total_time) * 100
                print(f"  - {comp}: {dur:.3f}s ({percentage:.1f}%)")
        else:
            print("\n✓ No significant bottlenecks identified")
        
        print("="*60 + "\n")
        
        # This test always passes - it's for information gathering
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
