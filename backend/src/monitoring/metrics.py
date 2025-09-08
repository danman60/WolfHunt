"""Metrics collection and monitoring system."""

import time
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    metric_type: MetricType


class MetricsCollector:
    """Collects and manages application metrics."""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        labels = labels or {}
        key = self._make_key(name, labels)
        
        self.counters[key] += value
        
        metric_point = MetricPoint(
            name=name,
            value=self.counters[key],
            labels=labels,
            timestamp=datetime.utcnow(),
            metric_type=MetricType.COUNTER
        )
        
        self.metrics[key].append(metric_point)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        labels = labels or {}
        key = self._make_key(name, labels)
        
        self.gauges[key] = value
        
        metric_point = MetricPoint(
            name=name,
            value=value,
            labels=labels,
            timestamp=datetime.utcnow(),
            metric_type=MetricType.GAUGE
        )
        
        self.metrics[key].append(metric_point)
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """Record a timing metric."""
        labels = labels or {}
        key = self._make_key(name, labels)
        
        # Keep only recent timer values for efficiency
        if len(self.timers[key]) >= 1000:
            self.timers[key] = self.timers[key][-500:]
        
        self.timers[key].append(duration)
        
        metric_point = MetricPoint(
            name=name,
            value=duration,
            labels=labels,
            timestamp=datetime.utcnow(),
            metric_type=MetricType.TIMER
        )
        
        self.metrics[key].append(metric_point)
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram metric."""
        labels = labels or {}
        key = self._make_key(name, labels)
        
        metric_point = MetricPoint(
            name=name,
            value=value,
            labels=labels,
            timestamp=datetime.utcnow(),
            metric_type=MetricType.HISTOGRAM
        )
        
        self.metrics[key].append(metric_point)
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        key = self._make_key(name, labels or {})
        return self.counters.get(key, 0.0)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value."""
        key = self._make_key(name, labels or {})
        return self.gauges.get(key)
    
    def get_timer_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Dict[str, float]]:
        """Get timer statistics (mean, median, p95, p99)."""
        key = self._make_key(name, labels or {})
        timer_values = self.timers.get(key, [])
        
        if not timer_values:
            return None
        
        sorted_values = sorted(timer_values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "mean": statistics.mean(sorted_values),
            "median": statistics.median(sorted_values),
            "min": min(sorted_values),
            "max": max(sorted_values),
            "p95": sorted_values[int(0.95 * count)] if count > 0 else 0,
            "p99": sorted_values[int(0.99 * count)] if count > 0 else 0,
        }
    
    def get_metrics_by_name(self, name: str) -> List[MetricPoint]:
        """Get all metrics with a specific name."""
        matching_metrics = []
        for key, metric_points in self.metrics.items():
            if key.startswith(name):
                matching_metrics.extend(list(metric_points))
        
        return sorted(matching_metrics, key=lambda x: x.timestamp)
    
    def get_recent_metrics(self, name: str, minutes: int = 5) -> List[MetricPoint]:
        """Get recent metrics within a time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        all_metrics = self.get_metrics_by_name(name)
        
        return [metric for metric in all_metrics if metric.timestamp >= cutoff_time]
    
    def get_all_metrics(self) -> Dict[str, List[MetricPoint]]:
        """Get all metrics."""
        return {key: list(points) for key, points in self.metrics.items()}
    
    def clear_metrics(self, name: Optional[str] = None):
        """Clear metrics, optionally by name."""
        if name:
            keys_to_remove = [key for key in self.metrics.keys() if key.startswith(name)]
            for key in keys_to_remove:
                del self.metrics[key]
                self.counters.pop(key, None)
                self.gauges.pop(key, None)
                self.timers.pop(key, None)
        else:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.timers.clear()
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create a unique key for a metric with labels."""
        if not labels:
            return name
        
        label_parts = [f"{k}={v}" for k, v in sorted(labels.items())]
        return f"{name}{{{','.join(label_parts)}}}"
    
    # Trading-specific metric methods
    
    def record_trade_execution(self, symbol: str, side: str, size: float, price: float, latency: float):
        """Record a trade execution with relevant metrics."""
        labels = {"symbol": symbol, "side": side}
        
        self.increment("trades_total", labels=labels)
        self.record_timer("trade_execution_latency", latency, labels=labels)
        self.set_gauge("last_trade_price", price, labels={"symbol": symbol})
        self.set_gauge("last_trade_size", size, labels=labels)
    
    def record_order_placement(self, symbol: str, order_type: str, latency: float, success: bool):
        """Record order placement metrics."""
        labels = {"symbol": symbol, "order_type": order_type, "success": str(success)}
        
        self.increment("orders_total", labels=labels)
        self.record_timer("order_placement_latency", latency, labels=labels)
    
    def record_strategy_signal(self, strategy: str, symbol: str, signal_type: str, strength: float):
        """Record strategy signal generation."""
        labels = {"strategy": strategy, "symbol": symbol, "signal_type": signal_type}
        
        self.increment("strategy_signals_total", labels=labels)
        self.set_gauge("signal_strength", strength, labels=labels)
    
    def record_position_update(self, symbol: str, size: float, unrealized_pnl: float):
        """Record position updates."""
        labels = {"symbol": symbol}
        
        self.set_gauge("position_size", size, labels=labels)
        self.set_gauge("unrealized_pnl", unrealized_pnl, labels=labels)
    
    def record_risk_check(self, check_type: str, passed: bool, value: float, limit: float):
        """Record risk management checks."""
        labels = {"check_type": check_type, "passed": str(passed)}
        
        self.increment("risk_checks_total", labels=labels)
        self.set_gauge("risk_value", value, labels={"check_type": check_type})
        self.set_gauge("risk_limit", limit, labels={"check_type": check_type})
    
    def record_api_call(self, endpoint: str, method: str, status_code: int, latency: float):
        """Record API call metrics."""
        labels = {
            "endpoint": endpoint, 
            "method": method, 
            "status_code": str(status_code),
            "success": str(200 <= status_code < 300)
        }
        
        self.increment("api_calls_total", labels=labels)
        self.record_timer("api_call_latency", latency, labels=labels)
    
    def record_websocket_event(self, event_type: str, channel: str, processing_time: float):
        """Record WebSocket event processing."""
        labels = {"event_type": event_type, "channel": channel}
        
        self.increment("websocket_events_total", labels=labels)
        self.record_timer("websocket_processing_time", processing_time, labels=labels)
    
    def record_error(self, error_type: str, component: str, severity: str = "error"):
        """Record application errors."""
        labels = {"error_type": error_type, "component": component, "severity": severity}
        
        self.increment("errors_total", labels=labels)
    
    def get_trading_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get a summary of trading metrics."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get recent trades
        recent_trades = []
        for key, points in self.metrics.items():
            if "trades_total" in key:
                recent_points = [p for p in points if p.timestamp >= cutoff_time]
                if recent_points:
                    recent_trades.extend(recent_points)
        
        total_trades = len(recent_trades)
        
        # Get trade latency stats
        latency_stats = self.get_timer_stats("trade_execution_latency")
        
        # Get current positions
        position_metrics = {}
        for key, value in self.gauges.items():
            if "position_size" in key:
                symbol = key.split("symbol=")[1].split("}")[0] if "symbol=" in key else "unknown"
                position_metrics[symbol] = value
        
        return {
            "period_hours": hours,
            "total_trades": total_trades,
            "avg_trade_latency": latency_stats.get("mean", 0) if latency_stats else 0,
            "current_positions": position_metrics,
            "total_api_calls": self.get_counter("api_calls_total"),
            "total_errors": self.get_counter("errors_total"),
            "last_updated": datetime.utcnow().isoformat()
        }


# Timer context manager for easy timing
class MetricTimer:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_timer(self.metric_name, duration, self.labels)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector