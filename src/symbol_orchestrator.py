"""
Symbol Orchestrator
Manages multiple symbol scanners and coordinates signal filtering.
"""
import logging
import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.symbol_scanner import SymbolScanner
from src.signal_filter import SignalFilter
from src.trade_tracker import TradeTracker
from src.asset_config_manager import AssetConfigManager
from src.signal_detector import Signal


logger = logging.getLogger(__name__)


class SymbolOrchestrator:
    """Manages multiple symbol scanners and coordinates signal filtering."""
    
    def __init__(
        self,
        config_manager: AssetConfigManager,
        alerter: Any,
        max_concurrent_symbols: int = 10
    ):
        """
        Initialize orchestrator.
        
        Args:
            config_manager: Asset configuration manager
            alerter: Alerter instance for sending notifications
            max_concurrent_symbols: Maximum number of symbols to scan concurrently
        """
        self.config_manager = config_manager
        self.alerter = alerter
        self.max_concurrent_symbols = max_concurrent_symbols
        
        # Core components
        self.signal_filter = SignalFilter(
            conflict_window_minutes=config_manager.get_global_setting('signal_conflict_window_minutes', 5),
            duplicate_window_minutes=config_manager.get_global_setting('duplicate_signal_window_minutes', 10)
        )
        
        self.trade_tracker = TradeTracker(
            alerter=alerter,
            grace_period_minutes=5,
            min_profit_threshold_crypto=1.0,
            min_profit_threshold_fx=0.3
        )
        
        # Symbol scanners
        self.scanners: Dict[str, SymbolScanner] = {}
        self.scanner_threads: Dict[str, threading.Thread] = {}
        
        # Control flags
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Statistics
        self.total_signals = 0
        self.suppressed_signals = 0
        self.start_time: Optional[datetime] = None
        
        # Error tracking
        self.error_tracker: Dict[str, Dict[str, Any]] = {}
        self.last_admin_alert_time: Dict[str, datetime] = {}
        self.admin_alert_cooldown_minutes = 30
        
        # Performance metrics
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}  # symbol -> metrics
        self.last_metrics_log_time: Optional[datetime] = None
        
        logger.info(f"Initialized SymbolOrchestrator (max_concurrent={max_concurrent_symbols})")
    
    def add_symbol(self, symbol: str) -> bool:
        """
        Add a symbol scanner.
        
        Args:
            symbol: Symbol identifier
            
        Returns:
            True if added successfully
        """
        try:
            # Get symbol configuration
            config = self.config_manager.get_symbol_config(symbol)
            if not config:
                logger.error(f"No configuration found for {symbol}")
                return False
            
            if not config.get('enabled', False):
                logger.info(f"Symbol {symbol} is disabled, skipping")
                return False
            
            # Check concurrent limit
            if len(self.scanners) >= self.max_concurrent_symbols:
                logger.warning(f"Max concurrent symbols reached ({self.max_concurrent_symbols}), cannot add {symbol}")
                return False
            
            # Create scanner
            scanner = SymbolScanner(
                symbol=symbol,
                asset_type=config.get('asset_type', 'crypto'),
                display_name=config.get('display_name', symbol),
                emoji=config.get('emoji', '📊'),
                timeframes=config.get('timeframes', ['5m', '15m']),
                asset_config=config,
                signal_callback=self._on_signal_detected,
                polling_interval=self.config_manager.get_global_setting('polling_interval_seconds', 60)
            )
            
            self.scanners[symbol] = scanner
            logger.info(f"Added scanner for {config.get('display_name', symbol)} ({symbol})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add symbol {symbol}: {e}")
            return False
    
    def remove_symbol(self, symbol: str) -> bool:
        """
        Remove a symbol scanner.
        
        Args:
            symbol: Symbol identifier
            
        Returns:
            True if removed successfully
        """
        try:
            if symbol not in self.scanners:
                logger.warning(f"Symbol {symbol} not found")
                return False
            
            # Stop scanner if running
            if symbol in self.scanner_threads:
                self.scanners[symbol].stop()
                self.scanner_threads[symbol].join(timeout=5)
                del self.scanner_threads[symbol]
            
            # Remove scanner
            del self.scanners[symbol]
            logger.info(f"Removed scanner for {symbol}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove symbol {symbol}: {e}")
            return False
    
    def start(self) -> None:
        """Start all symbol scanners."""
        try:
            self.running = True
            self.start_time = datetime.now()
            
            logger.info("=" * 60)
            logger.info("Starting Symbol Orchestrator")
            logger.info(f"Symbols to scan: {len(self.scanners)}")
            logger.info("=" * 60)
            
            # Connect all scanners
            for symbol, scanner in self.scanners.items():
                logger.info(f"Connecting {scanner.display_name}...")
                if not scanner.connect():
                    logger.error(f"Failed to connect {symbol}, skipping")
                    continue
                
                # Fetch initial data
                if not scanner.fetch_initial_data():
                    logger.error(f"Failed to fetch initial data for {symbol}")
                    continue
                
                # Stagger startup (1 second delay between symbols)
                time.sleep(1)
            
            # Start scanner threads
            for symbol, scanner in self.scanners.items():
                if scanner.market_client.is_connected():
                    thread = threading.Thread(
                        target=scanner.run,
                        name=f"Scanner-{symbol}",
                        daemon=True
                    )
                    thread.start()
                    self.scanner_threads[symbol] = thread
                    logger.info(f"Started scanner thread for {scanner.display_name}")
            
            # Send startup notification
            if self.alerter:
                self._send_startup_notification()
            
            logger.info(f"All scanners started ({len(self.scanner_threads)} active)")
            
        except Exception as e:
            logger.error(f"Error starting orchestrator: {e}")
            raise
    
    def _monitor_symbol_health(self) -> None:
        """Monitor symbol health and send admin alerts for issues."""
        for symbol, scanner in self.scanners.items():
            # Update error tracker
            if symbol not in self.error_tracker:
                self.error_tracker[symbol] = {
                    'consecutive_errors': 0,
                    'total_errors': 0,
                    'is_paused': False,
                    'last_check': datetime.now()
                }
            
            tracker = self.error_tracker[symbol]
            tracker['consecutive_errors'] = scanner.consecutive_errors
            tracker['total_errors'] = scanner.error_count
            tracker['is_paused'] = scanner.paused
            tracker['last_check'] = datetime.now()
            
            # Send admin alert if symbol is paused and cooldown has passed
            if scanner.paused:
                last_alert = self.last_admin_alert_time.get(symbol)
                now = datetime.now()
                
                if last_alert is None or (now - last_alert).total_seconds() > self.admin_alert_cooldown_minutes * 60:
                    self._send_admin_alert(symbol, scanner)
                    self.last_admin_alert_time[symbol] = now
    
    def _send_admin_alert(self, symbol: str, scanner: SymbolScanner) -> None:
        """
        Send admin alert for disabled/paused symbol.
        
        Args:
            symbol: Symbol identifier
            scanner: Scanner instance
        """
        try:
            message = f"⚠️ ADMIN ALERT: Scanner Paused\n\n"
            message += f"Symbol: {scanner.emoji} {scanner.display_name} ({symbol})\n"
            message += f"Reason: {scanner.pause_reason}\n"
            message += f"Consecutive Errors: {scanner.consecutive_errors}\n"
            message += f"Total Errors: {scanner.error_count}\n"
            message += f"Backoff Time: {scanner.reconnect_backoff}s\n\n"
            message += f"The scanner will attempt automatic reconnection.\n"
            message += f"If issues persist, check symbol availability and configuration."
            
            if self.alerter:
                self.alerter.send_alert(message)
                logger.info(f"Sent admin alert for {symbol}")
        except Exception as e:
            logger.error(f"Error sending admin alert for {symbol}: {e}")
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics for all symbols."""
        import json
        from pathlib import Path
        
        for symbol, scanner in self.scanners.items():
            if symbol not in self.performance_metrics:
                self.performance_metrics[symbol] = {
                    'scan_count': 0,
                    'signal_count': 0,
                    'total_scan_duration': 0.0,
                    'avg_scan_duration': 0.0
                }
            
            metrics = self.performance_metrics[symbol]
            metrics['scan_count'] = scanner.scan_count
            metrics['error_count'] = scanner.error_count
            metrics['consecutive_errors'] = scanner.consecutive_errors
            metrics['is_paused'] = scanner.paused
            metrics['last_scan_time'] = scanner.last_scan_time.isoformat() if scanner.last_scan_time else None
        
        # Log metrics every hour
        now = datetime.now()
        if self.last_metrics_log_time is None or (now - self.last_metrics_log_time).total_seconds() > 3600:
            self._log_performance_summary()
            self.last_metrics_log_time = now
        
        # Write health check file
        self._write_health_check_file()
    
    def _log_performance_summary(self) -> None:
        """Log performance summary statistics."""
        if not self.start_time:
            return
        
        uptime = datetime.now() - self.start_time
        uptime_hours = uptime.total_seconds() / 3600
        
        logger.info("=" * 60)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Uptime: {uptime_hours:.2f} hours")
        logger.info(f"Total Signals: {self.total_signals}")
        logger.info(f"Suppressed Signals: {self.suppressed_signals}")
        logger.info(f"Signals per Hour: {self.total_signals / uptime_hours:.2f}" if uptime_hours > 0 else "N/A")
        
        logger.info("\nPer-Symbol Statistics:")
        for symbol, metrics in self.performance_metrics.items():
            scanner = self.scanners.get(symbol)
            if scanner:
                logger.info(f"  {scanner.display_name} ({symbol}):")
                logger.info(f"    Scans: {metrics['scan_count']}")
                logger.info(f"    Errors: {metrics['error_count']} (consecutive: {metrics['consecutive_errors']})")
                logger.info(f"    Status: {'PAUSED' if metrics['is_paused'] else 'ACTIVE'}")
        
        logger.info("=" * 60)
    
    def _write_health_check_file(self) -> None:
        """Write health check status to JSON file."""
        import json
        from pathlib import Path
        
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                'total_signals': self.total_signals,
                'suppressed_signals': self.suppressed_signals,
                'active_scanners': len([s for s in self.scanners.values() if not s.paused]),
                'paused_scanners': len([s for s in self.scanners.values() if s.paused]),
                'symbols': {}
            }
            
            for symbol, scanner in self.scanners.items():
                health_data['symbols'][symbol] = {
                    'display_name': scanner.display_name,
                    'status': 'PAUSED' if scanner.paused else 'ACTIVE',
                    'scan_count': scanner.scan_count,
                    'error_count': scanner.error_count,
                    'consecutive_errors': scanner.consecutive_errors,
                    'last_scan_time': scanner.last_scan_time.isoformat() if scanner.last_scan_time else None,
                    'pause_reason': scanner.pause_reason if scanner.paused else None
                }
            
            health_file = log_dir / "scanner_health.json"
            with open(health_file, 'w') as f:
                json.dump(health_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error writing health check file: {e}")
    
    def stop(self) -> None:
        """Stop all symbol scanners gracefully."""
        try:
            logger.info("Stopping Symbol Orchestrator...")
            
            self.running = False
            self.shutdown_event.set()
            
            # Stop all scanners
            for symbol, scanner in self.scanners.items():
                scanner.stop()
            
            # Wait for threads to finish
            for symbol, thread in self.scanner_threads.items():
                logger.info(f"Waiting for {symbol} scanner to stop...")
                thread.join(timeout=10)
            
            # Send shutdown notification
            if self.alerter:
                self._send_shutdown_notification()
            
            logger.info("Symbol Orchestrator stopped")
            
        except Exception as e:
            logger.error(f"Error stopping orchestrator: {e}")
    
    def _on_signal_detected(self, symbol: str, signal: Signal) -> None:
        """
        Handle signal from a symbol scanner.
        Applies filtering before sending alerts.
        
        Args:
            symbol: Symbol that generated the signal
            signal: Detected signal
        """
        try:
            self.total_signals += 1
            
            logger.info(f"Signal received: {symbol} {signal.timeframe} {signal.signal_type} at ${signal.entry_price:.2f}")
            
            # Apply signal filter
            should_suppress, reason = self.signal_filter.should_suppress_signal(symbol, signal)
            
            if should_suppress:
                self.suppressed_signals += 1
                logger.info(f"Signal suppressed: {reason}")
                return
            
            # Signal passed filters - add to history
            self.signal_filter.add_signal_to_history(symbol, signal)
            
            # Set as active trade
            self.signal_filter.set_active_trade(symbol, signal)
            
            # Add to trade tracker
            self.trade_tracker.add_trade(signal, symbol)
            
            # Send alert
            if self.alerter:
                self.alerter.send_signal_alert(signal)
                logger.info(f"Alert sent for {symbol} {signal.signal_type}")
            
        except Exception as e:
            logger.error(f"Error handling signal for {symbol}: {e}")
    
    def update_trades(self) -> None:
        """Update all active trades with current prices."""
        try:
            for symbol, scanner in self.scanners.items():
                current_price = scanner.get_current_price()
                if current_price:
                    # Get indicators for exit logic
                    # For now, pass empty dict - can be enhanced later
                    indicators = {}
                    self.trade_tracker.update_trades(current_price, indicators)
                    
        except Exception as e:
            logger.error(f"Error updating trades: {e}")
    
    def _send_startup_notification(self) -> None:
        """Send startup notification."""
        try:
            symbols_list = [
                f"{scanner.emoji} {scanner.display_name}"
                for scanner in self.scanners.values()
            ]
            
            message = f"""
🚀 <b>Multi-Symbol Scanner Started</b>

📊 <b>Active Symbols ({len(self.scanners)}):</b>
{chr(10).join(symbols_list)}

⏰ Polling Interval: {self.config_manager.get_global_setting('polling_interval_seconds', 60)}s
🔍 Scanning for high-probability setups...

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
            
            self.alerter.send_message(message)
            
        except Exception as e:
            logger.warning(f"Failed to send startup notification: {e}")
    
    def _send_shutdown_notification(self) -> None:
        """Send shutdown notification."""
        try:
            runtime = datetime.now() - self.start_time if self.start_time else None
            runtime_str = f"{int(runtime.total_seconds() / 3600)}h {int((runtime.total_seconds() % 3600) / 60)}m" if runtime else "N/A"
            
            message = f"""
🛑 <b>Multi-Symbol Scanner Stopped</b>

📊 <b>Session Summary:</b>
• Runtime: {runtime_str}
• Total Signals: {self.total_signals}
• Suppressed: {self.suppressed_signals}
• Sent: {self.total_signals - self.suppressed_signals}

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
            
            self.alerter.send_message(message)
            
        except Exception as e:
            logger.warning(f"Failed to send shutdown notification: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics.
        
        Returns:
            Dictionary with statistics
        """
        scanner_stats = {
            symbol: scanner.get_statistics()
            for symbol, scanner in self.scanners.items()
        }
        
        filter_stats = self.signal_filter.get_statistics()
        
        runtime = datetime.now() - self.start_time if self.start_time else None
        
        return {
            'running': self.running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'runtime_seconds': runtime.total_seconds() if runtime else 0,
            'total_scanners': len(self.scanners),
            'active_threads': len(self.scanner_threads),
            'total_signals': self.total_signals,
            'suppressed_signals': self.suppressed_signals,
            'sent_signals': self.total_signals - self.suppressed_signals,
            'active_trades': self.trade_tracker.get_active_count(),
            'closed_trades': self.trade_tracker.get_closed_count(),
            'scanner_stats': scanner_stats,
            'filter_stats': filter_stats
        }
    
    def get_active_symbols(self) -> List[str]:
        """Get list of active symbol identifiers."""
        return list(self.scanners.keys())
    
    def reload_configuration(self) -> bool:
        """
        Reload configuration and update scanners.
        
        Returns:
            True if successful
        """
        try:
            logger.info("Reloading configuration...")
            
            success, errors = self.config_manager.reload_configs()
            
            if not success:
                logger.error(f"Configuration reload failed: {errors}")
                return False
            
            logger.info("Configuration reloaded successfully")
            
            # TODO: Update running scanners with new config
            # For now, just log - full implementation would restart scanners
            
            return True
            
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    from src.alerter import TelegramAlerter
    
    # Create config manager
    config_manager = AssetConfigManager("config/multi_crypto_scalp.json")
    
    # Create alerter (mock for testing)
    class MockAlerter:
        def send_message(self, msg):
            print(f"Alert: {msg[:100]}...")
        def send_signal_alert(self, signal):
            print(f"Signal Alert: {signal.signal_type} at ${signal.entry_price:.2f}")
    
    alerter = MockAlerter()
    
    # Create orchestrator
    orchestrator = SymbolOrchestrator(config_manager, alerter)
    
    # Add symbols
    for symbol in config_manager.get_enabled_symbols():
        orchestrator.add_symbol(symbol)
    
    print(f"Orchestrator ready with {len(orchestrator.scanners)} symbols")
    print(f"Statistics: {orchestrator.get_statistics()}")
