"""
YFinance Market Data Client for Gold (XAU/USD)
Fetches real Gold spot prices using Yahoo Finance
"""
import yfinance as yf
import pandas as pd
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


class YFinanceClient:
    """
    Market data client using Yahoo Finance for Gold and other assets.
    
    Compatible with the MarketDataClient interface but uses yfinance backend.
    """
    
    def __init__(self, symbol: str, timeframes: List[str], buffer_size: int = 200):
        """
        Initialize YFinance client.
        
        Args:
            symbol: Yahoo Finance symbol (e.g., 'GC=F' for Gold Futures, 'XAUUSD=X' for Gold Spot)
            timeframes: List of timeframes to monitor (e.g., ['1m', '5m', '15m', '1h', '4h', '1d'])
            buffer_size: Maximum number of candles to keep in memory per timeframe
        """
        self.symbol = symbol
        self.timeframes = timeframes
        self.buffer_size = buffer_size
        
        # Initialize ticker
        self.ticker = None
        self._connected = False
        
        # Thread-safe candlestick buffers
        self.buffers: Dict[str, deque] = {}
        self.buffer_locks: Dict[str, threading.Lock] = {}
        
        for tf in timeframes:
            self.buffers[tf] = deque(maxlen=buffer_size)
            self.buffer_locks[tf] = threading.Lock()
        
        # Timeframe mapping (yfinance uses different notation)
        self.timeframe_map = {
            '1m': '1m',
            '2m': '2m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '90m': '90m',
            '4h': '4h',
            '1d': '1d',
            '5d': '5d',
            '1wk': '1wk',
            '1mo': '1mo',
            '3mo': '3mo'
        }
        
        logger.info(f"Initialized YFinanceClient for {symbol}")
    
    def connect(self) -> bool:
        """
        Establish connection to Yahoo Finance.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initialize ticker
            self.ticker = yf.Ticker(self.symbol)
            
            # Test connection by fetching info
            info = self.ticker.info
            
            if info and 'symbol' in info:
                self._connected = True
                logger.info(f"Successfully connected to Yahoo Finance for {self.symbol}")
                return True
            else:
                logger.warning(f"Connected but no info available for {self.symbol}")
                self._connected = True  # Still allow connection
                return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Yahoo Finance: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected
    
    def get_latest_candles(self, timeframe: str, count: int = 200) -> pd.DataFrame:
        """
        Fetch historical candlesticks from Yahoo Finance.
        
        Args:
            timeframe: Timeframe string (e.g., '1m', '5m', '1h', '1d')
            count: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data and timestamp
            
        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self.ticker is None:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            # Map timeframe
            yf_interval = self.timeframe_map.get(timeframe, timeframe)
            
            # Determine period based on timeframe and count
            period = self._calculate_period(timeframe, count)
            
            # Fetch data
            df = self.ticker.history(period=period, interval=yf_interval)
            
            if df.empty:
                logger.warning(f"No data returned for {timeframe}")
                return pd.DataFrame()
            
            # Rename columns to match our format
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Reset index to get timestamp as column
            df = df.reset_index()
            df = df.rename(columns={'Date': 'timestamp', 'Datetime': 'timestamp'})
            
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Select only needed columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Take last 'count' rows
            df = df.tail(count)
            
            # Update buffer
            with self.buffer_locks[timeframe]:
                self.buffers[timeframe].clear()
                for _, row in df.iterrows():
                    self.buffers[timeframe].append(row.to_dict())
            
            logger.info(f"Fetched {len(df)} candles for {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch candles for {timeframe}: {e}")
            raise
    
    def _calculate_period(self, timeframe: str, count: int) -> str:
        """
        Calculate the period parameter for yfinance based on timeframe and count.
        
        Args:
            timeframe: Timeframe string
            count: Number of candles needed
            
        Returns:
            Period string for yfinance (e.g., '1d', '5d', '1mo', '3mo', '1y', '2y', 'max')
        """
        # Estimate total time needed
        timeframe_minutes = {
            '1m': 1,
            '2m': 2,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '90m': 90,
            '4h': 240,
            '1d': 1440,
            '5d': 7200,
            '1wk': 10080,
            '1mo': 43200
        }
        
        minutes_needed = timeframe_minutes.get(timeframe, 60) * count
        days_needed = minutes_needed / 1440
        
        # Map to yfinance periods
        if days_needed <= 1:
            return '1d'
        elif days_needed <= 5:
            return '5d'
        elif days_needed <= 30:
            return '1mo'
        elif days_needed <= 90:
            return '3mo'
        elif days_needed <= 180:
            return '6mo'
        elif days_needed <= 365:
            return '1y'
        elif days_needed <= 730:
            return '2y'
        elif days_needed <= 1825:
            return '5y'
        else:
            return 'max'
    
    def get_buffer_data(self, timeframe: str) -> pd.DataFrame:
        """
        Get current buffer data as DataFrame.
        
        Args:
            timeframe: Timeframe string
            
        Returns:
            DataFrame with buffered candlestick data
        """
        with self.buffer_locks[timeframe]:
            if not self.buffers[timeframe]:
                return pd.DataFrame()
            
            df = pd.DataFrame(list(self.buffers[timeframe]))
            return df
    
    def update_buffer(self, timeframe: str, candle: dict) -> None:
        """
        Update buffer with new candle data (thread-safe).
        
        Args:
            timeframe: Timeframe string
            candle: Dictionary with OHLCV data
        """
        with self.buffer_locks[timeframe]:
            # Check if this is an update to the last candle or a new candle
            if self.buffers[timeframe]:
                last_candle = self.buffers[timeframe][-1]
                
                # If timestamps match, update the last candle
                if last_candle['timestamp'] == candle['timestamp']:
                    self.buffers[timeframe][-1] = candle
                else:
                    # New candle
                    self.buffers[timeframe].append(candle)
            else:
                # First candle
                self.buffers[timeframe].append(candle)
    
    def reconnect(self, max_attempts: int = 5) -> bool:
        """
        Attempt to reconnect with exponential backoff.
        
        Args:
            max_attempts: Maximum number of reconnection attempts
            
        Returns:
            True if reconnection successful, False otherwise
        """
        backoff_delays = [1, 2, 4, 8, 16]  # seconds
        
        for attempt in range(max_attempts):
            delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
            
            logger.info(f"Reconnection attempt {attempt + 1}/{max_attempts} in {delay}s...")
            time.sleep(delay)
            
            if self.connect():
                logger.info("Reconnection successful")
                
                # Refetch candles to ensure continuity
                try:
                    for tf in self.timeframes:
                        self.get_latest_candles(tf, self.buffer_size)
                    return True
                except Exception as e:
                    logger.error(f"Failed to refetch candles after reconnection: {e}")
                    self._connected = False
                    continue
        
        logger.error(f"Failed to reconnect after {max_attempts} attempts")
        return False
    
    def get_last_update_time(self, timeframe: str) -> Optional[datetime]:
        """
        Get timestamp of last candle in buffer.
        
        Args:
            timeframe: Timeframe string
            
        Returns:
            Datetime of last candle, or None if buffer is empty
        """
        with self.buffer_locks[timeframe]:
            if not self.buffers[timeframe]:
                return None
            return self.buffers[timeframe][-1]['timestamp']
    
    def close(self) -> None:
        """Close connection and cleanup resources."""
        self._connected = False
        self.ticker = None
        logger.info("YFinance client closed")
    
    def get_current_price(self) -> Optional[float]:
        """
        Get current price (latest close).
        
        Returns:
            Current price or None if not available
        """
        try:
            if not self._connected or self.ticker is None:
                return None
            
            # Get latest data
            df = self.ticker.history(period='1d', interval='1m')
            
            if not df.empty:
                return float(df['Close'].iloc[-1])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get current price: {e}")
            return None
