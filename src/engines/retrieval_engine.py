"""Retrieval engine using FAISS for semantic search"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from src.config import EmbeddingConfig, RetrievalConfig
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
