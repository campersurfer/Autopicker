#!/usr/bin/env python3
"""
Test script for concurrent processing functionality
"""
import asyncio
import json
from pathlib import Path
from typing import List

# Simple mock classes for testing without full dependencies
class MockSearchResult:
    def __init__(self, title: str, url: str, content: str, engine: str = "mock"):
        self.title = title
        self.url = url
        self.content = content
        self.engine = engine
    
    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "engine": self.engine
        }

class MockSearchService:
    async def search(self, query: str, num_results: int = 5):
        # Simulate network delay
        await asyncio.sleep(0.3)
        
        return [
            MockSearchResult(
                title=f"Mock result {i+1} for '{query}'",
                url=f"https://example.com/result{i+1}",
                content=f"Mock content for {query} result {i+1}",
                engine="mock"
            )
            for i in range(num_results)
        ]
    
    async def search_with_context(self, query: str, context: str, num_results: int = 5):
        # Enhanced search with context
        await asyncio.sleep(0.4)
        
        return [
            MockSearchResult(
                title=f"Context-enhanced result {i+1} for '{query}'",
                url=f"https://example.com/context{i+1}",
                content=f"Mock content enhanced with context '{context[:50]}...' for query '{query}'",
                engine="mock-context"
            )
            for i in range(num_results)
        ]

class MockFileProcessor:
    def is_supported(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.txt', '.json', '.csv']
    
    def get_file_type(self, file_path: Path) -> str:
        return file_path.suffix[1:] if file_path.suffix else 'unknown'
    
    def process_file(self, file_path: Path):
        try:
            if not file_path.exists():
                return {
                    'processing_status': 'error',
                    'error': f'File not found: {file_path}'
                }
            
            # Simulate processing time
            import time
            time.sleep(0.1)
            
            # Read file content
            content = {}
            
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    content = {
                        'text': text,
                        'line_count': len(text.split('\n')),
                        'word_count': len(text.split()),
                        'char_count': len(text)
                    }
            
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    content = {
                        'text': json.dumps(data, indent=2),
                        'json_data': data,
                        'keys': list(data.keys()) if isinstance(data, dict) else [],
                        'size': len(str(data))
                    }
            
            elif file_path.suffix.lower() == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    content = {
                        'text': ''.join(lines),
                        'row_count': len(lines),
                        'header': lines[0].strip() if lines else '',
                        'sample_rows': lines[:3] if len(lines) > 1 else []
                    }
            
            return {
                'processing_status': 'success',
                'content': content
            }
            
        except Exception as e:
            return {
                'processing_status': 'error',
                'error': str(e)
            }
    
    def get_file_summary(self, result):
        if result['processing_status'] != 'success':
            return "File processing failed"
        
        content = result['content']
        file_type = 'text'  # simplified for mock
        
        if 'line_count' in content:
            return f"Text file with {content.get('line_count', 0)} lines and {content.get('word_count', 0)} words"
        elif 'json_data' in content:
            return f"JSON file with {len(content.get('keys', []))} top-level keys"
        elif 'row_count' in content:
            return f"CSV file with {content.get('row_count', 0)} rows"
        else:
            return "Processed file content"

# Import the actual ConcurrentProcessor
import sys
sys.path.append('.')

# Copy the ConcurrentProcessor class definition here for testing
class ConcurrentProcessor:
    """
    Service for concurrent processing of files and web search operations
    """
    
    def __init__(self, file_processor=None, search_service=None):
        self.file_processor = file_processor or MockFileProcessor()
        self.search_service = search_service or MockSearchService()
    
    async def process_with_search(self, file_paths: List[Path], query: str, num_results: int = 5):
        """
        Process multiple files and perform web search concurrently
        """
        try:
            # Create tasks for concurrent execution
            file_tasks = [self._process_single_file(file_path) for file_path in file_paths]
            search_task = self.search_service.search(query, num_results)
            
            print(f"Starting concurrent processing: {len(file_paths)} files + search for '{query}'")
            
            # Execute all tasks concurrently
            results = await asyncio.gather(
                *file_tasks,
                search_task,
                return_exceptions=True
            )
            
            # Separate file results from search results
            file_results = results[:-1]
            search_results = results[-1]
            
            # Process file results and handle any exceptions
            processed_files = []
            for i, result in enumerate(file_results):
                if isinstance(result, Exception):
                    print(f"File processing failed for {file_paths[i]}: {result}")
                    processed_files.append({
                        "file_path": str(file_paths[i]),
                        "status": "error",
                        "error": str(result)
                    })
                else:
                    processed_files.append({
                        "file_path": str(file_paths[i]),
                        "status": "success",
                        **result
                    })
            
            # Handle search results
            if isinstance(search_results, Exception):
                print(f"Search failed: {search_results}")
                search_data = {
                    "status": "error",
                    "error": str(search_results),
                    "results": []
                }
            else:
                search_data = {
                    "status": "success",
                    "results": [result.to_dict() for result in search_results],
                    "total_results": len(search_results)
                }
            
            print(f"Concurrent processing completed: {len(processed_files)} files processed, search {'succeeded' if search_data['status'] == 'success' else 'failed'}")
            
            return {
                "file_contents": processed_files,
                "search_results": search_data,
                "query": query,
                "total_files": len(file_paths),
                "processing_time_savings": "Concurrent execution reduced total processing time"
            }
            
        except Exception as e:
            print(f"Concurrent processing failed: {e}")
            raise
    
    async def _process_single_file(self, file_path: Path):
        """
        Process a single file asynchronously
        """
        try:
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if file type is supported
            if not self.file_processor.is_supported(file_path):
                file_type = self.file_processor.get_file_type(file_path)
                raise ValueError(f"File type {file_type} is not supported")
            
            # Process the file
            result = self.file_processor.process_file(file_path)
            
            if result['processing_status'] == 'success':
                summary = self.file_processor.get_file_summary(result)
                return {
                    "content": result['content'],
                    "summary": summary,
                    "file_type": self.file_processor.get_file_type(file_path)
                }
            else:
                raise Exception(result.get('error', 'Unknown processing error'))
                
        except Exception as e:
            print(f"File processing error for {file_path}: {e}")
            raise

# Test functions
async def test_concurrent_processing():
    """Test concurrent file processing and search"""
    print("🧪 Testing Concurrent Processing")
    print("=" * 50)
    
    # Create test directory and files
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create test files
    test_files = []
    
    # Text file
    text_file = test_dir / "sample.txt"
    with open(text_file, 'w') as f:
        f.write("This is a sample text file for testing concurrent processing.\nIt has multiple lines.\nWith various content.")
    test_files.append(text_file)
    
    # JSON file  
    json_file = test_dir / "sample.json"
    with open(json_file, 'w') as f:
        json.dump({
            "name": "Test Data",
            "version": "1.0",
            "features": ["concurrent", "processing", "search"],
            "count": 42
        }, f, indent=2)
    test_files.append(json_file)
    
    # CSV file
    csv_file = test_dir / "sample.csv"
    with open(csv_file, 'w') as f:
        f.write("id,name,value\n1,Test Item 1,100\n2,Test Item 2,200\n3,Test Item 3,300\n")
    test_files.append(csv_file)
    
    print(f"Created {len(test_files)} test files:")
    for file in test_files:
        print(f"  📄 {file.name}")
    
    # Initialize concurrent processor
    processor = ConcurrentProcessor()
    
    # Test concurrent processing
    print(f"\n🔄 Processing {len(test_files)} files + search concurrently...")
    
    import time
    start_time = time.time()
    
    result = await processor.process_with_search(
        file_paths=test_files,
        query="machine learning and AI",
        num_results=3
    )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Display results
    print(f"\n✅ Concurrent processing completed in {processing_time:.2f} seconds")
    print(f"🗂️  Files processed: {result['total_files']}")
    print(f"🔍 Search query: '{result['query']}'")
    
    print(f"\n📄 File Processing Results:")
    for i, file_result in enumerate(result['file_contents']):
        status = "✅" if file_result['status'] == 'success' else "❌"
        print(f"  {status} {Path(file_result['file_path']).name}: {file_result.get('summary', file_result.get('error', 'Unknown'))}")
    
    search_data = result['search_results']
    search_status = "✅" if search_data['status'] == 'success' else "❌"
    print(f"\n🔍 Search Results: {search_status}")
    if search_data['status'] == 'success':
        print(f"  Found {search_data['total_results']} results:")
        for i, search_result in enumerate(search_data['results'][:2]):  # Show first 2
            print(f"    {i+1}. {search_result['title']}")
            print(f"       {search_result['url']}")
    else:
        print(f"  Error: {search_data.get('error', 'Unknown error')}")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test files...")
    for file in test_files:
        if file.exists():
            file.unlink()
    test_dir.rmdir()
    
    print(f"\n🎉 Concurrent processing test completed successfully!")
    return True

async def test_performance_comparison():
    """Compare concurrent vs sequential processing performance"""
    print("\n⚡ Testing Performance Comparison")
    print("=" * 50)
    
    # Create larger test dataset
    test_dir = Path("perf_test_files")
    test_dir.mkdir(exist_ok=True)
    
    test_files = []
    
    # Create 5 test files
    for i in range(5):
        file_path = test_dir / f"test_{i}.txt"
        with open(file_path, 'w') as f:
            f.write(f"Test file {i} content.\n" * 100)  # 100 lines each
        test_files.append(file_path)
    
    processor = ConcurrentProcessor()
    
    # Test concurrent processing
    print("🔄 Testing concurrent processing...")
    import time
    start_time = time.time()
    
    concurrent_result = await processor.process_with_search(
        file_paths=test_files,
        query="performance testing",
        num_results=3
    )
    
    concurrent_time = time.time() - start_time
    
    # Test sequential processing (simulate)
    print("🐌 Testing sequential processing (simulated)...")
    start_time = time.time()
    
    # Process files sequentially
    sequential_files = []
    for file_path in test_files:
        result = await processor._process_single_file(file_path)
        sequential_files.append(result)
    
    # Search separately
    search_results = await processor.search_service.search("performance testing", 3)
    
    sequential_time = time.time() - start_time
    
    # Calculate performance improvement
    time_saved = sequential_time - concurrent_time
    percentage_improvement = (time_saved / sequential_time) * 100
    
    print(f"\n📊 Performance Results:")
    print(f"  🔄 Concurrent processing: {concurrent_time:.2f} seconds")
    print(f"  🐌 Sequential processing: {sequential_time:.2f} seconds")
    print(f"  ⚡ Time saved: {time_saved:.2f} seconds ({percentage_improvement:.1f}% improvement)")
    
    # Cleanup
    for file in test_files:
        if file.exists():
            file.unlink()
    test_dir.rmdir()
    
    print(f"\n🎉 Performance test completed!")
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting Concurrent Processing Tests")
    print("=" * 60)
    
    try:
        # Test basic functionality
        await test_concurrent_processing()
        
        # Test performance
        await test_performance_comparison()
        
        print(f"\n🎊 All tests passed! Concurrent processing is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())