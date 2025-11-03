"""
Spread Monitor for Gold Trading
Tracks bid-ask spread and pauses trading when spread is too wide
"""
from collections import deque
from datetime import datetime, timezone
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SpreadMonitor:
    """
    Monitors bid-ask spread for Gold (XAU/USD).
    
    Spread thresholds:
    - Normal: < 10 pips
    - Warning: 10-15 pips
    - Too wide: > 15 pips (pause trading)
    """
    
    def __init__(self, 
                 acceptable_spread_pips: float = 10.0,
                 pause_spread_pips: float = 15.0,
                 history_size: int = 100):
        """
        Initialize Spread Monitor.
        
        Args:
            acceptable_spread_pips: Maximum acceptable spread in pips
            pause_spread_pips: Spread threshold to pause trading
            history_size: Number of spread readings to keep
        """
        self.acceptable_spread_pips = acceptable_spread_pips
        self.pause_spread_pips = pause_spread_pips
        
        self.current_spread_pips: Optional[float] = None
        self.current_bid: Optional[float] = None
        self.current_ask: Optional[float] = None
        self.last_update: Optional[datetime] = None
        
        # Spread history for statistics
        self.spread_history: deque = deque(maxlen=history_size)
        
        logger.info(f"SpreadMonitor initialized (acceptable: {acceptable_spread_pips} pips, pause: {pause_spread_pips} pips)")
    
    def update_spread(self, bid: float, ask: float, timestamp: Optional[datetime] = None) -> float:
        """
        Update current spread with bid/ask prices.
        
        Args:
            bid: Current bid price
            ask: Current ask price
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Spread in pips
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        self.current_bid = bid
        self.current_ask = ask
        self.last_update = timestamp
        
        # Calculate spread in pips (Gold: 1 pip = 0.1)
        spread_price = ask - bid
        self.current_spread_pips = spread_price * 10
        
        # Add to history
        self.spread_history.append({
            'timestamp': timestamp,
            'spread_pips': self.current_spread_pips,
            'bid': bid,
            'ask': ask
        })
        
        # Log warnings for wide spreads
        if self.current_spread_pips > self.pause_spread_pips:
            logger.warning(f"Spread too wide: {self.current_spread_pips:.1f} pips (bid: {bid:.2f}, ask: {ask:.2f})")
        elif self.current_spread_pips > self.acceptable_spread_pips:
            logger.info(f"Spread elevated: {self.current_spread_pips:.1f} pips")
        
        return self.current_spread_pips
    
    def is_spread_acceptable(self) -> bool:
        """
        Check if current spread is acceptable for trading.
        
        Returns:
            True if spread <= acceptable threshold
        """
        if self.current_spread_pips is None:
            return False
        
        return self.current_spread_pips <= self.acceptable_spread_pips
    
    def should_pause_trading(self) -> tuple[bool, Optional[str]]:
        """
        Determine if trading should be paused due to wide spread.
        
        Returns:
            Tuple of (should_pause, reason)
        """
        if self.current_spread_pips is None:
            return True, "No spread data available"
        
        if self.current_spread_pips > self.pause_spread_pips:
            reason = f"Spread too wide: {self.current_spread_pips:.1f} pips (max: {self.pause_spread_pips} pips)"
            return True, reason
        
        return False, None
    
    def get_spread_status(self) -> Dict[str, any]:
        """
        Get comprehensive spread status.
        
        Returns:
            Dictionary with spread details
        """
        if self.current_spread_pips is None:
            return {
                'available': False,
                'message': 'No spread data'
            }
        
        # Calculate statistics from history
        avg_spread = None
        min_spread = None
        max_spread = None
        
        if self.spread_history:
            spreads = [s['spread_pips'] for s in self.spread_history]
            avg_spread = sum(spreads) / len(spreads)
            min_spread = min(spreads)
            max_spread = max(spreads)
        
        # Determine status
        if self.current_spread_pips <= self.acceptable_spread_pips:
            status = "good"
            status_emoji = "✅"
        elif self.current_spread_pips <= self.pause_spread_pips:
            status = "elevated"
            status_emoji = "⚠️"
        else:
            status = "too_wide"
            status_emoji = "🛑"
        
        return {
            'available': True,
            'current_pips': round(self.current_spread_pips, 1),
            'bid': self.current_bid,
            'ask': self.current_ask,
            'status': status,
            'status_emoji': status_emoji,
            'is_acceptable': self.is_spread_acceptable(),
            'should_pause': self.should_pause_trading()[0],
            'thresholds': {
                'acceptable': self.acceptable_spread_pips,
                'pause': self.pause_spread_pips
            },
            'statistics': {
                'average_pips': round(avg_spread, 1) if avg_spread else None,
                'min_pips': round(min_spread, 1) if min_spread else None,
                'max_pips': round(max_spread, 1) if max_spread else None,
                'samples': len(self.spread_history)
            },
            'last_update': self.last_update.strftime('%H:%M:%S GMT') if self.last_update else None
        }
    
    def get_average_spread(self, minutes: int = 5) -> Optional[float]:
        """
        Get average spread over last N minutes.
        
        Args:
            minutes: Number of minutes to average
            
        Returns:
            Average spread in pips or None
        """
        if not self.spread_history:
            return None
        
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        recent_spreads = [
            s['spread_pips'] for s in self.spread_history
            if s['timestamp'] >= cutoff
        ]
        
        if not recent_spreads:
            return None
        
        return sum(recent_spreads) / len(recent_spreads)
    
    def calculate_spread_cost(self, position_size: float) -> float:
        """
        Calculate the cost of spread for a given position size.
        
        Args:
            position_size: Position size in lots (1 lot = 100 oz)
            
        Returns:
            Spread cost in USD
        """
        if self.current_spread_pips is None:
            return 0.0
        
        # For Gold: 1 pip = $10 per lot
        spread_cost = self.current_spread_pips * position_size * 10
        
        return spread_cost
    
    def is_spread_widening(self, threshold_pips: float = 2.0) -> bool:
        """
        Check if spread is widening compared to recent average.
        
        Args:
            threshold_pips: Threshold for widening detection
            
        Returns:
            True if current spread is significantly wider than average
        """
        if self.current_spread_pips is None or len(self.spread_history) < 10:
            return False
        
        avg_spread = self.get_average_spread(minutes=5)
        
        if avg_spread is None:
            return False
        
        return self.current_spread_pips > (avg_spread + threshold_pips)


from datetime import timedelta  # Add missing import
