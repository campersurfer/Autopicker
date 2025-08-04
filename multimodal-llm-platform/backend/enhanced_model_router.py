#!/usr/bin/env python3
"""
Enhanced Model Router with OpenRouter Integration
Provides access to multiple AI models through different providers
"""

import os
import httpx
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger("autopicker.model_router")

class ModelProvider(Enum):
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"

@dataclass
class ModelInfo:
    id: str
    name: str
    provider: ModelProvider
    context_length: int
    cost_per_1k_tokens: float
    capabilities: List[str]  # ["text", "vision", "function_calling", "json_mode"]
    max_output_tokens: int
    description: str
    best_for: List[str]
    enterprise_cost: Optional[float] = None  # Enterprise pricing for direct APIs
    pricing_tier: str = "standard"  # "standard" (OpenRouter) or "enterprise" (direct)

class EnhancedModelRouter:
    """Enhanced model router with multiple provider support"""
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY") 
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # Pricing tier configuration
        self.default_pricing_tier = os.getenv("DEFAULT_PRICING_TIER", "standard")  # "standard" or "enterprise"
        self.enable_enterprise_apis = os.getenv("ENABLE_ENTERPRISE_APIS", "false").lower() == "true"
        
        # Model definitions
        self.models = self._initialize_models()
        
        # Fallback preferences (enterprise APIs preferred if available)
        self.fallback_order = [
            ModelProvider.OPENAI if self.enable_enterprise_apis else ModelProvider.OPENROUTER,
            ModelProvider.ANTHROPIC if self.enable_enterprise_apis else ModelProvider.OPENROUTER,
            ModelProvider.OPENROUTER,
            ModelProvider.OLLAMA
        ]
        
        # Usage tracking for Stripe billing
        self.usage_stats = {}
        self.billing_events = []
        
    def _initialize_models(self) -> Dict[str, ModelInfo]:
        """Initialize available models from different providers"""
        models = {}
        
        # OpenRouter Models (if API key available)
        if self.openrouter_api_key:
            openrouter_models = {
                # GPT Models
                "gpt-4o": ModelInfo(
                    id="openai/gpt-4o",
                    name="GPT-4o",
                    provider=ModelProvider.OPENROUTER,
                    context_length=128000,
                    cost_per_1k_tokens=5.0,
                    capabilities=["text", "vision", "function_calling", "json_mode"],
                    max_output_tokens=4096,
                    description="Latest GPT-4 with vision capabilities",
                    best_for=["complex_analysis", "vision", "function_calling", "large_documents"]
                ),
                "gpt-4o-mini": ModelInfo(
                    id="openai/gpt-4o-mini",
                    name="GPT-4o Mini",
                    provider=ModelProvider.OPENROUTER,
                    context_length=128000,
                    cost_per_1k_tokens=0.15,
                    capabilities=["text", "vision", "function_calling", "json_mode"],
                    max_output_tokens=16384,
                    description="Fast and affordable GPT-4 with vision",
                    best_for=["general_purpose", "fast_responses", "cost_effective"]
                ),
                "gpt-3.5-turbo": ModelInfo(
                    id="openai/gpt-3.5-turbo",
                    name="GPT-3.5 Turbo",
                    provider=ModelProvider.OPENROUTER,
                    context_length=16385,
                    cost_per_1k_tokens=0.5,
                    capabilities=["text", "function_calling"],
                    max_output_tokens=4096,
                    description="Fast and reliable for most tasks",
                    best_for=["simple_chat", "basic_analysis", "fast_responses"]
                ),
                
                # Claude Models
                "claude-3.5-sonnet": ModelInfo(
                    id="anthropic/claude-3.5-sonnet",
                    name="Claude 3.5 Sonnet",
                    provider=ModelProvider.OPENROUTER,
                    context_length=200000,
                    cost_per_1k_tokens=3.0,
                    capabilities=["text", "vision", "function_calling", "json_mode"],
                    max_output_tokens=8192,
                    description="Excellent for analysis and reasoning",
                    best_for=["document_analysis", "reasoning", "coding", "large_context"]
                ),
                "claude-3-haiku": ModelInfo(
                    id="anthropic/claude-3-haiku",
                    name="Claude 3 Haiku",
                    provider=ModelProvider.OPENROUTER,
                    context_length=200000,
                    cost_per_1k_tokens=0.25,
                    capabilities=["text", "vision"],
                    max_output_tokens=4096,
                    description="Fast and cost-effective Claude model",
                    best_for=["quick_summaries", "simple_analysis", "cost_effective"]
                ),
                
                # Gemini Models
                "gemini-pro": ModelInfo(
                    id="google/gemini-pro",
                    name="Gemini Pro",
                    provider=ModelProvider.OPENROUTER,
                    context_length=32768,
                    cost_per_1k_tokens=0.5,
                    capabilities=["text", "vision", "function_calling"],
                    max_output_tokens=8192,
                    description="Google's flagship model",
                    best_for=["multimodal", "creative_writing", "code_generation"]
                ),
                
                # Llama Models
                "llama-3.1-405b": ModelInfo(
                    id="meta-llama/llama-3.1-405b-instruct",
                    name="Llama 3.1 405B",
                    provider=ModelProvider.OPENROUTER,
                    context_length=32768,
                    cost_per_1k_tokens=2.7,
                    capabilities=["text", "function_calling", "json_mode"],
                    max_output_tokens=4096,
                    description="Most capable open-source model",
                    best_for=["complex_reasoning", "open_source", "large_scale_analysis"]
                ),
                "llama-3.1-70b": ModelInfo(
                    id="meta-llama/llama-3.1-70b-instruct",
                    name="Llama 3.1 70B",
                    provider=ModelProvider.OPENROUTER,
                    context_length=32768,
                    cost_per_1k_tokens=0.59,
                    capabilities=["text", "function_calling", "json_mode"],
                    max_output_tokens=4096,
                    description="Strong open-source model",
                    best_for=["general_purpose", "balanced_performance", "open_source"]
                ),
                "llama-3.1-8b": ModelInfo(
                    id="meta-llama/llama-3.1-8b-instruct",
                    name="Llama 3.1 8B",
                    provider=ModelProvider.OPENROUTER,
                    context_length=32768,
                    cost_per_1k_tokens=0.055,
                    capabilities=["text", "function_calling"],
                    max_output_tokens=4096,
                    description="Fast and affordable open-source model",
                    best_for=["simple_tasks", "cost_effective", "fast_responses"]
                ),
            }
            models.update(openrouter_models)
        
        # Direct Provider Models (Enterprise Pricing)
        if self.enable_enterprise_apis:
            # Direct OpenAI Models
            if self.openai_api_key:
                direct_openai_models = {
                    "gpt-4o-direct": ModelInfo(
                        id="gpt-4o",
                        name="GPT-4o (Direct API)",
                        provider=ModelProvider.OPENAI,
                        context_length=128000,
                        cost_per_1k_tokens=15.0,  # Direct OpenAI pricing
                        capabilities=["text", "vision", "function_calling", "json_mode"],
                        max_output_tokens=4096,
                        description="Latest GPT-4 with vision - Direct OpenAI API",
                        best_for=["complex_analysis", "vision", "function_calling", "large_documents"],
                        enterprise_cost=12.0,  # Negotiated enterprise rate
                        pricing_tier="enterprise"
                    ),
                    "gpt-4o-mini-direct": ModelInfo(
                        id="gpt-4o-mini",
                        name="GPT-4o Mini (Direct API)",
                        provider=ModelProvider.OPENAI,
                        context_length=128000,
                        cost_per_1k_tokens=0.60,  # Direct OpenAI pricing
                        capabilities=["text", "vision", "function_calling", "json_mode"],
                        max_output_tokens=16384,
                        description="Fast and affordable GPT-4 - Direct OpenAI API",
                        best_for=["general_purpose", "fast_responses", "cost_effective"],
                        enterprise_cost=0.40,  # Negotiated enterprise rate
                        pricing_tier="enterprise"
                    ),
                }
                models.update(direct_openai_models)
            
            # Direct Anthropic Models
            if self.anthropic_api_key:
                direct_anthropic_models = {
                    "claude-3.5-sonnet-direct": ModelInfo(
                        id="claude-3-5-sonnet-20241022",
                        name="Claude 3.5 Sonnet (Direct API)",
                        provider=ModelProvider.ANTHROPIC,
                        context_length=200000,
                        cost_per_1k_tokens=15.0,  # Direct Anthropic pricing
                        capabilities=["text", "vision", "function_calling", "json_mode"],
                        max_output_tokens=8192,
                        description="Excellent for analysis and reasoning - Direct Anthropic API",
                        best_for=["document_analysis", "reasoning", "coding", "large_context"],
                        enterprise_cost=10.0,  # Negotiated enterprise rate
                        pricing_tier="enterprise"
                    ),
                    "claude-3-haiku-direct": ModelInfo(
                        id="claude-3-haiku-20240307",
                        name="Claude 3 Haiku (Direct API)",
                        provider=ModelProvider.ANTHROPIC,
                        context_length=200000,
                        cost_per_1k_tokens=1.25,  # Direct Anthropic pricing
                        capabilities=["text", "vision"],
                        max_output_tokens=4096,
                        description="Fast and cost-effective - Direct Anthropic API",
                        best_for=["quick_summaries", "simple_analysis", "cost_effective"],
                        enterprise_cost=0.80,  # Negotiated enterprise rate
                        pricing_tier="enterprise"
                    ),
                }
                models.update(direct_anthropic_models)
        
        # Local Ollama Models (always available as fallback)
        ollama_models = {
            "llama3.2-local": ModelInfo(
                id="llama3.2:1b",
                name="Llama 3.2 1B (Local)",
                provider=ModelProvider.OLLAMA,
                context_length=2048,
                cost_per_1k_tokens=0.0,  # Free local model
                capabilities=["text"],
                max_output_tokens=2048,
                description="Local Ollama model - always available",
                best_for=["fallback", "offline", "privacy", "free"]
            )
        }
        models.update(ollama_models)
        
        return models
    
    def calculate_complexity_score(self, request: Any, file_info: List[Dict] = None) -> float:
        """Enhanced complexity calculation"""
        complexity_score = 0.0
        
        # Message complexity
        total_message_length = sum(len(msg.content) for msg in request.messages)
        if total_message_length > 5000:
            complexity_score += 40
        elif total_message_length > 2000:
            complexity_score += 25
        elif total_message_length > 500:
            complexity_score += 10
        
        # File complexity
        if file_info:
            total_files = len(file_info)
            total_file_size = sum(info.get("size", 0) for info in file_info)
            
            # Number of files
            if total_files > 10:
                complexity_score += 30
            elif total_files > 5:
                complexity_score += 20
            elif total_files > 1:
                complexity_score += 10
            
            # File size (in MB)
            total_size_mb = total_file_size / (1024 * 1024)
            if total_size_mb > 50:
                complexity_score += 35
            elif total_size_mb > 20:
                complexity_score += 25
            elif total_size_mb > 5:
                complexity_score += 15
            
            # File types
            file_types = set(info.get("file_type", "unknown") for info in file_info)
            if "pdf" in file_types and total_size_mb > 10:
                complexity_score += 20  # Large PDFs are complex
            if "audio" in file_types:
                complexity_score += 15  # Audio processing is complex
            if len(file_types) > 3:
                complexity_score += 10  # Multiple file types
        
        # Content analysis keywords
        content = " ".join(msg.content.lower() for msg in request.messages)
        analysis_keywords = [
            "analyze", "compare", "detailed", "comprehensive", "complex",
            "summary", "report", "research", "data", "statistics"
        ]
        
        keyword_matches = sum(1 for keyword in analysis_keywords if keyword in content)
        complexity_score += keyword_matches * 5
        
        # Special request types
        if any(word in content for word in ["financial", "legal", "medical", "technical"]):
            complexity_score += 15
        
        return min(complexity_score, 100.0)  # Cap at 100
    
    def select_best_model(self, request: Any, file_info: List[Dict] = None, user_preferences: Dict = None) -> str:
        """Select the best model based on complexity, capabilities, and cost"""
        
        # If user explicitly specified a model
        if hasattr(request, 'model') and request.model and request.model != "auto":
            if request.model in self.models:
                return request.model
            # Try to map legacy model names
            legacy_mapping = {
                "llama3.2-local": "llama3.2-local",
                "gpt-4": "gpt-4o",
                "gpt-4-turbo": "gpt-4o",
                "claude-3-sonnet": "claude-3.5-sonnet"
            }
            if request.model in legacy_mapping:
                return legacy_mapping[request.model]
        
        # Calculate complexity
        complexity_score = self.calculate_complexity_score(request, file_info)
        
        # Determine required capabilities
        required_capabilities = ["text"]
        if file_info:
            file_types = set(info.get("file_type", "") for info in file_info)
            if any(ft in ["jpg", "jpeg", "png", "gif", "webp", "bmp"] for ft in file_types):
                required_capabilities.append("vision")
        
        # Get user preferences
        preferences = user_preferences or {}
        max_cost = preferences.get("max_cost_per_1k", 10.0)
        prefer_fast = preferences.get("prefer_fast", False)
        prefer_cheap = preferences.get("prefer_cheap", False)
        
        # Filter models by capabilities and availability
        suitable_models = []
        for model_id, model in self.models.items():
            # Check if model has required capabilities
            if not all(cap in model.capabilities for cap in required_capabilities):
                continue
            
            # Check cost constraints
            if model.cost_per_1k_tokens > max_cost:
                continue
            
            # Check if provider is available
            if model.provider == ModelProvider.OPENROUTER and not self.openrouter_api_key:
                continue
            elif model.provider == ModelProvider.OPENAI and not self.openai_api_key:
                continue
            elif model.provider == ModelProvider.ANTHROPIC and not self.anthropic_api_key:
                continue
            
            suitable_models.append((model_id, model))
        
        if not suitable_models:
            logger.warning("No suitable models found, falling back to local model")
            return "llama3.2-local"
        
        # Score models based on complexity and preferences
        scored_models = []
        for model_id, model in suitable_models:
            score = 0.0
            
            # Complexity-based scoring
            if complexity_score >= 70:
                # High complexity - prefer powerful models
                if "gpt-4o" in model_id or "claude-3.5-sonnet" in model_id or "405b" in model_id:
                    score += 50
                elif "gpt-4o-mini" in model_id or "claude-3-haiku" in model_id or "70b" in model_id:
                    score += 30
            elif complexity_score >= 40:
                # Medium complexity - balanced models
                if "gpt-4o-mini" in model_id or "claude-3-haiku" in model_id or "70b" in model_id:
                    score += 40
                elif "gpt-3.5-turbo" in model_id or "8b" in model_id:
                    score += 30
            else:
                # Low complexity - prefer fast/cheap models
                if "gpt-3.5-turbo" in model_id or "8b" in model_id or "local" in model_id:
                    score += 40
            
            # Preference adjustments
            if prefer_fast:
                if model.cost_per_1k_tokens < 1.0:  # Cheaper models are usually faster
                    score += 20
            
            if prefer_cheap:
                # Inverse cost scoring (cheaper = higher score)
                score += max(0, 10 - model.cost_per_1k_tokens) * 5
            
            # Provider preference (OpenRouter > Ollama for most cases)
            if model.provider == ModelProvider.OPENROUTER:
                score += 10
            elif model.provider == ModelProvider.OLLAMA:
                score += 5  # Local models get some bonus for privacy/availability
            
            # Context length bonus for large files
            if file_info and len(file_info) > 5:
                if model.context_length > 100000:
                    score += 15
                elif model.context_length > 32000:
                    score += 10
            
            scored_models.append((score, model_id, model))
        
        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[0], reverse=True)
        
        # Select best model
        best_score, best_model_id, best_model = scored_models[0]
        
        logger.info(f"Model selection: complexity={complexity_score:.1f}, selected={best_model_id} (score={best_score:.1f})")
        
        return best_model_id
    
    async def make_api_call(self, model_id: str, messages: List[Dict], stream: bool = False, **kwargs) -> Any:
        """Make API call to the selected model provider"""
        
        if model_id not in self.models:
            raise ValueError(f"Unknown model: {model_id}")
        
        model = self.models[model_id]
        
        if model.provider == ModelProvider.OPENROUTER:
            return await self._call_openrouter(model, messages, stream, **kwargs)
        elif model.provider == ModelProvider.OLLAMA:
            return await self._call_ollama(model, messages, stream, **kwargs)
        elif model.provider == ModelProvider.OPENAI:
            return await self._call_openai_direct(model, messages, stream, **kwargs)
        elif model.provider == ModelProvider.ANTHROPIC:
            return await self._call_anthropic_direct(model, messages, stream, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {model.provider}")
    
    async def _call_openrouter(self, model: ModelInfo, messages: List[Dict], stream: bool = False, **kwargs) -> Any:
        """Call OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "https://autopicker.ai",
            "X-Title": "Autopicker Platform",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model.id,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                return self._stream_openrouter_response(client, headers, payload)
            else:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
    
    async def _stream_openrouter_response(self, client: httpx.AsyncClient, headers: Dict, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream response from OpenRouter"""
        async with client.stream(
            "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.strip():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content = delta["content"]
                                    if content:
                                        yield json.dumps({
                                            "id": data.get("id", "chatcmpl-autopicker"),
                                            "object": "chat.completion.chunk",
                                            "created": int(datetime.now().timestamp()),
                                            "model": payload["model"],
                                            "choices": [{
                                                "index": 0,
                                                "delta": {"content": content},
                                                "finish_reason": None
                                            }]
                                        })
                        except json.JSONDecodeError:
                            continue
    
    async def _call_ollama(self, model: ModelInfo, messages: List[Dict], stream: bool = False, **kwargs) -> Any:
        """Call local Ollama API"""
        payload = {
            "model": model.id,
            "messages": messages,
            "stream": stream
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                return self._stream_ollama_response(client, payload)
            else:
                response = await client.post(
                    "http://localhost:11434/api/chat",
                    json=payload
                )
                
                if response.status_code == 200:
                    ollama_response = response.json()
                    # Convert Ollama response to OpenAI format
                    return {
                        "id": f"chatcmpl-{datetime.now().timestamp()}",
                        "object": "chat.completion",
                        "created": int(datetime.now().timestamp()),
                        "model": model.id,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": ollama_response.get("message", {}).get("content", "")
                            },
                            "finish_reason": "stop"
                        }],
                        "usage": {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0
                        }
                    }
                else:
                    raise httpx.HTTPError(f"Ollama API error: {response.status_code}")
    
    async def _stream_ollama_response(self, client: httpx.AsyncClient, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream response from Ollama"""
        async with client.stream("POST", "http://localhost:11434/api/chat", json=payload) as response:
            if response.status_code == 200:
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            ollama_response = json.loads(line)
                            
                            if "message" in ollama_response and "content" in ollama_response["message"]:
                                content = ollama_response["message"]["content"]
                                if content:
                                    yield json.dumps({
                                        "id": f"chatcmpl-{datetime.now().timestamp()}",
                                        "object": "chat.completion.chunk",
                                        "created": int(datetime.now().timestamp()),
                                        "model": payload["model"],
                                        "choices": [{
                                            "index": 0,
                                            "delta": {"content": content},
                                            "finish_reason": None
                                        }]
                                    })
                            
                            if ollama_response.get("done", False):
                                yield json.dumps({
                                    "id": f"chatcmpl-{datetime.now().timestamp()}",  
                                    "object": "chat.completion.chunk",
                                    "created": int(datetime.now().timestamp()),
                                    "model": payload["model"],
                                    "choices": [{
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": "stop"
                                    }]
                                })
                                break
                                
                        except json.JSONDecodeError:
                            continue
    
    def get_available_models(self) -> List[Dict]:
        """Get list of available models"""
        models_list = []
        
        for model_id, model in self.models.items():
            # Check if provider is available
            available = True
            if model.provider == ModelProvider.OPENROUTER and not self.openrouter_api_key:
                available = False
            
            models_list.append({
                "id": model_id,
                "name": model.name,
                "provider": model.provider.value,
                "context_length": model.context_length,
                "cost_per_1k_tokens": model.cost_per_1k_tokens,
                "capabilities": model.capabilities,
                "description": model.description,
                "available": available,
                "best_for": model.best_for
            })
        
        return sorted(models_list, key=lambda x: (not x["available"], x["cost_per_1k_tokens"]))
    
    def get_model_info(self, model_id: str) -> Dict:
        """Get detailed information about a specific model"""
        if model_id not in self.models:
            return {"error": f"Model {model_id} not found"}
        
        model = self.models[model_id]
        available = True
        
        if model.provider == ModelProvider.OPENROUTER and not self.openrouter_api_key:
            available = False
        elif model.provider == ModelProvider.OPENAI and not self.openai_api_key:
            available = False
        elif model.provider == ModelProvider.ANTHROPIC and not self.anthropic_api_key:
            available = False
        
        return {
            "id": model_id,
            "name": model.name,
            "provider": model.provider.value,
            "context_length": model.context_length,
            "cost_per_1k_tokens": model.cost_per_1k_tokens,
            "capabilities": model.capabilities,
            "max_output_tokens": model.max_output_tokens,
            "description": model.description,
            "best_for": model.best_for,
            "available": available,
            "pricing_tier": model.pricing_tier,
            "enterprise_cost": model.enterprise_cost
        }
    
    async def _call_openai_direct(self, model: ModelInfo, messages: List[Dict], stream: bool = False, **kwargs) -> Any:
        """Call OpenAI API directly"""
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model.id,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        # Track usage for billing
        self.track_usage(model.id, len(str(messages)), model.cost_per_1k_tokens)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                return self._stream_openai_direct_response(client, headers, payload)
            else:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
    
    async def _stream_openai_direct_response(self, client: httpx.AsyncClient, headers: Dict, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI direct API"""
        async with client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.strip():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield json.dumps(data)
                        except json.JSONDecodeError:
                            continue
    
    async def _call_anthropic_direct(self, model: ModelInfo, messages: List[Dict], stream: bool = False, **kwargs) -> Any:
        """Call Anthropic API directly"""
        headers = {
            "x-api-key": self.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert OpenAI format to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": model.id,
            "messages": anthropic_messages,
            "max_tokens": model.max_output_tokens,
            "stream": stream,
            **kwargs
        }
        
        if system_message:
            payload["system"] = system_message
        
        # Track usage for billing
        self.track_usage(model.id, len(str(messages)), model.cost_per_1k_tokens)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                return self._stream_anthropic_direct_response(client, headers, payload)
            else:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                anthropic_response = response.json()
                
                # Convert Anthropic format back to OpenAI format
                return {
                    "id": f"chatcmpl-{datetime.now().timestamp()}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": model.id,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": anthropic_response.get("content", [{}])[0].get("text", "")
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": anthropic_response.get("usage", {}).get("input_tokens", 0),
                        "completion_tokens": anthropic_response.get("usage", {}).get("output_tokens", 0),
                        "total_tokens": anthropic_response.get("usage", {}).get("input_tokens", 0) + anthropic_response.get("usage", {}).get("output_tokens", 0)
                    }
                }
    
    async def _stream_anthropic_direct_response(self, client: httpx.AsyncClient, headers: Dict, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream response from Anthropic direct API"""
        async with client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.strip():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta":
                                content = data.get("delta", {}).get("text", "")
                                if content:
                                    # Convert to OpenAI format
                                    yield json.dumps({
                                        "id": f"chatcmpl-{datetime.now().timestamp()}",
                                        "object": "chat.completion.chunk",
                                        "created": int(datetime.now().timestamp()),
                                        "model": payload["model"],
                                        "choices": [{
                                            "index": 0,
                                            "delta": {"content": content},
                                            "finish_reason": None
                                        }]
                                    })
                        except json.JSONDecodeError:
                            continue
    
    def track_usage(self, model_id: str, input_tokens: int, cost_per_1k: float):
        """Track usage for Stripe billing"""
        usage_event = {
            "timestamp": datetime.now().isoformat(),
            "model_id": model_id,
            "input_tokens": input_tokens,
            "cost_per_1k": cost_per_1k,
            "estimated_cost": (input_tokens / 1000) * cost_per_1k
        }
        
        self.billing_events.append(usage_event)
        
        # Update running stats
        if model_id not in self.usage_stats:
            self.usage_stats[model_id] = {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0
            }
        
        self.usage_stats[model_id]["total_requests"] += 1
        self.usage_stats[model_id]["total_tokens"] += input_tokens
        self.usage_stats[model_id]["total_cost"] += usage_event["estimated_cost"]
        
        logger.info(f"Usage tracked: {model_id} - {input_tokens} tokens - ${usage_event['estimated_cost']:.4f}")
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics for billing"""
        return {
            "usage_by_model": self.usage_stats,
            "recent_events": self.billing_events[-100:],  # Last 100 events
            "total_cost": sum(stats["total_cost"] for stats in self.usage_stats.values()),
            "total_requests": sum(stats["total_requests"] for stats in self.usage_stats.values()),
            "total_tokens": sum(stats["total_tokens"] for stats in self.usage_stats.values())
        }

# Global instance
enhanced_router = EnhancedModelRouter()