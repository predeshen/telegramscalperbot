"""BTC Scalping Scanner - Main application entry point."""
import signal
import sys
import time
import threading
from datetime import datetime
import logging

from src.config_loader import ConfigLoader
from src.market_data_client import MarketDataClient
from src.websocket_streamer import BinanceWebSocketStreamer
from src.indicator_calculator import IndicatorCalculator
from src.signal_detector import SignalDetector
from src.alerter import EmailAlerter, TelegramAlerter, MultiAlerter
from src.health_monitor import HealthMonitor, setup_logging


logger = logging.getLogger(__name__)


class BTCScalpingScanner:
    """Main application orchestrator for BTC scalping signal detection."""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialize scanner application.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = ConfigLoader.load(config_path)
        
        # Setup logging
        setup_logging(
            self.config.logging.file,
            self.config.logging.level,
            self.config.logging.retention_days
        )
        
        logger.info("=" * 60)
        logger.info("BTC Scalping Scanner Starting")
        logger.info("=" * 60)
        
        # Initialize components
        self.health_monitor = HealthMonitor()
        
        self.market_client = MarketDataClient(
            exchange_name=self.config.exchange.name,
            symbol=self.config.exchange.symbol,
            timeframes=self.config.exchange.timeframes
        )
        
        self.indicator_calculator = IndicatorCalculator()
        
        self.signal_detector = SignalDetector(
            volume_spike_threshold=self.config.signal_rules.volume_spike_threshold,
            rsi_min=self.config.signal_rules.rsi_min,
            rsi_max=self.config.signal_rules.rsi_max,
            stop_loss_atr_multiplier=self.config.signal_rules.stop_loss_atr_multiplier,
            take_profit_atr_multiplier=self.config.signal_rules.take_profit_atr_multiplier,
            duplicate_time_window_minutes=self.config.signal_rules.duplicate_time_window_minutes,
            duplicate_price_threshold_percent=self.config.signal_rules.duplicate_price_threshold_percent
        )
        
        # Initialize alerters
        email_alerter = None
        if self.config.smtp.password != "DISABLED":
            email_alerter = EmailAlerter(
                smtp_server=self.config.smtp.server,
                smtp_port=self.config.smtp.port,
                smtp_user=self.config.smtp.user,
                smtp_password=self.config.smtp.password,
                from_email=self.config.smtp.from_email,
                to_email=self.config.smtp.to_email,
                use_ssl=self.config.smtp.use_ssl
            )
        
        telegram_alerter = None
        if self.config.telegram.enabled:
            telegram_alerter = TelegramAlerter(
                bot_token=self.config.telegram.bot_token,
                chat_id=self.config.telegram.chat_id
            )
        
        # Use Telegram-only if email is disabled
        if email_alerter:
            self.alerter = MultiAlerter(email_alerter, telegram_alerter)
        elif telegram_alerter:
            self.alerter = telegram_alerter
        else:
            raise RuntimeError("No alerter configured! Enable either email or Telegram.")
        
        # WebSocket streamer
        self.ws_streamer = None
        
        # Control flags
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Health monitoring thread
        self.health_thread = None
        
        logger.info("All components initialized successfully")
    
    def start(self) -> None:
        """Start the scanner application."""
        try:
            # Connect to exchange
            logger.info("Connecting to exchange...")
            if not self.market_client.connect():
                raise RuntimeError("Failed to connect to exchange")
            
            self.health_monitor.set_connection_status("connected")
            
            # Fetch initial historical data
            logger.info("Fetching initial candlestick data...")
            for timeframe in self.config.exchange.timeframes:
                self.market_client.get_latest_candles(timeframe, 200)
                logger.info(f"Loaded {timeframe} data")
            
            # Start WebSocket streamer
            logger.info("Starting WebSocket streamer...")
            self.ws_streamer = BinanceWebSocketStreamer(
                symbol=self.config.exchange.symbol,
                timeframes=self.config.exchange.timeframes,
                on_candle_callback=self._on_candle_update
            )
            self.ws_streamer.start()
            
            # Start health monitoring thread
            self.health_thread = threading.Thread(target=self._health_monitoring_loop, daemon=True)
            self.health_thread.start()
            
            # Set running flag
            self.running = True
            
            logger.info("Scanner is now running. Press Ctrl+C to stop.")
            
            # Main loop - just wait for shutdown
            while self.running and not self.shutdown_event.is_set():
                time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}", exc_info=True)
            self.health_monitor.record_error(e)
            self.alerter.send_error_alert(e, "Main loop critical error")
            raise
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the scanner application gracefully."""
        logger.info("Shutting down scanner...")
        
        self.running = False
        self.shutdown_event.set()
        
        # Stop WebSocket
        if self.ws_streamer:
            self.ws_streamer.stop()
        
        # Close market client
        if self.market_client:
            self.market_client.close()
        
        self.health_monitor.set_connection_status("disconnected")
        
        # Log final health summary
        self.health_monitor.log_health_summary(logger)
        
        logger.info("Scanner stopped successfully")
    
    def _on_candle_update(self, timeframe: str, candle: dict) -> None:
        """
        Callback for WebSocket candle updates.
        
        Args:
            timeframe: Timeframe of the candle
            candle: Candle data dictionary
        """
        try:
            # Update buffer
            self.market_client.update_buffer(timeframe, candle)
            
            # Update health monitor
            self.health_monitor.update_data_timestamp(candle['timestamp'])
            
            # Only process closed candles for signal detection
            if not candle.get('is_closed', False):
                return
            
            logger.debug(f"Processing closed candle: {timeframe} @ {candle['close']}")
            
            # Get buffer data
            data = self.market_client.get_buffer_data(timeframe)
            
            if data.empty or len(data) < 50:
                logger.debug(f"Insufficient data for {timeframe}: {len(data)} candles")
                return
            
            # Calculate indicators
            data_with_indicators = self.indicator_calculator.calculate_all_indicators(
                data,
                ema_periods=[
                    self.config.indicators.ema_fast,
                    self.config.indicators.ema_slow,
                    self.config.indicators.ema_trend,
                    100,
                    200
                ],
                atr_period=self.config.indicators.atr_period,
                rsi_period=self.config.indicators.rsi_period,
                volume_ma_period=self.config.indicators.volume_ma_period
            )
            
            if data_with_indicators.empty:
                logger.debug(f"No valid data after indicator calculation for {timeframe}")
                return
            
            # Detect signals
            signal = self.signal_detector.detect_signals(data_with_indicators, timeframe)
            
            if signal:
                logger.info(f"🎯 Signal detected: {signal.signal_type} on {timeframe}")
                
                # Record signal
                self.health_monitor.record_signal(signal.signal_type)
                
                # Send alerts
                alert_success = self.alerter.send_signal_alert(signal)
                
                if alert_success:
                    logger.info("Alert sent successfully")
                else:
                    logger.error("Failed to send alert")
                
                # Update email success rate
                if hasattr(self.alerter.email_alerter, 'get_success_rate'):
                    rate = self.alerter.email_alerter.get_success_rate()
                    self.health_monitor.set_email_success_rate(rate)
            
        except Exception as e:
            logger.error(f"Error processing candle update: {e}", exc_info=True)
            self.health_monitor.record_error(e)
    
    def _health_monitoring_loop(self) -> None:
        """Background thread for periodic health monitoring."""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Log health summary every 5 minutes
                time.sleep(300)
                
                if self.running:
                    self.health_monitor.log_health_summary(logger)
                    
                    # Check WebSocket connection
                    if self.ws_streamer and not self.ws_streamer.is_connected():
                        logger.warning("WebSocket disconnected, attempting reconnection...")
                        self.health_monitor.set_connection_status("reconnecting")
                        
                        # WebSocket auto-reconnects, just log the status
                        time.sleep(10)
                        
                        if self.ws_streamer.is_connected():
                            logger.info("WebSocket reconnected successfully")
                            self.health_monitor.set_connection_status("connected")
                        else:
                            logger.error("WebSocket reconnection failed")
                            self.health_monitor.set_connection_status("disconnected")
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                self.health_monitor.record_error(e)


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and start scanner
        scanner = BTCScalpingScanner()
        scanner.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
