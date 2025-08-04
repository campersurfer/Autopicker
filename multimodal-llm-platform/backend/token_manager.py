#!/usr/bin/env python3
"""
Token Management Module for Multimodal LLM Platform
Handles token counting, chunking, and context window management
"""

import tiktoken
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import re
import math

logger = logging.getLogger("autopicker.token_manager")

class ChunkingStrategy(Enum):
    """Chunking strategies for different content types"""
    SEMANTIC = "semantic"  # Split by sentences/paragraphs
    SLIDING_WINDOW = "sliding_window"  # Overlapping chunks
    DOCUMENT_SECTIONS = "document_sections"  # Split by headers/sections
    UNIFORM = "uniform"  # Fixed-size chunks

@dataclass
class TokenBudget:
    """Token budget allocation for different parts of the request"""
    max_context: int
    system_prompt: int = 500
    user_prompt: int = 1000
    web_search: int = 5000
    file_content: int = 0  # Calculated dynamically
    response_buffer: int = 4000
    
    def __post_init__(self):
        """Calculate available tokens for file content"""
        used = self.system_prompt + self.user_prompt + self.web_search + self.response_buffer
        self.file_content = max(0, self.max_context - used)

@dataclass
class ChunkInfo:
    """Information about a content chunk"""
    content: str
    tokens: int
    chunk_index: int
    total_chunks: int
    source_file: str
    chunk_type: str
    metadata: Dict[str, Any]

class TokenCounter:
    """Accurate token counting for different models"""
    
    def __init__(self):
        self.encoders = {}
        self._load_encoders()
    
    def _load_encoders(self):
        """Load tokenizer encodings for different model families"""
        try:
            # GPT models
            self.encoders['gpt-4'] = tiktoken.encoding_for_model("gpt-4")
            self.encoders['gpt-3.5'] = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except Exception as e:
            logger.warning(f"Could not load GPT encoders: {e}")
            # Fallback to cl100k_base for most modern models
            try:
                self.encoders['default'] = tiktoken.get_encoding("cl100k_base")
            except Exception as e2:
                logger.error(f"Could not load fallback encoder: {e2}")
    
    def count_tokens(self, text: str, model_family: str = "default") -> int:
        """Count tokens for given text and model family"""
        if not text:
            return 0
            
        # Choose appropriate encoder
        encoder_key = "default"
        if "gpt-4" in model_family.lower():
            encoder_key = "gpt-4"
        elif "gpt-3.5" in model_family.lower():
            encoder_key = "gpt-3.5"
        
        encoder = self.encoders.get(encoder_key, self.encoders.get("default"))
        if not encoder:
            # Rough estimation: ~4 characters per token
            return len(text) // 4
        
        try:
            return len(encoder.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using rough estimation")
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict[str, str]], model_family: str = "default") -> int:
        """Count tokens for a list of messages (OpenAI format)"""
        total_tokens = 0
        
        for message in messages:
            # Add tokens for message structure
            total_tokens += 4  # message overhead
            for key, value in message.items():
                total_tokens += self.count_tokens(str(value), model_family)
                if key == "name":
                    total_tokens += -1  # name is priced differently
        
        total_tokens += 2  # assistant reply priming
        return total_tokens

class ContentChunker:
    """Intelligent content chunking for large documents"""
    
    def __init__(self, token_counter: TokenCounter):
        self.token_counter = token_counter
    
    def chunk_content(
        self, 
        content: str, 
        max_tokens: int, 
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        overlap_tokens: int = 200,
        source_file: str = "unknown",
        model_family: str = "default"
    ) -> List[ChunkInfo]:
        """Chunk content using specified strategy"""
        
        if self.token_counter.count_tokens(content, model_family) <= max_tokens:
            return [ChunkInfo(
                content=content,
                tokens=self.token_counter.count_tokens(content, model_family),
                chunk_index=0,
                total_chunks=1,
                source_file=source_file,
                chunk_type=strategy.value,
                metadata={"original_length": len(content)}
            )]
        
        if strategy == ChunkingStrategy.SEMANTIC:
            return self._chunk_semantic(content, max_tokens, overlap_tokens, source_file, model_family)
        elif strategy == ChunkingStrategy.SLIDING_WINDOW:
            return self._chunk_sliding_window(content, max_tokens, overlap_tokens, source_file, model_family)
        elif strategy == ChunkingStrategy.DOCUMENT_SECTIONS:
            return self._chunk_by_sections(content, max_tokens, overlap_tokens, source_file, model_family)
        else:  # UNIFORM
            return self._chunk_uniform(content, max_tokens, overlap_tokens, source_file, model_family)
    
    def _chunk_semantic(self, content: str, max_tokens: int, overlap_tokens: int, source_file: str, model_family: str) -> List[ChunkInfo]:
        """Chunk by sentences and paragraphs (semantic boundaries)"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self.token_counter.count_tokens(paragraph, model_family)
            
            # If single paragraph exceeds max tokens, split by sentences
            if paragraph_tokens > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0
                
                # Split large paragraph by sentences
                sentences = re.split(r'[.!?]+\s+', paragraph)
                for sentence in sentences:
                    sentence_tokens = self.token_counter.count_tokens(sentence, model_family)
                    
                    if current_tokens + sentence_tokens > max_tokens and current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                        current_tokens = sentence_tokens
                    else:
                        current_chunk += (" " + sentence if current_chunk else sentence)
                        current_tokens += sentence_tokens
            
            # Check if adding this paragraph would exceed limit
            elif current_tokens + paragraph_tokens > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
                current_tokens = paragraph_tokens
            else:
                current_chunk += ("\n\n" + paragraph if current_chunk else paragraph)
                current_tokens += paragraph_tokens
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return self._create_chunk_infos(chunks, source_file, ChunkingStrategy.SEMANTIC.value, model_family)
    
    def _chunk_sliding_window(self, content: str, max_tokens: int, overlap_tokens: int, source_file: str, model_family: str) -> List[ChunkInfo]:
        """Create overlapping chunks with sliding window"""
        chunks = []
        words = content.split()
        
        # Estimate words per token (rough approximation)
        total_tokens = self.token_counter.count_tokens(content, model_family)
        words_per_token = len(words) / total_tokens if total_tokens > 0 else 0.75
        
        chunk_words = int(max_tokens * words_per_token)
        overlap_words = int(overlap_tokens * words_per_token)
        
        i = 0
        while i < len(words):
            end_idx = min(i + chunk_words, len(words))
            chunk_text = " ".join(words[i:end_idx])
            chunks.append(chunk_text)
            
            if end_idx >= len(words):
                break
                
            i += chunk_words - overlap_words
        
        return self._create_chunk_infos(chunks, source_file, ChunkingStrategy.SLIDING_WINDOW.value, model_family)
    
    def _chunk_by_sections(self, content: str, max_tokens: int, overlap_tokens: int, source_file: str, model_family: str) -> List[ChunkInfo]:
        """Chunk by document sections (headers, etc.)"""
        # Look for markdown headers or numbered sections
        header_pattern = r'^(#{1,6}\s+.+|^\d+\.?\s+.+|^[A-Z][A-Z\s]+:)$'
        lines = content.split('\n')
        
        sections = []
        current_section = []
        
        for line in lines:
            if re.match(header_pattern, line.strip(), re.MULTILINE):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        # Now chunk each section if needed
        chunks = []
        for section in sections:
            section_tokens = self.token_counter.count_tokens(section, model_family)
            if section_tokens <= max_tokens:
                chunks.append(section)
            else:
                # Further chunk large sections semantically
                sub_chunks = self._chunk_semantic(section, max_tokens, overlap_tokens, source_file, model_family)
                chunks.extend([chunk.content for chunk in sub_chunks])
        
        return self._create_chunk_infos(chunks, source_file, ChunkingStrategy.DOCUMENT_SECTIONS.value, model_family)
    
    def _chunk_uniform(self, content: str, max_tokens: int, overlap_tokens: int, source_file: str, model_family: str) -> List[ChunkInfo]:
        """Create uniform-sized chunks"""
        chunks = []
        words = content.split()
        
        # Estimate words per token
        total_tokens = self.token_counter.count_tokens(content, model_family)
        words_per_token = len(words) / total_tokens if total_tokens > 0 else 0.75
        
        chunk_words = int(max_tokens * words_per_token)
        
        for i in range(0, len(words), chunk_words):
            chunk_text = " ".join(words[i:i + chunk_words])
            chunks.append(chunk_text)
        
        return self._create_chunk_infos(chunks, source_file, ChunkingStrategy.UNIFORM.value, model_family)
    
    def _create_chunk_infos(self, chunks: List[str], source_file: str, chunk_type: str, model_family: str) -> List[ChunkInfo]:
        """Create ChunkInfo objects from text chunks"""
        chunk_infos = []
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            chunk_infos.append(ChunkInfo(
                content=chunk,
                tokens=self.token_counter.count_tokens(chunk, model_family),
                chunk_index=i,
                total_chunks=total_chunks,
                source_file=source_file,
                chunk_type=chunk_type,
                metadata={
                    "character_count": len(chunk),
                    "word_count": len(chunk.split())
                }
            ))
        
        return chunk_infos

class TokenManager:
    """Main token management orchestrator"""
    
    def __init__(self):
        self.token_counter = TokenCounter()
        self.chunker = ContentChunker(self.token_counter)
        
        # Model context windows from the enhanced router
        self.model_contexts = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-3.5-turbo": 16385,
            "claude-3.5-sonnet": 200000,
            "claude-3-haiku": 200000,
            "gemini-pro": 32768,
            "llama-3.1-405b": 32768,
            "llama-3.1-70b": 32768,
            "llama-3.1-8b": 32768,
        }
    
    def get_model_context_window(self, model_id: str) -> int:
        """Get context window for a model"""
        # Extract base model name
        for model_name, context in self.model_contexts.items():
            if model_name in model_id.lower():
                return context
        
        # Default fallback
        return 4096
    
    def create_token_budget(self, model_id: str, custom_allocations: Optional[Dict[str, int]] = None) -> TokenBudget:
        """Create a token budget for a specific model"""
        max_context = self.get_model_context_window(model_id)
        
        budget = TokenBudget(max_context=max_context)
        
        if custom_allocations:
            for key, value in custom_allocations.items():
                if hasattr(budget, key):
                    setattr(budget, key, value)
            # Recalculate file content allocation
            budget.__post_init__()
        
        return budget
    
    def analyze_content_for_chunking(
        self, 
        file_contents: List[Dict[str, Any]], 
        model_id: str,
        web_search_content: str = "",
        user_prompt: str = ""
    ) -> Dict[str, Any]:
        """Analyze content and determine if chunking is needed"""
        
        budget = self.create_token_budget(model_id)
        model_family = self._get_model_family(model_id)
        
        # Count existing tokens
        user_tokens = self.token_counter.count_tokens(user_prompt, model_family)
        web_tokens = self.token_counter.count_tokens(web_search_content, model_family)
        
        file_tokens = 0
        file_analysis = []
        
        for file_content in file_contents:
            content = str(file_content.get('content', ''))
            filename = file_content.get('filename', 'unknown')
            tokens = self.token_counter.count_tokens(content, model_family)
            
            file_analysis.append({
                'filename': filename,
                'tokens': tokens,
                'characters': len(content),
                'needs_chunking': tokens > budget.file_content // len(file_contents)
            })
            
            file_tokens += tokens
        
        total_tokens = user_tokens + web_tokens + file_tokens + budget.system_prompt + budget.response_buffer
        
        return {
            'total_estimated_tokens': total_tokens,
            'budget': budget,
            'exceeds_limit': total_tokens > budget.max_context,
            'user_prompt_tokens': user_tokens,
            'web_search_tokens': web_tokens,
            'file_tokens': file_tokens,
            'file_analysis': file_analysis,
            'chunking_recommended': total_tokens > budget.max_context * 0.8,  # 80% threshold
            'model_family': model_family
        }
    
    def chunk_files_for_model(
        self,
        file_contents: List[Dict[str, Any]],
        model_id: str,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    ) -> List[List[ChunkInfo]]:
        """Chunk multiple files for a specific model"""
        
        budget = self.create_token_budget(model_id)
        model_family = self._get_model_family(model_id)
        
        # Calculate tokens per file (distribute evenly)
        tokens_per_file = budget.file_content // len(file_contents) if file_contents else budget.file_content
        
        chunked_files = []
        
        for file_content in file_contents:
            content = str(file_content.get('content', ''))
            filename = file_content.get('filename', 'unknown')
            
            chunks = self.chunker.chunk_content(
                content=content,
                max_tokens=tokens_per_file,
                strategy=strategy,
                source_file=filename,
                model_family=model_family
            )
            
            chunked_files.append(chunks)
        
        return chunked_files
    
    def _get_model_family(self, model_id: str) -> str:
        """Determine model family for token counting"""
        model_lower = model_id.lower()
        
        if "gpt-4" in model_lower:
            return "gpt-4"
        elif "gpt-3.5" in model_lower:
            return "gpt-3.5"
        elif "claude" in model_lower:
            return "default"  # Use default encoder for Claude
        elif "gemini" in model_lower:
            return "default"
        elif "llama" in model_lower:
            return "default"
        else:
            return "default"
    
    def estimate_response_cost(self, token_count: int, model_id: str) -> float:
        """Estimate cost for token usage (if cost tracking is needed)"""
        # This could be enhanced with actual model pricing
        # For now, return a simple estimation
        
        cost_per_1k = {
            "gpt-4o": 5.0,
            "gpt-4o-mini": 0.15,
            "gpt-3.5-turbo": 0.5,
            "claude-3.5-sonnet": 3.0,
            "claude-3-haiku": 0.25,
            "gemini-pro": 0.5,
            "llama-3.1-405b": 2.7,
            "llama-3.1-70b": 0.59,
            "llama-3.1-8b": 0.055,
        }
        
        for model_name, cost in cost_per_1k.items():
            if model_name in model_id.lower():
                return (token_count / 1000) * cost
        
        return (token_count / 1000) * 1.0  # Default cost

# Global instances
token_manager = TokenManager()