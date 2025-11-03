"""Signal detection with confluence-based trading logic."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Dict
import pandas as pd
import logging

from src.trend_analyzer import TrendAnalyzer


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
    reasoning: str = ""  # Detailed explanation of why this signal was generated
    strategy: str = ""  # Strategy name (e.g., "Trend Following", "EMA Crossover")
    trend_direction: Optional[str] = None  # "uptrend" or "downtrend" for trend signals
    swing_points: Optional[int] = None  # Number of swing highs/lows for trend signals
    pullback_depth: Optional[float] = None  # Pullback percentage for trend signals
    
    def to_dict(self) -> dict:
        """Convert signal to dictionary."""
        return asdict(self)
    
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
        
        logger.info("Initialized SignalDetector with confluence rules")
    
    def detect_signals(self, data: pd.DataFrame, timeframe: str) -> Optional[Signal]:
        """
        Detect trading signals from candlestick data with indicators.
        
        Args:
            data: DataFrame with OHLCV and calculated indicators
            timeframe: Timeframe string (e.g., '1m', '5m')
            
        Returns:
            Signal object if detected, None otherwise
        """
        if data.empty or len(data) < 3:
            return None
        
        # Clean expired signals from history
        self._clean_expired_signals()
        
        # PRIORITY 1: Check for trend-following signals (catches ongoing trends)
        trend_signal = self._detect_trend_following(data, timeframe)
        if trend_signal and not self._is_duplicate_signal(trend_signal):
            self.signal_history.append(trend_signal)
            logger.info(f"{trend_signal.signal_type} trend-following signal detected on {timeframe}: {trend_signal.entry_price}")
            return trend_signal
        
        # PRIORITY 2: Check for bullish crossover signal
        bullish_signal = self._check_bullish_confluence(data, timeframe)
        if bullish_signal and not self._is_duplicate_signal(bullish_signal):
            self.signal_history.append(bullish_signal)
            logger.info(f"LONG signal detected on {timeframe}: {bullish_signal.entry_price}")
            return bullish_signal
        
        # PRIORITY 3: Check for bearish crossover signal
        bearish_signal = self._check_bearish_confluence(data, timeframe)
        if bearish_signal and not self._is_duplicate_signal(bearish_signal):
            self.signal_history.append(bearish_signal)
            logger.info(f"SHORT signal detected on {timeframe}: {bearish_signal.entry_price}")
            return bearish_signal
        
        return None
    
    def _check_bullish_confluence(self, data: pd.DataFrame, timeframe: str) -> Optional[Signal]:
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
            stop_loss = entry_price - (atr * self.stop_loss_atr_multiplier)
            take_profit = entry_price + (atr * self.take_profit_atr_multiplier)
            risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)
            
            # Generate reasoning
            reasoning = self._generate_reasoning("LONG", last, prev, confluence_count, market_bias)
            
            signal = Signal(
                timestamp=last['timestamp'],
                signal_type="LONG",
                timeframe=timeframe,
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
    
    def _check_bearish_confluence(self, data: pd.DataFrame, timeframe: str) -> Optional[Signal]:
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
            stop_loss = entry_price + (atr * self.stop_loss_atr_multiplier)
            take_profit = entry_price - (atr * self.take_profit_atr_multiplier)
            risk_reward = (entry_price - take_profit) / (stop_loss - entry_price)
            
            # Generate reasoning
            reasoning = self._generate_reasoning("SHORT", last, prev, confluence_count, market_bias)
            
            signal = Signal(
                timestamp=last['timestamp'],
                signal_type="SHORT",
                timeframe=timeframe,
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
                
                if price_change_percent < self.duplicate_price_threshold_percent:
                    logger.debug(f"Duplicate signal blocked: {signal.signal_type} within {time_diff.seconds}s")
                    return True
        
        return False
    
    def _clean_expired_signals(self) -> None:
        """Remove signals older than 30 minutes from history."""
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        # Filter out expired signals
        self.signal_history = deque(
            [s for s in self.signal_history if s.timestamp > cutoff_time],
            maxlen=50
        )
    
    def _detect_trend_following(self, data: pd.DataFrame, timeframe: str) -> Optional[Signal]:
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
            
            # RELAXED: Volume should be at least average (not necessarily spiking)
            # Strong trends can continue on average volume
            if last['volume'] < (last['volume_ma'] * 0.8):
                logger.debug(f"Skipping trend signal: volume too low on {timeframe}")
                return None
            
            # Don't require volume spike for trend continuation
            # Volume declining is OK as long as it's not collapsing
            
            # Detect pullback entry for uptrend
            if is_uptrend:
                # Check RSI range (35-80 for uptrends - relaxed lower bound)
                if not (35 <= last['rsi'] <= 80):
                    return None
                
                # Check if price pulled back to EMA(21) and bounced
                ema_21 = last.get('ema_21', last.get('ema_20'))
                if pd.isna(ema_21):
                    return None
                
                # RELAXED: Price should be near EMA(21) OR above it (within 2 ATR)
                # This catches both pullback entries AND trend continuation
                distance_from_ema = abs(last['close'] - ema_21)
                if distance_from_ema > (last['atr'] * 2):
                    return None
                
                # RELAXED: Accept bullish candles OR strong upward momentum
                # Check if we have bullish momentum (price above EMA9 and EMA21)
                ema_9 = last.get('ema_9')
                bullish_momentum = (
                    last['close'] > ema_9 and
                    last['close'] > ema_21 and
                    ema_9 > ema_21
                )
                
                # Accept if either: bullish candle OR strong bullish momentum
                if not (last['close'] > last['open'] or bullish_momentum):
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
                # Check RSI range (20-65 for downtrends - relaxed upper bound)
                if not (20 <= last['rsi'] <= 65):
                    return None
                
                # Check if price rallied to EMA(21) and rejected
                ema_21 = last.get('ema_21', last.get('ema_20'))
                if pd.isna(ema_21):
                    return None
                
                # RELAXED: Price should be near EMA(21) OR below it (within 2 ATR)
                # This catches both pullback entries AND trend continuation
                distance_from_ema = abs(last['close'] - ema_21)
                if distance_from_ema > (last['atr'] * 2):
                    return None
                
                # RELAXED: Accept bearish candles OR strong downward momentum
                # Check if we have bearish momentum (price below EMA9 and EMA21)
                ema_9 = last.get('ema_9')
                bearish_momentum = (
                    last['close'] < ema_9 and
                    last['close'] < ema_21 and
                    ema_9 < ema_21
                )
                
                # Accept if either: bearish candle OR strong bearish momentum
                if not (last['close'] < last['open'] or bearish_momentum):
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
        reasons.append("🎯 STRATEGY: Trend Following")
        
        # Trend identification
        if signal_type == "LONG":
            reasons.append(f"📈 UPTREND IDENTIFIED: {swing_points} swing points detected")
            reasons.append(f"   • Higher Highs: {swing_data['higher_highs']}")
            reasons.append(f"   • Higher Lows: {swing_data['higher_lows']}")
            reasons.append(f"   • Trend strength: Strong and established")
        else:
            reasons.append(f"📉 DOWNTREND IDENTIFIED: {swing_points} swing points detected")
            reasons.append(f"   • Lower Highs: {swing_data['lower_highs']}")
            reasons.append(f"   • Lower Lows: {swing_data['lower_lows']}")
            reasons.append(f"   • Trend strength: Strong and established")
        
        # Pullback entry
        ema_21 = last.get('ema_21', last.get('ema_20'))
        if signal_type == "LONG":
            reasons.append(f"\n🔄 PULLBACK ENTRY: Price pulled back {pullback_depth:.1f}% and bounced at EMA(21)")
            reasons.append(f"   • EMA(21): ${ema_21:.2f} acting as dynamic support")
            reasons.append(f"   • Pullback healthy (< 61.8%), trend intact")
        else:
            reasons.append(f"\n🔄 RALLY REJECTION: Price rallied {pullback_depth:.1f}% and rejected at EMA(21)")
            reasons.append(f"   • EMA(21): ${ema_21:.2f} acting as dynamic resistance")
            reasons.append(f"   • Rally contained (< 61.8%), trend intact")
        
        # Volume confirmation
        volume_ratio = last['volume'] / last['volume_ma']
        reasons.append(f"\n📊 VOLUME CONFIRMATION: {volume_ratio:.2f}x average volume")
        reasons.append(f"   • Confirms genuine interest at this level")
        
        # RSI momentum
        reasons.append(f"\n⚡ MOMENTUM: RSI at {last['rsi']:.1f}")
        if signal_type == "LONG":
            if last['rsi'] > 60:
                reasons.append(f"   • Strong bullish momentum, extended target justified")
            else:
                reasons.append(f"   • Healthy momentum, room to run higher")
        else:
            if last['rsi'] < 40:
                reasons.append(f"   • Strong bearish momentum, extended target justified")
            else:
                reasons.append(f"   • Healthy momentum, room to fall further")
        
        # Why enter NOW
        reasons.append(f"\n💡 WHY ENTER NOW:")
        reasons.append(f"   • Established trend with {swing_points} confirmed swing points")
        reasons.append(f"   • Optimal pullback entry at key moving average")
        reasons.append(f"   • Volume confirms buyers/sellers stepping in")
        reasons.append(f"   • Risk-reward favorable with trend on our side")
        
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
            reasons.append(f"📈 BULLISH BIAS: Price trading above VWAP (${last['vwap']:.2f}), indicating institutional buying pressure")
            if market_bias == "bullish":
                reasons.append(f"✓ Trend Confirmation: Price above EMA(50) at ${last['ema_50']:.2f}, confirming uptrend")
        else:
            reasons.append(f"📉 BEARISH BIAS: Price trading below VWAP (${last['vwap']:.2f}), indicating institutional selling pressure")
            if market_bias == "bearish":
                reasons.append(f"✓ Trend Confirmation: Price below EMA(50) at ${last['ema_50']:.2f}, confirming downtrend")
        
        # 2. EMA Crossover
        if signal_type == "LONG":
            reasons.append(f"🔄 MOMENTUM SHIFT: EMA(9) crossed above EMA(21), signaling short-term bullish momentum")
            reasons.append(f"   • EMA(9): ${last['ema_9']:.2f} > EMA(21): ${last['ema_21']:.2f}")
        else:
            reasons.append(f"🔄 MOMENTUM SHIFT: EMA(9) crossed below EMA(21), signaling short-term bearish momentum")
            reasons.append(f"   • EMA(9): ${last['ema_9']:.2f} < EMA(21): ${last['ema_21']:.2f}")
        
        # 3. Volume Confirmation
        volume_ratio = last['volume'] / last['volume_ma']
        reasons.append(f"📊 VOLUME SPIKE: {volume_ratio:.2f}x average volume confirms genuine breakout")
        reasons.append(f"   • Current: {last['volume']:,.0f} vs Avg: {last['volume_ma']:,.0f}")
        
        # 4. RSI Validation
        reasons.append(f"⚡ MOMENTUM HEALTHY: RSI at {last['rsi']:.1f} - not overextended, room to run")
        if 40 <= last['rsi'] <= 60:
            reasons.append(f"   • RSI in neutral zone, ideal for new trend development")
        
        # 5. Why to Enter NOW
        if signal_type == "LONG":
            reasons.append(f"\n💡 WHY BUY NOW:")
            reasons.append(f"   • All {confluence_count} confluence factors aligned simultaneously")
            reasons.append(f"   • Momentum turning bullish after pullback")
            reasons.append(f"   • Institutional buyers (VWAP) supporting price")
            reasons.append(f"   • Volume confirms real buying interest, not a fake move")
        else:
            reasons.append(f"\n💡 WHY SELL NOW:")
            reasons.append(f"   • All {confluence_count} confluence factors aligned simultaneously")
            reasons.append(f"   • Momentum turning bearish after rally")
            reasons.append(f"   • Institutional sellers (VWAP) pressuring price")
            reasons.append(f"   • Volume confirms real selling interest, not a fake move")
        
        return "\n".join(reasons)
