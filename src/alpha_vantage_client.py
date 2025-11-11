"""
Alpha Vantage data client for forex and indices (US30, XAU/USD)
Free tier: 5 calls/min, 500 calls/day
"""
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import time

logger = logging.getLogger(__name__)


class AlphaVantageClient:
    """Client for Alpha Vantage API - supports forex and indices"""
    
    # Symbol mappings
    SYMBOL_MAP = {
        'US30/USD': 'DJI',
        'US30': 'DJI',
        'XAU/USD': 'XAUUSD',
        'XAUUSD': 'XAUUSD',
        'GOLD/USD': 'XAUUSD',
    }
    
    # Interval mappings
    INTERVAL_MAP = {
        '1m': '1min',
        '5m': '5min',
        '15m': '15min',
        '30m': '30min',
        '1h': '60min',
        '4h': '60min',  # Will aggregate
        '1d': 'daily',
    }
    
    def __init__(self, api_key: str, symbol: str, timeframes: List[str], buffer_size: int = 100):
        """
        Initialize Alpha Vantage client
        
        Args:
            api_key: Alpha Vantage API key (get free at alphavantage.co)
            symbol: Trading symbol (e.g., 'US30/USD', 'XAU/USD')
            timeframes: List of timeframes to fetch
            buffer_size: Number of candles to keep in buffer
        """
        self.api_key = api_key
        self.symbol = symbol
        self.timeframes = timeframes
        self.buffer_size = buffer_size
        self.base_url = "https://www.alphavantage.co/query"
        
        # Map symbol
        self.av_symbol = self.SYMBOL_MAP.get(symbol, symbol)
        
        # Determine if forex or index
        self.is_forex = symbol in ['XAU/USD', 'XAUUSD', 'GOLD/USD']
        
        self.connected = False
        self.last_call_time = 0
        self.min_call_interval = 12  # 5 calls/min = 12 seconds between calls
        
        logger.info(f"Initialized AlphaVantageClient for {symbol} (mapped to {self.av_symbol})")
    
    def connect(self) -> bool:
        """Test connection to Alpha Vantage"""
        try:
            # Test with a simple quote request
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': self.av_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return False
                
                if 'Note' in data:
                    logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                    return False
                
                self.connected = True
                logger.info(f"Successfully connected to Alpha Vantage for {self.symbol}")
                return True
            else:
                logger.error(f"Connection failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Alpha Vantage: {e}")
            return False
    
    def _rate_limit_wait(self):
        """Wait if needed to respect rate limits"""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_call_interval:
            wait_time = self.min_call_interval - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        self.last_call_time = time.time()
    
    def get_latest_candles(self, timeframe: str, count: int = 100) -> pd.DataFrame:
        """
        Fetch latest candles for given timeframe
        
        Args:
            timeframe: Timeframe (e.g., '5m', '1h', '4h')
            count: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            self._rate_limit_wait()
            
            av_interval = self.INTERVAL_MAP.get(timeframe, '5min')
            
            if self.is_forex:
                function = 'FX_INTRADAY' if av_interval != 'daily' else 'FX_DAILY'
                params = {
                    'function': function,
                    'from_symbol': 'XAU',
                    'to_symbol': 'USD',
                    'interval': av_interval,
                    'outputsize': 'full' if count > 100 else 'compact',
                    'apikey': self.api_key
                }
            else:
                # Index data
                function = 'TIME_SERIES_INTRADAY' if av_interval != 'daily' else 'TIME_SERIES_DAILY'
                params = {
                    'function': function,
                    'symbol': self.av_symbol,
                    'interval': av_interval,
                    'outputsize': 'full' if count > 100 else 'compact',
                    'apikey': self.api_key
                }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} from Alpha Vantage")
                return pd.DataFrame()
            
            data = response.json()
            
            # Check for errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return pd.DataFrame()
            
            if 'Note' in data:
                logger.warning(f"Rate limit hit: {data['Note']}")
                return pd.DataFrame()
            
            # Extract time series data
            time_series_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break
            
            if not time_series_key:
                logger.error(f"No time series data found. Keys: {list(data.keys())}")
                return pd.DataFrame()
            
            time_series = data[time_series_key]
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Rename columns
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            
            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Add timestamp
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            df['timestamp'] = df.index
            df = df.reset_index(drop=True)
            
            # Take last N candles
            df = df.tail(count)
            
            logger.info(f"Fetched {len(df)} candles for {timeframe} from Alpha Vantage")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from Alpha Vantage: {e}", exc_info=True)
            return pd.DataFrame()
    
    def get_current_price(self) -> Optional[float]:
        """Get current price"""
        try:
            self._rate_limit_wait()
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': self.av_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                return float(data['Global Quote']['05. price'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
