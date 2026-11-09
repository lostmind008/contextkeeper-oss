#!/usr/bin/env python3
"""
Optimised Embedding Generation for ContextKeeper
Implements batch processing, caching, and connection pooling for Google GenAI embeddings
to significantly improve performance over single-request processing.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai.types import HttpOptions
import hashlib
import statistics

from performance_cache import EmbeddingCache

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingRequest:
    """Single embedding request with metadata"""
    text: str
    request_id: str
    metadata: Dict[str, Any]


@dataclass
class EmbeddingResponse:
    """Single embedding response with performance data"""
    request_id: str
    embedding: Optional[List[float]]
    error: Optional[str]
    processing_time_ms: float
    cached: bool


class OptimisedEmbeddingGenerator:
    """
    High-performance embedding generator with batch processing and intelligent caching
    
    Features:
    - Batch processing to reduce API calls
    - Intelligent caching with content hashing
    - Connection pooling for better throughput
    - Automatic retry with exponential backoff
    - Performance monitoring and optimisation
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-004",
        batch_size: int = 10,
        max_concurrent_batches: int = 3,
        cache_enabled: bool = True,
        cache_size_mb: int = 64
    ):
        self.api_key = api_key
        self.model = model
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        
        # Initialize clients pool for connection reuse
        self.clients = [
            genai.Client(
                api_key=api_key,
                http_options=HttpOptions(api_version="v1beta")
            )
            for _ in range(max_concurrent_batches)
        ]
        self.client_pool = iter(self.clients)
        
        # Initialize cache
        self.cache_enabled = cache_enabled
        self.cache = EmbeddingCache(cache_size_mb) if cache_enabled else None
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'cached_requests': 0,
            'batch_requests': 0,
            'total_api_calls': 0,
            'total_processing_time_ms': 0,
            'errors': 0
        }
        
        # Thread pool for concurrent batch processing
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_batches)

    def _get_client(self) -> genai.Client:
        """Get next client from pool (round-robin)"""
        try:
            return next(self.client_pool)
        except StopIteration:
            # Reset pool iterator
            self.client_pool = iter(self.clients)
            return next(self.client_pool)

    def _generate_content_hash(self, text: str) -> str:
        """Generate hash for content-based caching"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _should_batch_process(self, texts: List[str]) -> bool:
        """Determine if batch processing would be beneficial"""
        # Batch process if we have multiple texts and caching won't handle most of them
        if len(texts) < 2:
            return False
            
        if not self.cache_enabled:
            return len(texts) >= 2
        
        # Check cache hit rate prediction
        cached_count = 0
        for text in texts:
            if self.cache.get_cached_embedding(text, self.model) is not None:
                cached_count += 1
        
        uncached_count = len(texts) - cached_count
        return uncached_count >= 2

    async def generate_single_embedding(
        self,
        text: str,
        retry_count: int = 3
    ) -> EmbeddingResponse:
        """
        Generate embedding for single text with caching and retry logic
        
        Args:
            text: Text to embed
            retry_count: Number of retries on failure
            
        Returns:
            EmbeddingResponse with embedding or error
        """
        request_id = self._generate_content_hash(text)
        start_time = time.perf_counter()
        
        # Check cache first
        if self.cache_enabled:
            cached_embedding = self.cache.get_cached_embedding(text, self.model)
            if cached_embedding is not None:
                processing_time = (time.perf_counter() - start_time) * 1000
                self.stats['cached_requests'] += 1
                logger.debug(f"Cache hit for embedding request {request_id}")
                
                return EmbeddingResponse(
                    request_id=request_id,
                    embedding=cached_embedding,
                    error=None,
                    processing_time_ms=processing_time,
                    cached=True
                )
        
        # Generate embedding via API
        client = self._get_client()
        last_error = None
        
        for attempt in range(retry_count):
            try:
                try:
                    # Try with task_type parameter first (newer API)
                    response = client.models.embed_content(
                        model=self.model,
                        contents=text,
                        task_type="RETRIEVAL_DOCUMENT"
                    )
                except TypeError:
                    # Fallback for older API without task_type
                    response = client.models.embed_content(
                        model=self.model,
                        contents=text
                    )
                
                embedding = response.embeddings[0].values
                processing_time = (time.perf_counter() - start_time) * 1000
                
                # Cache the result
                if self.cache_enabled:
                    self.cache.cache_embedding(text, self.model, embedding)
                
                self.stats['total_api_calls'] += 1
                self.stats['total_processing_time_ms'] += processing_time
                
                return EmbeddingResponse(
                    request_id=request_id,
                    embedding=embedding,
                    error=None,
                    processing_time_ms=processing_time,
                    cached=False
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                
                if attempt < retry_count - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.stats['errors'] += 1
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return EmbeddingResponse(
            request_id=request_id,
            embedding=None,
            error=last_error,
            processing_time_ms=processing_time,
            cached=False
        )

    def _process_embedding_batch(
        self,
        batch_texts: List[str],
        batch_metadata: List[Dict[str, Any]]
    ) -> List[EmbeddingResponse]:
        """Process a batch of embeddings synchronously"""
        client = self._get_client()
        responses = []
        start_time = time.perf_counter()
        
        try:
            # Generate embeddings for entire batch
            try:
                # Try with task_type parameter first (newer API)
                response = client.models.embed_content(
                    model=self.model,
                    contents=batch_texts,
                    task_type="RETRIEVAL_DOCUMENT"
                )
            except TypeError:
                # Fallback for older API without task_type
                response = client.models.embed_content(
                    model=self.model,
                    contents=batch_texts
                )
            
            processing_time = (time.perf_counter() - start_time) * 1000
            avg_time_per_embedding = processing_time / len(batch_texts)
            
            # Process results
            for i, (text, metadata) in enumerate(zip(batch_texts, batch_metadata)):
                request_id = self._generate_content_hash(text)
                
                if i < len(response.embeddings):
                    embedding = response.embeddings[i].values
                    
                    # Cache the result
                    if self.cache_enabled:
                        self.cache.cache_embedding(text, self.model, embedding)
                    
                    responses.append(EmbeddingResponse(
                        request_id=request_id,
                        embedding=embedding,
                        error=None,
                        processing_time_ms=avg_time_per_embedding,
                        cached=False
                    ))
                else:
                    responses.append(EmbeddingResponse(
                        request_id=request_id,
                        embedding=None,
                        error="Missing embedding in batch response",
                        processing_time_ms=avg_time_per_embedding,
                        cached=False
                    ))
            
            self.stats['batch_requests'] += 1
            self.stats['total_api_calls'] += 1
            self.stats['total_processing_time_ms'] += processing_time
            
            logger.debug(f"Batch processed {len(batch_texts)} embeddings in {processing_time:.1f}ms")
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"Batch embedding failed: {error_msg}")
            
            # Return error responses for all items in batch
            for text, metadata in zip(batch_texts, batch_metadata):
                request_id = self._generate_content_hash(text)
                responses.append(EmbeddingResponse(
                    request_id=request_id,
                    embedding=None,
                    error=error_msg,
                    processing_time_ms=processing_time / len(batch_texts),
                    cached=False
                ))
            
            self.stats['errors'] += len(batch_texts)
        
        return responses

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[EmbeddingResponse]:
        """
        Generate embeddings for multiple texts with optimal batching strategy
        
        Args:
            texts: List of texts to embed
            metadata_list: Optional metadata for each text
            
        Returns:
            List of EmbeddingResponse objects
        """
        if not texts:
            return []
        
        if metadata_list is None:
            metadata_list = [{} for _ in texts]
        
        self.stats['total_requests'] += len(texts)
        
        # Check cache for all requests first
        responses = []
        uncached_texts = []
        uncached_metadata = []
        
        if self.cache_enabled:
            for text, metadata in zip(texts, metadata_list):
                cached_embedding = self.cache.get_cached_embedding(text, self.model)
                if cached_embedding is not None:
                    request_id = self._generate_content_hash(text)
                    responses.append(EmbeddingResponse(
                        request_id=request_id,
                        embedding=cached_embedding,
                        error=None,
                        processing_time_ms=0.1,  # Minimal cache access time
                        cached=True
                    ))
                    self.stats['cached_requests'] += 1
                else:
                    uncached_texts.append(text)
                    uncached_metadata.append(metadata)
        else:
            uncached_texts = texts
            uncached_metadata = metadata_list
        
        if not uncached_texts:
            logger.debug(f"All {len(texts)} embeddings served from cache")
            return responses
        
        # Determine processing strategy
        if len(uncached_texts) == 1:
            # Single request - use individual processing
            single_response = await self.generate_single_embedding(uncached_texts[0])
            responses.append(single_response)
        else:
            # Batch processing
            batches = []
            for i in range(0, len(uncached_texts), self.batch_size):
                batch_texts = uncached_texts[i:i + self.batch_size]
                batch_metadata = uncached_metadata[i:i + self.batch_size]
                batches.append((batch_texts, batch_metadata))
            
            # Process batches concurrently
            loop = asyncio.get_event_loop()
            futures = []
            
            for batch_texts, batch_metadata in batches:
                future = loop.run_in_executor(
                    self.executor,
                    self._process_embedding_batch,
                    batch_texts,
                    batch_metadata
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                batch_responses = await future
                responses.extend(batch_responses)
        
        logger.info(f"Generated embeddings: {len(responses)} total, "
                   f"{sum(1 for r in responses if r.cached)} cached, "
                   f"{sum(1 for r in responses if r.error)} errors")
        
        return responses

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        total_requests = self.stats['total_requests']
        if total_requests == 0:
            return {'message': 'No embedding requests processed yet'}
        
        cache_hit_rate = self.stats['cached_requests'] / total_requests
        avg_processing_time = (
            self.stats['total_processing_time_ms'] / 
            (total_requests - self.stats['cached_requests'])
            if total_requests > self.stats['cached_requests'] else 0
        )
        
        api_efficiency = (
            total_requests / self.stats['total_api_calls']
            if self.stats['total_api_calls'] > 0 else 0
        )
        
        stats = {
            'requests': {
                'total_requests': total_requests,
                'cached_requests': self.stats['cached_requests'],
                'api_requests': total_requests - self.stats['cached_requests'],
                'batch_requests': self.stats['batch_requests'],
                'errors': self.stats['errors']
            },
            'performance': {
                'cache_hit_rate': cache_hit_rate,
                'avg_processing_time_ms': avg_processing_time,
                'total_processing_time_ms': self.stats['total_processing_time_ms'],
                'api_efficiency_ratio': api_efficiency,  # requests per API call
                'error_rate': self.stats['errors'] / total_requests
            },
            'configuration': {
                'model': self.model,
                'batch_size': self.batch_size,
                'max_concurrent_batches': self.max_concurrent_batches,
                'cache_enabled': self.cache_enabled
            }
        }
        
        if self.cache_enabled:
            cache_stats = self.cache.get_detailed_stats()
            stats['cache_details'] = cache_stats
        
        return stats

    def optimise_configuration(self) -> Dict[str, Any]:
        """
        Analyse performance and suggest optimal configuration
        
        Returns:
            Dictionary with optimisation recommendations
        """
        stats = self.get_performance_stats()
        recommendations = []
        
        if 'performance' not in stats:
            return {'recommendations': ['Not enough data for optimisation analysis']}
        
        perf = stats['performance']
        
        # Cache analysis
        if perf['cache_hit_rate'] < 0.3:
            recommendations.append(
                f"Low cache hit rate ({perf['cache_hit_rate']:.1%}). "
                "Consider increasing cache size or TTL if processing similar content repeatedly."
            )
        elif perf['cache_hit_rate'] > 0.8:
            recommendations.append("Excellent cache performance! Consider reducing cache size if memory is constrained.")
        
        # API efficiency analysis
        if perf['api_efficiency_ratio'] < 2:
            recommendations.append(
                f"Low API efficiency ({perf['api_efficiency_ratio']:.1f} requests per API call). "
                "Consider increasing batch size for better throughput."
            )
        elif perf['api_efficiency_ratio'] > 8:
            recommendations.append("Excellent API efficiency through batching!")
        
        # Error rate analysis
        if perf['error_rate'] > 0.05:
            recommendations.append(
                f"High error rate ({perf['error_rate']:.1%}). "
                "Check API limits, network connectivity, or consider reducing batch size."
            )
        
        # Performance analysis
        if perf['avg_processing_time_ms'] > 1000:
            recommendations.append(
                f"Slow embedding generation ({perf['avg_processing_time_ms']:.0f}ms avg). "
                "Consider increasing concurrent batches or check network latency."
            )
        elif perf['avg_processing_time_ms'] < 200:
            recommendations.append("Excellent embedding performance!")
        
        # Configuration recommendations
        optimal_config = {
            'batch_size': self.batch_size,
            'max_concurrent_batches': self.max_concurrent_batches
        }
        
        # Suggest batch size adjustments
        if perf['error_rate'] > 0.1:
            optimal_config['batch_size'] = max(5, self.batch_size // 2)
            recommendations.append(f"Reduce batch size to {optimal_config['batch_size']} to reduce errors.")
        elif perf['error_rate'] < 0.01 and perf['avg_processing_time_ms'] < 500:
            optimal_config['batch_size'] = min(20, self.batch_size + 5)
            recommendations.append(f"Increase batch size to {optimal_config['batch_size']} for better efficiency.")
        
        return {
            'current_performance': stats,
            'recommendations': recommendations,
            'optimal_configuration': optimal_config
        }

    async def benchmark_performance(
        self,
        test_texts: List[str],
        runs: int = 3
    ) -> Dict[str, Any]:
        """
        Run performance benchmarks with test data
        
        Args:
            test_texts: List of test texts for benchmarking
            runs: Number of benchmark runs to average
            
        Returns:
            Benchmark results and performance analysis
        """
        logger.info(f"Starting embedding benchmark with {len(test_texts)} texts, {runs} runs")
        
        run_results = []
        
        for run in range(runs):
            # Clear cache for fair comparison (except first run)
            if run > 0 and self.cache_enabled:
                self.cache.clear()
            
            start_time = time.perf_counter()
            responses = await self.generate_embeddings_batch(test_texts)
            total_time = (time.perf_counter() - start_time) * 1000
            
            # Analyse results
            successful = sum(1 for r in responses if r.embedding is not None)
            cached = sum(1 for r in responses if r.cached)
            errors = sum(1 for r in responses if r.error is not None)
            
            run_results.append({
                'run': run + 1,
                'total_time_ms': total_time,
                'requests_per_second': len(test_texts) / (total_time / 1000),
                'successful': successful,
                'cached': cached,
                'errors': errors,
                'avg_time_per_request_ms': total_time / len(test_texts)
            })
            
            logger.info(f"Benchmark run {run + 1}: {total_time:.1f}ms total, "
                       f"{len(test_texts) / (total_time / 1000):.1f} req/sec")
        
        # Calculate overall statistics
        avg_total_time = statistics.mean([r['total_time_ms'] for r in run_results])
        avg_req_per_sec = statistics.mean([r['requests_per_second'] for r in run_results])
        avg_time_per_req = statistics.mean([r['avg_time_per_request_ms'] for r in run_results])
        
        return {
            'test_configuration': {
                'num_texts': len(test_texts),
                'benchmark_runs': runs,
                'batch_size': self.batch_size,
                'cache_enabled': self.cache_enabled
            },
            'individual_runs': run_results,
            'summary': {
                'avg_total_time_ms': avg_total_time,
                'avg_requests_per_second': avg_req_per_sec,
                'avg_time_per_request_ms': avg_time_per_req,
                'consistency_score': 1.0 - (statistics.stdev([r['total_time_ms'] for r in run_results]) / avg_total_time)
            },
            'performance_stats': self.get_performance_stats()
        }

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'executor'):
            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass  # Ignore cleanup errors