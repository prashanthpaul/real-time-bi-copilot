"""
MCP Resource: query_history
==============================
Tracks and exposes query execution history as an MCP resource.
Stores query text, timestamps, results, and performance metrics.
"""

import logging
import time
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)


class QueryHistory:
    """In-memory query history tracker."""

    def __init__(self, max_entries: int = 100):
        self._history: deque[dict] = deque(maxlen=max_entries)
        self._max_entries = max_entries

    def record(
        self,
        query: str,
        query_type: str,
        result_count: int,
        execution_time_ms: float,
        success: bool = True,
        error: str | None = None,
        generated_sql: str | None = None,
    ) -> None:
        """Record a query execution."""
        entry = {
            "id": len(self._history) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "query_type": query_type,
            "generated_sql": generated_sql,
            "result_count": result_count,
            "execution_time_ms": execution_time_ms,
            "success": success,
            "error": error,
        }
        self._history.append(entry)
        logger.info(f"Query #{entry['id']} recorded: {query_type}, {execution_time_ms}ms")

    def get_history(self, limit: int = 20) -> list[dict]:
        """Get recent query history."""
        entries = list(self._history)
        entries.reverse()
        return entries[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get query performance statistics."""
        if not self._history:
            return {"total_queries": 0}

        entries = list(self._history)
        times = [e["execution_time_ms"] for e in entries if e["success"]]
        errors = [e for e in entries if not e["success"]]

        return {
            "total_queries": len(entries),
            "successful": len(entries) - len(errors),
            "failed": len(errors),
            "avg_execution_ms": round(sum(times) / len(times), 2) if times else 0,
            "max_execution_ms": round(max(times), 2) if times else 0,
            "min_execution_ms": round(min(times), 2) if times else 0,
        }

    def clear(self) -> None:
        """Clear all history."""
        self._history.clear()


# Singleton instance
query_history = QueryHistory()

RESOURCE_DEFINITIONS = [
    {
        "uri": "bi-copilot://query-history",
        "name": "Query History",
        "description": "Recent query execution history with performance metrics",
        "mimeType": "application/json",
    }
]
