#!/usr/bin/env python3
"""
Performance Cache System for ContextKeeper
Implements intelligent caching for ChromaDB queries, embeddings, and other expensive operations
with memory management and cache invalidation strategies.
"""

import hashlib
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from threading import RLock
import psutil

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    key: str
    value: Any
    timestamp: datetime
    access_count: int
    last_accessed: datetime
    size_bytes: int
    ttl_seconds: Optional[int] = None


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int
    misses: int
    evictions: int
    total_size_bytes: int
    entry_count: int
    hit_rate: float
    memory_usage_mb: float


class IntelligentCache:
    """
    High-performance cache with intelligent eviction and memory management
    Optimised for ChromaDB query results and embeddings
    """

    def __init__(
        self,
        max_size_mb: int = 256,
        default_ttl_seconds: int = 3600,
        max_entries: int = 10000,
        cleanup_interval_seconds: int = 300
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds
        self.max_entries = max_entries
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = RLock()
        self._stats = CacheStats(0, 0, 0, 0, 0, 0.0, 0.0)
        self._last_cleanup = time.time()

    def _generate_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate deterministic cache key from operation and parameters"""
        # Sort params to ensure consistent key generation
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        key_data = f"{operation}:{sorted_params}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _estimate_size_bytes(self, value: Any) -> int:
        """Estimate memory size of cache value"""
        try:
            # For JSON-serializable objects
            if isinstance(value, (dict, list, str, int, float, bool)):
                return len(json.dumps(value, default=str).encode())
            # Fallback estimation
            return len(str(value).encode())
        except Exception:
            return 1024  # Default estimate

    def _should_cleanup(self) -> bool:
        """Check if cache cleanup is needed"""
        return (
            time.time() - self._last_cleanup > self.cleanup_interval_seconds or
            len(self._cache) > self.max_entries or
            self._stats.total_size_bytes > self.max_size_bytes
        )

    def _cleanup_expired_entries(self):
        """Remove expired cache entries"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, entry in self._cache.items():
            # Check TTL expiration
            if entry.ttl_seconds and (current_time - entry.timestamp).total_seconds() > entry.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
            self._stats.evictions += 1
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _evict_lru_entries(self, target_size_reduction: int):
        """Evict least recently used entries to free up space"""
        # Sort by last accessed time (LRU first)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: (x[1].last_accessed, x[1].access_count)
        )
        
        bytes_freed = 0
        evicted_count = 0
        
        for key, entry in sorted_entries:
            if bytes_freed >= target_size_reduction:
                break
                
            bytes_freed += entry.size_bytes
            self._remove_entry(key)
            evicted_count += 1
            self._stats.evictions += 1
        
        logger.debug(f"Evicted {evicted_count} LRU entries, freed {bytes_freed} bytes")

    def _remove_entry(self, key: str):
        """Remove a cache entry and update stats"""
        if key in self._cache:
            entry = self._cache[key]
            self._stats.total_size_bytes -= entry.size_bytes
            self._stats.entry_count -= 1
            del self._cache[key]

    def _update_stats(self):
        """Update cache statistics"""
        total_requests = self._stats.hits + self._stats.misses
        self._stats.hit_rate = self._stats.hits / total_requests if total_requests > 0 else 0.0
        
        # Update memory usage
        process = psutil.Process()
        self._stats.memory_usage_mb = process.memory_info().rss / 1024 / 1024

    def get(self, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Retrieve value from cache
        
        Args:
            operation: Operation name (e.g., 'chromadb_query', 'embedding_generation')
            params: Operation parameters for cache key generation
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._generate_cache_key(operation, params)
        
        with self._lock:
            if cache_key not in self._cache:
                self._stats.misses += 1
                self._update_stats()
                return None
            
            entry = self._cache[cache_key]
            
            # Check TTL expiration
            if entry.ttl_seconds:
                age_seconds = (datetime.now() - entry.timestamp).total_seconds()
                if age_seconds > entry.ttl_seconds:
                    self._remove_entry(cache_key)
                    self._stats.misses += 1
                    self._stats.evictions += 1
                    self._update_stats()
                    return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            self._stats.hits += 1
            self._update_stats()
            
            logger.debug(f"Cache hit for {operation} (key: {cache_key})")
            return entry.value

    def put(
        self,
        operation: str,
        params: Dict[str, Any],
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Store value in cache
        
        Args:
            operation: Operation name
            params: Operation parameters for cache key generation
            value: Value to cache
            ttl_seconds: Time-to-live override (uses default if None)
            
        Returns:
            True if successfully cached, False otherwise
        """
        cache_key = self._generate_cache_key(operation, params)
        size_bytes = self._estimate_size_bytes(value)
        
        # Skip caching very large objects
        if size_bytes > self.max_size_bytes * 0.1:  # No single item > 10% of cache
            logger.warning(f"Skipping cache for large object ({size_bytes} bytes)")
            return False
        
        with self._lock:
            # Perform cleanup if needed
            if self._should_cleanup():
                self._cleanup_expired_entries()
                self._last_cleanup = time.time()
            
            # Check if we need to evict entries to make room
            if self._stats.total_size_bytes + size_bytes > self.max_size_bytes:
                target_reduction = (self._stats.total_size_bytes + size_bytes) - int(self.max_size_bytes * 0.8)
                self._evict_lru_entries(target_reduction)
            
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=value,
                timestamp=datetime.now(),
                access_count=0,
                last_accessed=datetime.now(),
                size_bytes=size_bytes,
                ttl_seconds=ttl_seconds or self.default_ttl_seconds
            )
            
            # Remove existing entry if present
            if cache_key in self._cache:
                self._remove_entry(cache_key)
            
            # Add new entry
            self._cache[cache_key] = entry
            self._stats.total_size_bytes += size_bytes
            self._stats.entry_count += 1
            
            self._update_stats()
            
            logger.debug(f"Cached {operation} result (key: {cache_key}, size: {size_bytes} bytes)")
            return True

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate cache entries matching a pattern
        
        Args:
            pattern: Pattern to match against operation names
        """
        with self._lock:
            keys_to_remove = []
            
            for key, entry in self._cache.items():
                # Simple pattern matching - could be enhanced with regex
                if pattern in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._remove_entry(key)
                self._stats.evictions += 1
            
            self._update_stats()
            
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching pattern: {pattern}")

    def invalidate_project(self, project_id: str):
        """Invalidate all cache entries for a specific project"""
        self.invalidate_pattern(project_id)

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            evicted_count = len(self._cache)
            self._cache.clear()
            self._stats.total_size_bytes = 0
            self._stats.entry_count = 0
            self._stats.evictions += evicted_count
            self._update_stats()
            
            logger.info(f"Cache cleared - removed {evicted_count} entries")

    def get_stats(self) -> CacheStats:
        """Get current cache statistics"""
        with self._lock:
            self._update_stats()
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                total_size_bytes=self._stats.total_size_bytes,
                entry_count=self._stats.entry_count,
                hit_rate=self._stats.hit_rate,
                memory_usage_mb=self._stats.memory_usage_mb
            )

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics and analysis"""
        stats = self.get_stats()
        
        with self._lock:
            # Analyse cache entries by operation type
            operation_stats = {}
            for entry in self._cache.values():
                operation = entry.key.split(':')[0] if ':' in entry.key else 'unknown'
                if operation not in operation_stats:
                    operation_stats[operation] = {
                        'count': 0,
                        'total_size_bytes': 0,
                        'avg_access_count': 0,
                        'total_access_count': 0
                    }
                
                operation_stats[operation]['count'] += 1
                operation_stats[operation]['total_size_bytes'] += entry.size_bytes
                operation_stats[operation]['total_access_count'] += entry.access_count
            
            # Calculate averages
            for op_stats in operation_stats.values():
                if op_stats['count'] > 0:
                    op_stats['avg_access_count'] = op_stats['total_access_count'] / op_stats['count']
                    op_stats['avg_size_bytes'] = op_stats['total_size_bytes'] / op_stats['count']
        
        return {
            'overall_stats': asdict(stats),
            'operation_breakdown': operation_stats,
            'memory_efficiency': {
                'cache_size_mb': stats.total_size_bytes / 1024 / 1024,
                'max_size_mb': self.max_size_bytes / 1024 / 1024,
                'utilisation_percent': (stats.total_size_bytes / self.max_size_bytes) * 100,
                'avg_entry_size_bytes': stats.total_size_bytes / stats.entry_count if stats.entry_count > 0 else 0
            },
            'recommendations': self._generate_cache_recommendations(stats, operation_stats)
        }

    def _generate_cache_recommendations(self, stats: CacheStats, operation_stats: Dict) -> List[str]:
        """Generate cache optimization recommendations"""
        recommendations = []
        
        # Hit rate analysis
        if stats.hit_rate < 0.3:
            recommendations.append(
                f"Low cache hit rate ({stats.hit_rate:.1%}). Consider increasing cache size or TTL values."
            )
        elif stats.hit_rate > 0.8:
            recommendations.append("Excellent cache hit rate! Consider increasing cache size for even better performance.")
        
        # Memory utilisation analysis
        utilisation = (stats.total_size_bytes / self.max_size_bytes) * 100
        if utilisation > 90:
            recommendations.append("Cache is nearly full. Consider increasing cache size or reducing TTL values.")
        elif utilisation < 20:
            recommendations.append("Cache is underutilised. You could reduce cache size to free up memory.")
        
        # Operation-specific recommendations
        for operation, op_stats in operation_stats.items():
            if op_stats['avg_access_count'] < 2:
                recommendations.append(
                    f"Low reuse for {operation} operations. Consider shorter TTL or different caching strategy."
                )
            elif op_stats['avg_access_count'] > 10:
                recommendations.append(
                    f"High reuse for {operation} operations. Consider longer TTL to reduce cache misses."
                )
        
        return recommendations


class QueryResultCache(IntelligentCache):
    """Specialised cache for ChromaDB query results"""
    
    def __init__(self, max_size_mb: int = 128, default_ttl_seconds: int = 1800):
        super().__init__(max_size_mb, default_ttl_seconds)
        
    def cache_query_result(
        self,
        query: str,
        project_id: str,
        k: int,
        results: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Cache ChromaDB query results"""
        params = {
            'query': query,
            'project_id': project_id,
            'k': k,
            'query_hash': hashlib.md5(query.encode()).hexdigest()[:8]
        }
        
        return self.put('chromadb_query', params, results, ttl_seconds)
    
    def get_cached_query_result(
        self,
        query: str,
        project_id: str,
        k: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached ChromaDB query results"""
        params = {
            'query': query,
            'project_id': project_id,
            'k': k,
            'query_hash': hashlib.md5(query.encode()).hexdigest()[:8]
        }
        
        return self.get('chromadb_query', params)


class EmbeddingCache(IntelligentCache):
    """Specialised cache for embedding vectors"""
    
    def __init__(self, max_size_mb: int = 64, default_ttl_seconds: int = 7200):
        super().__init__(max_size_mb, default_ttl_seconds)
    
    def cache_embedding(
        self,
        text: str,
        model: str,
        embedding: List[float],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Cache embedding vector for text"""
        params = {
            'text_hash': hashlib.sha256(text.encode()).hexdigest(),
            'model': model,
            'text_length': len(text)
        }
        
        return self.put('embedding_generation', params, embedding, ttl_seconds)
    
    def get_cached_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Retrieve cached embedding for text"""
        params = {
            'text_hash': hashlib.sha256(text.encode()).hexdigest(),
            'model': model,
            'text_length': len(text)
        }
        
        return self.get('embedding_generation', params)