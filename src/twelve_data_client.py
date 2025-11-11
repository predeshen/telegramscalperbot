"""
Twelve Data client for real-time market data
Free tier: 800 calls/day, 8 calls/min
"""
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, List
import time

logger = logging.getLogger(__name__)


class TwelveDataClient:
    """Client for Twelve Data API - supports stocks, forex, crypto, indices"""
    
    # Symbol mappings
    SYMBOL_MAP = {
        'BTC/USD': 'BTC/USD',
        'BTCUSD': 'BTC/USD',
        'US30/USD': 'DJI',
        'US30': 'DJI',
        'XAU/USD': 'XAU/USD',
        'XAUUSD': 'XAU/USD',
        'GOLD/USD': 'XAU/USD',
    }
    
    # Interval mappings
    INTERVAL_MAP = {
        '1m': '1min',
        '5m': '5min',
        '15m': '15min',
        '30m': '30min',
        '1h': '1h',
        '4h': '4h',
        '1d': '1day',
    }
    
    def __init__(self, api_key: str, symbol: str, timeframes: List[str], buffer_size: int = 100):
        """
        Initialize Twelve Data client
        
        Args:
            api_key: Twelve Data API key
            symbol: Trading symbol
            timeframes: List of timeframes
            buffer_size: Buffer size
        """
        self.api_key = api_key
        self.symbol = symbol
        self.timeframes = timeframes
        self.buffer_size = buffer_size
        self.base_url = "https://api.twelvedata.com"
        
        # Map symbol
        self.td_symbol = self.SYMBOL_MAP.get(symbol, symbol)
        
        self.connected = False
        self.last_call_time = 0
        self.min_call_interval = 7.5  # 8 calls/min = 7.5 seconds between calls
        
        logger.info(f"Initialized TwelveDataClient for {symbol} (mapped to {self.td_symbol})")
    
    def connect(self) -> bool:
        """Test connection"""
        try:
            # Test with a quote request
            params = {
                'symbol': self.td_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/quote", params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'code' in data and data['code'] != 200:
                    logger.error(f"Twelve Data error: {data.get('message', 'Unknown error')}")
                    return False
                
                if 'status' in data and data['status'] == 'error':
                    logger.error(f"Twelve Data error: {data.get('message', 'Unknown error')}")
                    return False
                
                self.connected = True
                logger.info(f"Successfully connected to Twelve Data for {self.symbol}")
                return True
            else:
                logger.error(f"Connection failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Twelve Data: {e}")
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
        Fetch latest candles
        
        Args:
            timeframe: Timeframe
            count: Number of candles
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            self._rate_limit_wait()
            
            td_interval = self.INTERVAL_MAP.get(timeframe, '5min')
            
            params = {
                'symbol': self.td_symbol,
                'interval': td_interval,
                'outputsize': min(count, 5000),
                'apikey': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} from Twelve Data")
                return pd.DataFrame()
            
            data = response.json()
            
            # Check for errors
            if 'code' in data and data['code'] != 200:
                logger.error(f"Twelve Data error: {data.get('message', 'Unknown error')}")
                return pd.DataFrame()
            
            if 'status' in data and data['status'] == 'error':
                logger.error(f"Twelve Data error: {data.get('message', 'Unknown error')}")
                return pd.DataFrame()
            
            if 'values' not in data:
                logger.error(f"No values in response. Keys: {list(data.keys())}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(data['values'])
            
            # Rename and convert columns
            df = df.rename(columns={
                'datetime': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            # Convert to proper types
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            df = df.reset_index(drop=True)
            
            # Take last N candles
            df = df.tail(count)
            
            logger.info(f"Fetched {len(df)} candles for {timeframe} from Twelve Data")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from Twelve Data: {e}", exc_info=True)
            return pd.DataFrame()
    
    def get_current_price(self) -> Optional[float]:
        """Get current price"""
        try:
            self._rate_limit_wait()
            
            params = {
                'symbol': self.td_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/price", params=params, timeout=10)
            data = response.json()
            
            if 'price' in data:
                return float(data['price'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
