"""
Liquidity and Trading Hours Filter
Filters signals based on trading hours and liquidity conditions
"""
import logging
from datetime import datetime, time
from typing import Optional, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


class LiquidityFilter:
    """
    Filters signals based on liquidity and trading hours
    """
    
    # Trading session times (UTC)
    SESSIONS = {
        'London': {
            'start': time(8, 0),  # 8:00 AM UTC
            'end': time(16, 30)   # 4:30 PM UTC
        },
        'NewYork': {
            'start': time(13, 0),  # 1:00 PM UTC (8:00 AM EST)
            'end': time(22, 0)    # 10:00 PM UTC (5:00 PM EST)
        },
        'Tokyo': {
            'start': time(0, 0),   # 12:00 AM UTC
            'end': time(9, 0)      # 9:00 AM UTC
        }
    }
    
    # Major holidays (simplified - would need full calendar in production)
    MAJOR_HOLIDAYS = [
        # Format: (month, day)
        (1, 1),   # New Year's Day
        (12, 25), # Christmas
        (12, 26), # Boxing Day
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize liquidity filter
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        logger.info("Initialized LiquidityFilter")
    
    def is_trading_hours(self, timestamp: datetime, asset_symbol: str, asset_config: Dict) -> bool:
        """
        Check if current time is within trading hours for the asset
        
        Args:
            timestamp: Current timestamp
            asset_symbol: Asset symbol (BTC, XAUUSD, US30)
            asset_config: Asset-specific configuration
            
        Returns:
            True if within trading hours, False otherwise
        """
        # Get trading hours from asset config
        trading_hours = asset_config.get('trading_hours')
        
        # If no trading hours specified, allow 24/7 (like BTC)
        if trading_hours is None:
            return True
        
        # Check if current time is within any of the specified sessions
        current_time = timestamp.time()
        
        for session_name in trading_hours:
            if session_name in self.SESSIONS:
                session = self.SESSIONS[session_name]
                if self._is_time_in_range(current_time, session['start'], session['end']):
                    logger.debug(f"Within {session_name} session for {asset_symbol}")
                    return True
        
        logger.info(f"Outside trading hours for {asset_symbol} - current time: {current_time}, required sessions: {trading_hours}")
        return False
    
    def _is_time_in_range(self, current: time, start: time, end: time) -> bool:
        """Check if current time is within start and end times"""
        if start <= end:
            return start <= current <= end
        else:
            # Handle overnight sessions (e.g., 22:00 to 02:00)
            return current >= start or current <= end
    
    def is_low_liquidity_period(self, timestamp: datetime) -> bool:
        """
        Check if current time is a low liquidity period (weekend or major holiday)
        
        Args:
            timestamp: Current timestamp
            
        Returns:
            True if low liquidity period, False otherwise
        """
        # Check if weekend
        if timestamp.weekday() >= 5:  # Saturday = 5, Sunday = 6
            logger.info(f"Low liquidity - weekend: {timestamp.strftime('%A')}")
            return True
        
        # Check if major holiday
        if (timestamp.month, timestamp.day) in self.MAJOR_HOLIDAYS:
            logger.info(f"Low liquidity - major holiday: {timestamp.strftime('%B %d')}")
            return True
        
        return False
    
    def check_volume_liquidity(self, market_data: pd.DataFrame, min_volume_threshold: float = 0.5) -> bool:
        """
        Check if volume indicates sufficient liquidity
        
        Args:
            market_data: DataFrame with volume data
            min_volume_threshold: Minimum volume ratio (current / MA)
            
        Returns:
            True if sufficient liquidity, False otherwise
        """
        if market_data.empty:
            return False
        
        try:
            last = market_data.iloc[-1]
            
            if 'volume' not in last.index or 'volume_ma' not in last.index:
                logger.warning("Volume data not available for liquidity check")
                return True  # Allow if data not available
            
            volume_ratio = last['volume'] / last['volume_ma'] if last['volume_ma'] > 0 else 0
            
            if volume_ratio < min_volume_threshold:
                logger.info(f"Low liquidity - volume ratio {volume_ratio:.2f}x < {min_volume_threshold}x")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking volume liquidity: {e}")
            return True  # Allow if error
    
    def should_increase_confluence_requirement(self, timestamp: datetime, asset_symbol: str, asset_config: Dict) -> bool:
        """
        Check if confluence requirements should be increased due to low liquidity
        
        For XAU/USD outside London/NY sessions, increase min_confluence_factors to 5
        
        Args:
            timestamp: Current timestamp
            asset_symbol: Asset symbol
            asset_config: Asset-specific configuration
            
        Returns:
            True if should increase requirements, False otherwise
        """
        # Only applies to XAU/USD
        if asset_symbol != 'XAUUSD':
            return False
        
        # Check if outside high-liquidity sessions
        trading_hours = asset_config.get('trading_hours', [])
        if not trading_hours:
            return False
        
        current_time = timestamp.time()
        
        # Check if in any high-liquidity session
        for session_name in trading_hours:
            if session_name in self.SESSIONS:
                session = self.SESSIONS[session_name]
                if self._is_time_in_range(current_time, session['start'], session['end']):
                    return False  # In high-liquidity session, don't increase
        
        # Outside high-liquidity sessions
        logger.info(f"Outside high-liquidity sessions for {asset_symbol} - increasing confluence requirement to 5")
        return True
    
    def filter_signal(self, timestamp: datetime, asset_symbol: str, asset_config: Dict, market_data: Optional[pd.DataFrame] = None) -> tuple[bool, Optional[str]]:
        """
        Filter signal based on liquidity conditions
        
        Args:
            timestamp: Signal timestamp
            asset_symbol: Asset symbol
            asset_config: Asset-specific configuration
            market_data: Optional market data for volume check
            
        Returns:
            Tuple of (allow_signal: bool, rejection_reason: Optional[str])
        """
        # Check for low liquidity periods (weekends, holidays)
        if self.is_low_liquidity_period(timestamp):
            return False, "Low liquidity period (weekend or holiday)"
        
        # Check trading hours
        if not self.is_trading_hours(timestamp, asset_symbol, asset_config):
            return False, f"Outside trading hours for {asset_symbol}"
        
        # Check volume-based liquidity
        if market_data is not None:
            if not self.check_volume_liquidity(market_data):
                return False, "Insufficient volume liquidity"
        
        # Signal passes all liquidity checks
        return True, None
