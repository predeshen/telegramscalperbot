"""
Smart Stop Loss and Take Profit Calculator
Uses market structure (support/resistance, swing highs/lows) for realistic targets
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class SLTPCalculator:
    """Calculate structure-based stop loss and take profit levels."""
    
    @staticmethod
    def calculate_structure_based_sltp(
        data: pd.DataFrame,
        entry_price: float,
        signal_type: str,  # "LONG" or "SHORT"
        atr: float,
        lookback: int = 50,
        min_rr: float = 1.5,
        max_rr: float = 5.0
    ) -> Tuple[float, float, float]:
        """
        Calculate SL/TP based on market structure.
        
        Args:
            data: DataFrame with OHLCV data
            entry_price: Entry price
            signal_type: "LONG" or "SHORT"
            atr: Current ATR value
            lookback: Candles to look back for structure
            min_rr: Minimum acceptable risk/reward ratio
            max_rr: Maximum risk/reward ratio (cap unrealistic targets)
            
        Returns:
            Tuple of (stop_loss, take_profit, risk_reward)
        """
        if len(data) < lookback:
            lookback = len(data)
        
        recent_data = data.iloc[-lookback:]
        
        if signal_type == "LONG":
            # Find recent swing low for stop loss
            stop_loss = SLTPCalculator._find_swing_low_for_sl(
                recent_data, entry_price, atr
            )
            
            # Find recent swing high or resistance for take profit
            take_profit = SLTPCalculator._find_swing_high_for_tp(
                recent_data, entry_price, atr, stop_loss, min_rr, max_rr
            )
            
        else:  # SHORT
            # Find recent swing high for stop loss
            stop_loss = SLTPCalculator._find_swing_high_for_sl(
                recent_data, entry_price, atr
            )
            
            # Find recent swing low or support for take profit
            take_profit = SLTPCalculator._find_swing_low_for_tp(
                recent_data, entry_price, atr, stop_loss, min_rr, max_rr
            )
        
        # Calculate risk/reward
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        # Validate minimum R:R
        if risk_reward < min_rr:
            logger.debug(f"Adjusting TP to meet minimum R:R of {min_rr}")
            if signal_type == "LONG":
                take_profit = entry_price + (risk * min_rr)
            else:
                take_profit = entry_price - (risk * min_rr)
            risk_reward = min_rr
        
        # Cap maximum R:R (unrealistic targets)
        if risk_reward > max_rr:
            logger.debug(f"Capping TP to maximum R:R of {max_rr}")
            if signal_type == "LONG":
                take_profit = entry_price + (risk * max_rr)
            else:
                take_profit = entry_price - (risk * max_rr)
            risk_reward = max_rr
        
        return stop_loss, take_profit, risk_reward
    
    @staticmethod
    def _find_swing_low_for_sl(
        data: pd.DataFrame,
        entry_price: float,
        atr: float
    ) -> float:
        """Find recent swing low below entry for stop loss."""
        # Look for lowest low in recent data
        lows = data['low'].values
        
        # Find significant swing lows (local minima)
        swing_lows = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])
        
        # Find the nearest swing low below entry
        valid_lows = [low for low in swing_lows if low < entry_price]
        
        if valid_lows:
            # Use the highest swing low below entry (closest support)
            stop_loss = max(valid_lows) - (atr * 0.3)  # Small buffer below swing low
        else:
            # Fallback: use ATR-based stop
            stop_loss = entry_price - (atr * 1.0)
        
        return stop_loss
    
    @staticmethod
    def _find_swing_high_for_tp(
        data: pd.DataFrame,
        entry_price: float,
        atr: float,
        stop_loss: float,
        min_rr: float,
        max_rr: float
    ) -> float:
        """Find recent swing high above entry for take profit."""
        # Look for highest high in recent data
        highs = data['high'].values
        
        # Find significant swing highs (local maxima)
        swing_highs = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])
        
        # Find swing highs above entry
        valid_highs = [high for high in swing_highs if high > entry_price]
        
        if valid_highs:
            # Use the nearest swing high above entry (first resistance)
            risk = abs(entry_price - stop_loss)
            
            # Filter highs that give reasonable R:R
            for high in sorted(valid_highs):
                reward = abs(high - entry_price)
                rr = reward / risk if risk > 0 else 0
                
                if min_rr <= rr <= max_rr:
                    return high - (atr * 0.2)  # Small buffer before resistance
            
            # If no high meets criteria, use the first one
            take_profit = min(valid_highs) - (atr * 0.2)
        else:
            # Fallback: use ATR-based target with min R:R
            risk = abs(entry_price - stop_loss)
            take_profit = entry_price + (risk * 2.5)
        
        return take_profit
    
    @staticmethod
    def _find_swing_high_for_sl(
        data: pd.DataFrame,
        entry_price: float,
        atr: float
    ) -> float:
        """Find recent swing high above entry for stop loss (SHORT)."""
        highs = data['high'].values
        
        # Find significant swing highs
        swing_highs = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])
        
        # Find the nearest swing high above entry
        valid_highs = [high for high in swing_highs if high > entry_price]
        
        if valid_highs:
            # Use the lowest swing high above entry (closest resistance)
            stop_loss = min(valid_highs) + (atr * 0.3)  # Small buffer above swing high
        else:
            # Fallback: use ATR-based stop
            stop_loss = entry_price + (atr * 1.0)
        
        return stop_loss
    
    @staticmethod
    def _find_swing_low_for_tp(
        data: pd.DataFrame,
        entry_price: float,
        atr: float,
        stop_loss: float,
        min_rr: float,
        max_rr: float
    ) -> float:
        """Find recent swing low below entry for take profit (SHORT)."""
        lows = data['low'].values
        
        # Find significant swing lows
        swing_lows = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])
        
        # Find swing lows below entry
        valid_lows = [low for low in swing_lows if low < entry_price]
        
        if valid_lows:
            # Use the nearest swing low below entry (first support)
            risk = abs(stop_loss - entry_price)
            
            # Filter lows that give reasonable R:R
            for low in sorted(valid_lows, reverse=True):
                reward = abs(entry_price - low)
                rr = reward / risk if risk > 0 else 0
                
                if min_rr <= rr <= max_rr:
                    return low + (atr * 0.2)  # Small buffer above support
            
            # If no low meets criteria, use the first one
            take_profit = max(valid_lows) + (atr * 0.2)
        else:
            # Fallback: use ATR-based target with min R:R
            risk = abs(stop_loss - entry_price)
            take_profit = entry_price - (risk * 2.5)
        
        return take_profit
