"""Signal detection with confluence-based trading logic."""

from dataclasses import dataclass, asdict

from datetime import datetime, timedelta

from collections import deque

from typing import Optional, Dict, List

import pandas as pd

import logging



from src.trend_analyzer import TrendAnalyzer

from src.h4_hvg_detector import GapInfo, H4HVGDetector

from src.sl_tp_calculator import SLTPCalculator

from src.symbol_context import SymbolContext





logger = logging.getLogger(__name__)





@dataclass
class Signal:
    """Trading signal with entry, stop-loss, and take-profit levels."""
    timestamp: datetime
    signal_type: str  # "LONG" or "SHORT"
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    atr: float
    risk_reward: float
    market_bias: str  # "bullish", "bearish", "neutral"
    confidence: int  # 3-5 (number of confluence factors met)
    indicators: Dict[str, float]  # Snapshot of indicator values
    symbol_context: Optional[SymbolContext] = None  # Symbol context (required for new signals)
    reasoning: str = ""  # Detailed explanation of why this signal was generated
    symbol: str = "BTC/USD"  # Trading symbol (e.g., "BTC/USD", "XAU/USD", "US30") - DEPRECATED, use symbol_context

    strategy: str = ""  # Strategy name (e.g., "Trend Following", "EMA Crossover")

    trend_direction: Optional[str] = None  # "uptrend" or "downtrend" for trend signals

    swing_points: Optional[int] = None  # Number of swing highs/lows for trend signals

    pullback_depth: Optional[float] = None  # Pullback percentage for trend signals
    
    # H4 HVG specific fields
    gap_info: Optional['GapInfo'] = None  # Gap information for H4 HVG signals
    volume_spike_ratio: Optional[float] = None  # Volume spike ratio for H4 HVG signals
    confluence_factors: Optional[List[str]] = None  # List of confluence factors
    
    # Strategy-specific metadata
    strategy_metadata: Optional[Dict] = None  # Strategy-specific data (e.g., Fib levels, SR levels)

    
    def __post_init__(self):
        """Validate symbol context on creation"""
        # If symbol_context not provided, create from legacy symbol field
        if self.symbol_context is None and self.symbol:
            # Try to extract internal symbol from legacy format
            symbol_map = {
                "BTC/USD": "BTC",
                "BTC": "BTC",
                "XAU/USD": "XAUUSD",
                "XAUUSD": "XAUUSD",
                "US30": "US30"
            }
            internal_symbol = symbol_map.get(self.symbol, "BTC")
            try:
                self.symbol_context = SymbolContext.from_symbol(internal_symbol)
                logger.debug(f"Created symbol context from legacy symbol: {self.symbol} -> {internal_symbol}")
            except ValueError as e:
                logger.error(f"Failed to create symbol context from legacy symbol '{self.symbol}': {e}")
                raise ValueError(f"Signal must have valid symbol context. Legacy symbol '{self.symbol}' could not be converted.")
        
        # Validate symbol context
        if self.symbol_context and not self.symbol_context.validate():
            raise ValueError("Signal must have valid symbol context")

    

    def to_dict(self) -> dict:

        """Convert signal to dictionary."""

        data = asdict(self)
        # Convert symbol_context to dict if present
        if self.symbol_context:
            data['symbol_context'] = self.symbol_context.to_dict()
        return data

    

    def get_stop_distance_percent(self) -> float:

        """Calculate stop-loss distance as percentage of entry."""

        return abs(self.entry_price - self.stop_loss) / self.entry_price * 100

    

    def get_profit_distance_percent(self) -> float:

        """Calculate take-profit distance as percentage of entry."""

        return abs(self.take_profit - self.entry_price) / self.entry_price * 100

    

    def get_breakeven_price(self) -> float:

        """Calculate breakeven price (50% to target)."""

        if self.signal_type == "LONG":

            return self.entry_price + (self.take_profit - self.entry_price) * 0.5

        else:

            return self.entry_price - (self.entry_price - self.take_profit) * 0.5
    
    def to_alert_message(self, confidence_score: int = None, confluence_factors: List[str] = None) -> str:
        """
        Format signal for trader alert with quality metrics
        
        Args:
            confidence_score: Optional confidence score (1-5) from quality filter
            confluence_factors: Optional list of confluence factors that passed
            
        Returns:
            Formatted alert message string
        """
        # Use provided confidence or fall back to signal's confidence
        conf_score = confidence_score if confidence_score is not None else self.confidence
        
        # Create confidence stars
        stars = '⭐' * conf_score
        
        # Get symbol display name
        symbol_display = self.symbol
        if self.symbol_context:
            symbol_display = getattr(self.symbol_context, 'display_symbol', self.symbol_context.symbol if hasattr(self.symbol_context, 'symbol') else self.symbol)
        
        # Build message
        message = f"""
🔔 {self.signal_type} Signal - {symbol_display} ({self.timeframe})
Strategy: {self.strategy}
Confidence: {stars} ({conf_score}/5)

💰 Entry: {self.entry_price:.2f}
🛑 Stop Loss: {self.stop_loss:.2f}
🎯 Take Profit: {self.take_profit:.2f}
📊 Risk/Reward: {self.risk_reward:.2f}

"""
        
        # Add confluence factors if provided
        if confluence_factors:
            factors_met = len(confluence_factors)
            message += f"✅ Confluence: {factors_met}/7 factors\n"
            message += f"Key Factors: {', '.join(confluence_factors[:3])}\n\n"
        
        # Add market context
        if self.indicators:
            message += "📈 Market Context:\n"
            if 'rsi' in self.indicators:
                message += f"RSI: {self.indicators['rsi']:.1f}"
            if 'adx' in self.indicators:
                message += f" | ADX: {self.indicators['adx']:.1f}"
            if 'volume' in self.indicators and 'volume_ma' in self.indicators:
                vol_ratio = self.indicators['volume'] / self.indicators['volume_ma']
                message += f"\nVolume: {vol_ratio:.2f}x avg"
            message += "\n"
        
        # Add reasoning
        if self.reasoning:
            message += f"\n💡 {self.reasoning}"
        
        return message.strip()





class SignalDetector:

    """

    Detect trading signals using confluence of multiple technical indicators.

    

    Implements bullish/bearish signal detection with duplicate prevention.

    """

    

    def __init__(

        self,

        volume_spike_threshold: float = 1.5,

        rsi_min: int = 30,

        rsi_max: int = 70,

        stop_loss_atr_multiplier: float = 1.5,

        take_profit_atr_multiplier: float = 1.0,

        duplicate_time_window_minutes: int = 5,

        duplicate_price_threshold_percent: float = 0.3

    ):

        """

        Initialize signal detector.

        

        Args:

            volume_spike_threshold: Minimum volume ratio vs MA to confirm signal

            rsi_min: Minimum RSI value (avoid oversold)

            rsi_max: Maximum RSI value (avoid overbought)

            stop_loss_atr_multiplier: ATR multiplier for stop-loss distance

            take_profit_atr_multiplier: ATR multiplier for take-profit distance

            duplicate_time_window_minutes: Time window to block duplicate signals

            duplicate_price_threshold_percent: Price move % to allow new signal

        """

        self.volume_spike_threshold = volume_spike_threshold

        self.rsi_min = rsi_min

        self.rsi_max = rsi_max

        self.stop_loss_atr_multiplier = stop_loss_atr_multiplier

        self.take_profit_atr_multiplier = take_profit_atr_multiplier

        self.duplicate_time_window_minutes = duplicate_time_window_minutes

        self.duplicate_price_threshold_percent = duplicate_price_threshold_percent

        

        # Signal history for duplicate detection

        self.signal_history: deque = deque(maxlen=50)
        
        # H4 HVG detector - will be initialized per-symbol when needed
        # This allows it to work for BTC, Gold, US30, etc.
        self.h4_hvg_detector = None
        self.h4_hvg_detectors = {}  # Cache of detectors per symbol
        
        # Config for optional features (can be set externally)
        self.config = {}

        

        logger.info("Initialized SignalDetector with confluence rules")
    
    def _create_symbol_context(self, symbol: str) -> SymbolContext:
        """
        Create SymbolContext from symbol string
        
        Args:
            symbol: Symbol string (can be legacy format like "BTC/USD" or internal like "BTC")
            
        Returns:
            SymbolContext instance
        """
        # Map legacy symbol formats to internal symbols
        symbol_map = {
            "BTC/USD": "BTC",
            "BTC": "BTC",
            "XAU/USD": "XAUUSD",
            "XAUUSD": "XAUUSD",
            "US30": "US30"
        }
        
        internal_symbol = symbol_map.get(symbol, symbol)
        
        try:
            return SymbolContext.from_symbol(internal_symbol)
        except ValueError:
            # Fallback to BTC if unknown
            logger.warning(f"Unknown symbol '{symbol}', defaulting to BTC")
            return SymbolContext.from_symbol("BTC")
    
    def _get_asset_symbol(self, symbol: str) -> str:
        """
        Get asset symbol for configuration lookup
        
        Args:
            symbol: Symbol string (can be legacy format like "BTC/USD" or internal like "BTC")
            
        Returns:
            Asset symbol for config (BTC, XAUUSD, US30)
        """
        symbol_map = {
            "BTC/USD": "BTC",
            "BTC": "BTC",
            "XAU/USD": "XAUUSD",
            "XAUUSD": "XAUUSD",
            "US30": "US30"
        }
        
        return symbol_map.get(symbol, "BTC")
    
    def configure_h4_hvg(self, h4_hvg_config: dict, symbol: str) -> None:
        """
        Configure H4 HVG detector with specific settings for a symbol.
        
        Args:
            h4_hvg_config: H4 HVG configuration dictionary
            symbol: Trading symbol (BTC/USD, XAU/USD, US30, etc.)
        """
        try:
            # Create detector with custom config for this symbol
            self.h4_hvg_detectors[symbol] = H4HVGDetector(config=h4_hvg_config, symbol=symbol)
            logger.info(f"H4HVGDetector configured for {symbol} with custom settings")
        except Exception as e:
            logger.error(f"Error configuring H4HVGDetector for {symbol}: {e}")
    
    def _detect_mean_reversion(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:
        """
        Detect mean reversion signals.
        
        Strategy:
        - Price overextended (> 1.5 ATR from VWAP)
        - RSI extremes (< 25 oversold or > 75 overbought)
        - Reversal candle patterns (pin bar, doji, engulfing)
        - Volume >= 1.3x average
        - Target VWAP for mean reversion
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Signal if detected, None otherwise
        """
        try:
            if len(data) < 3:
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['vwap', 'rsi', 'atr', 'volume', 'volume_ma']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for mean reversion detection")
                return None
            
            # Check for NaN values
            if pd.isna(last['vwap']) or pd.isna(last['rsi']) or pd.isna(last['atr']):
                logger.warning(f"[{timeframe}] NaN values in indicators, skipping mean reversion")
                return None
            
            # Get asset-specific configuration
            asset_symbol = self._get_asset_symbol(symbol)
            asset_config = self.config.get('asset_specific', {}).get(asset_symbol, {})
            
            # Get configuration values with asset-specific overrides - Updated to 1.5x
            volume_threshold = asset_config.get('volume_thresholds', {}).get('mean_reversion',
                               self.config.get('signal_rules', {}).get('volume_mean_reversion', 1.5))
            
            atr = last['atr']
            vwap = last['vwap']
            current_price = last['close']
            
            # Check overextension (> 1.8 ATR from VWAP) - Updated from 1.5
            distance_from_vwap = abs(current_price - vwap)
            
            if distance_from_vwap < (atr * 1.8):
                logger.debug(f"[{timeframe}] Price not overextended: distance {distance_from_vwap:.2f} < {atr * 1.8:.2f} (1.8 ATR)")
                return None
            
            # Check RSI extremes - Updated to <20 or >80 (stricter)
            rsi_overbought = last['rsi'] > 80
            rsi_oversold = last['rsi'] < 20
            
            if not (rsi_overbought or rsi_oversold):
                logger.debug(f"[{timeframe}] RSI not extreme: {last['rsi']:.1f} (need < 20 or > 80)")
                return None
            
            # Calculate volume ratio
            volume_ratio = last['volume'] / last['volume_ma']
            
            # Check volume confirmation
            if volume_ratio < volume_threshold:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= {volume_threshold}x)")
                return None
            
            # Detect reversal candles
            is_pin_bar = self._is_pin_bar(last)
            is_engulfing = self._is_engulfing(last, prev)
            is_doji = self._is_doji(last)
            
            if not (is_pin_bar or is_engulfing or is_doji):
                logger.info(f"[{timeframe}] Mean reversion rejected - no clear reversal pattern (pin bar, engulfing, or doji)")
                return None
            
            pattern_name = "pin bar" if is_pin_bar else ("engulfing" if is_engulfing else "doji")
            
            # Bullish reversal (price below VWAP, oversold)
            if current_price < vwap and rsi_oversold:
                logger.info(f"[{timeframe}] Bullish mean reversion detected - Price ${current_price:.2f} < VWAP ${vwap:.2f}, RSI {last['rsi']:.1f}, {pattern_name} pattern")
                logger.info(f"[{timeframe}] Overextension: {distance_from_vwap:.2f} ({distance_from_vwap/atr:.1f} ATR), Volume {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry - (atr * 1.0)
                take_profit = vwap  # Target mean (VWAP)
                
                # Calculate risk/reward
                risk = abs(entry - stop_loss)
                reward = abs(take_profit - entry)
                risk_reward = reward / risk if risk > 0 else 0
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="neutral",
                    confidence=4,
                    indicators={
                        'vwap': vwap,
                        'rsi': last['rsi'],
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Mean Reversion: Price overextended {distance_from_vwap/atr:.1f} ATR below VWAP, RSI {last['rsi']:.1f}, {pattern_name} reversal, Volume {volume_ratio:.2f}x",
                    strategy="Mean Reversion"
                )
                
                return signal
            
            # Bearish reversal (price above VWAP, overbought)
            elif current_price > vwap and rsi_overbought:
                logger.info(f"[{timeframe}] Bearish mean reversion detected - Price ${current_price:.2f} > VWAP ${vwap:.2f}, RSI {last['rsi']:.1f}, {pattern_name} pattern")
                logger.info(f"[{timeframe}] Overextension: {distance_from_vwap:.2f} ({distance_from_vwap/atr:.1f} ATR), Volume {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry + (atr * 1.0)
                take_profit = vwap  # Target mean (VWAP)
                
                # Calculate risk/reward
                risk = abs(stop_loss - entry)
                reward = abs(entry - take_profit)
                risk_reward = reward / risk if risk > 0 else 0
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="neutral",
                    confidence=4,
                    indicators={
                        'vwap': vwap,
                        'rsi': last['rsi'],
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Mean Reversion: Price overextended {distance_from_vwap/atr:.1f} ATR above VWAP, RSI {last['rsi']:.1f}, {pattern_name} reversal, Volume {volume_ratio:.2f}x",
                    strategy="Mean Reversion"
                )
                
                return signal
            
            return None
            
        except KeyError as e:
            logger.error(f"Missing indicator in mean reversion detection: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in mean reversion detection: {e}", exc_info=True)
            return None
    
    def _detect_ema_cloud_breakout(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:
        """
        Detect EMA cloud breakout signals.
        
        Strategy:
        - EMA(21) and EMA(50) aligned (bullish: EMA21 > EMA50, bearish: EMA21 < EMA50)
        - Price vs VWAP (bullish: price > VWAP, bearish: price < VWAP)
        - RSI in range 25-75 (avoid extremes)
        - Volume >= 1.5x average (strong breakout)
        - Range breakout (price breaks recent 10-candle high/low)
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Signal if detected, None otherwise
        """
        try:
            if len(data) < 11:  # Need 10 candles for range + current
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['ema_21', 'ema_50', 'vwap', 'rsi', 'volume', 'volume_ma', 'atr']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for EMA cloud breakout detection")
                return None
            
            # Check for NaN values
            if pd.isna(last['ema_21']) or pd.isna(last['ema_50']) or pd.isna(last['vwap']):
                logger.warning(f"[{timeframe}] NaN values in indicators, skipping EMA cloud breakout")
                return None
            
            # Get asset-specific configuration
            asset_symbol = self._get_asset_symbol(symbol)
            asset_config = self.config.get('asset_specific', {}).get(asset_symbol, {})
            
            # Get configuration values with asset-specific overrides
            volume_threshold = asset_config.get('volume_thresholds', {}).get('breakout',
                               self.config.get('signal_rules', {}).get('volume_ema_cloud_breakout', 1.5))
            
            # Check EMA alignment
            bullish_alignment = last['ema_21'] > last['ema_50']
            bearish_alignment = last['ema_21'] < last['ema_50']
            
            if not (bullish_alignment or bearish_alignment):
                logger.debug(f"[{timeframe}] No EMA alignment: EMA21={last['ema_21']:.2f}, EMA50={last['ema_50']:.2f}")
                return None
            
            # Check VWAP position
            price_above_vwap = last['close'] > last['vwap']
            price_below_vwap = last['close'] < last['vwap']
            
            # Check RSI range (avoid extremes) - Updated to 30-70
            if last['rsi'] < 30 or last['rsi'] > 70:
                logger.debug(f"[{timeframe}] RSI extreme: {last['rsi']:.1f} (need 30-70 for breakout)")
                return None
            
            # Calculate volume ratio
            volume_ratio = last['volume'] / last['volume_ma']
            
            # Check volume threshold
            if volume_ratio < volume_threshold:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= {volume_threshold}x)")
                return None
            
            # Bullish setup
            if bullish_alignment and price_above_vwap:
                # Check for breakout (price breaking above recent 10-candle high by at least 0.2%)
                recent_high = data['high'].iloc[-11:-1].max()
                breakout_threshold = recent_high * 1.002  # 0.2% above
                
                logger.debug(f"[{timeframe}] Bullish EMA cloud: checking breakout above {breakout_threshold:.2f} (0.2% above {recent_high:.2f}), current: {last['close']:.2f}")
                
                if last['close'] > breakout_threshold:
                    logger.info(f"[{timeframe}] Bullish EMA cloud breakout detected - Price {last['close']:.2f} > Recent high {recent_high:.2f}")
                    logger.info(f"[{timeframe}] EMA21 {last['ema_21']:.2f} > EMA50 {last['ema_50']:.2f}, Price > VWAP {last['vwap']:.2f}, RSI {last['rsi']:.1f}, Volume {volume_ratio:.2f}x")
                    
                    entry = last['close']
                    stop_loss = entry - (last['atr'] * 1.2)
                    take_profit = entry + (last['atr'] * 1.5)
                    risk_reward = (take_profit - entry) / (entry - stop_loss)
                    
                    signal = Signal(
                        timestamp=last['timestamp'],
                        signal_type="LONG",
                        timeframe=timeframe,
                        symbol=symbol,
                        symbol_context=self._create_symbol_context(symbol),
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        atr=last['atr'],
                        risk_reward=risk_reward,
                        market_bias="bullish",
                        confidence=4,
                        indicators={
                            'ema_21': last['ema_21'],
                            'ema_50': last['ema_50'],
                            'vwap': last['vwap'],
                            'rsi': last['rsi'],
                            'volume': last['volume'],
                            'volume_ma': last['volume_ma']
                        },
                        reasoning=f"EMA Cloud Breakout: Bullish alignment, price > VWAP, breakout above {recent_high:.2f}, Volume {volume_ratio:.2f}x",
                        strategy="EMA Cloud Breakout"
                    )
                    
                    return signal
            
            # Bearish setup
            elif bearish_alignment and price_below_vwap:
                # Check for breakdown (price breaking below recent 10-candle low by at least 0.2%)
                recent_low = data['low'].iloc[-11:-1].min()
                breakdown_threshold = recent_low * 0.998  # 0.2% below
                
                logger.debug(f"[{timeframe}] Bearish EMA cloud: checking breakdown below {breakdown_threshold:.2f} (0.2% below {recent_low:.2f}), current: {last['close']:.2f}")
                
                if last['close'] < breakdown_threshold:
                    logger.info(f"[{timeframe}] Bearish EMA cloud breakdown detected - Price {last['close']:.2f} < Recent low {recent_low:.2f}")
                    logger.info(f"[{timeframe}] EMA21 {last['ema_21']:.2f} < EMA50 {last['ema_50']:.2f}, Price < VWAP {last['vwap']:.2f}, RSI {last['rsi']:.1f}, Volume {volume_ratio:.2f}x")
                    
                    entry = last['close']
                    stop_loss = entry + (last['atr'] * 1.2)
                    take_profit = entry - (last['atr'] * 1.5)
                    risk_reward = (entry - take_profit) / (stop_loss - entry)
                    
                    signal = Signal(
                        timestamp=last['timestamp'],
                        signal_type="SHORT",
                        timeframe=timeframe,
                        symbol=symbol,
                        symbol_context=self._create_symbol_context(symbol),
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        atr=last['atr'],
                        risk_reward=risk_reward,
                        market_bias="bearish",
                        confidence=4,
                        indicators={
                            'ema_21': last['ema_21'],
                            'ema_50': last['ema_50'],
                            'vwap': last['vwap'],
                            'rsi': last['rsi'],
                            'volume': last['volume'],
                            'volume_ma': last['volume_ma']
                        },
                        reasoning=f"EMA Cloud Breakout: Bearish alignment, price < VWAP, breakdown below {recent_low:.2f}, Volume {volume_ratio:.2f}x",
                        strategy="EMA Cloud Breakout"
                    )
                    
                    return signal
            
            return None
            
        except KeyError as e:
            logger.error(f"Missing indicator in EMA cloud breakout detection: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in EMA cloud breakout detection: {e}", exc_info=True)
            return None
    
    def _detect_trend_alignment(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:
        """
        Detect trend alignment signals - cascade EMA alignment with RSI confirmation.
        
        Strategy:
        - Bullish: Price > EMA9 > EMA21 > EMA50 (cascade alignment)
        - Bearish: Price < EMA9 < EMA21 < EMA50 (cascade alignment)
        - RSI > 50 (bullish) or < 50 (bearish)
        - RSI direction matches signal (rising for LONG, falling for SHORT)
        - ADX >= 19 (strong trend)
        - Volume >= 0.8x average
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Signal if detected, None otherwise
        """
        try:
            if len(data) < 3:
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['ema_9', 'ema_21', 'ema_50', 'rsi', 'adx', 'volume', 'volume_ma', 'atr']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for trend alignment detection")
                return None
            
            # Check for NaN values
            if pd.isna(last['ema_9']) or pd.isna(last['ema_21']) or pd.isna(last['ema_50']):
                logger.warning(f"[{timeframe}] NaN values in EMA indicators, skipping trend alignment")
                return None
            
            # Get asset-specific configuration
            asset_symbol = self._get_asset_symbol(symbol)
            asset_config = self.config.get('asset_specific', {}).get(asset_symbol, {})
            
            # Get configuration values with asset-specific overrides
            adx_threshold = asset_config.get('adx_threshold',
                            self.config.get('signal_rules', {}).get('adx_min_trend_alignment', 19))
            volume_threshold = asset_config.get('volume_thresholds', {}).get('trend_alignment',
                               self.config.get('signal_rules', {}).get('volume_trend_alignment', 0.8))
            
            # Check ADX >= threshold (strong trend)
            if last['adx'] < adx_threshold:
                logger.info(f"[{timeframe}] Trend alignment rejected - ADX too low: {last['adx']:.1f} < {adx_threshold} (asset: {asset_symbol})")
                return None
            
            # Calculate volume ratio
            volume_ratio = last['volume'] / last['volume_ma']
            
            # Check volume threshold
            if volume_ratio < volume_threshold:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= {volume_threshold}x)")
                return None
            
            # Check for bullish cascade alignment
            is_bullish_cascade = (
                last['close'] > last['ema_9'] and
                last['ema_9'] > last['ema_21'] and
                last['ema_21'] > last['ema_50']
            )
            
            # Check for bearish cascade alignment
            is_bearish_cascade = (
                last['close'] < last['ema_9'] and
                last['ema_9'] < last['ema_21'] and
                last['ema_21'] < last['ema_50']
            )
            
            # Log cascade status
            logger.debug(f"[{timeframe}] Checking cascade: Price={last['close']:.2f}, EMA9={last['ema_9']:.2f}, EMA21={last['ema_21']:.2f}, EMA50={last['ema_50']:.2f}")
            
            if is_bullish_cascade:
                logger.info(f"[{timeframe}] Bullish cascade detected: Price > EMA9 > EMA21 > EMA50")
            elif is_bearish_cascade:
                logger.info(f"[{timeframe}] Bearish cascade detected: Price < EMA9 < EMA21 < EMA50")
            else:
                logger.debug(f"[{timeframe}] No trend cascade detected")
                return None
            
            # Check RSI direction (rising for bullish, falling for bearish)
            rsi_rising = last['rsi'] > prev['rsi']
            rsi_falling = last['rsi'] < prev['rsi']
            
            # Bullish Trend Alignment Signal
            if is_bullish_cascade and last['rsi'] > 50 and rsi_rising:
                logger.info(f"[{timeframe}] Bullish trend alignment conditions met - RSI: {last['rsi']:.1f} (rising), ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry - (last['atr'] * self.stop_loss_atr_multiplier)
                take_profit = entry + (last['atr'] * self.take_profit_atr_multiplier)
                risk_reward = (take_profit - entry) / (entry - stop_loss)
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    risk_reward=risk_reward,
                    market_bias="bullish",
                    confidence=4,
                    indicators={
                        'ema_9': last['ema_9'],
                        'ema_21': last['ema_21'],
                        'ema_50': last['ema_50'],
                        'rsi': last['rsi'],
                        'adx': last['adx'],
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Trend Alignment: Bullish cascade with RSI {last['rsi']:.1f} rising, ADX {last['adx']:.1f}, Volume {volume_ratio:.2f}x",
                    strategy="Trend Alignment (Bullish)"
                )
                
                return signal
            
            # Bearish Trend Alignment Signal
            elif is_bearish_cascade and last['rsi'] < 50 and rsi_falling:
                logger.info(f"[{timeframe}] Bearish trend alignment conditions met - RSI: {last['rsi']:.1f} (falling), ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry + (last['atr'] * self.stop_loss_atr_multiplier)
                take_profit = entry - (last['atr'] * self.take_profit_atr_multiplier)
                risk_reward = (entry - take_profit) / (stop_loss - entry)
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    risk_reward=risk_reward,
                    market_bias="bearish",
                    confidence=4,
                    indicators={
                        'ema_9': last['ema_9'],
                        'ema_21': last['ema_21'],
                        'ema_50': last['ema_50'],
                        'rsi': last['rsi'],
                        'adx': last['adx'],
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Trend Alignment: Bearish cascade with RSI {last['rsi']:.1f} falling, ADX {last['adx']:.1f}, Volume {volume_ratio:.2f}x",
                    strategy="Trend Alignment (Bearish)"
                )
                
                return signal
            
            else:
                # Log why signal was not generated
                if is_bullish_cascade:
                    if last['rsi'] <= 50:
                        logger.debug(f"[{timeframe}] Bullish cascade but RSI too low: {last['rsi']:.1f} (need > 50)")
                    elif not rsi_rising:
                        logger.debug(f"[{timeframe}] Bullish cascade but RSI not rising: {prev['rsi']:.1f} -> {last['rsi']:.1f}")
                elif is_bearish_cascade:
                    if last['rsi'] >= 50:
                        logger.debug(f"[{timeframe}] Bearish cascade but RSI too high: {last['rsi']:.1f} (need < 50)")
                    elif not rsi_falling:
                        logger.debug(f"[{timeframe}] Bearish cascade but RSI not falling: {prev['rsi']:.1f} -> {last['rsi']:.1f}")
            
            return None
            
        except KeyError as e:
            logger.error(f"Missing indicator in trend alignment detection: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in trend alignment detection: {e}", exc_info=True)
            return None
    
    def _detect_momentum_shift(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:
        """
        Detect momentum shift signals - catches RSI turning with ADX confirmation.
        
        Strategy:
        - Uses RSI(14) for momentum detection
        - Bullish: RSI increasing over 3 consecutive candles
        - Bearish: RSI decreasing over 3 consecutive candles
        - ADX >= 18 (trend forming, not flat)
        - Volume >= 1.2x average
        - Validates trend context (price vs EMA50)
        - Checks recent 10-candle price action
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Signal if detected, None otherwise
        """
        try:
            if len(data) < 10:  # Need at least 10 candles for recent price trend check
                logger.debug(f"[{timeframe}] Insufficient data for momentum shift: {len(data)} candles")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            prev2 = data.iloc[-3]
            
            # Check for required indicators
            required_indicators = ['rsi', 'adx', 'volume', 'volume_ma', 'atr', 'ema_50']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for momentum shift detection")
                return None
            
            # Check for NaN values
            if pd.isna(last['rsi']) or pd.isna(last['adx']) or pd.isna(last['ema_50']):
                logger.warning(f"[{timeframe}] NaN values in indicators, skipping momentum shift")
                return None
            
            # Get asset-specific configuration
            asset_symbol = self._get_asset_symbol(symbol)
            asset_config = self.config.get('asset_specific', {}).get(asset_symbol, {})
            
            # Get configuration values with asset-specific overrides
            adx_threshold = self.config.get('signal_rules', {}).get('adx_min_momentum_shift', 18)
            volume_threshold = asset_config.get('volume_thresholds', {}).get('momentum_shift', 
                                self.config.get('signal_rules', {}).get('volume_momentum_shift', 1.2))
            rsi_momentum_threshold = asset_config.get('rsi_momentum_threshold',
                                      self.config.get('signal_rules', {}).get('rsi_momentum_threshold', 3.0))
            sl_multiplier = self.config.get('signal_rules', {}).get('momentum_shift_sl_multiplier', 2.0)
            tp_multiplier = self.config.get('signal_rules', {}).get('momentum_shift_tp_multiplier', 3.0)
            
            # Check ADX >= threshold (trend forming)
            if last['adx'] < adx_threshold:
                logger.debug(f"[{timeframe}] ADX too low: {last['adx']:.1f} (need >= {adx_threshold} for momentum shift)")
                return None
            
            # Calculate volume ratio
            volume_ratio = last['volume'] / last['volume_ma']
            
            # Check volume threshold
            if volume_ratio < volume_threshold:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= {volume_threshold}x)")
                return None
            
            # Get RSI values
            rsi_current = last['rsi']
            rsi_prev = prev['rsi']
            rsi_prev2 = prev2['rsi']
            
            # Calculate RSI change
            rsi_change = rsi_current - rsi_prev2
            
            logger.debug(f"[{timeframe}] Checking momentum shift: RSI {rsi_prev2:.1f} -> {rsi_prev:.1f} -> {rsi_current:.1f}, change: {rsi_change:.1f}")
            
            # Bullish Momentum Shift: RSI increasing over 3 candles
            if rsi_current > rsi_prev and rsi_prev > rsi_prev2 and rsi_change >= rsi_momentum_threshold:
                # CRITICAL: Check if we're actually in an uptrend
                if last['close'] < last['ema_50']:
                    logger.debug(f"[{timeframe}] Bullish RSI turn rejected - price below EMA(50): ${last['close']:.2f} < ${last['ema_50']:.2f} (downtrend)")
                    return None
                
                # Check recent price action (last 10 candles should show upward bias)
                recent_close = data['close'].iloc[-10]
                if last['close'] < recent_close:
                    logger.debug(f"[{timeframe}] Bullish RSI turn rejected - price declining over last 10 candles: ${recent_close:.2f} -> ${last['close']:.2f}")
                    return None
                
                logger.info(f"[{timeframe}] Bullish momentum shift detected - RSI: {rsi_prev2:.1f} -> {rsi_prev:.1f} -> {rsi_current:.1f} (change: +{rsi_change:.1f})")
                logger.info(f"[{timeframe}] Trend confirmed: Price ${last['close']:.2f} > EMA(50) ${last['ema_50']:.2f}")
                logger.info(f"[{timeframe}] ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry - (last['atr'] * sl_multiplier)
                take_profit = entry + (last['atr'] * tp_multiplier)
                risk_reward = (take_profit - entry) / (entry - stop_loss)
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    risk_reward=risk_reward,
                    market_bias="bullish",
                    confidence=4,
                    indicators={
                        'rsi': rsi_current,
                        'rsi_prev': rsi_prev,
                        'rsi_prev2': rsi_prev2,
                        'adx': last['adx'],
                        'ema_50': last['ema_50'],
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Momentum Shift: RSI turning up ({rsi_prev2:.1f} -> {rsi_current:.1f}), ADX {last['adx']:.1f}, Volume {volume_ratio:.2f}x",
                    strategy="Momentum Shift (Bullish)"
                )
                
                return signal
            
            # Bearish Momentum Shift: RSI decreasing over 3 candles
            elif rsi_current < rsi_prev and rsi_prev < rsi_prev2 and abs(rsi_change) >= rsi_momentum_threshold:
                # CRITICAL: Check if we're actually in a downtrend
                if last['close'] > last['ema_50']:
                    logger.debug(f"[{timeframe}] Bearish RSI turn rejected - price above EMA(50): ${last['close']:.2f} > ${last['ema_50']:.2f} (uptrend)")
                    return None
                
                # Check recent price action (last 10 candles should show downward bias)
                recent_close = data['close'].iloc[-10]
                if last['close'] > recent_close:
                    logger.debug(f"[{timeframe}] Bearish RSI turn rejected - price rising over last 10 candles: ${recent_close:.2f} -> ${last['close']:.2f}")
                    return None
                
                logger.info(f"[{timeframe}] Bearish momentum shift detected - RSI: {rsi_prev2:.1f} -> {rsi_prev:.1f} -> {rsi_current:.1f} (change: {rsi_change:.1f})")
                logger.info(f"[{timeframe}] Trend confirmed: Price ${last['close']:.2f} < EMA(50) ${last['ema_50']:.2f}")
                logger.info(f"[{timeframe}] ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry + (last['atr'] * sl_multiplier)
                take_profit = entry - (last['atr'] * tp_multiplier)
                risk_reward = (entry - take_profit) / (stop_loss - entry)
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    risk_reward=risk_reward,
                    market_bias="bearish",
                    confidence=4,
                    indicators={
                        'rsi': rsi_current,
                        'rsi_prev': rsi_prev,
                        'rsi_prev2': rsi_prev2,
                        'adx': last['adx'],
                        'ema_50': last['ema_50'],
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Momentum Shift: RSI turning down ({rsi_prev2:.1f} -> {rsi_current:.1f}), ADX {last['adx']:.1f}, Volume {volume_ratio:.2f}x",
                    strategy="Momentum Shift (Bearish)"
                )
                
                return signal
            
            else:
                logger.debug(f"[{timeframe}] No momentum shift: RSI change {rsi_change:.1f} (need >= {rsi_momentum_threshold})")
            
            return None
            
        except KeyError as e:
            logger.error(f"Missing indicator in momentum shift detection: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in momentum shift detection: {e}", exc_info=True)
            return None

    

    def _is_signal_stale(self, signal: Signal, max_age_minutes: int = 30) -> bool:
        """
        Check if a signal is too old to be actionable.
        
        This prevents sending stale signals after scanner restarts.
        
        Args:
            signal: Signal to check
            max_age_minutes: Maximum age in minutes (default: 30)
            
        Returns:
            True if signal is stale, False if fresh
        """
        try:
            now = datetime.now()
            signal_age = now - signal.timestamp
            age_minutes = signal_age.total_seconds() / 60
            
            if age_minutes > max_age_minutes:
                logger.warning(
                    f"Signal is stale: {age_minutes:.1f} minutes old (max: {max_age_minutes}). "
                    f"Signal: {signal.signal_type} {signal.symbol} at ${signal.entry_price:.2f}. "
                    f"Skipping to prevent trading on old setups."
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking signal age: {e}")
            # If we can't determine age, assume it's fresh to be safe
            return False
    
    def detect_signals(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:

        """

        Detect trading signals from candlestick data with indicators.

        

        Args:

            data: DataFrame with OHLCV and calculated indicators

            timeframe: Timeframe string (e.g., '1m', '5m')

            symbol: Trading symbol (e.g., 'BTC/USD', 'XAU/USD', 'US30')

            

        Returns:

            Signal object if detected, None otherwise

        """

        if data.empty or len(data) < 3:

            return None

        

        # Clean expired signals from history

        self._clean_expired_signals()

        

        # Priority 1: Check for momentum shift signal (NEW)
        momentum_signal = self._detect_momentum_shift(data, timeframe, symbol)
        if momentum_signal and not self._is_duplicate_signal(momentum_signal) and not self._is_signal_stale(momentum_signal):
            self.signal_history.append(momentum_signal)
            logger.info(f"{momentum_signal.signal_type} signal detected on {timeframe}: {momentum_signal.strategy}")
            return momentum_signal
        
        # Priority 2: Check for trend alignment signal (NEW)
        trend_alignment_signal = self._detect_trend_alignment(data, timeframe, symbol)
        if trend_alignment_signal and not self._is_duplicate_signal(trend_alignment_signal) and not self._is_signal_stale(trend_alignment_signal):
            self.signal_history.append(trend_alignment_signal)
            logger.info(f"{trend_alignment_signal.signal_type} signal detected on {timeframe}: {trend_alignment_signal.strategy}")
            return trend_alignment_signal
        
        # Priority 3: Check for EMA cloud breakout signal (NEW)
        ema_cloud_signal = self._detect_ema_cloud_breakout(data, timeframe, symbol)
        if ema_cloud_signal and not self._is_duplicate_signal(ema_cloud_signal) and not self._is_signal_stale(ema_cloud_signal):
            self.signal_history.append(ema_cloud_signal)
            logger.info(f"{ema_cloud_signal.signal_type} signal detected on {timeframe}: {ema_cloud_signal.strategy}")
            return ema_cloud_signal
        
        # Priority 4: Check for mean reversion signal (NEW)
        mean_reversion_signal = self._detect_mean_reversion(data, timeframe, symbol)
        if mean_reversion_signal and not self._is_duplicate_signal(mean_reversion_signal) and not self._is_signal_stale(mean_reversion_signal):
            self.signal_history.append(mean_reversion_signal)
            logger.info(f"{mean_reversion_signal.signal_type} signal detected on {timeframe}: {mean_reversion_signal.strategy}")
            return mean_reversion_signal

        

        # Priority 5: Check for bullish confluence signal

        bullish_signal = self._check_bullish_confluence(data, timeframe, symbol)

        if bullish_signal and not self._is_duplicate_signal(bullish_signal) and not self._is_signal_stale(bullish_signal):

            self.signal_history.append(bullish_signal)

            logger.info(f"LONG signal detected on {timeframe}: {bullish_signal.entry_price}")

            return bullish_signal

        

        # Priority 6: Check for bearish confluence signal

        bearish_signal = self._check_bearish_confluence(data, timeframe, symbol)

        if bearish_signal and not self._is_duplicate_signal(bearish_signal) and not self._is_signal_stale(bearish_signal):

            self.signal_history.append(bearish_signal)

            logger.info(f"SHORT signal detected on {timeframe}: {bearish_signal.entry_price}")

            return bearish_signal

        

        # Priority 7: Check for trend-following signal

        trend_signal = self._detect_trend_following(data, timeframe, symbol)

        if trend_signal and not self._is_duplicate_signal(trend_signal) and not self._is_signal_stale(trend_signal):

            self.signal_history.append(trend_signal)

            logger.info(f"{trend_signal.signal_type} trend-following signal detected on {timeframe}: {trend_signal.entry_price}")

            return trend_signal

        

        # Check for extreme RSI reversal signals (like the BTC drop)
        if self.config.get('signal_rules', {}).get('enable_extreme_rsi_signals', False):
            extreme_rsi_signal = self._detect_extreme_rsi_reversal(data, timeframe, symbol)
            if extreme_rsi_signal and not self._is_duplicate_signal(extreme_rsi_signal) and not self._is_signal_stale(extreme_rsi_signal):
                self.signal_history.append(extreme_rsi_signal)
                logger.info(f"{extreme_rsi_signal.signal_type} extreme RSI signal detected on {timeframe}: {extreme_rsi_signal.entry_price}")
                return extreme_rsi_signal

        # Check for H4 HVG signal on 4-hour timeframe
        if timeframe == '4h':
            hvg_signal = self._detect_h4_hvg(data, timeframe, symbol)
            if hvg_signal and not self._is_duplicate_signal(hvg_signal) and not self._is_signal_stale(hvg_signal):
                self.signal_history.append(hvg_signal)
                logger.info(f"H4 HVG {hvg_signal.signal_type} signal detected on {timeframe}: {hvg_signal.entry_price}")
                return hvg_signal

        return None
    
    def _detect_h4_hvg(self, data: pd.DataFrame, timeframe: str, symbol: str) -> Optional[Signal]:
        """
        Detect H4 HVG signals using the H4HVGDetector.
        Works for all symbols (BTC, Gold, US30, etc.)
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Signal object if H4 HVG detected, None otherwise
        """
        try:
            # Get or create H4 HVG detector for this symbol
            if symbol not in self.h4_hvg_detectors:
                # Initialize detector for this symbol
                self.h4_hvg_detectors[symbol] = H4HVGDetector(symbol=symbol)
                logger.info(f"Initialized H4HVGDetector for {symbol}")
            
            detector = self.h4_hvg_detectors[symbol]
            
            # Generate H4 HVG signal
            signal = detector.generate_h4_hvg_signal(data, timeframe, symbol)
            
            if signal:
                # Check for duplicates using H4 HVG detector's own duplicate detection
                if not detector.is_duplicate_signal(signal):
                    # Add to H4 HVG detector's history
                    detector.add_signal_to_history(signal)
                    return signal
                else:
                    logger.debug(f"H4 HVG signal rejected as duplicate for {symbol}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting H4 HVG signal for {symbol}: {e}")
            return None

    

    def _check_bullish_confluence(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:

        """

        Check for bullish (LONG) signal with confluence validation.

        

        Confluence factors:

        1. Price > VWAP

        2. EMA(9) crosses above EMA(21) in last 2 candles

        3. Volume > 1.5x volume MA

        4. RSI between 30 and 70

        5. Price > EMA(50) for bullish bias

        

        Args:

            data: DataFrame with indicators

            timeframe: Timeframe string

            

        Returns:

            Signal object if all confluence met, None otherwise

        """

        try:

            # Get last few rows

            last = data.iloc[-1]

            prev = data.iloc[-2] if len(data) >= 2 else None

            

            if prev is None:

                return None

            

            confluence_count = 0

            

            # Factor 1: Price > VWAP

            if last['close'] > last['vwap']:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 2: EMA(9) crosses above EMA(21)

            ema_cross = (

                last['ema_9'] > last['ema_21'] and

                prev['ema_9'] <= prev['ema_21']

            )

            if ema_cross:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 3: Volume spike

            if last['volume'] > (last['volume_ma'] * self.volume_spike_threshold):

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 4: RSI in valid range

            if self.rsi_min <= last['rsi'] <= self.rsi_max:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 5: Bullish bias (price > EMA50)

            market_bias = "neutral"

            if last['close'] > last['ema_50']:

                confluence_count += 1

                market_bias = "bullish"

            

            # All critical factors met, create signal

            entry_price = last['close']

            atr = last['atr']

            
            # Use improved ATR-based SL/TP (1.0 SL, 2.5 TP for 2.5:1 R:R)

            stop_loss = entry_price - (atr * self.stop_loss_atr_multiplier)

            take_profit = entry_price + (atr * self.take_profit_atr_multiplier)

            risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)

            

            # Generate reasoning

            reasoning = self._generate_reasoning("LONG", last, prev, confluence_count, market_bias)

            

            signal = Signal(

                timestamp=last['timestamp'],

                signal_type="LONG",

                timeframe=timeframe,

                symbol=symbol,

                symbol_context=self._create_symbol_context(symbol),

                entry_price=entry_price,

                stop_loss=stop_loss,

                take_profit=take_profit,

                atr=atr,

                risk_reward=risk_reward,

                market_bias=market_bias,

                confidence=confluence_count,

                indicators={

                    'ema_9': last['ema_9'],

                    'ema_21': last['ema_21'],

                    'ema_50': last['ema_50'],

                    'vwap': last['vwap'],

                    'rsi': last['rsi'],

                    'volume': last['volume'],

                    'volume_ma': last['volume_ma']

                },

                reasoning=reasoning

            )

            

            return signal

            

        except Exception as e:

            logger.error(f"Error checking bullish confluence: {e}")

            return None

    

    def _check_bearish_confluence(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:

        """

        Check for bearish (SHORT) signal with confluence validation.

        

        Confluence factors:

        1. Price < VWAP

        2. EMA(9) crosses below EMA(21) in last 2 candles

        3. Volume > 1.5x volume MA

        4. RSI between 30 and 70

        5. Price < EMA(50) for bearish bias

        

        Args:

            data: DataFrame with indicators

            timeframe: Timeframe string

            

        Returns:

            Signal object if all confluence met, None otherwise

        """

        try:

            # Get last few rows

            last = data.iloc[-1]

            prev = data.iloc[-2] if len(data) >= 2 else None

            

            if prev is None:

                return None

            

            confluence_count = 0

            

            # Factor 1: Price < VWAP

            if last['close'] < last['vwap']:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 2: EMA(9) crosses below EMA(21)

            ema_cross = (

                last['ema_9'] < last['ema_21'] and

                prev['ema_9'] >= prev['ema_21']

            )

            if ema_cross:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 3: Volume spike

            if last['volume'] > (last['volume_ma'] * self.volume_spike_threshold):

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 4: RSI in valid range

            if self.rsi_min <= last['rsi'] <= self.rsi_max:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 5: Bearish bias (price < EMA50)

            market_bias = "neutral"

            if last['close'] < last['ema_50']:

                confluence_count += 1

                market_bias = "bearish"

            

            # All critical factors met, create signal

            entry_price = last['close']

            atr = last['atr']

            
            # Use improved ATR-based SL/TP (1.0 SL, 2.5 TP for 2.5:1 R:R)

            stop_loss = entry_price + (atr * self.stop_loss_atr_multiplier)

            take_profit = entry_price - (atr * self.take_profit_atr_multiplier)

            risk_reward = (entry_price - take_profit) / (stop_loss - entry_price)

            

            # Generate reasoning

            reasoning = self._generate_reasoning("SHORT", last, prev, confluence_count, market_bias)

            

            signal = Signal(

                timestamp=last['timestamp'],

                signal_type="SHORT",

                timeframe=timeframe,

                symbol=symbol,

                symbol_context=self._create_symbol_context(symbol),

                entry_price=entry_price,

                stop_loss=stop_loss,

                take_profit=take_profit,

                atr=atr,

                risk_reward=risk_reward,

                market_bias=market_bias,

                confidence=confluence_count,

                indicators={

                    'ema_9': last['ema_9'],

                    'ema_21': last['ema_21'],

                    'ema_50': last['ema_50'],

                    'vwap': last['vwap'],

                    'rsi': last['rsi'],

                    'volume': last['volume'],

                    'volume_ma': last['volume_ma']

                },

                reasoning=reasoning

            )

            

            return signal

            

        except Exception as e:

            logger.error(f"Error checking bearish confluence: {e}")

            return None

    

    def _is_duplicate_signal(self, signal: Signal) -> bool:

        """

        Check if signal is a duplicate of recent signal.

        

        Args:

            signal: Signal to check

            

        Returns:

            True if duplicate, False otherwise

        """

        time_threshold = timedelta(minutes=self.duplicate_time_window_minutes)

        

        logger.debug(f"Checking for duplicates: history has {len(self.signal_history)} signals, threshold={self.duplicate_time_window_minutes}min")

        

        for prev_signal in self.signal_history:

            # Check same signal type

            if prev_signal.signal_type != signal.signal_type:

                continue

            

            # Check time window

            time_diff = signal.timestamp - prev_signal.timestamp

            if time_diff < time_threshold:

                # Check price movement

                price_change_percent = abs(

                    signal.entry_price - prev_signal.entry_price

                ) / prev_signal.entry_price * 100

                

                logger.debug(f"Checking duplicate: time_diff={time_diff.total_seconds()}s, price_change={price_change_percent:.4f}%, threshold={self.duplicate_price_threshold_percent}%")

                

                if price_change_percent < self.duplicate_price_threshold_percent:

                    logger.debug(f"Duplicate signal blocked: {signal.signal_type} within {time_diff.total_seconds()}s, price change {price_change_percent:.4f}%")

                    return True

        

        return False

    

    def _clean_expired_signals(self) -> None:

        """Remove signals older than 30 minutes from the most recent signal."""

        if not self.signal_history:

            return

        

        # Use the most recent signal's timestamp as reference

        most_recent_time = max(s.timestamp for s in self.signal_history)

        cutoff_time = most_recent_time - timedelta(minutes=30)

        

        # Filter out expired signals

        self.signal_history = deque(

            [s for s in self.signal_history if s.timestamp > cutoff_time],

            maxlen=50

        )

    

    def _detect_trend_following(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:

        """

        Detect trend-following signals based on swing points and pullbacks.

        

        Strategy:

        1. Detect swing points to identify trend

        2. Verify EMA alignment with trend

        3. Wait for pullback to EMA(21)

        4. Confirm bounce with volume

        5. Validate RSI range

        

        Args:

            data: DataFrame with OHLCV and indicators

            timeframe: Timeframe string

            

        Returns:

            Signal with strategy="Trend Following" if detected, None otherwise

        """

        try:

            if len(data) < 50:

                return None

            

            # Detect swing points

            swing_data = TrendAnalyzer.detect_swing_points(data, lookback=5)

            

            # Check for uptrend

            is_uptrend = TrendAnalyzer.is_uptrend(swing_data, min_swings=3)

            is_downtrend = TrendAnalyzer.is_downtrend(swing_data, min_swings=3)

            

            if not (is_uptrend or is_downtrend):

                return None

            

            trend_direction = "uptrend" if is_uptrend else "downtrend"

            

            # Check if market is consolidating (skip if ATR declining)

            if TrendAnalyzer.is_consolidating(data, periods=3):

                logger.debug(f"Skipping trend signal: market consolidating on {timeframe}")

                return None

            

            # Verify EMA alignment

            if not TrendAnalyzer.is_ema_aligned(data, trend_direction):

                return None

            

            # Get last candles

            last = data.iloc[-1]

            prev = data.iloc[-2]

            

            # Calculate pullback depth

            pullback_depth = TrendAnalyzer.calculate_pullback_depth(data, trend_direction)

            

            # Reject if pullback too deep (> 61.8%)

            if pullback_depth > 61.8:

                logger.debug(f"Skipping trend signal: pullback too deep ({pullback_depth:.1f}%) on {timeframe}")

                return None

            

            # Check volume confirmation (at least 1.2x average)

            if last['volume'] < (last['volume_ma'] * 1.2):

                return None

            

            # Check if volume is declining (reduce confidence)

            volume_declining = (

                last['volume'] < prev['volume'] and

                prev['volume'] < data.iloc[-3]['volume']

            )

            

            if volume_declining:

                logger.debug(f"Skipping trend signal: volume declining on {timeframe}")

                return None

            

            # Detect pullback entry for uptrend

            if is_uptrend:

                # Check RSI range (40-80 for uptrends)

                if not (40 <= last['rsi'] <= 80):

                    return None

                

                # Check if price pulled back to EMA(21) and bounced

                ema_21 = last.get('ema_21', last.get('ema_20'))

                if pd.isna(ema_21):

                    return None

                

                # Price should be near EMA(21) (within 1 ATR)

                distance_from_ema = abs(last['close'] - ema_21)

                if distance_from_ema > last['atr']:

                    return None

                

                # Price should be bouncing up (close > open)

                if last['close'] <= last['open']:

                    return None

                

                # Generate LONG signal

                entry_price = last['close']

                atr = last['atr']

                stop_loss = entry_price - (atr * 1.5)

                

                # Stronger trend gets larger target

                if last['rsi'] > 60:

                    take_profit = entry_price + (atr * 3.0)

                else:

                    take_profit = entry_price + (atr * 2.5)

                

                risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)

                

                # Count swing points for confidence

                total_swings = swing_data['higher_highs'] + swing_data['higher_lows']

                

                # Generate reasoning

                reasoning = self._generate_trend_reasoning(

                    "LONG", last, swing_data, pullback_depth, total_swings

                )

                

                signal = Signal(

                    timestamp=last['timestamp'],

                    signal_type="LONG",

                    timeframe=timeframe,

                    symbol=symbol,

                    symbol_context=self._create_symbol_context(symbol),

                    entry_price=entry_price,

                    stop_loss=stop_loss,

                    take_profit=take_profit,

                    atr=atr,

                    risk_reward=risk_reward,

                    market_bias="bullish",

                    confidence=4,  # Trend signals are high confidence

                    indicators={

                        'ema_9': last.get('ema_9'),

                        'ema_21': ema_21,

                        'ema_50': last['ema_50'],

                        'vwap': last.get('vwap'),

                        'rsi': last['rsi'],

                        'volume': last['volume'],

                        'volume_ma': last['volume_ma']

                    },

                    reasoning=reasoning,

                    strategy="Trend Following",

                    trend_direction=trend_direction,

                    swing_points=total_swings,

                    pullback_depth=pullback_depth

                )

                

                return signal

            

            # Detect pullback entry for downtrend

            elif is_downtrend:

                # Check RSI range (20-60 for downtrends)

                if not (20 <= last['rsi'] <= 60):

                    return None

                

                # Check if price rallied to EMA(21) and rejected

                ema_21 = last.get('ema_21', last.get('ema_20'))

                if pd.isna(ema_21):

                    return None

                

                # Price should be near EMA(21) (within 1 ATR)

                distance_from_ema = abs(last['close'] - ema_21)

                if distance_from_ema > last['atr']:

                    return None

                

                # Price should be rejecting down (close < open)

                if last['close'] >= last['open']:

                    return None

                

                # Generate SHORT signal

                entry_price = last['close']

                atr = last['atr']

                stop_loss = entry_price + (atr * 1.5)

                

                # Stronger trend gets larger target

                if last['rsi'] < 40:

                    take_profit = entry_price - (atr * 3.0)

                else:

                    take_profit = entry_price - (atr * 2.5)

                

                risk_reward = (entry_price - take_profit) / (stop_loss - entry_price)

                

                # Count swing points for confidence

                total_swings = swing_data['lower_highs'] + swing_data['lower_lows']

                

                # Generate reasoning

                reasoning = self._generate_trend_reasoning(

                    "SHORT", last, swing_data, pullback_depth, total_swings

                )

                

                signal = Signal(

                    timestamp=last['timestamp'],

                    signal_type="SHORT",

                    timeframe=timeframe,

                    symbol=symbol,

                    symbol_context=self._create_symbol_context(symbol),

                    entry_price=entry_price,

                    stop_loss=stop_loss,

                    take_profit=take_profit,

                    atr=atr,

                    risk_reward=risk_reward,

                    market_bias="bearish",

                    confidence=4,  # Trend signals are high confidence

                    indicators={

                        'ema_9': last.get('ema_9'),

                        'ema_21': ema_21,

                        'ema_50': last['ema_50'],

                        'vwap': last.get('vwap'),

                        'rsi': last['rsi'],

                        'volume': last['volume'],

                        'volume_ma': last['volume_ma']

                    },

                    reasoning=reasoning,

                    strategy="Trend Following",

                    trend_direction=trend_direction,

                    swing_points=total_swings,

                    pullback_depth=pullback_depth

                )

                

                return signal

            

            return None

            

        except Exception as e:

            logger.error(f"Error in trend-following detection: {e}")

            return None

    

    def _generate_trend_reasoning(self, signal_type: str, last: pd.Series,

                                  swing_data: Dict, pullback_depth: float,

                                  swing_points: int) -> str:

        """

        Generate reasoning for trend-following signals.

        

        Args:

            signal_type: "LONG" or "SHORT"

            last: Last candle data

            swing_data: Swing point data from TrendAnalyzer

            pullback_depth: Pullback percentage

            swing_points: Total number of swing points

            

        Returns:

            Formatted reasoning string

        """

        reasons = []

        

        # Strategy intro

        reasons.append("STRATEGY: Trend Following")

        

        # Trend identification

        if signal_type == "LONG":

            reasons.append(f"UPTREND IDENTIFIED: {swing_points} swing points detected")

            reasons.append(f"    Higher Highs: {swing_data['higher_highs']}")

            reasons.append(f"    Higher Lows: {swing_data['higher_lows']}")

            reasons.append(f"    Trend strength: Strong and established")

        else:

            reasons.append(f"DOWNTREND IDENTIFIED: {swing_points} swing points detected")

            reasons.append(f"    Lower Highs: {swing_data['lower_highs']}")

            reasons.append(f"    Lower Lows: {swing_data['lower_lows']}")

            reasons.append(f"    Trend strength: Strong and established")

        

        # Pullback entry

        ema_21 = last.get('ema_21', last.get('ema_20'))

        if signal_type == "LONG":

            reasons.append(f"\nPULLBACK ENTRY: Price pulled back {pullback_depth:.1f}% and bounced at EMA(21)")

            reasons.append(f"    EMA(21): ${ema_21:.2f} acting as dynamic support")

            reasons.append(f"    Pullback healthy (< 61.8%), trend intact")

        else:

            reasons.append(f"\nRALLY REJECTION: Price rallied {pullback_depth:.1f}% and rejected at EMA(21)")

            reasons.append(f"    EMA(21): ${ema_21:.2f} acting as dynamic resistance")

            reasons.append(f"    Rally contained (< 61.8%), trend intact")

        

        # Volume confirmation

        volume_ratio = last['volume'] / last['volume_ma']

        reasons.append(f"\nVOLUME CONFIRMATION: {volume_ratio:.2f}x average volume")

        reasons.append(f"    Confirms genuine interest at this level")

        

        # RSI momentum

        reasons.append(f"\n MOMENTUM: RSI at {last['rsi']:.1f}")

        if signal_type == "LONG":

            if last['rsi'] > 60:

                reasons.append(f"    Strong bullish momentum, extended target justified")

            else:

                reasons.append(f"    Healthy momentum, room to run higher")

        else:

            if last['rsi'] < 40:

                reasons.append(f"    Strong bearish momentum, extended target justified")

            else:

                reasons.append(f"    Healthy momentum, room to fall further")

        

        # Why enter NOW

        reasons.append(f"\nWHY ENTER NOW:")

        reasons.append(f"    Established trend with {swing_points} confirmed swing points")

        reasons.append(f"    Optimal pullback entry at key moving average")

        reasons.append(f"    Volume confirms buyers/sellers stepping in")

        reasons.append(f"    Risk-reward favorable with trend on our side")

        

        return "\n".join(reasons)

    

    def _generate_reasoning(self, signal_type: str, last: pd.Series, prev: pd.Series, 

                           confluence_count: int, market_bias: str) -> str:

        """

        Generate detailed reasoning for why this signal was generated.

        

        Args:

            signal_type: "LONG" or "SHORT"

            last: Last candle data

            prev: Previous candle data

            confluence_count: Number of confluence factors met

            market_bias: Market bias string

            

        Returns:

            Formatted reasoning string

        """

        reasons = []

        

        # 1. Market Bias

        if signal_type == "LONG":

            reasons.append(f"BULLISH BIAS: Price trading above VWAP (${last['vwap']:.2f}), indicating institutional buying pressure")

            if market_bias == "bullish":

                reasons.append(f" Trend Confirmation: Price above EMA(50) at ${last['ema_50']:.2f}, confirming uptrend")

        else:

            reasons.append(f"BEARISH BIAS: Price trading below VWAP (${last['vwap']:.2f}), indicating institutional selling pressure")

            if market_bias == "bearish":

                reasons.append(f" Trend Confirmation: Price below EMA(50) at ${last['ema_50']:.2f}, confirming downtrend")

        

        # 2. EMA Crossover

        if signal_type == "LONG":

            reasons.append(f"MOMENTUM SHIFT: EMA(9) crossed above EMA(21), signaling short-term bullish momentum")

            reasons.append(f"    EMA(9): ${last['ema_9']:.2f} > EMA(21): ${last['ema_21']:.2f}")

        else:

            reasons.append(f"MOMENTUM SHIFT: EMA(9) crossed below EMA(21), signaling short-term bearish momentum")

            reasons.append(f"    EMA(9): ${last['ema_9']:.2f} < EMA(21): ${last['ema_21']:.2f}")

        

        # 3. Volume Confirmation

        volume_ratio = last['volume'] / last['volume_ma']

        reasons.append(f"VOLUME SPIKE: {volume_ratio:.2f}x average volume confirms genuine breakout")

        reasons.append(f"    Current: {last['volume']:,.0f} vs Avg: {last['volume_ma']:,.0f}")

        

        # 4. RSI Validation

        reasons.append(f" MOMENTUM HEALTHY: RSI at {last['rsi']:.1f} - not overextended, room to run")

        if 40 <= last['rsi'] <= 60:

            reasons.append(f"    RSI in neutral zone, ideal for new trend development")

        

        # 5. Why to Enter NOW

        if signal_type == "LONG":

            reasons.append(f"\nWHY BUY NOW:")

            reasons.append(f"    All {confluence_count} confluence factors aligned simultaneously")

            reasons.append(f"    Momentum turning bullish after pullback")

            reasons.append(f"    Institutional buyers (VWAP) supporting price")

            reasons.append(f"    Volume confirms real buying interest, not a fake move")

        else:

            reasons.append(f"\nWHY SELL NOW:")

            reasons.append(f"    All {confluence_count} confluence factors aligned simultaneously")

            reasons.append(f"    Momentum turning bearish after rally")

            reasons.append(f"    Institutional sellers (VWAP) pressuring price")

            reasons.append(f"    Volume confirms real selling interest, not a fake move")

        

        return "\n".join(reasons)

    def _detect_extreme_rsi_reversal(self, data: pd.DataFrame, timeframe: str, symbol: str) -> Optional[Signal]:
        """
        Detect extreme RSI reversal signals for strong momentum moves.
        
        This catches signals like the BTC drop where RSI goes to extreme levels
        with strong ADX indicating a powerful trend that may continue.
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if len(data) < 3:
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['rsi', 'adx', 'atr', 'volume', 'volume_ma']
            if not all(ind in last.index for ind in required_indicators):
                return None
            
            # Get configuration
            adx_min = self.config.get('signal_rules', {}).get('adx_min_trend', 20)
            volume_threshold = self.config.get('signal_rules', {}).get('volume_spike_threshold', 0.8)
            
            # Check for strong trend (high ADX)
            if last['adx'] < adx_min:
                return None
            
            # Check volume
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < volume_threshold:
                return None
            
            # Extreme oversold with strong bearish momentum (like BTC drop)
            if (last['rsi'] <= 15 and  # Extremely oversold
                last['rsi'] < prev['rsi'] and  # Still declining
                last['adx'] > 30):  # Strong trend
                
                logger.info(f"[{timeframe}] Extreme RSI bearish continuation detected - RSI: {last['rsi']:.1f}, ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry + (last['atr'] * self.config['signal_rules']['stop_loss_atr_multiplier'])
                take_profit = entry - (last['atr'] * self.config['signal_rules']['take_profit_atr_multiplier'])
                
                # Calculate risk/reward
                risk = abs(stop_loss - entry)
                reward = abs(entry - take_profit)
                risk_reward = reward / risk if risk > 0 else 0
                
                # Generate reasoning
                reasoning = f"""🔥 EXTREME RSI BEARISH MOMENTUM 🔥
                
📉 OVERSOLD CONTINUATION SIGNAL:
• RSI at extreme level: {last['rsi']:.1f} (< 15)
• Strong bearish trend: ADX {last['adx']:.1f} (> 30)
• Volume confirmation: {volume_ratio:.2f}x average
• Price momentum: Still declining

⚡ MOMENTUM ANALYSIS:
• This is NOT a reversal signal - it's a continuation
• Extreme RSI with high ADX = powerful trend in motion
• Volume confirms institutional participation
• Similar to major market crashes/breakdowns

🎯 TRADE RATIONALE:
• Ride the momentum while it's strong
• Exit when RSI starts to recover or ADX weakens
• High probability continuation pattern
• Risk/Reward: {risk_reward:.2f}:1"""

                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    risk_reward=risk_reward,
                    market_bias="bearish",
                    confidence=4,  # High confidence for extreme moves
                    indicators=last.to_dict(),
                    reasoning=reasoning,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    strategy="Extreme RSI Continuation"
                )
                
                return signal
            
            # Extreme overbought with strong bullish momentum
            elif (last['rsi'] >= 85 and  # Extremely overbought
                  last['rsi'] > prev['rsi'] and  # Still rising
                  last['adx'] > 30):  # Strong trend
                
                logger.info(f"[{timeframe}] Extreme RSI bullish continuation detected - RSI: {last['rsi']:.1f}, ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry - (last['atr'] * self.config['signal_rules']['stop_loss_atr_multiplier'])
                take_profit = entry + (last['atr'] * self.config['signal_rules']['take_profit_atr_multiplier'])
                
                # Calculate risk/reward
                risk = abs(stop_loss - entry)
                reward = abs(take_profit - entry)
                risk_reward = reward / risk if risk > 0 else 0
                
                # Generate reasoning
                reasoning = f"""🚀 EXTREME RSI BULLISH MOMENTUM 🚀
                
📈 OVERBOUGHT CONTINUATION SIGNAL:
• RSI at extreme level: {last['rsi']:.1f} (> 85)
• Strong bullish trend: ADX {last['adx']:.1f} (> 30)
• Volume confirmation: {volume_ratio:.2f}x average
• Price momentum: Still rising

⚡ MOMENTUM ANALYSIS:
• This is NOT a reversal signal - it's a continuation
• Extreme RSI with high ADX = powerful trend in motion
• Volume confirms institutional participation
• Similar to major market rallies/breakouts

🎯 TRADE RATIONALE:
• Ride the momentum while it's strong
• Exit when RSI starts to cool or ADX weakens
• High probability continuation pattern
• Risk/Reward: {risk_reward:.2f}:1"""

                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    risk_reward=risk_reward,
                    market_bias="bullish",
                    confidence=4,  # High confidence for extreme moves
                    indicators=last.to_dict(),
                    reasoning=reasoning,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    strategy="Extreme RSI Continuation"
                )
                
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in extreme RSI detection: {e}", exc_info=True)
            return None
    
    def _is_pin_bar(self, candle: pd.Series) -> bool:
        """
        Detect pin bar pattern (long wick, small body).
        
        A pin bar has a long wick (at least 2x the body size) with the body
        in the upper or lower third of the candle range.
        
        Args:
            candle: Candle data (open, high, low, close)
            
        Returns:
            True if pin bar detected, False otherwise
        """
        try:
            body_size = abs(candle['close'] - candle['open'])
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                return False
            
            # Calculate wick sizes
            if candle['close'] > candle['open']:  # Bullish candle
                upper_wick = candle['high'] - candle['close']
                lower_wick = candle['open'] - candle['low']
            else:  # Bearish candle
                upper_wick = candle['high'] - candle['open']
                lower_wick = candle['close'] - candle['low']
            
            # Pin bar has one wick at least 2x body size
            has_long_wick = (upper_wick >= body_size * 2) or (lower_wick >= body_size * 2)
            
            # Body should be in upper/lower 1/3 of candle
            body_position = (min(candle['close'], candle['open']) - candle['low']) / total_range
            in_lower_third = body_position < 0.33
            in_upper_third = body_position > 0.67
            
            return has_long_wick and (in_lower_third or in_upper_third)
            
        except Exception as e:
            logger.error(f"Error detecting pin bar: {e}")
            return False
    
    def _is_doji(self, candle: pd.Series) -> bool:
        """
        Detect doji pattern (very small body).
        
        A doji has a body size less than 10% of the total candle range,
        indicating indecision in the market.
        
        Args:
            candle: Candle data (open, high, low, close)
            
        Returns:
            True if doji detected, False otherwise
        """
        try:
            body_size = abs(candle['close'] - candle['open'])
            total_range = candle['high'] - candle['low']
            
            if total_range == 0:
                return False
            
            # Doji has body < 10% of total range
            body_ratio = body_size / total_range
            return body_ratio < 0.10
            
        except Exception as e:
            logger.error(f"Error detecting doji: {e}")
            return False
    
    def _is_engulfing(self, current: pd.Series, previous: pd.Series) -> bool:
        """
        Detect engulfing candle pattern.
        
        Bullish engulfing: Current green candle body completely engulfs previous red candle body
        Bearish engulfing: Current red candle body completely engulfs previous green candle body
        
        Args:
            current: Current candle data
            previous: Previous candle data
            
        Returns:
            True if engulfing pattern detected, False otherwise
        """
        try:
            # Current candle body
            current_body_top = max(current['close'], current['open'])
            current_body_bottom = min(current['close'], current['open'])
            current_is_bullish = current['close'] > current['open']
            
            # Previous candle body
            prev_body_top = max(previous['close'], previous['open'])
            prev_body_bottom = min(previous['close'], previous['open'])
            prev_is_bullish = previous['close'] > previous['open']
            
            # Bullish engulfing: current bullish candle engulfs previous bearish candle
            if current_is_bullish and not prev_is_bullish:
                return (current_body_bottom < prev_body_bottom and 
                       current_body_top > prev_body_top)
            
            # Bearish engulfing: current bearish candle engulfs previous bullish candle
            elif not current_is_bullish and prev_is_bullish:
                return (current_body_bottom < prev_body_bottom and 
                       current_body_top > prev_body_top)
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting engulfing pattern: {e}")
            return False

    def _detect_fibonacci_retracement(
        self, 
        data: pd.DataFrame, 
        timeframe: str, 
        symbol: str = "BTC/USD",
        swing_lookback: int = 50,
        level_tolerance_percent: float = 0.5,
        volume_threshold: float = 1.3,
        require_reversal_candle: bool = True
    ) -> Optional[Signal]:
        """
        Detect Fibonacci retracement signals.
        
        Strategy:
        1. Identify significant swing (high to low or low to high)
        2. Calculate Fib levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
        3. Check if price is near a Fib level (within tolerance)
        4. Look for reversal candle pattern
        5. Validate with volume and RSI
        6. Set SL beyond next Fib level
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            swing_lookback: Candles to look back for swing
            level_tolerance_percent: Tolerance for level proximity
            volume_threshold: Minimum volume ratio
            require_reversal_candle: Whether to require reversal pattern
            
        Returns:
            Signal if detected, None otherwise
        """
        from src.strategy_helpers import FibonacciCalculator
        
        try:
            if len(data) < swing_lookback:
                logger.debug(f"[{timeframe}] Insufficient data for Fibonacci detection")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['rsi', 'atr', 'volume', 'volume_ma']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for Fibonacci detection")
                return None
            
            # Find significant swing
            swing_result = FibonacciCalculator.find_swing(data, lookback=swing_lookback)
            if not swing_result:
                logger.debug(f"[{timeframe}] No significant swing found for Fibonacci")
                return None
            
            swing_high, swing_low, direction = swing_result
            
            # Calculate Fibonacci levels
            fib_levels = FibonacciCalculator.calculate_levels(swing_high, swing_low, direction)
            
            # Check if current price is near any Fibonacci level
            current_price = last['close']
            nearest = FibonacciCalculator.get_nearest_level(current_price, fib_levels)
            
            if not nearest:
                logger.debug(f"[{timeframe}] Price not near any Fibonacci level")
                return None
            
            level_price, level_name = nearest
            
            # Check if price is within tolerance
            if not FibonacciCalculator.is_near_level(current_price, level_price, level_tolerance_percent):
                logger.debug(f"[{timeframe}] Price not within tolerance of Fibonacci level")
                return None
            
            logger.info(f"[{timeframe}] Price ${current_price:.2f} near Fibonacci {level_name} level ${level_price:.2f}")
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma'] if last['volume_ma'] > 0 else 0
            if volume_ratio < volume_threshold:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= {volume_threshold}x)")
                return None
            
            # Check for reversal candle pattern if required
            if require_reversal_candle:
                is_pin_bar = self._is_pin_bar(last)
                is_engulfing = self._is_engulfing(last, prev)
                is_doji = self._is_doji(last)
                
                if not (is_pin_bar or is_engulfing or is_doji):
                    logger.debug(f"[{timeframe}] No reversal candle pattern at Fibonacci level")
                    return None
                
                pattern_name = "pin bar" if is_pin_bar else ("engulfing" if is_engulfing else "doji")
                logger.info(f"[{timeframe}] Reversal pattern detected: {pattern_name}")
            
            # Check RSI for divergence or confirmation
            rsi = last['rsi']
            rsi_prev = prev['rsi']
            
            # Determine signal direction based on Fibonacci retracement direction
            if direction == "retracement_up":
                # Price retraced down from high, looking for bounce up
                # Bullish setup: RSI should be recovering (turning up)
                if rsi <= rsi_prev:
                    logger.debug(f"[{timeframe}] RSI not recovering for bullish Fib setup")
                    return None
                
                # Priority levels (golden ratios) get higher confidence
                is_golden_ratio = level_name in ["38.2%", "61.8%"]
                confidence = 5 if is_golden_ratio else 4
                
                # Calculate entry, SL, TP
                entry = last['close']
                atr = last['atr']
                
                # Stop loss beyond next Fibonacci level down
                if level_name == "23.6%":
                    stop_loss = fib_levels.swing_low - (atr * 0.5)
                elif level_name == "38.2%":
                    stop_loss = fib_levels.level_236 - (atr * 0.5)
                elif level_name == "50%":
                    stop_loss = fib_levels.level_382 - (atr * 0.5)
                elif level_name == "61.8%":
                    stop_loss = fib_levels.level_500 - (atr * 0.5)
                else:  # 78.6%
                    stop_loss = fib_levels.level_618 - (atr * 0.5)
                
                # Take profit at swing high
                take_profit = fib_levels.swing_high
                
                # Calculate risk/reward
                risk = abs(entry - stop_loss)
                reward = abs(take_profit - entry)
                risk_reward = reward / risk if risk > 0 else 0
                
                # Require minimum risk/reward
                if risk_reward < 1.5:
                    logger.debug(f"[{timeframe}] Risk/reward too low: {risk_reward:.2f}")
                    return None
                
                logger.info(f"[{timeframe}] Bullish Fibonacci retracement signal at {level_name} level")
                logger.info(f"[{timeframe}] Entry: ${entry:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}, R:R={risk_reward:.2f}")
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="bullish",
                    confidence=confidence,
                    indicators={
                        'rsi': rsi,
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Fibonacci Retracement: Price bouncing at {level_name} level (${level_price:.2f}), "
                             f"RSI recovering ({rsi:.1f}), Volume {volume_ratio:.2f}x, "
                             f"Target swing high ${fib_levels.swing_high:.2f}",
                    strategy="Fibonacci Retracement",
                    strategy_metadata={
                        'fib_level': level_name,
                        'fib_level_price': level_price,
                        'swing_high': fib_levels.swing_high,
                        'swing_low': fib_levels.swing_low,
                        'swing_direction': direction,
                        'is_golden_ratio': is_golden_ratio
                    }
                )
                
                return signal
            
            else:  # retracement_down
                # Price retraced up from low, looking for rejection down
                # Bearish setup: RSI should be declining (turning down)
                if rsi >= rsi_prev:
                    logger.debug(f"[{timeframe}] RSI not declining for bearish Fib setup")
                    return None
                
                # Priority levels (golden ratios) get higher confidence
                is_golden_ratio = level_name in ["38.2%", "61.8%"]
                confidence = 5 if is_golden_ratio else 4
                
                # Calculate entry, SL, TP
                entry = last['close']
                atr = last['atr']
                
                # Stop loss beyond next Fibonacci level up
                if level_name == "23.6%":
                    stop_loss = fib_levels.level_382 + (atr * 0.5)
                elif level_name == "38.2%":
                    stop_loss = fib_levels.level_500 + (atr * 0.5)
                elif level_name == "50%":
                    stop_loss = fib_levels.level_618 + (atr * 0.5)
                elif level_name == "61.8%":
                    stop_loss = fib_levels.level_786 + (atr * 0.5)
                else:  # 78.6%
                    stop_loss = fib_levels.swing_high + (atr * 0.5)
                
                # Take profit at swing low
                take_profit = fib_levels.swing_low
                
                # Calculate risk/reward
                risk = abs(stop_loss - entry)
                reward = abs(entry - take_profit)
                risk_reward = reward / risk if risk > 0 else 0
                
                # Require minimum risk/reward
                if risk_reward < 1.5:
                    logger.debug(f"[{timeframe}] Risk/reward too low: {risk_reward:.2f}")
                    return None
                
                logger.info(f"[{timeframe}] Bearish Fibonacci retracement signal at {level_name} level")
                logger.info(f"[{timeframe}] Entry: ${entry:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}, R:R={risk_reward:.2f}")
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="bearish",
                    confidence=confidence,
                    indicators={
                        'rsi': rsi,
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Fibonacci Retracement: Price rejecting at {level_name} level (${level_price:.2f}), "
                             f"RSI declining ({rsi:.1f}), Volume {volume_ratio:.2f}x, "
                             f"Target swing low ${fib_levels.swing_low:.2f}",
                    strategy="Fibonacci Retracement",
                    strategy_metadata={
                        'fib_level': level_name,
                        'fib_level_price': level_price,
                        'swing_high': fib_levels.swing_high,
                        'swing_low': fib_levels.swing_low,
                        'swing_direction': direction,
                        'is_golden_ratio': is_golden_ratio
                    }
                )
                
                return signal
            
        except Exception as e:
            logger.error(f"Error in Fibonacci retracement detection: {e}", exc_info=True)
            return None

    def _detect_support_resistance_bounce(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str = "BTC/USD",
        lookback_candles: int = 100,
        min_touches: int = 2,
        level_tolerance_percent: float = 0.3,
        volume_threshold: float = 1.4,
        require_reversal_candle: bool = True
    ) -> Optional[Signal]:
        """
        Detect support/resistance bounce signals.
        
        Strategy:
        1. Identify support levels where price has bounced at least 2 times
        2. Identify resistance levels where price has reversed at least 2 times
        3. Detect price proximity to support/resistance (within 0.3%)
        4. Validate reversal candle patterns (pin bar, engulfing, doji)
        5. Check volume confirmation (1.4x average minimum)
        6. Increase confidence for multiple touches (3+ touches)
        7. Increase priority for round number alignment
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            lookback_candles: Number of candles to analyze for levels
            min_touches: Minimum touches required for valid level
            level_tolerance_percent: Price tolerance for level clustering
            volume_threshold: Minimum volume ratio
            require_reversal_candle: Whether to require reversal pattern
            
        Returns:
            Signal if detected, None otherwise
        """
        from src.strategy_helpers import SupportResistanceFinder
        
        try:
            if len(data) < lookback_candles:
                logger.debug(f"[{timeframe}] Insufficient data for S/R detection")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['rsi', 'atr', 'volume', 'volume_ma']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for S/R detection")
                return None
            
            # Find support/resistance levels
            levels = SupportResistanceFinder.find_levels(
                data,
                lookback=lookback_candles,
                min_touches=min_touches,
                tolerance_percent=level_tolerance_percent
            )
            
            if not levels:
                logger.debug(f"[{timeframe}] No support/resistance levels found")
                return None
            
            logger.debug(f"[{timeframe}] Found {len(levels)} S/R levels")
            
            # Get nearest level to current price
            current_price = last['close']
            nearest_level = SupportResistanceFinder.get_nearest_level(
                current_price,
                levels,
                max_distance_percent=level_tolerance_percent
            )
            
            if not nearest_level:
                logger.debug(f"[{timeframe}] Price not near any S/R level")
                return None
            
            logger.info(f"[{timeframe}] Price ${current_price:.2f} near {nearest_level.level_type} level ${nearest_level.price:.2f} ({nearest_level.touches} touches)")
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma'] if last['volume_ma'] > 0 else 0
            if volume_ratio < volume_threshold:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= {volume_threshold}x)")
                return None
            
            # Check for reversal candle pattern if required
            if require_reversal_candle:
                is_pin_bar = self._is_pin_bar(last)
                is_engulfing = self._is_engulfing(last, prev)
                is_doji = self._is_doji(last)
                
                if not (is_pin_bar or is_engulfing or is_doji):
                    logger.debug(f"[{timeframe}] No reversal candle pattern at S/R level")
                    return None
                
                pattern_name = "pin bar" if is_pin_bar else ("engulfing" if is_engulfing else "doji")
                logger.info(f"[{timeframe}] Reversal pattern detected: {pattern_name}")
            
            # Determine signal direction based on level type
            if nearest_level.level_type == "support":
                # Bullish bounce from support
                # Check RSI not oversold (avoid catching falling knife)
                if last['rsi'] < 25:
                    logger.debug(f"[{timeframe}] RSI too low for support bounce: {last['rsi']:.1f}")
                    return None
                
                # Calculate confidence based on touches and round number
                confidence = 4
                if nearest_level.touches >= 3:
                    confidence = 5
                if nearest_level.is_round_number:
                    confidence = min(5, confidence + 1)
                
                # Calculate entry, SL, TP
                entry = last['close']
                atr = last['atr']
                
                # Stop loss below support level
                stop_loss = nearest_level.price - (atr * 0.8)
                
                # Take profit based on risk (2:1 R:R minimum)
                risk = abs(entry - stop_loss)
                take_profit = entry + (risk * 2.0)
                
                risk_reward = 2.0
                
                logger.info(f"[{timeframe}] Bullish support bounce signal")
                logger.info(f"[{timeframe}] Entry: ${entry:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}")
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="bullish",
                    confidence=confidence,
                    indicators={
                        'rsi': last['rsi'],
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Support Bounce: Price bouncing at support ${nearest_level.price:.2f} "
                             f"({nearest_level.touches} touches{', round number' if nearest_level.is_round_number else ''}), "
                             f"RSI {last['rsi']:.1f}, Volume {volume_ratio:.2f}x",
                    strategy="Support/Resistance Bounce",
                    strategy_metadata={
                        'level_type': 'support',
                        'level_price': nearest_level.price,
                        'touches': nearest_level.touches,
                        'strength': nearest_level.strength,
                        'is_round_number': nearest_level.is_round_number,
                        'last_touch_candles_ago': nearest_level.last_touch_candles_ago
                    }
                )
                
                return signal
            
            else:  # resistance
                # Bearish rejection from resistance
                # Check RSI not overbought (avoid shorting strong uptrend)
                if last['rsi'] > 75:
                    logger.debug(f"[{timeframe}] RSI too high for resistance rejection: {last['rsi']:.1f}")
                    return None
                
                # Calculate confidence based on touches and round number
                confidence = 4
                if nearest_level.touches >= 3:
                    confidence = 5
                if nearest_level.is_round_number:
                    confidence = min(5, confidence + 1)
                
                # Calculate entry, SL, TP
                entry = last['close']
                atr = last['atr']
                
                # Stop loss above resistance level
                stop_loss = nearest_level.price + (atr * 0.8)
                
                # Take profit based on risk (2:1 R:R minimum)
                risk = abs(stop_loss - entry)
                take_profit = entry - (risk * 2.0)
                
                risk_reward = 2.0
                
                logger.info(f"[{timeframe}] Bearish resistance rejection signal")
                logger.info(f"[{timeframe}] Entry: ${entry:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}")
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="bearish",
                    confidence=confidence,
                    indicators={
                        'rsi': last['rsi'],
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Resistance Rejection: Price rejecting at resistance ${nearest_level.price:.2f} "
                             f"({nearest_level.touches} touches{', round number' if nearest_level.is_round_number else ''}), "
                             f"RSI {last['rsi']:.1f}, Volume {volume_ratio:.2f}x",
                    strategy="Support/Resistance Bounce",
                    strategy_metadata={
                        'level_type': 'resistance',
                        'level_price': nearest_level.price,
                        'touches': nearest_level.touches,
                        'strength': nearest_level.strength,
                        'is_round_number': nearest_level.is_round_number,
                        'last_touch_candles_ago': nearest_level.last_touch_candles_ago
                    }
                )
                
                return signal
            
        except Exception as e:
            logger.error(f"Error in support/resistance bounce detection: {e}", exc_info=True)
            return None

    def _detect_key_level_break_retest(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str = "BTC/USD",
        retest_window_candles: tuple = (5, 10),
        volume_threshold_break: float = 1.5,
        volume_threshold_retest: float = 0.8,
        major_level_volume_multiplier: float = 1.5
    ) -> Optional[Signal]:
        """
        Detect key level break and retest signals.
        
        Strategy:
        1. Identify key levels (round numbers, previous highs/lows, psychological levels)
        2. Detect key level breaks with volume confirmation
        3. Monitor for retest within 5-10 candles
        4. Validate retest holds with volume (0.8x breakout volume minimum)
        5. Generate continuation signal on successful retest
        6. Require stronger confirmation for major round numbers (1.5x volume)
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            retest_window_candles: Tuple of (min, max) candles for retest
            volume_threshold_break: Minimum volume ratio for break
            volume_threshold_retest: Minimum volume ratio for retest
            major_level_volume_multiplier: Extra volume multiplier for major levels
            
        Returns:
            Signal if detected, None otherwise
        """
        from src.strategy_helpers import KeyLevelTracker
        
        try:
            if len(data) < 50:
                logger.debug(f"[{timeframe}] Insufficient data for key level detection")
                return None
            
            last = data.iloc[-1]
            
            # Check for required indicators
            required_indicators = ['rsi', 'atr', 'volume', 'volume_ma']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for key level detection")
                return None
            
            # Initialize key level tracker
            asset = symbol.split('/')[0] if '/' in symbol else symbol
            tracker = KeyLevelTracker(asset)
            tracker.update_levels(data)
            
            if not tracker.key_levels:
                logger.debug(f"[{timeframe}] No key levels identified")
                return None
            
            logger.debug(f"[{timeframe}] Tracking {len(tracker.key_levels)} key levels")
            
            # Look for recent break (within last 10 candles)
            break_info = None
            break_candle_idx = None
            
            for i in range(min(retest_window_candles[1], len(data) - 1), 0, -1):
                current = data.iloc[-i]
                previous = data.iloc[-i-1]
                
                detected_break = tracker.detect_break(current, previous)
                if detected_break:
                    break_info = detected_break
                    break_candle_idx = i
                    logger.info(f"[{timeframe}] Found level break {break_info['direction']} at ${break_info['level']:.2f}, {i} candles ago")
                    break
            
            if not break_info:
                logger.debug(f"[{timeframe}] No recent key level break found")
                return None
            
            # Check if break is within retest window
            if break_candle_idx < retest_window_candles[0] or break_candle_idx > retest_window_candles[1]:
                logger.debug(f"[{timeframe}] Break outside retest window: {break_candle_idx} candles ago")
                return None
            
            # Get break candle
            break_candle = data.iloc[-break_candle_idx]
            
            # Validate break had sufficient volume
            break_volume_ratio = break_candle['volume'] / break_candle['volume_ma'] if break_candle['volume_ma'] > 0 else 0
            
            required_break_volume = volume_threshold_break
            if break_info['is_round_number']:
                required_break_volume *= major_level_volume_multiplier
                logger.debug(f"[{timeframe}] Major round number - requiring {required_break_volume:.1f}x volume")
            
            if break_volume_ratio < required_break_volume:
                logger.debug(f"[{timeframe}] Break volume too low: {break_volume_ratio:.2f}x (need >= {required_break_volume:.1f}x)")
                return None
            
            # Check for retest (price came back to level)
            level = break_info['level']
            current_price = last['close']
            atr = last['atr']
            
            # Define retest zone (within 0.5 ATR of level)
            retest_tolerance = atr * 0.5
            
            if break_info['direction'] == 'up':
                # Upward break - looking for retest from above
                # Price should have come back down near level
                if current_price < level - retest_tolerance or current_price > level + retest_tolerance:
                    logger.debug(f"[{timeframe}] Price not in retest zone: ${current_price:.2f} vs level ${level:.2f}")
                    return None
                
                # Check if price is holding above level (successful retest)
                if current_price < level:
                    logger.debug(f"[{timeframe}] Price below broken level - failed retest")
                    return None
                
                # Validate retest volume
                retest_volume_ratio = last['volume'] / last['volume_ma'] if last['volume_ma'] > 0 else 0
                required_retest_volume = break_volume_ratio * volume_threshold_retest
                
                if retest_volume_ratio < required_retest_volume:
                    logger.debug(f"[{timeframe}] Retest volume too low: {retest_volume_ratio:.2f}x (need >= {required_retest_volume:.2f}x)")
                    return None
                
                # Check RSI for continuation
                if last['rsi'] < 40:
                    logger.debug(f"[{timeframe}] RSI too low for bullish continuation: {last['rsi']:.1f}")
                    return None
                
                logger.info(f"[{timeframe}] Bullish key level break & retest confirmed at ${level:.2f}")
                
                # Calculate entry, SL, TP
                entry = last['close']
                stop_loss = level - (atr * 0.8)  # Stop below retested level
                take_profit = entry + (atr * 2.5)  # 2.5 ATR target
                
                risk = abs(entry - stop_loss)
                reward = abs(take_profit - entry)
                risk_reward = reward / risk if risk > 0 else 0
                
                confidence = 5 if break_info['is_round_number'] else 4
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="bullish",
                    confidence=confidence,
                    indicators={
                        'rsi': last['rsi'],
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Key Level Break & Retest: Broke above ${level:.2f} "
                             f"({break_candle_idx} candles ago, {break_volume_ratio:.1f}x volume), "
                             f"successful retest with {retest_volume_ratio:.1f}x volume"
                             f"{', major round number' if break_info['is_round_number'] else ''}",
                    strategy="Key Level Break & Retest",
                    strategy_metadata={
                        'level': level,
                        'break_direction': 'up',
                        'break_candles_ago': break_candle_idx,
                        'break_volume_ratio': break_volume_ratio,
                        'retest_volume_ratio': retest_volume_ratio,
                        'is_round_number': break_info['is_round_number']
                    }
                )
                
                return signal
            
            else:  # direction == 'down'
                # Downward break - looking for retest from below
                # Price should have come back up near level
                if current_price < level - retest_tolerance or current_price > level + retest_tolerance:
                    logger.debug(f"[{timeframe}] Price not in retest zone: ${current_price:.2f} vs level ${level:.2f}")
                    return None
                
                # Check if price is holding below level (successful retest)
                if current_price > level:
                    logger.debug(f"[{timeframe}] Price above broken level - failed retest")
                    return None
                
                # Validate retest volume
                retest_volume_ratio = last['volume'] / last['volume_ma'] if last['volume_ma'] > 0 else 0
                required_retest_volume = break_volume_ratio * volume_threshold_retest
                
                if retest_volume_ratio < required_retest_volume:
                    logger.debug(f"[{timeframe}] Retest volume too low: {retest_volume_ratio:.2f}x (need >= {required_retest_volume:.2f}x)")
                    return None
                
                # Check RSI for continuation
                if last['rsi'] > 60:
                    logger.debug(f"[{timeframe}] RSI too high for bearish continuation: {last['rsi']:.1f}")
                    return None
                
                logger.info(f"[{timeframe}] Bearish key level break & retest confirmed at ${level:.2f}")
                
                # Calculate entry, SL, TP
                entry = last['close']
                stop_loss = level + (atr * 0.8)  # Stop above retested level
                take_profit = entry - (atr * 2.5)  # 2.5 ATR target
                
                risk = abs(stop_loss - entry)
                reward = abs(entry - take_profit)
                risk_reward = reward / risk if risk > 0 else 0
                
                confidence = 5 if break_info['is_round_number'] else 4
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="bearish",
                    confidence=confidence,
                    indicators={
                        'rsi': last['rsi'],
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"Key Level Break & Retest: Broke below ${level:.2f} "
                             f"({break_candle_idx} candles ago, {break_volume_ratio:.1f}x volume), "
                             f"successful retest with {retest_volume_ratio:.1f}x volume"
                             f"{', major round number' if break_info['is_round_number'] else ''}",
                    strategy="Key Level Break & Retest",
                    strategy_metadata={
                        'level': level,
                        'break_direction': 'down',
                        'break_candles_ago': break_candle_idx,
                        'break_volume_ratio': break_volume_ratio,
                        'retest_volume_ratio': retest_volume_ratio,
                        'is_round_number': break_info['is_round_number']
                    }
                )
                
                return signal
            
        except Exception as e:
            logger.error(f"Error in key level break & retest detection: {e}", exc_info=True)
            return None

    def _detect_adx_rsi_momentum_confluence(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str = "BTC/USD",
        adx_min: float = 20,
        adx_strong: float = 25,
        rsi_momentum_threshold: float = 3.0,
        volume_threshold: float = 1.2,
        require_adx_rising: bool = False
    ) -> Optional[Signal]:
        """
        Detect ADX + RSI + Momentum confluence signals.
        
        Strategy:
        1. Check ADX > adx_min (trend forming, default 20)
        2. Check ADX > adx_strong for strong trend (default 25)
        3. Detect RSI directional crosses (above/below 50)
        4. Calculate RSI momentum acceleration (change > 3 points over 2 candles)
        5. Validate price momentum alignment (higher highs for bullish, lower lows for bearish)
        6. Require volume > 1.2x average
        7. Increase confidence when ADX is rising (strengthening trend)
        8. Reject signals when ADX < 18 (market too flat)
        9. Require additional confirmation when RSI in extreme zones (< 30 or > 70)
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            adx_min: Minimum ADX for trend (default 20)
            adx_strong: ADX threshold for strong trend (default 25)
            rsi_momentum_threshold: Minimum RSI change for momentum (default 3.0)
            volume_threshold: Minimum volume ratio (default 1.2)
            require_adx_rising: Whether to require ADX to be rising
            
        Returns:
            Signal if detected, None otherwise
        """
        try:
            if len(data) < 5:
                logger.debug(f"[{timeframe}] Insufficient data for ADX+RSI+Momentum detection")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            prev2 = data.iloc[-3]
            
            # Check for required indicators
            required_indicators = ['adx', 'rsi', 'atr', 'volume', 'volume_ma']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for ADX+RSI+Momentum detection")
                return None
            
            # Check ADX >= minimum (trend forming)
            if last['adx'] < adx_min:
                logger.debug(f"[{timeframe}] ADX too low: {last['adx']:.1f} (need >= {adx_min})")
                return None
            
            # Reject if ADX < 18 (too flat)
            if last['adx'] < 18:
                logger.debug(f"[{timeframe}] Market too flat: ADX {last['adx']:.1f} < 18")
                return None
            
            # Check if ADX is rising (strengthening trend)
            adx_rising = last['adx'] > prev['adx']
            
            if require_adx_rising and not adx_rising:
                logger.debug(f"[{timeframe}] ADX not rising: {prev['adx']:.1f} -> {last['adx']:.1f}")
                return None
            
            # Determine if strong trend
            is_strong_trend = last['adx'] > adx_strong
            
            # Check RSI directional position
            rsi = last['rsi']
            rsi_prev = prev['rsi']
            rsi_prev2 = prev2['rsi']
            
            # Calculate RSI momentum (change over last 2 candles)
            rsi_momentum = abs(rsi - rsi_prev2)
            
            if rsi_momentum < rsi_momentum_threshold:
                logger.debug(f"[{timeframe}] RSI momentum too low: {rsi_momentum:.1f} (need >= {rsi_momentum_threshold})")
                return None
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma'] if last['volume_ma'] > 0 else 0
            if volume_ratio < volume_threshold:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= {volume_threshold}x)")
                return None
            
            # Check price momentum alignment
            current_price = last['close']
            prev_price = prev['close']
            prev2_price = prev2['close']
            
            # Bullish setup: RSI > 50, RSI rising, price making higher highs
            if rsi > 50 and rsi > rsi_prev:
                # Check price momentum (higher highs)
                if current_price <= prev_price or prev_price <= prev2_price:
                    logger.debug(f"[{timeframe}] Price not making higher highs for bullish setup")
                    return None
                
                # Check for extreme RSI (require additional confirmation)
                if rsi > 70:
                    # In extreme zone - require very strong momentum
                    if rsi_momentum < rsi_momentum_threshold * 1.5:
                        logger.debug(f"[{timeframe}] RSI extreme ({rsi:.1f}) - need stronger momentum")
                        return None
                
                # Calculate confidence
                confidence = 4
                if is_strong_trend:
                    confidence = 5
                if adx_rising:
                    confidence = min(5, confidence + 1)
                
                logger.info(f"[{timeframe}] Bullish ADX+RSI+Momentum confluence detected")
                logger.info(f"[{timeframe}] ADX: {last['adx']:.1f}{' (rising)' if adx_rising else ''}, RSI: {rsi:.1f} (momentum: +{rsi_momentum:.1f}), Volume: {volume_ratio:.2f}x")
                
                # Calculate entry, SL, TP
                entry = last['close']
                atr = last['atr']
                
                # Tighter stop for strong trends
                sl_multiplier = 1.5 if is_strong_trend else 2.0
                tp_multiplier = 3.0 if is_strong_trend else 2.5
                
                stop_loss = entry - (atr * sl_multiplier)
                take_profit = entry + (atr * tp_multiplier)
                
                risk = abs(entry - stop_loss)
                reward = abs(take_profit - entry)
                risk_reward = reward / risk if risk > 0 else 0
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="bullish",
                    confidence=confidence,
                    indicators={
                        'adx': last['adx'],
                        'rsi': rsi,
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"ADX+RSI+Momentum Confluence: ADX {last['adx']:.1f} "
                             f"({'strong trend' if is_strong_trend else 'trending'}"
                             f"{', rising' if adx_rising else ''}), "
                             f"RSI {rsi:.1f} with +{rsi_momentum:.1f} momentum, "
                             f"Price making higher highs, Volume {volume_ratio:.2f}x",
                    strategy="ADX+RSI+Momentum",
                    strategy_metadata={
                        'adx': last['adx'],
                        'adx_rising': adx_rising,
                        'is_strong_trend': is_strong_trend,
                        'rsi': rsi,
                        'rsi_momentum': rsi_momentum,
                        'price_momentum': 'higher_highs'
                    }
                )
                
                return signal
            
            # Bearish setup: RSI < 50, RSI falling, price making lower lows
            elif rsi < 50 and rsi < rsi_prev:
                # Check price momentum (lower lows)
                if current_price >= prev_price or prev_price >= prev2_price:
                    logger.debug(f"[{timeframe}] Price not making lower lows for bearish setup")
                    return None
                
                # Check for extreme RSI (require additional confirmation)
                if rsi < 30:
                    # In extreme zone - require very strong momentum
                    if rsi_momentum < rsi_momentum_threshold * 1.5:
                        logger.debug(f"[{timeframe}] RSI extreme ({rsi:.1f}) - need stronger momentum")
                        return None
                
                # Calculate confidence
                confidence = 4
                if is_strong_trend:
                    confidence = 5
                if adx_rising:
                    confidence = min(5, confidence + 1)
                
                logger.info(f"[{timeframe}] Bearish ADX+RSI+Momentum confluence detected")
                logger.info(f"[{timeframe}] ADX: {last['adx']:.1f}{' (rising)' if adx_rising else ''}, RSI: {rsi:.1f} (momentum: -{rsi_momentum:.1f}), Volume: {volume_ratio:.2f}x")
                
                # Calculate entry, SL, TP
                entry = last['close']
                atr = last['atr']
                
                # Tighter stop for strong trends
                sl_multiplier = 1.5 if is_strong_trend else 2.0
                tp_multiplier = 3.0 if is_strong_trend else 2.5
                
                stop_loss = entry + (atr * sl_multiplier)
                take_profit = entry - (atr * tp_multiplier)
                
                risk = abs(stop_loss - entry)
                reward = abs(entry - take_profit)
                risk_reward = reward / risk if risk > 0 else 0
                
                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    symbol=symbol,
                    symbol_context=self._create_symbol_context(symbol),
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    risk_reward=risk_reward,
                    market_bias="bearish",
                    confidence=confidence,
                    indicators={
                        'adx': last['adx'],
                        'rsi': rsi,
                        'atr': atr,
                        'volume': last['volume'],
                        'volume_ma': last['volume_ma']
                    },
                    reasoning=f"ADX+RSI+Momentum Confluence: ADX {last['adx']:.1f} "
                             f"({'strong trend' if is_strong_trend else 'trending'}"
                             f"{', rising' if adx_rising else ''}), "
                             f"RSI {rsi:.1f} with -{rsi_momentum:.1f} momentum, "
                             f"Price making lower lows, Volume {volume_ratio:.2f}x",
                    strategy="ADX+RSI+Momentum",
                    strategy_metadata={
                        'adx': last['adx'],
                        'adx_rising': adx_rising,
                        'is_strong_trend': is_strong_trend,
                        'rsi': rsi,
                        'rsi_momentum': rsi_momentum,
                        'price_momentum': 'lower_lows'
                    }
                )
                
                return signal
            
            else:
                logger.debug(f"[{timeframe}] No clear RSI directional signal: RSI {rsi:.1f}")
                return None
            
        except Exception as e:
            logger.error(f"Error in ADX+RSI+Momentum confluence detection: {e}", exc_info=True)
            return None
