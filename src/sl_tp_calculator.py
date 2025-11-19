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

    @staticmethod
    def calculate_historical_sltp(
        data: pd.DataFrame,
        entry_price: float,
        signal_type: str,  # "LONG" or "SHORT"
        atr: float,
        lookback: int = 100,
        min_rr: float = 1.2
    ) -> Tuple[float, float, float]:
        """
        Calculate SL/TP based on historical price action analysis.
        
        Analyzes previous candles to find the most common reversal distances
        and uses these as the basis for SL/TP placement.
        
        Args:
            data: DataFrame with OHLCV data (minimum 100 candles)
            entry_price: Entry price
            signal_type: "LONG" or "SHORT"
            atr: Current ATR value
            lookback: Number of candles to analyze (minimum 100)
            min_rr: Minimum acceptable risk/reward ratio
            
        Returns:
            Tuple of (stop_loss, take_profit, risk_reward)
        """
        if len(data) < lookback:
            logger.warning(f"Insufficient data for historical analysis ({len(data)} < {lookback}), falling back to ATR")
            return SLTPCalculator._calculate_atr_based_sltp(entry_price, signal_type, atr, min_rr)
        
        try:
            # Analyze historical reversals
            reversal_distances = SLTPCalculator._analyze_historical_reversals(data, signal_type)
            
            if not reversal_distances:
                logger.warning("No historical reversals found, falling back to ATR")
                return SLTPCalculator._calculate_atr_based_sltp(entry_price, signal_type, atr, min_rr)
            
            # Calculate mode (most common distance)
            mode_distance = SLTPCalculator._calculate_mode_distance(reversal_distances)
            
            if signal_type == "LONG":
                # For LONG: SL below entry, TP above entry
                stop_loss = entry_price - mode_distance
                
                # Calculate TP to achieve minimum R:R
                risk = abs(entry_price - stop_loss)
                take_profit = entry_price + (risk * min_rr)
                
            else:  # SHORT
                # For SHORT: SL above entry, TP below entry
                stop_loss = entry_price + mode_distance
                
                # Calculate TP to achieve minimum R:R
                risk = abs(stop_loss - entry_price)
                take_profit = entry_price - (risk * min_rr)
            
            # Calculate risk/reward
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            logger.info(f"Historical SL/TP: Mode distance={mode_distance:.2f}, SL={stop_loss:.2f}, TP={take_profit:.2f}, R:R={risk_reward:.2f}")
            
            return stop_loss, take_profit, risk_reward
            
        except Exception as e:
            logger.error(f"Error in historical SL/TP calculation: {e}, falling back to ATR")
            return SLTPCalculator._calculate_atr_based_sltp(entry_price, signal_type, atr, min_rr)
    
    @staticmethod
    def _analyze_historical_reversals(
        data: pd.DataFrame,
        signal_type: str
    ) -> List[float]:
        """
        Analyze historical price reversals to find common distances.
        
        Args:
            data: DataFrame with OHLCV data
            signal_type: "LONG" or "SHORT"
            
        Returns:
            List of reversal distances
        """
        try:
            reversals = []
            
            if signal_type == "LONG":
                # For LONG signals, find distances from local lows to subsequent highs
                for i in range(2, len(data) - 2):
                    # Check if this is a local low
                    if data.iloc[i]['low'] < data.iloc[i-1]['low'] and \
                       data.iloc[i]['low'] < data.iloc[i+1]['low']:
                        
                        # Find the next local high
                        for j in range(i+1, min(i+20, len(data)-1)):
                            if data.iloc[j]['high'] > data.iloc[j-1]['high'] and \
                               data.iloc[j]['high'] > data.iloc[j+1]['high']:
                                
                                # Calculate distance
                                distance = data.iloc[j]['high'] - data.iloc[i]['low']
                                reversals.append(distance)
                                break
            
            else:  # SHORT
                # For SHORT signals, find distances from local highs to subsequent lows
                for i in range(2, len(data) - 2):
                    # Check if this is a local high
                    if data.iloc[i]['high'] > data.iloc[i-1]['high'] and \
                       data.iloc[i]['high'] > data.iloc[i+1]['high']:
                        
                        # Find the next local low
                        for j in range(i+1, min(i+20, len(data)-1)):
                            if data.iloc[j]['low'] < data.iloc[j-1]['low'] and \
                               data.iloc[j]['low'] < data.iloc[j+1]['low']:
                                
                                # Calculate distance
                                distance = data.iloc[i]['high'] - data.iloc[j]['low']
                                reversals.append(distance)
                                break
            
            logger.debug(f"Found {len(reversals)} historical reversals for {signal_type}")
            return reversals
            
        except Exception as e:
            logger.error(f"Error analyzing historical reversals: {e}")
            return []
    
    @staticmethod
    def _calculate_mode_distance(distances: List[float]) -> float:
        """
        Calculate mode (most common distance) from list of distances.
        
        Uses histogram binning to find the most common distance range.
        
        Args:
            distances: List of distance values
            
        Returns:
            Mode distance value
        """
        try:
            if not distances:
                return 0.0
            
            # Create histogram with 20 bins
            counts, bins = np.histogram(distances, bins=20)
            
            # Find bin with most occurrences
            max_count_idx = np.argmax(counts)
            
            # Return midpoint of the bin with most occurrences
            mode_distance = (bins[max_count_idx] + bins[max_count_idx + 1]) / 2
            
            logger.debug(f"Mode distance: {mode_distance:.2f} (from {len(distances)} samples)")
            
            return mode_distance
            
        except Exception as e:
            logger.error(f"Error calculating mode distance: {e}")
            # Fallback to median
            return float(np.median(distances)) if distances else 0.0
    
    @staticmethod
    def _calculate_atr_based_sltp(
        entry_price: float,
        signal_type: str,
        atr: float,
        min_rr: float = 1.2
    ) -> Tuple[float, float, float]:
        """
        Calculate SL/TP using ATR-based method (fallback).
        
        Args:
            entry_price: Entry price
            signal_type: "LONG" or "SHORT"
            atr: Current ATR value
            min_rr: Minimum risk/reward ratio
            
        Returns:
            Tuple of (stop_loss, take_profit, risk_reward)
        """
        if signal_type == "LONG":
            stop_loss = entry_price - (atr * 1.2)
            take_profit = entry_price + (atr * 2.0)
        else:  # SHORT
            stop_loss = entry_price + (atr * 1.2)
            take_profit = entry_price - (atr * 2.0)
        
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        return stop_loss, take_profit, risk_reward
    
    @staticmethod
    def validate_risk_reward(
        entry: float,
        sl: float,
        tp: float,
        min_ratio: float = 1.2
    ) -> bool:
        """
        Validate that risk/reward ratio meets minimum threshold.
        
        Args:
            entry: Entry price
            sl: Stop loss price
            tp: Take profit price
            min_ratio: Minimum acceptable ratio
            
        Returns:
            True if ratio meets minimum, False otherwise
        """
        try:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            
            if risk == 0:
                return False
            
            ratio = reward / risk
            return ratio >= min_ratio
            
        except Exception as e:
            logger.error(f"Error validating risk/reward: {e}")
            return False
