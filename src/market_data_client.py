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


# Default freshness thresholds for each timeframe (in seconds)
# These are set to allow for real-world API delays while still catching truly stale data
FRESHNESS_THRESHOLDS = {
    '1m': 300,     # 5 minutes (allows for API delays)
    '5m': 600,     # 10 minutes
    '15m': 1800,   # 30 minutes
    '1h': 7200,    # 2 hours
    '4h': 21600,   # 6 hours
    '1d': 129600   # 36 hours
}


class MarketDataClient:
    """
    Manages connection to cryptocurrency exchange and maintains real-time candlestick buffers.
    
    Supports both REST API (historical data) and WebSocket (real-time streaming).
    """
    
    def __init__(self, exchange_name: str, symbol: str, timeframes: List[str], buffer_size: int = 500):
        """
        Initialize market data client.
        
        Args:
            exchange_name: Name of exchange (e.g., 'binance')
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframes: List of timeframes to monitor (e.g., ['1m', '5m'])
            buffer_size: Maximum number of candles to keep in memory per timeframe (default: 500)
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
    
    def validate_data_freshness(
        self, 
        df: pd.DataFrame, 
        timeframe: str, 
        max_age_seconds: Optional[int] = None
    ) -> tuple[bool, float]:
        """
        Validate that the latest candle is fresh enough for the given timeframe.
        
        Args:
            df: DataFrame with candlestick data
            timeframe: Timeframe string (e.g., '1m', '5m')
            max_age_seconds: Maximum acceptable age in seconds (optional, auto-calculated if None)
            
        Returns:
            Tuple of (is_fresh: bool, age_seconds: float)
        """
        if df.empty:
            logger.warning(f"Cannot validate freshness: DataFrame is empty for {timeframe}")
            return False, float('inf')
        
        # Get the latest candle timestamp
        latest_timestamp = df.iloc[-1]['timestamp']
        
        # Convert to datetime if needed
        if not isinstance(latest_timestamp, datetime):
            try:
                latest_timestamp = pd.to_datetime(latest_timestamp)
            except Exception as e:
                logger.error(f"Failed to convert timestamp to datetime: {e}")
                return False, float('inf')
        
        # Calculate age in seconds
        # pd.to_datetime with unit='ms' creates UTC timestamps
        # So we need to use UTC time for comparison
        from datetime import timezone
        current_time = datetime.now(timezone.utc)
        
        # Ensure both timestamps are timezone-naive for comparison
        if latest_timestamp.tzinfo is not None:
            latest_timestamp = latest_timestamp.replace(tzinfo=None)
        if current_time.tzinfo is not None:
            current_time = current_time.replace(tzinfo=None)
        
        age_seconds = (current_time - latest_timestamp).total_seconds()
        
        # Determine threshold
        if max_age_seconds is None:
            # Use default threshold for timeframe
            threshold = FRESHNESS_THRESHOLDS.get(timeframe, 300)  # Default 5 minutes
        else:
            threshold = max_age_seconds
        
        is_fresh = age_seconds < threshold
        
        # Log freshness check result
        logger.debug(
            f"Freshness check for {timeframe}: age={age_seconds:.1f}s, "
            f"threshold={threshold}s, fresh={is_fresh}"
        )
        
        if not is_fresh:
            logger.warning(
                f"Stale data detected for {timeframe}: "
                f"age={age_seconds:.1f}s exceeds threshold={threshold}s"
            )
        
        return is_fresh, age_seconds
    
    def get_latest_candles(
        self, 
        timeframe: str, 
        count: int = 500,
        validate_freshness: bool = True
    ) -> tuple[pd.DataFrame, bool]:
        """
        Fetch historical candlesticks from exchange via REST API with optional freshness validation.
        
        Args:
            timeframe: Timeframe string (e.g., '1m', '5m')
            count: Number of candles to fetch (default: 500)
            validate_freshness: Whether to validate data freshness (default: True)
            
        Returns:
            Tuple of (DataFrame with OHLCV data, is_fresh: bool)
            If validate_freshness is False, is_fresh will always be True
            
        Raises:
            RuntimeError: If not connected to exchange
            ValueError: If fetched data is invalid
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
            
            # Validate fetched data
            if not ohlcv:
                logger.error(f"No data returned from exchange for {timeframe}")
                raise ValueError(f"No data returned from exchange for {timeframe}")
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Validate DataFrame
            if df.empty:
                logger.error(f"Empty DataFrame after conversion for {timeframe}")
                raise ValueError(f"Empty DataFrame for {timeframe}")
            
            # Check for required columns
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing columns in fetched data: {missing_columns}")
                raise ValueError(f"Missing columns: {', '.join(missing_columns)}")
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Check for NaN values in OHLCV columns
            ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in ohlcv_cols:
                nan_count = df[col].isna().sum()
                if nan_count > 0:
                    logger.warning(f"{nan_count} NaN values found in '{col}' column for {timeframe}")
            
            # Log data quality
            if len(df) < count:
                logger.warning(f"Requested {count} candles but got {len(df)} for {timeframe}")
            
            # Update buffer
            with self.buffer_locks[timeframe]:
                self.buffers[timeframe].clear()
                for _, row in df.iterrows():
                    self.buffers[timeframe].append(row.to_dict())
            
            # Validate freshness if requested
            is_fresh = True
            if validate_freshness:
                is_fresh, age_seconds = self.validate_data_freshness(df, timeframe)
                if not is_fresh:
                    logger.warning(
                        f"Fetched data for {timeframe} is stale: age={age_seconds:.1f}s"
                    )
            
            logger.info(f"Fetched {len(df)} candles for {timeframe} (requested: {count}, fresh: {is_fresh})")
            return df, is_fresh
            
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
                        _, _ = self.get_latest_candles(tf, self.buffer_size, validate_freshness=False)
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
