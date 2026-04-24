"""Utility script to pre-compute embeddings for demo documents"""

from pathlib import Path
from typing import List
from src.engines.retrieval_engine import RetrievalEngine
from src.models.schemas import ExtractedDocument
from src.config import FilePaths
import json


def precompute_demo_embeddings(demo_documents: List[ExtractedDocument]) -> None:
    """
    Pre-compute embeddings for demo documents and save to cache.
    
    This function implements requirement 3.7 and 8.7:
    - Cache embeddings to optimize demo performance
    - Pre-compute and cache embeddings for demo documents
    
    Args:
        demo_documents: List of ExtractedDocument objects to pre-compute embeddings for
    """
    print("Initializing retrieval engine...")
    engine = RetrievalEngine()
    
    print(f"Adding {len(demo_documents)} documents to index...")
    engine.add_documents(demo_documents)
    
    print(f"Index now contains {engine.index.ntotal} chunks")
    
    print("Saving embeddings to disk cache...")
    engine.save_to_disk()
    
    print(f"Cache saved to:")
    print(f"  - Index: {engine.index_cache_path}")
    print(f"  - Metadata: {engine.metadata_cache_path}")
    
    print("Pre-computation complete!")


def load_cached_embeddings() -> RetrievalEngine:
    """
    Load pre-computed embeddings from cache.
    
    Returns:
        RetrievalEngine with loaded embeddings, or empty engine if cache doesn't exist
    """
    engine = RetrievalEngine()
    
    success = engine.load_from_disk()
    
    if success:
        print(f"Loaded {engine.index.ntotal} cached embeddings")
    else:
        print("No cached embeddings found, starting with empty index")
    
    return engine


def create_sample_demo_documents() -> List[ExtractedDocument]:
    """
    Create sample demo documents for testing the pre-computation.
    
    In a real scenario, these would be loaded from actual PDF files.
    
    Returns:
        List of sample ExtractedDocument objects
    """
    sample_docs = [
        ExtractedDocument(
            document_id="demo_bidder1_financial",
            bidder_id="bidder1",
            file_name="bidder1_financial_statement.pdf",
            pages=[
                "ABC Corporation Financial Statement 2023. Annual revenue: $15 million. "
                "Net profit: $2.5 million. Total assets: $25 million. "
                "The company has maintained strong financial performance with 20% year-over-year growth. "
                "Cash reserves: $5 million. Debt-to-equity ratio: 0.3. "
                "Operating expenses: $10 million. Gross margin: 35%."
            ],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        ),
        ExtractedDocument(
            document_id="demo_bidder1_technical",
            bidder_id="bidder1",
            file_name="bidder1_technical_capabilities.pdf",
            pages=[
                "Technical Capabilities and Certifications. "
                "ISO 9001:2015 certified for quality management systems. "
                "ISO 27001:2013 certified for information security management. "
                "Our team consists of 50 software engineers with expertise in Python, Java, and cloud technologies. "
                "We have successfully delivered 100+ projects in the last 5 years. "
                "Technical infrastructure includes AWS cloud deployment, CI/CD pipelines, and automated testing. "
                "Average project completion time: 6 months. Client satisfaction rate: 95%."
            ],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        ),
        ExtractedDocument(
            document_id="demo_bidder2_financial",
            bidder_id="bidder2",
            file_name="bidder2_financial_statement.pdf",
            pages=[
                "XYZ Limited Financial Report 2023. Annual turnover: $8 million. "
                "Net income: $1.2 million. Total assets: $12 million. "
                "The company has shown steady growth with 15% increase in revenue. "
                "Working capital: $3 million. Current ratio: 2.1. "
                "Operating costs: $6 million. Profit margin: 15%."
            ],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        ),
        ExtractedDocument(
            document_id="demo_bidder2_compliance",
            bidder_id="bidder2",
            file_name="bidder2_compliance_documents.pdf",
            pages=[
                "Compliance and Regulatory Documentation. "
                "Company registration number: 12345678. Registered on: January 15, 2010. "
                "Tax compliance certificate valid until December 31, 2024. "
                "GST registration: GSTIN123456789. "
                "All statutory compliances are up to date as of March 2024. "
                "Environmental clearance certificate obtained on February 1, 2023. "
                "Labor law compliance certificate valid until June 30, 2024."
            ],
            page_metadata=[{"page": 1}],
            extraction_method="pdfplumber"
        )
    ]
    
    return sample_docs


def main():
    """Main function to demonstrate pre-computation workflow"""
    print("=" * 60)
    print("Demo Embeddings Pre-computation Utility")
    print("=" * 60)
    print()
    
    # Create sample demo documents
    print("Creating sample demo documents...")
    demo_docs = create_sample_demo_documents()
    print(f"Created {len(demo_docs)} sample documents")
    print()
    
    # Pre-compute embeddings
    precompute_demo_embeddings(demo_docs)
    print()
    
    # Test loading cached embeddings
    print("Testing cache loading...")
    engine = load_cached_embeddings()
    print()
    
    # Test retrieval with cached embeddings
    print("Testing retrieval with cached embeddings...")
    query = "financial revenue information"
    results = engine.retrieve(query, top_k=3)
    
    print(f"Query: '{query}'")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Document: {result.source_file}")
        print(f"    Page: {result.page_number}")
        print(f"    Confidence: {result.confidence:.4f}")
        print(f"    Text preview: {result.text[:100]}...")
    
    print()
    print("=" * 60)
    print("Pre-computation workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
