"""
Fibonacci Retracement Trading Strategy
Identifies trading signals at Fibonacci retracement levels with reversal confirmation.
"""
import logging
from typing import Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class FibonacciStrategy:
    """Fibonacci retracement strategy implementation"""
    
    # Fibonacci levels
    FIBONACCI_LEVELS = {
        'level_236': 0.236,
        'level_382': 0.382,
        'level_500': 0.500,
        'level_618': 0.618,
        'level_786': 0.786
    }
    
    def __init__(self, config: dict = None):
        """
        Initialize Fibonacci strategy.
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.swing_lookback = self.config.get('swing_lookback', 50)
        self.level_tolerance_percent = self.config.get('level_tolerance_percent', 0.5)
        self.volume_threshold = self.config.get('volume_threshold', 1.3)
        self.require_reversal_candle = self.config.get('require_reversal_candle', True)
    
    def detect_signal(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str
    ) -> Optional[any]:
        """
        Detect Fibonacci retracement signals.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if len(data) < self.swing_lookback:
                logger.debug(f"Insufficient data for Fibonacci ({len(data)} < {self.swing_lookback})")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['high', 'low', 'close', 'volume', 'volume_ma', 'atr', 'rsi']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"Missing required indicators for Fibonacci strategy")
                return None
            
            # Check for NaN values
            if pd.isna(last['high']) or pd.isna(last['low']) or pd.isna(last['close']):
                logger.warning(f"NaN values in price data, skipping Fibonacci")
                return None
            
            # Calculate Fibonacci levels
            recent = data.tail(self.swing_lookback)
            swing_high = recent['high'].max()
            swing_low = recent['low'].min()
            
            if swing_high == swing_low:
                logger.debug("Swing high equals swing low, cannot calculate Fibonacci levels")
                return None
            
            # Calculate Fibonacci levels
            diff = swing_high - swing_low
            fib_levels = {
                'level_236': swing_high - (diff * 0.236),
                'level_382': swing_high - (diff * 0.382),
                'level_500': swing_high - (diff * 0.500),
                'level_618': swing_high - (diff * 0.618),
                'level_786': swing_high - (diff * 0.786)
            }
            
            current_price = last['close']
            tolerance = current_price * (self.level_tolerance_percent / 100)
            
            # Check if price is near any Fibonacci level
            nearest_level = None
            nearest_level_name = None
            nearest_distance = float('inf')
            
            for level_name, level_price in fib_levels.items():
                distance = abs(current_price - level_price)
                if distance < tolerance and distance < nearest_distance:
                    nearest_level = level_price
                    nearest_level_name = level_name
                    nearest_distance = distance
            
            if nearest_level is None:
                logger.debug(f"Price not near any Fibonacci level (tolerance: {tolerance:.2f})")
                return None
            
            logger.debug(f"Price near Fibonacci level {nearest_level_name}: {nearest_level:.2f}")
            
            # Check for reversal candle pattern
            if self.require_reversal_candle:
                is_pin_bar = self._is_pin_bar(last, prev)
                is_engulfing = self._is_engulfing(last, prev)
                is_doji = self._is_doji(last)
                
                if not (is_pin_bar or is_engulfing or is_doji):
                    logger.debug(f"No reversal candle pattern at Fibonacci level")
                    return None
                
                pattern_name = "pin bar" if is_pin_bar else ("engulfing" if is_engulfing else "doji")
                logger.debug(f"Reversal pattern detected: {pattern_name}")
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < self.volume_threshold:
                logger.debug(f"Volume too low: {volume_ratio:.2f}x (need >= {self.volume_threshold}x)")
                return None
            
            # Determine signal direction based on price position relative to Fibonacci level
            if current_price < nearest_level:
                # Price below Fibonacci level, expect bounce up (LONG)
                signal_type = "LONG"
                entry = current_price
                stop_loss = entry - (last['atr'] * 1.0)
                take_profit = nearest_level
            else:
                # Price above Fibonacci level, expect bounce down (SHORT)
                signal_type = "SHORT"
                entry = current_price
                stop_loss = entry + (last['atr'] * 1.0)
                take_profit = nearest_level
            
            # Calculate risk/reward
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            risk_reward = reward / risk if risk > 0 else 0
            
            # Validate minimum risk/reward
            if risk_reward < 1.2:
                logger.debug(f"Risk/reward too low: {risk_reward:.2f} (need >= 1.2)")
                return None
            
            logger.info(f"Fibonacci signal detected: {signal_type} at {nearest_level_name}")
            logger.info(f"Entry: {entry:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}, R:R: {risk_reward:.2f}")
            
            # Create signal object
            from src.signal_detector import Signal
            from src.symbol_context import SymbolContext
            
            try:
                symbol_context = SymbolContext.from_symbol(symbol if symbol in ['BTC', 'XAUUSD', 'US30', 'US100'] else 'BTC')
            except:
                symbol_context = None
            
            signal = Signal(
                timestamp=last['timestamp'],
                signal_type=signal_type,
                timeframe=timeframe,
                symbol=symbol,
                symbol_context=symbol_context,
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                atr=last['atr'],
                risk_reward=risk_reward,
                market_bias="neutral",
                confidence=4,
                indicators={
                    'fib_level': nearest_level,
                    'fib_level_name': nearest_level_name,
                    'swing_high': swing_high,
                    'swing_low': swing_low,
                    'rsi': last.get('rsi', 50),
                    'volume': last['volume'],
                    'volume_ma': last['volume_ma']
                },
                reasoning=f"Fibonacci Retracement: Price at {nearest_level_name} ({nearest_level:.2f}), reversal pattern, Volume {volume_ratio:.2f}x",
                strategy="Fibonacci Retracement"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in Fibonacci strategy: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _is_pin_bar(last: pd.Series, prev: pd.Series) -> bool:
        """
        Detect pin bar pattern (long wick, small body).
        
        Args:
            last: Current candle
            prev: Previous candle
            
        Returns:
            True if pin bar detected
        """
        try:
            # Pin bar has long wick and small body
            body = abs(last['close'] - last['open'])
            wick_up = last['high'] - max(last['open'], last['close'])
            wick_down = min(last['open'], last['close']) - last['low']
            total_range = last['high'] - last['low']
            
            # Pin bar: wick is at least 2x the body
            if total_range > 0:
                wick_ratio = max(wick_up, wick_down) / total_range
                body_ratio = body / total_range
                
                return wick_ratio > 0.6 and body_ratio < 0.3
            
            return False
            
        except Exception as e:
            logger.debug(f"Error detecting pin bar: {e}")
            return False
    
    @staticmethod
    def _is_engulfing(last: pd.Series, prev: pd.Series) -> bool:
        """
        Detect engulfing pattern.
        
        Args:
            last: Current candle
            prev: Previous candle
            
        Returns:
            True if engulfing pattern detected
        """
        try:
            # Bullish engulfing: current close > prev open and current open < prev close
            bullish = last['close'] > prev['open'] and last['open'] < prev['close']
            
            # Bearish engulfing: current close < prev open and current open > prev close
            bearish = last['close'] < prev['open'] and last['open'] > prev['close']
            
            return bullish or bearish
            
        except Exception as e:
            logger.debug(f"Error detecting engulfing: {e}")
            return False
    
    @staticmethod
    def _is_doji(last: pd.Series) -> bool:
        """
        Detect doji pattern (open ≈ close).
        
        Args:
            last: Current candle
            
        Returns:
            True if doji pattern detected
        """
        try:
            body = abs(last['close'] - last['open'])
            total_range = last['high'] - last['low']
            
            # Doji: body is very small (< 10% of range)
            if total_range > 0:
                body_ratio = body / total_range
                return body_ratio < 0.1
            
            return False
            
        except Exception as e:
            logger.debug(f"Error detecting doji: {e}")
            return False

