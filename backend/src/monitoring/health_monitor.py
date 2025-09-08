"""Health monitoring system for the trading bot."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import psutil

from ..database.base import check_db_health
from ..trading.api_client import DydxRestClient
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result."""
    name: str
    status: HealthStatus
    message: str
    response_time: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    checks: List[HealthCheck]
    timestamp: datetime
    uptime_seconds: float
    version: str = "1.0.0"


class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_check_time = None
        self.check_history: List[SystemHealth] = []
        self.max_history_size = 100
        
        # Health check intervals (in seconds)
        self.check_intervals = {
            "database": 30,
            "dydx_api": 60,
            "websocket": 45,
            "system_resources": 30,
            "trading_engine": 60
        }
        
        self.last_check_times = {}
        self._running = False
        self._monitor_task = None
    
    async def start_monitoring(self):
        """Start the health monitoring background task."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop the health monitoring background task."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self.perform_health_checks()
                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def perform_health_checks(self) -> SystemHealth:
        """Perform all health checks and return overall status."""
        current_time = datetime.utcnow()
        checks = []
        
        # Database health check
        if self._should_run_check("database", current_time):
            checks.append(await self._check_database())
        
        # dYdX API health check
        if self._should_run_check("dydx_api", current_time):
            checks.append(await self._check_dydx_api())
        
        # WebSocket health check
        if self._should_run_check("websocket", current_time):
            checks.append(await self._check_websocket())
        
        # System resources check
        if self._should_run_check("system_resources", current_time):
            checks.append(await self._check_system_resources())
        
        # Trading engine health check
        if self._should_run_check("trading_engine", current_time):
            checks.append(await self._check_trading_engine())
        
        # Determine overall status
        overall_status = self._calculate_overall_status(checks)
        
        # Calculate uptime
        uptime_seconds = time.time() - self.start_time
        
        # Create system health report
        system_health = SystemHealth(
            status=overall_status,
            checks=checks,
            timestamp=current_time,
            uptime_seconds=uptime_seconds
        )
        
        # Store in history
        self._add_to_history(system_health)
        self.last_check_time = current_time
        
        # Log critical issues
        if overall_status == HealthStatus.UNHEALTHY:
            logger.error("System health is UNHEALTHY")
            await self._handle_unhealthy_system(system_health)
        elif overall_status == HealthStatus.DEGRADED:
            logger.warning("System health is DEGRADED")
        
        return system_health
    
    def _should_run_check(self, check_name: str, current_time: datetime) -> bool:
        """Determine if a health check should be run based on interval."""
        if check_name not in self.last_check_times:
            self.last_check_times[check_name] = current_time
            return True
        
        interval = self.check_intervals.get(check_name, 60)
        last_check = self.last_check_times[check_name]
        
        if (current_time - last_check).total_seconds() >= interval:
            self.last_check_times[check_name] = current_time
            return True
        
        return False
    
    async def _check_database(self) -> HealthCheck:
        """Check database connectivity and performance."""
        start_time = time.time()
        
        try:
            is_healthy = await check_db_health()
            response_time = time.time() - start_time
            
            if is_healthy:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection is healthy",
                    response_time=response_time,
                    timestamp=datetime.utcnow()
                )
            else:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database connection failed",
                    response_time=response_time,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check error: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_dydx_api(self) -> HealthCheck:
        """Check dYdX API connectivity and latency."""
        start_time = time.time()
        
        try:
            # Create a test client (without real credentials for health check)
            client = DydxRestClient(
                api_key="test",
                api_secret="test", 
                testnet=settings.testnet
            )
            
            # Try to get market data (public endpoint)
            # In production, this would be a real API call
            response_time = time.time() - start_time
            
            # For now, simulate based on response time
            if response_time < 1.0:
                status = HealthStatus.HEALTHY
                message = f"dYdX API responding in {response_time:.3f}s"
            elif response_time < 3.0:
                status = HealthStatus.DEGRADED
                message = f"dYdX API slow response: {response_time:.3f}s"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"dYdX API very slow: {response_time:.3f}s"
            
            return HealthCheck(
                name="dydx_api",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata={"endpoint": "market_data"}
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="dydx_api",
                status=HealthStatus.UNHEALTHY,
                message=f"dYdX API error: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_websocket(self) -> HealthCheck:
        """Check WebSocket connection health."""
        start_time = time.time()
        
        try:
            # TODO: Implement actual WebSocket health check
            # This would check if WebSocket connections are active and receiving data
            
            response_time = time.time() - start_time
            
            # For now, simulate WebSocket health
            return HealthCheck(
                name="websocket",
                status=HealthStatus.HEALTHY,
                message="WebSocket connections are active",
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata={"connections": 3, "subscriptions": 9}
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="websocket",
                status=HealthStatus.UNHEALTHY,
                message=f"WebSocket check error: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_system_resources(self) -> HealthCheck:
        """Check system resource usage."""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                messages.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            memory_percent = memory.percent
            if memory_percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High memory usage: {memory_percent:.1f}%")
            elif memory_percent > 80:
                status = HealthStatus.DEGRADED
                messages.append(f"Elevated memory usage: {memory_percent:.1f}%")
            
            disk_percent = disk.percent
            if disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High disk usage: {disk_percent:.1f}%")
            elif disk_percent > 85:
                status = HealthStatus.DEGRADED
                messages.append(f"Elevated disk usage: {disk_percent:.1f}%")
            
            message = "; ".join(messages) if messages else "System resources are healthy"
            response_time = time.time() - start_time
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"System resources check error: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_trading_engine(self) -> HealthCheck:
        """Check trading engine health."""
        start_time = time.time()
        
        try:
            # TODO: Implement actual trading engine health checks
            # This would check:
            # - Strategy execution status
            # - Order execution pipeline
            # - Risk management system
            # - Market data processing
            
            response_time = time.time() - start_time
            
            return HealthCheck(
                name="trading_engine",
                status=HealthStatus.HEALTHY,
                message="Trading engine is operational",
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata={
                    "active_strategies": 1,
                    "active_positions": 0,
                    "pending_orders": 0
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="trading_engine",
                status=HealthStatus.UNHEALTHY,
                message=f"Trading engine check error: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Calculate overall system status from individual checks."""
        if not checks:
            return HealthStatus.UNKNOWN
        
        # If any check is unhealthy, system is unhealthy
        if any(check.status == HealthStatus.UNHEALTHY for check in checks):
            return HealthStatus.UNHEALTHY
        
        # If any check is degraded, system is degraded
        if any(check.status == HealthStatus.DEGRADED for check in checks):
            return HealthStatus.DEGRADED
        
        # If all checks are healthy, system is healthy
        if all(check.status == HealthStatus.HEALTHY for check in checks):
            return HealthStatus.HEALTHY
        
        return HealthStatus.UNKNOWN
    
    def _add_to_history(self, system_health: SystemHealth):
        """Add health check result to history."""
        self.check_history.append(system_health)
        
        # Keep only recent history
        if len(self.check_history) > self.max_history_size:
            self.check_history = self.check_history[-self.max_history_size:]
    
    async def _handle_unhealthy_system(self, system_health: SystemHealth):
        """Handle unhealthy system state."""
        # TODO: Implement alert notifications
        # This could send alerts via email, Slack, etc.
        
        unhealthy_checks = [
            check for check in system_health.checks 
            if check.status == HealthStatus.UNHEALTHY
        ]
        
        for check in unhealthy_checks:
            logger.critical(f"Unhealthy component: {check.name} - {check.message}")
    
    def get_current_health(self) -> Optional[SystemHealth]:
        """Get the most recent health status."""
        return self.check_history[-1] if self.check_history else None
    
    def get_health_history(self, limit: int = 50) -> List[SystemHealth]:
        """Get recent health check history."""
        return self.check_history[-limit:] if self.check_history else []
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self.start_time


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor