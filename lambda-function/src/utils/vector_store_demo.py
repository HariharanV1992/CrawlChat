"""
Vector Store Demo Script
Demonstrates the vector store functionality with sample data.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from src.services.vector_store_service import vector_store_service
from src.services.document_processing_service import document_processing_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample stock market data for demonstration
SAMPLE_DATA = [
    {
        "title": "Tesla Stock Analysis Q4 2024",
        "content": """
        Tesla (TSLA) reported strong Q4 2024 earnings with revenue of $25.17 billion, 
        up 3% year-over-year. The company delivered 484,507 vehicles in Q4, bringing 
        total 2024 deliveries to 1.81 million vehicles. Tesla's energy storage business 
        continues to grow, with deployments reaching 14.7 GWh in 2024. The company 
        expects vehicle volume growth to be notably lower in 2025 as teams work on 
        launching the next-generation vehicle and other products.
        
        Key highlights:
        - Q4 revenue: $25.17 billion
        - Q4 deliveries: 484,507 vehicles
        - 2024 total deliveries: 1.81 million
        - Energy storage deployments: 14.7 GWh
        - Next-generation vehicle in development
        """,
        "url": "https://example.com/tesla-q4-2024",
        "domain": "example.com",
        "crawled_at": int(datetime.utcnow().timestamp())
    },
    {
        "title": "Apple's AI Strategy and Market Position",
        "content": """
        Apple (AAPL) is making significant strides in artificial intelligence integration 
        across its product ecosystem. The company's AI strategy focuses on on-device 
        processing, privacy, and seamless user experience. Apple's latest iPhone 15 
        series features advanced AI capabilities including improved photography, 
        enhanced Siri functionality, and intelligent battery management.
        
        Market analysts predict Apple's AI investments will drive long-term growth, 
        particularly in services revenue. The company's approach to AI emphasizes 
        user privacy and data security, setting it apart from competitors who rely 
        heavily on cloud-based AI processing.
        
        Key AI features:
        - On-device AI processing
        - Enhanced photography with AI
        - Improved Siri capabilities
        - Privacy-focused approach
        """,
        "url": "https://example.com/apple-ai-strategy",
        "domain": "example.com",
        "crawled_at": int(datetime.utcnow().timestamp())
    },
    {
        "title": "Microsoft's Cloud Computing Dominance",
        "content": """
        Microsoft (MSFT) continues to lead in cloud computing with Azure showing 
        strong growth in Q4 2024. The company reported cloud revenue of $25.9 billion, 
        up 20% year-over-year. Azure's growth was driven by strong demand for AI 
        services, with customers increasingly adopting Azure OpenAI Service and 
        other AI-powered solutions.
        
        Microsoft's partnership with OpenAI has positioned the company as a leader 
        in enterprise AI adoption. The integration of AI capabilities across 
        Microsoft 365, Azure, and other services is driving customer engagement 
        and revenue growth.
        
        Key metrics:
        - Cloud revenue: $25.9 billion
        - Azure growth: 20% YoY
        - AI services adoption increasing
        - Strong enterprise demand
        """,
        "url": "https://example.com/microsoft-cloud-2024",
        "domain": "example.com",
        "crawled_at": int(datetime.utcnow().timestamp())
    },
    {
        "title": "Amazon's E-commerce and AWS Performance",
        "content": """
        Amazon (AMZN) reported mixed Q4 2024 results with strong AWS performance 
        but slower e-commerce growth. AWS revenue reached $24.2 billion, up 13% 
        year-over-year, driven by enterprise cloud adoption and AI services. 
        The company's e-commerce business showed signs of recovery with improved 
        profitability despite slower revenue growth.
        
        Amazon's AI investments in AWS are paying off, with customers adopting 
        services like Amazon Bedrock and SageMaker for machine learning projects. 
        The company's logistics network continues to improve efficiency, reducing 
        delivery times and costs.
        
        Performance highlights:
        - AWS revenue: $24.2 billion
        - AWS growth: 13% YoY
        - AI services gaining traction
        - Improved logistics efficiency
        """,
        "url": "https://example.com/amazon-q4-2024",
        "domain": "example.com",
        "crawled_at": int(datetime.utcnow().timestamp())
    },
    {
        "title": "Google's AI and Advertising Revenue",
        "content": """
        Google (GOOGL) parent Alphabet reported strong Q4 2024 results with 
        advertising revenue growth and AI innovation driving performance. The 
        company's advertising revenue reached $65.5 billion, up 11% year-over-year, 
        while YouTube advertising grew 15% to $9.2 billion.
        
        Google's AI investments are transforming its products and services. The 
        company's Gemini AI model is being integrated across Google's ecosystem, 
        improving search results, productivity tools, and advertising effectiveness. 
        Google Cloud also showed strong growth, reaching $9.2 billion in revenue.
        
        Key achievements:
        - Advertising revenue: $65.5 billion
        - YouTube growth: 15% YoY
        - Gemini AI integration
        - Cloud revenue: $9.2 billion
        """,
        "url": "https://example.com/google-ai-advertising",
        "domain": "example.com",
        "crawled_at": int(datetime.utcnow().timestamp())
    }
]

async def demo_vector_store_creation():
    """Demonstrate vector store creation and setup."""
    logger.info("=== Vector Store Creation Demo ===")
    
    try:
        # Create or get vector store
        vector_store_id = await vector_store_service.get_or_create_vector_store(
            name="Stock Market Demo Store"
        )
        logger.info(f"Vector store ID: {vector_store_id}")
        
        # Get vector store info
        store_info = await vector_store_service.get_vector_store_info()
        logger.info(f"Vector store info: {json.dumps(store_info, indent=2)}")
        
        return vector_store_id
        
    except Exception as e:
        logger.error(f"Error in vector store creation demo: {e}")
        raise

async def demo_document_processing():
    """Demonstrate document processing with sample data."""
    logger.info("=== Document Processing Demo ===")
    
    try:
        # Process sample data
        results = await document_processing_service.process_crawled_data(SAMPLE_DATA)
        
        # Count successes and failures
        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = len(results) - success_count
        
        logger.info(f"Processed {len(results)} documents:")
        logger.info(f"  - Successful: {success_count}")
        logger.info(f"  - Failed: {error_count}")
        
        # Show successful results
        for i, result in enumerate(results):
            if result.get("status") == "success":
                logger.info(f"  Document {i+1}: {result.get('document_id')}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in document processing demo: {e}")
        raise

async def demo_semantic_search():
    """Demonstrate semantic search capabilities."""
    logger.info("=== Semantic Search Demo ===")
    
    try:
        # Test queries
        test_queries = [
            "What are Tesla's Q4 2024 earnings?",
            "How is Apple performing in AI?",
            "What is Microsoft's cloud revenue?",
            "Tell me about Amazon's AWS performance",
            "How is Google's advertising business doing?"
        ]
        
        for query in test_queries:
            logger.info(f"\nSearching for: '{query}'")
            
            # Perform search
            search_results = await document_processing_service.search_documents(
                query=query,
                max_results=3
            )
            
            logger.info(f"Found {search_results['total_results']} results:")
            
            for i, result in enumerate(search_results['results'][:2]):  # Show top 2
                score = result.get('score', 0)
                filename = result.get('filename', 'Unknown')
                logger.info(f"  {i+1}. {filename} (Score: {score:.3f})")
                
                # Show first content snippet
                content_parts = []
                for content in result.get('content', []):
                    if content.get('type') == 'text':
                        content_parts.append(content['text'][:100] + "...")
                
                if content_parts:
                    logger.info(f"     Content: {content_parts[0]}")
        
    except Exception as e:
        logger.error(f"Error in semantic search demo: {e}")
        raise

async def demo_summary_generation():
    """Demonstrate AI-powered summary generation."""
    logger.info("=== Summary Generation Demo ===")
    
    try:
        # Test summary queries
        summary_queries = [
            "Summarize the latest tech company earnings",
            "What are the key trends in AI adoption by tech companies?",
            "Compare the cloud computing performance of major tech companies"
        ]
        
        for query in summary_queries:
            logger.info(f"\nGenerating summary for: '{query}'")
            
            # Generate summary
            summary = await document_processing_service.get_document_summary(
                query=query,
                max_results=5
            )
            
            logger.info(f"Summary:\n{summary}")
        
    except Exception as e:
        logger.error(f"Error in summary generation demo: {e}")
        raise

async def demo_advanced_search():
    """Demonstrate advanced search with filters."""
    logger.info("=== Advanced Search Demo ===")
    
    try:
        # Search for earnings content
        logger.info("\nSearching for earnings content:")
        results = await document_processing_service.search_documents(
            query="earnings revenue growth",
            max_results=3
        )
        
        logger.info(f"Found {results['total_results']} results")
        
        # Search for AI content
        logger.info("\nSearching for AI content:")
        results = await document_processing_service.search_documents(
            query="AI artificial intelligence",
            max_results=3
        )
        
        logger.info(f"Found {results['total_results']} results")
        
    except Exception as e:
        logger.error(f"Error in advanced search demo: {e}")
        raise

async def demo_vector_store_stats():
    """Demonstrate vector store statistics."""
    logger.info("=== Vector Store Statistics Demo ===")
    
    try:
        # Get stats
        stats = await document_processing_service.get_vector_store_stats()
        
        logger.info("Vector Store Statistics:")
        logger.info(json.dumps(stats, indent=2))
        
        # List files
        files = await vector_store_service.list_vector_store_files()
        logger.info(f"\nTotal files in vector store: {len(files)}")
        
        for i, file_info in enumerate(files[:5]):  # Show first 5
            logger.info(f"  {i+1}. {file_info.get('filename', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Error in vector store stats demo: {e}")
        raise

async def main():
    """Run the complete vector store demonstration."""
    logger.info("Starting Vector Store Demo...")
    
    try:
        # 1. Create vector store
        await demo_vector_store_creation()
        
        # 2. Process documents
        await demo_document_processing()
        
        # 3. Demonstrate semantic search
        await demo_semantic_search()
        
        # 4. Generate summaries
        await demo_summary_generation()
        
        # 5. Advanced search with filters
        await demo_advanced_search()
        
        # 6. Show statistics
        await demo_vector_store_stats()
        
        logger.info("\n=== Vector Store Demo Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main()) 