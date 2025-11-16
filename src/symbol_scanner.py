"""
Symbol Scanner
Wraps existing scanner logic for a single symbol with asset-specific configuration.
"""
import logging
import logging.handlers
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
import pandas as pd

from src.yfinance_client import YFinanceClient
from src.indicator_calculator import IndicatorCalculator
from src.signal_detector import SignalDetector, Signal
from src.fvg_detector import FVGDetector, FVGZone
from src.nwog_detector import NWOGDetector, NWOGZone


logger = logging.getLogger(__name__)


class SymbolScanner:
    """Scanner for a single symbol with asset-specific configuration."""
    
    def __init__(
        self,
        symbol: str,
        asset_type: str,
        display_name: str,
        emoji: str,
        timeframes: List[str],
        asset_config: Dict[str, Any],
        signal_callback: Callable[[str, Signal], None],
        polling_interval: int = 60
    ):
        """
        Initialize symbol scanner.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USD', 'EURUSD=X')
            asset_type: Type of asset ('crypto', 'fx', 'index', 'commodity')
            display_name: Human-readable name (e.g., 'Bitcoin')
            emoji: Symbol emoji for alerts (e.g., '₿')
            timeframes: List of timeframes to monitor
            asset_config: Asset-specific parameters
            signal_callback: Function to call when signal detected (symbol, signal)
            polling_interval: Seconds between data polls
        """
        self.symbol = symbol
        self.asset_type = asset_type
        self.display_name = display_name
        self.emoji = emoji
        self.timeframes = timeframes
        self.config = asset_config
        self.signal_callback = signal_callback
        self.polling_interval = polling_interval
        
        self.running = False
        self.error_count = 0
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.max_errors = 10
        self.last_scan_time: Optional[datetime] = None
        self.scan_count = 0
        self.paused = False
        self.pause_reason = ""
        self.reconnect_backoff = 1  # Start with 1 second backoff
        
        # Volatility and volume tracking
        self.current_volatility_pct: float = 0.0
        self.avg_volume: float = 0.0
        self.volume_threshold_met: bool = True
        self.volatility_thresholds = asset_config.get('volatility_thresholds', {
            'min_atr_percent': 0.5,
            'max_atr_percent': 10.0
        })
        
        # Advanced feature detectors
        self.enable_fvg = asset_config.get('enable_fvg', False)
        self.enable_nwog = asset_config.get('enable_nwog', False)
        
        if self.enable_fvg:
            fvg_config = asset_config.get('fvg_config', {})
            self.fvg_detector = FVGDetector(
                min_gap_percent=fvg_config.get('min_gap_percent', 0.2)
            )
            logger.info(f"FVG detection enabled for {display_name}")
        else:
            self.fvg_detector = None
        
        if self.enable_nwog and asset_type == 'index':
            nwog_config = asset_config.get('nwog_config', {})
            self.nwog_detector = NWOGDetector(
                min_gap_percent=nwog_config.get('min_gap_percent', 0.1)
            )
            logger.info(f"NWOG detection enabled for {display_name}")
        else:
            self.nwog_detector = None
        
        # Setup per-symbol logging
        self._setup_symbol_logger()
        
        # Initialize components
        try:
            self.market_client = YFinanceClient(
                symbol=symbol,
                timeframes=timeframes,
                buffer_size=500
            )
            
            self.indicator_calc = IndicatorCalculator()
            
            # Extract signal rules from config
            signal_rules = asset_config.get('signal_rules', {})
            self.signal_detector = SignalDetector(
                volume_spike_threshold=signal_rules.get('volume_spike_threshold', 0.8),
                rsi_min=signal_rules.get('rsi_min', 30),
                rsi_max=signal_rules.get('rsi_max', 70),
                stop_loss_atr_multiplier=signal_rules.get('stop_loss_atr_multiplier', 1.5),
                take_profit_atr_multiplier=signal_rules.get('take_profit_atr_multiplier', 2.0),
                duplicate_time_window_minutes=signal_rules.get('duplicate_time_window_minutes', 5),
                duplicate_price_threshold_percent=signal_rules.get('duplicate_price_threshold_percent', 0.3)
            )
            
            # Set additional config for signal detector
            self.signal_detector.config = {
                'signal_rules': signal_rules
            }
            
            self.symbol_logger.info(f"Initialized SymbolScanner for {display_name} ({symbol})")
            
        except Exception as e:
            logger.error(f"Failed to initialize SymbolScanner for {symbol}: {e}")
            raise
    
    def _setup_symbol_logger(self) -> None:
        """Setup per-symbol log file with rotation."""
        try:
            # Create logs directory
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Create symbol-specific logger
            symbol_clean = self.symbol.replace('/', '_').replace('^', '').replace('=', '').lower()
            log_file = log_dir / f"{symbol_clean}_scanner.log"
            
            # Create logger
            self.symbol_logger = logging.getLogger(f"scanner.{symbol_clean}")
            self.symbol_logger.setLevel(logging.DEBUG)
            
            # Remove existing handlers to avoid duplicates
            self.symbol_logger.handlers = []
            
            # Add rotating file handler (10MB max, 5 backups)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.symbol_logger.addHandler(file_handler)
            
            logger.info(f"Setup per-symbol logging for {self.display_name}: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to setup symbol logger for {self.symbol}: {e}")
            # Fallback to main logger
            self.symbol_logger = logger
    
    def connect(self) -> bool:
        """
        Connect to market data source.
        
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Connecting to market data for {self.display_name}...")
            success = self.market_client.connect()
            
            if success:
                logger.info(f"Successfully connected: {self.display_name}")
                self.error_count = 0
            else:
                logger.error(f"Failed to connect: {self.display_name}")
                self.error_count += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Connection error for {self.display_name}: {e}")
            self.error_count += 1
            return False
    
    def fetch_initial_data(self) -> bool:
        """
        Fetch initial historical data for all timeframes.
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Fetching initial data for {self.display_name}...")
            
            for timeframe in self.timeframes:
                df = self.market_client.get_latest_candles(timeframe, count=500)
                
                if df.empty:
                    logger.warning(f"No data received for {self.display_name} {timeframe}")
                    continue
                
                # Calculate indicators
                df = self._calculate_indicators(df)
                
                logger.info(f"Loaded {len(df)} candles for {self.display_name} {timeframe}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fetch initial data for {self.display_name}: {e}")
            self.error_count += 1
            return False
    
    def scan_timeframe(self, timeframe: str) -> Optional[Signal]:
        """
        Scan a single timeframe for signals.
        
        Args:
            timeframe: Timeframe to scan
            
        Returns:
            Signal if detected, None otherwise
        """
        try:
            # Fetch latest data
            df = self.market_client.get_latest_candles(timeframe, count=500)
            
            if df.empty:
                logger.warning(f"Empty data for {self.display_name} {timeframe}")
                return None
            
            # Calculate indicators
            df = self._calculate_indicators(df)
            
            # Update volatility and volume metrics
            self._update_volatility_metrics(df)
            
            # Check if volume threshold is met
            if not self.volume_threshold_met:
                logger.debug(f"Volume below threshold for {self.display_name}, skipping signal detection")
                return None
            
            # Detect signals
            signal = self.signal_detector.detect_signals(df, timeframe)
            
            if signal:
                # Enhance signal with symbol information
                signal.symbol = self.symbol
                signal.display_name = self.display_name
                signal.emoji = self.emoji
                signal.asset_type = self.asset_type
                
                # Adjust signal sensitivity based on volatility
                if self.current_volatility_pct > self.volatility_thresholds['max_atr_percent']:
                    logger.info(f"High volatility detected ({self.current_volatility_pct:.2f}%), increasing signal sensitivity")
                
                logger.info(f"Signal detected: {self.display_name} {timeframe} {signal.signal_type}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error scanning {self.display_name} {timeframe}: {e}")
            self.error_count += 1
            self.consecutive_errors += 1
            
            # Check if we should pause due to consecutive errors
            if self.consecutive_errors >= self.max_consecutive_errors:
                self.paused = True
                self.pause_reason = f"Too many consecutive errors ({self.consecutive_errors})"
                logger.error(f"Pausing {self.display_name} scanner: {self.pause_reason}")
                
                # Calculate exponential backoff
                self.reconnect_backoff = min(self.reconnect_backoff * 2, 300)  # Max 5 minutes
            
            return None
    
    def scan_all_timeframes(self) -> List[Signal]:
        """
        Scan all timeframes for signals.
        
        Returns:
            List of detected signals
        """
        # Check if paused
        if self.paused:
            logger.debug(f"Scanner for {self.display_name} is paused: {self.pause_reason}")
            
            # Attempt reconnection with backoff
            time.sleep(self.reconnect_backoff)
            logger.info(f"Attempting to reconnect {self.display_name} after {self.reconnect_backoff}s backoff")
            
            # Try a simple health check
            try:
                df = self.market_client.get_latest_candles(self.timeframes[0], count=1)
                if not df.empty:
                    # Success! Reset error state
                    self.paused = False
                    self.pause_reason = ""
                    self.consecutive_errors = 0
                    self.reconnect_backoff = 1
                    logger.info(f"Successfully reconnected {self.display_name}")
                else:
                    logger.warning(f"Reconnection attempt failed for {self.display_name}")
                    return []
            except Exception as e:
                logger.error(f"Reconnection attempt failed for {self.display_name}: {e}")
                return []
        
        signals = []
        
        # Scan for regular signals
        for timeframe in self.timeframes:
            try:
                signal = self.scan_timeframe(timeframe)
                if signal:
                    # Reset consecutive errors on successful signal detection
                    self.consecutive_errors = 0
                    self.reconnect_backoff = 1
                    
                    signals.append(signal)
                    
                    # Call callback
                    if self.signal_callback:
                        self.signal_callback(self.symbol, signal)
                        
            except Exception as e:
                logger.error(f"Error in scan_all_timeframes for {self.display_name} {timeframe}: {e}")
                continue
        
        # Scan for FVG signals on higher timeframes
        if self.enable_fvg and self.fvg_detector:
            try:
                fvg_signal = self._scan_fvg_signals()
                if fvg_signal:
                    signals.append(fvg_signal)
                    if self.signal_callback:
                        self.signal_callback(self.symbol, fvg_signal)
            except Exception as e:
                logger.error(f"Error scanning FVG signals for {self.display_name}: {e}")
        
        # Scan for NWOG signals
        if self.enable_nwog and self.nwog_detector:
            try:
                nwog_signal = self._scan_nwog_signals()
                if nwog_signal:
                    signals.append(nwog_signal)
                    if self.signal_callback:
                        self.signal_callback(self.symbol, nwog_signal)
            except Exception as e:
                logger.error(f"Error scanning NWOG signals for {self.display_name}: {e}")
        
        self.last_scan_time = datetime.now()
        self.scan_count += 1
        
        return signals
    
    def run(self) -> None:
        """
        Main scanning loop.
        Continuously scans all timeframes at polling interval.
        """
        self.running = True
        logger.info(f"Starting scanner loop for {self.display_name}")
        
        while self.running:
            try:
                # Check error threshold
                if self.error_count >= self.max_errors:
                    logger.error(f"Max errors reached for {self.display_name}, pausing scanner")
                    time.sleep(300)  # Wait 5 minutes before retry
                    self.error_count = 0
                    
                    # Try to reconnect
                    if not self.connect():
                        continue
                
                # Scan all timeframes
                self.scan_all_timeframes()
                
                # Wait for next poll
                time.sleep(self.polling_interval)
                
            except KeyboardInterrupt:
                logger.info(f"Scanner interrupted for {self.display_name}")
                break
            except Exception as e:
                logger.error(f"Error in scanner loop for {self.display_name}: {e}")
                self.error_count += 1
                time.sleep(self.polling_interval)
        
        self.running = False
        logger.info(f"Scanner stopped for {self.display_name}")
    
    def stop(self) -> None:
        """Stop the scanner loop."""
        logger.info(f"Stopping scanner for {self.display_name}")
        self.running = False
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicators added
        """
        try:
            # EMAs
            df['ema_9'] = self.indicator_calc.calculate_ema(df, 9)
            df['ema_21'] = self.indicator_calc.calculate_ema(df, 21)
            df['ema_50'] = self.indicator_calc.calculate_ema(df, 50)
            df['ema_100'] = self.indicator_calc.calculate_ema(df, 100)
            df['ema_200'] = self.indicator_calc.calculate_ema(df, 200)
            
            # VWAP
            df['vwap'] = self.indicator_calc.calculate_vwap(df)
            
            # ATR
            df['atr'] = self.indicator_calc.calculate_atr(df, 14)
            
            # RSI
            df['rsi'] = self.indicator_calc.calculate_rsi(df, 14)
            
            # Volume MA
            df['volume_ma'] = self.indicator_calc.calculate_volume_ma(df, 20)
            
            # Stochastic
            stoch_k, stoch_d = self.indicator_calc.calculate_stochastic(df, k_period=14, d_period=3, smooth_k=3)
            df['stoch_k'] = stoch_k
            df['stoch_d'] = stoch_d
            
            # ADX
            df['adx'] = self.indicator_calc.calculate_adx(df, period=14)
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {self.display_name}: {e}")
            return df
    
    def _update_volatility_metrics(self, df: pd.DataFrame) -> None:
        """
        Update volatility and volume metrics.
        
        Args:
            df: DataFrame with indicators
        """
        try:
            if df.empty or len(df) < 20:
                return
            
            last_row = df.iloc[-1]
            
            # Calculate 24h volatility (ATR as percentage of price)
            if 'atr' in df.columns and 'close' in df.columns:
                atr = last_row['atr']
                price = last_row['close']
                self.current_volatility_pct = (atr / price) * 100 if price > 0 else 0
            
            # Calculate average volume
            if 'volume_ma' in df.columns:
                self.avg_volume = last_row['volume_ma']
            
            # Check volume threshold
            if 'volume' in df.columns and self.avg_volume > 0:
                current_volume = last_row['volume']
                volume_ratio = current_volume / self.avg_volume
                
                # Pause if volume is too low (< 0.5x average)
                self.volume_threshold_met = volume_ratio >= 0.5
                
                if not self.volume_threshold_met:
                    logger.debug(f"Low volume for {self.display_name}: {volume_ratio:.2f}x average")
            
        except Exception as e:
            logger.error(f"Error updating volatility metrics for {self.display_name}: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scanner statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'symbol': self.symbol,
            'display_name': self.display_name,
            'asset_type': self.asset_type,
            'timeframes': self.timeframes,
            'running': self.running,
            'scan_count': self.scan_count,
            'error_count': self.error_count,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'polling_interval': self.polling_interval,
            'volatility_pct': round(self.current_volatility_pct, 2),
            'avg_volume': round(self.avg_volume, 0),
            'volume_threshold_met': self.volume_threshold_met
        }
    
    def _scan_fvg_signals(self) -> Optional[Signal]:
        """
        Scan for FVG-based signals.
        
        Returns:
            Signal if FVG setup detected, None otherwise
        """
        try:
            # Use higher timeframe for FVG detection (4h or 1d)
            higher_tf = '4h' if '4h' in self.timeframes else ('1d' if '1d' in self.timeframes else self.timeframes[-1])
            df_higher = self.market_client.get_latest_candles(higher_tf, count=100)
            
            if df_higher.empty:
                return None
            
            # Detect FVGs
            new_fvgs = self.fvg_detector.detect_fvgs(df_higher, higher_tf)
            
            # Get active FVGs
            active_fvgs = self.fvg_detector.get_active_fvgs(higher_tf)
            
            if not active_fvgs:
                return None
            
            # Check if price is re-entering any FVG zone
            current_price = df_higher.iloc[-1]['close']
            
            for fvg in active_fvgs:
                if self.fvg_detector.check_fvg_reentry(current_price, fvg):
                    # Price in FVG zone - check lower timeframe confirmation
                    lower_tf = '1h' if '1h' in self.timeframes else self.timeframes[0]
                    df_lower = self.market_client.get_latest_candles(lower_tf, count=20)
                    
                    shift_detected, shift_desc = self.fvg_detector.detect_lower_tf_shift(df_lower, fvg)
                    
                    if shift_detected:
                        # Generate FVG signal
                        df_higher = self._calculate_indicators(df_higher)
                        last_row = df_higher.iloc[-1]
                        
                        # Calculate targets
                        target1, target2 = self.fvg_detector.calculate_fvg_targets(df_higher, fvg)
                        
                        # Determine signal type
                        signal_type = "SHORT" if fvg.fvg_type == 'inverse' else "LONG"
                        
                        # Create signal
                        from src.signal_detector import Signal
                        signal = Signal(
                            timestamp=datetime.now(),
                            signal_type=signal_type,
                            timeframe=higher_tf,
                            entry_price=current_price,
                            stop_loss=fvg.high if signal_type == "SHORT" else fvg.low,
                            take_profit=target1,
                            atr=last_row.get('atr', current_price * 0.02),
                            risk_reward=abs(target1 - current_price) / abs(current_price - (fvg.high if signal_type == "SHORT" else fvg.low)),
                            market_bias="bearish" if signal_type == "SHORT" else "bullish",
                            confidence=5,
                            indicators={
                                'ema_9': last_row.get('ema_9', 0),
                                'ema_21': last_row.get('ema_21', 0),
                                'ema_50': last_row.get('ema_50', 0),
                                'rsi': last_row.get('rsi', 50),
                                'volume': last_row.get('volume', 0),
                                'volume_ma': last_row.get('volume_ma', 1),
                                'vwap': last_row.get('vwap', current_price)
                            },
                            symbol=self.symbol,
                            reasoning=f"FVG {fvg.fvg_type} zone re-entry with {shift_desc}. Gap: ${fvg.low:.2f}-${fvg.high:.2f} ({fvg.gap_percent:.2f}%)",
                            strategy="FVG"
                        )
                        
                        # Enhance with symbol info
                        signal.display_name = self.display_name
                        signal.emoji = self.emoji
                        signal.asset_type = self.asset_type
                        
                        logger.info(f"FVG signal generated: {self.display_name} {signal_type} at ${current_price:.2f}")
                        return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in _scan_fvg_signals: {e}")
            return None
    
    def _scan_nwog_signals(self) -> Optional[Signal]:
        """
        Scan for NWOG-based signals.
        
        Returns:
            Signal if NWOG setup detected, None otherwise
        """
        try:
            # Use daily timeframe for NWOG detection
            df_daily = self.market_client.get_latest_candles('1d', count=30)
            
            if df_daily.empty:
                return None
            
            # Detect NWOG
            nwog = self.nwog_detector.detect_nwog(df_daily)
            
            # Get active NWOGs
            active_nwogs = self.nwog_detector.get_active_nwogs(max_age_weeks=4)
            
            if not active_nwogs:
                return None
            
            # Check if price is respecting any NWOG zone
            current_price = df_daily.iloc[-1]['close']
            
            for nwog in active_nwogs:
                # Get lower timeframe for confirmation
                lower_tf = '1h' if '1h' in self.timeframes else self.timeframes[0]
                df_lower = self.market_client.get_latest_candles(lower_tf, count=20)
                
                is_respected, respect_desc = self.nwog_detector.check_nwog_respect(
                    current_price, nwog, df_lower
                )
                
                if is_respected:
                    # Generate NWOG signal
                    df_daily = self._calculate_indicators(df_daily)
                    last_row = df_daily.iloc[-1]
                    
                    # Calculate targets
                    target1, target2 = self.nwog_detector.calculate_nwog_targets(nwog, df_daily)
                    
                    # Determine signal type
                    signal_type = "SHORT" if nwog.gap_type == 'bearish' else "LONG"
                    
                    # Create signal
                    from src.signal_detector import Signal
                    signal = Signal(
                        timestamp=datetime.now(),
                        signal_type=signal_type,
                        timeframe='1d',
                        entry_price=current_price,
                        stop_loss=nwog.gap_low if signal_type == "SHORT" else nwog.gap_high,
                        take_profit=target1,
                        atr=last_row.get('atr', current_price * 0.02),
                        risk_reward=abs(target1 - current_price) / abs(current_price - (nwog.gap_low if signal_type == "SHORT" else nwog.gap_high)),
                        market_bias="bearish" if signal_type == "SHORT" else "bullish",
                        confidence=5,
                        indicators={
                            'ema_9': last_row.get('ema_9', 0),
                            'ema_21': last_row.get('ema_21', 0),
                            'ema_50': last_row.get('ema_50', 0),
                            'rsi': last_row.get('rsi', 50),
                            'volume': last_row.get('volume', 0),
                            'volume_ma': last_row.get('volume_ma', 1),
                            'vwap': last_row.get('vwap', current_price)
                        },
                        symbol=self.symbol,
                        reasoning=f"NWOG {nwog.gap_type} zone respect. {respect_desc}. Gap: ${nwog.gap_low:.2f}-${nwog.gap_high:.2f} ({nwog.gap_size_percent:.2f}%). Respected {nwog.respect_count}x",
                        strategy="NWOG"
                    )
                    
                    # Enhance with symbol info
                    signal.display_name = self.display_name
                    signal.emoji = self.emoji
                    signal.asset_type = self.asset_type
                    
                    logger.info(f"NWOG signal generated: {self.display_name} {signal_type} at ${current_price:.2f}")
                    return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in _scan_nwog_signals: {e}")
            return None
    
    def get_current_price(self) -> Optional[float]:
        """
        Get current price for the symbol.
        
        Returns:
            Current price or None
        """
        try:
            return self.market_client.get_current_price()
        except Exception as e:
            logger.error(f"Error getting current price for {self.display_name}: {e}")
            return None


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    def signal_handler(symbol: str, signal: Signal):
        print(f"Signal received: {symbol} {signal.signal_type} at ${signal.entry_price:.2f}")
    
    config = {
        'signal_rules': {
            'volume_spike_threshold': 0.8,
            'rsi_min': 30,
            'rsi_max': 70,
            'stop_loss_atr_multiplier': 1.5,
            'take_profit_atr_multiplier': 2.0
        }
    }
    
    scanner = SymbolScanner(
        symbol='BTC-USD',
        asset_type='crypto',
        display_name='Bitcoin',
        emoji='₿',
        timeframes=['5m', '15m'],
        asset_config=config,
        signal_callback=signal_handler,
        polling_interval=60
    )
    
    if scanner.connect():
        scanner.fetch_initial_data()
        print(f"Scanner ready: {scanner.get_statistics()}")
