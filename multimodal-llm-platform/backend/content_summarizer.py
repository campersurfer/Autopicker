#!/usr/bin/env python3
"""
Content Summarization Module for Token Optimization
Intelligently summarizes and compresses content to fit within token limits
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

logger = logging.getLogger("autopicker.content_summarizer")

class SummarizationStrategy(Enum):
    """Different summarization strategies"""
    EXTRACTIVE = "extractive"  # Extract key sentences
    STRUCTURAL = "structural"  # Preserve structure, compress content
    KEYWORD_FOCUSED = "keyword_focused"  # Focus on keywords and topics
    HYBRID = "hybrid"  # Combination of strategies

@dataclass
class SummaryResult:
    """Result of content summarization"""
    original_content: str
    summarized_content: str
    original_tokens: int
    summarized_tokens: int
    compression_ratio: float
    strategy_used: str
    key_points: List[str]
    metadata: Dict[str, Any]

class ContentSummarizer:
    """Intelligent content summarization for token optimization"""
    
    def __init__(self, token_counter):
        self.token_counter = token_counter
        
        # Common stopwords for filtering
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Importance indicators
        self.importance_indicators = {
            'high': ['important', 'critical', 'essential', 'key', 'main', 'primary', 
                    'significant', 'major', 'fundamental', 'core', 'vital', 'crucial'],
            'medium': ['notable', 'relevant', 'useful', 'valuable', 'interesting', 
                      'worth', 'consider', 'note', 'observe', 'mention'],
            'structural': ['first', 'second', 'third', 'finally', 'conclusion', 
                          'summary', 'overview', 'introduction', 'background']
        }
    
    def summarize_content(
        self,
        content: str,
        target_tokens: int,
        strategy: SummarizationStrategy = SummarizationStrategy.HYBRID,
        model_family: str = "default",
        context_keywords: Optional[List[str]] = None
    ) -> SummaryResult:
        """Summarize content to fit within target token limit"""
        
        original_tokens = self.token_counter.count_tokens(content, model_family)
        
        if original_tokens <= target_tokens:
            return SummaryResult(
                original_content=content,
                summarized_content=content,
                original_tokens=original_tokens,
                summarized_tokens=original_tokens,
                compression_ratio=1.0,
                strategy_used="none_needed",
                key_points=self._extract_key_points(content),
                metadata={"no_compression_needed": True}
            )
        
        # Apply summarization strategy
        if strategy == SummarizationStrategy.EXTRACTIVE:
            summarized = self._extractive_summarization(content, target_tokens, model_family, context_keywords)
        elif strategy == SummarizationStrategy.STRUCTURAL:
            summarized = self._structural_summarization(content, target_tokens, model_family)
        elif strategy == SummarizationStrategy.KEYWORD_FOCUSED:
            summarized = self._keyword_focused_summarization(content, target_tokens, model_family, context_keywords)
        else:  # HYBRID
            summarized = self._hybrid_summarization(content, target_tokens, model_family, context_keywords)
        
        summarized_tokens = self.token_counter.count_tokens(summarized, model_family)
        compression_ratio = summarized_tokens / original_tokens if original_tokens > 0 else 1.0
        
        return SummaryResult(
            original_content=content,
            summarized_content=summarized,
            original_tokens=original_tokens,
            summarized_tokens=summarized_tokens,
            compression_ratio=compression_ratio,
            strategy_used=strategy.value,
            key_points=self._extract_key_points(summarized),
            metadata={
                "target_tokens": target_tokens,
                "tokens_saved": original_tokens - summarized_tokens,
                "compression_percentage": round((1 - compression_ratio) * 100, 1)
            }
        )
    
    def _extractive_summarization(
        self, 
        content: str, 
        target_tokens: int, 
        model_family: str,
        context_keywords: Optional[List[str]] = None
    ) -> str:
        """Extract the most important sentences"""
        
        sentences = self._split_into_sentences(content)
        if not sentences:
            return content[:target_tokens * 4]  # Rough character limit fallback
        
        # Score sentences by importance
        scored_sentences = []
        for sentence in sentences:
            score = self._score_sentence_importance(sentence, context_keywords)
            tokens = self.token_counter.count_tokens(sentence, model_family)
            scored_sentences.append((sentence, score, tokens))
        
        # Sort by importance score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Select sentences until we hit token limit
        selected_sentences = []
        current_tokens = 0
        
        for sentence, score, tokens in scored_sentences:
            if current_tokens + tokens <= target_tokens:
                selected_sentences.append((sentence, score))
                current_tokens += tokens
            else:
                break
        
        # Sort selected sentences by original order
        original_order = []
        for sentence, _ in selected_sentences:
            try:
                idx = sentences.index(sentence)
                original_order.append((idx, sentence))
            except ValueError:
                continue
        
        original_order.sort(key=lambda x: x[0])
        
        return " ".join([sentence for _, sentence in original_order])
    
    def _structural_summarization(self, content: str, target_tokens: int, model_family: str) -> str:
        """Preserve document structure while compressing content"""
        
        # Identify sections/paragraphs
        paragraphs = content.split('\n\n')
        if len(paragraphs) == 1:
            paragraphs = content.split('\n')
        
        # Calculate target tokens per section
        target_per_section = target_tokens // len(paragraphs) if paragraphs else target_tokens
        
        compressed_sections = []
        remaining_tokens = target_tokens
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            para_tokens = self.token_counter.count_tokens(paragraph, model_family)
            
            if para_tokens <= target_per_section or remaining_tokens >= para_tokens:
                # Keep paragraph as is
                compressed_sections.append(paragraph)
                remaining_tokens -= para_tokens
            else:
                # Compress paragraph
                compressed = self._compress_paragraph(paragraph, min(target_per_section, remaining_tokens), model_family)
                compressed_sections.append(compressed)
                remaining_tokens -= self.token_counter.count_tokens(compressed, model_family)
            
            if remaining_tokens <= 0:
                break
        
        return '\n\n'.join(compressed_sections)
    
    def _keyword_focused_summarization(
        self, 
        content: str, 
        target_tokens: int, 
        model_family: str,
        context_keywords: Optional[List[str]] = None
    ) -> str:
        """Focus on content related to specific keywords"""
        
        if not context_keywords:
            # Extract keywords from content
            context_keywords = self._extract_keywords(content)
        
        sentences = self._split_into_sentences(content)
        keyword_sentences = []
        current_tokens = 0
        
        # Prioritize sentences containing keywords
        for sentence in sentences:
            sentence_keywords = sum(1 for keyword in context_keywords 
                                  if keyword.lower() in sentence.lower())
            
            if sentence_keywords > 0:
                tokens = self.token_counter.count_tokens(sentence, model_family)
                if current_tokens + tokens <= target_tokens:
                    keyword_sentences.append(sentence)
                    current_tokens += tokens
                else:
                    break
        
        # If we have remaining space, add other important sentences
        if current_tokens < target_tokens * 0.9:  # 90% threshold
            remaining_sentences = [s for s in sentences if s not in keyword_sentences]
            for sentence in remaining_sentences:
                tokens = self.token_counter.count_tokens(sentence, model_family)
                if current_tokens + tokens <= target_tokens:
                    keyword_sentences.append(sentence)
                    current_tokens += tokens
                else:
                    break
        
        return " ".join(keyword_sentences)
    
    def _hybrid_summarization(
        self, 
        content: str, 
        target_tokens: int, 
        model_family: str,
        context_keywords: Optional[List[str]] = None
    ) -> str:
        """Combine multiple summarization strategies"""
        
        # First, try keyword-focused if we have keywords
        if context_keywords:
            keyword_summary = self._keyword_focused_summarization(
                content, int(target_tokens * 0.7), model_family, context_keywords
            )
            remaining_tokens = target_tokens - self.token_counter.count_tokens(keyword_summary, model_family)
            
            if remaining_tokens > 0:
                # Add extractive content for remaining space
                remaining_content = content
                for sentence in self._split_into_sentences(keyword_summary):
                    remaining_content = remaining_content.replace(sentence, "")
                
                if remaining_content.strip():
                    extractive_summary = self._extractive_summarization(
                        remaining_content, remaining_tokens, model_family
                    )
                    return f"{keyword_summary} {extractive_summary}".strip()
            
            return keyword_summary
        
        else:
            # Use structural + extractive approach
            structural_summary = self._structural_summarization(
                content, int(target_tokens * 0.8), model_family
            )
            
            structural_tokens = self.token_counter.count_tokens(structural_summary, model_family)
            
            if structural_tokens < target_tokens:
                return structural_summary
            else:
                # Fall back to extractive
                return self._extractive_summarization(content, target_tokens, model_family)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - could be enhanced with NLTK/spaCy
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _score_sentence_importance(self, sentence: str, context_keywords: Optional[List[str]] = None) -> float:
        """Score a sentence's importance"""
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Length score (moderate length preferred)
        length_score = min(len(sentence) / 100, 1.0)  # Normalize to 0-1
        if 50 <= len(sentence) <= 200:  # Sweet spot
            length_score *= 1.5
        score += length_score
        
        # Importance keywords
        for level, keywords in self.importance_indicators.items():
            multiplier = 3.0 if level == 'high' else 2.0 if level == 'medium' else 1.5
            for keyword in keywords:
                if keyword in sentence_lower:
                    score += multiplier
        
        # Context keywords
        if context_keywords:
            for keyword in context_keywords:
                if keyword.lower() in sentence_lower:
                    score += 5.0
        
        # Numbers and specific information
        if re.search(r'\d+', sentence):
            score += 1.0
        
        # Questions (often important)
        if sentence.strip().endswith('?'):
            score += 2.0
        
        # First and last sentences often important
        return score
    
    def _compress_paragraph(self, paragraph: str, target_tokens: int, model_family: str) -> str:
        """Compress a single paragraph"""
        sentences = self._split_into_sentences(paragraph)
        if len(sentences) <= 1:
            # Single sentence - truncate if needed
            return paragraph[:target_tokens * 4]  # Rough character limit
        
        # Keep the most important sentences
        return self._extractive_summarization(paragraph, target_tokens, model_family)
    
    def _extract_keywords(self, content: str, max_keywords: int = 20) -> List[str]:
        """Extract important keywords from content"""
        # Simple keyword extraction - could be enhanced with TF-IDF or other methods
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        word_freq = {}
        
        for word in words:
            if word not in self.stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        sentences = self._split_into_sentences(content)
        key_points = []
        
        for sentence in sentences:
            # Look for sentences that seem like key points
            if any(indicator in sentence.lower() for indicator in self.importance_indicators['high']):
                key_points.append(sentence.strip())
            elif sentence.strip().endswith(':'):  # Likely a header or important statement
                key_points.append(sentence.strip())
            elif len(sentence.split()) <= 15 and any(char.isupper() for char in sentence):
                # Short sentences with capitals might be key points
                key_points.append(sentence.strip())
        
        return key_points[:10]  # Limit to top 10
    
    def batch_summarize_files(
        self,
        file_contents: List[Dict[str, Any]],
        total_target_tokens: int,
        model_family: str = "default",
        context_keywords: Optional[List[str]] = None
    ) -> List[SummaryResult]:
        """Summarize multiple files within a total token budget"""
        
        if not file_contents:
            return []
        
        # Calculate token budget per file
        tokens_per_file = total_target_tokens // len(file_contents)
        
        summaries = []
        remaining_budget = total_target_tokens
        
        for file_content in file_contents:
            content = str(file_content.get('content', ''))
            filename = file_content.get('filename', 'unknown')
            
            # Use remaining budget or per-file allocation, whichever is smaller
            target_tokens = min(tokens_per_file, remaining_budget)
            
            if target_tokens <= 0:
                # Create minimal summary if no budget left
                summary = SummaryResult(
                    original_content=content,
                    summarized_content=f"[File: {filename} - Content omitted due to token limits]",
                    original_tokens=self.token_counter.count_tokens(content, model_family),
                    summarized_tokens=20,
                    compression_ratio=0.01,
                    strategy_used="budget_exceeded",
                    key_points=[],
                    metadata={"budget_exceeded": True}
                )
            else:
                summary = self.summarize_content(
                    content=content,
                    target_tokens=target_tokens,
                    strategy=SummarizationStrategy.HYBRID,
                    model_family=model_family,
                    context_keywords=context_keywords
                )
                remaining_budget -= summary.summarized_tokens
            
            summaries.append(summary)
        
        return summaries

# Global instance
content_summarizer = None  # Initialized with token_counter when needed