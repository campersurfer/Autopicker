import httpx
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import asyncio

logger = logging.getLogger(__name__)

class SearchResult:
    """
    Represents a single search result
    """
    def __init__(self, title: str, url: str, content: str, engine: str = "unknown"):
        self.title = title
        self.url = url
        self.content = content
        self.engine = engine
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "engine": self.engine
        }

class SearchService:
    """
    Web search service supporting multiple search backends
    """
    
    def __init__(self, searxng_url: str = "http://localhost:8888"):
        self.searxng_url = searxng_url
        self.timeout = 10.0
        
    async def search(self, query: str, num_results: int = 5, engines: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Perform web search using available search engines
        """
        try:
            # First try SearXNG if available
            return await self._search_searxng(query, num_results, engines)
        except Exception as e:
            logger.warning(f"SearXNG search failed: {e}")
            # Fallback to mock search for demonstration
            return await self._mock_search(query, num_results)
    
    async def _search_searxng(self, query: str, num_results: int = 5, engines: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Search using SearXNG instance
        """
        try:
            params = {
                "q": query,
                "format": "json",
                "safesearch": "0"
            }
            
            if engines:
                params["engines"] = ",".join(engines)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.searxng_url}/search", params=params)
                
                if response.status_code != 200:
                    raise Exception(f"SearXNG returned status code {response.status_code}")
                
                data = response.json()
                results = []
                
                for item in data.get("results", [])[:num_results]:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("content", ""),
                        engine=item.get("engine", "searxng")
                    )
                    results.append(result)
                
                logger.info(f"SearXNG search completed: {len(results)} results for query '{query}'")
                return results
                
        except Exception as e:
            logger.error(f"SearXNG search error: {e}")
            raise
    
    async def _mock_search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Mock search service for development and testing
        """
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        # Generate mock results based on query
        mock_results = [
            SearchResult(
                title=f"Search result 1 for '{query}'",
                url=f"https://example.com/result1?q={quote_plus(query)}",
                content=f"This is a mock search result related to {query}. It contains relevant information that would typically be found on the web.",
                engine="mock"
            ),
            SearchResult(
                title=f"Comprehensive guide to {query}",
                url=f"https://guide.example.com/{query.replace(' ', '-')}",
                content=f"A detailed guide covering all aspects of {query}, including best practices, tutorials, and expert insights.",
                engine="mock"
            ),
            SearchResult(
                title=f"{query} - Latest News and Updates",
                url=f"https://news.example.com/latest/{query.replace(' ', '-')}",
                content=f"Latest news and developments related to {query}. Stay updated with the most recent information and trends.",
                engine="mock"
            ),
            SearchResult(
                title=f"Forum Discussion: {query}",
                url=f"https://forum.example.com/discuss/{query.replace(' ', '-')}",
                content=f"Community discussion about {query}. Users share experiences, tips, and solutions related to this topic.",
                engine="mock"
            ),
            SearchResult(
                title=f"Research Paper: {query}",
                url=f"https://research.example.com/papers/{query.replace(' ', '-')}",
                content=f"Academic research and scientific papers about {query}. Peer-reviewed content from leading researchers.",
                engine="mock"
            )
        ]
        
        # Return requested number of results
        results = mock_results[:num_results]
        logger.info(f"Mock search completed: {len(results)} results for query '{query}'")
        return results
    
    async def search_with_context(self, query: str, context: str, num_results: int = 5) -> List[SearchResult]:
        """
        Enhanced search that includes context to improve relevance
        """
        # Enhance query with context
        enhanced_query = f"{query} {context}".strip()
        return await self.search(enhanced_query, num_results)
    
    async def multi_engine_search(self, query: str, engines: List[str], num_results: int = 5) -> Dict[str, List[SearchResult]]:
        """
        Search across multiple engines and return results grouped by engine
        """
        results = {}
        
        for engine in engines:
            try:
                engine_results = await self.search(query, num_results, [engine])
                results[engine] = engine_results
            except Exception as e:
                logger.warning(f"Search failed for engine {engine}: {e}")
                results[engine] = []
        
        return results
    
    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        """
        Format search results in a way that's optimal for LLM consumption
        """
        if not results:
            return "No search results found."
        
        formatted = "Search Results:\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **{result.title}**\n"
            formatted += f"   URL: {result.url}\n"
            formatted += f"   Content: {result.content[:200]}{'...' if len(result.content) > 200 else ''}\n\n"
        
        return formatted
    
    async def is_available(self) -> bool:
        """
        Check if SearXNG service is available
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.searxng_url}/")
                return response.status_code == 200
        except Exception:
            return False

# Convenience function
async def search_web(query: str, num_results: int = 5) -> List[SearchResult]:
    """
    Convenience function for web search
    """
    service = SearchService()
    return await service.search(query, num_results)