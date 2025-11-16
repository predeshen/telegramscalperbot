"""
FVG Detector - Fair Value Gap Detection
Detects institutional supply/demand zones based on price gaps.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class FVGZone:
    """Represents a Fair Value Gap zone."""
    fvg_type: str  # 'inverse' (bearish) or 'regular' (bullish)
    timeframe: str
    high: float  # Upper boundary of gap
    low: float  # Lower boundary of gap
    gap_percent: float  # Gap size as percentage
    created_at: datetime
    candle_index: int
    filled: bool = False
    filled_at: Optional[datetime] = None
    respect_count: int = 0  # Number of times price respected this zone


class FVGDetector:
    """Detects Fair Value Gaps and liquidity voids."""
    
    def __init__(self, min_gap_percent: float = 0.2):
        """
        Initialize FVG detector.
        
        Args:
            min_gap_percent: Minimum gap size as percentage of price
        """
        self.min_gap_percent = min_gap_percent
        self.active_fvgs: Dict[str, List[FVGZone]] = {}  # timeframe -> zones
        
        logger.info(f"Initialized FVGDetector (min_gap={min_gap_percent}%)")
    
    def detect_fvgs(self, df: pd.DataFrame, timeframe: str) -> List[FVGZone]:
        """
        Detect Fair Value Gaps in candlestick data.
        
        An FVG exists when there's a gap between candles:
        - Inverse FVG (bearish): candle[i-1].low > candle[i+1].high
        - Regular FVG (bullish): candle[i-1].high < candle[i+1].low
        
        Args:
            df: DataFrame with OHLCV data
            timeframe: Timeframe being analyzed
            
        Returns:
            List of newly detected FVG zones
        """
        try:
            if df.empty or len(df) < 3:
                return []
            
            new_fvgs = []
            
            # Scan for FVGs (need at least 3 candles)
            for i in range(1, len(df) - 1):
                prev_candle = df.iloc[i - 1]
                current_candle = df.iloc[i]
                next_candle = df.iloc[i + 1]
                
                # Check for Inverse FVG (bearish gap)
                if prev_candle['low'] > next_candle['high']:
                    gap_high = prev_candle['low']
                    gap_low = next_candle['high']
                    gap_size = gap_high - gap_low
                    gap_percent = (gap_size / prev_candle['close']) * 100
                    
                    if gap_percent >= self.min_gap_percent:
                        fvg = FVGZone(
                            fvg_type='inverse',
                            timeframe=timeframe,
                            high=gap_high,
                            low=gap_low,
                            gap_percent=gap_percent,
                            created_at=current_candle['timestamp'],
                            candle_index=i
                        )
                        new_fvgs.append(fvg)
                        logger.info(f"Inverse FVG detected on {timeframe}: ${gap_low:.2f}-${gap_high:.2f} ({gap_percent:.2f}%)")
                
                # Check for Regular FVG (bullish gap)
                elif prev_candle['high'] < next_candle['low']:
                    gap_low = prev_candle['high']
                    gap_high = next_candle['low']
                    gap_size = gap_high - gap_low
                    gap_percent = (gap_size / prev_candle['close']) * 100
                    
                    if gap_percent >= self.min_gap_percent:
                        fvg = FVGZone(
                            fvg_type='regular',
                            timeframe=timeframe,
                            high=gap_high,
                            low=gap_low,
                            gap_percent=gap_percent,
                            created_at=current_candle['timestamp'],
                            candle_index=i
                        )
                        new_fvgs.append(fvg)
                        logger.info(f"Regular FVG detected on {timeframe}: ${gap_low:.2f}-${gap_high:.2f} ({gap_percent:.2f}%)")
            
            # Add to active FVGs
            if timeframe not in self.active_fvgs:
                self.active_fvgs[timeframe] = []
            
            self.active_fvgs[timeframe].extend(new_fvgs)
            
            # Keep only recent FVGs (last 20)
            self.active_fvgs[timeframe] = self.active_fvgs[timeframe][-20:]
            
            return new_fvgs
            
        except Exception as e:
            logger.error(f"Error detecting FVGs: {e}")
            return []
    
    def check_fvg_reentry(
        self,
        current_price: float,
        fvg_zone: FVGZone,
        tolerance_pct: float = 0.1
    ) -> bool:
        """
        Check if price has re-entered an FVG zone.
        
        Args:
            current_price: Current market price
            fvg_zone: FVG zone to check
            tolerance_pct: Tolerance percentage for zone boundaries
            
        Returns:
            True if price is in the zone
        """
        try:
            # Add tolerance to zone boundaries
            tolerance = (fvg_zone.high - fvg_zone.low) * (tolerance_pct / 100)
            zone_high = fvg_zone.high + tolerance
            zone_low = fvg_zone.low - tolerance
            
            return zone_low <= current_price <= zone_high
            
        except Exception as e:
            logger.error(f"Error checking FVG re-entry: {e}")
            return False
    
    def detect_lower_tf_shift(
        self,
        df_lower: pd.DataFrame,
        fvg_zone: FVGZone
    ) -> Tuple[bool, str]:
        """
        Detect market structure shift on lower timeframe within FVG zone.
        
        For inverse FVG (bearish):
        - Look for break of structure (BOS) to downside
        - Confirm with lower high formation
        
        For regular FVG (bullish):
        - Look for break of structure (BOS) to upside
        - Confirm with higher low formation
        
        Args:
            df_lower: Lower timeframe DataFrame
            fvg_zone: FVG zone to analyze
            
        Returns:
            (shift_detected, shift_description)
        """
        try:
            if df_lower.empty or len(df_lower) < 10:
                return False, "Insufficient data"
            
            # Get recent candles
            recent = df_lower.tail(10)
            
            if fvg_zone.fvg_type == 'inverse':
                # Bearish FVG - look for downside break
                # Find recent high
                recent_high = recent['high'].max()
                recent_high_idx = recent['high'].idxmax()
                
                # Check if price broke below recent low after making high
                candles_after_high = recent.loc[recent_high_idx:]
                if len(candles_after_high) > 1:
                    recent_low = candles_after_high['low'].min()
                    
                    # Check for lower high formation
                    if recent['high'].iloc[-1] < recent_high:
                        return True, f"Bearish BOS: Lower high at ${recent['high'].iloc[-1]:.2f}"
            
            else:  # regular FVG
                # Bullish FVG - look for upside break
                # Find recent low
                recent_low = recent['low'].min()
                recent_low_idx = recent['low'].idxmin()
                
                # Check if price broke above recent high after making low
                candles_after_low = recent.loc[recent_low_idx:]
                if len(candles_after_low) > 1:
                    recent_high = candles_after_low['high'].max()
                    
                    # Check for higher low formation
                    if recent['low'].iloc[-1] > recent_low:
                        return True, f"Bullish BOS: Higher low at ${recent['low'].iloc[-1]:.2f}"
            
            return False, "No structure shift detected"
            
        except Exception as e:
            logger.error(f"Error detecting lower TF shift: {e}")
            return False, f"Error: {str(e)}"
    
    def calculate_fvg_targets(
        self,
        df: pd.DataFrame,
        fvg_zone: FVGZone,
        lookback: int = 50
    ) -> Tuple[float, float]:
        """
        Calculate target levels based on swing points and liquidity.
        
        Args:
            df: DataFrame with price data
            fvg_zone: FVG zone
            lookback: Number of candles to look back
            
        Returns:
            (target1, target2) - Two target levels
        """
        try:
            if df.empty or len(df) < lookback:
                lookback = len(df)
            
            recent = df.tail(lookback)
            
            if fvg_zone.fvg_type == 'inverse':
                # Bearish targets - find swing lows
                lows = recent['low'].values
                
                # Find local minima
                swing_lows = []
                for i in range(2, len(lows) - 2):
                    if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
                       lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                        swing_lows.append(lows[i])
                
                if len(swing_lows) >= 2:
                    swing_lows.sort()
                    target1 = swing_lows[0]
                    target2 = swing_lows[1] if len(swing_lows) > 1 else swing_lows[0] * 0.98
                else:
                    # Default targets below FVG
                    target1 = fvg_zone.low * 0.98
                    target2 = fvg_zone.low * 0.96
            
            else:  # regular FVG
                # Bullish targets - find swing highs
                highs = recent['high'].values
                
                # Find local maxima
                swing_highs = []
                for i in range(2, len(highs) - 2):
                    if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
                       highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                        swing_highs.append(highs[i])
                
                if len(swing_highs) >= 2:
                    swing_highs.sort(reverse=True)
                    target1 = swing_highs[0]
                    target2 = swing_highs[1] if len(swing_highs) > 1 else swing_highs[0] * 1.02
                else:
                    # Default targets above FVG
                    target1 = fvg_zone.high * 1.02
                    target2 = fvg_zone.high * 1.04
            
            return target1, target2
            
        except Exception as e:
            logger.error(f"Error calculating FVG targets: {e}")
            # Return default targets
            if fvg_zone.fvg_type == 'inverse':
                return fvg_zone.low * 0.98, fvg_zone.low * 0.96
            else:
                return fvg_zone.high * 1.02, fvg_zone.high * 1.04
    
    def mark_fvg_filled(self, fvg_zone: FVGZone, current_time: datetime) -> None:
        """
        Mark an FVG zone as filled when price fully retraces through it.
        
        Args:
            fvg_zone: FVG zone to mark as filled
            current_time: Current timestamp
        """
        fvg_zone.filled = True
        fvg_zone.filled_at = current_time
        logger.info(f"FVG zone marked as filled: {fvg_zone.fvg_type} ${fvg_zone.low:.2f}-${fvg_zone.high:.2f}")
    
    def get_active_fvgs(self, timeframe: str, include_filled: bool = False) -> List[FVGZone]:
        """
        Get active FVG zones for a timeframe.
        
        Args:
            timeframe: Timeframe to get FVGs for
            include_filled: Whether to include filled zones
            
        Returns:
            List of FVG zones
        """
        if timeframe not in self.active_fvgs:
            return []
        
        if include_filled:
            return self.active_fvgs[timeframe]
        else:
            return [fvg for fvg in self.active_fvgs[timeframe] if not fvg.filled]
    
    def cleanup_old_fvgs(self, max_age_candles: int = 100) -> None:
        """
        Remove old FVG zones.
        
        Args:
            max_age_candles: Maximum age in candles
        """
        for timeframe in self.active_fvgs:
            # Keep only recent FVGs
            self.active_fvgs[timeframe] = self.active_fvgs[timeframe][-max_age_candles:]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data with a gap
    data = {
        'timestamp': pd.date_range('2025-01-01', periods=10, freq='1H'),
        'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'high': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
        'close': [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
        'volume': [1000] * 10
    }
    df = pd.DataFrame(data)
    
    # Create FVG detector
    detector = FVGDetector(min_gap_percent=0.1)
    
    # Detect FVGs
    fvgs = detector.detect_fvgs(df, '1h')
    print(f"Detected {len(fvgs)} FVGs")
    
    for fvg in fvgs:
        print(f"  {fvg.fvg_type}: ${fvg.low:.2f}-${fvg.high:.2f} ({fvg.gap_percent:.2f}%)")
