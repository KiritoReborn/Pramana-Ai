"""Configuration file for Pramana AI Tender Evaluator"""

import os
from pathlib import Path


class LLMConfig:
    """LLM settings for Ollama"""
    MODEL_NAME = "llama3.1"
    TEMPERATURE = 0.1  # Low temperature for consistency
    MAX_TOKENS = 2048
    TIMEOUT = 30  # seconds
    MAX_RETRIES = 3


class PerformanceTargets:
    """Performance targets for demo"""
    TENDER_PROCESSING_TIME = 60  # seconds
    BIDDER_EVALUATION_TIME = 90  # seconds
    CACHE_ENABLED = True


class FilePaths:
    """File paths for data storage"""
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    DEMO_DATA_DIR = BASE_DIR / "demo_data"
    CACHE_DIR = BASE_DIR / "cache"
    AUDIT_LOGS_DIR = BASE_DIR / "audit_logs"
    
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    DEMO_DATA_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
    AUDIT_LOGS_DIR.mkdir(exist_ok=True)


class EmbeddingConfig:
    """Embedding model configuration"""
    MODEL_NAME = "all-MiniLM-L6-v2"
    DIMENSION = 384
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 256  # 50% overlap


class RetrievalConfig:
    """FAISS retrieval configuration"""
    TOP_K = 5
    MIN_CONFIDENCE = 0.5
    LOW_CONFIDENCE_THRESHOLD = 0.7


class SystemConfig:
    """System metadata"""
    VERSION = "1.0.0"
    NAME = "Pramana AI Tender Evaluator"
