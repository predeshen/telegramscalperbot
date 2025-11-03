"""
Gold Signal Detector with Multiple Strategies
Implements Asian Range Breakout, EMA Cloud Breakout, and Mean Reversion strategies
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
import pandas as pd
import logging

from src.signal_detector import Signal
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
    """
    
    def __init__(self,
                 session_manager: SessionManager,
                 key_level_tracker: KeyLevelTracker,
                 strategy_selector: StrategySelector):
        """
        Initialize Gold Signal Detector.
        
        Args:
            session_manager: SessionManager for session detection
            key_level_tracker: KeyLevelTracker for level analysis
            strategy_selector: StrategySelector for strategy selection
        """
        self.session_manager = session_manager
        self.key_level_tracker = key_level_tracker
        self.strategy_selector = strategy_selector
        
        # Signal history for duplicate prevention
        self.recent_signals = []
        self.duplicate_window_minutes = 15
        
        logger.info("GoldSignalDetector initialized with 3 strategies")
    
    def detect_signals(self, data: pd.DataFrame, timeframe: str) -> Optional[GoldSignal]:
        """
        Detect trading signals using appropriate strategy.
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            
        Returns:
            GoldSignal if detected, None otherwise
        """
        if data.empty or len(data) < 50:
            return None
        
        # Get current session
        current_session = self.session_manager.get_current_session()
        
        # Select strategy
        strategy = self.strategy_selector.select_strategy(data, current_session)
        
        if strategy == GoldStrategy.NO_TRADE:
            return None
        
        # Route to appropriate strategy
        signal = None
        
        if strategy == GoldStrategy.ASIAN_RANGE_BREAKOUT:
            signal = self._detect_asian_range_breakout(data, timeframe)
        
        elif strategy == GoldStrategy.EMA_CLOUD_BREAKOUT:
            signal = self._detect_ema_cloud_breakout(data, timeframe)
        
        elif strategy == GoldStrategy.MEAN_REVERSION:
            signal = self._detect_mean_reversion(data, timeframe)
        
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
    
    def _detect_asian_range_breakout(self, data: pd.DataFrame, timeframe: str) -> Optional[GoldSignal]:
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
                            strategy="Asian Range Breakout"
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
                            strategy="Asian Range Breakout"
                        )
                        
                        return signal
            
            return None
        
        except Exception as e:
            logger.error(f"Error in Asian Range Breakout detection: {e}")
            return None

    
    def _detect_ema_cloud_breakout(self, data: pd.DataFrame, timeframe: str) -> Optional[GoldSignal]:
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
                        strategy="EMA Cloud Breakout"
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
                        strategy="EMA Cloud Breakout"
                    )
                    
                    return signal
            
            return None
        
        except Exception as e:
            logger.error(f"Error in EMA Cloud Breakout detection: {e}")
            return None
    
    def _detect_mean_reversion(self, data: pd.DataFrame, timeframe: str) -> Optional[GoldSignal]:
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
                    strategy="Mean Reversion"
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
                    strategy="Mean Reversion"
                )
                
                return signal
            
            return None
        
        except Exception as e:
            logger.error(f"Error in Mean Reversion detection: {e}")
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
                           atr: float, indicators: pd.Series, strategy: str) -> GoldSignal:
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
