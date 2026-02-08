"""
THERESE v2 - Performance Service

US-PERF-01 to US-PERF-05: Performance monitoring and optimization.
"""

import asyncio
import gc
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# US-PERF-01: First Token Time Metrics
# ============================================================


@dataclass
class StreamingMetrics:
    """Metrics for a single streaming response."""

    conversation_id: str
    start_time: float = field(default_factory=time.time)
    first_token_time: float | None = None
    total_tokens: int = 0
    total_time: float | None = None
    provider: str = ""
    model: str = ""

    def record_first_token(self) -> float:
        """Record time to first token and return the latency in ms."""
        if self.first_token_time is None:
            self.first_token_time = time.time()
            latency_ms = (self.first_token_time - self.start_time) * 1000
            logger.info(
                f"[PERF] First token latency: {latency_ms:.0f}ms "
                f"(conv={self.conversation_id[:8]}, provider={self.provider})"
            )
            return latency_ms
        return 0

    def record_token(self) -> None:
        """Record a token."""
        if self.first_token_time is None:
            self.record_first_token()
        self.total_tokens += 1

    def finish(self) -> dict:
        """Finish metrics and return summary."""
        self.total_time = time.time() - self.start_time
        tokens_per_second = (
            self.total_tokens / self.total_time if self.total_time > 0 else 0
        )

        summary = {
            "conversation_id": self.conversation_id,
            "first_token_ms": (
                (self.first_token_time - self.start_time) * 1000
                if self.first_token_time
                else None
            ),
            "total_time_ms": self.total_time * 1000,
            "total_tokens": self.total_tokens,
            "tokens_per_second": tokens_per_second,
            "provider": self.provider,
            "model": self.model,
        }

        logger.info(
            f"[PERF] Stream complete: {self.total_tokens} tokens in "
            f"{self.total_time * 1000:.0f}ms ({tokens_per_second:.1f} tok/s)"
        )

        return summary


class PerformanceMonitor:
    """
    Singleton performance monitor.

    Tracks streaming metrics, memory usage, and provides optimization hints.
    """

    _instance: "PerformanceMonitor | None" = None

    def __new__(cls) -> "PerformanceMonitor":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Recent metrics (keep last 100)
        self._recent_metrics: deque[dict] = deque(maxlen=100)

        # Aggregated stats
        self._total_requests = 0
        self._total_tokens = 0
        self._first_token_latencies: deque[float] = deque(maxlen=100)

        # Memory tracking
        self._last_gc_time = time.time()
        self._gc_interval = 300  # 5 minutes

        # Active streams
        self._active_streams: dict[str, StreamingMetrics] = {}

    def start_stream(
        self, conversation_id: str, provider: str = "", model: str = ""
    ) -> StreamingMetrics:
        """Start tracking a new streaming response."""
        metrics = StreamingMetrics(
            conversation_id=conversation_id,
            provider=provider,
            model=model,
        )
        self._active_streams[conversation_id] = metrics
        self._total_requests += 1
        return metrics

    def get_stream(self, conversation_id: str) -> StreamingMetrics | None:
        """Get metrics for an active stream."""
        return self._active_streams.get(conversation_id)

    def finish_stream(self, conversation_id: str) -> dict | None:
        """Finish tracking a stream and record metrics."""
        metrics = self._active_streams.pop(conversation_id, None)
        if not metrics:
            return None

        summary = metrics.finish()
        self._recent_metrics.append(summary)

        if summary.get("first_token_ms"):
            self._first_token_latencies.append(summary["first_token_ms"])

        self._total_tokens += summary.get("total_tokens", 0)

        # Trigger GC if needed
        self._maybe_gc()

        return summary

    def get_stats(self) -> dict:
        """Get aggregated performance statistics."""
        avg_first_token = (
            sum(self._first_token_latencies) / len(self._first_token_latencies)
            if self._first_token_latencies
            else 0
        )

        p95_first_token = 0
        if self._first_token_latencies:
            sorted_latencies = sorted(self._first_token_latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p95_first_token = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]

        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "active_streams": len(self._active_streams),
            "avg_first_token_ms": avg_first_token,
            "p95_first_token_ms": p95_first_token,
            "recent_metrics_count": len(self._recent_metrics),
            "meets_sla": avg_first_token < 2000,  # < 2s SLA
        }

    def _maybe_gc(self) -> None:
        """Run garbage collection if interval has passed."""
        now = time.time()
        if now - self._last_gc_time > self._gc_interval:
            gc.collect()
            self._last_gc_time = now
            logger.debug("[PERF] Garbage collection triggered")


# Singleton instance
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the performance monitor singleton."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


# ============================================================
# US-PERF-02: Conversation Pagination
# ============================================================


@dataclass
class PaginatedResult:
    """Result with pagination metadata."""

    items: list[Any]
    total: int
    limit: int
    offset: int
    has_more: bool

    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "total": self.total,
            "limit": self.limit,
            "offset": self.offset,
            "has_more": self.has_more,
        }


# ============================================================
# US-PERF-03: Memory Management & Cleanup
# ============================================================


class MemoryManager:
    """
    Memory management service.

    Handles cleanup of orphaned resources and memory optimization.
    """

    _instance: "MemoryManager | None" = None

    def __new__(cls) -> "MemoryManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._start_time = time.time()
        self._cleanup_callbacks: list[callable] = []
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600  # 1 hour

    def register_cleanup(self, callback: callable) -> None:
        """Register a cleanup callback."""
        self._cleanup_callbacks.append(callback)

    def get_uptime_hours(self) -> float:
        """Get application uptime in hours."""
        return (time.time() - self._start_time) / 3600

    async def run_cleanup(self) -> dict:
        """Run all cleanup callbacks."""
        logger.info("[PERF] Running memory cleanup...")
        results = {}

        for callback in self._cleanup_callbacks:
            try:
                name = callback.__name__
                if asyncio.iscoroutinefunction(callback):
                    result = await callback()
                else:
                    result = callback()
                results[name] = result
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
                results[callback.__name__] = {"error": str(e)}

        # Force garbage collection
        gc.collect()

        self._last_cleanup = time.time()
        logger.info(f"[PERF] Cleanup complete: {results}")
        return results

    def get_memory_stats(self) -> dict:
        """Get current memory statistics."""

        # Get object counts
        gc_stats = gc.get_stats()

        return {
            "uptime_hours": self.get_uptime_hours(),
            "gc_stats": gc_stats,
            "last_cleanup_ago_minutes": (time.time() - self._last_cleanup) / 60,
            "registered_cleanups": len(self._cleanup_callbacks),
        }


_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get the memory manager singleton."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


# ============================================================
# US-PERF-04: Search Optimization
# ============================================================


class SearchIndex:
    """
    In-memory search index for fast conversation search.

    Uses inverted index for keyword matching.
    """

    def __init__(self):
        # Inverted index: word -> set of conversation_ids
        self._index: dict[str, set[str]] = {}
        # Title cache: conversation_id -> title
        self._titles: dict[str, str] = {}
        # Last update time per conversation
        self._updated: dict[str, float] = {}

    def index_conversation(
        self, conversation_id: str, title: str, content: str = ""
    ) -> None:
        """Index a conversation for search."""
        # Remove old entries
        self._remove_conversation(conversation_id)

        # Tokenize title and content
        text = f"{title} {content}".lower()
        words = set(text.split())

        # Add to inverted index
        for word in words:
            if len(word) >= 2:  # Skip single chars
                if word not in self._index:
                    self._index[word] = set()
                self._index[word].add(conversation_id)

        self._titles[conversation_id] = title
        self._updated[conversation_id] = time.time()

    def _remove_conversation(self, conversation_id: str) -> None:
        """Remove a conversation from the index."""
        for word_set in self._index.values():
            word_set.discard(conversation_id)

        self._titles.pop(conversation_id, None)
        self._updated.pop(conversation_id, None)

    def search(self, query: str, limit: int = 50) -> list[tuple[str, str, float]]:
        """
        Search conversations by query.

        Returns list of (conversation_id, title, score) tuples.
        """
        if not query:
            return []

        query_words = set(query.lower().split())
        scores: dict[str, float] = {}

        for word in query_words:
            # Exact match
            if word in self._index:
                for conv_id in self._index[word]:
                    scores[conv_id] = scores.get(conv_id, 0) + 1.0

            # Prefix match
            for indexed_word, conv_ids in self._index.items():
                if indexed_word.startswith(word) and indexed_word != word:
                    for conv_id in conv_ids:
                        scores[conv_id] = scores.get(conv_id, 0) + 0.5

        # Sort by score and return top results
        results = [
            (conv_id, self._titles.get(conv_id, ""), score)
            for conv_id, score in scores.items()
        ]
        results.sort(key=lambda x: (-x[2], -self._updated.get(x[0], 0)))

        return results[:limit]

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "indexed_conversations": len(self._titles),
            "unique_words": len(self._index),
            "total_entries": sum(len(s) for s in self._index.values()),
        }


_search_index: SearchIndex | None = None


def get_search_index() -> SearchIndex:
    """Get the search index singleton."""
    global _search_index
    if _search_index is None:
        _search_index = SearchIndex()
    return _search_index


# ============================================================
# US-PERF-05: Battery Optimization
# ============================================================


@dataclass
class PowerSettings:
    """Power/battery optimization settings."""

    # Polling intervals (in seconds)
    health_check_interval: int = 30  # Default: 30s
    conversation_sync_interval: int = 60  # Default: 60s

    # Reduce activity when on battery
    battery_saver_mode: bool = False

    # Animation settings
    reduce_animations: bool = False

    def to_dict(self) -> dict:
        return {
            "health_check_interval": self.health_check_interval,
            "conversation_sync_interval": self.conversation_sync_interval,
            "battery_saver_mode": self.battery_saver_mode,
            "reduce_animations": self.reduce_animations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PowerSettings":
        return cls(
            health_check_interval=data.get("health_check_interval", 30),
            conversation_sync_interval=data.get("conversation_sync_interval", 60),
            battery_saver_mode=data.get("battery_saver_mode", False),
            reduce_animations=data.get("reduce_animations", False),
        )

    @classmethod
    def battery_saver(cls) -> "PowerSettings":
        """Settings optimized for battery life."""
        return cls(
            health_check_interval=120,  # 2 min
            conversation_sync_interval=300,  # 5 min
            battery_saver_mode=True,
            reduce_animations=True,
        )


_power_settings: PowerSettings | None = None


def get_power_settings() -> PowerSettings:
    """Get current power settings."""
    global _power_settings
    if _power_settings is None:
        _power_settings = PowerSettings()
    return _power_settings


def set_power_settings(settings: PowerSettings) -> None:
    """Set power settings."""
    global _power_settings
    _power_settings = settings
    logger.info(f"[PERF] Power settings updated: {settings.to_dict()}")
