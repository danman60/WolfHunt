"""Health check API routes."""

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from typing import Optional, List
import logging

from ..monitoring.health_monitor import get_health_monitor, HealthStatus
from ..monitoring.metrics import get_metrics_collector
from ..monitoring.alerts import get_alert_manager, AlertSeverity
from ..security.auth import get_current_user, User

router = APIRouter(prefix="/api/health", tags=["health"])
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


@router.get("/")
@router.get("/status")
async def get_health_status():
    """Get basic health status (public endpoint)."""
    try:
        health_monitor = get_health_monitor()
        current_health = health_monitor.get_current_health()
        
        if current_health is None:
            # Perform immediate health check if no recent data
            current_health = await health_monitor.perform_health_checks()
        
        # Basic health response without sensitive details
        basic_status = {
            "status": current_health.status.value,
            "timestamp": current_health.timestamp.isoformat(),
            "uptime_seconds": current_health.uptime_seconds,
            "version": current_health.version,
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "response_time": check.response_time
                }
                for check in current_health.checks
            }
        }
        
        return basic_status
        
    except Exception as e:
        logger.error(f"Health status error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": "unknown",
            "error": "Health check system unavailable"
        }


@router.get("/detailed")
async def get_detailed_health(
    current_user: User = Depends(get_current_user)
):
    """Get detailed health status (authenticated endpoint)."""
    try:
        health_monitor = get_health_monitor()
        current_health = health_monitor.get_current_health()
        
        if current_health is None:
            current_health = await health_monitor.perform_health_checks()
        
        # Detailed health response with full check information
        detailed_status = {
            "status": current_health.status.value,
            "timestamp": current_health.timestamp.isoformat(),
            "uptime_seconds": current_health.uptime_seconds,
            "version": current_health.version,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "response_time": check.response_time,
                    "timestamp": check.timestamp.isoformat(),
                    "metadata": check.metadata
                }
                for check in current_health.checks
            ]
        }
        
        return detailed_status
        
    except Exception as e:
        logger.error(f"Detailed health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/history")
async def get_health_history(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Get health check history."""
    try:
        health_monitor = get_health_monitor()
        history = health_monitor.get_health_history(limit)
        
        return {
            "history": [
                {
                    "status": entry.status.value,
                    "timestamp": entry.timestamp.isoformat(),
                    "uptime_seconds": entry.uptime_seconds,
                    "checks": [
                        {
                            "name": check.name,
                            "status": check.status.value,
                            "response_time": check.response_time
                        }
                        for check in entry.checks
                    ]
                }
                for entry in history
            ],
            "total_entries": len(history)
        }
        
    except Exception as e:
        logger.error(f"Health history error: {e}")
        return {"error": str(e)}


@router.get("/metrics")
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
    hours: int = 24
):
    """Get system metrics summary."""
    try:
        metrics_collector = get_metrics_collector()
        trading_summary = metrics_collector.get_trading_summary(hours)
        
        # Get key performance metrics
        api_latency_stats = metrics_collector.get_timer_stats("api_call_latency")
        trade_latency_stats = metrics_collector.get_timer_stats("trade_execution_latency")
        websocket_stats = metrics_collector.get_timer_stats("websocket_processing_time")
        
        return {
            "trading_summary": trading_summary,
            "performance_metrics": {
                "api_latency": api_latency_stats,
                "trade_execution_latency": trade_latency_stats,
                "websocket_processing": websocket_stats
            },
            "current_gauges": {
                "unrealized_pnl": metrics_collector.get_gauge("unrealized_pnl"),
                "position_count": len([k for k in metrics_collector.gauges.keys() if "position_size" in k]),
                "last_trade_price_btc": metrics_collector.get_gauge("last_trade_price", {"symbol": "BTC-USD"}),
                "last_trade_price_eth": metrics_collector.get_gauge("last_trade_price", {"symbol": "ETH-USD"}),
            },
            "counters": {
                "total_trades": metrics_collector.get_counter("trades_total"),
                "total_orders": metrics_collector.get_counter("orders_total"),
                "total_api_calls": metrics_collector.get_counter("api_calls_total"),
                "total_errors": metrics_collector.get_counter("errors_total")
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return {"error": str(e)}


@router.get("/alerts")
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    severity: Optional[str] = None
):
    """Get active alerts."""
    try:
        alert_manager = get_alert_manager()
        
        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity.lower())
            except ValueError:
                pass
        
        active_alerts = alert_manager.get_active_alerts(severity_filter)
        
        return {
            "active_alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "component": alert.component,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata
                }
                for alert in active_alerts
            ],
            "count": len(active_alerts)
        }
        
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        return {"error": str(e)}


@router.get("/alerts/history")
async def get_alert_history(
    current_user: User = Depends(get_current_user),
    hours: int = 24,
    severity: Optional[str] = None
):
    """Get alert history."""
    try:
        alert_manager = get_alert_manager()
        
        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity.lower())
            except ValueError:
                pass
        
        alert_history = alert_manager.get_alert_history(hours, severity_filter)
        
        return {
            "alert_history": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "component": alert.component,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
                }
                for alert in alert_history
            ],
            "period_hours": hours,
            "count": len(alert_history)
        }
        
    except Exception as e:
        logger.error(f"Alert history error: {e}")
        return {"error": str(e)}


@router.get("/alerts/stats")
async def get_alert_stats(
    current_user: User = Depends(get_current_user),
    hours: int = 24
):
    """Get alert statistics."""
    try:
        alert_manager = get_alert_manager()
        stats = alert_manager.get_alert_stats(hours)
        
        return stats
        
    except Exception as e:
        logger.error(f"Alert stats error: {e}")
        return {"error": str(e)}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Resolve an active alert."""
    try:
        alert_manager = get_alert_manager()
        success = alert_manager.resolve_alert(alert_id)
        
        if success:
            return {
                "success": True,
                "message": f"Alert {alert_id} resolved successfully"
            }
        else:
            return {
                "success": False,
                "message": f"Alert {alert_id} not found or already resolved"
            }
            
    except Exception as e:
        logger.error(f"Alert resolution error: {e}")
        return {"error": str(e)}


@router.post("/check")
async def trigger_health_check(
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a health check."""
    try:
        health_monitor = get_health_monitor()
        health_result = await health_monitor.perform_health_checks()
        
        return {
            "success": True,
            "message": "Health check completed",
            "status": health_result.status.value,
            "timestamp": health_result.timestamp.isoformat(),
            "checks_performed": len(health_result.checks)
        }
        
    except Exception as e:
        logger.error(f"Manual health check error: {e}")
        return {"error": str(e)}


@router.get("/readiness")
async def readiness_check():
    """Kubernetes-style readiness check."""
    try:
        health_monitor = get_health_monitor()
        current_health = health_monitor.get_current_health()
        
        if current_health is None or current_health.status == HealthStatus.UNHEALTHY:
            return {"status": "not_ready", "ready": False}
        
        return {"status": "ready", "ready": True}
        
    except Exception:
        return {"status": "not_ready", "ready": False}


@router.get("/liveness")
async def liveness_check():
    """Kubernetes-style liveness check."""
    try:
        health_monitor = get_health_monitor()
        uptime = health_monitor.get_uptime()
        
        # If the service has been running for at least 30 seconds, consider it live
        if uptime > 30:
            return {"status": "alive", "live": True, "uptime_seconds": uptime}
        else:
            return {"status": "starting", "live": True, "uptime_seconds": uptime}
            
    except Exception:
        return {"status": "not_alive", "live": False}