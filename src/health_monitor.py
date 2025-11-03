"""Health monitoring and logging configuration."""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class HealthStatus:
    """System health status snapshot."""
    uptime_seconds: float
    total_signals: int
    long_signals: int
    short_signals: int
    last_data_update: Optional[datetime]
    connection_status: str
    errors_last_hour: int
    email_success_rate: float


class HealthMonitor:
    """
    Monitor system health metrics and provide status reporting.
    
    Tracks uptime, signal counts, connection status, and error rates.
    """
    
    def __init__(self):
        """Initialize health monitor."""
        self.start_time = datetime.now()
        self.long_signal_count = 0
        self.short_signal_count = 0
        self.last_data_update: Optional[datetime] = None
        self.connection_status = "disconnected"
        
        # Error tracking with timestamps
        self.error_history: deque = deque(maxlen=1000)
        
        # Email success rate (will be updated from alerter)
        self.email_success_rate = 0.0
    
    def record_signal(self, signal_type: str) -> None:
        """
        Record a signal generation.
        
        Args:
            signal_type: "LONG" or "SHORT"
        """
        if signal_type == "LONG":
            self.long_signal_count += 1
        elif signal_type == "SHORT":
            self.short_signal_count += 1
    
    def record_error(self, error: Exception) -> None:
        """
        Record an error occurrence.
        
        Args:
            error: Exception that occurred
        """
        self.error_history.append({
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error)
        })
    
    def update_data_timestamp(self, timestamp: datetime) -> None:
        """
        Update last data update timestamp.
        
        Args:
            timestamp: Timestamp of last data update
        """
        self.last_data_update = timestamp
    
    def set_connection_status(self, status: str) -> None:
        """
        Set connection status.
        
        Args:
            status: "connected" or "disconnected"
        """
        self.connection_status = status
    
    def set_email_success_rate(self, rate: float) -> None:
        """
        Set email success rate.
        
        Args:
            rate: Success rate percentage (0-100)
        """
        self.email_success_rate = rate
    
    def get_health_status(self) -> HealthStatus:
        """
        Get current health status snapshot.
        
        Returns:
            HealthStatus object with current metrics
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        errors_last_hour = self._count_errors_last_hour()
        
        return HealthStatus(
            uptime_seconds=uptime,
            total_signals=self.long_signal_count + self.short_signal_count,
            long_signals=self.long_signal_count,
            short_signals=self.short_signal_count,
            last_data_update=self.last_data_update,
            connection_status=self.connection_status,
            errors_last_hour=errors_last_hour,
            email_success_rate=self.email_success_rate
        )
    
    def get_metrics(self) -> Dict:
        """
        Get health metrics as dictionary.
        
        Returns:
            Dictionary with all health metrics
        """
        status = self.get_health_status()
        
        return {
            'uptime_seconds': status.uptime_seconds,
            'uptime_formatted': self._format_uptime(status.uptime_seconds),
            'total_signals': status.total_signals,
            'long_signals': status.long_signals,
            'short_signals': status.short_signals,
            'last_data_update': status.last_data_update.isoformat() if status.last_data_update else None,
            'connection_status': status.connection_status,
            'errors_last_hour': status.errors_last_hour,
            'email_success_rate': f"{status.email_success_rate:.1f}%"
        }
    
    def log_health_summary(self, logger: logging.Logger) -> None:
        """
        Log health summary to logger.
        
        Args:
            logger: Logger instance to use
        """
        metrics = self.get_metrics()
        
        logger.info("=" * 60)
        logger.info("HEALTH SUMMARY")
        logger.info(f"Uptime: {metrics['uptime_formatted']}")
        logger.info(f"Signals: {metrics['total_signals']} (Long: {metrics['long_signals']}, Short: {metrics['short_signals']})")
        logger.info(f"Connection: {metrics['connection_status']}")
        logger.info(f"Last Data Update: {metrics['last_data_update']}")
        logger.info(f"Errors (1h): {metrics['errors_last_hour']}")
        logger.info(f"Email Success Rate: {metrics['email_success_rate']}")
        logger.info("=" * 60)
    
    def _count_errors_last_hour(self) -> int:
        """Count errors in the last hour."""
        cutoff_time = datetime.now() - timedelta(hours=1)
        return sum(1 for err in self.error_history if err['timestamp'] > cutoff_time)
    
    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Format uptime seconds into human-readable string."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


def setup_logging(log_file: str, log_level: str = "INFO", retention_days: int = 7) -> logging.Logger:
    """
    Set up structured logging with rotation.
    
    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        retention_days: Number of days to retain logs
        
    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with daily rotation
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=retention_days,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized: {log_file} (level={log_level}, retention={retention_days} days)")
    
    return logger
