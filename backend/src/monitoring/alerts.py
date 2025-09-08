"""Alert management and notification system."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from urllib.parse import urlencode
import aiohttp

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    component: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    component: str
    message_template: str
    cooldown_minutes: int = 60
    channels: List[AlertChannel] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = [AlertChannel.EMAIL]


class AlertManager:
    """Manages alert generation, notification, and tracking."""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: Dict[str, AlertRule] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        self.max_history_size = 1000
        
        # Initialize default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default alert rules for the trading bot."""
        
        # Database connectivity alert
        self.add_rule(AlertRule(
            name="database_unhealthy",
            condition=lambda data: data.get("database_status") == "unhealthy",
            severity=AlertSeverity.CRITICAL,
            component="database",
            message_template="Database connection is unhealthy: {message}",
            cooldown_minutes=5,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
        ))
        
        # API connectivity alert
        self.add_rule(AlertRule(
            name="api_unhealthy",
            condition=lambda data: data.get("api_status") == "unhealthy",
            severity=AlertSeverity.ERROR,
            component="api",
            message_template="dYdX API is unhealthy: {message}",
            cooldown_minutes=10,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
        ))
        
        # High latency alert
        self.add_rule(AlertRule(
            name="high_api_latency",
            condition=lambda data: data.get("api_latency", 0) > 3.0,
            severity=AlertSeverity.WARNING,
            component="api",
            message_template="High API latency detected: {api_latency:.2f}s",
            cooldown_minutes=30
        ))
        
        # Daily loss limit alert
        self.add_rule(AlertRule(
            name="daily_loss_limit",
            condition=lambda data: data.get("daily_pnl", 0) < data.get("daily_loss_limit", 0),
            severity=AlertSeverity.CRITICAL,
            component="risk",
            message_template="Daily loss limit breached: ${daily_pnl:.2f} (limit: ${daily_loss_limit:.2f})",
            cooldown_minutes=60,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.SMS]
        ))
        
        # Position size alert
        self.add_rule(AlertRule(
            name="large_position",
            condition=lambda data: data.get("position_size_percent", 0) > 10,
            severity=AlertSeverity.WARNING,
            component="risk",
            message_template="Large position detected: {position_size_percent:.1f}% of portfolio in {symbol}",
            cooldown_minutes=120
        ))
        
        # System resource alert
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            condition=lambda data: data.get("cpu_percent", 0) > 90,
            severity=AlertSeverity.WARNING,
            component="system",
            message_template="High CPU usage: {cpu_percent:.1f}%",
            cooldown_minutes=30
        ))
        
        # Memory usage alert
        self.add_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda data: data.get("memory_percent", 0) > 90,
            severity=AlertSeverity.WARNING,
            component="system",
            message_template="High memory usage: {memory_percent:.1f}%",
            cooldown_minutes=30
        ))
        
        # Error rate alert
        self.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda data: data.get("error_rate", 0) > 0.1,
            severity=AlertSeverity.ERROR,
            component="application",
            message_template="High error rate detected: {error_rate:.2%}",
            cooldown_minutes=15
        ))
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove an alert rule."""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
            return True
        return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable an alert rule."""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable an alert rule."""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = False
            return True
        return False
    
    async def check_rules(self, data: Dict[str, Any]):
        """Check all alert rules against provided data."""
        current_time = datetime.utcnow()
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Check cooldown period
                last_alert_time = self.last_alert_times.get(rule_name)
                if last_alert_time and (current_time - last_alert_time).total_seconds() < rule.cooldown_minutes * 60:
                    continue
                
                # Evaluate condition
                if rule.condition(data):
                    alert_id = f"{rule_name}_{current_time.strftime('%Y%m%d_%H%M%S')}"
                    
                    # Format message
                    message = rule.message_template.format(**data)
                    
                    # Create alert
                    alert = Alert(
                        id=alert_id,
                        title=f"{rule.component.title()} Alert: {rule_name}",
                        message=message,
                        severity=rule.severity,
                        component=rule.component,
                        timestamp=current_time,
                        metadata={"rule_name": rule_name, "data": data}
                    )
                    
                    # Store alert
                    self.active_alerts[alert_id] = alert
                    self.alert_history.append(alert)
                    self.last_alert_times[rule_name] = current_time
                    
                    # Trim history if needed
                    if len(self.alert_history) > self.max_history_size:
                        self.alert_history = self.alert_history[-self.max_history_size:]
                    
                    # Send notifications
                    await self._send_notifications(alert, rule.channels)
                    
                    logger.warning(f"Alert triggered: {alert.title} - {alert.message}")
                    
            except Exception as e:
                logger.error(f"Error checking rule {rule_name}: {e}")
    
    async def _send_notifications(self, alert: Alert, channels: List[AlertChannel]):
        """Send alert notifications through specified channels."""
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email_notification(alert)
                elif channel == AlertChannel.SLACK:
                    await self._send_slack_notification(alert)
                elif channel == AlertChannel.SMS:
                    await self._send_sms_notification(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_notification(alert)
            except Exception as e:
                logger.error(f"Failed to send {channel.value} notification: {e}")
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification."""
        if not settings.email_enabled:
            logger.debug("Email notifications disabled")
            return
        
        # Email configuration from settings
        smtp_server = settings.smtp_server
        smtp_port = settings.smtp_port
        smtp_username = settings.smtp_username
        smtp_password = settings.smtp_password
        from_email = settings.from_email
        to_emails = settings.alert_emails
        
        if not all([smtp_server, smtp_username, smtp_password, from_email, to_emails]):
            logger.warning("Email configuration incomplete")
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert.severity.upper()}] {alert.title}"
            
            # Email body
            body = f"""
            Alert Details:
            
            Title: {alert.title}
            Severity: {alert.severity.upper()}
            Component: {alert.component}
            Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            Message:
            {alert.message}
            
            Metadata:
            {json.dumps(alert.metadata, indent=2) if alert.metadata else 'None'}
            
            ---
            dYdX Trading Bot Alert System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent for alert {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification."""
        slack_webhook_url = settings.slack_webhook_url
        
        if not slack_webhook_url:
            logger.debug("Slack webhook URL not configured")
            return
        
        # Color based on severity
        color_map = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning", 
            AlertSeverity.ERROR: "danger",
            AlertSeverity.CRITICAL: "danger"
        }
        
        # Create Slack message
        payload = {
            "username": "Trading Bot Alerts",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "warning"),
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Component", 
                            "value": alert.component,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                            "short": False
                        }
                    ],
                    "timestamp": int(alert.timestamp.timestamp())
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(slack_webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert {alert.id}")
                    else:
                        logger.error(f"Slack notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_sms_notification(self, alert: Alert):
        """Send SMS notification (placeholder - implement with SMS service)."""
        # This would integrate with services like Twilio, AWS SNS, etc.
        logger.info(f"SMS notification would be sent for alert {alert.id}")
        
        # Example implementation with Twilio:
        # twilio_client = Client(account_sid, auth_token)
        # message = twilio_client.messages.create(
        #     body=f"{alert.title}: {alert.message}",
        #     from_=twilio_phone_number,
        #     to=alert_phone_number
        # )
    
    async def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification."""
        webhook_url = settings.alert_webhook_url
        
        if not webhook_url:
            logger.debug("Webhook URL not configured")
            return
        
        try:
            payload = alert.to_dict()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"Webhook notification sent for alert {alert.id}")
                    else:
                        logger.error(f"Webhook notification failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_history(self, hours: int = 24, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get alert history within a time window."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics."""
        recent_alerts = self.get_alert_history(hours)
        
        severity_counts = {}
        component_counts = {}
        
        for alert in recent_alerts:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            component_counts[alert.component] = component_counts.get(alert.component, 0) + 1
        
        return {
            "period_hours": hours,
            "total_alerts": len(recent_alerts),
            "active_alerts": len(self.active_alerts),
            "severity_breakdown": severity_counts,
            "component_breakdown": component_counts,
            "last_updated": datetime.utcnow().isoformat()
        }


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager