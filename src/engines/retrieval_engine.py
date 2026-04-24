"""Retrieval engine using FAISS for semantic search"""

import faiss
import numpy as np
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from src.config import EmbeddingConfig, RetrievalConfig, FilePaths
from src.models.schemas import ExtractedDocument, EvidenceChunk


class RetrievalEngine:
    """FAISS-based retrieval engine for semantic search over bidder documents"""
    
    def __init__(self):
        """Initialize sentence-transformers model and FAISS index"""
        # Initialize embedding model (all-MiniLM-L6-v2)
        self.embedding_model = SentenceTransformer(EmbeddingConfig.MODEL_NAME)
        
        # Create FAISS IndexFlatL2 with dimension 384
        self.dimension = EmbeddingConfig.DIMENSION
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Metadata mapping: index → document_id, page_number, text, source_file
        self.metadata: Dict[int, dict] = {}
        
        # Cache paths
        self.cache_dir = FilePaths.CACHE_DIR
        self.index_cache_path = self.cache_dir / "faiss_index.bin"
        self.metadata_cache_path = self.cache_dir / "faiss_metadata.pkl"
        
    def add_documents(self, documents: List[ExtractedDocument]) -> None:
        """
        Embed and index document chunks with metadata storage.
        
        Implements text chunking with 512 token chunks and 50% overlap.
        Stores metadata mapping (index → document_id, page_number, text, source_file).
        
        Args:
            documents: List of ExtractedDocument objects to add to the index
        """
        for doc in documents:
            for page_num, page_text in enumerate(doc.pages):
                # Chunk page text with 512 token chunks and 50% overlap
                chunks = self._chunk_text(
                    page_text, 
                    chunk_size=EmbeddingConfig.CHUNK_SIZE,
                    overlap=EmbeddingConfig.CHUNK_OVERLAP
                )
                
                for chunk in chunks:
                    if not chunk.strip():  # Skip empty chunks
                        continue
                    
                    # Create embedding for chunk
                    embedding = self.embedding_model.encode([chunk])[0]
                    
                    # Get current index position
                    idx = self.index.ntotal
                    
                    # Add embedding to FAISS index
                    self.index.add(np.array([embedding], dtype=np.float32))
                    
                    # Store metadata mapping
                    self.metadata[idx] = {
                        "document_id": doc.document_id,
                        "page_number": page_num + 1,  # 1-indexed page numbers
                        "text": chunk,
                        "source_file": doc.file_name
                    }
    
    def retrieve(self, query: str, top_k: int = RetrievalConfig.TOP_K) -> List[EvidenceChunk]:
        """
        Retrieve top-k most relevant chunks for a query using semantic search.
        
        Converts L2 distances to confidence scores and returns EvidenceChunk objects.
        Handles case where fewer than k chunks exist in the index.
        
        Args:
            query: Query text for semantic search
            top_k: Number of chunks to retrieve (default: 5)
            
        Returns:
            List of EvidenceChunk objects with metadata and confidence scores
        """
        # Handle empty index
        if self.index.ntotal == 0:
            return []
        
        # Adjust k if index has fewer chunks than requested
        actual_k = min(top_k, self.index.ntotal)
        
        # Create query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Search FAISS index
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            actual_k
        )
        
        # Convert results to EvidenceChunk objects
        chunks = []
        for dist, idx in zip(distances[0], indices[0]):
            # Skip invalid indices (FAISS returns -1 for missing results)
            if idx == -1:
                continue
            
            # Get metadata for this chunk
            meta = self.metadata[int(idx)]
            
            # Convert L2 distance to confidence score
            # Using formula: confidence = 1 / (1 + distance)
            # This maps distance 0 -> confidence 1.0, larger distances -> lower confidence
            confidence = 1.0 / (1.0 + float(dist))
            
            # Create EvidenceChunk object
            chunk = EvidenceChunk(
                text=meta["text"],
                document_id=meta["document_id"],
                page_number=meta["page_number"],
                confidence=confidence,
                source_file=meta["source_file"]
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 256) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in tokens (default: 512)
            overlap: Overlap between chunks in tokens (default: 256, 50% overlap)
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        # Create overlapping chunks
        step_size = chunk_size - overlap
        for i in range(0, len(words), step_size):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
        
        return chunks
    
    def save_to_disk(self, index_path: Optional[Path] = None, metadata_path: Optional[Path] = None) -> None:
        """
        Save FAISS index and metadata to disk for caching.
        
        Implements requirement 3.7: Cache embeddings to optimize demo performance.
        Implements requirement 8.7: Pre-compute and cache embeddings.
        
        Args:
            index_path: Path to save FAISS index (default: cache/faiss_index.bin)
            metadata_path: Path to save metadata (default: cache/faiss_metadata.pkl)
        """
        # Use default paths if not provided
        if index_path is None:
            index_path = self.index_cache_path
        if metadata_path is None:
            metadata_path = self.metadata_cache_path
        
        # Ensure cache directory exists
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_path))
        
        # Save metadata using pickle
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def load_from_disk(self, index_path: Optional[Path] = None, metadata_path: Optional[Path] = None) -> bool:
        """
        Load FAISS index and metadata from disk cache.
        
        Implements requirement 3.7: Cache embeddings to optimize demo performance.
        Implements requirement 8.7: Pre-compute and cache embeddings.
        
        Args:
            index_path: Path to load FAISS index from (default: cache/faiss_index.bin)
            metadata_path: Path to load metadata from (default: cache/faiss_metadata.pkl)
            
        Returns:
            True if successfully loaded, False if cache files don't exist
        """
        # Use default paths if not provided
        if index_path is None:
            index_path = self.index_cache_path
        if metadata_path is None:
            metadata_path = self.metadata_cache_path
        
        # Check if cache files exist
        if not index_path.exists() or not metadata_path.exists():
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            return True
        except Exception as e:
            # If loading fails, return False and keep empty index
            print(f"Failed to load cache: {e}")
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = {}
            return False
    
    def clear_cache(self) -> None:
        """
        Clear cached FAISS index and metadata from disk.
        
        Removes cache files if they exist.
        """
        if self.index_cache_path.exists():
            self.index_cache_path.unlink()
        if self.metadata_cache_path.exists():
            self.metadata_cache_path.unlink()
