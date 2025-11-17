"""Unit tests for retry logic and trade update fallback."""
import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
import time


def utc_now():
    """Helper to get current UTC time as timezone-naive datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    def test_retry_succeeds_on_first_attempt(self):
        """Test that retry succeeds immediately if first attempt returns fresh data."""
        from main import BTCScalpingScanner
        
        # Create mock scanner instance
        scanner = Mock(spec=BTCScalpingScanner)
        scanner.market_client = Mock()
        
        # Mock successful fetch on first attempt
        now = utc_now()
        fresh_df = pd.DataFrame({
            'timestamp': [now - timedelta(seconds=30)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        scanner.market_client.get_latest_candles = Mock(return_value=(fresh_df, True))
        
        # Call retry logic - call as unbound method with self
        df, is_fresh = BTCScalpingScanner._retry_fetch_with_backoff(scanner, '1m', max_retries=3)
        
        assert is_fresh is True
        assert df is not None
        assert len(df) == 1
        # Should only call once (no retries needed)
        assert scanner.market_client.get_latest_candles.call_count == 1
    
    @patch('time.sleep')
    def test_retry_succeeds_on_second_attempt(self, mock_sleep):
        """Test that retry succeeds on second attempt after first fails."""
        from main import BTCScalpingScanner
        
        scanner = Mock(spec=BTCScalpingScanner)
        scanner.market_client = Mock()
        
        now = utc_now()
        stale_df = pd.DataFrame({
            'timestamp': [now - timedelta(minutes=5)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        fresh_df = pd.DataFrame({
            'timestamp': [now - timedelta(seconds=30)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        # First call returns stale, second returns fresh
        scanner.market_client.get_latest_candles = Mock(side_effect=[
            (stale_df, False),
            (fresh_df, True)
        ])
        
        df, is_fresh = BTCScalpingScanner._retry_fetch_with_backoff(scanner, '1m', max_retries=3)
        
        assert is_fresh is True
        assert df is not None
        # Should call twice (first attempt + 1 retry)
        assert scanner.market_client.get_latest_candles.call_count == 2
        # Should have slept once (5 seconds before retry)
        mock_sleep.assert_called_once_with(5)
    
    @patch('time.sleep')
    def test_retry_all_attempts_fail(self, mock_sleep):
        """Test that retry returns None after all attempts fail."""
        from main import BTCScalpingScanner
        
        scanner = Mock(spec=BTCScalpingScanner)
        scanner.market_client = Mock()
        
        now = utc_now()
        stale_df = pd.DataFrame({
            'timestamp': [now - timedelta(minutes=5)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        # All attempts return stale data
        scanner.market_client.get_latest_candles = Mock(return_value=(stale_df, False))
        
        df, is_fresh = BTCScalpingScanner._retry_fetch_with_backoff(scanner, '1m', max_retries=3)
        
        assert is_fresh is False
        assert df is None
        # Should call 3 times (initial + 2 retries)
        assert scanner.market_client.get_latest_candles.call_count == 3
        # Should have slept twice (5s, 10s)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(5)
        mock_sleep.assert_any_call(10)
    
    @patch('time.sleep')
    def test_retry_backoff_delays(self, mock_sleep):
        """Test that retry uses correct exponential backoff delays."""
        from main import BTCScalpingScanner
        
        scanner = Mock(spec=BTCScalpingScanner)
        scanner.market_client = Mock()
        
        now = utc_now()
        stale_df = pd.DataFrame({
            'timestamp': [now - timedelta(minutes=5)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        
        # All attempts return stale data
        scanner.market_client.get_latest_candles = Mock(return_value=(stale_df, False))
        
        df, is_fresh = BTCScalpingScanner._retry_fetch_with_backoff(scanner, '1m', max_retries=3)
        
        # Verify backoff delays: [5, 10, 30] seconds
        assert mock_sleep.call_count == 2
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert calls == [5, 10]


class TestTradeUpdateFallback:
    """Test trade update price fallback logic."""
    
    def test_use_live_price_when_available(self):
        """Test that live price is used when available."""
        from main import BTCScalpingScanner
        
        scanner = Mock(spec=BTCScalpingScanner)
        scanner.config = Mock()
        scanner.config.exchange.timeframes = ['1m']
        scanner.market_client = Mock()
        scanner.last_known_price = None
        scanner.last_known_price_time = None
        
        now = utc_now()
        fresh_df = pd.DataFrame({
            'timestamp': [now - timedelta(seconds=30)],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [100]
        })
        scanner.market_client.get_latest_candles = Mock(return_value=(fresh_df, True))
        
        price = BTCScalpingScanner._get_current_price_for_trades(scanner)
        
        assert price == 50050
        assert scanner.last_known_price == 50050
        assert scanner.last_known_price_time is not None
    
    def test_use_cached_price_when_live_unavailable(self):
        """Test that cached price is used when live price unavailable."""
        from main import BTCScalpingScanner
        
        scanner = Mock(spec=BTCScalpingScanner)
        scanner.config = Mock()
        scanner.config.exchange.timeframes = ['1m']
        scanner.market_client = Mock()
        scanner.last_known_price = 50000
        scanner.last_known_price_time = datetime.now() - timedelta(minutes=2)
        
        # Mock fetch failure
        scanner.market_client.get_latest_candles = Mock(side_effect=Exception("API error"))
        
        price = BTCScalpingScanner._get_current_price_for_trades(scanner)
        
        # Should return cached price (< 5 min old)
        assert price == 50000
    
    def test_skip_update_when_cache_too_old(self):
        """Test that None is returned when cache is too old."""
        from main import BTCScalpingScanner
        
        scanner = Mock(spec=BTCScalpingScanner)
        scanner.config = Mock()
        scanner.config.exchange.timeframes = ['1m']
        scanner.market_client = Mock()
        scanner.last_known_price = 50000
        scanner.last_known_price_time = datetime.now() - timedelta(minutes=10)
        
        # Mock fetch failure
        scanner.market_client.get_latest_candles = Mock(side_effect=Exception("API error"))
        
        price = BTCScalpingScanner._get_current_price_for_trades(scanner)
        
        # Should return None (cache > 5 min old)
        assert price is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
