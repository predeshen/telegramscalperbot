"""
Unified Scanner Base Class
Provides common initialization, polling logic, and signal processing for all scanners.
"""
import logging
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd

logger = logging.getLogger(__name__)


class BaseScanner:
    """
    Base class for all trading scanners.
    
    Provides:
    - Unified initialization and configuration loading
    - Data fetching with freshness validation
    - Indicator calculation pipeline
    - Strategy detection coordination
    - Alert delivery and trade tracking
    - Health monitoring
    """
    
    def __init__(
        self,
        scanner_name: str,
        symbol: str,
        timeframes: List[str],
        config_path: str = "config/config.json",
        asset_config: Optional[Dict] = None
    ):
        """
        Initialize base scanner.
        
        Args:
            scanner_name: Name of scanner (e.g., "BTC Scalp", "Gold Swing")
            symbol: Trading symbol (BTC, XAUUSD, US30, US100)
            timeframes: List of timeframes to monitor (e.g., ["1m", "5m", "15m"])
            config_path: Path to configuration file
            asset_config: Optional asset-specific configuration overrides
        """
        self.scanner_name = scanner_name
        self.symbol = symbol
        self.timeframes = timeframes
        self.config_path = config_path
        self.asset_config = asset_config or {}
        
        # Load configuration
        from src.config_loader import ConfigLoader
        self.config = ConfigLoader.load(config_path)
        
        # Setup logging
        from src.health_monitor import setup_logging
        setup_logging(
            self.config.logging.file,
            self.config.logging.level,
            self.config.logging.retention_days
        )
        
        logger.info(f"Initializing {scanner_name} scanner for {symbol}")
        
        # Initialize components
        self.data_client = None
        self.indicator_calculator = None
        self.strategy_detector = None
        self.signal_quality_filter = None
        self.alerter = None
        self.trade_tracker = None
        self.health_monitor = None
        
        # Control flags
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Data freshness tracking
        self.last_fresh_data_time: Dict[str, datetime] = {}
        self.stale_data_count: Dict[str, int] = {}
        
        # Initialize all components
        self._initialize_components()
        
        logger.info(f"{scanner_name} scanner initialized successfully")
    
    def _initialize_components(self):
        """Initialize all scanner components"""
        try:
            # Initialize data client
            from src.unified_data_source import UnifiedDataSource, DataSourceConfig
            
            data_config = DataSourceConfig(
                primary_source="binance",
                fallback_sources=["twelve_data", "alpha_vantage", "mt5"],
                alpha_vantage_key=self.config.data_providers.alpha_vantage_key if self.config.data_providers else None,
                twelve_data_key=self.config.data_providers.twelve_data_key if self.config.data_providers else None,
                freshness_threshold_seconds=300
            )
            self.data_client = UnifiedDataSource(data_config)
            logger.info("Data client initialized")
            
            # Initialize indicator calculator
            from src.indicator_calculator import IndicatorCalculator
            self.indicator_calculator = IndicatorCalculator()
            logger.info("Indicator calculator initialized")
            
            # Initialize strategy detector
            from src.strategy_detector import StrategyDetector
            self.strategy_detector = StrategyDetector()
            logger.info("Strategy detector initialized")
            
            # Initialize signal quality filter
            from src.signal_quality_filter import SignalQualityFilter, QualityConfig
            quality_config = QualityConfig(
                min_confluence_factors=self.asset_config.get('min_confluence_factors', 4),
                min_confidence_score=self.asset_config.get('min_confidence_score', 3)
            )
            self.signal_quality_filter = SignalQualityFilter(quality_config)
            logger.info("Signal quality filter initialized")
            
            # Initialize alerter
            from src.alerter import EmailAlerter, TelegramAlerter, MultiAlerter
            
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
            
            if email_alerter:
                self.alerter = MultiAlerter(email_alerter, telegram_alerter)
            elif telegram_alerter:
                self.alerter = telegram_alerter
            else:
                logger.warning("No alerter configured (email and Telegram both disabled)")
            
            logger.info("Alerter initialized")
            
            # Initialize trade tracker
            from src.trade_tracker import TradeTracker
            self.trade_tracker = TradeTracker(alerter=self.alerter)
            logger.info("Trade tracker initialized")
            
            # Initialize health monitor
            from src.health_monitor import HealthMonitor
            self.health_monitor = HealthMonitor()
            logger.info("Health monitor initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}", exc_info=True)
            raise
    
    def start(self) -> bool:
        """
        Start the scanner.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            logger.info(f"Starting {self.scanner_name} scanner")
            
            # Fetch initial data
            logger.info("Fetching initial market data...")
            for timeframe in self.timeframes:
                try:
                    df, is_fresh = self.data_client.get_latest_candles(
                        self.symbol,
                        timeframe,
                        limit=500,
                        validate_freshness=False
                    )
                    
                    if df.empty:
                        logger.error(f"Failed to fetch initial data for {timeframe}")
                        return False
                    
                    self.stale_data_count[timeframe] = 0
                    self.last_fresh_data_time[timeframe] = datetime.now()
                    logger.info(f"Loaded {len(df)} candles for {timeframe}")
                    
                except Exception as e:
                    logger.error(f"Error fetching initial data for {timeframe}: {e}")
                    return False
            
            # Set running flag
            self.running = True
            
            # Send startup notification
            if self.alerter:
                try:
                    startup_msg = (
                        f"🟢 <b>{self.scanner_name} Started</b>\n\n"
                        f"Symbol: {self.symbol}\n"
                        f"Timeframes: {', '.join(self.timeframes)}\n"
                        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    )
                    self.alerter.send_message(startup_msg)
                except Exception as e:
                    logger.warning(f"Failed to send startup message: {e}")
            
            logger.info(f"{self.scanner_name} scanner started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting scanner: {e}", exc_info=True)
            return False
    
    def stop(self):
        """Stop the scanner"""
        logger.info(f"Stopping {self.scanner_name} scanner")
        self.running = False
        self.shutdown_event.set()
        
        # Send shutdown notification
        if self.alerter:
            try:
                shutdown_msg = (
                    f"🔴 <b>{self.scanner_name} Stopped</b>\n\n"
                    f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
                self.alerter.send_message(shutdown_msg)
            except Exception as e:
                logger.warning(f"Failed to send shutdown message: {e}")
        
        logger.info(f"{self.scanner_name} scanner stopped")
    
    def run_polling_loop(self, interval_seconds: int = 10):
        """
        Run the main polling loop.
        
        Args:
            interval_seconds: Polling interval in seconds
        """
        logger.info(f"Starting polling loop (interval: {interval_seconds}s)")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Process each timeframe
                for timeframe in self.timeframes:
                    try:
                        self._process_timeframe(timeframe)
                    except Exception as e:
                        logger.error(f"Error processing {timeframe}: {e}")
                        continue
                
                # Sleep before next poll
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Polling loop interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                time.sleep(interval_seconds)
    
    def _process_timeframe(self, timeframe: str):
        """
        Process a single timeframe.
        
        Args:
            timeframe: Timeframe to process
        """
        try:
            # Fetch latest data
            df, is_fresh = self.data_client.get_latest_candles(
                self.symbol,
                timeframe,
                limit=500,
                validate_freshness=True
            )
            
            if df.empty:
                logger.error(f"Empty data for {timeframe}")
                return
            
            # Update freshness tracking
            if not is_fresh:
                self.stale_data_count[timeframe] = self.stale_data_count.get(timeframe, 0) + 1
                logger.warning(f"Stale data for {timeframe} (count: {self.stale_data_count[timeframe]})")
            else:
                self.stale_data_count[timeframe] = 0
                self.last_fresh_data_time[timeframe] = datetime.now()
            
            # Calculate indicators
            data_with_indicators = self.indicator_calculator.calculate_all_indicators(
                df,
                ema_periods=[9, 21, 50, 100, 200],
                atr_period=14,
                rsi_period=6,
                volume_ma_period=20
            )
            
            if data_with_indicators.empty:
                logger.error(f"No valid data after indicator calculation for {timeframe}")
                return
            
            # Detect signals
            signal = self.strategy_detector.detect_signals(
                data_with_indicators,
                timeframe,
                self.symbol
            )
            
            if signal:
                # Filter signal quality
                filter_result = self.signal_quality_filter.evaluate_signal(signal, data_with_indicators)
                
                if filter_result.passed:
                    logger.info(f"✓ Signal passed quality filter: {signal.signal_type} on {timeframe}")
                    
                    # Send alert
                    if self.alerter:
                        try:
                            self.alerter.send_signal_alert(signal)
                            logger.info("Alert sent successfully")
                        except Exception as e:
                            logger.error(f"Failed to send alert: {e}")
                    
                    # Add to trade tracker
                    if self.trade_tracker:
                        self.trade_tracker.add_trade(signal)
                    
                    # Add to signal history for duplicate detection
                    self.signal_quality_filter.add_signal_to_history(signal)
                else:
                    logger.info(f"Signal rejected: {filter_result.rejection_reason}")
            
            # Update health monitor
            self.health_monitor.update_data_timestamp(data_with_indicators.iloc[-1]['timestamp'])
            
        except Exception as e:
            logger.error(f"Error processing timeframe {timeframe}: {e}", exc_info=True)
    
    def get_status(self) -> Dict:
        """
        Get scanner status.
        
        Returns:
            Dictionary with scanner status
        """
        return {
            'scanner_name': self.scanner_name,
            'symbol': self.symbol,
            'running': self.running,
            'timeframes': self.timeframes,
            'last_fresh_data': self.last_fresh_data_time,
            'stale_data_count': self.stale_data_count,
            'data_source_status': self.data_client.get_source_status() if self.data_client else {},
            'health': self.health_monitor.get_status() if self.health_monitor else {}
        }

