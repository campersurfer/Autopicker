#!/usr/bin/env python3
"""
Test script for token management and chunking functionality
"""

import sys
from pathlib import Path
import asyncio

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from token_manager import token_manager, ChunkingStrategy
from content_summarizer import ContentSummarizer

def test_token_counting():
    """Test basic token counting functionality"""
    print("=== Testing Token Counting ===")
    
    test_text = "This is a test document with some content to analyze for token counting purposes."
    tokens = token_manager.token_counter.count_tokens(test_text)
    print(f"Test text: '{test_text}'")
    print(f"Estimated tokens: {tokens}")
    
    # Test with different model families
    gpt4_tokens = token_manager.token_counter.count_tokens(test_text, "gpt-4")
    print(f"GPT-4 tokens: {gpt4_tokens}")
    
    print()

def test_chunking():
    """Test content chunking functionality"""
    print("=== Testing Content Chunking ===")
    
    # Create a longer test document
    long_text = """
    This is a comprehensive test document that contains multiple paragraphs and sections.
    
    Introduction:
    This document serves as a test case for our chunking algorithm. It contains various types of content including headers, paragraphs, and structured information.
    
    Main Content:
    The main content section includes detailed information about various topics. This section is designed to be long enough to require chunking when processed with smaller token limits.
    
    Technical Details:
    Here we include technical specifications, code examples, and detailed explanations that would typically be found in documentation or technical papers.
    
    Conclusion:
    The conclusion summarizes the key points and provides final thoughts on the subject matter discussed throughout the document.
    """ * 5  # Repeat to make it longer
    
    print(f"Original content length: {len(long_text)} characters")
    
    # Test chunking with different strategies
    chunker = token_manager.chunker
    max_tokens = 200
    
    # Semantic chunking
    chunks = chunker.chunk_content(
        content=long_text,
        max_tokens=max_tokens,
        strategy=ChunkingStrategy.SEMANTIC,
        source_file="test_document.txt"
    )
    
    print(f"\nSemantic chunking with {max_tokens} max tokens:")
    print(f"Number of chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\nChunk {i+1}:")
        print(f"  Tokens: {chunk.tokens}")
        print(f"  Content preview: {chunk.content[:100]}...")
    
    print()

def test_content_summarization():
    """Test content summarization functionality"""
    print("=== Testing Content Summarization ===")
    
    # Initialize content summarizer
    summarizer = ContentSummarizer(token_manager.token_counter)
    
    # Test document
    test_document = """
    Artificial Intelligence and Machine Learning in Modern Applications
    
    Introduction:
    Artificial intelligence (AI) and machine learning (ML) have become critical technologies in modern software development. These technologies enable systems to learn from data, make predictions, and automate complex decision-making processes.
    
    Key Applications:
    1. Natural Language Processing: AI systems can understand, interpret, and generate human language with increasing accuracy.
    2. Computer Vision: Machine learning algorithms can analyze and interpret visual information from images and videos.
    3. Predictive Analytics: AI models can forecast trends and outcomes based on historical data patterns.
    4. Automation: Intelligent systems can automate repetitive tasks and optimize workflows.
    
    Implementation Considerations:
    When implementing AI/ML solutions, developers must consider data quality, model selection, training requirements, and performance optimization. It's important to evaluate different algorithms and approaches to find the best fit for specific use cases.
    
    Future Trends:
    The field continues to evolve rapidly with advances in deep learning, neural networks, and specialized hardware. Organizations are increasingly adopting AI-powered solutions to gain competitive advantages and improve operational efficiency.
    
    Conclusion:
    AI and ML technologies offer significant opportunities for innovation and improvement across various industries. Success requires careful planning, proper implementation, and ongoing optimization of these powerful tools.
    """
    
    print(f"Original document length: {len(test_document)} characters")
    original_tokens = token_manager.token_counter.count_tokens(test_document)
    print(f"Original tokens: {original_tokens}")
    
    # Test summarization with different target sizes
    target_tokens = 100
    
    summary = summarizer.summarize_content(
        content=test_document,
        target_tokens=target_tokens,
        context_keywords=["AI", "machine learning", "applications"]
    )
    
    print(f"\nSummarization results (target: {target_tokens} tokens):")
    print(f"Strategy used: {summary.strategy_used}")
    print(f"Original tokens: {summary.original_tokens}")
    print(f"Summarized tokens: {summary.summarized_tokens}")
    print(f"Compression ratio: {summary.compression_ratio:.2f}")
    print(f"Compression percentage: {summary.metadata.get('compression_percentage', 0)}%")
    
    print(f"\nSummarized content:")
    print(summary.summarized_content)
    
    print(f"\nKey points identified:")
    for point in summary.key_points:
        print(f"  - {point}")
    
    print()

def test_batch_summarization():
    """Test batch file summarization"""
    print("=== Testing Batch Summarization ===")
    
    summarizer = ContentSummarizer(token_manager.token_counter)
    
    # Simulate multiple files
    file_contents = [
        {
            "filename": "document1.txt",
            "type": "text",
            "content": "This is the first document containing information about project planning and requirements gathering. It includes detailed specifications and technical requirements for the development process."
        },
        {
            "filename": "document2.txt", 
            "type": "text",
            "content": "The second document focuses on implementation strategies and best practices. It covers coding standards, testing procedures, and deployment methodologies that should be followed throughout the project lifecycle."
        },
        {
            "filename": "document3.txt",
            "type": "text", 
            "content": "This final document discusses performance optimization, security considerations, and maintenance procedures. It provides guidelines for ensuring the system operates efficiently and securely in production environments."
        }
    ]
    
    total_target_tokens = 150
    
    summaries = summarizer.batch_summarize_files(
        file_contents=file_contents,
        total_target_tokens=total_target_tokens,
        context_keywords=["project", "development", "implementation"]
    )
    
    print(f"Batch summarization with {total_target_tokens} total target tokens:")
    print(f"Number of files: {len(file_contents)}")
    
    total_original = sum(s.original_tokens for s in summaries)
    total_summarized = sum(s.summarized_tokens for s in summaries)
    
    print(f"Total original tokens: {total_original}")
    print(f"Total summarized tokens: {total_summarized}")
    print(f"Overall compression: {round((1 - total_summarized/total_original) * 100, 1)}%")
    
    for i, summary in enumerate(summaries):
        print(f"\nFile {i+1} ({file_contents[i]['filename']}):")
        print(f"  Original tokens: {summary.original_tokens}")
        print(f"  Summarized tokens: {summary.summarized_tokens}")
        print(f"  Strategy: {summary.strategy_used}")
        print(f"  Summary: {summary.summarized_content[:100]}...")
    
    print()

def test_model_analysis():
    """Test model context analysis"""
    print("=== Testing Model Context Analysis ===")
    
    # Test different models
    test_models = ["gpt-4o", "claude-3.5-sonnet", "gemini-pro", "llama-3.1-70b"]
    
    for model in test_models:
        context_window = token_manager.get_model_context_window(model)
        budget = token_manager.create_token_budget(model)
        
        print(f"\n{model}:")
        print(f"  Context window: {context_window:,} tokens")
        print(f"  Available for files: {budget.file_content:,} tokens")
        print(f"  System prompt allocation: {budget.system_prompt} tokens")
        print(f"  Response buffer: {budget.response_buffer} tokens")
    
    print()

def main():
    """Run all tests"""
    print("🧪 Token Management Test Suite")
    print("=" * 50)
    
    try:
        test_token_counting()
        test_chunking()
        test_content_summarization()
        test_batch_summarization()
        test_model_analysis()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()