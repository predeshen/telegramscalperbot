"""BTC Scalping Scanner - Main application entry point."""
import signal
import sys
import time
import threading
from datetime import datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from src.config_loader import ConfigLoader
from src.market_data_client import MarketDataClient
from src.websocket_streamer import BinanceWebSocketStreamer
from src.indicator_calculator import IndicatorCalculator
from src.signal_detector import SignalDetector
from src.signal_quality_filter import SignalQualityFilter, QualityConfig
from src.liquidity_filter import LiquidityFilter
from src.data_validation import DataValidator
from src.alerter import EmailAlerter, TelegramAlerter, MultiAlerter
from src.health_monitor import HealthMonitor, setup_logging
from src.excel_reporter import ExcelReporter
from src.trade_tracker import TradeTracker
from src.news_calendar import NewsCalendar
from src.signal_diagnostics import SignalDiagnostics
from src.config_validator import ConfigValidator
from src.bypass_mode import BypassMode


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
        
        # Initialize diagnostic system
        self.diagnostics = SignalDiagnostics("BTC-Scalp")
        logger.info("Diagnostic system initialized")
        
        # Validate configuration
        validator = ConfigValidator()
        config_dict = self.config.__dict__ if hasattr(self.config, '__dict__') else {}
        warnings = validator.validate_config(config_dict)
        if warnings:
            for warning in warnings:
                logger.warning(f"Config: {warning}")
        
        # Initialize bypass mode
        self.bypass_mode = BypassMode(config_dict, None)  # Will set alerter later
        
        # Use HybridDataClient for hybrid exchange, otherwise use MarketDataClient
        if self.config.exchange.name == 'hybrid':
            from src.hybrid_data_client import HybridDataClient
            
            # Get data provider keys from config
            alpha_vantage_key = None
            twelve_data_key = None
            preferred_provider = None
            
            if hasattr(self.config, 'data_providers'):
                alpha_vantage_key = getattr(self.config.data_providers, 'alpha_vantage_key', None)
                twelve_data_key = getattr(self.config.data_providers, 'twelve_data_key', None)
                preferred_provider = getattr(self.config.data_providers, 'preferred_provider', None)
            
            self.market_client = HybridDataClient(
                symbol=self.config.exchange.symbol,
                timeframes=self.config.exchange.timeframes,
                buffer_size=500,
                alpha_vantage_key=alpha_vantage_key,
                twelve_data_key=twelve_data_key,
                preferred_provider=preferred_provider
            )
            logger.info("Using HybridDataClient for multi-provider support")
        else:
            self.market_client = MarketDataClient(
                exchange_name=self.config.exchange.name,
                symbol=self.config.exchange.symbol,
                timeframes=self.config.exchange.timeframes,
                buffer_size=500  # Increased from 200 for better indicator calculations
            )
        
        self.indicator_calculator = IndicatorCalculator()
        
        self.signal_detector = SignalDetector(
            volume_spike_threshold=self.config.signal_rules.volume_spike_threshold,
            rsi_min=self.config.signal_rules.rsi_min,
            rsi_max=self.config.signal_rules.rsi_max,
            stop_loss_atr_multiplier=self.config.signal_rules.stop_loss_atr_multiplier,
            take_profit_atr_multiplier=self.config.signal_rules.take_profit_atr_multiplier,
            duplicate_time_window_minutes=self.config.signal_rules.duplicate_time_window_minutes,
            duplicate_price_threshold_percent=self.config.signal_rules.duplicate_price_threshold_percent,
            diagnostics=self.diagnostics
        )
        
        # Set config for new detection strategies
        self.signal_detector.config = {
            'signal_rules': {
                'volume_momentum_shift': self.config.signal_rules.volume_momentum_shift,
                'volume_trend_alignment': self.config.signal_rules.volume_trend_alignment,
                'volume_ema_cloud_breakout': self.config.signal_rules.volume_ema_cloud_breakout,
                'volume_mean_reversion': self.config.signal_rules.volume_mean_reversion,
                'rsi_momentum_threshold': self.config.signal_rules.rsi_momentum_threshold,
                'adx_min_momentum_shift': self.config.signal_rules.adx_min_momentum_shift,
                'adx_min_trend_alignment': self.config.signal_rules.adx_min_trend_alignment,
                'adx_min_trend': self.config.signal_rules.adx_min_trend,
                'momentum_shift_sl_multiplier': self.config.signal_rules.momentum_shift_sl_multiplier,
                'momentum_shift_tp_multiplier': self.config.signal_rules.momentum_shift_tp_multiplier,
                'enable_extreme_rsi_signals': self.config.signal_rules.enable_extreme_rsi_signals,
            }
        }
        
        # Configure H4 HVG if enabled
        if self.config.h4_hvg and self.config.h4_hvg.enabled:
            # Convert dataclass to dict for H4HVGDetector
            h4_hvg_config = {
                'min_gap_percent': self.config.h4_hvg.min_gap_percent,
                'volume_spike_threshold': self.config.h4_hvg.volume_spike_threshold,
                'atr_multiplier_sl': self.config.h4_hvg.atr_multiplier_sl,
                'gap_target_multiplier': self.config.h4_hvg.gap_target_multiplier,
                'min_risk_reward': self.config.h4_hvg.min_risk_reward,
                'max_gap_age_candles': self.config.h4_hvg.max_gap_age_candles,
                'rsi_min': self.config.h4_hvg.rsi_min,
                'rsi_max': self.config.h4_hvg.rsi_max,
                'require_ema_confluence': self.config.h4_hvg.require_ema_confluence,
                'duplicate_time_window_minutes': self.config.h4_hvg.duplicate_time_window_minutes,
                'duplicate_price_threshold_percent': self.config.h4_hvg.duplicate_price_threshold_percent
            }
            self.signal_detector.configure_h4_hvg(h4_hvg_config, self.config.exchange.symbol)
            logger.info("H4 HVG detection enabled for BTC scalping")
        
        # Initialize Signal Quality Filter with config values
        quality_filter_config = getattr(self.config, 'quality_filter', {})
        quality_config = QualityConfig(
            min_confluence_factors=quality_filter_config.get('min_confluence_factors', 3),
            min_confidence_score=quality_filter_config.get('min_confidence_score', 3),
            duplicate_window_seconds=quality_filter_config.get('duplicate_window_seconds', 600),
            duplicate_price_tolerance_pct=quality_filter_config.get('duplicate_price_tolerance_pct', 1.0),
            significant_price_move_pct=quality_filter_config.get('significant_price_move_pct', 1.5),
            min_risk_reward=quality_filter_config.get('min_risk_reward', 1.2)
        )
        self.quality_filter = SignalQualityFilter(quality_config, diagnostics=self.diagnostics)
        logger.info("Signal Quality Filter initialized")
        
        # Initialize Liquidity Filter
        self.liquidity_filter = LiquidityFilter()
        logger.info("Liquidity Filter initialized")
        
        # Initialize Data Validator
        self.data_validator = DataValidator(max_consecutive_errors=10)
        logger.info("Data Validator initialized")
        
        # Initialize news calendar
        self.news_calendar = NewsCalendar()
        logger.info("News calendar initialized for BTC scanner")
        
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
        
        # Set alerter for bypass mode
        self.bypass_mode.alerter = self.alerter
        
        # WebSocket streamer
        self.ws_streamer = None
        
        # Control flags
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Health monitoring thread
        self.health_thread = None
        
        # Trade tracker
        self.trade_tracker = TradeTracker(alerter=self.alerter)
        
        # Data freshness tracking
        self.last_fresh_data_time: dict[str, datetime] = {}
        self.stale_data_count: dict[str, int] = {}
        self.last_stale_alert_time: dict[str, datetime] = {}
        
        # Trade update tracking
        self.last_trade_update_time: datetime | None = None
        self.last_known_price: float | None = None
        self.last_known_price_time: datetime | None = None
        self.trade_update_failure_count: int = 0
        
        # Excel reporter
        self.excel_reporter = None
        if hasattr(self.config, 'excel_reporting') and self.config.excel_reporting.get('enabled', False):
            try:
                # Use existing SMTP config or dedicated one
                smtp_config = self.config.excel_reporting.get('smtp', {
                    'server': self.config.smtp.server,
                    'port': self.config.smtp.port,
                    'user': self.config.smtp.user,
                    'password': self.config.smtp.password,
                    'from_email': self.config.smtp.from_email,
                    'to_email': self.config.smtp.to_email,
                    'use_ssl': self.config.smtp.use_ssl
                })
                
                # Only enable if SMTP password is set
                if smtp_config.get('password') and smtp_config['password'] != 'DISABLED':
                    self.excel_reporter = ExcelReporter(
                        excel_file_path=self.config.excel_reporting.get('excel_file_path', 'logs/btc_scalp_scans.xlsx'),
                        smtp_config=smtp_config,
                        report_interval_seconds=self.config.excel_reporting.get('report_interval_seconds', 3600),
                        initial_report_delay_seconds=self.config.excel_reporting.get('initial_report_delay_seconds', 300),
                        scanner_name="BTC Scalp Scanner"
                    )
                    logger.info("Excel reporting enabled")
                else:
                    logger.warning("Excel reporting disabled: SMTP password not configured")
            except Exception as e:
                logger.error(f"Failed to initialize Excel reporter: {e}")
        
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
                _, _ = self.market_client.get_latest_candles(timeframe, 500, validate_freshness=False)
                logger.info(f"Loaded {timeframe} data")
                # Initialize state tracking
                self.stale_data_count[timeframe] = 0
                self.last_fresh_data_time[timeframe] = datetime.now()
            
            # Use polling mode instead of WebSocket for better compatibility
            logger.info("Using polling mode for data updates (more reliable across exchanges)...")
            self.ws_streamer = None  # Disabled for compatibility
            
            # Start health monitoring thread
            self.health_thread = threading.Thread(target=self._health_monitoring_loop, daemon=True)
            self.health_thread.start()
            
            # Start Excel reporter
            if self.excel_reporter:
                self.excel_reporter.start()
            
            # Set running flag
            self.running = True
            
            # Send startup notification
            if self.alerter:
                try:
                    # Get current price
                    df, _ = self.market_client.get_latest_candles(self.config.exchange.timeframes[0], 10, validate_freshness=False)
                    current_price = df.iloc[-1]['close'] if not df.empty else 0
                    
                    # Get news status
                    news_status = self.news_calendar.get_news_status()
                    news_info = ""
                    if news_status['next_event']:
                        next_event = news_status['next_event']
                        news_info = f"\n📰 Next Event: {next_event['title']} in {int(next_event['minutes_until'])}min"
                    
                    startup_msg = (
                        f"🟢 <b>BTC Scalping Scanner Started</b>\n\n"
                        f"💰 Current Price: ${current_price:,.2f}\n"
                        f"⏰ Timeframes: {', '.join(self.config.exchange.timeframes)}\n"
                        f"🎯 Strategy: EMA Crossover + Volume Confirmation\n"
                        f"📊 Exchange: {self.config.exchange.name.upper()}{news_info}\n\n"
                        f"🔍 Scanning for scalping opportunities..."
                    )
                    self.alerter.send_message(startup_msg)
                except Exception as e:
                    logger.warning(f"Failed to send startup message: {e}")
            
            logger.info("Scanner is now running. Press Ctrl+C to stop.")
            
            # Track last heartbeat time
            last_heartbeat = time.time()
            heartbeat_interval = 5400  # 90 minutes in seconds
            
            # Main loop - poll for new data every 10 seconds
            logger.info("Starting main polling loop (10-second intervals)...")
            last_news_pause = False
            
            while self.running and not self.shutdown_event.is_set():
                try:
                    # Check news calendar
                    should_pause_news, news_reason = self.news_calendar.should_pause_trading()
                    
                    if should_pause_news != last_news_pause:
                        if should_pause_news:
                            logger.warning(f"📰 Trading paused: {news_reason}")
                            if self.alerter:
                                self.alerter.send_message(f"⏸️ *BTC Trading Paused*\n\n{news_reason}")
                        else:
                            logger.info("✅ Trading resumed after news")
                            if self.alerter:
                                self.alerter.send_message("▶️ *BTC Trading Resumed*\n\nNews event passed, back to normal trading.")
                        
                        last_news_pause = should_pause_news
                    
                    # Skip trading if paused for news
                    if should_pause_news:
                        time.sleep(60)
                        continue
                    
                    # Fetch latest data for each timeframe with freshness validation
                    for timeframe in self.config.exchange.timeframes:
                        try:
                            df, is_fresh = self.market_client.get_latest_candles(timeframe, 500)
                            
                            if df.empty:
                                logger.error(f"Received empty DataFrame for {timeframe} - skipping this iteration")
                                continue
                            
                            # Check data freshness
                            if not is_fresh:
                                logger.warning(f"Stale data detected for {timeframe}, attempting retry...")
                                
                                # Increment stale counter
                                self.stale_data_count[timeframe] = self.stale_data_count.get(timeframe, 0) + 1
                                
                                # Get data age for alert
                                _, age_seconds = self.market_client.validate_data_freshness(df, timeframe)
                                
                                # Retry with backoff
                                df, is_fresh = self._retry_fetch_with_backoff(timeframe)
                                
                                if not is_fresh or df is None:
                                    logger.error(f"Failed to get fresh data for {timeframe} after retries")
                                    
                                    # Send stale data alert after 3 consecutive failures
                                    self._send_stale_data_alert(timeframe, age_seconds)
                                    
                                    # Skip signal detection for this timeframe but continue loop
                                    continue
                                else:
                                    # Fresh data obtained after retry
                                    logger.info(f"Fresh data restored for {timeframe}")
                                    
                                    # Send recovery alert if data was stale for a while
                                    if self.stale_data_count.get(timeframe, 0) >= 3:
                                        last_fresh = self.last_fresh_data_time.get(timeframe)
                                        if last_fresh:
                                            stale_duration = (datetime.now() - last_fresh).total_seconds()
                                            self._send_recovery_alert(timeframe, stale_duration)
                                    
                                    self.stale_data_count[timeframe] = 0
                                    self.last_fresh_data_time[timeframe] = datetime.now()
                            else:
                                # Data is fresh
                                # Check if we're recovering from stale data
                                if self.stale_data_count.get(timeframe, 0) >= 3:
                                    last_fresh = self.last_fresh_data_time.get(timeframe)
                                    if last_fresh:
                                        stale_duration = (datetime.now() - last_fresh).total_seconds()
                                        self._send_recovery_alert(timeframe, stale_duration)
                                
                                self.stale_data_count[timeframe] = 0
                                self.last_fresh_data_time[timeframe] = datetime.now()
                            
                        except Exception as e:
                            logger.error(f"Failed to fetch data for {timeframe}: {e}")
                            continue
                        
                        # Process data (we know it's not empty and fresh here)
                        # Update health monitor
                        self.health_monitor.update_data_timestamp(df.iloc[-1]['timestamp'])
                        
                        # Calculate indicators
                        data_with_indicators = self.indicator_calculator.calculate_all_indicators(
                            df,
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
                        
                        if not data_with_indicators.empty:
                            # Detect signals
                            signal = self.signal_detector.detect_signals(data_with_indicators, timeframe)
                            
                            # Log scan result to Excel
                            if self.excel_reporter:
                                last_row = data_with_indicators.iloc[-1]
                                # Determine scanner name based on strategy
                                scanner_name = 'BTC-Scalp'
                                if signal and getattr(signal, 'strategy', '') == 'H4 HVG':
                                    scanner_name = 'BTC-Scalp-H4HVG'
                                
                                scan_data = {
                                    'timestamp': datetime.now(),
                                    'scanner': scanner_name,
                                    'symbol': self.config.exchange.symbol,
                                    'timeframe': timeframe,
                                    'price': last_row['close'],
                                    'volume': last_row['volume'],
                                    'indicators': {
                                        'ema_9': last_row.get('ema_9', None),
                                        'ema_21': last_row.get('ema_21', None),
                                        'ema_50': last_row.get('ema_50', None),
                                        'ema_100': last_row.get('ema_100', None),
                                        'ema_200': last_row.get('ema_200', None),
                                        'rsi': last_row.get('rsi', None),
                                        'atr': last_row.get('atr', None),
                                        'volume_ma': last_row.get('volume_ma', None)
                                    },
                                    'signal_detected': signal is not None,
                                    'signal_type': signal.signal_type if signal else None,
                                    'signal_details': {
                                        'entry_price': signal.entry_price,
                                        'stop_loss': signal.stop_loss,
                                        'take_profit': signal.take_profit,
                                        'risk_reward': signal.risk_reward,
                                        'strategy': getattr(signal, 'strategy', 'N/A'),
                                        'gap_size_percent': getattr(signal, 'gap_info', {}).gap_percent if signal and hasattr(signal, 'gap_info') and signal.gap_info else None,
                                        'volume_spike_ratio': getattr(signal, 'volume_spike_ratio', None) if signal else None,
                                        'confluence_factors': len(getattr(signal, 'confluence_factors', [])) if signal and hasattr(signal, 'confluence_factors') and signal.confluence_factors else None
                                    } if signal else {}
                                }
                                self.excel_reporter.log_scan_result(scan_data)
                            
                            if signal:
                                logger.info(f"🎯 Signal detected: {signal.signal_type} on {timeframe}")
                                
                                # Record signal
                                self.health_monitor.record_signal(signal.signal_type)
                                
                                # Send alerts
                                alert_success = self.alerter.send_signal_alert(signal)
                                
                                if alert_success:
                                    logger.info("Alert sent successfully")
                                    
                                    # Add trade to tracker
                                    self.trade_tracker.add_trade(signal)
                                else:
                                    logger.error("Failed to send alert")
                                
                                # Update email success rate
                                if hasattr(self.alerter, 'email_alerter') and self.alerter.email_alerter:
                                    rate = self.alerter.email_alerter.get_success_rate()
                                    self.health_monitor.set_email_success_rate(rate)
                                
                    
                    # ALWAYS update active trades (independent of signal detection)
                    # This ensures TP/SL notifications are sent even if signal detection fails
                    if self.trade_tracker.get_active_count() > 0:
                        current_price = self._get_current_price_for_trades()
                        
                        if current_price:
                            # Get indicators if available
                            indicators = None
                            try:
                                primary_tf = self.config.exchange.timeframes[0]
                                df, _ = self.market_client.get_latest_candles(primary_tf, 10, validate_freshness=False)
                                if not df.empty:
                                    last_row = df.iloc[-1]
                                    indicators = {
                                        'rsi': last_row.get('rsi', 50),
                                        'prev_rsi': df.iloc[-2].get('rsi', 50) if len(df) > 1 else 50,
                                        'adx': last_row.get('adx', 0),
                                        'volume_ratio': last_row['volume'] / last_row.get('volume_ma', 1) if last_row.get('volume_ma', 0) > 0 else 0
                                    }
                            except Exception as e:
                                logger.warning(f"Failed to get indicators for trade updates: {e}")
                            
                            # Update trades
                            self.trade_tracker.update_trades(current_price, indicators)
                            self.last_trade_update_time = datetime.now()
                            self.trade_update_failure_count = 0
                        else:
                            # Failed to get price
                            self.trade_update_failure_count += 1
                            logger.error(
                                f"Cannot update trades: no valid price available "
                                f"(failures: {self.trade_update_failure_count})"
                            )
                            
                            # Send alert after 3 consecutive failures
                            self._send_trade_update_failure_alert()
                    
                    # Check if it's time for heartbeat message (every 15 minutes)
                    current_time = time.time()
                    if current_time - last_heartbeat >= heartbeat_interval:
                        try:
                            # Get latest data for heartbeat
                            df, _ = self.market_client.get_latest_candles(self.config.exchange.timeframes[0], 10, validate_freshness=False)
                            if not df.empty:
                                last_candle = df.iloc[-1]
                                heartbeat_msg = (
                                    f"💚 <b>BTC Scanner Heartbeat</b>\n\n"
                                    f"⏰ Time: {datetime.now().strftime('%H:%M:%S UTC')}\n"
                                    f"💰 Price: ${last_candle['close']:,.2f}\n"
                                    f"📊 Volume: {last_candle['volume']:,.0f}\n"
                                    f"📈 RSI: {last_candle.get('rsi', 0):.1f}\n"
                                    f"🔍 Status: Actively scanning..."
                                )
                                self.alerter.send_message(heartbeat_msg)
                                last_heartbeat = current_time
                        except Exception as e:
                            logger.warning(f"Failed to send heartbeat: {e}")
                    
                    # Wait 10 seconds before next poll
                    time.sleep(10)
                    
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    self.health_monitor.record_error(e)
                    time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}", exc_info=True)
            self.health_monitor.record_error(e)
            self.alerter.send_error_alert(e, "Main loop critical error")
            raise
        finally:
            self.stop()
    
    def _retry_fetch_with_backoff(
        self, 
        timeframe: str, 
        max_retries: int = 3
    ) -> tuple:
        """
        Attempt to fetch fresh data with exponential backoff.
        
        Args:
            timeframe: Timeframe to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (DataFrame or None, is_fresh: bool)
        """
        import pandas as pd
        
        backoff_delays = [5, 10, 30]  # seconds
        
        for attempt in range(max_retries):
            if attempt > 0:
                delay = backoff_delays[min(attempt - 1, len(backoff_delays) - 1)]
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} for {timeframe} in {delay}s...")
                time.sleep(delay)
            
            try:
                df, is_fresh = self.market_client.get_latest_candles(timeframe, 500)
                
                if is_fresh:
                    logger.info(f"Successfully fetched fresh data for {timeframe} on attempt {attempt + 1}")
                    return df, True
                else:
                    logger.warning(f"Fetched data for {timeframe} is still stale on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"Failed to fetch data for {timeframe} on attempt {attempt + 1}: {e}")
        
        logger.error(f"All {max_retries} retry attempts failed for {timeframe}")
        return None, False
    
    def _get_current_price_for_trades(self) -> float | None:
        """
        Get the most recent price for trade updates, using fallback strategies.
        
        Priority:
        1. Latest candle from primary timeframe (if fresh)
        2. Cached price from last successful fetch (if < 5 min old)
        3. None (skip trade updates)
        
        Returns:
            Current price or None if no valid price available
        """
        # Try to get fresh price from primary timeframe
        try:
            primary_tf = self.config.exchange.timeframes[0]
            df, is_fresh = self.market_client.get_latest_candles(primary_tf, 10)
            
            if not df.empty and is_fresh:
                current_price = df.iloc[-1]['close']
                # Update cache
                self.last_known_price = current_price
                self.last_known_price_time = datetime.now()
                logger.debug(f"Using live price for trade updates: ${current_price:.2f}")
                return current_price
                
        except Exception as e:
            logger.warning(f"Failed to fetch live price for trade updates: {e}")
        
        # Fallback to cached price if recent enough
        if self.last_known_price and self.last_known_price_time:
            cache_age = (datetime.now() - self.last_known_price_time).total_seconds()
            
            if cache_age < 300:  # 5 minutes
                logger.warning(
                    f"Using cached price for trade updates: ${self.last_known_price:.2f} "
                    f"(age: {cache_age:.0f}s)"
                )
                return self.last_known_price
            else:
                logger.error(
                    f"Cached price too old ({cache_age:.0f}s), cannot update trades"
                )
        
        logger.error("No valid price available for trade updates")
        return None
    
    def _send_stale_data_alert(self, timeframe: str, age_seconds: float) -> None:
        """
        Send alert when data remains stale after retries.
        
        Args:
            timeframe: Timeframe with stale data
            age_seconds: Age of the stale data in seconds
        """
        # Check if we should send alert (3+ consecutive stale occurrences)
        if self.stale_data_count.get(timeframe, 0) < 3:
            return
        
        # Check deduplication (no alert within last 15 minutes)
        last_alert = self.last_stale_alert_time.get(timeframe)
        if last_alert:
            time_since_alert = (datetime.now() - last_alert).total_seconds()
            if time_since_alert < 900:  # 15 minutes
                logger.debug(f"Stale data alert suppressed for {timeframe} (last alert {time_since_alert:.0f}s ago)")
                return
        
        # Get last fresh time
        last_fresh = self.last_fresh_data_time.get(timeframe)
        last_fresh_str = last_fresh.strftime('%H:%M:%S UTC') if last_fresh else 'Unknown'
        
        # Get threshold for this timeframe
        from src.market_data_client import FRESHNESS_THRESHOLDS
        threshold = FRESHNESS_THRESHOLDS.get(timeframe, 300)
        
        message = f"""
⚠️ *STALE DATA ALERT*

*Timeframe:* {timeframe}
*Data Age:* {age_seconds / 60:.1f} minutes
*Last Fresh:* {last_fresh_str}
*Threshold:* {threshold} seconds

The scanner is receiving outdated market data.
Trade monitoring may be delayed.

*Actions:*
• Check exchange API status
• Verify internet connection
• Scanner will continue retrying

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        try:
            self.alerter.send_message(message)
            self.last_stale_alert_time[timeframe] = datetime.now()
            logger.info(f"Sent stale data alert for {timeframe}")
        except Exception as e:
            logger.error(f"Failed to send stale data alert: {e}")
    
    def _send_trade_update_failure_alert(self) -> None:
        """Send alert when trade updates fail repeatedly."""
        # Only send after 3 consecutive failures
        if self.trade_update_failure_count < 3:
            return
        
        last_update_str = self.last_trade_update_time.strftime('%H:%M:%S UTC') if self.last_trade_update_time else 'Never'
        active_count = self.trade_tracker.get_active_count()
        
        message = f"""
🚨 *TRADE UPDATE FAILURE*

Cannot update active trades due to stale data.
TP/SL notifications may be delayed.

*Last Successful Update:* {last_update_str}
*Active Trades:* {active_count}
*Failure Count:* {self.trade_update_failure_count}

The scanner is attempting to recover.

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        try:
            self.alerter.send_message(message)
            logger.info("Sent trade update failure alert")
            # Reset counter after sending alert to avoid spam
            self.trade_update_failure_count = 0
        except Exception as e:
            logger.error(f"Failed to send trade update failure alert: {e}")
    
    def _send_recovery_alert(self, timeframe: str, stale_duration_seconds: float) -> None:
        """
        Send alert when data freshness is restored.
        
        Args:
            timeframe: Timeframe that recovered
            stale_duration_seconds: How long data was stale
        """
        message = f"""
✅ *DATA FRESHNESS RESTORED*

*Timeframe:* {timeframe}
Fresh data received after {stale_duration_seconds / 60:.1f} minutes

Trade monitoring has resumed normally.

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        try:
            self.alerter.send_message(message)
            logger.info(f"Sent recovery alert for {timeframe}")
        except Exception as e:
            logger.error(f"Failed to send recovery alert: {e}")
    
    def stop(self) -> None:
        """Stop the scanner application gracefully."""
        logger.info("Shutting down scanner...")
        
        self.running = False
        self.shutdown_event.set()
        
        # Stop Excel reporter
        if self.excel_reporter:
            self.excel_reporter.stop()
        
        # Stop WebSocket (if enabled)
        if self.ws_streamer:
            self.ws_streamer.stop()
            logger.info("WebSocket streamer stopped")
        
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
            
            # Validate market data
            is_valid, errors = self.data_validator.validate_market_data(data_with_indicators, self.config.exchange.symbol)
            if not is_valid:
                logger.warning(f"Market data validation failed: {', '.join(errors)}")
                return
            
            # Detect signals
            signal = self.signal_detector.detect_signals(data_with_indicators, timeframe)
            
            if signal:
                logger.info(f"🎯 Preliminary signal detected: {signal.signal_type} on {timeframe} - {signal.strategy}")
                
                # Apply Signal Quality Filter
                filter_result = self.quality_filter.evaluate_signal(signal, data_with_indicators)
                
                if not filter_result.passed:
                    logger.info(f"❌ Signal rejected by quality filter: {filter_result.rejection_reason}")
                    return
                
                # Apply Liquidity Filter
                asset_symbol = 'BTC'  # For BTC scanner
                asset_config = self.signal_detector.config.get('asset_specific', {}).get(asset_symbol, {})
                liquidity_ok, liquidity_reason = self.liquidity_filter.filter_signal(
                    signal.timestamp, asset_symbol, asset_config, data_with_indicators
                )
                
                if not liquidity_ok:
                    logger.info(f"❌ Signal rejected by liquidity filter: {liquidity_reason}")
                    return
                
                # Signal passed all filters!
                logger.info(f"✅ Signal APPROVED: {signal.signal_type} on {timeframe}")
                logger.info(f"   Confidence: {filter_result.confidence_score}/5, Factors: {len(filter_result.confluence_factors)}/7")
                
                # Add signal to quality filter history
                self.quality_filter.add_signal_to_history(signal)
                
                # Record signal
                self.health_monitor.record_signal(signal.signal_type)
                
                # Create enhanced alert message with quality metrics
                alert_message = signal.to_alert_message(
                    confidence_score=filter_result.confidence_score,
                    confluence_factors=filter_result.confluence_factors
                )
                
                # Send alerts with enhanced message
                alert_success = self.alerter.send_alert(
                    f"{signal.signal_type} Signal - {self.config.exchange.symbol}",
                    alert_message
                )
                
                if alert_success:
                    logger.info("Alert sent successfully")
                else:
                    logger.error("Failed to send alert")
                
                # Update email success rate
                if hasattr(self.alerter, 'email_alerter') and hasattr(self.alerter.email_alerter, 'get_success_rate'):
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
