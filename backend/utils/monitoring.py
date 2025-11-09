"""
Monitoring and metrics utilities for production deployment.
"""
import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class RequestMetrics:
    """Track request metrics for monitoring."""
    
    def __init__(self, window_minutes: int = 60):
        self.window_minutes = window_minutes
        self.requests = deque()
        self.errors = deque()
        self.response_times = deque()
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "errors": 0,
            "total_time": 0.0
        })
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        error: Optional[str] = None
    ):
        """Record a request."""
        now = time.time()
        
        # Clean old entries
        self._clean_old_entries()
        
        # Record request
        self.requests.append({
            "timestamp": now,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration": duration,
            "error": error
        })
        
        # Track response time
        self.response_times.append(duration)
        
        # Track errors
        if status_code >= 400 or error:
            self.errors.append({
                "timestamp": now,
                "endpoint": endpoint,
                "status_code": status_code,
                "error": error
            })
        
        # Update endpoint stats
        key = f"{method}:{endpoint}"
        self.endpoint_stats[key]["count"] += 1
        self.endpoint_stats[key]["total_time"] += duration
        if status_code >= 400 or error:
            self.endpoint_stats[key]["errors"] += 1
    
    def _clean_old_entries(self):
        """Remove entries outside the time window."""
        cutoff = time.time() - (self.window_minutes * 60)
        
        while self.requests and self.requests[0]["timestamp"] < cutoff:
            self.requests.popleft()
        
        while self.errors and self.errors[0]["timestamp"] < cutoff:
            self.errors.popleft()
        
        while self.response_times and len(self.response_times) > 1000:
            self.response_times.popleft()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        self._clean_old_entries()
        
        total_requests = len(self.requests)
        total_errors = len(self.errors)
        
        # Calculate percentiles for response times
        sorted_times = sorted(self.response_times)
        
        def percentile(p):
            if not sorted_times:
                return 0
            k = (len(sorted_times) - 1) * p
            f = int(k)
            c = f + 1
            if c >= len(sorted_times):
                return sorted_times[f]
            return sorted_times[f] * (c - k) + sorted_times[c] * (k - f)
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "requests_per_minute": total_requests / self.window_minutes,
            "response_time": {
                "p50": percentile(0.50),
                "p95": percentile(0.95),
                "p99": percentile(0.99),
                "mean": sum(sorted_times) / len(sorted_times) if sorted_times else 0
            },
            "endpoint_stats": dict(self.endpoint_stats),
            "window_minutes": self.window_minutes
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status based on metrics."""
        metrics = self.get_metrics()
        error_rate = metrics["error_rate"]
        p95_response_time = metrics["response_time"]["p95"]
        
        # Determine health status
        if error_rate > 0.1 or p95_response_time > 10.0:
            status = "unhealthy"
            issues = []
            if error_rate > 0.1:
                issues.append(f"High error rate: {error_rate:.2%}")
            if p95_response_time > 10.0:
                issues.append(f"High response time: {p95_response_time:.2f}s")
        elif error_rate > 0.05 or p95_response_time > 5.0:
            status = "degraded"
            issues = []
            if error_rate > 0.05:
                issues.append(f"Elevated error rate: {error_rate:.2%}")
            if p95_response_time > 5.0:
                issues.append(f"Elevated response time: {p95_response_time:.2f}s")
        else:
            status = "healthy"
            issues = []
        
        return {
            "status": status,
            "issues": issues,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean old requests
        while self.requests[identifier] and self.requests[identifier][0] < cutoff:
            self.requests[identifier].popleft()
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in window."""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean old requests
        while self.requests[identifier] and self.requests[identifier][0] < cutoff:
            self.requests[identifier].popleft()
        
        return max(0, self.max_requests - len(self.requests[identifier]))
    
    def get_reset_time(self, identifier: str) -> Optional[float]:
        """Get time when rate limit resets."""
        if not self.requests[identifier]:
            return None
        
        oldest = self.requests[identifier][0]
        return oldest + self.window_seconds


# Global instances
request_metrics = RequestMetrics()
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


# ==========================================
# MIDDLEWARE HELPERS
# ==========================================

def track_request(endpoint: str, method: str):
    """Decorator to track request metrics."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                request_metrics.record_request(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    duration=duration,
                    error=error
                )
        
        return wrapper
    return decorator


async def log_system_metrics():
    """Periodically log system metrics."""
    while True:
        try:
            metrics = request_metrics.get_metrics()
            health = request_metrics.get_health_status()
            
            logger.info(f"System Health: {health['status']}")
            logger.info(f"Requests/min: {metrics['requests_per_minute']:.2f}")
            logger.info(f"Error rate: {metrics['error_rate']:.2%}")
            logger.info(f"Response time (p95): {metrics['response_time']['p95']:.2f}s")
            
            if health['issues']:
                logger.warning(f"Health issues: {', '.join(health['issues'])}")
        
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
        
        # Log every 5 minutes
        await asyncio.sleep(300)

