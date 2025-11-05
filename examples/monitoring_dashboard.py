"""
Real-Time Monitoring Dashboard

Simple monitoring dashboard that displays data feed health metrics.

Run with:
    python examples/monitoring_dashboard.py
"""

import os
import time
from datetime import datetime
from alphalens.data.unified_data_manager import UnifiedDataManager
from alphalens.monitoring import DataFeedMonitor, console_alert_handler
from loguru import logger


def display_dashboard(monitor: DataFeedMonitor):
    """Display monitoring dashboard in terminal."""
    # Clear screen (works on Unix/Linux/Mac)
    os.system('clear' if os.name == 'posix' else 'cls')

    dashboard_data = monitor.get_dashboard_data()

    print("=" * 80)
    print(" " * 25 + "DATA FEED HEALTH MONITOR")
    print("=" * 80)
    print(f"\nLast Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Checks Performed: {dashboard_data['stats']['checks_performed']}")
    print(f"Alerts Sent: {dashboard_data['stats']['alerts_sent']}")

    print("\n" + "-" * 80)
    print("CURRENT HEALTH STATUS")
    print("-" * 80)

    # Display current health metrics
    current_health = dashboard_data.get('current_health', {})

    for name, metric_data in current_health.items():
        status = metric_data['status']
        value = metric_data['value']
        message = metric_data.get('message', '')

        # Status symbol
        symbol = {
            'ok': '✓',
            'warning': '⚠',
            'error': '✗'
        }.get(status, '?')

        # Color (basic terminal colors)
        color_start = {
            'ok': '\033[92m',      # Green
            'warning': '\033[93m',  # Yellow
            'error': '\033[91m'     # Red
        }.get(status, '')
        color_end = '\033[0m'

        print(f"{color_start}{symbol} {name:30} {value:8.2f}  {message}{color_end}")

    # Display summary
    print("\n" + "-" * 80)
    print("METRICS SUMMARY")
    print("-" * 80)

    summary = dashboard_data.get('summary', {})
    by_status = summary.get('by_status', {})

    print(f"OK:      {by_status.get('ok', 0):4d}")
    print(f"Warning: {by_status.get('warning', 0):4d}")
    print(f"Error:   {by_status.get('error', 0):4d}")

    print("\n" + "=" * 80)
    print("Press Ctrl+C to exit")
    print("=" * 80)


def run_continuous_monitoring(
    monitor: DataFeedMonitor,
    interval: int = 60,
    display_dashboard_ui: bool = True
):
    """
    Run continuous monitoring with periodic health checks.

    Args:
        monitor: DataFeedMonitor instance
        interval: Check interval in seconds
        display_dashboard_ui: Show live dashboard (terminal only)
    """
    logger.info(f"Starting continuous monitoring (interval: {interval}s)")

    try:
        while True:
            # Perform health check
            metrics = monitor.check_health()

            # Display dashboard
            if display_dashboard_ui:
                display_dashboard(monitor)
            else:
                # Just log status
                logger.info("Health check completed")
                for name, metric in metrics.items():
                    logger.info(f"  {name}: {metric.value:.2f} [{metric.status}]")

            # Export metrics periodically
            monitor.export_metrics()

            # Wait for next check
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user")

    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        raise


def setup_monitoring_with_alerts():
    """Setup monitoring with multiple alert handlers."""
    logger.info("Setting up data feed monitoring...")

    # Create data manager
    data_manager = UnifiedDataManager(
        alpaca_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
        polygon_key=os.getenv("POLYGON_API_KEY"),
        enable_caching=True
    )

    # Create monitor
    monitor = DataFeedMonitor(data_manager)

    # Add console alert handler
    monitor.add_alert_handler(console_alert_handler)

    # Add Slack handler if webhook configured
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook:
        from alphalens.monitoring import slack_alert_handler
        monitor.add_alert_handler(
            lambda alert: slack_alert_handler(alert, slack_webhook)
        )
        logger.info("Slack alerts enabled")
    else:
        logger.info("Slack webhook not configured (set SLACK_WEBHOOK_URL)")

    # Add email handler if SMTP configured
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    alert_emails = os.getenv("ALERT_EMAILS")  # Comma-separated

    if smtp_server and alert_emails:
        from alphalens.monitoring import email_alert_handler
        emails = [e.strip() for e in alert_emails.split(",")]

        def email_handler(alert):
            email_alert_handler(
                alert,
                smtp_server=smtp_server,
                from_email=smtp_user or "alerts@alphalens.local",
                to_emails=emails,
                smtp_user=smtp_user,
                smtp_password=smtp_password
            )

        monitor.add_alert_handler(email_handler)
        logger.info(f"Email alerts enabled (to: {emails})")
    else:
        logger.info("Email alerts not configured")

    return monitor


def main():
    """Run monitoring dashboard."""
    # Setup monitoring
    monitor = setup_monitoring_with_alerts()

    # Run initial health check
    logger.info("Running initial health check...")
    metrics = monitor.check_health()

    logger.info("Initial health status:")
    for name, metric in metrics.items():
        logger.info(f"  {name}: {metric.value:.2f} [{metric.status}] - {metric.message}")

    # Ask user for monitoring mode
    print("\n" + "=" * 80)
    print("Monitoring Options:")
    print("  1. Continuous monitoring with live dashboard (60s interval)")
    print("  2. Single health check and exit")
    print("  3. Continuous monitoring without dashboard (60s interval)")
    print("=" * 80)

    try:
        choice = input("\nSelect option (1-3) [1]: ").strip() or "1"

        if choice == "1":
            logger.info("Starting live dashboard...")
            time.sleep(2)
            run_continuous_monitoring(monitor, interval=60, display_dashboard_ui=True)

        elif choice == "2":
            logger.info("Single health check completed")
            monitor.export_metrics()
            logger.info("Metrics exported to .monitoring/metrics.json")

        elif choice == "3":
            logger.info("Starting background monitoring...")
            run_continuous_monitoring(monitor, interval=60, display_dashboard_ui=False)

        else:
            logger.error("Invalid choice")
            return

    except KeyboardInterrupt:
        logger.info("\nExiting...")

    # Final export
    monitor.export_metrics()
    logger.info("Final metrics exported")


if __name__ == "__main__":
    main()
