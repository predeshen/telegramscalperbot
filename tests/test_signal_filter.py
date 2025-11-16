"""Tests for SignalFilter."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from src.signal_filter import SignalFilter


class TestSignalFilter:
    """Test suite for SignalFilter."""
    
    @pytest.fixture
    def signal_filter(self):
        """Create a SignalFilter instance."""
        return SignalFilter(conflict_window_minutes=5, duplicate_window_minutes=10)
    
    @pytest.fixture
    def mock_signal(self):
        """Create a mock signal."""
        signal = Mock()
        signal.timestamp = datetime.now()
        signal.timeframe = "15m"
        signal.signal_type = "LONG"
        signal.entry_price = 95000.0
        return signal
    
    def test_initialization(self, signal_filter):
        """Test SignalFilter initialization."""
        assert signal_filter.conflict_window_minutes == 5
        assert signal_filter.duplicate_window_minutes == 10
        assert len(signal_filter.recent_signals) == 0
        assert len(signal_filter.active_trades) == 0
    
    def test_no_suppression_for_first_signal(self, signal_filter, mock_signal):
        """Test that first signal is not suppressed."""
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", mock_signal)
        
        assert not should_suppress
        assert reason == ""
    
    def test_timeframe_conflict_higher_priority(self, signal_filter):
        """Test that higher timeframe takes priority in conflicts."""
        # Add a 1d SHORT signal
        signal_1d = Mock()
        signal_1d.timestamp = datetime.now()
        signal_1d.timeframe = "1d"
        signal_1d.signal_type = "SHORT"
        signal_1d.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", signal_1d)
        
        # Try to add a 15m LONG signal (conflicting)
        signal_15m = Mock()
        signal_15m.timestamp = datetime.now()
        signal_15m.timeframe = "15m"
        signal_15m.signal_type = "LONG"
        signal_15m.entry_price = 95100.0
        
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", signal_15m)
        
        assert should_suppress
        assert "Conflicting signal" in reason
        assert "1d" in reason
        assert "higher priority" in reason
    
    def test_no_conflict_same_direction(self, signal_filter):
        """Test that same direction signals don't conflict."""
        # Add a 1d LONG signal
        signal_1d = Mock()
        signal_1d.timestamp = datetime.now()
        signal_1d.timeframe = "1d"
        signal_1d.signal_type = "LONG"
        signal_1d.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", signal_1d)
        
        # Try to add a 15m LONG signal (same direction)
        signal_15m = Mock()
        signal_15m.timestamp = datetime.now()
        signal_15m.timeframe = "15m"
        signal_15m.signal_type = "LONG"
        signal_15m.entry_price = 95100.0
        
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", signal_15m)
        
        assert not should_suppress
    
    def test_active_trade_conflict(self, signal_filter):
        """Test that opposite signals are suppressed when active trade exists."""
        # Set active LONG trade
        active_signal = Mock()
        active_signal.signal_type = "LONG"
        active_signal.entry_price = 95000.0
        signal_filter.set_active_trade("BTC-USD", active_signal)
        
        # Try to add SHORT signal
        short_signal = Mock()
        short_signal.timestamp = datetime.now()
        short_signal.timeframe = "15m"
        short_signal.signal_type = "SHORT"
        short_signal.entry_price = 95000.0
        
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", short_signal)
        
        assert should_suppress
        assert "Active" in reason
        assert "LONG" in reason
    
    def test_duplicate_signal_detection(self, signal_filter):
        """Test duplicate signal detection."""
        # Add first signal
        signal1 = Mock()
        signal1.timestamp = datetime.now()
        signal1.timeframe = "15m"
        signal1.signal_type = "LONG"
        signal1.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", signal1)
        
        # Try to add duplicate signal (same timeframe, type, similar price)
        signal2 = Mock()
        signal2.timestamp = datetime.now()
        signal2.timeframe = "15m"
        signal2.signal_type = "LONG"
        signal2.entry_price = 95050.0  # Within 0.5%
        
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", signal2)
        
        assert should_suppress
        assert "Duplicate" in reason
    
    def test_no_duplicate_different_price(self, signal_filter):
        """Test that signals with different prices are not duplicates."""
        # Add first signal
        signal1 = Mock()
        signal1.timestamp = datetime.now()
        signal1.timeframe = "15m"
        signal1.signal_type = "LONG"
        signal1.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", signal1)
        
        # Try to add signal with significantly different price
        signal2 = Mock()
        signal2.timestamp = datetime.now()
        signal2.timeframe = "15m"
        signal2.signal_type = "LONG"
        signal2.entry_price = 96000.0  # > 1% difference
        
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", signal2)
        
        assert not should_suppress
    
    def test_old_signals_ignored(self, signal_filter):
        """Test that old signals outside window are ignored."""
        # Add old signal (outside conflict window)
        old_signal = Mock()
        old_signal.timestamp = datetime.now() - timedelta(minutes=10)
        old_signal.timeframe = "1d"
        old_signal.signal_type = "SHORT"
        old_signal.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", old_signal)
        
        # Try to add new LONG signal (would conflict if old signal was recent)
        new_signal = Mock()
        new_signal.timestamp = datetime.now()
        new_signal.timeframe = "15m"
        new_signal.signal_type = "LONG"
        new_signal.entry_price = 95100.0
        
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", new_signal)
        
        assert not should_suppress
    
    def test_per_symbol_tracking(self, signal_filter):
        """Test that signals are tracked per symbol."""
        # Add BTC signal
        btc_signal = Mock()
        btc_signal.timestamp = datetime.now()
        btc_signal.timeframe = "15m"
        btc_signal.signal_type = "LONG"
        btc_signal.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", btc_signal)
        
        # Add ETH signal (should not conflict with BTC)
        eth_signal = Mock()
        eth_signal.timestamp = datetime.now()
        eth_signal.timeframe = "15m"
        eth_signal.signal_type = "SHORT"
        eth_signal.entry_price = 3500.0
        
        should_suppress, reason = signal_filter.should_suppress_signal("ETH-USD", eth_signal)
        
        assert not should_suppress
    
    def test_clear_active_trade(self, signal_filter):
        """Test clearing active trade."""
        # Set active trade
        signal = Mock()
        signal.signal_type = "LONG"
        signal.entry_price = 95000.0
        signal_filter.set_active_trade("BTC-USD", signal)
        
        assert "BTC-USD" in signal_filter.active_trades
        
        # Clear it
        signal_filter.clear_active_trade("BTC-USD")
        
        assert "BTC-USD" not in signal_filter.active_trades
    
    def test_get_statistics(self, signal_filter, mock_signal):
        """Test getting filter statistics."""
        signal_filter.add_signal_to_history("BTC-USD", mock_signal)
        signal_filter.set_active_trade("BTC-USD", mock_signal)
        
        stats = signal_filter.get_statistics()
        
        assert stats["total_signals_tracked"] >= 1
        assert stats["symbols_tracked"] >= 1
        assert stats["active_trades"] == 1
    
    def test_suppression_logging(self, signal_filter):
        """Test that suppressions are logged."""
        # Create conflicting signals
        signal_1d = Mock()
        signal_1d.timestamp = datetime.now()
        signal_1d.timeframe = "1d"
        signal_1d.signal_type = "SHORT"
        signal_1d.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", signal_1d)
        
        signal_15m = Mock()
        signal_15m.timestamp = datetime.now()
        signal_15m.timeframe = "15m"
        signal_15m.signal_type = "LONG"
        signal_15m.entry_price = 95100.0
        
        # This should be suppressed
        signal_filter.should_suppress_signal("BTC-USD", signal_15m)
        
        # Check suppression was logged
        suppressions = signal_filter.get_suppressed_signals("BTC-USD")
        assert len(suppressions) > 0
        assert suppressions[0]["symbol"] == "BTC-USD"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
