"""
Data Feed Health Monitoring and Alerting

Monitors:
- Data feed availability
- API response times
- Error rates
- Data quality
- Cache performance
- Rate limiting

Alerts:
- Email notifications
- Slack webhooks
- Console logging
- Metrics export (Prometheus)
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from loguru import logger

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Health metric data point."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "ok"  # ok, warning, error
    message: Optional[str] = None


@dataclass
class Alert:
    """Alert notification."""
    level: AlertLevel
    source: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


class DataFeedMonitor:
    """
    Monitors data feed health and sends alerts.

    Usage:
        monitor = DataFeedMonitor(data_manager)
        monitor.add_alert_handler(email_handler)
        monitor.add_alert_handler(slack_handler)
        monitor.start_monitoring(interval=60)
    """

    def __init__(
        self,
        data_manager,
        alert_handlers: Optional[List[Callable]] = None,
        metrics_file: str = ".monitoring/metrics.json"
    ):
        """
        Initialize monitor.

        Args:
            data_manager: UnifiedDataManager instance
            alert_handlers: List of alert handler functions
            metrics_file: Path to save metrics
        """
        self.data_manager = data_manager
        self.alert_handlers = alert_handlers or []
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(exist_ok=True)

        # Thresholds
        self.thresholds = {
            "response_time_warning": 2.0,  # seconds
            "response_time_error": 5.0,
            "error_rate_warning": 0.05,  # 5%
            "error_rate_error": 0.20,  # 20%
            "cache_hit_rate_warning": 0.30,  # 30%
        }

        # Metrics history
        self.metrics_history: List[HealthMetric] = []
        self.max_history_size = 10000

        # Statistics
        self.stats = {
            "checks_performed": 0,
            "alerts_sent": 0,
            "last_check": None,
            "last_alert": None,
        }

        logger.info("Data feed monitor initialized")

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add alert handler function."""
        self.alert_handlers.append(handler)

    def check_health(self) -> Dict[str, HealthMetric]:
        """
        Perform comprehensive health check.

        Returns:
            Dictionary of health metrics
        """
        self.stats["checks_performed"] += 1
        self.stats["last_check"] = datetime.now()

        metrics = {}

        # Check data source availability
        metrics.update(self._check_data_sources())

        # Check response times
        metrics.update(self._check_response_times())

        # Check cache performance
        metrics.update(self._check_cache_performance())

        # Check data quality
        metrics.update(self._check_data_quality())

        # Store metrics
        for metric in metrics.values():
            self._record_metric(metric)

        # Check for alerts
        self._evaluate_alerts(metrics)

        return metrics

    def _check_data_sources(self) -> Dict[str, HealthMetric]:
        """Check availability of data sources."""
        metrics = {}

        try:
            health = self.data_manager.health_check()

            for source, status in health.items():
                metric = HealthMetric(
                    name=f"source_{source}_available",
                    value=1.0 if status else 0.0,
                    status="ok" if status else "error",
                    message=f"{source} is {'available' if status else 'unavailable'}"
                )
                metrics[f"source_{source}"] = metric

        except Exception as e:
            logger.error(f"Error checking data sources: {e}")
            metric = HealthMetric(
                name="source_check_error",
                value=0.0,
                status="error",
                message=str(e)
            )
            metrics["source_check"] = metric

        return metrics

    def _check_response_times(self) -> Dict[str, HealthMetric]:
        """Check API response times."""
        metrics = {}

        # Test with a simple query
        try:
            end = datetime.now()
            start = end - timedelta(days=1)

            t1 = time.time()
            df = self.data_manager.get_latest_prices(["SPY"])
            t2 = time.time()

            response_time = t2 - t1

            # Determine status
            if response_time < self.thresholds["response_time_warning"]:
                status = "ok"
            elif response_time < self.thresholds["response_time_error"]:
                status = "warning"
            else:
                status = "error"

            metric = HealthMetric(
                name="api_response_time",
                value=response_time,
                status=status,
                message=f"Response time: {response_time:.2f}s"
            )
            metrics["response_time"] = metric

        except Exception as e:
            logger.error(f"Error checking response time: {e}")
            metric = HealthMetric(
                name="api_response_time",
                value=-1.0,
                status="error",
                message=str(e)
            )
            metrics["response_time"] = metric

        return metrics

    def _check_cache_performance(self) -> Dict[str, HealthMetric]:
        """Check cache performance."""
        metrics = {}

        try:
            stats = self.data_manager.get_cache_stats()

            hit_rate = stats.get("hit_rate", 0.0)

            # Determine status
            if hit_rate >= self.thresholds["cache_hit_rate_warning"]:
                status = "ok"
            else:
                status = "warning"

            metric = HealthMetric(
                name="cache_hit_rate",
                value=hit_rate,
                status=status,
                message=f"Cache hit rate: {hit_rate:.1%}"
            )
            metrics["cache_hit_rate"] = metric

            # Cache size
            metric = HealthMetric(
                name="cache_hits",
                value=float(stats.get("cache_hits", 0)),
                status="ok",
                message=f"Cache hits: {stats.get('cache_hits', 0)}"
            )
            metrics["cache_hits"] = metric

        except Exception as e:
            logger.error(f"Error checking cache: {e}")

        return metrics

    def _check_data_quality(self) -> Dict[str, HealthMetric]:
        """Check data quality."""
        metrics = {}

        try:
            # Fetch recent data
            end = datetime.now()
            start = end - timedelta(days=5)

            df = self.data_manager.get_historical_data(
                symbols=["SPY"],
                start=start,
                end=end,
                timeframe="1Day"
            )

            if df.empty:
                metric = HealthMetric(
                    name="data_quality",
                    value=0.0,
                    status="error",
                    message="No data available"
                )
            else:
                # Check for missing values
                missing_rate = df.isnull().sum().sum() / df.size

                if missing_rate > 0.05:
                    status = "warning"
                else:
                    status = "ok"

                metric = HealthMetric(
                    name="data_quality",
                    value=1.0 - missing_rate,
                    status=status,
                    message=f"Data quality: {(1-missing_rate):.1%}"
                )

            metrics["data_quality"] = metric

        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
            metric = HealthMetric(
                name="data_quality",
                value=0.0,
                status="error",
                message=str(e)
            )
            metrics["data_quality"] = metric

        return metrics

    def _evaluate_alerts(self, metrics: Dict[str, HealthMetric]) -> None:
        """Evaluate metrics and send alerts if needed."""
        for name, metric in metrics.items():
            if metric.status == "error":
                self._send_alert(Alert(
                    level=AlertLevel.ERROR,
                    source=name,
                    message=metric.message or f"Error in {name}",
                    data={"value": metric.value}
                ))
            elif metric.status == "warning":
                self._send_alert(Alert(
                    level=AlertLevel.WARNING,
                    source=name,
                    message=metric.message or f"Warning in {name}",
                    data={"value": metric.value}
                ))

    def _send_alert(self, alert: Alert) -> None:
        """Send alert to all handlers."""
        self.stats["alerts_sent"] += 1
        self.stats["last_alert"] = alert.timestamp

        logger.warning(f"ALERT [{alert.level.value.upper()}] {alert.source}: {alert.message}")

        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def _record_metric(self, metric: HealthMetric) -> None:
        """Record metric in history."""
        self.metrics_history.append(metric)

        # Limit history size
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of recent metrics."""
        if not self.metrics_history:
            return {}

        summary = {
            "total_metrics": len(self.metrics_history),
            "by_status": {},
            "recent_metrics": []
        }

        # Count by status
        for metric in self.metrics_history:
            status = metric.status
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

        # Recent metrics (last 10)
        summary["recent_metrics"] = [
            {
                "name": m.name,
                "value": m.value,
                "status": m.status,
                "timestamp": m.timestamp.isoformat()
            }
            for m in self.metrics_history[-10:]
        ]

        return summary

    def export_metrics(self, filepath: Optional[str] = None) -> None:
        """Export metrics to JSON file."""
        filepath = filepath or str(self.metrics_file)

        data = {
            "exported_at": datetime.now().isoformat(),
            "stats": self.stats,
            "summary": self.get_metrics_summary(),
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "status": m.status,
                    "message": m.message,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.metrics_history[-1000:]  # Last 1000
            ]
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        return {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "current_health": {
                name: {
                    "value": metric.value,
                    "status": metric.status,
                    "message": metric.message
                }
                for name, metric in self.check_health().items()
            },
            "summary": self.get_metrics_summary()
        }


# Alert handlers

def console_alert_handler(alert: Alert) -> None:
    """Print alert to console."""
    symbol = {
        AlertLevel.INFO: "ℹ️",
        AlertLevel.WARNING: "⚠️",
        AlertLevel.ERROR: "❌",
        AlertLevel.CRITICAL: "🚨"
    }.get(alert.level, "•")

    print(f"\n{symbol} [{alert.level.value.upper()}] {alert.timestamp.strftime('%H:%M:%S')}")
    print(f"   Source: {alert.source}")
    print(f"   Message: {alert.message}")
    if alert.data:
        print(f"   Data: {alert.data}")


def email_alert_handler(
    alert: Alert,
    smtp_server: str,
    from_email: str,
    to_emails: List[str],
    smtp_port: int = 587,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None
) -> None:
    """
    Send alert via email.

    Requires: smtplib (standard library)
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # Create message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = f"[{alert.level.value.upper()}] Data Feed Alert: {alert.source}"

    body = f"""
Data Feed Alert

Level: {alert.level.value.upper()}
Source: {alert.source}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{alert.message}

Additional Data:
{json.dumps(alert.data, indent=2)}
"""

    msg.attach(MIMEText(body, "plain"))

    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.send_message(msg)
        server.quit()

        logger.info(f"Email alert sent to {to_emails}")

    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")


def slack_alert_handler(alert: Alert, webhook_url: str) -> None:
    """
    Send alert to Slack via webhook.

    Args:
        alert: Alert to send
        webhook_url: Slack webhook URL
    """
    if not REQUESTS_AVAILABLE:
        logger.error("Requests library required for Slack alerts")
        return

    # Color coding
    color_map = {
        AlertLevel.INFO: "#36a64f",      # green
        AlertLevel.WARNING: "#ff9900",   # orange
        AlertLevel.ERROR: "#ff0000",     # red
        AlertLevel.CRITICAL: "#8b0000"   # dark red
    }

    payload = {
        "attachments": [
            {
                "color": color_map.get(alert.level, "#808080"),
                "title": f"Data Feed Alert: {alert.source}",
                "text": alert.message,
                "fields": [
                    {
                        "title": "Level",
                        "value": alert.level.value.upper(),
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        "short": True
                    }
                ],
                "footer": "Alphalens Data Feed Monitor",
                "ts": int(alert.timestamp.timestamp())
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            logger.info("Slack alert sent")
        else:
            logger.error(f"Slack alert failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")


# Example usage

if __name__ == "__main__":
    import os
    from alphalens.data.unified_data_manager import UnifiedDataManager

    # Create data manager
    data_manager = UnifiedDataManager(
        alpaca_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
        polygon_key=os.getenv("POLYGON_API_KEY")
    )

    # Create monitor
    monitor = DataFeedMonitor(data_manager)

    # Add console handler
    monitor.add_alert_handler(console_alert_handler)

    # Add Slack handler (if webhook configured)
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook:
        monitor.add_alert_handler(
            lambda alert: slack_alert_handler(alert, slack_webhook)
        )

    # Run health check
    logger.info("Running health check...")
    metrics = monitor.check_health()

    logger.info(f"\nHealth Check Results:")
    for name, metric in metrics.items():
        logger.info(f"  {name}: {metric.value:.2f} [{metric.status}] - {metric.message}")

    # Export metrics
    monitor.export_metrics()

    # Show summary
    summary = monitor.get_metrics_summary()
    logger.info(f"\nMetrics Summary:")
    logger.info(f"  Total metrics: {summary.get('total_metrics', 0)}")
    logger.info(f"  By status: {summary.get('by_status', {})}")
