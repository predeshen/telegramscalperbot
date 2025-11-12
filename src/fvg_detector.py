"""
Fair Value Gap (FVG) Detector
Detects imbalance zones where price moved too fast, leaving gaps to be filled
"""
import logging
from dataclasses import dataclass
from typing import Optional, List
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FVG:
    """Fair Value Gap information"""
    gap_type: str  # "bullish" or "bearish"
    gap_high: float
    gap_low: float
    gap_size: float
    gap_percent: float
    candle_index: int
    timestamp: datetime
    volume_ratio: float  # Volume during gap formation
    is_filled: bool = False
    
    def contains_price(self, price: float) -> bool:
        """Check if price is within the gap"""
        return self.gap_low <= price <= self.gap_high
    
    def get_midpoint(self) -> float:
        """Get gap midpoint"""
        return (self.gap_high + self.gap_low) / 2


class FVGDetector:
    """
    Detect Fair Value Gaps (FVG) - 3-candle patterns where price gaps
    
    Bullish FVG: Candle 1 high < Candle 3 low (gap between them)
    Bearish FVG: Candle 1 low > Candle 3 high (gap between them)
    """
    
    def __init__(self, min_gap_percent: float = 0.05, max_lookback: int = 20):
        """
        Initialize FVG detector
        
        Args:
            min_gap_percent: Minimum gap size as % of price (0.05 = 0.05%)
            max_lookback: Maximum candles to look back for unfilled gaps
        """
        self.min_gap_percent = min_gap_percent
        self.max_lookback = max_lookback
        logger.info(f"FVGDetector initialized: min_gap={min_gap_percent}%, lookback={max_lookback}")
    
    def detect_fvg(self, data: pd.DataFrame) -> Optional[FVG]:
        """
        Detect most recent FVG in the data
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            FVG object if detected, None otherwise
        """
        if len(data) < 3:
            return None
        
        try:
            # Check last 3 candles for FVG formation
            candle_1 = data.iloc[-3]
            candle_2 = data.iloc[-2]
            candle_3 = data.iloc[-1]
            
            current_price = candle_3['close']
            
            # Bullish FVG: Gap between candle 1 high and candle 3 low
            if candle_1['high'] < candle_3['low']:
                gap_low = candle_1['high']
                gap_high = candle_3['low']
                gap_size = gap_high - gap_low
                gap_percent = (gap_size / current_price) * 100
                
                # Check minimum gap size
                if gap_percent >= self.min_gap_percent:
                    volume_ratio = candle_3['volume'] / candle_3.get('volume_ma', candle_3['volume'])
                    
                    fvg = FVG(
                        gap_type="bullish",
                        gap_high=gap_high,
                        gap_low=gap_low,
                        gap_size=gap_size,
                        gap_percent=gap_percent,
                        candle_index=len(data) - 1,
                        timestamp=candle_3['timestamp'],
                        volume_ratio=volume_ratio
                    )
                    
                    logger.info(f"Bullish FVG detected: {gap_low:.2f} - {gap_high:.2f} ({gap_percent:.2f}%), Volume: {volume_ratio:.2f}x")
                    return fvg
            
            # Bearish FVG: Gap between candle 1 low and candle 3 high
            elif candle_1['low'] > candle_3['high']:
                gap_high = candle_1['low']
                gap_low = candle_3['high']
                gap_size = gap_high - gap_low
                gap_percent = (gap_size / current_price) * 100
                
                # Check minimum gap size
                if gap_percent >= self.min_gap_percent:
                    volume_ratio = candle_3['volume'] / candle_3.get('volume_ma', candle_3['volume'])
                    
                    fvg = FVG(
                        gap_type="bearish",
                        gap_high=gap_high,
                        gap_low=gap_low,
                        gap_size=gap_size,
                        gap_percent=gap_percent,
                        candle_index=len(data) - 1,
                        timestamp=candle_3['timestamp'],
                        volume_ratio=volume_ratio
                    )
                    
                    logger.info(f"Bearish FVG detected: {gap_low:.2f} - {gap_high:.2f} ({gap_percent:.2f}%), Volume: {volume_ratio:.2f}x")
                    return fvg
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting FVG: {e}")
            return None
    
    def get_unfilled_fvgs(self, data: pd.DataFrame) -> List[FVG]:
        """
        Get all unfilled FVGs in recent history
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            List of unfilled FVG objects
        """
        unfilled_fvgs = []
        
        if len(data) < 3:
            return unfilled_fvgs
        
        try:
            current_price = data.iloc[-1]['close']
            
            # Look back through recent candles
            lookback = min(self.max_lookback, len(data) - 2)
            
            for i in range(lookback):
                idx = -(i + 3)  # Start from 3 candles back
                
                if abs(idx) > len(data):
                    break
                
                candle_1 = data.iloc[idx]
                candle_2 = data.iloc[idx + 1]
                candle_3 = data.iloc[idx + 2]
                
                # Bullish FVG
                if candle_1['high'] < candle_3['low']:
                    gap_low = candle_1['high']
                    gap_high = candle_3['low']
                    gap_size = gap_high - gap_low
                    gap_percent = (gap_size / current_price) * 100
                    
                    if gap_percent >= self.min_gap_percent:
                        # Check if gap is still unfilled (current price hasn't touched it)
                        if current_price > gap_high:
                            volume_ratio = candle_3['volume'] / candle_3.get('volume_ma', candle_3['volume'])
                            
                            fvg = FVG(
                                gap_type="bullish",
                                gap_high=gap_high,
                                gap_low=gap_low,
                                gap_size=gap_size,
                                gap_percent=gap_percent,
                                candle_index=len(data) + idx + 2,
                                timestamp=candle_3['timestamp'],
                                volume_ratio=volume_ratio,
                                is_filled=False
                            )
                            unfilled_fvgs.append(fvg)
                
                # Bearish FVG
                elif candle_1['low'] > candle_3['high']:
                    gap_high = candle_1['low']
                    gap_low = candle_3['high']
                    gap_size = gap_high - gap_low
                    gap_percent = (gap_size / current_price) * 100
                    
                    if gap_percent >= self.min_gap_percent:
                        # Check if gap is still unfilled (current price hasn't touched it)
                        if current_price < gap_low:
                            volume_ratio = candle_3['volume'] / candle_3.get('volume_ma', candle_3['volume'])
                            
                            fvg = FVG(
                                gap_type="bearish",
                                gap_high=gap_high,
                                gap_low=gap_low,
                                gap_size=gap_size,
                                gap_percent=gap_percent,
                                candle_index=len(data) + idx + 2,
                                timestamp=candle_3['timestamp'],
                                volume_ratio=volume_ratio,
                                is_filled=False
                            )
                            unfilled_fvgs.append(fvg)
            
            if unfilled_fvgs:
                logger.debug(f"Found {len(unfilled_fvgs)} unfilled FVGs")
            
            return unfilled_fvgs
            
        except Exception as e:
            logger.error(f"Error getting unfilled FVGs: {e}")
            return []
