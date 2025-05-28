import asyncio
import logging
import time
import psutil
import gc
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import weakref
from collections import defaultdict, deque
import threading
import json

from app.services.redis_cache import RedisCache
from app.services.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    DATABASE_CONNECTIONS = "database_connections"
    QUERY_TIME = "query_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


@dataclass
class Alert:
    """Performance alert"""
    level: AlertLevel
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    timestamp: datetime
    response_times: Dict[str, float]
    system_metrics: Dict[str, float]
    cache_metrics: Dict[str, float]
    database_metrics: Dict[str, float]
    error_rates: Dict[str, float]
    alerts: List[Alert]
    recommendations: List[str]


class ResponseTimeTracker:
    """Tracks API response times with percentiles"""
    
    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples
        self.samples = deque(maxlen=max_samples)
        self.endpoint_samples = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()
        
    def record(self, endpoint: str, duration: float):
        """Record response time for an endpoint"""
        with self.lock:
            timestamp = time.time()
            self.samples.append((timestamp, duration))
            self.endpoint_samples[endpoint].append((timestamp, duration))
            
    def get_stats(self, window_seconds: int = 300) -> Dict[str, float]:
        """Get response time statistics for the last window_seconds"""
        with self.lock:
            cutoff = time.time() - window_seconds
            recent_samples = [duration for timestamp, duration in self.samples if timestamp >= cutoff]
            
            if not recent_samples:
                return {"count": 0}
                
            return {
                "count": len(recent_samples),
                "mean": statistics.mean(recent_samples),
                "median": statistics.median(recent_samples),
                "p95": self._percentile(recent_samples, 0.95),
                "p99": self._percentile(recent_samples, 0.99),
                "min": min(recent_samples),
                "max": max(recent_samples)
            }
            
    def get_endpoint_stats(self, endpoint: str, window_seconds: int = 300) -> Dict[str, float]:
        """Get stats for a specific endpoint"""
        with self.lock:
            cutoff = time.time() - window_seconds
            samples = self.endpoint_samples.get(endpoint, [])
            recent_samples = [duration for timestamp, duration in samples if timestamp >= cutoff]
            
            if not recent_samples:
                return {"count": 0}
                
            return {
                "count": len(recent_samples),
                "mean": statistics.mean(recent_samples),
                "median": statistics.median(recent_samples),
                "p95": self._percentile(recent_samples, 0.95),
                "p99": self._percentile(recent_samples, 0.99)
            }
            
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]


class SystemMonitor:
    """Monitors system resources"""
    
    def __init__(self):
        self.process = psutil.Process()
        
    def get_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        try:
            # Memory metrics
            memory_info = self.process.memory_info()
            system_memory = psutil.virtual_memory()
            
            # CPU metrics
            cpu_percent = self.process.cpu_percent()
            system_cpu = psutil.cpu_percent(interval=1)
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            
            # Network metrics (if available)
            network_io = psutil.net_io_counters()
            
            return {
                # Process memory
                "process_memory_rss": memory_info.rss / (1024 * 1024),  # MB
                "process_memory_vms": memory_info.vms / (1024 * 1024),  # MB
                "process_memory_percent": self.process.memory_percent(),
                
                # System memory
                "system_memory_total": system_memory.total / (1024 * 1024 * 1024),  # GB
                "system_memory_available": system_memory.available / (1024 * 1024 * 1024),  # GB
                "system_memory_percent": system_memory.percent,
                
                # CPU
                "process_cpu_percent": cpu_percent,
                "system_cpu_percent": system_cpu,
                "cpu_count": psutil.cpu_count(),
                
                # Disk
                "disk_total": disk_usage.total / (1024 * 1024 * 1024),  # GB
                "disk_used": disk_usage.used / (1024 * 1024 * 1024),    # GB
                "disk_percent": (disk_usage.used / disk_usage.total) * 100,
                
                # Network
                "network_bytes_sent": network_io.bytes_sent if network_io else 0,
                "network_bytes_recv": network_io.bytes_recv if network_io else 0,
                
                # Process info
                "open_file_descriptors": self.process.num_fds() if hasattr(self.process, 'num_fds') else 0,
                "threads": self.process.num_threads(),
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}


class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self, cache_manager: CacheManager, redis_cache: RedisCache):
        self.cache_manager = cache_manager
        self.redis_cache = redis_cache
        
        # Monitoring components
        self.response_tracker = ResponseTimeTracker()
        self.system_monitor = SystemMonitor()
        
        # Metrics storage
        self.metrics_history = deque(maxlen=10000)
        self.alerts = deque(maxlen=1000)
        self.active_alerts = {}
        
        # Configuration
        self.thresholds = {
            MetricType.RESPONSE_TIME: {"warning": 100, "critical": 1000},  # ms
            MetricType.MEMORY_USAGE: {"warning": 80, "critical": 95},      # %
            MetricType.CPU_USAGE: {"warning": 80, "critical": 95},        # %
            MetricType.CACHE_HIT_RATE: {"warning": 80, "critical": 60},   # % (lower is worse)
            MetricType.ERROR_RATE: {"warning": 1, "critical": 5},         # %
            MetricType.QUERY_TIME: {"warning": 50, "critical": 200},      # ms
        }
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        self.alert_callbacks = []
        
        # Core Web Vitals tracking
        self.web_vitals = {
            "largest_contentful_paint": deque(maxlen=100),
            "first_input_delay": deque(maxlen=100),
            "cumulative_layout_shift": deque(maxlen=100)
        }
        
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info("Performance monitoring started")
        
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")
        
    async def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        try:
            while self.monitoring_active:
                await self._collect_metrics()
                await self._check_alerts()
                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            
    async def _collect_metrics(self):
        """Collect all performance metrics"""
        timestamp = datetime.utcnow()
        
        try:
            # System metrics
            system_metrics = self.system_monitor.get_metrics()
            
            # Response time metrics
            response_stats = self.response_tracker.get_stats()
            
            # Cache metrics
            cache_stats = await self.cache_manager.get_performance_stats()
            
            # Store metrics
            for metric_name, value in system_metrics.items():
                metric = PerformanceMetric(
                    metric_type=self._map_metric_type(metric_name),
                    value=value,
                    timestamp=timestamp,
                    labels={"source": "system", "metric": metric_name}
                )
                self.metrics_history.append(metric)
                
            # Response time metrics
            if response_stats.get("count", 0) > 0:
                for stat_name, value in response_stats.items():
                    if stat_name != "count":
                        metric = PerformanceMetric(
                            metric_type=MetricType.RESPONSE_TIME,
                            value=value,
                            timestamp=timestamp,
                            labels={"source": "response_time", "stat": stat_name}
                        )
                        self.metrics_history.append(metric)
                        
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            
    async def _check_alerts(self):
        """Check metrics against thresholds and generate alerts"""
        current_time = datetime.utcnow()
        
        # Get recent metrics (last 5 minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if (current_time - m.timestamp).total_seconds() < 300
        ]
        
        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_type[metric.metric_type].append(metric)
            
        # Check each metric type
        for metric_type, metrics in metrics_by_type.items():
            if metric_type in self.thresholds:
                await self._check_metric_threshold(metric_type, metrics)
                
    async def _check_metric_threshold(self, metric_type: MetricType, metrics: List[PerformanceMetric]):
        """Check if metrics exceed thresholds"""
        if not metrics:
            return
            
        # Calculate current value (average of recent metrics)
        current_value = statistics.mean([m.value for m in metrics])
        thresholds = self.thresholds[metric_type]
        
        alert_key = f"{metric_type.value}_threshold"
        
        # Check critical threshold
        if self._is_threshold_exceeded(metric_type, current_value, thresholds["critical"]):
            if alert_key not in self.active_alerts or self.active_alerts[alert_key].level != AlertLevel.CRITICAL:
                alert = Alert(
                    level=AlertLevel.CRITICAL,
                    metric_type=metric_type,
                    message=f"{metric_type.value} critically high: {current_value:.2f}",
                    value=current_value,
                    threshold=thresholds["critical"],
                    timestamp=datetime.utcnow()
                )
                await self._trigger_alert(alert)
                self.active_alerts[alert_key] = alert
                
        # Check warning threshold
        elif self._is_threshold_exceeded(metric_type, current_value, thresholds["warning"]):
            if alert_key not in self.active_alerts:
                alert = Alert(
                    level=AlertLevel.WARNING,
                    metric_type=metric_type,
                    message=f"{metric_type.value} above warning threshold: {current_value:.2f}",
                    value=current_value,
                    threshold=thresholds["warning"],
                    timestamp=datetime.utcnow()
                )
                await self._trigger_alert(alert)
                self.active_alerts[alert_key] = alert
                
        # Resolve alert if threshold is no longer exceeded
        elif alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            del self.active_alerts[alert_key]
            
            # Trigger resolution notification
            resolution_alert = Alert(
                level=AlertLevel.INFO,
                metric_type=metric_type,
                message=f"{metric_type.value} alert resolved: {current_value:.2f}",
                value=current_value,
                threshold=0,
                timestamp=datetime.utcnow()
            )
            await self._trigger_alert(resolution_alert)
            
    def _is_threshold_exceeded(self, metric_type: MetricType, value: float, threshold: float) -> bool:
        """Check if threshold is exceeded (handles inverted metrics like cache hit rate)"""
        if metric_type == MetricType.CACHE_HIT_RATE:
            return value < threshold  # Lower cache hit rate is worse
        else:
            return value > threshold
            
    async def _trigger_alert(self, alert: Alert):
        """Trigger alert and notify callbacks"""
        self.alerts.append(alert)
        
        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }[alert.level]
        
        logger.log(log_level, f"Performance Alert: {alert.message}")
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
                
    def _map_metric_type(self, metric_name: str) -> MetricType:
        """Map metric name to MetricType enum"""
        if "memory" in metric_name:
            return MetricType.MEMORY_USAGE
        elif "cpu" in metric_name:
            return MetricType.CPU_USAGE
        elif "response" in metric_name:
            return MetricType.RESPONSE_TIME
        else:
            return MetricType.THROUGHPUT
            
    def record_response_time(self, endpoint: str, duration_ms: float):
        """Record API response time"""
        self.response_tracker.record(endpoint, duration_ms)
        
    def record_web_vital(self, metric_name: str, value: float):
        """Record Core Web Vital metric"""
        if metric_name in self.web_vitals:
            self.web_vitals[metric_name].append({
                "value": value,
                "timestamp": time.time()
            })
            
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)
        
    async def get_performance_report(self) -> PerformanceReport:
        """Generate comprehensive performance report"""
        current_time = datetime.utcnow()
        
        # Response time stats
        response_stats = self.response_tracker.get_stats()
        
        # System metrics
        system_metrics = self.system_monitor.get_metrics()
        
        # Cache metrics
        cache_stats = await self.cache_manager.get_performance_stats()
        
        # Recent alerts
        recent_alerts = [
            alert for alert in self.alerts
            if (current_time - alert.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(system_metrics, cache_stats, response_stats)
        
        return PerformanceReport(
            timestamp=current_time,
            response_times=response_stats,
            system_metrics=system_metrics,
            cache_metrics=cache_stats,
            database_metrics={},  # Would be populated with actual DB metrics
            error_rates={},       # Would be populated with error tracking
            alerts=recent_alerts,
            recommendations=recommendations
        )
        
    async def _generate_recommendations(self, system_metrics: Dict, cache_stats: Dict, response_stats: Dict) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Memory recommendations
        memory_percent = system_metrics.get("system_memory_percent", 0)
        if memory_percent > 85:
            recommendations.append("High memory usage detected. Consider increasing memory or optimizing cache sizes.")
        elif memory_percent > 70:
            recommendations.append("Memory usage is elevated. Monitor for memory leaks and optimize data structures.")
            
        # Cache recommendations
        for data_type, stats in cache_stats.get("memory_caches", {}).items():
            hit_rate = stats.get("hit_rate", 0)
            if hit_rate < 0.8:
                recommendations.append(f"Low cache hit rate for {data_type} ({hit_rate:.1%}). Consider adjusting TTL or cache size.")
                
        # Response time recommendations
        if response_stats.get("p95", 0) > 200:
            recommendations.append("95th percentile response time is high. Consider optimizing slow endpoints.")
            
        # CPU recommendations
        cpu_percent = system_metrics.get("system_cpu_percent", 0)
        if cpu_percent > 80:
            recommendations.append("High CPU usage. Consider scaling horizontally or optimizing CPU-intensive operations.")
            
        return recommendations
        
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for performance dashboard"""
        current_time = datetime.utcnow()
        
        # Recent metrics (last hour)
        recent_metrics = [
            m for m in self.metrics_history
            if (current_time - m.timestamp).total_seconds() < 3600
        ]
        
        # Group by type and create time series
        time_series = defaultdict(list)
        for metric in recent_metrics:
            time_series[metric.metric_type.value].append({
                "timestamp": metric.timestamp.isoformat(),
                "value": metric.value,
                "labels": metric.labels
            })
            
        # Current system status
        system_metrics = self.system_monitor.get_metrics()
        response_stats = self.response_tracker.get_stats()
        
        # Active alerts
        active_alerts = list(self.active_alerts.values())
        
        # Web Vitals
        web_vitals_summary = {}
        for vital_name, measurements in self.web_vitals.items():
            if measurements:
                recent_measurements = [
                    m["value"] for m in measurements
                    if time.time() - m["timestamp"] < 3600
                ]
                if recent_measurements:
                    web_vitals_summary[vital_name] = {
                        "current": recent_measurements[-1],
                        "p75": self.response_tracker._percentile(recent_measurements, 0.75),
                        "p90": self.response_tracker._percentile(recent_measurements, 0.90)
                    }
                    
        return {
            "timestamp": current_time.isoformat(),
            "system_status": {
                "memory_percent": system_metrics.get("system_memory_percent", 0),
                "cpu_percent": system_metrics.get("system_cpu_percent", 0),
                "disk_percent": system_metrics.get("disk_percent", 0)
            },
            "response_times": response_stats,
            "active_alerts": [asdict(alert) for alert in active_alerts],
            "time_series": dict(time_series),
            "web_vitals": web_vitals_summary,
            "health_status": await self._get_health_status()
        }
        
    async def _get_health_status(self) -> str:
        """Get overall system health status"""
        if len(self.active_alerts) == 0:
            return "healthy"
        elif any(alert.level == AlertLevel.CRITICAL for alert in self.active_alerts.values()):
            return "critical"
        elif any(alert.level == AlertLevel.ERROR for alert in self.active_alerts.values()):
            return "degraded"
        else:
            return "warning"


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


async def get_performance_monitor() -> PerformanceMonitor:
    """Get or create performance monitor instance"""
    global _performance_monitor
    
    if _performance_monitor is None:
        from app.services.cache_manager import get_cache_manager
        from app.services.redis_cache import get_redis_cache
        
        cache_manager = await get_cache_manager()
        redis_cache = await get_redis_cache()
        _performance_monitor = PerformanceMonitor(cache_manager, redis_cache)
        
    return _performance_monitor