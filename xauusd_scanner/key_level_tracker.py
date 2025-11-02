"""
Key Level Tracker for Gold Trading
Tracks psychological levels, daily highs/lows, and previous close
"""
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class KeyLevelTracker:
    """
    Tracks key price levels for Gold (XAU/USD).
    
    Monitors:
    - Psychological round numbers (2300, 2350, 2400, etc.)
    - Daily high/low
    - Previous day close
    - Weekly high/low
    """
    
    def __init__(self, round_number_interval: float = 50.0):
        """
        Initialize Key Level Tracker.
        
        Args:
            round_number_interval: Interval for psychological levels (default 50)
        """
        self.round_number_interval = round_number_interval
        
        # Daily levels
        self.daily_high: Optional[float] = None
        self.daily_low: Optional[float] = None
        self.daily_open: Optional[float] = None
        self.previous_close: Optional[float] = None
        
        # Weekly levels
        self.weekly_high: Optional[float] = None
        self.weekly_low: Optional[float] = None
        
        # Current date tracking
        self.current_date: Optional[str] = None
        self.current_week: Optional[int] = None
        
        logger.info(f"KeyLevelTracker initialized (round numbers every ${round_number_interval})")
    
    def update_levels(self, high: float, low: float, close: float, 
                     timestamp: Optional[datetime] = None) -> None:
        """
        Update key levels with current price data.
        
        Args:
            high: Current period high
            low: Current period low
            close: Current close price
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        current_date = timestamp.strftime('%Y-%m-%d')
        current_week = timestamp.isocalendar()[1]
        
        # Check for new day
        if self.current_date != current_date:
            # Save previous close
            if self.daily_high is not None:
                self.previous_close = close
            
            # Reset daily levels
            self.daily_high = high
            self.daily_low = low
            self.daily_open = close
            self.current_date = current_date
            
            prev_close_str = f"{self.previous_close:.2f}" if self.previous_close is not None else "N/A"
            logger.info(f"New day: {current_date}, Previous close: {prev_close_str}")
        else:
            # Update daily levels
            if self.daily_high is None or high > self.daily_high:
                self.daily_high = high
            if self.daily_low is None or low < self.daily_low:
                self.daily_low = low
        
        # Check for new week
        if self.current_week != current_week:
            self.weekly_high = high
            self.weekly_low = low
            self.current_week = current_week
            logger.info(f"New week: {current_week}")
        else:
            # Update weekly levels
            if self.weekly_high is None or high > self.weekly_high:
                self.weekly_high = high
            if self.weekly_low is None or low < self.weekly_low:
                self.weekly_low = low
    
    def get_psychological_levels(self, current_price: float, 
                                count: int = 5) -> List[float]:
        """
        Get nearest psychological round number levels.
        
        Args:
            current_price: Current market price
            count: Number of levels above and below to return
            
        Returns:
            List of psychological levels sorted by proximity
        """
        # Find nearest round number
        base = (current_price // self.round_number_interval) * self.round_number_interval
        
        levels = []
        
        # Generate levels above and below
        for i in range(-count, count + 1):
            level = base + (i * self.round_number_interval)
            if level > 0:  # Only positive prices
                levels.append(level)
        
        # Sort by distance from current price
        levels.sort(key=lambda x: abs(x - current_price))
        
        return levels[:count * 2]
    
    def get_nearest_level(self, current_price: float) -> Tuple[float, str, float]:
        """
        Get the nearest key level to current price.
        
        Args:
            current_price: Current market price
            
        Returns:
            Tuple of (level_price, level_type, distance_pips)
        """
        levels = []
        
        # Add daily levels
        if self.daily_high:
            levels.append((self.daily_high, "Daily High", abs(current_price - self.daily_high) * 10))
        if self.daily_low:
            levels.append((self.daily_low, "Daily Low", abs(current_price - self.daily_low) * 10))
        if self.previous_close:
            levels.append((self.previous_close, "Previous Close", abs(current_price - self.previous_close) * 10))
        
        # Add weekly levels
        if self.weekly_high:
            levels.append((self.weekly_high, "Weekly High", abs(current_price - self.weekly_high) * 10))
        if self.weekly_low:
            levels.append((self.weekly_low, "Weekly Low", abs(current_price - self.weekly_low) * 10))
        
        # Add nearest psychological levels
        psych_levels = self.get_psychological_levels(current_price, count=2)
        for level in psych_levels:
            levels.append((level, f"Psychological ${level:.0f}", abs(current_price - level) * 10))
        
        # Sort by distance
        levels.sort(key=lambda x: x[2])
        
        return levels[0] if levels else (current_price, "None", 0.0)
    
    def is_near_level(self, current_price: float, threshold_pips: float = 5.0) -> Tuple[bool, Optional[Dict]]:
        """
        Check if price is near a key level.
        
        Args:
            current_price: Current market price
            threshold_pips: Distance threshold in pips
            
        Returns:
            Tuple of (is_near, level_info)
        """
        nearest_level, level_type, distance_pips = self.get_nearest_level(current_price)
        
        if distance_pips <= threshold_pips:
            return True, {
                'level': nearest_level,
                'type': level_type,
                'distance_pips': round(distance_pips, 1),
                'above': current_price > nearest_level
            }
        
        return False, None
    
    def get_support_resistance(self, current_price: float) -> Dict[str, any]:
        """
        Get nearest support and resistance levels.
        
        Args:
            current_price: Current market price
            
        Returns:
            Dictionary with support and resistance info
        """
        all_levels = []
        
        # Collect all levels
        if self.daily_high:
            all_levels.append(self.daily_high)
        if self.daily_low:
            all_levels.append(self.daily_low)
        if self.previous_close:
            all_levels.append(self.previous_close)
        if self.weekly_high:
            all_levels.append(self.weekly_high)
        if self.weekly_low:
            all_levels.append(self.weekly_low)
        
        # Add psychological levels
        psych_levels = self.get_psychological_levels(current_price, count=3)
        all_levels.extend(psych_levels)
        
        # Separate into support (below) and resistance (above)
        support_levels = [l for l in all_levels if l < current_price]
        resistance_levels = [l for l in all_levels if l > current_price]
        
        # Get nearest
        nearest_support = max(support_levels) if support_levels else None
        nearest_resistance = min(resistance_levels) if resistance_levels else None
        
        return {
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'support_distance_pips': (current_price - nearest_support) * 10 if nearest_support else None,
            'resistance_distance_pips': (nearest_resistance - current_price) * 10 if nearest_resistance else None,
            'all_support': sorted(support_levels, reverse=True)[:3],
            'all_resistance': sorted(resistance_levels)[:3]
        }
    
    def get_level_status(self, current_price: float) -> Dict[str, any]:
        """
        Get comprehensive level status.
        
        Args:
            current_price: Current market price
            
        Returns:
            Dictionary with all level information
        """
        nearest_level, level_type, distance_pips = self.get_nearest_level(current_price)
        is_near, near_info = self.is_near_level(current_price, threshold_pips=5.0)
        sr_info = self.get_support_resistance(current_price)
        
        return {
            'current_price': current_price,
            'daily': {
                'high': self.daily_high,
                'low': self.daily_low,
                'open': self.daily_open,
                'range_pips': (self.daily_high - self.daily_low) * 10 if self.daily_high and self.daily_low else None
            },
            'previous_close': self.previous_close,
            'weekly': {
                'high': self.weekly_high,
                'low': self.weekly_low
            },
            'nearest_level': {
                'price': nearest_level,
                'type': level_type,
                'distance_pips': round(distance_pips, 1)
            },
            'is_near_level': is_near,
            'near_level_info': near_info,
            'support_resistance': sr_info,
            'psychological_levels': self.get_psychological_levels(current_price, count=3)
        }
    
    def get_level_context_for_signal(self, current_price: float, signal_type: str) -> str:
        """
        Generate level context text for signal reasoning.
        
        Args:
            current_price: Current market price
            signal_type: "LONG" or "SHORT"
            
        Returns:
            Formatted string with level context
        """
        is_near, near_info = self.is_near_level(current_price, threshold_pips=5.0)
        sr_info = self.get_support_resistance(current_price)
        
        context_lines = []
        
        if is_near and near_info:
            direction = "above" if near_info['above'] else "below"
            context_lines.append(f"📍 KEY LEVEL: Price {direction} {near_info['type']} at ${near_info['level']:.2f} ({near_info['distance_pips']} pips away)")
            
            if signal_type == "LONG" and not near_info['above']:
                context_lines.append(f"   • Bouncing off support - good for LONG")
            elif signal_type == "SHORT" and near_info['above']:
                context_lines.append(f"   • Rejecting resistance - good for SHORT")
        
        # Add support/resistance context
        if signal_type == "LONG" and sr_info['nearest_support']:
            context_lines.append(f"🛡️ Support: ${sr_info['nearest_support']:.2f} ({sr_info['support_distance_pips']:.1f} pips below)")
        
        if signal_type == "SHORT" and sr_info['nearest_resistance']:
            context_lines.append(f"🎯 Resistance: ${sr_info['nearest_resistance']:.2f} ({sr_info['resistance_distance_pips']:.1f} pips above)")
        
        return "\n".join(context_lines) if context_lines else ""
