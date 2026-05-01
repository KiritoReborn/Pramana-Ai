"""Tests for retrieval engine"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil
from src.engines.retrieval_engine import RetrievalEngine
from src.models.schemas import ExtractedDocument


class TestRetrievalEngine:
    """Test suite for RetrievalEngine"""
    
    def test_initialization(self):
        """Test that RetrievalEngine initializes correctly"""
        engine = RetrievalEngine()
        
        # Verify model is initialized
        assert engine.embedding_model is not None
        assert engine.embedding_model.get_embedding_dimension() == 384
        
        # Verify FAISS index is initialized with correct dimension
        assert engine.index is not None
        assert engine.dimension == 384
        
        # Verify metadata storage is initialized
        assert engine.metadata == {}
        assert engine.index.ntotal == 0
    
    def test_add_documents_single_page(self):
        """Test adding a single-page document to the index"""
        engine = RetrievalEngine()
        
        # Create a test document
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="test.pdf",
            pages=["This is a test document with some content for indexing."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        # Add document to index
        engine.add_documents([doc])
        
        # Verify index has entries
        assert engine.index.ntotal > 0
        
        # Verify metadata is stored
        assert len(engine.metadata) > 0
        
        # Check metadata structure
        first_meta = engine.metadata[0]
        assert first_meta["document_id"] == "doc1"
        assert first_meta["page_number"] == 1
        assert first_meta["source_file"] == "test.pdf"
        assert "text" in first_meta
    
    def test_add_documents_multiple_pages(self):
        """Test adding a multi-page document to the index"""
        engine = RetrievalEngine()
        
        # Create a test document with multiple pages
        doc = ExtractedDocument(
            document_id="doc2",
            bidder_id="bidder1",
            file_name="multi_page.pdf",
            pages=[
                "Page one content with financial information.",
                "Page two content with technical specifications.",
                "Page three content with compliance details."
            ],
            page_metadata=[{"page": 1}, {"page": 2}, {"page": 3}],
            extraction_method="pdfplumber"
        )
        
        # Add document to index
        engine.add_documents([doc])
        
        # Verify all pages are indexed
        assert engine.index.ntotal > 0
        
        # Verify metadata for different pages
        page_numbers = [meta["page_number"] for meta in engine.metadata.values()]
        assert 1 in page_numbers
        assert 2 in page_numbers
        assert 3 in page_numbers
    
    def test_chunking_with_overlap(self):
        """Test text chunking with 512 token chunks and 50% overlap"""
        engine = RetrievalEngine()
        
        # Create a long text that will be chunked
        words = ["word"] * 1000  # 1000 words
        long_text = " ".join(words)
        
        chunks = engine._chunk_text(long_text, chunk_size=512, overlap=256)
        
        # Verify chunks are created
        assert len(chunks) > 1
        
        # Verify chunk sizes (approximately 512 words)
        for chunk in chunks[:-1]:  # All but last chunk
            word_count = len(chunk.split())
            assert word_count <= 512
        
        # Verify overlap exists (chunks should share content)
        if len(chunks) > 1:
            # Check that consecutive chunks have overlapping content
            first_chunk_words = chunks[0].split()
            second_chunk_words = chunks[1].split()
            
            # The overlap should be approximately 256 words
            # Last 256 words of first chunk should match first 256 words of second chunk
            overlap_words = first_chunk_words[-256:]
            second_start_words = second_chunk_words[:256]
            
            # At least some overlap should exist
            assert len(set(overlap_words) & set(second_start_words)) > 0
    
    def test_empty_text_handling(self):
        """Test that empty text is handled gracefully"""
        engine = RetrievalEngine()
        
        # Create document with empty page
        doc = ExtractedDocument(
            document_id="doc3",
            bidder_id="bidder1",
            file_name="empty.pdf",
            pages=[""],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        # Add document - should not crash
        engine.add_documents([doc])
        
        # Index should remain empty or have no meaningful entries
        assert engine.index.ntotal == 0
    
    def test_metadata_mapping_consistency(self):
        """Test that metadata indices match FAISS index positions"""
        engine = RetrievalEngine()
        
        # Create test documents
        docs = [
            ExtractedDocument(
                document_id=f"doc{i}",
                bidder_id="bidder1",
                file_name=f"test{i}.pdf",
                pages=[f"Content for document {i}"],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            )
            for i in range(3)
        ]
        
        # Add documents
        engine.add_documents(docs)
        
        # Verify metadata indices are sequential and match index size
        assert len(engine.metadata) == engine.index.ntotal
        
        # Verify all indices from 0 to ntotal-1 exist
        for i in range(engine.index.ntotal):
            assert i in engine.metadata
    
    def test_embedding_dimension(self):
        """Test that embeddings have correct dimension (384)"""
        engine = RetrievalEngine()
        
        # Create a test document
        doc = ExtractedDocument(
            document_id="doc_dim",
            bidder_id="bidder1",
            file_name="test_dim.pdf",
            pages=["Test content for dimension verification"],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        # Add document
        engine.add_documents([doc])
        
        # Verify FAISS index dimension
        assert engine.index.d == 384
        
        # Verify we can retrieve vectors with correct dimension
        if engine.index.ntotal > 0:
            # Reconstruct first vector to verify dimension
            vector = engine.index.reconstruct(0)
            assert len(vector) == 384


    def test_retrieve_basic(self):
        """Test basic retrieval functionality"""
        engine = RetrievalEngine()
        
        # Create test documents with distinct content
        docs = [
            ExtractedDocument(
                document_id="doc1",
                bidder_id="bidder1",
                file_name="financial.pdf",
                pages=["The company has annual revenue of 5 million dollars with strong financial performance."],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            ),
            ExtractedDocument(
                document_id="doc2",
                bidder_id="bidder1",
                file_name="technical.pdf",
                pages=["Our technical team has ISO 9001 certification and extensive software development experience."],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            )
        ]
        
        # Add documents to index
        engine.add_documents(docs)
        
        # Query for financial information
        results = engine.retrieve("financial revenue information", top_k=5)
        
        # Verify results
        assert len(results) > 0
        assert all(isinstance(chunk, type(results[0])) for chunk in results)
        
        # Verify EvidenceChunk structure
        first_result = results[0]
        assert hasattr(first_result, 'text')
        assert hasattr(first_result, 'document_id')
        assert hasattr(first_result, 'page_number')
        assert hasattr(first_result, 'confidence')
        assert hasattr(first_result, 'source_file')
        
        # Verify confidence is in valid range [0, 1]
        assert 0.0 <= first_result.confidence <= 1.0
    
    def test_retrieve_top_k_limit(self):
        """Test that retrieve returns exactly k results when k chunks exist"""
        engine = RetrievalEngine()
        
        # Create document with enough content for multiple chunks
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="test.pdf",
            pages=["This is test content. " * 100],  # Long enough for multiple chunks
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine.add_documents([doc])
        
        # Request top 5 results
        results = engine.retrieve("test content", top_k=5)
        
        # Should return at most 5 results
        assert len(results) <= 5
    
    def test_retrieve_fewer_than_k_chunks(self):
        """Test retrieval when index has fewer than k chunks"""
        engine = RetrievalEngine()
        
        # Create document with minimal content (will create only 1-2 chunks)
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="small.pdf",
            pages=["Small document with minimal content."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine.add_documents([doc])
        
        # Request 5 results but index has fewer chunks
        results = engine.retrieve("content", top_k=5)
        
        # Should return all available chunks (fewer than 5)
        assert len(results) <= 5
        assert len(results) == engine.index.ntotal
    
    def test_retrieve_empty_index(self):
        """Test retrieval from empty index"""
        engine = RetrievalEngine()
        
        # Query empty index
        results = engine.retrieve("any query", top_k=5)
        
        # Should return empty list
        assert results == []
        assert len(results) == 0
    
    def test_retrieve_confidence_scores(self):
        """Test that confidence scores are properly calculated from L2 distances"""
        engine = RetrievalEngine()
        
        # Create test document
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="test.pdf",
            pages=["Financial information about revenue and profits."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine.add_documents([doc])
        
        # Query with very similar text (should have high confidence)
        results = engine.retrieve("Financial information about revenue", top_k=5)
        
        assert len(results) > 0
        
        # Verify all confidence scores are in valid range
        for chunk in results:
            assert 0.0 <= chunk.confidence <= 1.0
        
        # First result should have highest confidence (most relevant)
        if len(results) > 1:
            assert results[0].confidence >= results[1].confidence
    
    def test_retrieve_returns_evidence_chunks(self):
        """Test that retrieve returns valid EvidenceChunk Pydantic objects"""
        engine = RetrievalEngine()
        
        # Create test document
        doc = ExtractedDocument(
            document_id="doc123",
            bidder_id="bidder456",
            file_name="evidence.pdf",
            pages=["This document contains important evidence for evaluation."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine.add_documents([doc])
        
        # Retrieve results
        results = engine.retrieve("evidence evaluation", top_k=5)
        
        assert len(results) > 0
        
        # Verify each result is a valid EvidenceChunk with correct metadata
        for chunk in results:
            assert chunk.document_id == "doc123"
            assert chunk.page_number == 1  # First page (1-indexed)
            assert chunk.source_file == "evidence.pdf"
            assert isinstance(chunk.text, str)
            assert len(chunk.text) > 0
            assert isinstance(chunk.confidence, float)
    
    def test_retrieve_semantic_relevance(self):
        """Test that retrieve returns semantically relevant results"""
        engine = RetrievalEngine()
        
        # Create documents with different topics
        docs = [
            ExtractedDocument(
                document_id="financial_doc",
                bidder_id="bidder1",
                file_name="finance.pdf",
                pages=["Annual revenue is 10 million dollars. Profit margin is 15 percent. Strong financial health."],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            ),
            ExtractedDocument(
                document_id="technical_doc",
                bidder_id="bidder1",
                file_name="tech.pdf",
                pages=["Software development using Python and Java. Cloud infrastructure on AWS. DevOps practices."],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            )
        ]
        
        engine.add_documents(docs)
        
        # Query for financial information
        financial_results = engine.retrieve("revenue profit financial", top_k=3)
        
        # The top result should be from the financial document
        assert len(financial_results) > 0
        # Check that financial document appears in results
        doc_ids = [chunk.document_id for chunk in financial_results]
        assert "financial_doc" in doc_ids
    
    def test_retrieve_with_custom_k(self):
        """Test retrieve with custom top_k parameter"""
        engine = RetrievalEngine()
        
        # Create document with enough content
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="test.pdf",
            pages=["Content for testing. " * 200],  # Long content
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine.add_documents([doc])
        
        # Test with k=3
        results_3 = engine.retrieve("testing content", top_k=3)
        assert len(results_3) <= 3
        
        # Test with k=10
        results_10 = engine.retrieve("testing content", top_k=10)
        assert len(results_10) <= 10


class TestRetrievalEngineCaching:
    """Test suite for RetrievalEngine caching functionality"""
    
    def test_save_to_disk(self):
        """Test saving FAISS index and metadata to disk"""
        engine = RetrievalEngine()
        
        # Create test document
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="test.pdf",
            pages=["This is test content for caching."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine.add_documents([doc])
        
        # Create temporary directory for cache
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test_index.bin"
            metadata_path = Path(tmpdir) / "test_metadata.pkl"
            
            # Save to disk
            engine.save_to_disk(index_path, metadata_path)
            
            # Verify files were created
            assert index_path.exists()
            assert metadata_path.exists()
            
            # Verify files are not empty
            assert index_path.stat().st_size > 0
            assert metadata_path.stat().st_size > 0
    
    def test_load_from_disk(self):
        """Test loading FAISS index and metadata from disk"""
        engine1 = RetrievalEngine()
        
        # Create and index test documents
        docs = [
            ExtractedDocument(
                document_id="doc1",
                bidder_id="bidder1",
                file_name="test1.pdf",
                pages=["Financial information about revenue."],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            ),
            ExtractedDocument(
                document_id="doc2",
                bidder_id="bidder1",
                file_name="test2.pdf",
                pages=["Technical specifications and certifications."],
                page_metadata=[{"page": 1}],
                extraction_method="pdfplumber"
            )
        ]
        
        engine1.add_documents(docs)
        original_index_size = engine1.index.ntotal
        original_metadata_size = len(engine1.metadata)
        
        # Save to disk
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test_index.bin"
            metadata_path = Path(tmpdir) / "test_metadata.pkl"
            
            engine1.save_to_disk(index_path, metadata_path)
            
            # Create new engine and load from disk
            engine2 = RetrievalEngine()
            success = engine2.load_from_disk(index_path, metadata_path)
            
            # Verify load was successful
            assert success is True
            
            # Verify index size matches
            assert engine2.index.ntotal == original_index_size
            
            # Verify metadata size matches
            assert len(engine2.metadata) == original_metadata_size
            
            # Verify metadata content matches
            for idx in range(original_index_size):
                assert idx in engine2.metadata
                assert engine2.metadata[idx]["document_id"] in ["doc1", "doc2"]
    
    def test_load_from_disk_nonexistent_files(self):
        """Test loading from disk when cache files don't exist"""
        engine = RetrievalEngine()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "nonexistent_index.bin"
            metadata_path = Path(tmpdir) / "nonexistent_metadata.pkl"
            
            # Try to load from nonexistent files
            success = engine.load_from_disk(index_path, metadata_path)
            
            # Should return False
            assert success is False
            
            # Engine should still be usable with empty index
            assert engine.index.ntotal == 0
            assert len(engine.metadata) == 0
    
    def test_cache_preserves_retrieval_functionality(self):
        """Test that cached index produces same retrieval results"""
        engine1 = RetrievalEngine()
        
        # Create test document
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="test.pdf",
            pages=["Financial revenue information with profit margins."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine1.add_documents([doc])
        
        # Get retrieval results from original engine
        query = "financial revenue"
        results1 = engine1.retrieve(query, top_k=5)
        
        # Save to disk
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test_index.bin"
            metadata_path = Path(tmpdir) / "test_metadata.pkl"
            
            engine1.save_to_disk(index_path, metadata_path)
            
            # Load into new engine
            engine2 = RetrievalEngine()
            engine2.load_from_disk(index_path, metadata_path)
            
            # Get retrieval results from loaded engine
            results2 = engine2.retrieve(query, top_k=5)
            
            # Verify results match
            assert len(results1) == len(results2)
            
            for r1, r2 in zip(results1, results2):
                assert r1.document_id == r2.document_id
                assert r1.page_number == r2.page_number
                assert r1.text == r2.text
                assert r1.source_file == r2.source_file
                # Confidence scores should be very close (allow small floating point differences)
                assert abs(r1.confidence - r2.confidence) < 0.0001
    
    def test_clear_cache(self):
        """Test clearing cache files from disk"""
        engine = RetrievalEngine()
        
        # Create test document
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="test.pdf",
            pages=["Test content for cache clearing."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine.add_documents([doc])
        
        # Create temporary directory for cache
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test_index.bin"
            metadata_path = Path(tmpdir) / "test_metadata.pkl"
            
            # Override cache paths
            engine.index_cache_path = index_path
            engine.metadata_cache_path = metadata_path
            
            # Save to disk
            engine.save_to_disk()
            
            # Verify files exist
            assert index_path.exists()
            assert metadata_path.exists()
            
            # Clear cache
            engine.clear_cache()
            
            # Verify files are deleted
            assert not index_path.exists()
            assert not metadata_path.exists()
    
    def test_save_empty_index(self):
        """Test saving an empty index to disk"""
        engine = RetrievalEngine()
        
        # Don't add any documents
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "empty_index.bin"
            metadata_path = Path(tmpdir) / "empty_metadata.pkl"
            
            # Save empty index
            engine.save_to_disk(index_path, metadata_path)
            
            # Verify files were created
            assert index_path.exists()
            assert metadata_path.exists()
            
            # Load into new engine
            engine2 = RetrievalEngine()
            success = engine2.load_from_disk(index_path, metadata_path)
            
            # Should load successfully
            assert success is True
            
            # Should have empty index
            assert engine2.index.ntotal == 0
            assert len(engine2.metadata) == 0
    
    def test_default_cache_paths(self):
        """Test that default cache paths are used when not specified"""
        engine = RetrievalEngine()
        
        # Verify default paths are set
        assert engine.index_cache_path is not None
        assert engine.metadata_cache_path is not None
        assert "cache" in str(engine.index_cache_path)
        assert "faiss_index.bin" in str(engine.index_cache_path)
        assert "faiss_metadata.pkl" in str(engine.metadata_cache_path)
    
    def test_multiple_save_load_cycles(self):
        """Test multiple save and load cycles preserve data integrity"""
        engine1 = RetrievalEngine()
        
        # Create test document
        doc = ExtractedDocument(
            document_id="doc1",
            bidder_id="bidder1",
            file_name="test.pdf",
            pages=["Test content for multiple save/load cycles."],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
        
        engine1.add_documents([doc])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test_index.bin"
            metadata_path = Path(tmpdir) / "test_metadata.pkl"
            
            # First save
            engine1.save_to_disk(index_path, metadata_path)
            
            # First load
            engine2 = RetrievalEngine()
            engine2.load_from_disk(index_path, metadata_path)
            
            # Second save (from loaded engine)
            engine2.save_to_disk(index_path, metadata_path)
            
            # Second load
            engine3 = RetrievalEngine()
            engine3.load_from_disk(index_path, metadata_path)
            
            # Verify data integrity after multiple cycles
            assert engine3.index.ntotal == engine1.index.ntotal
            assert len(engine3.metadata) == len(engine1.metadata)
            
            # Verify retrieval still works
            results = engine3.retrieve("test content", top_k=5)
            assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
