"""
NWOG Detector - New Week Opening Gap Detection
Detects institutional levels formed at weekly opens for indices.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import pandas as pd


logger = logging.getLogger(__name__)


@dataclass
class NWOGZone:
    """Represents a New Week Opening Gap zone."""
    gap_type: str  # 'bullish' (gap up) or 'bearish' (gap down)
    friday_close: float
    monday_open: float
    gap_high: float  # Upper boundary
    gap_low: float  # Lower boundary
    gap_size_percent: float
    created_at: datetime
    week_number: int
    respected: bool = False  # Has price respected this level?
    respect_count: int = 0  # Number of times price respected this zone


class NWOGDetector:
    """Detects New Week Opening Gaps for indices."""
    
    def __init__(self, min_gap_percent: float = 0.1):
        """
        Initialize NWOG detector.
        
        Args:
            min_gap_percent: Minimum gap size as percentage of price
        """
        self.min_gap_percent = min_gap_percent
        self.active_nwogs: List[NWOGZone] = []
        
        logger.info(f"Initialized NWOGDetector (min_gap={min_gap_percent}%)")
    
    def detect_nwog(self, df: pd.DataFrame) -> Optional[NWOGZone]:
        """
        Detect New Week Opening Gap.
        
        Identifies gap between Friday close and Monday open.
        
        Args:
            df: DataFrame with daily or 4h data including day of week
            
        Returns:
            NWOGZone if gap detected, None otherwise
        """
        try:
            if df.empty or len(df) < 5:
                return None
            
            # Ensure timestamp column exists
            if 'timestamp' not in df.columns:
                return None
            
            # Add day of week if not present
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            
            # Find Friday (4) and Monday (0) candles
            fridays = df[df['day_of_week'] == 4]
            mondays = df[df['day_of_week'] == 0]
            
            if fridays.empty or mondays.empty:
                return None
            
            # Get most recent Friday and following Monday
            last_friday = fridays.iloc[-1]
            
            # Find Monday after this Friday
            friday_date = pd.to_datetime(last_friday['timestamp'])
            mondays_after = mondays[pd.to_datetime(mondays['timestamp']) > friday_date]
            
            if mondays_after.empty:
                return None
            
            next_monday = mondays_after.iloc[0]
            
            friday_close = last_friday['close']
            monday_open = next_monday['open']
            
            # Calculate gap
            gap_size = abs(monday_open - friday_close)
            gap_percent = (gap_size / friday_close) * 100
            
            if gap_percent < self.min_gap_percent:
                return None
            
            # Determine gap type and boundaries
            if monday_open > friday_close:
                gap_type = 'bullish'
                gap_low = friday_close
                gap_high = monday_open
            else:
                gap_type = 'bearish'
                gap_low = monday_open
                gap_high = friday_close
            
            # Get week number
            week_number = friday_date.isocalendar()[1]
            
            nwog = NWOGZone(
                gap_type=gap_type,
                friday_close=friday_close,
                monday_open=monday_open,
                gap_high=gap_high,
                gap_low=gap_low,
                gap_size_percent=gap_percent,
                created_at=next_monday['timestamp'],
                week_number=week_number
            )
            
            logger.info(f"NWOG detected: {gap_type} gap of {gap_percent:.2f}% "
                       f"(${gap_low:.2f}-${gap_high:.2f}) Week {week_number}")
            
            # Add to active NWOGs
            self.active_nwogs.append(nwog)
            
            # Keep only recent NWOGs (last 8 weeks)
            self.active_nwogs = self.active_nwogs[-8:]
            
            return nwog
            
        except Exception as e:
            logger.error(f"Error detecting NWOG: {e}")
            return None
    
    def check_nwog_respect(
        self,
        current_price: float,
        nwog_zone: NWOGZone,
        df_lower: pd.DataFrame,
        tolerance_pct: float = 0.2
    ) -> Tuple[bool, str]:
        """
        Check if price is respecting NWOG zone as support/resistance.
        
        For bearish NWOG (gap down):
        - Price should reject at gap high (resistance)
        - Look for bearish reversal patterns
        
        For bullish NWOG (gap up):
        - Price should reject at gap low (support)
        - Look for bullish reversal patterns
        
        Args:
            current_price: Current market price
            nwog_zone: NWOG zone to check
            df_lower: Lower timeframe DataFrame for confirmation
            tolerance_pct: Tolerance percentage for zone boundaries
            
        Returns:
            (is_respected, rejection_description)
        """
        try:
            # Check if price is near the zone
            tolerance = (nwog_zone.gap_high - nwog_zone.gap_low) * (tolerance_pct / 100)
            
            if nwog_zone.gap_type == 'bearish':
                # Check for resistance at gap high
                zone_high = nwog_zone.gap_high + tolerance
                zone_low = nwog_zone.gap_high - tolerance
                
                if zone_low <= current_price <= zone_high:
                    # Price is at resistance - check for rejection
                    if not df_lower.empty and len(df_lower) >= 3:
                        recent = df_lower.tail(3)
                        
                        # Look for bearish rejection (lower highs)
                        if recent['high'].iloc[-1] < recent['high'].iloc[-2]:
                            nwog_zone.respect_count += 1
                            nwog_zone.respected = True
                            return True, f"Bearish rejection at NWOG resistance ${nwog_zone.gap_high:.2f}"
            
            else:  # bullish NWOG
                # Check for support at gap low
                zone_high = nwog_zone.gap_low + tolerance
                zone_low = nwog_zone.gap_low - tolerance
                
                if zone_low <= current_price <= zone_high:
                    # Price is at support - check for rejection
                    if not df_lower.empty and len(df_lower) >= 3:
                        recent = df_lower.tail(3)
                        
                        # Look for bullish rejection (higher lows)
                        if recent['low'].iloc[-1] > recent['low'].iloc[-2]:
                            nwog_zone.respect_count += 1
                            nwog_zone.respected = True
                            return True, f"Bullish rejection at NWOG support ${nwog_zone.gap_low:.2f}"
            
            return False, "No rejection detected"
            
        except Exception as e:
            logger.error(f"Error checking NWOG respect: {e}")
            return False, f"Error: {str(e)}"
    
    def calculate_nwog_targets(
        self,
        nwog_zone: NWOGZone,
        df: pd.DataFrame,
        lookback: int = 50
    ) -> Tuple[float, float]:
        """
        Calculate target levels from NWOG zone.
        
        Targets based on:
        - Previous week's swing points
        - Liquidity pools below/above NWOG
        
        Args:
            nwog_zone: NWOG zone
            df: DataFrame with price data
            lookback: Number of candles to look back
            
        Returns:
            (target1, target2)
        """
        try:
            if df.empty or len(df) < lookback:
                lookback = len(df)
            
            recent = df.tail(lookback)
            
            if nwog_zone.gap_type == 'bearish':
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
                    target2 = swing_lows[1] if len(swing_lows) > 1 else swing_lows[0] * 0.99
                else:
                    # Default targets below NWOG
                    target1 = nwog_zone.gap_low * 0.99
                    target2 = nwog_zone.gap_low * 0.98
            
            else:  # bullish NWOG
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
                    target2 = swing_highs[1] if len(swing_highs) > 1 else swing_highs[0] * 1.01
                else:
                    # Default targets above NWOG
                    target1 = nwog_zone.gap_high * 1.01
                    target2 = nwog_zone.gap_high * 1.02
            
            return target1, target2
            
        except Exception as e:
            logger.error(f"Error calculating NWOG targets: {e}")
            # Return default targets
            if nwog_zone.gap_type == 'bearish':
                return nwog_zone.gap_low * 0.99, nwog_zone.gap_low * 0.98
            else:
                return nwog_zone.gap_high * 1.01, nwog_zone.gap_high * 1.02
    
    def get_active_nwogs(self, max_age_weeks: int = 4) -> List[NWOGZone]:
        """
        Get active NWOG zones (not older than max_age_weeks).
        
        Args:
            max_age_weeks: Maximum age in weeks
            
        Returns:
            List of active NWOG zones
        """
        if not self.active_nwogs:
            return []
        
        cutoff_date = datetime.now() - timedelta(weeks=max_age_weeks)
        
        return [
            nwog for nwog in self.active_nwogs
            if nwog.created_at >= cutoff_date
        ]
    
    def cleanup_old_nwogs(self, max_age_weeks: int = 8) -> None:
        """
        Remove old NWOG zones.
        
        Args:
            max_age_weeks: Maximum age in weeks
        """
        cutoff_date = datetime.now() - timedelta(weeks=max_age_weeks)
        
        self.active_nwogs = [
            nwog for nwog in self.active_nwogs
            if nwog.created_at >= cutoff_date
        ]
        
        logger.info(f"Cleaned up old NWOGs, {len(self.active_nwogs)} remaining")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample weekly data
    dates = pd.date_range('2025-01-01', periods=14, freq='D')
    data = {
        'timestamp': dates,
        'open': [100 + i for i in range(14)],
        'high': [101 + i for i in range(14)],
        'low': [99 + i for i in range(14)],
        'close': [100.5 + i for i in range(14)],
        'volume': [1000] * 14
    }
    df = pd.DataFrame(data)
    
    # Create NWOG detector
    detector = NWOGDetector(min_gap_percent=0.1)
    
    # Detect NWOG
    nwog = detector.detect_nwog(df)
    if nwog:
        print(f"NWOG detected: {nwog.gap_type} ${nwog.gap_low:.2f}-${nwog.gap_high:.2f}")
        print(f"Gap size: {nwog.gap_size_percent:.2f}%")
    else:
        print("No NWOG detected")
