"""
Gold Signal Detector with Multiple Strategies
Implements Asian Range Breakout, EMA Cloud Breakout, Mean Reversion, Trend Following, and H4 HVG strategies
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
import pandas as pd
import logging

from src.signal_detector import Signal
from src.trend_analyzer import TrendAnalyzer
from src.h4_hvg_detector import H4HVGDetector
from xauusd_scanner.strategy_selector import GoldStrategy, StrategySelector
from xauusd_scanner.session_manager import SessionManager
from xauusd_scanner.key_level_tracker import KeyLevelTracker

logger = logging.getLogger(__name__)


@dataclass
class GoldSignal(Signal):
    """Extended signal class for Gold with additional context."""
    strategy: str = ""
    session: str = ""
    asian_range_info: Optional[Dict] = None
    key_level_info: Optional[Dict] = None
    spread_pips: Optional[float] = None


class GoldSignalDetector:
    """
    Detects trading signals for Gold (XAU/USD) using multiple strategies.
    
    Strategies:
    1. Asian Range Breakout - Breakout of Asian session range
    2. EMA Cloud Breakout - Trend following with EMA alignment
    3. Mean Reversion - Reversals when overextended from VWAP
    4. Trend Following - Pullback entries within established trends
    5. H4 HVG - 4-Hour High Volume Gap detection
    """
    
    def __init__(self,
                 session_manager: SessionManager,
                 key_level_tracker: KeyLevelTracker,
                 strategy_selector: StrategySelector,
                 h4_hvg_config: Optional[Dict] = None):
        """
        Initialize Gold Signal Detector.
        
        Args:
            session_manager: SessionManager for session detection
            key_level_tracker: KeyLevelTracker for level analysis
            strategy_selector: StrategySelector for strategy selection
            h4_hvg_config: H4 HVG configuration dictionary
        """
        self.session_manager = session_manager
        self.key_level_tracker = key_level_tracker
        self.strategy_selector = strategy_selector
        
        # Initialize H4 HVG detector if config provided
        self.h4_hvg_detector = None
        if h4_hvg_config:
            self.h4_hvg_detector = H4HVGDetector(config=h4_hvg_config, symbol="XAU/USD")
            logger.info("H4HVGDetector initialized for Gold with XAU market settings")
        
        # Signal history for duplicate prevention
        self.recent_signals = []
        self.duplicate_window_minutes = 15
        
        strategy_count = 5 if self.h4_hvg_detector else 4
        logger.info(f"GoldSignalDetector initialized with {strategy_count} strategies")
    
    def detect_signals(self, data: pd.DataFrame, timeframe: str, symbol: str = "XAU/USD") -> Optional[GoldSignal]:
        """
        Detect trading signals using appropriate strategy.
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            symbol: Trading symbol (default: "XAU/USD", used for H4 HVG detection and alerts)
            
        Returns:
            GoldSignal if detected, None otherwise
        """
        if data.empty or len(data) < 50:
            return None
        
        # Check for H4 HVG signal first on 4-hour timeframe
        if timeframe == '4h' and self.h4_hvg_detector:
            hvg_signal = self.h4_hvg_detector.generate_h4_hvg_signal(data, timeframe, symbol)
            if hvg_signal:
                # Check for duplicates using H4 HVG detector's own duplicate detection
                if not self.h4_hvg_detector.is_duplicate_signal(hvg_signal):
                    # Add to H4 HVG detector's history
                    self.h4_hvg_detector.add_signal_to_history(hvg_signal)
                    
                    # Convert to GoldSignal and add session context
                    gold_signal = self._convert_to_gold_signal(hvg_signal)
                    current_session = self.session_manager.get_current_session()
                    gold_signal.session = current_session.value
                    
                    # Add Asian range info if available
                    asian_range = self.session_manager.get_asian_range()
                    if asian_range:
                        gold_signal.asian_range_info = asian_range
                    
                    # Add key level info
                    last_price = data.iloc[-1]['close']
                    gold_signal.key_level_info = self.key_level_tracker.get_level_status(last_price)
                    
                    logger.info(f"🎯 {gold_signal.signal_type} signal: H4 HVG on {timeframe}")
                    return gold_signal
        
        # Try momentum shift first (universal strategy that works in all sessions)
        signal = self._detect_momentum_shift(data, timeframe, symbol)
        
        if signal:
            # Add session context
            current_session = self.session_manager.get_current_session()
            signal.session = current_session.value
            signal.strategy = "Momentum Shift"
            
            # Check for duplicates
            if not self._is_duplicate(signal):
                self.recent_signals.append(signal)
                logger.info(f"🎯 {signal.signal_type} signal: Momentum Shift on {timeframe}")
                return signal
        
        # Get current session
        current_session = self.session_manager.get_current_session()
        
        # Select strategy
        strategy = self.strategy_selector.select_strategy(data, current_session)
        
        if strategy == GoldStrategy.NO_TRADE:
            return None
        
        # Route to appropriate strategy
        signal = None
        
        if strategy == GoldStrategy.ASIAN_RANGE_BREAKOUT:
            signal = self._detect_asian_range_breakout(data, timeframe, symbol)
        
        elif strategy == GoldStrategy.EMA_CLOUD_BREAKOUT:
            signal = self._detect_ema_cloud_breakout(data, timeframe, symbol)
        
        elif strategy == GoldStrategy.MEAN_REVERSION:
            signal = self._detect_mean_reversion(data, timeframe, symbol)
        
        elif strategy == GoldStrategy.TREND_FOLLOWING:
            signal = self._detect_trend_following(data, timeframe, symbol)
        
        # Add session and strategy context if signal found
        if signal:
            signal.strategy = strategy.value
            signal.session = current_session.value
            
            # Add Asian range info if available
            asian_range = self.session_manager.get_asian_range()
            if asian_range:
                signal.asian_range_info = asian_range
            
            # Add key level info
            last_price = data.iloc[-1]['close']
            signal.key_level_info = self.key_level_tracker.get_level_status(last_price)
            
            # Check for duplicates
            if not self._is_duplicate(signal):
                self.recent_signals.append(signal)
                logger.info(f"🎯 {signal.signal_type} signal: {strategy.value} on {timeframe}")
                return signal
        
        return None
    
    def _detect_momentum_shift(self, data: pd.DataFrame, timeframe: str, symbol: str = "XAU/USD") -> Optional[GoldSignal]:
        """
        Detect Momentum Shift signals - catches RSI turning with ADX confirmation.
        
        Strategy (universal - works in all sessions):
        - Uses RSI(7) for faster momentum detection
        - Bullish: RSI turning up (increasing over last 2-3 candles)
        - Bearish: RSI turning down (decreasing over last 2-3 candles)
        - ADX >= 18 (trend forming, not flat)
        - Volume >= 1.2x average (Gold needs good volume)
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            symbol: Trading symbol (default: "XAU/USD")
            
        Returns:
            GoldSignal if detected, None otherwise
        """
        try:
            if len(data) < 4:
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            prev2 = data.iloc[-3]
            
            # Check for required indicators
            required_indicators = ['rsi_7', 'adx', 'volume', 'volume_ma', 'atr']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for momentum shift detection")
                return None
            
            # Check ADX >= 18 (trend forming)
            if last['adx'] < 18:
                logger.debug(f"[{timeframe}] ADX too low: {last['adx']:.1f} (need >= 18 for momentum shift)")
                return None
            
            # Calculate volume ratio
            volume_ratio = last['volume'] / last['volume_ma']
            
            # Check volume threshold (1.2x for Gold)
            if volume_ratio < 1.2:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= 1.2x)")
                return None
            
            # Check for RSI(7) turning up (bullish momentum shift)
            rsi_7_current = last['rsi_7']
            rsi_7_prev = prev['rsi_7']
            rsi_7_prev2 = prev2['rsi_7']
            
            # Bullish Momentum Shift: RSI(7) turning up
            if rsi_7_current > rsi_7_prev and rsi_7_prev > rsi_7_prev2:
                # CRITICAL: Check if we're actually in an uptrend
                # Don't generate LONG signals in a downtrend!
                if last['close'] < last['ema_50']:
                    logger.debug(f"[{timeframe}] Bullish RSI turn rejected - price below EMA(50): ${last['close']:.2f} < ${last['ema_50']:.2f} (downtrend)")
                    return None
                
                # Check recent price action (last 10 candles should show upward bias)
                if len(data) >= 10:
                    recent_close = data['close'].iloc[-10]
                    if last['close'] < recent_close:
                        logger.debug(f"[{timeframe}] Bullish RSI turn rejected - price declining over last 10 candles: ${recent_close:.2f} -> ${last['close']:.2f}")
                        return None
                
                logger.info(f"[{timeframe}] Bullish momentum shift detected - RSI(7): {rsi_7_prev2:.1f} -> {rsi_7_prev:.1f} -> {rsi_7_current:.1f} (turning up)")
                logger.info(f"[{timeframe}] Trend confirmed: Price ${last['close']:.2f} > EMA(50) ${last['ema_50']:.2f}")
                logger.info(f"[{timeframe}] ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry - (last['atr'] * 2.0)
                take_profit = entry + (last['atr'] * 3.0)
                
                signal = self._create_gold_signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    indicators=last,
                    strategy="Momentum Shift (Bullish RSI Turn)",
                    symbol=symbol
                )
                
                return signal
            
            # Bearish Momentum Shift: RSI(7) turning down
            elif rsi_7_current < rsi_7_prev and rsi_7_prev < rsi_7_prev2:
                # CRITICAL: Check if we're actually in a downtrend
                # Don't generate SHORT signals in an uptrend!
                if last['close'] > last['ema_50']:
                    logger.debug(f"[{timeframe}] Bearish RSI turn rejected - price above EMA(50): ${last['close']:.2f} > ${last['ema_50']:.2f} (uptrend)")
                    return None
                
                # Check recent price action (last 10 candles should show downward bias)
                if len(data) >= 10:
                    recent_close = data['close'].iloc[-10]
                    if last['close'] > recent_close:
                        logger.debug(f"[{timeframe}] Bearish RSI turn rejected - price rising over last 10 candles: ${recent_close:.2f} -> ${last['close']:.2f}")
                        return None
                
                logger.info(f"[{timeframe}] Bearish momentum shift detected - RSI(7): {rsi_7_prev2:.1f} -> {rsi_7_prev:.1f} -> {rsi_7_current:.1f} (turning down)")
                logger.info(f"[{timeframe}] Trend confirmed: Price ${last['close']:.2f} < EMA(50) ${last['ema_50']:.2f}")
                logger.info(f"[{timeframe}] ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry + (last['atr'] * 2.0)
                take_profit = entry - (last['atr'] * 3.0)
                
                signal = self._create_gold_signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    indicators=last,
                    strategy="Momentum Shift (Bearish RSI Turn)",
                    symbol=symbol
                )
                
                return signal
            
            else:
                logger.debug(f"[{timeframe}] No momentum shift: RSI(7) {rsi_7_prev2:.1f} -> {rsi_7_prev:.1f} -> {rsi_7_current:.1f}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in momentum shift detection: {e}", exc_info=True)
            return None
    
    def _detect_asian_range_breakout(self, data: pd.DataFrame, timeframe: str, symbol: str = "XAU/USD") -> Optional[GoldSignal]:
        """
        Detect Asian Range Breakout signals.
        
        Strategy:
        1. Price breaks above/below Asian range
        2. Wait for re-test of broken level
        3. Confirm with pin bar or engulfing candle
        4. Volume > 1.2x average
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            
        Returns:
            GoldSignal if detected
        """
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            prev2 = data.iloc[-3] if len(data) >= 3 else None
            
            asian_range = self.session_manager.get_asian_range()
            if not asian_range or asian_range['is_tracking']:
                return None
            
            current_price = last['close']
            atr = last['atr']
            
            # Check for breakout
            is_bullish_breakout = self.session_manager.is_breakout_above_asian_range(current_price, buffer_pips=2.0)
            is_bearish_breakout = self.session_manager.is_breakout_below_asian_range(current_price, buffer_pips=2.0)
            
            if not (is_bullish_breakout or is_bearish_breakout):
                return None
            
            # Check volume confirmation
            if last['volume'] < (last['volume_ma'] * 1.2):
                return None
            
            # Detect re-test (price came back to range then bounced)
            if prev2:
                if is_bullish_breakout:
                    # Check if previous candle tested the high
                    retest = (prev['low'] <= asian_range['high'] + 0.2 and  # Came back to level
                             last['close'] > prev['close'])  # Then bounced up
                    
                    if retest:
                        # LONG signal
                        entry = last['close']
                        stop_loss = asian_range['high'] - (atr * 0.5)  # Tight stop below breakout level
                        take_profit = entry + (atr * 1.5)
                        
                        signal = self._create_gold_signal(
                            timestamp=last['timestamp'],
                            signal_type="LONG",
                            timeframe=timeframe,
                            entry_price=entry,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            atr=atr,
                            indicators=last,
                            strategy="Asian Range Breakout",
                            symbol=symbol
                        )
                        
                        return signal
                
                elif is_bearish_breakout:
                    # Check if previous candle tested the low
                    retest = (prev['high'] >= asian_range['low'] - 0.2 and
                             last['close'] < prev['close'])
                    
                    if retest:
                        # SHORT signal
                        entry = last['close']
                        stop_loss = asian_range['low'] + (atr * 0.5)
                        take_profit = entry - (atr * 1.5)
                        
                        signal = self._create_gold_signal(
                            timestamp=last['timestamp'],
                            signal_type="SHORT",
                            timeframe=timeframe,
                            entry_price=entry,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            atr=atr,
                            indicators=last,
                            strategy="Asian Range Breakout",
                            symbol=symbol
                        )
                        
                        return signal
            
            return None
        
        except Exception as e:
            logger.error(f"Error in Asian Range Breakout detection: {e}")
            return None

    
    def _detect_ema_cloud_breakout(self, data: pd.DataFrame, timeframe: str, symbol: str = "XAU/USD") -> Optional[GoldSignal]:
        """
        Detect EMA Cloud Breakout signals.
        
        Strategy:
        1. EMA(20) and EMA(50) aligned (trending)
        2. Price vs VWAP for institutional bias
        3. Range breakout with volume confirmation
        4. RSI 25-75 range
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            
        Returns:
            GoldSignal if detected
        """
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Use ema_21 if ema_20 not available
            ema_20 = last.get('ema_20', last.get('ema_21'))
            ema_50 = last['ema_50']
            atr = last['atr']
            
            # Check EMA alignment
            bullish_alignment = ema_20 > ema_50
            bearish_alignment = ema_20 < ema_50
            
            if not (bullish_alignment or bearish_alignment):
                return None
            
            # Check VWAP position
            price_above_vwap = last['close'] > last['vwap']
            price_below_vwap = last['close'] < last['vwap']
            
            # Check RSI range
            if last['rsi'] < 25 or last['rsi'] > 75:
                return None
            
            # Check volume
            if last['volume'] < (last['volume_ma'] * 1.5):
                return None
            
            # Bullish setup
            if bullish_alignment and price_above_vwap:
                # Check for breakout (price breaking above recent high)
                recent_high = data['high'].iloc[-10:-1].max()
                
                if last['close'] > recent_high:
                    entry = last['close']
                    stop_loss = entry - (atr * 1.2)
                    take_profit = entry + (atr * 1.5)
                    
                    signal = self._create_gold_signal(
                        timestamp=last['timestamp'],
                        signal_type="LONG",
                        timeframe=timeframe,
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        atr=atr,
                        indicators=last,
                        strategy="EMA Cloud Breakout",
                        symbol=symbol
                    )
                    
                    return signal
            
            # Bearish setup
            elif bearish_alignment and price_below_vwap:
                # Check for breakdown
                recent_low = data['low'].iloc[-10:-1].min()
                
                if last['close'] < recent_low:
                    entry = last['close']
                    stop_loss = entry + (atr * 1.2)
                    take_profit = entry - (atr * 1.5)
                    
                    signal = self._create_gold_signal(
                        timestamp=last['timestamp'],
                        signal_type="SHORT",
                        timeframe=timeframe,
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        atr=atr,
                        indicators=last,
                        strategy="EMA Cloud Breakout",
                        symbol=symbol
                    )
                    
                    return signal
            
            return None
        
        except Exception as e:
            logger.error(f"Error in EMA Cloud Breakout detection: {e}")
            return None
    
    def _detect_mean_reversion(self, data: pd.DataFrame, timeframe: str, symbol: str = "XAU/USD") -> Optional[GoldSignal]:
        """
        Detect Mean Reversion signals.
        
        Strategy:
        1. Price overextended (> 1.5x ATR from VWAP)
        2. RSI extremes (> 75 or < 25)
        3. Reversal candle (pin bar, doji, engulfing)
        4. Volume confirms reversal
        5. Target VWAP for mean reversion
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            
        Returns:
            GoldSignal if detected
        """
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            atr = last['atr']
            vwap = last['vwap']
            current_price = last['close']
            
            # Check overextension
            distance_from_vwap = abs(current_price - vwap)
            
            if distance_from_vwap < (atr * 1.5):
                return None
            
            # Check RSI extremes
            rsi_overbought = last['rsi'] > 75
            rsi_oversold = last['rsi'] < 25
            
            if not (rsi_overbought or rsi_oversold):
                return None
            
            # Check volume confirmation
            if last['volume'] < (last['volume_ma'] * 1.3):
                return None
            
            # Detect reversal candles
            is_pin_bar = self._is_pin_bar(last)
            is_engulfing = self._is_engulfing(last, prev)
            is_doji = self._is_doji(last)
            
            if not (is_pin_bar or is_engulfing or is_doji):
                return None
            
            # Bullish reversal (price below VWAP, oversold)
            if current_price < vwap and rsi_oversold:
                entry = last['close']
                stop_loss = entry - (atr * 1.0)
                take_profit = vwap  # Target mean (VWAP)
                
                signal = self._create_gold_signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    indicators=last,
                    strategy="Mean Reversion",
                    symbol=symbol
                )
                
                return signal
            
            # Bearish reversal (price above VWAP, overbought)
            elif current_price > vwap and rsi_overbought:
                entry = last['close']
                stop_loss = entry + (atr * 1.0)
                take_profit = vwap  # Target mean (VWAP)
                
                signal = self._create_gold_signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    indicators=last,
                    strategy="Mean Reversion",
                    symbol=symbol
                )
                
                return signal
            
            return None
        
        except Exception as e:
            logger.error(f"Error in Mean Reversion detection: {e}")
            return None
    
    def _detect_trend_following(self, data: pd.DataFrame, timeframe: str, symbol: str = "XAU/USD") -> Optional[GoldSignal]:
        """
        Detect trend-following signals for Gold.
        
        Strategy:
        1. Detect swing points to identify trend
        2. Verify EMA alignment with trend
        3. Wait for pullback to EMA(21)
        4. Confirm bounce with volume
        5. Validate RSI range
        6. Integrate session awareness and key levels
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            
        Returns:
            GoldSignal if detected, None otherwise
        """
        try:
            if len(data) < 50:
                return None
            
            # Detect swing points
            swing_data = TrendAnalyzer.detect_swing_points(data, lookback=5)
            
            # Check for uptrend or downtrend
            is_uptrend = TrendAnalyzer.is_uptrend(swing_data, min_swings=3)
            is_downtrend = TrendAnalyzer.is_downtrend(swing_data, min_swings=3)
            
            if not (is_uptrend or is_downtrend):
                return None
            
            trend_direction = "uptrend" if is_uptrend else "downtrend"
            
            # Check if market is consolidating
            if TrendAnalyzer.is_consolidating(data, periods=3):
                logger.debug(f"Skipping Gold trend signal: market consolidating on {timeframe}")
                return None
            
            # Verify EMA alignment
            if not TrendAnalyzer.is_ema_aligned(data, trend_direction):
                return None
            
            # Get last candles
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Calculate pullback depth
            pullback_depth = TrendAnalyzer.calculate_pullback_depth(data, trend_direction)
            
            # Reject if pullback too deep
            if pullback_depth > 61.8:
                logger.debug(f"Skipping Gold trend signal: pullback too deep ({pullback_depth:.1f}%) on {timeframe}")
                return None
            
            # Check volume confirmation
            if last['volume'] < (last['volume_ma'] * 1.2):
                return None
            
            # Check if volume is declining
            volume_declining = (
                last['volume'] < prev['volume'] and
                prev['volume'] < data.iloc[-3]['volume']
            )
            
            if volume_declining:
                logger.debug(f"Skipping Gold trend signal: volume declining on {timeframe}")
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
                
                # Count swing points
                total_swings = swing_data['higher_highs'] + swing_data['higher_lows']
                
                # Create signal
                signal = self._create_gold_signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    indicators=last,
                    strategy="Trend Following",
                    symbol=symbol
                )
                
                # Add trend-specific metadata
                signal.trend_direction = trend_direction
                signal.swing_points = total_swings
                signal.pullback_depth = pullback_depth
                
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
                
                # Count swing points
                total_swings = swing_data['lower_highs'] + swing_data['lower_lows']
                
                # Create signal
                signal = self._create_gold_signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=atr,
                    indicators=last,
                    strategy="Trend Following",
                    symbol=symbol
                )
                
                # Add trend-specific metadata
                signal.trend_direction = trend_direction
                signal.swing_points = total_swings
                signal.pullback_depth = pullback_depth
                
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Gold Trend Following detection: {e}")
            return None
    
    def _is_pin_bar(self, candle: pd.Series) -> bool:
        """Check if candle is a pin bar (long wick, small body)."""
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        if total_range == 0:
            return False
        
        # Body should be < 30% of total range
        # Wick should be > 60% of total range
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        
        long_upper_wick = upper_wick > (total_range * 0.6) and body < (total_range * 0.3)
        long_lower_wick = lower_wick > (total_range * 0.6) and body < (total_range * 0.3)
        
        return long_upper_wick or long_lower_wick
    
    def _is_engulfing(self, current: pd.Series, previous: pd.Series) -> bool:
        """Check if current candle engulfs previous."""
        curr_body = abs(current['close'] - current['open'])
        prev_body = abs(previous['close'] - previous['open'])
        
        # Current body should be larger
        if curr_body <= prev_body:
            return False
        
        # Bullish engulfing
        if current['close'] > current['open'] and previous['close'] < previous['open']:
            if current['open'] < previous['close'] and current['close'] > previous['open']:
                return True
        
        # Bearish engulfing
        if current['close'] < current['open'] and previous['close'] > previous['open']:
            if current['open'] > previous['close'] and current['close'] < previous['open']:
                return True
        
        return False
    
    def _is_doji(self, candle: pd.Series) -> bool:
        """Check if candle is a doji (very small body)."""
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        if total_range == 0:
            return False
        
        # Body should be < 10% of total range
        return body < (total_range * 0.1)
    
    def _create_gold_signal(self, timestamp: datetime, signal_type: str, timeframe: str,
                           entry_price: float, stop_loss: float, take_profit: float,
                           atr: float, indicators: pd.Series, strategy: str, symbol: str = "XAU/USD") -> GoldSignal:
        """Create a GoldSignal with full context."""
        risk_reward = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
        
        # Get market bias
        if indicators['close'] > indicators['ema_50']:
            market_bias = "bullish"
        elif indicators['close'] < indicators['ema_50']:
            market_bias = "bearish"
        else:
            market_bias = "neutral"
        
        # Generate reasoning
        reasoning = self._generate_gold_reasoning(
            signal_type, indicators, strategy, market_bias
        )
        
        signal = GoldSignal(
            timestamp=timestamp,
            signal_type=signal_type,
            timeframe=timeframe,
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            atr=atr,
            risk_reward=risk_reward,
            market_bias=market_bias,
            confidence=4,  # Gold signals are high confidence
            indicators={
                'ema_9': indicators.get('ema_9'),
                'ema_21': indicators.get('ema_21'),
                'ema_50': indicators['ema_50'],
                'vwap': indicators['vwap'],
                'rsi': indicators['rsi'],
                'volume': indicators['volume'],
                'volume_ma': indicators['volume_ma']
            },
            reasoning=reasoning,
            strategy=strategy,
            session="",  # Will be set by caller
            asian_range_info=None,  # Will be set by caller
            key_level_info=None,  # Will be set by caller
            spread_pips=None  # Will be set by caller
        )
        
        return signal
    
    def _generate_gold_reasoning(self, signal_type: str, indicators: pd.Series,
                                 strategy: str, market_bias: str) -> str:
        """Generate detailed reasoning for Gold signal."""
        reasons = []
        
        # Strategy-specific intro
        reasons.append(f"🎯 STRATEGY: {strategy}")
        
        # Session context
        session_info = self.session_manager.get_session_info()
        reasons.append(f"⏰ SESSION: {session_info['session']} - {session_info['recommendation']}")
        
        # Asian range context (if applicable)
        if strategy == "Asian Range Breakout":
            asian_range = self.session_manager.get_asian_range()
            if asian_range:
                reasons.append(f"📊 ASIAN RANGE: ${asian_range['low']:.2f} - ${asian_range['high']:.2f} ({asian_range['range_pips']:.1f} pips)")
                if signal_type == "LONG":
                    reasons.append(f"   • Breaking above range with re-test confirmation")
                else:
                    reasons.append(f"   • Breaking below range with re-test confirmation")
        
        # Market bias
        if signal_type == "LONG":
            reasons.append(f"📈 BULLISH SETUP: Price above VWAP (${indicators['vwap']:.2f}), institutional buyers active")
        else:
            reasons.append(f"📉 BEARISH SETUP: Price below VWAP (${indicators['vwap']:.2f}), institutional sellers active")
        
        # Volume confirmation
        volume_ratio = indicators['volume'] / indicators['volume_ma']
        reasons.append(f"📊 VOLUME: {volume_ratio:.2f}x average - confirms genuine move")
        
        # RSI context
        reasons.append(f"⚡ RSI: {indicators['rsi']:.1f} - momentum {'strong' if 40 <= indicators['rsi'] <= 60 else 'extreme'}")
        
        # Key levels
        last_price = indicators['close']
        level_context = self.key_level_tracker.get_level_context_for_signal(last_price, signal_type)
        if level_context:
            reasons.append(level_context)
        
        # Why enter NOW
        reasons.append(f"\n💡 WHY ENTER NOW:")
        reasons.append(f"   • {strategy} setup fully formed")
        reasons.append(f"   • {session_info['session']} session - optimal timing")
        reasons.append(f"   • All confluence factors aligned")
        reasons.append(f"   • Volume confirms institutional participation")
        
        return "\n".join(reasons)
    
    def _convert_to_gold_signal(self, hvg_signal) -> GoldSignal:
        """
        Convert H4 HVG Signal to GoldSignal with Gold-specific context.
        
        Args:
            hvg_signal: H4 HVG Signal object
            
        Returns:
            GoldSignal with Gold-specific enhancements
        """
        # Create GoldSignal from H4 HVG signal
        gold_signal = GoldSignal(
            timestamp=hvg_signal.timestamp,
            signal_type=hvg_signal.signal_type,
            timeframe=hvg_signal.timeframe,
            symbol=hvg_signal.symbol,
            entry_price=hvg_signal.entry_price,
            stop_loss=hvg_signal.stop_loss,
            take_profit=hvg_signal.take_profit,
            atr=hvg_signal.atr,
            risk_reward=hvg_signal.risk_reward,
            market_bias=hvg_signal.market_bias,
            confidence=hvg_signal.confidence,
            indicators=hvg_signal.indicators,
            reasoning=hvg_signal.reasoning,
            strategy=hvg_signal.strategy,
            gap_info=hvg_signal.gap_info,
            volume_spike_ratio=hvg_signal.volume_spike_ratio,
            confluence_factors=hvg_signal.confluence_factors,
            session="",  # Will be set by caller
            asian_range_info=None,  # Will be set by caller
            key_level_info=None,  # Will be set by caller
            spread_pips=None  # Will be set by caller
        )
        
        return gold_signal
    
    def _is_duplicate(self, signal: GoldSignal) -> bool:
        """Check if signal is duplicate of recent signal."""
        from datetime import timedelta
        
        cutoff_time = signal.timestamp - timedelta(minutes=self.duplicate_window_minutes)
        
        for prev_signal in self.recent_signals:
            if prev_signal.timestamp < cutoff_time:
                continue
            
            if prev_signal.signal_type != signal.signal_type:
                continue
            
            price_diff = abs(signal.entry_price - prev_signal.entry_price)
            if price_diff < (signal.atr * 0.5):
                logger.debug(f"Duplicate signal blocked: {signal.signal_type}")
                return True
        
        return False
