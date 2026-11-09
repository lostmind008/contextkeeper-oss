#!/usr/bin/env python3
"""
Performance Optimizations Integration for ContextKeeper
Integrates caching, optimised embeddings, and performance monitoring into the existing RAG system.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from google import genai
from google.genai.types import HttpOptions

from performance_cache import QueryResultCache, EmbeddingCache
from optimised_embeddings import OptimisedEmbeddingGenerator
from performance_profiler import PerformanceProfiler

logger = logging.getLogger(__name__)


class PerformanceOptimizedEmbeddingFunction:
    """
    Drop-in replacement for GoogleGenAIEmbeddingFunction with performance optimisations
    """
    
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        self.api_key = api_key
        self.model = model
        
        # Initialize optimised embedding generator
        self.embedding_generator = OptimisedEmbeddingGenerator(
            api_key=api_key,
            model=model,
            batch_size=10,
            max_concurrent_batches=3,
            cache_enabled=True,
            cache_size_mb=64
        )
        
        # Performance tracking
        self.profiler = PerformanceProfiler()
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Embed a list of texts with performance optimisations
        Compatible with ChromaDB embedding function interface
        """
        if not input:
            return []
        
        try:
            with self.profiler.profile_operation(
                "chromadb_embedding_batch",
                {"batch_size": len(input), "model": self.model}
            ):
                # Use async embedding generation in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    responses = loop.run_until_complete(
                        self.embedding_generator.generate_embeddings_batch(input)
                    )
                finally:
                    loop.close()
                
                # Extract embeddings and handle errors
                embeddings = []
                for response in responses:
                    if response.embedding is not None:
                        embeddings.append(response.embedding)
                    else:
                        # Return zero vector on error (compatible with original behavior)
                        logger.error(f"Embedding error: {response.error}")
                        embeddings.append([0.0] * 768)
                
                return embeddings
        
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            # Fallback to zero vectors
            return [[0.0] * 768 for _ in input]
    
    def name(self) -> str:
        """Return the name of the embedding function"""
        return f"optimised_google_genai_{self.model}"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from embedding generator"""
        return self.embedding_generator.get_performance_stats()


class PerformanceOptimizedRAGAgent:
    """
    Mixin class to add performance optimisations to existing RAG agent
    Provides caching, performance monitoring, and optimised operations
    """
    
    def __init__(self):
        # Initialize performance components
        self.query_cache = QueryResultCache(max_size_mb=128, default_ttl_seconds=1800)
        self.profiler = PerformanceProfiler()
        
        # Performance monitoring flags
        self.performance_monitoring_enabled = True
        self.detailed_profiling_enabled = False
    
    async def query_with_cache(
        self,
        question: str,
        k: int = 5,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced query method with intelligent caching
        
        Args:
            question: Question to query
            k: Number of results to return
            project_id: Target project ID
            
        Returns:
            Query results with cache performance metadata
        """
        # Use focused project if no project_id provided
        if project_id is None:
            project_id = getattr(self, 'project_manager', None)
            if project_id and hasattr(project_id, 'focused_project_id'):
                project_id = project_id.focused_project_id
        
        if project_id is None:
            return {
                'query': question,
                'error': 'No project context specified',
                'results': [],
                'cache_hit': False
            }
        
        # Check cache first
        cached_result = self.query_cache.get_cached_query_result(question, project_id, k)
        if cached_result is not None:
            logger.debug(f"Cache hit for query: {question[:50]}...")
            self.profiler.record_cache_hit()
            
            # Add cache metadata
            cached_result['cache_hit'] = True
            cached_result['cached_at'] = time.time()
            return cached_result
        
        # Record cache miss
        self.profiler.record_cache_miss()
        
        # Profile the query operation
        with self.profiler.profile_operation(
            "chromadb_query_with_llm",
            {"question_length": len(question), "k": k, "project_id": project_id}
        ):
            # Execute original query (assuming the method exists)
            if hasattr(self, 'query'):
                results = await self.query(question, k, project_id)
            else:
                results = {
                    'error': 'Base query method not available',
                    'results': []
                }
        
        # Cache successful results
        if results and not results.get('error'):
            self.query_cache.cache_query_result(question, project_id, k, results)
        
        # Add performance metadata
        results['cache_hit'] = False
        return results
    
    async def ingest_with_performance_tracking(
        self,
        path: str,
        project_id: str,
        chunk_batch_size: int = 50
    ) -> int:
        """
        Enhanced ingestion with performance tracking and batch optimisation
        
        Args:
            path: Path to ingest
            project_id: Target project ID
            chunk_batch_size: Number of chunks to process in each batch
            
        Returns:
            Number of chunks ingested
        """
        with self.profiler.profile_operation(
            "document_ingestion",
            {"path": path, "project_id": project_id, "batch_size": chunk_batch_size}
        ):
            if hasattr(self, 'ingest_file'):
                # Use existing ingestion method if available
                if os.path.isfile(path):
                    return await self.ingest_file(path, project_id)
                else:
                    return await self.ingest_directory(path, project_id)
            else:
                logger.error("Base ingestion methods not available")
                return 0
    
    def invalidate_project_cache(self, project_id: str):
        """Invalidate all cached results for a specific project"""
        self.query_cache.invalidate_project(project_id)
        logger.info(f"Invalidated cache for project: {project_id}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics across all components
        
        Returns:
            Dictionary containing performance statistics and recommendations
        """
        performance_report = self.profiler.get_performance_report()
        
        # Add cache statistics
        if hasattr(self, 'query_cache'):
            cache_stats = self.query_cache.get_detailed_stats()
            performance_report['query_cache'] = cache_stats
        
        # Add embedding performance if available
        if hasattr(self, 'embedding_function') and hasattr(self.embedding_function, 'get_performance_stats'):
            embedding_stats = self.embedding_function.get_performance_stats()
            performance_report['embeddings'] = embedding_stats
        
        return performance_report
    
    def optimize_performance_settings(self) -> Dict[str, Any]:
        """
        Analyse current performance and suggest optimisations
        
        Returns:
            Dictionary with optimization recommendations
        """
        metrics = self.get_performance_metrics()
        recommendations = []
        
        # Analyze query performance
        if 'operation_statistics' in metrics:
            ops = metrics['operation_statistics']
            
            if 'chromadb_query' in ops:
                avg_query_time = ops['chromadb_query']['avg_time_ms']
                if avg_query_time > 1000:
                    recommendations.append({
                        'component': 'ChromaDB Queries',
                        'issue': f'Slow query performance ({avg_query_time:.0f}ms average)',
                        'recommendation': 'Consider adding more specific filters or reducing vector dimensions',
                        'priority': 'high'
                    })
            
            if 'chromadb_embedding_batch' in ops:
                avg_embed_time = ops['chromadb_embedding_batch']['avg_time_ms']
                if avg_embed_time > 500:
                    recommendations.append({
                        'component': 'Embedding Generation',
                        'issue': f'Slow embedding generation ({avg_embed_time:.0f}ms average)',
                        'recommendation': 'Consider increasing batch size or cache duration',
                        'priority': 'medium'
                    })
        
        # Analyze cache performance
        if 'cache_statistics' in metrics:
            hit_rate = metrics['cache_statistics']['hit_rate']
            if hit_rate < 0.3:
                recommendations.append({
                    'component': 'Query Cache',
                    'issue': f'Low cache hit rate ({hit_rate:.1%})',
                    'recommendation': 'Consider increasing cache size or TTL duration',
                    'priority': 'medium'
                })
        
        return {
            'current_metrics': metrics,
            'recommendations': recommendations,
            'optimization_suggestions': {
                'cache_size_mb': min(512, max(128, metrics.get('query_cache', {}).get('memory_efficiency', {}).get('cache_size_mb', 128) * 1.5)),
                'embedding_batch_size': 15,  # Slightly larger batches for better throughput
                'query_cache_ttl': 3600  # 1 hour TTL for frequent queries
            }
        }
    
    async def run_performance_benchmark(
        self,
        test_queries: Optional[List[str]] = None,
        benchmark_duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Run comprehensive performance benchmark
        
        Args:
            test_queries: Optional list of test queries (generates defaults if None)
            benchmark_duration_minutes: Duration for benchmark testing
            
        Returns:
            Benchmark results and performance analysis
        """
        if test_queries is None:
            test_queries = [
                "How does authentication work?",
                "Show me error handling patterns",
                "What are the main components?",
                "Find database connection code",
                "How is caching implemented?"
            ]
        
        logger.info(f"Starting {benchmark_duration_minutes}-minute performance benchmark")
        
        benchmark_results = {
            'start_time': time.time(),
            'duration_minutes': benchmark_duration_minutes,
            'test_queries': len(test_queries),
            'results': []
        }
        
        # Get focused project for testing
        project_id = None
        if hasattr(self, 'project_manager') and hasattr(self.project_manager, 'focused_project_id'):
            project_id = self.project_manager.focused_project_id
        
        if not project_id:
            return {
                'error': 'No focused project available for benchmarking'
            }
        
        # Run benchmark queries
        start_time = time.time()
        end_time = start_time + (benchmark_duration_minutes * 60)
        
        query_count = 0
        total_query_time = 0
        cache_hits = 0
        
        while time.time() < end_time:
            for query in test_queries:
                if time.time() >= end_time:
                    break
                
                query_start = time.time()
                result = await self.query_with_cache(query, k=5, project_id=project_id)
                query_time = time.time() - query_start
                
                query_count += 1
                total_query_time += query_time
                
                if result.get('cache_hit', False):
                    cache_hits += 1
                
                # Brief pause between queries
                await asyncio.sleep(0.1)
        
        # Calculate benchmark statistics
        avg_query_time = total_query_time / query_count if query_count > 0 else 0
        cache_hit_rate = cache_hits / query_count if query_count > 0 else 0
        queries_per_second = query_count / (time.time() - start_time)
        
        benchmark_results.update({
            'end_time': time.time(),
            'total_queries': query_count,
            'avg_query_time_ms': avg_query_time * 1000,
            'cache_hit_rate': cache_hit_rate,
            'queries_per_second': queries_per_second,
            'performance_metrics': self.get_performance_metrics()
        })
        
        logger.info(f"Benchmark complete: {query_count} queries, "
                   f"{avg_query_time*1000:.1f}ms avg, "
                   f"{cache_hit_rate:.1%} cache hit rate")
        
        return benchmark_results
    
    def enable_detailed_profiling(self, enabled: bool = True):
        """Enable or disable detailed performance profiling"""
        self.detailed_profiling_enabled = enabled
        logger.info(f"Detailed profiling {'enabled' if enabled else 'disabled'}")
    
    def export_performance_report(self, filename: str):
        """Export comprehensive performance report to file"""
        report = {
            'timestamp': time.time(),
            'performance_metrics': self.get_performance_metrics(),
            'optimization_analysis': self.optimize_performance_settings()
        }
        
        import json
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Performance report exported to {filename}")


# Integration helper functions

def enhance_rag_agent_with_performance(agent_instance):
    """
    Enhance an existing RAG agent instance with performance optimisations
    
    Args:
        agent_instance: Existing RAG agent to enhance
        
    Returns:
        Enhanced agent with performance optimisations
    """
    # Add performance optimisation methods
    for method_name in dir(PerformanceOptimizedRAGAgent):
        if not method_name.startswith('_') and callable(getattr(PerformanceOptimizedRAGAgent, method_name)):
            setattr(agent_instance, method_name, 
                   getattr(PerformanceOptimizedRAGAgent(), method_name).__get__(agent_instance))
    
    # Initialize performance components
    agent_instance.query_cache = QueryResultCache(max_size_mb=128, default_ttl_seconds=1800)
    agent_instance.profiler = PerformanceProfiler()
    agent_instance.performance_monitoring_enabled = True
    agent_instance.detailed_profiling_enabled = False
    
    logger.info("RAG agent enhanced with performance optimisations")
    return agent_instance


def replace_embedding_function_with_optimized(agent_instance, api_key: str):
    """
    Replace the agent's embedding function with the performance-optimised version
    
    Args:
        agent_instance: RAG agent instance
        api_key: Google AI API key
    """
    if hasattr(agent_instance, 'embedding_function'):
        old_model = getattr(agent_instance.embedding_function, 'model', 'text-embedding-004')
        agent_instance.embedding_function = PerformanceOptimizedEmbeddingFunction(
            api_key=api_key,
            model=old_model
        )
        logger.info("Embedding function replaced with performance-optimised version")
    else:
        logger.warning("No embedding function found to replace")


async def benchmark_performance_improvements(
    original_agent,
    optimized_agent,
    test_queries: List[str],
    project_id: str
) -> Dict[str, Any]:
    """
    Compare performance between original and optimised agents
    
    Args:
        original_agent: Original RAG agent
        optimized_agent: Performance-optimised RAG agent
        test_queries: List of test queries
        project_id: Project ID for testing
        
    Returns:
        Performance comparison results
    """
    results = {
        'test_configuration': {
            'num_queries': len(test_queries),
            'project_id': project_id
        },
        'original_performance': {},
        'optimized_performance': {},
        'improvements': {}
    }
    
    # Test original agent
    logger.info("Testing original agent performance...")
    original_start = time.time()
    original_times = []
    
    for query in test_queries:
        query_start = time.time()
        await original_agent.query(query, k=5, project_id=project_id)
        original_times.append((time.time() - query_start) * 1000)
    
    original_total_time = (time.time() - original_start) * 1000
    
    # Test optimized agent
    logger.info("Testing optimized agent performance...")
    optimized_start = time.time()
    optimized_times = []
    cache_hits = 0
    
    for query in test_queries:
        query_start = time.time()
        result = await optimized_agent.query_with_cache(query, k=5, project_id=project_id)
        optimized_times.append((time.time() - query_start) * 1000)
        
        if result.get('cache_hit', False):
            cache_hits += 1
    
    optimized_total_time = (time.time() - optimized_start) * 1000
    
    # Calculate statistics
    import statistics
    
    results['original_performance'] = {
        'total_time_ms': original_total_time,
        'avg_query_time_ms': statistics.mean(original_times),
        'queries_per_second': len(test_queries) / (original_total_time / 1000)
    }
    
    results['optimized_performance'] = {
        'total_time_ms': optimized_total_time,
        'avg_query_time_ms': statistics.mean(optimized_times),
        'queries_per_second': len(test_queries) / (optimized_total_time / 1000),
        'cache_hit_rate': cache_hits / len(test_queries)
    }
    
    # Calculate improvements
    time_improvement = (original_total_time - optimized_total_time) / original_total_time
    throughput_improvement = (results['optimized_performance']['queries_per_second'] - 
                            results['original_performance']['queries_per_second']) / results['original_performance']['queries_per_second']
    
    results['improvements'] = {
        'time_reduction_percent': time_improvement * 100,
        'throughput_increase_percent': throughput_improvement * 100,
        'cache_hit_rate_percent': results['optimized_performance']['cache_hit_rate'] * 100
    }
    
    logger.info(f"Performance comparison complete. "
               f"Time reduction: {time_improvement*100:.1f}%, "
               f"Throughput increase: {throughput_improvement*100:.1f}%")
    
    return results