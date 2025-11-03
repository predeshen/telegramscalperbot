"""
Trend Analyzer Module
Analyzes price data to identify trends, swing points, and pullback patterns.
"""
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyzes price data to identify trends and trading opportunities.
    
    This class provides static methods for:
    - Detecting swing highs and swing lows
    - Identifying uptrends and downtrends
    - Calculating pullback depth
    - Verifying EMA alignment with trends
    """
    
    @staticmethod
    def detect_swing_points(data: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        Detect swing highs and swing lows in price data.
        
        A swing high is a peak where the high is higher than the highs
        of 'lookback' candles before and after it.
        
        A swing low is a trough where the low is lower than the lows
        of 'lookback' candles before and after it.
        
        Args:
            data: DataFrame with 'high', 'low', 'close' columns
            lookback: Number of candles to look before/after for swing detection
            
        Returns:
            Dictionary containing:
                - swing_highs: List of (index, price) tuples
                - swing_lows: List of (index, price) tuples
                - higher_highs: Count of higher highs
                - higher_lows: Count of higher lows
                - lower_highs: Count of lower highs
                - lower_lows: Count of lower lows
        """
        if data.empty or len(data) < (lookback * 2 + 1):
            return {
                'swing_highs': [],
                'swing_lows': [],
                'higher_highs': 0,
                'higher_lows': 0,
                'lower_highs': 0,
                'lower_lows': 0
            }
        
        swing_highs = []
        swing_lows = []
        
        # Detect swing points
        for i in range(lookback, len(data) - lookback):
            # Check for swing high
            current_high = data.iloc[i]['high']
            is_swing_high = True
            
            for j in range(i - lookback, i + lookback + 1):
                if j != i and data.iloc[j]['high'] >= current_high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append((i, current_high))
            
            # Check for swing low
            current_low = data.iloc[i]['low']
            is_swing_low = True
            
            for j in range(i - lookback, i + lookback + 1):
                if j != i and data.iloc[j]['low'] <= current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append((i, current_low))
        
        # Count higher highs, higher lows, lower highs, lower lows
        higher_highs = 0
        lower_highs = 0
        for i in range(1, len(swing_highs)):
            if swing_highs[i][1] > swing_highs[i-1][1]:
                higher_highs += 1
            elif swing_highs[i][1] < swing_highs[i-1][1]:
                lower_highs += 1
        
        higher_lows = 0
        lower_lows = 0
        for i in range(1, len(swing_lows)):
            if swing_lows[i][1] > swing_lows[i-1][1]:
                higher_lows += 1
            elif swing_lows[i][1] < swing_lows[i-1][1]:
                lower_lows += 1
        
        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'higher_highs': higher_highs,
            'higher_lows': higher_lows,
            'lower_highs': lower_highs,
            'lower_lows': lower_lows
        }
    
    @staticmethod
    def is_uptrend(swing_data: Dict, min_swings: int = 3) -> bool:
        """
        Check if swing data indicates an uptrend.
        
        An uptrend is characterized by:
        - At least min_swings higher highs
        - At least min_swings higher lows
        
        Args:
            swing_data: Dictionary from detect_swing_points()
            min_swings: Minimum number of swing points required
            
        Returns:
            True if uptrend detected, False otherwise
        """
        higher_highs = swing_data.get('higher_highs', 0)
        higher_lows = swing_data.get('higher_lows', 0)
        
        return higher_highs >= min_swings and higher_lows >= min_swings
    
    @staticmethod
    def is_downtrend(swing_data: Dict, min_swings: int = 3) -> bool:
        """
        Check if swing data indicates a downtrend.
        
        A downtrend is characterized by:
        - At least min_swings lower highs
        - At least min_swings lower lows
        
        Args:
            swing_data: Dictionary from detect_swing_points()
            min_swings: Minimum number of swing points required
            
        Returns:
            True if downtrend detected, False otherwise
        """
        lower_highs = swing_data.get('lower_highs', 0)
        lower_lows = swing_data.get('lower_lows', 0)
        
        return lower_highs >= min_swings and lower_lows >= min_swings
    
    @staticmethod
    def calculate_pullback_depth(data: pd.DataFrame, trend_direction: str) -> float:
        """
        Calculate pullback depth as percentage of previous trend leg.
        
        For uptrends: measures how much price pulled back from recent high
        For downtrends: measures how much price rallied from recent low
        
        Args:
            data: DataFrame with 'high', 'low', 'close' columns
            trend_direction: "uptrend" or "downtrend"
            
        Returns:
            Pullback depth as percentage (0-100)
        """
        if data.empty or len(data) < 20:
            return 0.0
        
        recent_data = data.tail(20)
        
        if trend_direction == "uptrend":
            # Find recent high and current pullback low
            recent_high = recent_data['high'].max()
            recent_low = recent_data['low'].min()
            current_price = data.iloc[-1]['close']
            
            # Find the swing low before the recent high
            high_idx = recent_data['high'].idxmax()
            data_before_high = recent_data.loc[:high_idx]
            
            if len(data_before_high) > 0:
                swing_low = data_before_high['low'].min()
                trend_leg = recent_high - swing_low
                
                if trend_leg > 0:
                    pullback = recent_high - current_price
                    pullback_percent = (pullback / trend_leg) * 100
                    return max(0.0, min(100.0, pullback_percent))
        
        elif trend_direction == "downtrend":
            # Find recent low and current rally high
            recent_low = recent_data['low'].min()
            recent_high = recent_data['high'].max()
            current_price = data.iloc[-1]['close']
            
            # Find the swing high before the recent low
            low_idx = recent_data['low'].idxmin()
            data_before_low = recent_data.loc[:low_idx]
            
            if len(data_before_low) > 0:
                swing_high = data_before_low['high'].max()
                trend_leg = swing_high - recent_low
                
                if trend_leg > 0:
                    rally = current_price - recent_low
                    rally_percent = (rally / trend_leg) * 100
                    return max(0.0, min(100.0, rally_percent))
        
        return 0.0
    
    @staticmethod
    def is_ema_aligned(data: pd.DataFrame, trend_direction: str) -> bool:
        """
        Check if EMAs are aligned with trend direction.
        
        For uptrends: EMA(21) > EMA(50) and both rising
        For downtrends: EMA(21) < EMA(50) and both falling
        
        Args:
            data: DataFrame with 'ema_21', 'ema_50' columns
            trend_direction: "uptrend" or "downtrend"
            
        Returns:
            True if EMAs aligned with trend, False otherwise
        """
        if data.empty or len(data) < 5:
            return False
        
        # Check if required EMAs exist
        if 'ema_21' not in data.columns or 'ema_50' not in data.columns:
            # Try alternative names
            if 'ema_20' in data.columns:
                ema_fast = 'ema_20'
            else:
                return False
            ema_slow = 'ema_50'
        else:
            ema_fast = 'ema_21'
            ema_slow = 'ema_50'
        
        last = data.iloc[-1]
        prev = data.iloc[-2]
        
        # Check EMA values exist and are not NaN
        if pd.isna(last[ema_fast]) or pd.isna(last[ema_slow]):
            return False
        if pd.isna(prev[ema_fast]) or pd.isna(prev[ema_slow]):
            return False
        
        if trend_direction == "uptrend":
            # EMA(21) should be above EMA(50)
            ema_order = last[ema_fast] > last[ema_slow]
            
            # Both EMAs should be rising
            ema_fast_rising = last[ema_fast] > prev[ema_fast]
            ema_slow_rising = last[ema_slow] > prev[ema_slow]
            
            return ema_order and ema_fast_rising and ema_slow_rising
        
        elif trend_direction == "downtrend":
            # EMA(21) should be below EMA(50)
            ema_order = last[ema_fast] < last[ema_slow]
            
            # Both EMAs should be falling
            ema_fast_falling = last[ema_fast] < prev[ema_fast]
            ema_slow_falling = last[ema_slow] < prev[ema_slow]
            
            return ema_order and ema_fast_falling and ema_slow_falling
        
        return False
    
    @staticmethod
    def get_trend_strength(swing_data: Dict) -> str:
        """
        Determine trend strength based on swing point counts.
        
        Args:
            swing_data: Dictionary from detect_swing_points()
            
        Returns:
            "strong", "moderate", "weak", or "none"
        """
        if TrendAnalyzer.is_uptrend(swing_data, min_swings=5):
            return "strong"
        elif TrendAnalyzer.is_uptrend(swing_data, min_swings=3):
            return "moderate"
        elif TrendAnalyzer.is_downtrend(swing_data, min_swings=5):
            return "strong"
        elif TrendAnalyzer.is_downtrend(swing_data, min_swings=3):
            return "moderate"
        else:
            return "weak"
    
    @staticmethod
    def is_consolidating(data: pd.DataFrame, periods: int = 3) -> bool:
        """
        Check if market is consolidating (ATR declining).
        
        Args:
            data: DataFrame with 'atr' column
            periods: Number of periods to check
            
        Returns:
            True if ATR declining for specified periods
        """
        if data.empty or len(data) < periods + 1:
            return False
        
        if 'atr' not in data.columns:
            return False
        
        recent_atr = data['atr'].tail(periods + 1)
        
        # Check if ATR is declining
        for i in range(len(recent_atr) - 1):
            if pd.isna(recent_atr.iloc[i]) or pd.isna(recent_atr.iloc[i + 1]):
                return False
            if recent_atr.iloc[i + 1] >= recent_atr.iloc[i]:
                return False
        
        return True
