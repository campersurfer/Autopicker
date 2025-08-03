import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from .search_service import SearchService, SearchResult
from ..processors.file_processor import FileProcessor

logger = logging.getLogger(__name__)

class ConcurrentProcessor:
    """
    Service for concurrent processing of files and web search operations
    """
    
    def __init__(self, file_processor: FileProcessor = None, search_service: SearchService = None):
        self.file_processor = file_processor or FileProcessor()
        self.search_service = search_service or SearchService()
    
    async def process_with_search(self, file_paths: List[Path], query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Process multiple files and perform web search concurrently
        
        Args:
            file_paths: List of file paths to process
            query: Search query to execute
            num_results: Number of search results to return
            
        Returns:
            Dictionary containing file contents and search results
        """
        try:
            # Create tasks for concurrent execution
            file_tasks = [self._process_single_file(file_path) for file_path in file_paths]
            search_task = self.search_service.search(query, num_results)
            
            logger.info(f"Starting concurrent processing: {len(file_paths)} files + search for '{query}'")
            
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
                    logger.error(f"File processing failed for {file_paths[i]}: {result}")
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
                logger.error(f"Search failed: {search_results}")
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
            
            logger.info(f"Concurrent processing completed: {len(processed_files)} files processed, search {'succeeded' if search_data['status'] == 'success' else 'failed'}")
            
            return {
                "file_contents": processed_files,
                "search_results": search_data,
                "query": query,
                "total_files": len(file_paths),
                "processing_time_savings": "Concurrent execution reduced total processing time"
            }
            
        except Exception as e:
            logger.error(f"Concurrent processing failed: {e}")
            raise
    
    async def _process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a single file asynchronously
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary containing file processing results
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
            logger.error(f"File processing error for {file_path}: {e}")
            raise
    
    async def process_files_with_context_search(self, file_paths: List[Path], base_query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Process files and perform context-enhanced search using file content
        
        Args:
            file_paths: List of file paths to process
            base_query: Base search query
            num_results: Number of search results per context search
            
        Returns:
            Dictionary containing file contents and context-enhanced search results
        """
        try:
            # First, process all files concurrently
            file_tasks = [self._process_single_file(file_path) for file_path in file_paths]
            file_results = await asyncio.gather(*file_tasks, return_exceptions=True)
            
            # Process file results and extract contexts
            processed_files = []
            search_contexts = []
            
            for i, result in enumerate(file_results):
                if isinstance(result, Exception):
                    logger.error(f"File processing failed for {file_paths[i]}: {result}")
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
                    # Extract text content for context
                    text_content = result.get('content', {}).get('text', '')
                    if text_content:
                        search_contexts.append(text_content[:500])  # First 500 chars
            
            # Perform context-enhanced searches concurrently
            if search_contexts:
                search_tasks = [
                    self.search_service.search_with_context(base_query, context, num_results)
                    for context in search_contexts
                ]
                search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                # Process search results
                context_searches = []
                for i, result in enumerate(search_results):
                    if isinstance(result, Exception):
                        logger.error(f"Context search failed for file {i}: {result}")
                        context_searches.append({
                            "file_index": i,
                            "status": "error",
                            "error": str(result)
                        })
                    else:
                        context_searches.append({
                            "file_index": i,
                            "status": "success",
                            "results": [r.to_dict() for r in result],
                            "total_results": len(result)
                        })
            else:
                context_searches = []
            
            logger.info(f"Context-enhanced concurrent processing completed: {len(processed_files)} files, {len(context_searches)} context searches")
            
            return {
                "file_contents": processed_files,
                "context_searches": context_searches,
                "base_query": base_query,
                "total_files": len(file_paths),
                "successful_context_searches": len([s for s in context_searches if s.get('status') == 'success'])
            }
            
        except Exception as e:
            logger.error(f"Context-enhanced concurrent processing failed: {e}")
            raise
    
    async def batch_process_files(self, file_paths: List[Path], batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Process files in batches to avoid overwhelming the system
        
        Args:
            file_paths: List of file paths to process
            batch_size: Number of files to process concurrently in each batch
            
        Returns:
            List of file processing results
        """
        try:
            all_results = []
            
            # Process files in batches
            for i in range(0, len(file_paths), batch_size):
                batch_paths = file_paths[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: {len(batch_paths)} files")
                
                # Process current batch concurrently
                batch_tasks = [self._process_single_file(file_path) for file_path in batch_paths]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process batch results
                for j, result in enumerate(batch_results):
                    file_path = batch_paths[j]
                    if isinstance(result, Exception):
                        logger.error(f"File processing failed for {file_path}: {result}")
                        all_results.append({
                            "file_path": str(file_path),
                            "status": "error",
                            "error": str(result)
                        })
                    else:
                        all_results.append({
                            "file_path": str(file_path),
                            "status": "success",
                            **result
                        })
            
            logger.info(f"Batch processing completed: {len(all_results)} files processed")
            return all_results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise

# Convenience functions
async def concurrent_file_search(file_paths: List[Path], query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Convenience function for concurrent file processing and search
    """
    processor = ConcurrentProcessor()
    return await processor.process_with_search(file_paths, query, num_results)

async def batch_process_files(file_paths: List[Path], batch_size: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function for batch file processing
    """
    processor = ConcurrentProcessor()
    return await processor.batch_process_files(file_paths, batch_size)