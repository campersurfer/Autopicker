#!/usr/bin/env python3
"""
Performance optimization and load testing suite for Autopicker Platform
Includes caching, connection pooling, async optimization, and load testing
"""

import asyncio
import time
import json
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import hashlib
import statistics
from pathlib import Path
import concurrent.futures
from dataclasses import dataclass

# Third-party imports
import httpx
import aiofiles
from functools import lru_cache, wraps
import asyncio_throttle

# Optional Redis for caching
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: Redis not available. Using in-memory caching.")


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AsyncCache:
    """High-performance async caching system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0}
        self.redis_url = redis_url
        # Note: async setup will be called when the async cache is first used
    
    async def setup_cache(self, redis_url: str):
        """Setup Redis cache if available"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                await self.redis_client.ping()
                print("Redis cache initialized")
            except Exception as e:
                print(f"Redis not available, using memory cache: {e}")
                self.redis_client = None
        else:
            print("Using in-memory cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Ensure cache is set up
        if self.redis_client is None and REDIS_AVAILABLE:
            await self.setup_cache(self.redis_url)
            
        try:
            if self.redis_client:
                # Try Redis first
                value = await self.redis_client.get(key)
                if value:
                    self.cache_stats["hits"] += 1
                    return json.loads(value)
            
            # Fallback to memory cache
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if entry["expires"] > time.time():
                    self.cache_stats["hits"] += 1
                    return entry["value"]
                else:
                    del self.memory_cache[key]
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            print(f"Cache get error: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            serialized = json.dumps(value, default=str)
            
            if self.redis_client:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                # Memory cache with expiration
                self.memory_cache[key] = {
                    "value": value,
                    "expires": time.time() + ttl
                }
                
                # Clean old entries
                current_time = time.time()
                expired_keys = [
                    k for k, v in self.memory_cache.items()
                    if v["expires"] < current_time
                ]
                for k in expired_keys:
                    del self.memory_cache[k]
            
            self.cache_stats["sets"] += 1
            
        except Exception as e:
            print(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            if key in self.memory_cache:
                del self.memory_cache[key]
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_type": "redis" if self.redis_client else "memory",
            "memory_cache_size": len(self.memory_cache)
        }


class ConnectionPool:
    """Optimized HTTP connection pool"""
    
    def __init__(self, max_connections: int = 100, max_keepalive: int = 20):
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive
            ),
            timeout=httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=10.0,
                pool=5.0
            ),
            http2=True  # Enable HTTP/2 for better performance
        )
    
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with connection pooling"""
        return await self.client.request(method, url, **kwargs)
    
    async def close(self):
        """Close connection pool"""
        await self.client.aclose()


class PerformanceOptimizer:
    """Main performance optimization manager"""
    
    def __init__(self):
        self.cache = AsyncCache()
        self.connection_pool = ConnectionPool()
        self.metrics: List[PerformanceMetrics] = []
        self.throttle = asyncio_throttle.Throttler(rate_limit=100, period=60)  # 100/min
        
    def cache_result(self, ttl: int = 3600, key_func: Optional[Callable] = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation
                    key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
                    cache_key = hashlib.md5(key_data.encode()).hexdigest()
                
                # Try to get from cache
                cached_result = await self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.cache.set(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator
    
    def measure_performance(self, operation_name: str):
        """Decorator to measure function performance"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    
                    metric = PerformanceMetrics(
                        operation=operation_name,
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        success=success,
                        error=error
                    )
                    
                    self.metrics.append(metric)
                    
                    # Keep only recent metrics (last 1000)
                    if len(self.metrics) > 1000:
                        self.metrics = self.metrics[-1000:]
            
            return wrapper
        return decorator
    
    async def batch_process(self, items: List[Any], process_func: Callable, 
                          batch_size: int = 10, max_concurrent: int = 5) -> List[Any]:
        """Process items in optimized batches"""
        results = []
        
        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch with concurrency limit
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_item(item):
                async with semaphore:
                    return await process_func(item)
            
            batch_results = await asyncio.gather(
                *[process_item(item) for item in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
        
        return results
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.metrics:
            return {"message": "No metrics available"}
        
        # Group metrics by operation
        operations = {}
        for metric in self.metrics:
            op = metric.operation
            if op not in operations:
                operations[op] = []
            operations[op].append(metric)
        
        # Calculate statistics for each operation
        summary = {}
        for op, metrics in operations.items():
            durations = [m.duration_ms for m in metrics if m.success]
            errors = [m for m in metrics if not m.success]
            
            if durations:
                summary[op] = {
                    "total_requests": len(metrics),
                    "successful_requests": len(durations),
                    "failed_requests": len(errors),
                    "success_rate_percent": round(len(durations) / len(metrics) * 100, 2),
                    "avg_duration_ms": round(statistics.mean(durations), 2),
                    "min_duration_ms": round(min(durations), 2),
                    "max_duration_ms": round(max(durations), 2),
                    "p95_duration_ms": round(statistics.quantiles(durations, n=20)[18], 2) if len(durations) >= 20 else None,
                    "p99_duration_ms": round(statistics.quantiles(durations, n=100)[98], 2) if len(durations) >= 100 else None,
                    "recent_errors": [e.error for e in errors[-5:]]  # Last 5 errors
                }
        
        return {
            "summary": summary,
            "cache_stats": self.cache.get_stats(),
            "total_metrics": len(self.metrics),
            "last_updated": datetime.now().isoformat()
        }


class LoadTester:
    """Load testing utilities"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[Dict[str, Any]] = []
    
    async def test_endpoint(self, endpoint: str, method: str = "GET", 
                          payload: Optional[Dict[str, Any]] = None,
                          concurrent_users: int = 10, 
                          requests_per_user: int = 10,
                          ramp_up_time: int = 5) -> Dict[str, Any]:
        """Load test a specific endpoint"""
        print(f"Starting load test: {concurrent_users} users, {requests_per_user} req/user on {endpoint}")
        
        url = f"{self.base_url}{endpoint}"
        results = []
        
        async def user_simulation(user_id: int):
            """Simulate a single user making requests"""
            user_results = []
            
            async with httpx.AsyncClient() as client:
                for request_num in range(requests_per_user):
                    start_time = time.time()
                    
                    try:
                        if method.upper() == "POST" and payload:
                            response = await client.post(url, json=payload)
                        else:
                            response = await client.get(url)
                        
                        duration_ms = (time.time() - start_time) * 1000
                        
                        user_results.append({
                            "user_id": user_id,
                            "request_num": request_num,
                            "status_code": response.status_code,
                            "duration_ms": duration_ms,
                            "success": 200 <= response.status_code < 300,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Small delay between requests
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000
                        user_results.append({
                            "user_id": user_id,
                            "request_num": request_num,
                            "status_code": 0,
                            "duration_ms": duration_ms,
                            "success": False,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
            
            return user_results
        
        # Ramp up users gradually
        tasks = []
        for user_id in range(concurrent_users):
            delay = (ramp_up_time / concurrent_users) * user_id
            task = asyncio.create_task(self._delayed_user_simulation(user_simulation, user_id, delay))
            tasks.append(task)
        
        # Wait for all users to complete
        all_results = await asyncio.gather(*tasks)
        
        # Flatten results
        for user_results in all_results:
            results.extend(user_results)
        
        # Calculate statistics
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        durations = [r["duration_ms"] for r in successful_requests]
        
        test_summary = {
            "endpoint": endpoint,
            "method": method,
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate_percent": round(len(successful_requests) / len(results) * 100, 2) if results else 0,
            "avg_response_time_ms": round(statistics.mean(durations), 2) if durations else 0,
            "min_response_time_ms": round(min(durations), 2) if durations else 0,
            "max_response_time_ms": round(max(durations), 2) if durations else 0,
            "p95_response_time_ms": round(statistics.quantiles(durations, n=20)[18], 2) if len(durations) >= 20 else None,
            "p99_response_time_ms": round(statistics.quantiles(durations, n=100)[98], 2) if len(durations) >= 100 else None,
            "requests_per_second": round(len(successful_requests) / (ramp_up_time + (requests_per_user * 0.1)), 2),
            "errors": list(set([r.get("error", "Unknown") for r in failed_requests if r.get("error")]))
        }
        
        self.results.append(test_summary)
        return test_summary
    
    async def _delayed_user_simulation(self, user_func: Callable, user_id: int, delay: float):
        """Run user simulation with delay"""
        await asyncio.sleep(delay)
        return await user_func(user_id)
    
    async def comprehensive_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load tests on key endpoints"""
        endpoints_to_test = [
            {"endpoint": "/health", "method": "GET"},
            {"endpoint": "/api/v1/models", "method": "GET"},
            {"endpoint": "/api/v1/files", "method": "GET"},
            {"endpoint": "/api/v1/chat/completions", "method": "POST", "payload": {
                "messages": [{"role": "user", "content": "Hello, this is a test message."}],
                "model": "auto",
                "max_tokens": 50
            }},
        ]
        
        print("Running comprehensive load tests...")
        all_results = []
        
        for test_config in endpoints_to_test:
            print(f"Testing {test_config['endpoint']}...")
            result = await self.test_endpoint(
                endpoint=test_config["endpoint"],
                method=test_config["method"],
                payload=test_config.get("payload"),
                concurrent_users=5,  # Moderate load for comprehensive test
                requests_per_user=10,
                ramp_up_time=3
            )
            all_results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(2)
        
        return {
            "test_results": all_results,
            "overall_summary": {
                "total_endpoints_tested": len(all_results),
                "total_requests": sum(r["total_requests"] for r in all_results),
                "overall_success_rate": round(
                    sum(r["successful_requests"] for r in all_results) / 
                    sum(r["total_requests"] for r in all_results) * 100, 2
                ) if sum(r["total_requests"] for r in all_results) > 0 else 0,
                "avg_response_time_ms": round(
                    statistics.mean([r["avg_response_time_ms"] for r in all_results if r["avg_response_time_ms"] > 0]), 2
                ) if any(r["avg_response_time_ms"] > 0 for r in all_results) else 0
            },
            "timestamp": datetime.now().isoformat()
        }


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()


async def optimize_ollama_requests():
    """Optimize Ollama API requests with connection pooling"""
    # This would be integrated into the main API
    pass


async def preload_models():
    """Preload AI models for faster response times"""
    # This would ensure models are loaded and ready
    pass


if __name__ == "__main__":
    # Performance testing
    async def main():
        print("Starting performance optimization tests...")
        
        # Test caching
        cache = AsyncCache()
        await cache.set("test_key", {"data": "test_value"}, 60)
        cached_value = await cache.get("test_key")
        print(f"Cache test: {cached_value}")
        
        # Test load testing
        print("\nRunning load tests...")
        load_tester = LoadTester("http://localhost:8001")
        
        # Test health endpoint
        health_results = await load_tester.test_endpoint(
            "/health", 
            concurrent_users=3, 
            requests_per_user=5
        )
        
        print(f"Health endpoint test results:")
        print(f"- Success rate: {health_results['success_rate_percent']}%")
        print(f"- Avg response time: {health_results['avg_response_time_ms']}ms")
        print(f"- Requests per second: {health_results['requests_per_second']}")
        
        # Get performance summary
        summary = performance_optimizer.get_performance_summary()
        print(f"\nPerformance summary: {json.dumps(summary, indent=2)}")
    
    asyncio.run(main())