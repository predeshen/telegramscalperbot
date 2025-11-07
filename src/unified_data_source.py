"""
Unified Data Source Layer
Provides consistent market data across all scanners with validation and MT5-compatible pricing
"""
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.yfinance_client import YFinanceClient


logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Retry configuration for data source"""
    max_retries: int = 5
    initial_delay_seconds: int = 1
    max_delay_seconds: int = 60
    exponential_base: float = 2.0


@dataclass
class DataSourceConfig:
    """Configuration for unified data source"""
    provider: str = "yfinance"
    symbol_map: Dict[str, str] = None
    retry_config: RetryConfig = None
    
    def __post_init__(self):
        if self.symbol_map is None:
            self.symbol_map = {
                "BTC": "BTC-USD",
                "XAUUSD": "GC=F",
                "US30": "^DJI"
            }
        if self.retry_config is None:
            self.retry_config = RetryConfig()


class DataSourceError(Exception):
    """Exception raised for data source errors"""
    pass


class UnifiedDataSource:
    """
    Unified data source interface for all scanners
    Provides consistent market data with validation and retry logic
    """
    
    def __init__(self, config: DataSourceConfig):
        """
        Initialize unified data source
        
        Args:
            config: DataSourceConfig with provider and symbol mapping
        """
        self.config = config
        self.provider = config.provider
        self.symbol_map = config.symbol_map
        self.retry_config = config.retry_config
        
        # Client instances per symbol
        self.clients: Dict[str, YFinanceClient] = {}
        
        logger.info(f"Initialized UnifiedDataSource with provider: {self.provider}")
        logger.info(f"Symbol mapping: {self.symbol_map}")
    
    def get_yfinance_symbol(self, internal_symbol: str) -> str:
        """
        Map internal symbol to Yahoo Finance symbol
        
        Args:
            internal_symbol: Internal symbol (BTC, XAUUSD, US30)
            
        Returns:
            Yahoo Finance symbol (BTC-USD, GC=F, ^DJI)
            
        Raises:
            ValueError: If symbol not found in mapping
        """
        if internal_symbol not in self.symbol_map:
            raise ValueError(f"Unknown symbol: {internal_symbol}. Available: {list(self.symbol_map.keys())}")
        
        return self.symbol_map[internal_symbol]
    
    def connect(self, symbol: str, timeframes: List[str]) -> bool:
        """
        Connect to data source for a specific symbol
        
        Args:
            symbol: Internal symbol (BTC, XAUUSD, US30)
            timeframes: List of timeframes to monitor
            
        Returns:
            True if connection successful
            
        Raises:
            DataSourceError: If connection fails after retries
        """
        yf_symbol = self.get_yfinance_symbol(symbol)
        
        # Create client if doesn't exist
        if symbol not in self.clients:
            self.clients[symbol] = YFinanceClient(
                symbol=yf_symbol,
                timeframes=timeframes,
                buffer_size=500
            )
        
        # Attempt connection with retry
        success = self._connect_with_retry(symbol)
        
        if not success:
            raise DataSourceError(f"Failed to connect to data source for {symbol} after {self.retry_config.max_retries} attempts")
        
        return True
    
    def _connect_with_retry(self, symbol: str) -> bool:
        """
        Attempt connection with exponential backoff
        
        Args:
            symbol: Internal symbol
            
        Returns:
            True if connection successful
        """
        client = self.clients[symbol]
        
        for attempt in range(self.retry_config.max_retries):
            try:
                if client.connect():
                    logger.info(f"Connected to data source for {symbol}")
                    return True
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1}/{self.retry_config.max_retries} failed for {symbol}: {e}")
            
            # Calculate backoff delay
            if attempt < self.retry_config.max_retries - 1:
                delay = min(
                    self.retry_config.initial_delay_seconds * (self.retry_config.exponential_base ** attempt),
                    self.retry_config.max_delay_seconds
                )
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
        
        return False
    
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """
        Fetch OHLCV data with validation and retry logic
        
        Args:
            symbol: Internal symbol (BTC, XAUUSD, US30)
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with validated candle data including symbol context
            
        Raises:
            DataSourceError: If connection fails after retries
            ValueError: If data validation fails
        """
        if symbol not in self.clients:
            raise DataSourceError(f"No client initialized for {symbol}. Call connect() first.")
        
        client = self.clients[symbol]
        
        # Check connection
        if not client.is_connected():
            logger.warning(f"Client not connected for {symbol}, attempting reconnection...")
            if not self.reconnect_with_backoff(symbol):
                raise DataSourceError(f"Failed to reconnect for {symbol}")
        
        # Fetch data with retry
        for attempt in range(self.retry_config.max_retries):
            try:
                df = client.get_latest_candles(timeframe, count=limit)
                
                if df.empty:
                    raise ValueError(f"Empty DataFrame returned for {symbol} {timeframe}")
                
                # Add symbol context to DataFrame
                df['symbol'] = symbol
                
                logger.debug(f"Fetched {len(df)} candles for {symbol} {timeframe}")
                return df
                
            except Exception as e:
                logger.error(f"Fetch attempt {attempt + 1}/{self.retry_config.max_retries} failed for {symbol} {timeframe}: {e}")
                
                if attempt < self.retry_config.max_retries - 1:
                    # Try to reconnect
                    if not self.reconnect_with_backoff(symbol):
                        continue
                    
                    # Calculate backoff delay
                    delay = min(
                        self.retry_config.initial_delay_seconds * (self.retry_config.exponential_base ** attempt),
                        self.retry_config.max_delay_seconds
                    )
                    time.sleep(delay)
                else:
                    raise DataSourceError(f"Failed to fetch data for {symbol} {timeframe} after {self.retry_config.max_retries} attempts: {e}")
        
        raise DataSourceError(f"Failed to fetch data for {symbol} {timeframe}")
    
    def reconnect_with_backoff(self, symbol: str, max_retries: Optional[int] = None) -> bool:
        """
        Attempt reconnection with exponential backoff
        
        Args:
            symbol: Internal symbol
            max_retries: Override default max retries
            
        Returns:
            True if reconnection successful
        """
        if max_retries is None:
            max_retries = self.retry_config.max_retries
        
        if symbol not in self.clients:
            logger.error(f"No client found for {symbol}")
            return False
        
        client = self.clients[symbol]
        
        logger.info(f"Attempting to reconnect for {symbol}...")
        
        for attempt in range(max_retries):
            try:
                # Calculate backoff delay
                delay = min(
                    self.retry_config.initial_delay_seconds * (self.retry_config.exponential_base ** attempt),
                    self.retry_config.max_delay_seconds
                )
                
                if attempt > 0:
                    logger.info(f"Reconnection attempt {attempt + 1}/{max_retries} in {delay:.1f}s...")
                    time.sleep(delay)
                
                if client.reconnect(max_attempts=1):
                    logger.info(f"Successfully reconnected for {symbol}")
                    return True
                    
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed for {symbol}: {e}")
        
        logger.error(f"Failed to reconnect for {symbol} after {max_retries} attempts")
        return False
    
    def is_connected(self, symbol: str) -> bool:
        """
        Check if connected for a specific symbol
        
        Args:
            symbol: Internal symbol
            
        Returns:
            True if connected
        """
        if symbol not in self.clients:
            return False
        
        return self.clients[symbol].is_connected()
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        
        Args:
            symbol: Internal symbol
            
        Returns:
            Current price or None if not available
        """
        if symbol not in self.clients:
            return None
        
        return self.clients[symbol].get_current_price()
    
    def close(self, symbol: Optional[str] = None) -> None:
        """
        Close connection for symbol(s)
        
        Args:
            symbol: Internal symbol, or None to close all
        """
        if symbol:
            if symbol in self.clients:
                self.clients[symbol].close()
                logger.info(f"Closed connection for {symbol}")
        else:
            for sym, client in self.clients.items():
                client.close()
            logger.info("Closed all connections")
