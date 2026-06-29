"""
Performance Monitor & Structured Logging

Features:
- Tool execution statistics (call count, success rate, avg duration)
- LLM request tracking (latency, token usage, error rate)
- Structured event logging with context
- Performance alerts for slow operations
"""
import time
import logging
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class ToolStats:
    """Statistics for a single tool."""
    name: str
    call_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    last_error: str = ""
    last_used: str = ""

    @property
    def success_rate(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.success_count / self.call_count * 100

    @property
    def avg_duration_ms(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.total_duration_ms / self.call_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "call_count": self.call_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate, 1),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "min_duration_ms": round(self.min_duration_ms, 1) if self.min_duration_ms != float('inf') else 0,
            "max_duration_ms": round(self.max_duration_ms, 1),
            "last_error": self.last_error,
            "last_used": self.last_used,
        }


@dataclass
class LLMRequestStats:
    """Statistics for LLM API requests."""
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_duration_ms: float = 0.0
    last_error: str = ""

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests * 100

    @property
    def avg_duration_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "error_rate": round(self.error_rate, 1),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "last_error": self.last_error,
        }


class PerformanceMonitor:
    """Global performance monitor."""

    def __init__(self, data_dir: Optional[str] = None):
        self.tool_stats: Dict[str, ToolStats] = defaultdict(lambda: None)
        self.llm_stats: Dict[str, LLMRequestStats] = defaultdict(lambda: None)
        self.events: List[Dict[str, Any]] = []
        self.max_events = 1000  # Keep last N events in memory
        self.slow_threshold_ms = 5000  # Alert for operations > 5s
        
        if data_dir is None:
            self.data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "..", "data", "metrics"
            )
        else:
            self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_tool_stats(self, name: str) -> ToolStats:
        if self.tool_stats[name] is None:
            self.tool_stats[name] = ToolStats(name=name)
        return self.tool_stats[name]

    def _get_llm_stats(self, provider: str) -> LLMRequestStats:
        if self.llm_stats[provider] is None:
            self.llm_stats[provider] = LLMRequestStats(provider=provider)
        return self.llm_stats[provider]

    # ── Tool Tracking ───────────────────────────────────────

    def record_tool_call(self, name: str, success: bool, duration_ms: float,
                         error: str = "") -> None:
        """Record a tool execution."""
        stats = self._get_tool_stats(name)
        stats.call_count += 1
        stats.total_duration_ms += duration_ms
        stats.min_duration_ms = min(stats.min_duration_ms, duration_ms)
        stats.max_duration_ms = max(stats.max_duration_ms, duration_ms)
        stats.last_used = datetime.now().isoformat()

        if success:
            stats.success_count += 1
        else:
            stats.error_count += 1
            stats.last_error = error

        # Log slow operations
        if duration_ms > self.slow_threshold_ms:
            logger.warning(f"⏱️ Slow tool: {name} took {duration_ms:.0f}ms (success={success})")
            self.log_event("slow_tool", {
                "tool": name, "duration_ms": duration_ms, "success": success
            })

        self.log_event("tool_call", {
            "tool": name, "success": success, "duration_ms": round(duration_ms, 1)
        })

    # ── LLM Tracking ────────────────────────────────────────

    def record_llm_request(self, provider: str, success: bool, duration_ms: float,
                           tokens_in: int = 0, tokens_out: int = 0,
                           error: str = "") -> None:
        """Record an LLM API request."""
        stats = self._get_llm_stats(provider)
        stats.total_requests += 1
        stats.total_duration_ms += duration_ms
        stats.total_tokens_in += tokens_in
        stats.total_tokens_out += tokens_out

        if success:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1
            stats.last_error = error

        if duration_ms > self.slow_threshold_ms * 2:
            logger.warning(f"⏱️ Slow LLM request: {provider} took {duration_ms:.0f}ms")

        self.log_event("llm_request", {
            "provider": provider, "success": success,
            "duration_ms": round(duration_ms, 1),
            "tokens_in": tokens_in, "tokens_out": tokens_out,
        })

    # ── Event Logging ───────────────────────────────────────

    def log_event(self, event_type: str, data: Dict[str, Any],
                  level: str = "info") -> None:
        """Log a structured event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "level": level,
            "data": data,
        }
        self.events.append(event)

        # Trim old events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        # Also log to standard logger
        msg = f"[{event_type}] {json.dumps(data, ensure_ascii=False)}"
        if level == "error":
            logger.error(msg)
        elif level == "warning":
            logger.warning(msg)
        else:
            logger.debug(msg)

    # ── Reporting ───────────────────────────────────────────

    def get_tool_report(self) -> List[Dict[str, Any]]:
        """Get tool execution statistics."""
        return sorted(
            [s.to_dict() for s in self.tool_stats.values() if s is not None],
            key=lambda x: x["call_count"],
            reverse=True
        )

    def get_llm_report(self) -> List[Dict[str, Any]]:
        """Get LLM request statistics."""
        return [s.to_dict() for s in self.llm_stats.values() if s is not None]

    def get_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        tool_reports = self.get_tool_report()
        llm_reports = self.get_llm_report()
        
        total_tool_calls = sum(t["call_count"] for t in tool_reports)
        total_tool_errors = sum(t["error_count"] for t in tool_reports)
        total_llm_requests = sum(l["total_requests"] for l in llm_reports)
        total_llm_errors = sum(l["failed_requests"] for l in llm_reports)
        total_tokens = sum(l["total_tokens_in"] + l["total_tokens_out"] for l in llm_reports)

        return {
            "tools": {
                "registered": len(tool_reports),
                "total_calls": total_tool_calls,
                "total_errors": total_tool_errors,
                "error_rate": round(total_tool_errors / max(total_tool_calls, 1) * 100, 1),
            },
            "llm": {
                "providers": len(llm_reports),
                "total_requests": total_llm_requests,
                "total_errors": total_llm_errors,
                "error_rate": round(total_llm_errors / max(total_llm_requests, 1) * 100, 1),
                "total_tokens": total_tokens,
            },
            "events_logged": len(self.events),
        }

    def get_recent_events(self, count: int = 50, event_type: str = None) -> List[Dict]:
        """Get recent events, optionally filtered by type."""
        events = self.events
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        return events[-count:]

    # ── Persistence ─────────────────────────────────────────

    def save_metrics(self) -> str:
        """Save metrics to disk."""
        filepath = os.path.join(self.data_dir, f"metrics_{datetime.now().strftime('%Y%m%d')}.json")
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "tools": self.get_tool_report(),
            "llm": self.get_llm_report(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Metrics saved to {filepath}")
        return filepath

    def reset(self) -> None:
        """Reset all statistics."""
        self.tool_stats.clear()
        self.llm_stats.clear()
        self.events.clear()
        logger.info("Performance monitor reset")


# ── Timing Context Manager ──────────────────────────────────

class Timer:
    """Context manager for timing operations and recording to monitor."""
    
    def __init__(self, monitor: PerformanceMonitor, operation: str,
                 category: str = "generic", extra: Dict = None):
        self.monitor = monitor
        self.operation = operation
        self.category = category
        self.extra = extra or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        success = exc_type is None
        error = str(exc_val) if exc_val else ""

        if self.category == "tool":
            self.monitor.record_tool_call(self.operation, success, duration_ms, error)
        elif self.category == "llm":
            self.monitor.record_llm_request(self.operation, success, duration_ms, error=error)
        else:
            self.monitor.log_event(f"{self.category}_timing", {
                "operation": self.operation,
                "duration_ms": round(duration_ms, 1),
                "success": success,
                **self.extra,
            })
        
        return False  # Don't suppress exceptions


# ── Global Instance ─────────────────────────────────────────

_monitor_instance: Optional[PerformanceMonitor] = None

def get_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance
