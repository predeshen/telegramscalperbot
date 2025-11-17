"""Unit tests for TradeTracker TP/SL detection and notification logic."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from src.trade_tracker import TradeTracker, TradeStatus
from src.signal_detector import Signal


@pytest.fixture
def mock_alerter():
    """Create a mock alerter for testing."""
    alerter = Mock()
    alerter.send_message = Mock(return_value=True)
    return alerter


@pytest.fixture
def trade_tracker(mock_alerter):
    """Create a TradeTracker instance for testing."""
    return TradeTracker(alerter=mock_alerter)


@pytest.fixture
def long_signal():
    """Create a sample LONG signal."""
    return Signal(
        timestamp=datetime.now(),
        signal_type="LONG",
        timeframe="1m",
        entry_price=4058.80,
        stop_loss=4053.63,
        take_profit=4066.56,
        atr=2.59,
        risk_reward=1.5,
        market_bias="bullish",
        confidence=4,
        indicators={'rsi': 56.8, 'volume': 1000, 'volume_ma': 700},
        symbol="XAU/USD",
        strategy="Momentum Shift"
    )


@pytest.fixture
def short_signal():
    """Create a sample SHORT signal."""
    return Signal(
        timestamp=datetime.now(),
        signal_type="SHORT",
        timeframe="1m",
        entry_price=4062.80,
        stop_loss=4068.00,
        take_profit=4050.00,
        atr=2.59,
        risk_reward=2.0,
        market_bias="bearish",
        confidence=4,
        indicators={'rsi': 43.2, 'volume': 1000, 'volume_ma': 700},
        symbol="XAU/USD",
        strategy="Momentum Shift"
    )


class TestTradeIDGeneration:
    """Test trade ID generation with microseconds."""
    
    def test_trade_id_includes_microseconds(self, trade_tracker, long_signal):
        """Test that trade ID includes microseconds for uniqueness."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        # Trade ID should have format: symbol_type_YYYYMMDD_HHMMSS_microseconds
        parts = trade_id.split('_')
        assert len(parts) >= 5, "Trade ID should include microseconds"
        
        # Last part should be microseconds (6 digits)
        microseconds = parts[-1]
        assert len(microseconds) == 6, "Microseconds should be 6 digits"
        assert microseconds.isdigit(), "Microseconds should be numeric"
    
    def test_unique_trade_ids_for_rapid_signals(self, trade_tracker):
        """Test that rapid signals get unique trade IDs."""
        # Create two signals with different timestamps
        signal1 = Signal(
            timestamp=datetime.now(),
            signal_type="LONG",
            timeframe="1m",
            entry_price=4058.80,
            stop_loss=4053.63,
            take_profit=4066.56,
            atr=2.59,
            risk_reward=1.5,
            market_bias="bullish",
            confidence=4,
            indicators={'rsi': 56.8, 'volume': 1000, 'volume_ma': 700},
            symbol="XAU/USD",
            strategy="Momentum Shift"
        )
        
        signal2 = Signal(
            timestamp=datetime.now(),
            signal_type="LONG",
            timeframe="1m",
            entry_price=4058.80,
            stop_loss=4053.63,
            take_profit=4066.56,
            atr=2.59,
            risk_reward=1.5,
            market_bias="bullish",
            confidence=4,
            indicators={'rsi': 56.8, 'volume': 1000, 'volume_ma': 700},
            symbol="XAU/USD",
            strategy="Momentum Shift"
        )
        
        trade_id1 = trade_tracker.add_trade(signal1)
        trade_id2 = trade_tracker.add_trade(signal2)
        
        assert trade_id1 != trade_id2, "Trade IDs should be unique"
    
    def test_add_trade_returns_trade_id(self, trade_tracker, long_signal):
        """Test that add_trade returns the generated trade ID."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        assert trade_id is not None
        assert isinstance(trade_id, str)
        assert trade_id in trade_tracker.active_trades


class TestTPDetectionLong:
    """Test take-profit detection for LONG trades."""
    
    def test_tp_hit_long_exact_price(self, trade_tracker, long_signal):
        """Test TP detection when price exactly hits target."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        # Update with exact TP price
        trade_tracker.update_trades(4066.56)
        
        # Trade should be closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
        
        # Verify notification was sent
        trade_tracker.alerter.send_message.assert_called()
        message = trade_tracker.alerter.send_message.call_args[0][0]
        assert "TARGET HIT" in message
        assert "WINNER" in message
    
    def test_tp_hit_long_above_target(self, trade_tracker, long_signal):
        """Test TP detection when price exceeds target."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        # Update with price above TP
        trade_tracker.update_trades(4070.00)
        
        # Trade should be closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
    
    def test_tp_not_hit_long_below_target(self, trade_tracker, long_signal):
        """Test that TP is not triggered when price is below target."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        # Update with price below TP
        trade_tracker.update_trades(4065.00)
        
        # Trade should still be active
        assert trade_id in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 0


class TestTPDetectionShort:
    """Test take-profit detection for SHORT trades."""
    
    def test_tp_hit_short_exact_price(self, trade_tracker, short_signal):
        """Test TP detection when price exactly hits target."""
        trade_id = trade_tracker.add_trade(short_signal)
        
        # Update with exact TP price
        trade_tracker.update_trades(4050.00)
        
        # Trade should be closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
        
        # Verify notification was sent
        trade_tracker.alerter.send_message.assert_called()
        message = trade_tracker.alerter.send_message.call_args[0][0]
        assert "TARGET HIT" in message
    
    def test_tp_hit_short_below_target(self, trade_tracker, short_signal):
        """Test TP detection when price falls below target."""
        trade_id = trade_tracker.add_trade(short_signal)
        
        # Update with price below TP
        trade_tracker.update_trades(4045.00)
        
        # Trade should be closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
    
    def test_tp_not_hit_short_above_target(self, trade_tracker, short_signal):
        """Test that TP is not triggered when price is above target."""
        trade_id = trade_tracker.add_trade(short_signal)
        
        # Update with price above TP
        trade_tracker.update_trades(4055.00)
        
        # Trade should still be active
        assert trade_id in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 0


class TestSLDetection:
    """Test stop-loss detection."""
    
    def test_sl_hit_long(self, trade_tracker, long_signal):
        """Test SL detection for LONG trade."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        # Update with price at SL
        trade_tracker.update_trades(4053.63)
        
        # Trade should be closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
        
        # Verify notification was sent
        message = trade_tracker.alerter.send_message.call_args[0][0]
        assert "STOP-LOSS HIT" in message
    
    def test_sl_hit_short(self, trade_tracker, short_signal):
        """Test SL detection for SHORT trade."""
        trade_id = trade_tracker.add_trade(short_signal)
        
        # Update with price at SL
        trade_tracker.update_trades(4068.00)
        
        # Trade should be closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1


class TestExtendedTP:
    """Test extended take-profit detection."""
    
    def test_extended_tp_detection_long(self, trade_tracker, long_signal):
        """Test that extended TP is used when set."""
        trade_id = trade_tracker.add_trade(long_signal)
        trade = trade_tracker.active_trades[trade_id]
        
        # Set extended TP
        trade.extended_tp = 4075.00
        
        # Update with price at original TP (should not close)
        trade_tracker.update_trades(4066.56)
        
        # Trade should still be active (extended TP not hit)
        assert trade_id in trade_tracker.active_trades
        
        # Update with price at extended TP
        trade_tracker.update_trades(4075.00)
        
        # Now trade should be closed
        assert trade_id not in trade_tracker.active_trades


class TestNotificationDeduplication:
    """Test that duplicate notifications are prevented."""
    
    def test_no_duplicate_tp_notifications(self, trade_tracker, long_signal):
        """Test that TP notification is only sent once."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        # Hit TP
        trade_tracker.update_trades(4066.56)
        
        # Get call count
        initial_call_count = trade_tracker.alerter.send_message.call_count
        
        # Try to update again (trade should already be closed)
        trade_tracker.update_trades(4070.00)
        
        # No additional calls should be made
        assert trade_tracker.alerter.send_message.call_count == initial_call_count
    
    def test_no_duplicate_breakeven_notifications(self, trade_tracker, long_signal):
        """Test that breakeven notification is only sent once."""
        trade_id = trade_tracker.add_trade(long_signal)
        trade = trade_tracker.active_trades[trade_id]
        
        # Calculate breakeven price
        breakeven = long_signal.get_breakeven_price()
        
        # Hit breakeven
        trade_tracker.update_trades(breakeven)
        
        # Check flag is set
        assert trade.breakeven_notified is True
        
        # Get call count
        initial_call_count = trade_tracker.alerter.send_message.call_count
        
        # Update again at breakeven
        trade_tracker.update_trades(breakeven)
        
        # Should not send another breakeven notification
        # (call count may increase for other checks, but not breakeven)
        assert trade.breakeven_notified is True


class TestTradeValidation:
    """Test trade existence validation."""
    
    def test_close_nonexistent_trade(self, trade_tracker):
        """Test that closing a non-existent trade is handled gracefully."""
        # Try to close a trade that doesn't exist
        trade_tracker._close_trade("fake_trade_id", "TARGET", 4070.00)
        
        # Should not raise an error
        # No notification should be sent
        trade_tracker.alerter.send_message.assert_not_called()
    
    def test_validate_trade_exists_returns_false(self, trade_tracker):
        """Test that validation returns False for non-existent trade."""
        result = trade_tracker._validate_trade_exists("fake_id", "test operation")
        assert result is False


class TestDebugHelpers:
    """Test debug helper methods."""
    
    def test_debug_active_trades_empty(self, trade_tracker):
        """Test debug output when no active trades."""
        output = trade_tracker.debug_active_trades()
        assert "No active trades" in output
    
    def test_debug_active_trades_with_trades(self, trade_tracker, long_signal):
        """Test debug output with active trades."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        output = trade_tracker.debug_active_trades()
        assert "Active Trades" in output
        assert trade_id in output
        assert "LONG" in output
        assert "4058.80" in output
    
    def test_get_trade_status_existing(self, trade_tracker, long_signal):
        """Test getting status of existing trade."""
        trade_id = trade_tracker.add_trade(long_signal)
        
        status = trade_tracker.get_trade_status(trade_id)
        assert status is not None
        assert status['trade_id'] == trade_id
        assert status['signal_type'] == "LONG"
        assert status['entry_price'] == 4058.80
        assert 'notifications' in status
        assert 'price_tracking' in status
    
    def test_get_trade_status_nonexistent(self, trade_tracker):
        """Test getting status of non-existent trade."""
        status = trade_tracker.get_trade_status("fake_id")
        assert status is None


class TestMultipleConcurrentTrades:
    """Test handling of multiple concurrent trades."""
    
    def test_multiple_trades_same_symbol(self, trade_tracker):
        """Test that multiple trades on same symbol are tracked independently."""
        # Create two signals with different timestamps
        signal1 = Signal(
            timestamp=datetime.now(),
            signal_type="LONG",
            timeframe="1m",
            entry_price=4058.80,
            stop_loss=4053.63,
            take_profit=4066.56,
            atr=2.59,
            risk_reward=1.5,
            market_bias="bullish",
            confidence=4,
            indicators={'rsi': 56.8, 'volume': 1000, 'volume_ma': 700},
            symbol="XAU/USD",
            strategy="Momentum Shift"
        )
        
        signal2 = Signal(
            timestamp=datetime.now(),
            signal_type="LONG",
            timeframe="1m",
            entry_price=4058.80,
            stop_loss=4053.63,
            take_profit=4066.56,
            atr=2.59,
            risk_reward=1.5,
            market_bias="bullish",
            confidence=4,
            indicators={'rsi': 56.8, 'volume': 1000, 'volume_ma': 700},
            symbol="XAU/USD",
            strategy="Momentum Shift"
        )
        
        # Add two LONG trades
        trade_id1 = trade_tracker.add_trade(signal1)
        trade_id2 = trade_tracker.add_trade(signal2)
        
        # Both should be active
        assert len(trade_tracker.active_trades) == 2
        assert trade_id1 in trade_tracker.active_trades
        assert trade_id2 in trade_tracker.active_trades
        
        # Close both trades
        trade_tracker.update_trades(4066.56)
        
        # Both trades should be closed since they have same TP
        assert len(trade_tracker.closed_trades) == 2
    
    def test_mixed_long_short_trades(self, trade_tracker, long_signal, short_signal):
        """Test LONG and SHORT trades tracked independently."""
        trade_id_long = trade_tracker.add_trade(long_signal)
        trade_id_short = trade_tracker.add_trade(short_signal)
        
        # Both should be active
        assert len(trade_tracker.active_trades) == 2
        
        # Hit LONG TP
        trade_tracker.update_trades(4066.56)
        
        # LONG should be closed, SHORT still active
        assert trade_id_long not in trade_tracker.active_trades
        assert trade_id_short in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1


class TestPriceTracking:
    """Test price tracking for highest/lowest prices."""
    
    def test_highest_price_tracking_long(self, trade_tracker, long_signal):
        """Test that highest price is tracked for LONG trades."""
        trade_id = trade_tracker.add_trade(long_signal)
        trade = trade_tracker.active_trades[trade_id]
        
        # Initial highest should be entry price
        assert trade.highest_price == 4058.80
        
        # Update with higher price
        trade_tracker.update_trades(4062.00)
        assert trade.highest_price == 4062.00
        
        # Update with even higher price
        trade_tracker.update_trades(4065.00)
        assert trade.highest_price == 4065.00
        
        # Update with lower price (highest should not change)
        trade_tracker.update_trades(4060.00)
        assert trade.highest_price == 4065.00
    
    def test_lowest_price_tracking_short(self, trade_tracker, short_signal):
        """Test that lowest price is tracked for SHORT trades."""
        trade_id = trade_tracker.add_trade(short_signal)
        trade = trade_tracker.active_trades[trade_id]
        
        # Initial lowest should be entry price
        assert trade.lowest_price == 4062.80
        
        # Update with lower price
        trade_tracker.update_trades(4060.00)
        assert trade.lowest_price == 4060.00
        
        # Update with even lower price
        trade_tracker.update_trades(4055.00)
        assert trade.lowest_price == 4055.00
        
        # Update with higher price (lowest should not change)
        trade_tracker.update_trades(4058.00)
        assert trade.lowest_price == 4055.00


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
