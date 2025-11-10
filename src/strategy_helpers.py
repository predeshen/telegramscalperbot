"""Strategy helper classes and utilities for unified strategy framework."""

from dataclasses import dataclass
from typing import Optional, List, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketConditions:
    """Market condition analysis result."""
    trend_strength: float  # ADX value
    volatility: float      # ATR ratio vs average
    is_trending: bool      # ADX > 20
    is_ranging: bool       # ADX < 20
    momentum: str          # "bullish", "bearish", "neutral"
    volume_profile: str    # "high", "normal", "low"


@dataclass
class FibonacciLevels:
    """Fibonacci retracement levels."""
    swing_high: float
    swing_low: float
    level_236: float  # 23.6%
    level_382: float  # 38.2%
    level_500: float  # 50%
    level_618: float  # 61.8%
    level_786: float  # 78.6%
    direction: str    # "retracement_up" or "retracement_down"
    swing_size: float  # Absolute size of the swing


@dataclass
class SupportResistanceLevel:
    """Support or resistance level."""
    price: float
    level_type: str    # "support" or "resistance"
    touches: int       # Number of times price touched this level
    strength: float    # 0-1 score based on touches and recency
    is_round_number: bool
    last_touch_candles_ago: int


class FibonacciCalculator:
    """Calculate Fibonacci retracement levels."""
    
    @staticmethod
    def find_swing(data: pd.DataFrame, lookback: int = 50) -> Optional[Tuple[float, float, str]]:
        """
        Find most significant swing in recent data.
        
        Args:
            data: DataFrame with OHLCV data
            lookback: Number of candles to look back
            
        Returns:
            Tuple of (swing_high, swing_low, direction) or None if no significant swing
        """
        try:
            if len(data) < lookback:
                lookback = len(data)
            
            recent_data = data.iloc[-lookback:]
            
            # Find highest high and lowest low
            swing_high = recent_data['high'].max()
            swing_low = recent_data['low'].min()
            
            # Find indices
            high_idx = recent_data['high'].idxmax()
            low_idx = recent_data['low'].idxmin()
            
            # Determine direction based on which came first
            if high_idx < low_idx:
                # High came before low - retracement down (bearish swing)
                direction = "retracement_down"
            else:
                # Low came before high - retracement up (bullish swing)
                direction = "retracement_up"
            
            # Calculate swing size
            swing_size = abs(swing_high - swing_low)
            
            # Check if swing is significant (at least 1% move)
            if swing_size / swing_low < 0.01:
                logger.debug(f"Swing too small: {swing_size} ({swing_size/swing_low*100:.2f}%)")
                return None
            
            logger.debug(f"Found swing: {direction}, high={swing_high:.2f}, low={swing_low:.2f}, size={swing_size:.2f}")
            return (swing_high, swing_low, direction)
            
        except Exception as e:
            logger.error(f"Error finding swing: {e}")
            return None
    
    @staticmethod
    def calculate_levels(swing_high: float, swing_low: float, direction: str) -> FibonacciLevels:
        """
        Calculate Fibonacci levels from swing.
        
        Args:
            swing_high: Highest point of swing
            swing_low: Lowest point of swing
            direction: "retracement_up" or "retracement_down"
            
        Returns:
            FibonacciLevels object with all levels
        """
        swing_size = swing_high - swing_low
        
        # Calculate retracement levels
        level_236 = swing_low + (swing_size * 0.236)
        level_382 = swing_low + (swing_size * 0.382)
        level_500 = swing_low + (swing_size * 0.500)
        level_618 = swing_low + (swing_size * 0.618)
        level_786 = swing_low + (swing_size * 0.786)
        
        return FibonacciLevels(
            swing_high=swing_high,
            swing_low=swing_low,
            level_236=level_236,
            level_382=level_382,
            level_500=level_500,
            level_618=level_618,
            level_786=level_786,
            direction=direction,
            swing_size=swing_size
        )
    
    @staticmethod
    def is_near_level(price: float, level: float, tolerance_percent: float = 0.5) -> bool:
        """
        Check if price is near a Fibonacci level.
        
        Args:
            price: Current price
            level: Fibonacci level price
            tolerance_percent: Tolerance as percentage (default 0.5%)
            
        Returns:
            True if price is within tolerance of level
        """
        tolerance = level * (tolerance_percent / 100)
        return abs(price - level) <= tolerance
    
    @staticmethod
    def get_nearest_level(price: float, fib_levels: FibonacciLevels) -> Optional[Tuple[float, str]]:
        """
        Get nearest Fibonacci level to current price.
        
        Args:
            price: Current price
            fib_levels: FibonacciLevels object
            
        Returns:
            Tuple of (level_price, level_name) or None
        """
        levels = {
            '23.6%': fib_levels.level_236,
            '38.2%': fib_levels.level_382,
            '50%': fib_levels.level_500,
            '61.8%': fib_levels.level_618,
            '78.6%': fib_levels.level_786
        }
        
        nearest_level = None
        nearest_distance = float('inf')
        nearest_name = None
        
        for name, level in levels.items():
            distance = abs(price - level)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_level = level
                nearest_name = name
        
        return (nearest_level, nearest_name) if nearest_level else None


class SupportResistanceFinder:
    """Identify support and resistance levels."""
    
    @staticmethod
    def find_levels(
        data: pd.DataFrame, 
        lookback: int = 100,
        min_touches: int = 2,
        tolerance_percent: float = 0.3
    ) -> List[SupportResistanceLevel]:
        """
        Find support/resistance levels in historical data.
        
        Args:
            data: DataFrame with OHLCV data
            lookback: Number of candles to analyze
            min_touches: Minimum touches required for a valid level
            tolerance_percent: Price tolerance for level clustering
            
        Returns:
            List of SupportResistanceLevel objects
        """
        try:
            if len(data) < lookback:
                lookback = len(data)
            
            recent_data = data.iloc[-lookback:]
            levels = []
            
            # Find potential support levels (local lows)
            support_candidates = SupportResistanceFinder._find_local_extrema(
                recent_data, 'low', window=5
            )
            
            # Find potential resistance levels (local highs)
            resistance_candidates = SupportResistanceFinder._find_local_extrema(
                recent_data, 'high', window=5
            )
            
            # Cluster and validate support levels
            for level_price in support_candidates:
                level = SupportResistanceFinder._validate_level(
                    recent_data, level_price, 'support', tolerance_percent, min_touches
                )
                if level:
                    levels.append(level)
            
            # Cluster and validate resistance levels
            for level_price in resistance_candidates:
                level = SupportResistanceFinder._validate_level(
                    recent_data, level_price, 'resistance', tolerance_percent, min_touches
                )
                if level:
                    levels.append(level)
            
            # Sort by strength (descending)
            levels.sort(key=lambda x: x.strength, reverse=True)
            
            logger.debug(f"Found {len(levels)} support/resistance levels")
            return levels
            
        except Exception as e:
            logger.error(f"Error finding support/resistance levels: {e}")
            return []
    
    @staticmethod
    def _find_local_extrema(data: pd.DataFrame, column: str, window: int = 5) -> List[float]:
        """Find local extrema (highs or lows) in data."""
        extrema = []
        
        for i in range(window, len(data) - window):
            if column == 'low':
                # Check if this is a local minimum
                window_data = data[column].iloc[i-window:i+window+1]
                if data[column].iloc[i] == window_data.min():
                    extrema.append(data[column].iloc[i])
            else:  # 'high'
                # Check if this is a local maximum
                window_data = data[column].iloc[i-window:i+window+1]
                if data[column].iloc[i] == window_data.max():
                    extrema.append(data[column].iloc[i])
        
        return extrema
    
    @staticmethod
    def _validate_level(
        data: pd.DataFrame,
        level_price: float,
        level_type: str,
        tolerance_percent: float,
        min_touches: int
    ) -> Optional[SupportResistanceLevel]:
        """Validate and create a support/resistance level."""
        tolerance = level_price * (tolerance_percent / 100)
        
        # Count touches
        touches = 0
        last_touch_idx = -1
        
        for idx, row in data.iterrows():
            if level_type == 'support':
                # Check if low touched the level
                if abs(row['low'] - level_price) <= tolerance:
                    touches += 1
                    last_touch_idx = idx
            else:  # resistance
                # Check if high touched the level
                if abs(row['high'] - level_price) <= tolerance:
                    touches += 1
                    last_touch_idx = idx
        
        # Require minimum touches
        if touches < min_touches:
            return None
        
        # Calculate strength (0-1 based on touches and recency)
        strength = min(touches / 5.0, 1.0)  # Max out at 5 touches
        
        # Calculate candles since last touch
        last_touch_candles_ago = len(data) - data.index.get_loc(last_touch_idx) - 1
        
        # Check if it's a round number
        is_round = SupportResistanceFinder.is_round_number(level_price, "BTC")
        
        return SupportResistanceLevel(
            price=level_price,
            level_type=level_type,
            touches=touches,
            strength=strength,
            is_round_number=is_round,
            last_touch_candles_ago=last_touch_candles_ago
        )
    
    @staticmethod
    def is_round_number(price: float, asset: str) -> bool:
        """
        Check if price is a round number for the asset.
        
        Args:
            price: Price to check
            asset: Asset type ("BTC", "GOLD", "US30")
            
        Returns:
            True if price is a round number
        """
        if asset.upper() in ["BTC", "BITCOIN"]:
            # Round to nearest 1000 for BTC
            return price % 1000 == 0 or price % 500 == 0
        elif asset.upper() in ["GOLD", "XAU", "XAUUSD"]:
            # Round to nearest 50 or 100 for Gold
            return price % 100 == 0 or price % 50 == 0
        elif asset.upper() in ["US30", "DOW"]:
            # Round to nearest 100 or 500 for US30
            return price % 500 == 0 or price % 100 == 0
        else:
            # Default: check if divisible by 100
            return price % 100 == 0
    
    @staticmethod
    def get_nearest_level(
        price: float, 
        levels: List[SupportResistanceLevel],
        max_distance_percent: float = 0.5
    ) -> Optional[SupportResistanceLevel]:
        """
        Get nearest support/resistance level to current price.
        
        Args:
            price: Current price
            levels: List of SupportResistanceLevel objects
            max_distance_percent: Maximum distance as percentage
            
        Returns:
            Nearest level or None
        """
        if not levels:
            return None
        
        max_distance = price * (max_distance_percent / 100)
        
        nearest_level = None
        nearest_distance = float('inf')
        
        for level in levels:
            distance = abs(price - level.price)
            if distance < nearest_distance and distance <= max_distance:
                nearest_distance = distance
                nearest_level = level
        
        return nearest_level


class KeyLevelTracker:
    """Track and identify key price levels."""
    
    def __init__(self, asset: str):
        """
        Initialize key level tracker.
        
        Args:
            asset: Asset type ("BTC", "GOLD", "US30")
        """
        self.asset = asset.upper()
        self.key_levels = []
        self.previous_highs = []
        self.previous_lows = []
    
    def update_levels(self, data: pd.DataFrame):
        """
        Update key levels from recent data.
        
        Args:
            data: DataFrame with OHLCV data
        """
        try:
            # Update previous highs/lows (last 50 candles)
            lookback = min(50, len(data))
            recent_data = data.iloc[-lookback:]
            
            # Find significant highs and lows
            self.previous_highs = self._find_significant_highs(recent_data)
            self.previous_lows = self._find_significant_lows(recent_data)
            
            # Get current price for round number calculation
            current_price = data.iloc[-1]['close']
            
            # Combine all key levels
            self.key_levels = []
            self.key_levels.extend(self.previous_highs)
            self.key_levels.extend(self.previous_lows)
            self.key_levels.extend(self.get_round_numbers(current_price, range_percent=5.0))
            
            # Remove duplicates (within 0.1% of each other)
            self.key_levels = self._remove_duplicates(self.key_levels)
            
            logger.debug(f"Updated key levels: {len(self.key_levels)} levels tracked")
            
        except Exception as e:
            logger.error(f"Error updating key levels: {e}")
    
    def _find_significant_highs(self, data: pd.DataFrame) -> List[float]:
        """Find significant high points in data."""
        highs = []
        window = 5
        
        for i in range(window, len(data) - window):
            window_data = data['high'].iloc[i-window:i+window+1]
            if data['high'].iloc[i] == window_data.max():
                highs.append(data['high'].iloc[i])
        
        return highs
    
    def _find_significant_lows(self, data: pd.DataFrame) -> List[float]:
        """Find significant low points in data."""
        lows = []
        window = 5
        
        for i in range(window, len(data) - window):
            window_data = data['low'].iloc[i-window:i+window+1]
            if data['low'].iloc[i] == window_data.min():
                lows.append(data['low'].iloc[i])
        
        return lows
    
    def _remove_duplicates(self, levels: List[float], tolerance_percent: float = 0.1) -> List[float]:
        """Remove duplicate levels within tolerance."""
        if not levels:
            return []
        
        unique_levels = []
        sorted_levels = sorted(levels)
        
        for level in sorted_levels:
            is_duplicate = False
            for unique_level in unique_levels:
                if abs(level - unique_level) / unique_level < (tolerance_percent / 100):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_levels.append(level)
        
        return unique_levels
    
    def get_round_numbers(self, current_price: float, range_percent: float = 5.0) -> List[float]:
        """
        Get round numbers near current price.
        
        Args:
            current_price: Current market price
            range_percent: Range around price to search (percentage)
            
        Returns:
            List of round number levels
        """
        round_numbers = []
        price_range = current_price * (range_percent / 100)
        
        if self.asset in ["BTC", "BITCOIN"]:
            # Round to nearest 1000 and 500
            step = 500
            start = int((current_price - price_range) / step) * step
            end = int((current_price + price_range) / step) * step
            
            for price in range(start, end + step, step):
                if price > 0:
                    round_numbers.append(float(price))
        
        elif self.asset in ["GOLD", "XAU", "XAUUSD"]:
            # Round to nearest 100 and 50
            step = 50
            start = int((current_price - price_range) / step) * step
            end = int((current_price + price_range) / step) * step
            
            for price in range(start, end + step, step):
                if price > 0:
                    round_numbers.append(float(price))
        
        elif self.asset in ["US30", "DOW"]:
            # Round to nearest 500 and 100
            step = 100
            start = int((current_price - price_range) / step) * step
            end = int((current_price + price_range) / step) * step
            
            for price in range(start, end + step, step):
                if price > 0:
                    round_numbers.append(float(price))
        
        return round_numbers
    
    def detect_break(self, current_candle: pd.Series, prev_candle: pd.Series) -> Optional[dict]:
        """
        Detect if a key level was broken.
        
        Args:
            current_candle: Current candle data
            prev_candle: Previous candle data
            
        Returns:
            Dict with break info or None
        """
        try:
            for level in self.key_levels:
                # Check for upward break (resistance break)
                if prev_candle['close'] < level <= current_candle['close']:
                    return {
                        'level': level,
                        'direction': 'up',
                        'is_round_number': SupportResistanceFinder.is_round_number(level, self.asset),
                        'break_size': current_candle['close'] - level
                    }
                
                # Check for downward break (support break)
                if prev_candle['close'] > level >= current_candle['close']:
                    return {
                        'level': level,
                        'direction': 'down',
                        'is_round_number': SupportResistanceFinder.is_round_number(level, self.asset),
                        'break_size': level - current_candle['close']
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting level break: {e}")
            return None
    
    def get_nearest_key_level(self, price: float, max_distance_percent: float = 1.0) -> Optional[float]:
        """
        Get nearest key level to current price.
        
        Args:
            price: Current price
            max_distance_percent: Maximum distance as percentage
            
        Returns:
            Nearest key level or None
        """
        if not self.key_levels:
            return None
        
        max_distance = price * (max_distance_percent / 100)
        
        nearest_level = None
        nearest_distance = float('inf')
        
        for level in self.key_levels:
            distance = abs(price - level)
            if distance < nearest_distance and distance <= max_distance:
                nearest_distance = distance
                nearest_level = level
        
        return nearest_level
