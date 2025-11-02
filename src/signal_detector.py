"""Signal detection with confluence-based trading logic."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Dict
import pandas as pd
import logging


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
        
        # Check for bullish signal
        bullish_signal = self._check_bullish_confluence(data, timeframe)
        if bullish_signal and not self._is_duplicate_signal(bullish_signal):
            self.signal_history.append(bullish_signal)
            logger.info(f"LONG signal detected on {timeframe}: {bullish_signal.entry_price}")
            return bullish_signal
        
        # Check for bearish signal
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
