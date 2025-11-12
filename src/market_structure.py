"""
Market Structure Analyzer
Detects swing highs/lows, breaks of structure (BOS), and change of character (CHoCH)
"""
import logging
from dataclasses import dataclass
from typing import Optional, List, Tuple
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SwingPoint:
    """Swing high or low point"""
    point_type: str  # "high" or "low"
    price: float
    index: int
    timestamp: datetime
    strength: int  # Number of candles on each side confirming the swing


@dataclass
class StructureBreak:
    """Break of Structure (BOS) or Change of Character (CHoCH)"""
    break_type: str  # "BOS" or "CHoCH"
    direction: str  # "bullish" or "bearish"
    break_price: float
    previous_structure: float  # Previous high/low that was broken
    strength: int  # How significant the break is (1-5)
    timestamp: datetime


class MarketStructureAnalyzer:
    """
    Analyze market structure to identify:
    - Swing highs and lows
    - Break of Structure (BOS) - continuation
    - Change of Character (CHoCH) - reversal
    """
    
    def __init__(self, swing_lookback: int = 5, min_break_percent: float = 0.1):
        """
        Initialize market structure analyzer
        
        Args:
            swing_lookback: Candles on each side to confirm swing point
            min_break_percent: Minimum % move to confirm structure break
        """
        self.swing_lookback = swing_lookback
        self.min_break_percent = min_break_percent
        logger.info(f"MarketStructureAnalyzer initialized: lookback={swing_lookback}, min_break={min_break_percent}%")
    
    def find_swing_highs(self, data: pd.DataFrame, lookback: int = None) -> List[SwingPoint]:
        """
        Find swing high points in the data
        
        Args:
            data: DataFrame with OHLCV data
            lookback: Override default swing_lookback
            
        Returns:
            List of SwingPoint objects for highs
        """
        if lookback is None:
            lookback = self.swing_lookback
        
        swing_highs = []
        
        if len(data) < (lookback * 2 + 1):
            return swing_highs
        
        try:
            # Check each candle (excluding edges)
            for i in range(lookback, len(data) - lookback):
                current_high = data.iloc[i]['high']
                
                # Check if this is higher than surrounding candles
                is_swing_high = True
                
                # Check left side
                for j in range(i - lookback, i):
                    if data.iloc[j]['high'] >= current_high:
                        is_swing_high = False
                        break
                
                if not is_swing_high:
                    continue
                
                # Check right side
                for j in range(i + 1, i + lookback + 1):
                    if data.iloc[j]['high'] >= current_high:
                        is_swing_high = False
                        break
                
                if is_swing_high:
                    swing_point = SwingPoint(
                        point_type="high",
                        price=current_high,
                        index=i,
                        timestamp=data.iloc[i]['timestamp'],
                        strength=lookback
                    )
                    swing_highs.append(swing_point)
            
            return swing_highs
            
        except Exception as e:
            logger.error(f"Error finding swing highs: {e}")
            return []
    
    def find_swing_lows(self, data: pd.DataFrame, lookback: int = None) -> List[SwingPoint]:
        """
        Find swing low points in the data
        
        Args:
            data: DataFrame with OHLCV data
            lookback: Override default swing_lookback
            
        Returns:
            List of SwingPoint objects for lows
        """
        if lookback is None:
            lookback = self.swing_lookback
        
        swing_lows = []
        
        if len(data) < (lookback * 2 + 1):
            return swing_lows
        
        try:
            # Check each candle (excluding edges)
            for i in range(lookback, len(data) - lookback):
                current_low = data.iloc[i]['low']
                
                # Check if this is lower than surrounding candles
                is_swing_low = True
                
                # Check left side
                for j in range(i - lookback, i):
                    if data.iloc[j]['low'] <= current_low:
                        is_swing_low = False
                        break
                
                if not is_swing_low:
                    continue
                
                # Check right side
                for j in range(i + 1, i + lookback + 1):
                    if data.iloc[j]['low'] <= current_low:
                        is_swing_low = False
                        break
                
                if is_swing_low:
                    swing_point = SwingPoint(
                        point_type="low",
                        price=current_low,
                        index=i,
                        timestamp=data.iloc[i]['timestamp'],
                        strength=lookback
                    )
                    swing_lows.append(swing_point)
            
            return swing_lows
            
        except Exception as e:
            logger.error(f"Error finding swing lows: {e}")
            return []
    
    def detect_structure_break(self, data: pd.DataFrame) -> Optional[StructureBreak]:
        """
        Detect if current price action shows a structure break
        
        BOS (Break of Structure): Price breaks previous high in uptrend or low in downtrend
        CHoCH (Change of Character): Price breaks previous low in uptrend or high in downtrend
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            StructureBreak object if detected, None otherwise
        """
        if len(data) < 20:
            return None
        
        try:
            current_candle = data.iloc[-1]
            current_price = current_candle['close']
            
            # Find recent swing points
            swing_highs = self.find_swing_highs(data)
            swing_lows = self.find_swing_lows(data)
            
            if not swing_highs or not swing_lows:
                return None
            
            # Get most recent swing high and low
            recent_high = max(swing_highs, key=lambda x: x.index)
            recent_low = max(swing_lows, key=lambda x: x.index)
            
            # Determine current trend (which came last)
            if recent_high.index > recent_low.index:
                current_trend = "bullish"
                previous_structure = recent_high.price
            else:
                current_trend = "bearish"
                previous_structure = recent_low.price
            
            # Check for bullish BOS (breaking previous high in uptrend)
            if current_trend == "bullish" and current_price > previous_structure:
                break_percent = ((current_price - previous_structure) / previous_structure) * 100
                
                if break_percent >= self.min_break_percent:
                    # Calculate strength based on volume and break size
                    volume_ratio = current_candle['volume'] / current_candle.get('volume_ma', current_candle['volume'])
                    strength = min(5, int(break_percent * 10) + (2 if volume_ratio > 1.5 else 0))
                    
                    structure_break = StructureBreak(
                        break_type="BOS",
                        direction="bullish",
                        break_price=current_price,
                        previous_structure=previous_structure,
                        strength=strength,
                        timestamp=current_candle['timestamp']
                    )
                    
                    logger.info(f"Bullish BOS detected: Price {current_price:.2f} broke {previous_structure:.2f} (+{break_percent:.2f}%), Strength: {strength}/5")
                    return structure_break
            
            # Check for bearish BOS (breaking previous low in downtrend)
            elif current_trend == "bearish" and current_price < previous_structure:
                break_percent = ((previous_structure - current_price) / previous_structure) * 100
                
                if break_percent >= self.min_break_percent:
                    volume_ratio = current_candle['volume'] / current_candle.get('volume_ma', current_candle['volume'])
                    strength = min(5, int(break_percent * 10) + (2 if volume_ratio > 1.5 else 0))
                    
                    structure_break = StructureBreak(
                        break_type="BOS",
                        direction="bearish",
                        break_price=current_price,
                        previous_structure=previous_structure,
                        strength=strength,
                        timestamp=current_candle['timestamp']
                    )
                    
                    logger.info(f"Bearish BOS detected: Price {current_price:.2f} broke {previous_structure:.2f} (-{break_percent:.2f}%), Strength: {strength}/5")
                    return structure_break
            
            # Check for CHoCH (trend reversal)
            # Get second most recent swing point of opposite type
            if current_trend == "bullish":
                # In uptrend, check if we broke below recent low (reversal)
                if len(swing_lows) >= 2:
                    second_recent_low = sorted(swing_lows, key=lambda x: x.index)[-2]
                    if current_price < second_recent_low.price:
                        break_percent = ((second_recent_low.price - current_price) / second_recent_low.price) * 100
                        
                        if break_percent >= self.min_break_percent:
                            volume_ratio = current_candle['volume'] / current_candle.get('volume_ma', current_candle['volume'])
                            strength = min(5, int(break_percent * 10) + (2 if volume_ratio > 1.5 else 0))
                            
                            structure_break = StructureBreak(
                                break_type="CHoCH",
                                direction="bearish",
                                break_price=current_price,
                                previous_structure=second_recent_low.price,
                                strength=strength,
                                timestamp=current_candle['timestamp']
                            )
                            
                            logger.info(f"Bearish CHoCH detected: Price {current_price:.2f} broke {second_recent_low.price:.2f} (-{break_percent:.2f}%), Strength: {strength}/5")
                            return structure_break
            
            else:  # bearish trend
                # In downtrend, check if we broke above recent high (reversal)
                if len(swing_highs) >= 2:
                    second_recent_high = sorted(swing_highs, key=lambda x: x.index)[-2]
                    if current_price > second_recent_high.price:
                        break_percent = ((current_price - second_recent_high.price) / second_recent_high.price) * 100
                        
                        if break_percent >= self.min_break_percent:
                            volume_ratio = current_candle['volume'] / current_candle.get('volume_ma', current_candle['volume'])
                            strength = min(5, int(break_percent * 10) + (2 if volume_ratio > 1.5 else 0))
                            
                            structure_break = StructureBreak(
                                break_type="CHoCH",
                                direction="bullish",
                                break_price=current_price,
                                previous_structure=second_recent_high.price,
                                strength=strength,
                                timestamp=current_candle['timestamp']
                            )
                            
                            logger.info(f"Bullish CHoCH detected: Price {current_price:.2f} broke {second_recent_high.price:.2f} (+{break_percent:.2f}%), Strength: {strength}/5")
                            return structure_break
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting structure break: {e}")
            return None
    
    def get_current_trend(self, data: pd.DataFrame) -> str:
        """
        Determine current market trend based on swing structure
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            "bullish", "bearish", or "neutral"
        """
        if len(data) < 20:
            return "neutral"
        
        try:
            swing_highs = self.find_swing_highs(data)
            swing_lows = self.find_swing_lows(data)
            
            if not swing_highs or not swing_lows:
                return "neutral"
            
            # Get last 2 swing highs and lows
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                recent_highs = sorted(swing_highs, key=lambda x: x.index)[-2:]
                recent_lows = sorted(swing_lows, key=lambda x: x.index)[-2:]
                
                # Uptrend: Higher highs and higher lows
                if recent_highs[1].price > recent_highs[0].price and recent_lows[1].price > recent_lows[0].price:
                    return "bullish"
                
                # Downtrend: Lower highs and lower lows
                elif recent_highs[1].price < recent_highs[0].price and recent_lows[1].price < recent_lows[0].price:
                    return "bearish"
            
            return "neutral"
            
        except Exception as e:
            logger.error(f"Error determining trend: {e}")
            return "neutral"
