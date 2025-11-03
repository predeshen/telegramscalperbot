"""Market data client for fetching and streaming BTC/USD price data."""
import ccxt
import pandas as pd
import threading
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


class MarketDataClient:
    """
    Manages connection to cryptocurrency exchange and maintains real-time candlestick buffers.
    
    Supports both REST API (historical data) and WebSocket (real-time streaming).
    """
    
    def __init__(self, exchange_name: str, symbol: str, timeframes: List[str], buffer_size: int = 200):
        """
        Initialize market data client.
        
        Args:
            exchange_name: Name of exchange (e.g., 'binance')
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframes: List of timeframes to monitor (e.g., ['1m', '5m'])
            buffer_size: Maximum number of candles to keep in memory per timeframe
        """
        self.exchange_name = exchange_name
        self.symbol = symbol
        self.timeframes = timeframes
        self.buffer_size = buffer_size
        
        # Initialize exchange
        self.exchange = None
        self._connected = False
        
        # Thread-safe candlestick buffers
        self.buffers: Dict[str, deque] = {}
        self.buffer_locks: Dict[str, threading.Lock] = {}
        
        for tf in timeframes:
            self.buffers[tf] = deque(maxlen=buffer_size)
            self.buffer_locks[tf] = threading.Lock()
        
        logger.info(f"Initialized MarketDataClient for {symbol} on {exchange_name}")
    
    def connect(self) -> bool:
        """
        Establish connection to exchange.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initialize CCXT exchange
            exchange_class = getattr(ccxt, self.exchange_name)
            self.exchange = exchange_class({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
            
            # Test connection by fetching markets
            self.exchange.load_markets()
            
            # Verify symbol exists
            if self.symbol not in self.exchange.markets:
                logger.error(f"Symbol {self.symbol} not found on {self.exchange_name}")
                return False
            
            self._connected = True
            logger.info(f"Successfully connected to {self.exchange_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_name}: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected to exchange."""
        return self._connected
    
    def get_latest_candles(self, timeframe: str, count: int = 200) -> pd.DataFrame:
        """
        Fetch historical candlesticks from exchange via REST API.
        
        Args:
            timeframe: Timeframe string (e.g., '1m', '5m')
            count: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data and timestamp
            
        Raises:
            RuntimeError: If not connected to exchange
        """
        if not self._connected or self.exchange is None:
            raise RuntimeError("Not connected to exchange. Call connect() first.")
        
        try:
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=self.symbol,
                timeframe=timeframe,
                limit=count
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
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
        Attempt to reconnect to exchange with exponential backoff.
        
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
        """Close exchange connection and cleanup resources."""
        self._connected = False
        self.exchange = None
        logger.info("Market data client closed")
