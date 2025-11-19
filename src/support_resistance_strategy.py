"""
Support/Resistance Trading Strategy
Identifies trading signals when price bounces from key support and resistance levels.
"""
import logging
from typing import Optional, List
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class SupportResistanceStrategy:
    """Support/Resistance strategy implementation"""
    
    def __init__(self, config: dict = None):
        """
        Initialize Support/Resistance strategy.
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.lookback_candles = self.config.get('lookback_candles', 100)
        self.min_touches = self.config.get('min_touches', 2)
        self.level_tolerance_percent = self.config.get('level_tolerance_percent', 0.3)
        self.volume_threshold = self.config.get('volume_threshold', 1.4)
        self.require_reversal_candle = self.config.get('require_reversal_candle', True)
    
    def detect_signal(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str
    ) -> Optional[any]:
        """
        Detect Support/Resistance signals.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if len(data) < self.lookback_candles:
                logger.debug(f"Insufficient data for S/R ({len(data)} < {self.lookback_candles})")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['high', 'low', 'close', 'volume', 'volume_ma', 'atr', 'rsi']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"Missing required indicators for S/R strategy")
                return None
            
            # Check for NaN values
            if pd.isna(last['high']) or pd.isna(last['low']) or pd.isna(last['close']):
                logger.warning(f"NaN values in price data, skipping S/R")
                return None
            
            # Identify support and resistance levels
            support_levels, resistance_levels = self._identify_levels(data)
            
            if not support_levels and not resistance_levels:
                logger.debug("No support/resistance levels identified")
                return None
            
            current_price = last['close']
            tolerance = current_price * (self.level_tolerance_percent / 100)
            
            # Check if price is near any S/R level
            nearest_level = None
            nearest_level_type = None
            nearest_distance = float('inf')
            
            # Check support levels
            for level in support_levels:
                distance = abs(current_price - level)
                if distance < tolerance and distance < nearest_distance:
                    nearest_level = level
                    nearest_level_type = 'support'
                    nearest_distance = distance
            
            # Check resistance levels
            for level in resistance_levels:
                distance = abs(current_price - level)
                if distance < tolerance and distance < nearest_distance:
                    nearest_level = level
                    nearest_level_type = 'resistance'
                    nearest_distance = distance
            
            if nearest_level is None:
                logger.debug(f"Price not near any S/R level (tolerance: {tolerance:.2f})")
                return None
            
            logger.debug(f"Price near {nearest_level_type} level: {nearest_level:.2f}")
            
            # Check for reversal candle pattern
            if self.require_reversal_candle:
                is_pin_bar = self._is_pin_bar(last, prev)
                is_engulfing = self._is_engulfing(last, prev)
                is_doji = self._is_doji(last)
                
                if not (is_pin_bar or is_engulfing or is_doji):
                    logger.debug(f"No reversal candle pattern at S/R level")
                    return None
                
                pattern_name = "pin bar" if is_pin_bar else ("engulfing" if is_engulfing else "doji")
                logger.debug(f"Reversal pattern detected: {pattern_name}")
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < self.volume_threshold:
                logger.debug(f"Volume too low: {volume_ratio:.2f}x (need >= {self.volume_threshold}x)")
                return None
            
            # Determine signal direction based on level type
            if nearest_level_type == 'support':
                # Price bouncing from support, expect move up (LONG)
                signal_type = "LONG"
                entry = current_price
                stop_loss = entry - (last['atr'] * 1.0)
                take_profit = entry + (last['atr'] * 2.0)
            else:
                # Price bouncing from resistance, expect move down (SHORT)
                signal_type = "SHORT"
                entry = current_price
                stop_loss = entry + (last['atr'] * 1.0)
                take_profit = entry - (last['atr'] * 2.0)
            
            # Calculate risk/reward
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            risk_reward = reward / risk if risk > 0 else 0
            
            # Validate minimum risk/reward
            if risk_reward < 1.2:
                logger.debug(f"Risk/reward too low: {risk_reward:.2f} (need >= 1.2)")
                return None
            
            logger.info(f"S/R signal detected: {signal_type} at {nearest_level_type} {nearest_level:.2f}")
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
                    'sr_level': nearest_level,
                    'sr_type': nearest_level_type,
                    'rsi': last.get('rsi', 50),
                    'volume': last['volume'],
                    'volume_ma': last['volume_ma']
                },
                reasoning=f"Support/Resistance: Price bouncing from {nearest_level_type} at {nearest_level:.2f}, reversal pattern, Volume {volume_ratio:.2f}x",
                strategy="Support/Resistance Bounce"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in S/R strategy: {e}", exc_info=True)
            return None
    
    def _identify_levels(self, data: pd.DataFrame) -> tuple:
        """
        Identify support and resistance levels.
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            Tuple of (support_levels, resistance_levels) lists
        """
        try:
            recent = data.tail(self.lookback_candles)
            
            # Find local highs and lows
            highs = []
            lows = []
            
            for i in range(1, len(recent) - 1):
                # Local high
                if recent.iloc[i]['high'] > recent.iloc[i-1]['high'] and \
                   recent.iloc[i]['high'] > recent.iloc[i+1]['high']:
                    highs.append(recent.iloc[i]['high'])
                
                # Local low
                if recent.iloc[i]['low'] < recent.iloc[i-1]['low'] and \
                   recent.iloc[i]['low'] < recent.iloc[i+1]['low']:
                    lows.append(recent.iloc[i]['low'])
            
            # Group nearby levels using tolerance
            support_levels = self._group_levels(lows, self.level_tolerance_percent)
            resistance_levels = self._group_levels(highs, self.level_tolerance_percent)
            
            # Filter by minimum touches
            support_levels = [level for level in support_levels if self._count_touches(data, level, 'support') >= self.min_touches]
            resistance_levels = [level for level in resistance_levels if self._count_touches(data, level, 'resistance') >= self.min_touches]
            
            logger.debug(f"Identified {len(support_levels)} support and {len(resistance_levels)} resistance levels")
            
            return support_levels, resistance_levels
            
        except Exception as e:
            logger.error(f"Error identifying S/R levels: {e}")
            return [], []
    
    @staticmethod
    def _group_levels(levels: List[float], tolerance_pct: float) -> List[float]:
        """
        Group nearby levels using tolerance.
        
        Args:
            levels: List of price levels
            tolerance_pct: Tolerance percentage
            
        Returns:
            List of grouped levels
        """
        if not levels:
            return []
        
        levels = sorted(levels)
        grouped = []
        current_group = [levels[0]]
        
        for level in levels[1:]:
            # Check if within tolerance of current group average
            group_avg = sum(current_group) / len(current_group)
            tolerance = group_avg * (tolerance_pct / 100)
            
            if abs(level - group_avg) <= tolerance:
                current_group.append(level)
            else:
                # Start new group
                grouped.append(sum(current_group) / len(current_group))
                current_group = [level]
        
        # Add last group
        if current_group:
            grouped.append(sum(current_group) / len(current_group))
        
        return grouped
    
    @staticmethod
    def _count_touches(data: pd.DataFrame, level: float, level_type: str, tolerance_pct: float = 0.3) -> int:
        """
        Count how many times price touched a level.
        
        Args:
            data: DataFrame with OHLC data
            level: Price level
            level_type: 'support' or 'resistance'
            tolerance_pct: Tolerance percentage
            
        Returns:
            Number of touches
        """
        try:
            tolerance = level * (tolerance_pct / 100)
            touches = 0
            
            for _, row in data.iterrows():
                if level_type == 'support':
                    # Check if low touched the level
                    if abs(row['low'] - level) <= tolerance:
                        touches += 1
                else:  # resistance
                    # Check if high touched the level
                    if abs(row['high'] - level) <= tolerance:
                        touches += 1
            
            return touches
            
        except Exception as e:
            logger.debug(f"Error counting touches: {e}")
            return 0
    
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
            body = abs(last['close'] - last['open'])
            wick_up = last['high'] - max(last['open'], last['close'])
            wick_down = min(last['open'], last['close']) - last['low']
            total_range = last['high'] - last['low']
            
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
            bullish = last['close'] > prev['open'] and last['open'] < prev['close']
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
            
            if total_range > 0:
                body_ratio = body / total_range
                return body_ratio < 0.1
            
            return False
            
        except Exception as e:
            logger.debug(f"Error detecting doji: {e}")
            return False

