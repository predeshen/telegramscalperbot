"""
Multi-provider hybrid data client for cloud deployment
Routes to best available provider with automatic fallback:
- Alpha Vantage (primary for US30/XAU) - 5 calls/min, 500/day
- Twelve Data (secondary) - 8 calls/min, 800/day  
- yfinance (fallback) - Unlimited but delayed
"""
import logging
import pandas as pd
from typing import Optional, List, Dict
import time

logger = logging.getLogger(__name__)


class HybridDataClient:
    """Multi-provider client with automatic fallback and rate limiting"""
    
    # Provider priority by asset type
    PROVIDER_PRIORITY = {
        'BTC': ['yfinance', 'kraken', 'twelve_data', 'alpha_vantage'],  # yfinance first (real-time, no limits)
        'US30': ['yfinance', 'alpha_vantage', 'twelve_data'],  # yfinance first (real-time, no limits)
        'XAU': ['yfinance', 'twelve_data', 'alpha_vantage'],   # yfinance first (fresh, no limits)
    }
    
    def __init__(self, symbol: str, timeframes: List[str], buffer_size: int = 100,
                 alpha_vantage_key: Optional[str] = None,
                 twelve_data_key: Optional[str] = None,
                 preferred_provider: Optional[str] = None):
        """
        Initialize multi-provider hybrid client
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USD', 'US30/USD', 'XAU/USD')
            timeframes: List of timeframes
            buffer_size: Buffer size for candles
            alpha_vantage_key: Alpha Vantage API key (optional)
            twelve_data_key: Twelve Data API key (optional)
            preferred_provider: Force specific provider (optional)
        """
        self.symbol = symbol
        self.timeframes = timeframes
        self.buffer_size = buffer_size
        self.alpha_vantage_key = alpha_vantage_key
        self.twelve_data_key = twelve_data_key
        self.preferred_provider = preferred_provider
        
        # Determine asset type
        self.asset_type = self._get_asset_type(symbol)
        
        # Track provider usage for rate limiting
        self.provider_last_call = {}
        self.provider_call_count = {}
        
        self.client = None
        self.client_type = None
        self.providers_tried = []
        
        self._initialize_client()
    
    def _get_asset_type(self, symbol: str) -> str:
        """Determine asset type from symbol"""
        symbol_upper = symbol.upper()
        if 'BTC' in symbol_upper or 'ETH' in symbol_upper:
            return 'BTC'
        elif 'US30' in symbol_upper or 'DJI' in symbol_upper:
            return 'US30'
        elif 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
            return 'XAU'
        return 'OTHER'
    
    def _initialize_client(self):
        """Initialize client with provider priority"""
        
        # Get provider priority for this asset
        if self.preferred_provider:
            providers = [self.preferred_provider]
        else:
            providers = self.PROVIDER_PRIORITY.get(self.asset_type, ['yfinance'])
        
        # Try each provider in order
        for provider in providers:
            if self._try_provider(provider):
                return
        
        # If all fail, use yfinance as last resort
        logger.warning(f"All preferred providers failed, using yfinance as fallback")
        self._use_yfinance()
    
    def _try_provider(self, provider: str) -> bool:
        """Try to initialize a specific provider"""
        self.providers_tried.append(provider)
        
        try:
            if provider == 'kraken':
                return self._use_kraken()
            elif provider == 'alpha_vantage' and self.alpha_vantage_key:
                return self._use_alpha_vantage()
            elif provider == 'twelve_data' and self.twelve_data_key:
                return self._use_twelve_data()
            elif provider == 'yfinance':
                return self._use_yfinance()
            else:
                logger.debug(f"Provider {provider} not available (missing API key or not supported)")
                return False
        except Exception as e:
            logger.warning(f"Failed to initialize {provider}: {e}")
            return False
    
    def _use_kraken(self) -> bool:
        """Use Kraken via CCXT (for BTC only)"""
        try:
            from src.market_data_client import MarketDataClient
            
            # Map symbol to Kraken format
            kraken_symbol = 'BTC/USD' if 'BTC' in self.symbol.upper() else self.symbol
            
            self.client = MarketDataClient(
                exchange_name='kraken',
                symbol=kraken_symbol,
                timeframes=self.timeframes,
                buffer_size=self.buffer_size
            )
            self.client_type = 'kraken'
            logger.info(f"Using Kraken (CCXT) for {self.symbol}")
            return True
        except Exception as e:
            logger.warning(f"Kraken not available: {e}")
            return False
    
    def _use_alpha_vantage(self) -> bool:
        """Use Alpha Vantage"""
        try:
            from src.alpha_vantage_client import AlphaVantageClient
            
            self.client = AlphaVantageClient(
                api_key=self.alpha_vantage_key,
                symbol=self.symbol,
                timeframes=self.timeframes,
                buffer_size=self.buffer_size
            )
            self.client_type = 'alpha_vantage'
            logger.info(f"Using Alpha Vantage for {self.symbol}")
            return True
        except ImportError:
            logger.warning("Alpha Vantage client not available")
            return False
    
    def _use_twelve_data(self) -> bool:
        """Use Twelve Data"""
        try:
            from src.twelve_data_client import TwelveDataClient
            
            self.client = TwelveDataClient(
                api_key=self.twelve_data_key,
                symbol=self.symbol,
                timeframes=self.timeframes,
                buffer_size=self.buffer_size
            )
            self.client_type = 'twelve_data'
            logger.info(f"Using Twelve Data for {self.symbol}")
            return True
        except ImportError:
            logger.warning("Twelve Data client not available")
            return False
    
    def _use_yfinance(self) -> bool:
        """Use yfinance (always available fallback)"""
        try:
            from src.yfinance_client import YFinanceClient
            
            # Symbol mappings
            symbol_map = {
                'BTC/USD': 'BTC-USD',
                'BTCUSD': 'BTC-USD',
                'US30/USD': '^DJI',
                'US30': '^DJI',
                'XAU/USD': 'GC=F',
                'XAUUSD': 'GC=F',
            }
            
            yf_symbol = symbol_map.get(self.symbol, self.symbol)
            
            self.client = YFinanceClient(
                symbol=yf_symbol,
                timeframes=self.timeframes,
                buffer_size=self.buffer_size
            )
            self.client_type = 'yfinance'
            logger.info(f"Using yfinance for {self.symbol} (ticker: {yf_symbol})")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize yfinance: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to the data provider"""
        if not self.client:
            logger.error("No client initialized")
            return False
        
        success = self.client.connect()
        
        if not success:
            logger.warning(f"Failed to connect with {self.client_type}, trying fallback...")
            # Try next provider in priority list
            remaining_providers = [p for p in self.PROVIDER_PRIORITY.get(self.asset_type, ['yfinance']) 
                                 if p not in self.providers_tried]
            
            for provider in remaining_providers:
                if self._try_provider(provider):
                    return self.client.connect()
            
            logger.error("All providers failed to connect")
            return False
        
        return True
    
    def get_latest_candles(self, timeframe: str, count: int = 100) -> pd.DataFrame:
        """
        Get latest candles with automatic fallback
        
        Args:
            timeframe: Timeframe (e.g., '5m', '1h')
            count: Number of candles
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.client:
            logger.error("No client initialized")
            return pd.DataFrame()
        
        try:
            data = self.client.get_latest_candles(timeframe, count)
            
            # If data is empty, try fallback
            if data.empty:
                logger.warning(f"{self.client_type} returned empty data, trying fallback...")
                return self._try_fallback_data(timeframe, count)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data from {self.client_type}: {e}")
            return self._try_fallback_data(timeframe, count)
    
    def _try_fallback_data(self, timeframe: str, count: int) -> pd.DataFrame:
        """Try to get data from fallback provider"""
        remaining_providers = [p for p in self.PROVIDER_PRIORITY.get(self.asset_type, ['yfinance']) 
                             if p not in self.providers_tried]
        
        for provider in remaining_providers:
            logger.info(f"Trying fallback provider: {provider}")
            if self._try_provider(provider):
                if self.client.connect():
                    data = self.client.get_latest_candles(timeframe, count)
                    if not data.empty:
                        logger.info(f"Successfully got data from fallback provider {provider}")
                        return data
        
        logger.error("All fallback providers failed")
        return pd.DataFrame()
    
    def get_current_price(self) -> Optional[float]:
        """Get current price"""
        if not self.client:
            return None
        
        try:
            if hasattr(self.client, 'get_current_price'):
                return self.client.get_current_price()
            
            # Fallback: get from latest candle
            df = self.get_latest_candles(self.timeframes[0], 1)
            if not df.empty:
                return float(df.iloc[-1]['close'])
            
            return None
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    def get_client_info(self) -> dict:
        """Get information about the active client"""
        # Check connection status
        connected = False
        if self.client:
            if hasattr(self.client, 'connected'):
                connected = self.client.connected
            elif hasattr(self.client, '_connected'):
                connected = self.client._connected
        
        return {
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'client_type': self.client_type,
            'providers_tried': self.providers_tried,
            'connected': connected,
            'has_alpha_vantage': self.alpha_vantage_key is not None,
            'has_twelve_data': self.twelve_data_key is not None,
        }
