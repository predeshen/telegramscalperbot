"""
Unified Data Source Layer with Multi-Provider Fallback
Provides consistent market data across all scanners with validation, retry logic, and automatic fallback.

Data Source Priority:
1. Binance (primary, real-time, no limits)
2. Twelve Data (backup, reliable, rate-limited)
3. Alpha Vantage (fallback, slower, rate-limited)
4. MT5 (fallback, local)
5. Cached data (last resort)
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Retry configuration for data source"""
    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 8.0
    backoff_multiplier: float = 2.0


@dataclass
class DataSourceConfig:
    """Configuration for unified data source"""
    primary_source: str = "binance"
    fallback_sources: List[str] = field(default_factory=lambda: ["twelve_data", "alpha_vantage", "mt5"])
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    freshness_threshold_seconds: int = 300  # 5 minutes
    cache_enabled: bool = True
    
    # API Keys
    alpha_vantage_key: Optional[str] = None
    twelve_data_key: Optional[str] = None
    
    # Symbol mapping
    symbol_map: Dict[str, str] = field(default_factory=lambda: {
        "BTC": "BTC/USDT",
        "XAUUSD": "XAUUSD",
        "US30": "US30",
        "US100": "US100"
    })


class DataSourceError(Exception):
    """Exception raised for data source errors"""
    pass


class DataSourceCache:
    """Simple cache for market data with TTL"""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time-to-live for cached data
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}
    
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """
        Get cached data if not expired
        
        Args:
            key: Cache key (symbol_timeframe)
            
        Returns:
            DataFrame if cached and not expired, None otherwise
        """
        if key not in self.cache:
            return None
        
        df, timestamp = self.cache[key]
        age_seconds = (datetime.now() - timestamp).total_seconds()
        
        if age_seconds > self.ttl_seconds:
            del self.cache[key]
            return None
        
        logger.debug(f"Cache hit for {key} (age: {age_seconds:.1f}s)")
        return df
    
    def set(self, key: str, df: pd.DataFrame) -> None:
        """
        Cache data
        
        Args:
            key: Cache key (symbol_timeframe)
            df: DataFrame to cache
        """
        self.cache[key] = (df, datetime.now())
        logger.debug(f"Cached {key}")
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache
        
        Args:
            key: Specific key to clear, or None to clear all
        """
        if key:
            if key in self.cache:
                del self.cache[key]
        else:
            self.cache.clear()


class UnifiedDataSource:
    """
    Unified data source interface for all scanners with multi-provider fallback.
    
    Features:
    - Automatic fallback between data sources
    - Exponential backoff retry logic
    - Data freshness validation
    - Caching for resilience
    - Per-source connection tracking
    """
    
    def __init__(self, config: DataSourceConfig):
        """
        Initialize unified data source
        
        Args:
            config: DataSourceConfig with provider settings
        """
        self.config = config
        self.cache = DataSourceCache(ttl_seconds=config.freshness_threshold_seconds)
        
        # Track data source status
        self.source_status: Dict[str, bool] = {}
        self.source_last_success: Dict[str, datetime] = {}
        self.source_failure_count: Dict[str, int] = {}
        
        # Initialize all sources as available
        all_sources = [config.primary_source] + config.fallback_sources
        for source in all_sources:
            self.source_status[source] = True
            self.source_failure_count[source] = 0
        
        # Client instances per source
        self.clients: Dict[str, any] = {}
        
        logger.info(f"Initialized UnifiedDataSource")
        logger.info(f"Primary source: {config.primary_source}")
        logger.info(f"Fallback sources: {config.fallback_sources}")
        logger.info(f"Freshness threshold: {config.freshness_threshold_seconds}s")
    
    def get_latest_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        validate_freshness: bool = True
    ) -> Tuple[pd.DataFrame, bool]:
        """
        Fetch latest candles with automatic fallback between data sources.
        
        Args:
            symbol: Trading symbol (BTC, XAUUSD, US30, US100)
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            validate_freshness: Whether to validate data freshness
            
        Returns:
            Tuple of (DataFrame with candles, is_fresh: bool)
            
        Raises:
            DataSourceError: If all sources fail and no cached data available
        """
        cache_key = f"{symbol}_{timeframe}"
        
        # Try to get data from primary and fallback sources
        all_sources = [self.config.primary_source] + self.config.fallback_sources
        
        for source in all_sources:
            # Skip disabled sources
            if not self.source_status.get(source, False):
                logger.debug(f"Skipping disabled source: {source}")
                continue
            
            try:
                logger.debug(f"Attempting to fetch {symbol} {timeframe} from {source}")
                df = self._fetch_from_source(source, symbol, timeframe, limit)
                
                if df is not None and not df.empty:
                    # Validate freshness if requested
                    is_fresh = True
                    if validate_freshness:
                        is_fresh = self._validate_freshness(df, timeframe)
                    
                    # Cache the data
                    if self.config.cache_enabled:
                        self.cache.set(cache_key, df)
                    
                    # Update source status
                    self.source_status[source] = True
                    self.source_last_success[source] = datetime.now()
                    self.source_failure_count[source] = 0
                    
                    logger.info(f"Successfully fetched {len(df)} candles from {source} (fresh: {is_fresh})")
                    return df, is_fresh
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {source}: {e}")
                self.source_failure_count[source] = self.source_failure_count.get(source, 0) + 1
                
                # Disable source after 3 consecutive failures
                if self.source_failure_count[source] >= 3:
                    logger.error(f"Disabling source {source} after 3 consecutive failures")
                    self.source_status[source] = False
                
                continue
        
        # All sources failed, try cache
        logger.warning(f"All data sources failed for {symbol} {timeframe}, attempting cache")
        cached_df = self.cache.get(cache_key)
        
        if cached_df is not None and not cached_df.empty:
            logger.warning(f"Using cached data for {symbol} {timeframe}")
            return cached_df, False  # Mark as not fresh
        
        # No data available
        raise DataSourceError(
            f"Failed to fetch {symbol} {timeframe} from all sources and no cached data available"
        )
    
    def _fetch_from_source(
        self,
        source: str,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from specific source with retry logic.
        
        Args:
            source: Data source name (binance, twelve_data, alpha_vantage, mt5)
            symbol: Trading symbol
            timeframe: Candle timeframe
            limit: Number of candles
            
        Returns:
            DataFrame with candles or None if failed
        """
        for attempt in range(self.config.retry_config.max_attempts):
            try:
                if source == "binance":
                    return self._fetch_from_binance(symbol, timeframe, limit)
                elif source == "twelve_data":
                    return self._fetch_from_twelve_data(symbol, timeframe, limit)
                elif source == "alpha_vantage":
                    return self._fetch_from_alpha_vantage(symbol, timeframe, limit)
                elif source == "mt5":
                    return self._fetch_from_mt5(symbol, timeframe, limit)
                else:
                    logger.error(f"Unknown data source: {source}")
                    return None
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.config.retry_config.max_attempts} failed for {source}: {e}")
                
                if attempt < self.config.retry_config.max_attempts - 1:
                    # Exponential backoff
                    delay = min(
                        self.config.retry_config.initial_delay_seconds * (
                            self.config.retry_config.backoff_multiplier ** attempt
                        ),
                        self.config.retry_config.max_delay_seconds
                    )
                    logger.debug(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        
        return None
    
    def _fetch_from_binance(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> Optional[pd.DataFrame]:
        """Fetch data from Binance"""
        try:
            import ccxt
            
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            
            # Map symbol to Binance format
            binance_symbol = self.config.symbol_map.get(symbol, symbol)
            
            ohlcv = exchange.fetch_ohlcv(binance_symbol, timeframe, limit=limit)
            
            if not ohlcv:
                logger.warning(f"No data returned from Binance for {binance_symbol}")
                return None
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            
            return df
            
        except Exception as e:
            logger.error(f"Binance fetch failed: {e}")
            raise
    
    def _fetch_from_twelve_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> Optional[pd.DataFrame]:
        """Fetch data from Twelve Data API"""
        try:
            if not self.config.twelve_data_key:
                logger.warning("Twelve Data API key not configured")
                return None
            
            from src.twelve_data_client import TwelveDataClient
            
            client = TwelveDataClient(api_key=self.config.twelve_data_key)
            df = client.get_ohlcv(symbol, timeframe, limit)
            
            if df is None or df.empty:
                logger.warning(f"No data returned from Twelve Data for {symbol}")
                return None
            
            df['symbol'] = symbol
            return df
            
        except Exception as e:
            logger.error(f"Twelve Data fetch failed: {e}")
            raise
    
    def _fetch_from_alpha_vantage(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> Optional[pd.DataFrame]:
        """Fetch data from Alpha Vantage API"""
        try:
            if not self.config.alpha_vantage_key:
                logger.warning("Alpha Vantage API key not configured")
                return None
            
            from src.alpha_vantage_client import AlphaVantageClient
            
            client = AlphaVantageClient(api_key=self.config.alpha_vantage_key)
            df = client.get_ohlcv(symbol, timeframe, limit)
            
            if df is None or df.empty:
                logger.warning(f"No data returned from Alpha Vantage for {symbol}")
                return None
            
            df['symbol'] = symbol
            return df
            
        except Exception as e:
            logger.error(f"Alpha Vantage fetch failed: {e}")
            raise
    
    def _fetch_from_mt5(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> Optional[pd.DataFrame]:
        """Fetch data from MT5"""
        try:
            from src.mt5_data_client import MT5DataClient
            
            client = MT5DataClient()
            df = client.get_ohlcv(symbol, timeframe, limit)
            
            if df is None or df.empty:
                logger.warning(f"No data returned from MT5 for {symbol}")
                return None
            
            df['symbol'] = symbol
            return df
            
        except Exception as e:
            logger.error(f"MT5 fetch failed: {e}")
            raise
    
    def _validate_freshness(self, df: pd.DataFrame, timeframe: str) -> bool:
        """
        Validate that data is fresh enough for the timeframe.
        
        Args:
            df: DataFrame with candle data
            timeframe: Candle timeframe
            
        Returns:
            True if data is fresh, False otherwise
        """
        if df.empty:
            logger.warning("Cannot validate freshness: DataFrame is empty")
            return False
        
        try:
            latest_timestamp = df.iloc[-1]['timestamp']
            
            if not isinstance(latest_timestamp, pd.Timestamp):
                latest_timestamp = pd.to_datetime(latest_timestamp)
            
            # Convert to naive datetime for comparison
            if latest_timestamp.tzinfo is not None:
                latest_timestamp = latest_timestamp.tz_localize(None)
            
            current_time = datetime.now()
            age_seconds = (current_time - latest_timestamp).total_seconds()
            
            is_fresh = age_seconds < self.config.freshness_threshold_seconds
            
            logger.debug(
                f"Freshness check for {timeframe}: age={age_seconds:.1f}s, "
                f"threshold={self.config.freshness_threshold_seconds}s, fresh={is_fresh}"
            )
            
            return is_fresh
            
        except Exception as e:
            logger.error(f"Error validating freshness: {e}")
            return False
    
    def get_source_status(self) -> Dict[str, Dict]:
        """
        Get status of all data sources.
        
        Returns:
            Dictionary with status for each source
        """
        status = {}
        for source in self.source_status.keys():
            status[source] = {
                'enabled': self.source_status[source],
                'failures': self.source_failure_count.get(source, 0),
                'last_success': self.source_last_success.get(source)
            }
        return status
    
    def reset_source_status(self, source: str) -> None:
        """
        Reset failure count for a source (e.g., after manual intervention).
        
        Args:
            source: Data source name
        """
        if source in self.source_status:
            self.source_status[source] = True
            self.source_failure_count[source] = 0
            logger.info(f"Reset status for {source}")
    
    def clear_cache(self, key: Optional[str] = None) -> None:
        """
        Clear cache.
        
        Args:
            key: Specific cache key to clear, or None to clear all
        """
        self.cache.clear(key)
        logger.info(f"Cleared cache: {key or 'all'}")

