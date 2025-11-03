"""
Session Manager for Gold Trading
Handles Asian, London, and New York session detection and management
"""
from datetime import datetime, time, timezone
from enum import Enum
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class TradingSession(Enum):
    """Trading session types."""
    ASIAN = "Asian"
    LONDON = "London"
    NEW_YORK = "New York"
    OVERLAP_LONDON_NY = "London/NY Overlap"
    CLOSED = "Closed"


class SessionManager:
    """
    Manages trading sessions for Gold (XAU/USD).
    
    Session Times (GMT):
    - Asian: 00:00 - 08:00 GMT
    - London: 08:00 - 16:00 GMT
    - New York: 13:00 - 22:00 GMT
    - Overlap: 13:00 - 16:00 GMT (London + NY)
    """
    
    # Session time ranges in GMT
    ASIAN_START = time(0, 0)
    ASIAN_END = time(8, 0)
    
    LONDON_START = time(8, 0)
    LONDON_END = time(16, 0)
    
    NY_START = time(13, 0)
    NY_END = time(22, 0)
    
    # Overlap is when both London and NY are open
    OVERLAP_START = time(13, 0)
    OVERLAP_END = time(16, 0)
    
    def __init__(self):
        """Initialize Session Manager."""
        self.current_session: Optional[TradingSession] = None
        self.last_session_change: Optional[datetime] = None
        
        # Asian range tracking
        self.asian_range_high: Optional[float] = None
        self.asian_range_low: Optional[float] = None
        self.asian_range_date: Optional[str] = None
        self.tracking_asian_range: bool = False
        
        logger.info("SessionManager initialized with GMT timezone")
    
    def get_current_session(self, current_time: Optional[datetime] = None) -> TradingSession:
        """
        Get the current trading session based on GMT time.
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            
        Returns:
            TradingSession enum value
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Ensure we're working with GMT/UTC
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        current_time_gmt = current_time.astimezone(timezone.utc).time()
        
        # Check for overlap first (most active period)
        if self.OVERLAP_START <= current_time_gmt < self.OVERLAP_END:
            session = TradingSession.OVERLAP_LONDON_NY
        
        # Check Asian session
        elif self.ASIAN_START <= current_time_gmt < self.ASIAN_END:
            session = TradingSession.ASIAN
        
        # Check London session
        elif self.LONDON_START <= current_time_gmt < self.LONDON_END:
            session = TradingSession.LONDON
        
        # Check New York session
        elif self.NY_START <= current_time_gmt < self.NY_END:
            session = TradingSession.NEW_YORK
        
        # Market closed
        else:
            session = TradingSession.CLOSED
        
        # Track session changes
        if self.current_session != session:
            old_session = self.current_session
            self.current_session = session
            self.last_session_change = current_time
            
            if old_session is not None:
                logger.info(f"Session changed: {old_session.value} → {session.value}")
        
        return session
    
    def is_active_session(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if we're in an active trading session (not closed).
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            
        Returns:
            True if in active session, False if closed
        """
        session = self.get_current_session(current_time)
        return session != TradingSession.CLOSED
    
    def is_high_volatility_session(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if we're in a high-volatility session (London, NY, or Overlap).
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            
        Returns:
            True if in high-volatility session
        """
        session = self.get_current_session(current_time)
        return session in [
            TradingSession.LONDON,
            TradingSession.NEW_YORK,
            TradingSession.OVERLAP_LONDON_NY
        ]
    
    def get_session_info(self, current_time: Optional[datetime] = None) -> Dict[str, any]:
        """
        Get detailed information about the current session.
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            
        Returns:
            Dictionary with session details
        """
        session = self.get_current_session(current_time)
        
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        info = {
            'session': session.value,
            'is_active': session != TradingSession.CLOSED,
            'is_high_volatility': session in [
                TradingSession.LONDON,
                TradingSession.NEW_YORK,
                TradingSession.OVERLAP_LONDON_NY
            ],
            'current_time_gmt': current_time.strftime('%H:%M:%S GMT'),
            'last_change': self.last_session_change.strftime('%Y-%m-%d %H:%M:%S GMT') if self.last_session_change else None
        }
        
        # Add session-specific recommendations
        if session == TradingSession.ASIAN:
            info['recommendation'] = "Track Asian range for London breakout setup"
            info['strategy_focus'] = "Range tracking"
        elif session == TradingSession.LONDON:
            info['recommendation'] = "Look for Asian range breakouts and EMA cloud setups"
            info['strategy_focus'] = "Breakout trading"
        elif session == TradingSession.NEW_YORK:
            info['recommendation'] = "Continue trend following, watch for reversals"
            info['strategy_focus'] = "Trend continuation"
        elif session == TradingSession.OVERLAP_LONDON_NY:
            info['recommendation'] = "Highest volatility - all strategies active"
            info['strategy_focus'] = "All strategies"
        else:
            info['recommendation'] = "Market closed - no trading"
            info['strategy_focus'] = "None"
        
        return info
    
    def get_time_until_next_session(self, current_time: Optional[datetime] = None) -> Dict[str, any]:
        """
        Calculate time remaining until next session change.
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            
        Returns:
            Dictionary with next session info and time remaining
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        current_session = self.get_current_session(current_time)
        current_time_gmt = current_time.astimezone(timezone.utc).time()
        
        # Determine next session and time
        if current_session == TradingSession.ASIAN:
            next_session = TradingSession.LONDON
            next_time = self.LONDON_START
        elif current_session == TradingSession.LONDON:
            if current_time_gmt < self.OVERLAP_START:
                next_session = TradingSession.OVERLAP_LONDON_NY
                next_time = self.OVERLAP_START
            else:
                next_session = TradingSession.NEW_YORK
                next_time = self.LONDON_END
        elif current_session == TradingSession.OVERLAP_LONDON_NY:
            next_session = TradingSession.NEW_YORK
            next_time = self.OVERLAP_END
        elif current_session == TradingSession.NEW_YORK:
            next_session = TradingSession.CLOSED
            next_time = self.NY_END
        else:  # CLOSED
            next_session = TradingSession.ASIAN
            next_time = self.ASIAN_START
        
        # Calculate time difference
        current_seconds = current_time_gmt.hour * 3600 + current_time_gmt.minute * 60 + current_time_gmt.second
        next_seconds = next_time.hour * 3600 + next_time.minute * 60
        
        if next_seconds > current_seconds:
            seconds_remaining = next_seconds - current_seconds
        else:
            # Next session is tomorrow
            seconds_remaining = (24 * 3600) - current_seconds + next_seconds
        
        hours = seconds_remaining // 3600
        minutes = (seconds_remaining % 3600) // 60
        
        return {
            'current_session': current_session.value,
            'next_session': next_session.value,
            'time_remaining': f"{hours}h {minutes}m",
            'seconds_remaining': seconds_remaining
        }

    
    def update_asian_range(self, high: float, low: float, current_time: Optional[datetime] = None) -> None:
        """
        Update Asian session range with current high/low.
        
        Args:
            high: Current high price
            low: Current low price
            current_time: Optional datetime (defaults to now in GMT)
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        session = self.get_current_session(current_time)
        current_date = current_time.strftime('%Y-%m-%d')
        
        # Only track during Asian session
        if session != TradingSession.ASIAN:
            return
        
        # Reset range if new day
        if self.asian_range_date != current_date:
            self.asian_range_high = high
            self.asian_range_low = low
            self.asian_range_date = current_date
            self.tracking_asian_range = True
            logger.info(f"Started tracking Asian range for {current_date}")
        else:
            # Update range
            if self.asian_range_high is None or high > self.asian_range_high:
                self.asian_range_high = high
            if self.asian_range_low is None or low < self.asian_range_low:
                self.asian_range_low = low
    
    def finalize_asian_range(self, current_time: Optional[datetime] = None) -> Dict[str, any]:
        """
        Finalize Asian range at end of session.
        
        Args:
            current_time: Optional datetime (defaults to now in GMT)
            
        Returns:
            Dictionary with Asian range details
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        session = self.get_current_session(current_time)
        
        # Finalize when transitioning from Asian to London
        if session == TradingSession.LONDON and self.tracking_asian_range:
            self.tracking_asian_range = False
            
            if self.asian_range_high and self.asian_range_low:
                range_pips = (self.asian_range_high - self.asian_range_low) * 10  # Gold pips
                midpoint = (self.asian_range_high + self.asian_range_low) / 2
                
                logger.info(f"Asian range finalized: {self.asian_range_low:.2f} - {self.asian_range_high:.2f} ({range_pips:.1f} pips)")
                
                return {
                    'date': self.asian_range_date,
                    'high': self.asian_range_high,
                    'low': self.asian_range_low,
                    'midpoint': midpoint,
                    'range_pips': range_pips,
                    'finalized': True
                }
        
        return {'finalized': False}
    
    def get_asian_range(self) -> Optional[Dict[str, any]]:
        """
        Get the current Asian range.
        
        Returns:
            Dictionary with Asian range details or None if not available
        """
        if self.asian_range_high is None or self.asian_range_low is None:
            return None
        
        range_pips = (self.asian_range_high - self.asian_range_low) * 10
        midpoint = (self.asian_range_high + self.asian_range_low) / 2
        
        return {
            'date': self.asian_range_date,
            'high': self.asian_range_high,
            'low': self.asian_range_low,
            'midpoint': midpoint,
            'range_pips': range_pips,
            'is_tracking': self.tracking_asian_range
        }
    
    def is_breakout_above_asian_range(self, price: float, buffer_pips: float = 2.0) -> bool:
        """
        Check if price has broken above Asian range.
        
        Args:
            price: Current price
            buffer_pips: Buffer in pips to confirm breakout (default 2 pips)
            
        Returns:
            True if price is above Asian high + buffer
        """
        if self.asian_range_high is None:
            return False
        
        buffer = buffer_pips / 10  # Convert pips to price
        return price > (self.asian_range_high + buffer)
    
    def is_breakout_below_asian_range(self, price: float, buffer_pips: float = 2.0) -> bool:
        """
        Check if price has broken below Asian range.
        
        Args:
            price: Current price
            buffer_pips: Buffer in pips to confirm breakout (default 2 pips)
            
        Returns:
            True if price is below Asian low - buffer
        """
        if self.asian_range_low is None:
            return False
        
        buffer = buffer_pips / 10  # Convert pips to price
        return price < (self.asian_range_low - buffer)
    
    def is_price_in_asian_range(self, price: float) -> bool:
        """
        Check if price is within Asian range.
        
        Args:
            price: Current price
            
        Returns:
            True if price is within range
        """
        if self.asian_range_high is None or self.asian_range_low is None:
            return False
        
        return self.asian_range_low <= price <= self.asian_range_high
