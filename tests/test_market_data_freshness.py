"""Unit tests for market data freshness validation."""
import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from src.market_data_client import MarketDataClient, FRESHNESS_THRESHOLDS


def utc_now():
    """Helper to get current UTC time as timezone-naive datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def mock_exchange():
    """Create a mock CCXT exchange."""
    exchange = Mock()
    exchange.load_markets = Mock()
    exchange.markets = {'BTC/USDT': {}}
    return exchange


@pytest.fixture
def market_client():
    """Create a MarketDataClient instance for testing."""
    with patch('src.market_data_client.ccxt') as mock_ccxt:
        mock_exchange = Mock()
        mock_exchange.load_markets = Mock()
        mock_exchange.markets = {'BTC/USDT': {}}
        mock_ccxt.binance.return_value = mock_exchange
        
        client = MarketDataClient('binance', 'BTC/USDT', ['1m', '5m'])
        client.exchange = mock_exchange
        client._connected = True
        return client


class TestFreshnessThresholds:
    """Test freshness threshold constants."""
    
    def test_freshness_thresholds_defined(self):
        """Test that freshness thresholds are defined for common timeframes."""
        assert '1m' in FRESHNESS_THRESHOLDS
        assert '5m' in FRESHNESS_THRESHOLDS
        assert '15m' in FRESHNESS_THRESHOLDS
        assert '1h' in FRESHNESS_THRESHOLDS
        assert '4h' in FRESHNESS_THRESHOLDS
        assert '1d' in FRESHNESS_THRESHOLDS
    
    def test_freshness_thresholds_reasonable(self):
        """Test that thresholds are reasonable for each timeframe."""
        # 1m threshold should be around 1.5 minutes
        assert 60 < FRESHNESS_THRESHOLDS['1m'] < 180
        
        # 5m threshold should be around 7 minutes
        assert 300 < FRESHNESS_THRESHOLDS['5m'] < 600
        
        # 1h threshold should be around 90 minutes
        assert 3600 < FRESHNESS_THRESHOLDS['1h'] < 7200


class TestValidateDataFreshness:
    """Test data freshness validation."""
    
    def test_validate_fresh_data_1m(self, market_client):
        """Test validation with fresh 1m data."""
        # Create DataFrame with recent timestamp (30 seconds ago)
        now = utc_now()
        df = pd.DataFrame({
            'timestamp': [now - timedelta(seconds=30)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '1m')
        
        assert is_fresh is True
        assert 25 < age_seconds < 35  # Should be around 30 seconds
    
    def test_validate_stale_data_1m(self, market_client):
        """Test validation with stale 1m data."""
        # Create DataFrame with old timestamp (5 minutes ago)
        now = utc_now()
        df = pd.DataFrame({
            'timestamp': [now - timedelta(minutes=5)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '1m')
        
        assert is_fresh is False
        assert 295 < age_seconds < 305  # Should be around 300 seconds
    
    def test_validate_fresh_data_5m(self, market_client):
        """Test validation with fresh 5m data."""
        # Create DataFrame with recent timestamp (3 minutes ago)
        now = utc_now()
        df = pd.DataFrame({
            'timestamp': [now - timedelta(minutes=3)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '5m')
        
        assert is_fresh is True
        assert 175 < age_seconds < 185  # Should be around 180 seconds
    
    def test_validate_stale_data_5m(self, market_client):
        """Test validation with stale 5m data."""
        # Create DataFrame with old timestamp (10 minutes ago)
        now = utc_now()
        df = pd.DataFrame({
            'timestamp': [now - timedelta(minutes=10)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '5m')
        
        assert is_fresh is False
        assert 595 < age_seconds < 605  # Should be around 600 seconds
    
    def test_validate_data_at_threshold(self, market_client):
        """Test validation with data exactly at threshold."""
        # Create DataFrame with timestamp exactly at 1m threshold (90 seconds)
        now = utc_now()
        df = pd.DataFrame({
            'timestamp': [now - timedelta(seconds=90)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '1m')
        
        # At exactly threshold, should be considered stale (age < threshold for fresh)
        assert is_fresh is False
        assert 88 < age_seconds < 92
    
    def test_validate_data_just_over_threshold(self, market_client):
        """Test validation with data just over threshold."""
        # Create DataFrame with timestamp just over 1m threshold (91 seconds)
        now = utc_now()
        df = pd.DataFrame({
            'timestamp': [now - timedelta(seconds=91)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '1m')
        
        # Just over threshold should be stale
        assert is_fresh is False
        assert 89 < age_seconds < 93
    
    def test_validate_empty_dataframe(self, market_client):
        """Test validation with empty DataFrame."""
        df = pd.DataFrame()
        
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '1m')
        
        assert is_fresh is False
        assert age_seconds == float('inf')
    
    def test_validate_with_custom_threshold(self, market_client):
        """Test validation with custom threshold."""
        # Create DataFrame with timestamp 2 minutes ago
        now = utc_now()
        df = pd.DataFrame({
            'timestamp': [now - timedelta(minutes=2)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        # With custom threshold of 180 seconds (3 minutes), should be fresh
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '1m', max_age_seconds=180)
        
        assert is_fresh is True
        assert 115 < age_seconds < 125
        
        # With custom threshold of 60 seconds (1 minute), should be stale
        is_fresh, age_seconds = market_client.validate_data_freshness(df, '1m', max_age_seconds=60)
        
        assert is_fresh is False
    
    def test_validate_unknown_timeframe_uses_default(self, market_client):
        """Test that unknown timeframe uses default threshold."""
        # Create DataFrame with timestamp 4 minutes ago
        now = utc_now()
        df = pd.DataFrame({
            'timestamp': [now - timedelta(minutes=4)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        # Unknown timeframe should use default (300 seconds = 5 minutes)
        is_fresh, age_seconds = market_client.validate_data_freshness(df, 'unknown_tf')
        
        assert is_fresh is True  # 4 minutes < 5 minutes default
        assert 235 < age_seconds < 245


class TestGetLatestCandlesWithFreshness:
    """Test get_latest_candles with freshness validation."""
    
    def test_get_latest_candles_returns_tuple(self, market_client):
        """Test that get_latest_candles returns tuple with freshness flag."""
        # Mock exchange response with fresh data
        now = utc_now()
        mock_ohlcv = [
            [int((now - timedelta(minutes=2)).timestamp() * 1000), 50000, 50100, 49900, 50050, 100],
            [int((now - timedelta(minutes=1)).timestamp() * 1000), 50050, 50150, 50000, 50100, 110],
            [int(now.timestamp() * 1000), 50100, 50200, 50050, 50150, 120]
        ]
        market_client.exchange.fetch_ohlcv = Mock(return_value=mock_ohlcv)
        
        df, is_fresh = market_client.get_latest_candles('1m', 3)
        
        assert isinstance(df, pd.DataFrame)
        assert isinstance(is_fresh, bool)
        assert len(df) == 3
    
    def test_get_latest_candles_fresh_data(self, market_client):
        """Test get_latest_candles with fresh data."""
        # Mock exchange response with fresh data (30 seconds ago)
        # Create timestamp in UTC (as exchanges do)
        import time
        now_utc_timestamp = time.time()  # Current UTC timestamp
        timestamp_30s_ago = now_utc_timestamp - 30
        timestamp_ms = int(timestamp_30s_ago * 1000)
        
        mock_ohlcv = [
            [timestamp_ms, 50000, 50100, 49900, 50050, 100]
        ]
        market_client.exchange.fetch_ohlcv = Mock(return_value=mock_ohlcv)
        
        df, is_fresh = market_client.get_latest_candles('1m', 1)
        
        assert is_fresh is True
        assert len(df) == 1
    
    def test_get_latest_candles_stale_data(self, market_client):
        """Test get_latest_candles with stale data."""
        # Mock exchange response with stale data (5 minutes ago)
        now = utc_now()
        mock_ohlcv = [
            [int((now - timedelta(minutes=5)).timestamp() * 1000), 50000, 50100, 49900, 50050, 100]
        ]
        market_client.exchange.fetch_ohlcv = Mock(return_value=mock_ohlcv)
        
        df, is_fresh = market_client.get_latest_candles('1m', 1)
        
        assert is_fresh is False
        assert len(df) == 1
    
    def test_get_latest_candles_validation_disabled(self, market_client):
        """Test get_latest_candles with validation disabled."""
        # Mock exchange response with stale data
        now = utc_now()
        mock_ohlcv = [
            [int((now - timedelta(minutes=5)).timestamp() * 1000), 50000, 50100, 49900, 50050, 100]
        ]
        market_client.exchange.fetch_ohlcv = Mock(return_value=mock_ohlcv)
        
        df, is_fresh = market_client.get_latest_candles('1m', 1, validate_freshness=False)
        
        # Should always return True when validation is disabled
        assert is_fresh is True
        assert len(df) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
