"""Integration tests for TradeTracker end-to-end trade lifecycle."""
import pytest
from datetime import datetime
from unittest.mock import Mock
from src.trade_tracker import TradeTracker
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


class TestEndToEndTPFlow:
    """Test complete trade lifecycle from signal to TP hit."""
    
    def test_long_trade_full_lifecycle_to_tp(self, trade_tracker):
        """Test complete LONG trade from entry to TP hit."""
        # Create signal
        signal = Signal(
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
        
        # Add trade
        trade_id = trade_tracker.add_trade(signal)
        assert trade_id in trade_tracker.active_trades
        assert len(trade_tracker.active_trades) == 1
        
        # Simulate price movement toward TP
        # Price moves up but not to breakeven yet
        trade_tracker.update_trades(4060.00)
        assert trade_id in trade_tracker.active_trades
        
        # Price reaches breakeven (50% to target)
        breakeven = signal.get_breakeven_price()
        trade_tracker.update_trades(breakeven)
        
        # Trade should still be active, breakeven notification sent
        assert trade_id in trade_tracker.active_trades
        trade = trade_tracker.active_trades[trade_id]
        assert trade.breakeven_notified is True
        
        # Price continues toward TP
        trade_tracker.update_trades(4065.00)
        assert trade_id in trade_tracker.active_trades
        
        # Price hits TP
        trade_tracker.update_trades(4066.56)
        
        # Verify trade is closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
        
        # Verify closed trade details
        closed_trade = trade_tracker.closed_trades[0]
        assert closed_trade.status == "CLOSED_TP"
        assert closed_trade.target_notified is True
        
        # Verify TARGET HIT notification was sent
        calls = trade_tracker.alerter.send_message.call_args_list
        target_hit_call = [call for call in calls if "TARGET HIT" in str(call)]
        assert len(target_hit_call) > 0, "TARGET HIT notification should be sent"
        
        # Verify notification contains correct information
        target_message = target_hit_call[0][0][0]
        assert "WINNER" in target_message
        assert "4,058.80" in target_message or "4058.80" in target_message  # Entry price (with or without comma)
        assert "4,066.56" in target_message or "4066.56" in target_message  # Exit price (with or without comma)
        assert "LONG" in target_message
    
    def test_short_trade_full_lifecycle_to_tp(self, trade_tracker):
        """Test complete SHORT trade from entry to TP hit."""
        # Create signal
        signal = Signal(
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
        
        # Add trade
        trade_id = trade_tracker.add_trade(signal)
        
        # Simulate price movement toward TP
        trade_tracker.update_trades(4060.00)
        assert trade_id in trade_tracker.active_trades
        
        # Price reaches breakeven
        breakeven = signal.get_breakeven_price()
        trade_tracker.update_trades(breakeven)
        assert trade_id in trade_tracker.active_trades
        
        # Price hits TP
        trade_tracker.update_trades(4050.00)
        
        # Verify trade is closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
        
        # Verify TARGET HIT notification
        calls = trade_tracker.alerter.send_message.call_args_list
        target_hit_call = [call for call in calls if "TARGET HIT" in str(call)]
        assert len(target_hit_call) > 0
    
    def test_long_trade_full_lifecycle_to_sl(self, trade_tracker):
        """Test complete LONG trade from entry to SL hit."""
        signal = Signal(
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
        
        # Add trade
        trade_id = trade_tracker.add_trade(signal)
        
        # Price moves against us
        trade_tracker.update_trades(4056.00)
        assert trade_id in trade_tracker.active_trades
        
        # Price approaches SL (should trigger warning)
        trade_tracker.update_trades(4054.50)
        trade = trade_tracker.active_trades[trade_id]
        assert trade.stop_warning_sent is True
        
        # Price hits SL
        trade_tracker.update_trades(4053.63)
        
        # Verify trade is closed
        assert trade_id not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
        
        # Verify STOP-LOSS HIT notification
        calls = trade_tracker.alerter.send_message.call_args_list
        sl_hit_call = [call for call in calls if "STOP-LOSS HIT" in str(call)]
        assert len(sl_hit_call) > 0


class TestMultipleConcurrentTradesIntegration:
    """Test multiple trades running concurrently."""
    
    def test_two_long_trades_different_outcomes(self, trade_tracker):
        """Test two LONG trades with different outcomes."""
        # Create first signal
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
        
        # Create second signal with different levels
        signal2 = Signal(
            timestamp=datetime.now(),
            signal_type="LONG",
            timeframe="5m",
            entry_price=4060.00,
            stop_loss=4055.00,
            take_profit=4070.00,
            atr=2.59,
            risk_reward=2.0,
            market_bias="bullish",
            confidence=4,
            indicators={'rsi': 58.0, 'volume': 1200, 'volume_ma': 800},
            symbol="XAU/USD",
            strategy="Trend Following"
        )
        
        # Add both trades
        trade_id1 = trade_tracker.add_trade(signal1)
        trade_id2 = trade_tracker.add_trade(signal2)
        
        assert len(trade_tracker.active_trades) == 2
        
        # Price moves to hit first trade's TP
        trade_tracker.update_trades(4066.56)
        
        # First trade should be closed, second still active
        assert trade_id1 not in trade_tracker.active_trades
        assert trade_id2 in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 1
        
        # Price continues to hit second trade's TP
        trade_tracker.update_trades(4070.00)
        
        # Both trades should be closed
        assert trade_id2 not in trade_tracker.active_trades
        assert len(trade_tracker.closed_trades) == 2
        
        # Verify both got TARGET HIT notifications
        calls = trade_tracker.alerter.send_message.call_args_list
        target_hit_calls = [call for call in calls if "TARGET HIT" in str(call)]
        assert len(target_hit_calls) == 2
    
    def test_long_and_short_trades_concurrent(self, trade_tracker):
        """Test LONG and SHORT trades running at same time."""
        # Create LONG signal
        long_signal = Signal(
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
        
        # Create SHORT signal
        short_signal = Signal(
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
            symbol="BTC/USD",
            strategy="Momentum Shift"
        )
        
        # Add both trades
        trade_id_long = trade_tracker.add_trade(long_signal)
        trade_id_short = trade_tracker.add_trade(short_signal)
        
        assert len(trade_tracker.active_trades) == 2
        
        # Price moves to hit LONG TP (XAU/USD)
        trade_tracker.update_trades(4066.56)
        
        # LONG should be closed, SHORT still active
        assert trade_id_long not in trade_tracker.active_trades
        assert trade_id_short in trade_tracker.active_trades
        
        # Price moves to hit SHORT TP (BTC/USD)
        trade_tracker.update_trades(4050.00)
        
        # Both should be closed
        assert len(trade_tracker.active_trades) == 0
        assert len(trade_tracker.closed_trades) == 2


class TestNotificationSequence:
    """Test that notifications are sent in correct sequence."""
    
    def test_notification_order_for_winning_trade(self, trade_tracker):
        """Test notification sequence for a winning trade."""
        signal = Signal(
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
        
        trade_id = trade_tracker.add_trade(signal)
        
        # Track notification sequence
        notifications = []
        
        def track_notification(msg):
            if "Breakeven" in msg:
                notifications.append("BREAKEVEN")
            elif "TARGET HIT" in msg:
                notifications.append("TARGET_HIT")
            elif "STOP-LOSS" in msg:
                notifications.append("STOP_LOSS")
            return True
        
        trade_tracker.alerter.send_message.side_effect = track_notification
        
        # Move to breakeven
        breakeven = signal.get_breakeven_price()
        trade_tracker.update_trades(breakeven)
        
        # Move to TP
        trade_tracker.update_trades(4066.56)
        
        # Verify sequence
        assert "BREAKEVEN" in notifications
        assert "TARGET_HIT" in notifications
        assert notifications.index("BREAKEVEN") < notifications.index("TARGET_HIT")
    
    def test_no_notifications_after_trade_closed(self, trade_tracker):
        """Test that no notifications are sent after trade is closed."""
        signal = Signal(
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
        
        trade_id = trade_tracker.add_trade(signal)
        
        # Hit TP
        trade_tracker.update_trades(4066.56)
        
        # Get call count
        call_count_after_close = trade_tracker.alerter.send_message.call_count
        
        # Try to update again (trade is already closed)
        trade_tracker.update_trades(4070.00)
        trade_tracker.update_trades(4075.00)
        
        # No additional notifications should be sent
        assert trade_tracker.alerter.send_message.call_count == call_count_after_close


class TestTradeStateManagement:
    """Test trade state transitions."""
    
    def test_trade_status_transitions(self, trade_tracker):
        """Test that trade status transitions correctly."""
        signal = Signal(
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
        
        trade_id = trade_tracker.add_trade(signal)
        trade = trade_tracker.active_trades[trade_id]
        
        # Initial state
        assert trade.status == "ACTIVE"
        assert trade.target_notified is False
        assert trade.breakeven_notified is False
        
        # Move to breakeven
        breakeven = signal.get_breakeven_price()
        trade_tracker.update_trades(breakeven)
        assert trade.breakeven_notified is True
        assert trade.status == "ACTIVE"
        
        # Hit TP
        trade_tracker.update_trades(4066.56)
        
        # Verify final state in closed trades
        closed_trade = trade_tracker.closed_trades[0]
        assert closed_trade.status == "CLOSED_TP"
        assert closed_trade.target_notified is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
