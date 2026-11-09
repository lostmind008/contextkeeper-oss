#!/usr/bin/env python3
"""
Performance Profiler for ContextKeeper
Measures and reports on ChromaDB query performance, embedding generation times,
and overall system performance characteristics.
"""

import time
import asyncio
import psutil
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Container for performance measurement data"""
    operation: str
    duration_ms: float
    memory_before_mb: float
    memory_after_mb: float
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class QueryPerformanceStats:
    """Statistics for query performance"""
    avg_query_time_ms: float
    p50_query_time_ms: float
    p95_query_time_ms: float
    p99_query_time_ms: float
    total_queries: int
    cache_hit_rate: float
    avg_memory_usage_mb: float


class PerformanceProfiler:
    """
    Performance profiler for ContextKeeper operations
    Tracks query times, memory usage, and provides optimisation recommendations
    """

    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.query_cache_stats = {"hits": 0, "misses": 0}
        self.start_time = datetime.now()
        
    @contextmanager
    def profile_operation(self, operation_name: str, metadata: Dict[str, Any] = None):
        """Context manager for profiling operations"""
        if metadata is None:
            metadata = {}
            
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.perf_counter()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            duration_ms = (end_time - start_time) * 1000
            
            metric = PerformanceMetric(
                operation=operation_name,
                duration_ms=duration_ms,
                memory_before_mb=memory_before,
                memory_after_mb=memory_after,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self.metrics.append(metric)
            
            # Log slow operations
            if duration_ms > 1000:  # Over 1 second
                logger.warning(f"Slow operation: {operation_name} took {duration_ms:.2f}ms")

    def measure_chromadb_query_performance(self, agent, test_queries: List[str], project_id: str) -> QueryPerformanceStats:
        """
        Measure ChromaDB query performance with a set of test queries
        
        Args:
            agent: The RAG agent instance
            test_queries: List of test queries to run
            project_id: Target project ID
            
        Returns:
            QueryPerformanceStats with performance metrics
        """
        query_times = []
        memory_usages = []
        
        for query in test_queries:
            with self.profile_operation("chromadb_query", {"query": query[:50], "project_id": project_id}):
                try:
                    # Run the query
                    results = asyncio.run(agent.query(query, k=5, project_id=project_id))
                    
                    # Record the time from the last metric
                    if self.metrics:
                        last_metric = self.metrics[-1]
                        query_times.append(last_metric.duration_ms)
                        memory_usages.append(last_metric.memory_after_mb)
                        
                except Exception as e:
                    logger.error(f"Query performance test failed: {e}")
                    continue
        
        if not query_times:
            return QueryPerformanceStats(0, 0, 0, 0, 0, 0, 0)
            
        # Calculate statistics
        query_times.sort()
        total_queries = len(query_times)
        
        return QueryPerformanceStats(
            avg_query_time_ms=statistics.mean(query_times),
            p50_query_time_ms=query_times[int(total_queries * 0.5)],
            p95_query_time_ms=query_times[int(total_queries * 0.95)] if total_queries > 20 else query_times[-1],
            p99_query_time_ms=query_times[int(total_queries * 0.99)] if total_queries > 100 else query_times[-1],
            total_queries=total_queries,
            cache_hit_rate=self._calculate_cache_hit_rate(),
            avg_memory_usage_mb=statistics.mean(memory_usages) if memory_usages else 0
        )

    def measure_embedding_performance(self, embedding_function, test_texts: List[str]) -> Dict[str, Any]:
        """
        Measure embedding generation performance
        
        Args:
            embedding_function: The embedding function to test
            test_texts: List of texts to embed
            
        Returns:
            Performance metrics for embedding generation
        """
        embedding_times = []
        
        for text in test_texts:
            with self.profile_operation("embedding_generation", {"text_length": len(text)}):
                try:
                    embeddings = embedding_function([text])
                    if self.metrics:
                        embedding_times.append(self.metrics[-1].duration_ms)
                except Exception as e:
                    logger.error(f"Embedding performance test failed: {e}")
                    continue
        
        if not embedding_times:
            return {"error": "No successful embedding operations"}
            
        return {
            "avg_embedding_time_ms": statistics.mean(embedding_times),
            "total_embeddings": len(embedding_times),
            "embeddings_per_second": len(embedding_times) / (sum(embedding_times) / 1000),
            "p95_embedding_time_ms": sorted(embedding_times)[int(len(embedding_times) * 0.95)] if len(embedding_times) > 20 else max(embedding_times)
        }

    def measure_memory_usage_over_time(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """
        Monitor memory usage over time to identify memory leaks
        
        Args:
            duration_minutes: How long to monitor memory usage
            
        Returns:
            Memory usage statistics
        """
        memory_samples = []
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_samples.append(memory_mb)
            time.sleep(10)  # Sample every 10 seconds
        
        if not memory_samples:
            return {"error": "No memory samples collected"}
            
        return {
            "duration_minutes": duration_minutes,
            "avg_memory_mb": statistics.mean(memory_samples),
            "peak_memory_mb": max(memory_samples),
            "min_memory_mb": min(memory_samples),
            "memory_growth_mb": memory_samples[-1] - memory_samples[0],
            "samples_count": len(memory_samples),
            "memory_std_dev": statistics.stdev(memory_samples) if len(memory_samples) > 1 else 0
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate from recorded stats"""
        total_requests = self.query_cache_stats["hits"] + self.query_cache_stats["misses"]
        if total_requests == 0:
            return 0.0
        return self.query_cache_stats["hits"] / total_requests

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Returns:
            Dictionary containing performance analysis and recommendations
        """
        if not self.metrics:
            return {"error": "No performance metrics collected"}
            
        # Group metrics by operation
        operations = {}
        for metric in self.metrics:
            if metric.operation not in operations:
                operations[metric.operation] = []
            operations[metric.operation].append(metric)
        
        # Calculate statistics for each operation type
        operation_stats = {}
        for op_name, metrics in operations.items():
            times = [m.duration_ms for m in metrics]
            memory_usage = [m.memory_after_mb - m.memory_before_mb for m in metrics]
            
            operation_stats[op_name] = {
                "count": len(metrics),
                "avg_time_ms": statistics.mean(times),
                "max_time_ms": max(times),
                "min_time_ms": min(times),
                "avg_memory_delta_mb": statistics.mean(memory_usage),
                "total_time_ms": sum(times)
            }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(operation_stats)
        
        return {
            "profiling_session": {
                "start_time": self.start_time.isoformat(),
                "duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
                "total_operations": len(self.metrics)
            },
            "operation_statistics": operation_stats,
            "cache_statistics": {
                "hit_rate": self._calculate_cache_hit_rate(),
                "hits": self.query_cache_stats["hits"],
                "misses": self.query_cache_stats["misses"]
            },
            "recommendations": recommendations,
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "total_memory_gb": psutil.virtual_memory().total / 1024**3,
                "available_memory_gb": psutil.virtual_memory().available / 1024**3
            }
        }

    def _generate_recommendations(self, operation_stats: Dict[str, Dict]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Check for slow queries
        if "chromadb_query" in operation_stats:
            query_stats = operation_stats["chromadb_query"]
            if query_stats["avg_time_ms"] > 500:
                recommendations.append(
                    f"ChromaDB queries are slow (avg: {query_stats['avg_time_ms']:.0f}ms). "
                    "Consider implementing query result caching or optimising vector indices."
                )
        
        # Check for slow embeddings
        if "embedding_generation" in operation_stats:
            embed_stats = operation_stats["embedding_generation"]
            if embed_stats["avg_time_ms"] > 200:
                recommendations.append(
                    f"Embedding generation is slow (avg: {embed_stats['avg_time_ms']:.0f}ms). "
                    "Consider batch processing embeddings or caching embeddings for repeated content."
                )
        
        # Check cache hit rate
        cache_hit_rate = self._calculate_cache_hit_rate()
        if cache_hit_rate < 0.3 and cache_hit_rate > 0:
            recommendations.append(
                f"Low cache hit rate ({cache_hit_rate:.1%}). Consider increasing cache size or duration."
            )
        
        # Check for memory-intensive operations
        for op_name, stats in operation_stats.items():
            if stats["avg_memory_delta_mb"] > 50:
                recommendations.append(
                    f"{op_name} operations consume significant memory (avg: {stats['avg_memory_delta_mb']:.1f}MB). "
                    "Consider implementing memory optimization or processing in smaller batches."
                )
        
        return recommendations

    def export_metrics_to_json(self, filename: str):
        """Export collected metrics to JSON file"""
        report = self.get_performance_report()
        
        # Add raw metrics for detailed analysis
        report["raw_metrics"] = [
            {
                "operation": m.operation,
                "duration_ms": m.duration_ms,
                "memory_before_mb": m.memory_before_mb,
                "memory_after_mb": m.memory_after_mb,
                "timestamp": m.timestamp.isoformat(),
                "metadata": m.metadata
            }
            for m in self.metrics
        ]
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance metrics exported to {filename}")

    def record_cache_hit(self):
        """Record a cache hit for hit rate calculations"""
        self.query_cache_stats["hits"] += 1

    def record_cache_miss(self):
        """Record a cache miss for hit rate calculations"""
        self.query_cache_stats["misses"] += 1


def create_test_queries() -> List[str]:
    """Create a set of test queries for performance testing"""
    return [
        "How does the authentication system work?",
        "What are the main components of the architecture?",
        "Show me error handling patterns",
        "Find database connection code",
        "What testing frameworks are used?",
        "How is caching implemented?",
        "Show me API endpoint definitions",
        "What are the configuration options?",
        "How is logging configured?",
        "Find security-related code",
        "What are the main data models?",
        "How is state management handled?",
        "Show me validation logic",
        "Find performance optimization code",
        "What dependencies are used?"
    ]


def create_test_texts() -> List[str]:
    """Create test texts for embedding performance testing"""
    return [
        "Short text for embedding test",
        "This is a medium length text that contains more content for embedding performance testing and should represent typical document chunks",
        "This is a much longer text that simulates a large code file or documentation section. " * 10,
        "def function_example():\n    return 'code snippet test'",
        "# Configuration\nSETTING_1 = 'value'\nSETTING_2 = 42",
        "Error: Connection failed to database at localhost:5432",
        "Successfully processed 1000 items in 2.5 seconds",
        "{'key': 'value', 'nested': {'data': [1, 2, 3]}}",
        "SELECT * FROM users WHERE active = true AND created_at > '2024-01-01'",
        "async function processData() { await doSomething(); }"
    ]