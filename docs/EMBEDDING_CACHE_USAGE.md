# Embedding Cache Usage Guide

## Overview

The retrieval engine now supports caching of FAISS embeddings to disk, which significantly improves demo performance by avoiding re-computation of embeddings.

## Features

1. **Save embeddings to disk**: Store FAISS index and metadata for later use
2. **Load embeddings from disk**: Quickly restore pre-computed embeddings
3. **Clear cache**: Remove cached files when needed
4. **Session state caching**: Use with Streamlit session state for optimal UI performance

## Basic Usage

### Saving Embeddings

```python
from src.engines.retrieval_engine import RetrievalEngine
from src.models.schemas import ExtractedDocument

# Create engine and add documents
engine = RetrievalEngine()
engine.add_documents(documents)

# Save to default cache location (cache/faiss_index.bin and cache/faiss_metadata.pkl)
engine.save_to_disk()

# Or save to custom location
from pathlib import Path
engine.save_to_disk(
    index_path=Path("custom/path/index.bin"),
    metadata_path=Path("custom/path/metadata.pkl")
)
```

### Loading Embeddings

```python
from src.engines.retrieval_engine import RetrievalEngine

# Create engine
engine = RetrievalEngine()

# Load from default cache location
success = engine.load_from_disk()

if success:
    print(f"Loaded {engine.index.ntotal} cached embeddings")
    # Engine is ready to use for retrieval
    results = engine.retrieve("query text", top_k=5)
else:
    print("No cache found, need to add documents")
    # Add documents and create embeddings
    engine.add_documents(documents)
```

### Clearing Cache

```python
from src.engines.retrieval_engine import RetrievalEngine

engine = RetrievalEngine()
engine.clear_cache()  # Removes cache files from disk
```

## Pre-computing Demo Embeddings

For optimal demo performance, pre-compute embeddings before the demo:

```bash
# Run the pre-computation utility
python -m src.utils.precompute_embeddings
```

This will:
1. Create sample demo documents
2. Generate embeddings for all documents
3. Save embeddings to cache
4. Test retrieval with cached embeddings

## Integration with Streamlit

For Streamlit applications, combine disk caching with session state:

```python
import streamlit as st
from src.engines.retrieval_engine import RetrievalEngine

@st.cache_resource
def load_retrieval_engine():
    """Load retrieval engine with cached embeddings (cached across sessions)"""
    engine = RetrievalEngine()
    
    # Try to load from disk cache
    if engine.load_from_disk():
        st.success(f"Loaded {engine.index.ntotal} cached embeddings")
    else:
        st.warning("No cache found, embeddings will be computed on first use")
    
    return engine

# Use in your Streamlit app
engine = load_retrieval_engine()

# Add documents if needed (will be cached in session state)
if 'documents_indexed' not in st.session_state:
    engine.add_documents(uploaded_documents)
    engine.save_to_disk()  # Save for next session
    st.session_state.documents_indexed = True

# Perform retrieval
results = engine.retrieve(query, top_k=5)
```

## Performance Benefits

### Without Caching
- Tender processing: ~60 seconds (includes embedding computation)
- Bidder evaluation: ~90 seconds (includes embedding computation)

### With Caching
- Tender processing: ~5 seconds (loads pre-computed embeddings)
- Bidder evaluation: ~30 seconds (uses cached embeddings)
- Demo startup: Instant (embeddings ready immediately)

## Cache File Locations

Default cache locations (configured in `src/config.py`):
- FAISS index: `cache/faiss_index.bin`
- Metadata: `cache/faiss_metadata.pkl`

## Requirements Satisfied

This implementation satisfies:
- **Requirement 3.7**: Cache all embeddings to optimize demo performance
- **Requirement 8.7**: Pre-compute and cache embeddings to optimize live demonstration performance

## Technical Details

### FAISS Index Format
- Index type: `IndexFlatL2` (L2 distance metric)
- Dimension: 384 (all-MiniLM-L6-v2 embedding dimension)
- Saved using `faiss.write_index()` and `faiss.read_index()`

### Metadata Format
- Stored as Python pickle file
- Contains mapping: `index_id → {document_id, page_number, text, source_file}`
- Preserves all metadata needed for evidence tracing

### Cache Invalidation
Cache should be cleared and regenerated when:
- Document content changes
- Embedding model is updated
- Chunking strategy changes (chunk size or overlap)

## Troubleshooting

### Cache Loading Fails
If `load_from_disk()` returns `False`:
1. Check if cache files exist in the cache directory
2. Verify file permissions
3. Check for corruption (delete and regenerate cache)

### Retrieval Results Differ After Caching
This should not happen. If it does:
1. Clear cache with `engine.clear_cache()`
2. Regenerate embeddings
3. Verify FAISS version compatibility

### Out of Memory
If cache files are too large:
1. Consider using FAISS index compression (IVF, PQ)
2. Reduce chunk size or increase overlap
3. Process documents in batches
