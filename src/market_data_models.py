"""
Market Data Models
Data models for market data with validation
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import pandas as pd
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Market data with OHLCV and indicators"""
    asset: str
    timeframe: str
    timestamp: datetime
    
    # Price data
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # Indicators
    rsi: float
    adx: float
    ema_9: float
    ema_21: float
    ema_50: float
    atr: float
    vwap: float
    volume_ma: float
    
    @property
    def volume_ratio(self) -> float:
        """Calculate volume ratio vs moving average"""
        return self.volume / self.volume_ma if self.volume_ma > 0 else 0
    
    def validate(self) -> bool:
        """
        Check for NaN or invalid values in indicators
        
        Returns:
            True if all values are valid, False otherwise
        """
        # Check for NaN values in critical indicators
        for field_name in ['rsi', 'adx', 'ema_9', 'ema_21', 'ema_50', 'atr', 'vwap']:
            value = getattr(self, field_name)
            if math.isnan(value) or value <= 0:
                logger.warning(f"Invalid {field_name}: {value}")
                return False
        
        # Check price data
        if self.close <= 0 or self.high <= 0 or self.low <= 0:
            logger.warning(f"Invalid price data: close={self.close}, high={self.high}, low={self.low}")
            return False
        
        # Check volume
        if self.volume < 0:
            logger.warning(f"Invalid volume: {self.volume}")
            return False
        
        return True
    
    @classmethod
    def from_series(cls, series: pd.Series, asset: str, timeframe: str) -> Optional['MarketData']:
        """
        Create MarketData from pandas Series
        
        Args:
            series: Pandas Series with OHLCV and indicators
            asset: Asset symbol
            timeframe: Timeframe string
            
        Returns:
            MarketData instance or None if required fields missing
        """
        try:
            # Required fields
            required_fields = [
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'rsi', 'adx', 'ema_9', 'ema_21', 'ema_50', 'atr', 'vwap', 'volume_ma'
            ]
            
            # Check if all required fields exist
            for field in required_fields:
                if field not in series.index:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            # Create instance
            market_data = cls(
                asset=asset,
                timeframe=timeframe,
                timestamp=series['timestamp'],
                open=float(series['open']),
                high=float(series['high']),
                low=float(series['low']),
                close=float(series['close']),
                volume=float(series['volume']),
                rsi=float(series['rsi']),
                adx=float(series['adx']),
                ema_9=float(series['ema_9']),
                ema_21=float(series['ema_21']),
                ema_50=float(series['ema_50']),
                atr=float(series['atr']),
                vwap=float(series['vwap']),
                volume_ma=float(series['volume_ma'])
            )
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error creating MarketData from series: {e}")
            return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'asset': self.asset,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'rsi': self.rsi,
            'adx': self.adx,
            'ema_9': self.ema_9,
            'ema_21': self.ema_21,
            'ema_50': self.ema_50,
            'atr': self.atr,
            'vwap': self.vwap,
            'volume_ma': self.volume_ma,
            'volume_ratio': self.volume_ratio
        }
