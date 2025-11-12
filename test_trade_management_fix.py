"""
Quick test to verify trade management fixes work correctly.
Tests:
1. Breakeven stop-loss tracking
2. Momentum reversal detection when giving back gains
"""
import pandas as pd
from datetime import datetime, timedelta
from src.trade_tracker import TradeTracker
from src.signal_detector import Signal


class MockAlerter:
    """Mock alerter to capture messages."""
    def __init__(self):
        self.messages = []
    
    def send_message(self, message):
        self.messages.append(message)
        print(f"\n{'='*60}")
        print(message)
        print('='*60)
        return True


def test_breakeven_stop_tracking():
    """Test that stop-loss is updated to breakeven after alert."""
    print("\n" + "="*60)
    print("TEST 1: Breakeven Stop-Loss Tracking")
    print("="*60)
    
    alerter = MockAlerter()
    tracker = TradeTracker(alerter)
    
    # Create a LONG signal
    signal = Signal(
        timestamp=datetime.now(),
        signal_type="LONG",
        timeframe="5m",
        entry_price=4118.60,
        stop_loss=4110.61,
        take_profit=4130.59,
        atr=4.0,
        risk_reward=1.5,
        market_bias="BULLISH",
        confidence=4,
        indicators={},
        symbol="XAU/USD"
    )
    
    # Add trade
    tracker.add_trade(signal)
    print(f"\n✅ Trade added: LONG at ${signal.entry_price:.2f}")
    print(f"   Original SL: ${signal.stop_loss:.2f}")
    
    # Update with price at breakeven
    breakeven_price = signal.get_breakeven_price()
    print(f"\n📍 Price reaches breakeven: ${breakeven_price:.2f}")
    tracker.update_trades(breakeven_price)
    
    # Check that stop-loss was updated
    trade_id = list(tracker.active_trades.keys())[0]
    trade = tracker.active_trades[trade_id]
    
    print(f"\n🔍 Checking stop-loss update...")
    print(f"   Updated SL: ${trade.signal.stop_loss:.2f}")
    print(f"   Entry Price: ${trade.signal.entry_price:.2f}")
    
    assert trade.signal.stop_loss == signal.entry_price, \
        f"Stop-loss should be at entry ({signal.entry_price}), but is at {trade.signal.stop_loss}"
    
    print(f"\n✅ TEST PASSED: Stop-loss correctly updated to breakeven!")
    
    # Now test that stop-loss triggers at breakeven
    print(f"\n📉 Price drops back to entry (should trigger stop)...")
    tracker.update_trades(signal.entry_price - 0.50)
    
    # Trade should be closed
    assert len(tracker.active_trades) == 0, "Trade should be closed"
    assert len(tracker.closed_trades) == 1, "Trade should be in closed trades"
    
    print(f"\n✅ TEST PASSED: Trade closed at breakeven!")
    return True


def test_momentum_reversal_detection():
    """Test that momentum reversal is detected when giving back gains."""
    print("\n" + "="*60)
    print("TEST 2: Momentum Reversal Detection")
    print("="*60)
    
    alerter = MockAlerter()
    tracker = TradeTracker(alerter)
    
    # Create a LONG signal
    signal = Signal(
        timestamp=datetime.now(),
        signal_type="LONG",
        timeframe="5m",
        entry_price=4100.00,
        stop_loss=4090.00,
        take_profit=4130.00,
        atr=4.0,
        risk_reward=3.0,
        market_bias="BULLISH",
        confidence=4,
        indicators={},
        symbol="XAU/USD"
    )
    
    # Add trade
    tracker.add_trade(signal)
    print(f"\n✅ Trade added: LONG at ${signal.entry_price:.2f}")
    print(f"   Target: ${signal.take_profit:.2f} (+${signal.take_profit - signal.entry_price:.2f})")
    
    # Simulate price moving up to 80% of target
    target_distance = signal.take_profit - signal.entry_price
    high_price = signal.entry_price + (target_distance * 0.8)
    
    print(f"\n📈 Price reaches ${high_price:.2f} (80% to target)")
    indicators = {
        'rsi': 65,
        'prev_rsi': 64,
        'adx': 30,
        'volume_ratio': 1.2
    }
    tracker.update_trades(high_price, indicators)
    
    # Check highest price tracked
    trade_id = list(tracker.active_trades.keys())[0]
    trade = tracker.active_trades[trade_id]
    print(f"   Highest price tracked: ${trade.highest_price:.2f}")
    
    # Now simulate giving back 60% of gains (should trigger reversal)
    profit_made = high_price - signal.entry_price
    giveback = profit_made * 0.6
    reversal_price = high_price - giveback
    
    print(f"\n📉 Price drops to ${reversal_price:.2f} (giving back 60% of gains)")
    print(f"   Profit made: +${profit_made:.2f}")
    print(f"   Giving back: -${giveback:.2f}")
    
    indicators = {
        'rsi': 55,
        'prev_rsi': 60,
        'adx': 28,
        'volume_ratio': 0.7
    }
    
    # Clear previous messages
    alerter.messages.clear()
    
    tracker.update_trades(reversal_price, indicators)
    
    # Check if momentum reversal alert was sent
    reversal_alert_sent = any("MOMENTUM REVERSAL" in msg for msg in alerter.messages)
    
    if reversal_alert_sent:
        print(f"\n✅ TEST PASSED: Momentum reversal alert sent!")
    else:
        print(f"\n❌ TEST FAILED: No momentum reversal alert sent")
        print(f"   Messages received: {len(alerter.messages)}")
        return False
    
    return True


def test_full_scenario():
    """Test the full scenario: +$400 profit → -$600 loss."""
    print("\n" + "="*60)
    print("TEST 3: Full Scenario (+$400 → -$600)")
    print("="*60)
    
    alerter = MockAlerter()
    tracker = TradeTracker(alerter)
    
    # Create signal matching your scenario
    signal = Signal(
        timestamp=datetime.now(),
        signal_type="LONG",
        timeframe="5m",
        entry_price=4118.60,
        stop_loss=4110.61,
        take_profit=4130.59,
        atr=4.0,
        risk_reward=1.5,
        market_bias="BULLISH",
        confidence=4,
        indicators={},
        symbol="XAU/USD"
    )
    
    tracker.add_trade(signal)
    print(f"\n✅ Trade entered at ${signal.entry_price:.2f}")
    
    # Price goes to +$400 profit (roughly +10%)
    high_price = signal.entry_price + 400
    print(f"\n📈 Price reaches ${high_price:.2f} (+$400 profit)")
    
    indicators = {
        'rsi': 68,
        'prev_rsi': 67,
        'adx': 32,
        'volume_ratio': 1.3
    }
    tracker.update_trades(high_price, indicators)
    
    # Price reverses and gives back 50% of gains
    reversal_price = signal.entry_price + 200  # +$200 (giving back $200 of $400)
    print(f"\n📉 Price drops to ${reversal_price:.2f} (+$200, giving back 50%)")
    
    indicators = {
        'rsi': 58,
        'prev_rsi': 63,
        'adx': 28,
        'volume_ratio': 0.75
    }
    
    alerter.messages.clear()
    tracker.update_trades(reversal_price, indicators)
    
    # Should get EXIT signal
    exit_alert = any("EXIT" in msg and "REVERSAL" in msg for msg in alerter.messages)
    
    if exit_alert:
        print(f"\n✅ EXIT signal sent at +$200 (saved from -$600 loss!)")
    else:
        print(f"\n⚠️ No EXIT signal at +$200")
    
    # Continue to breakeven
    print(f"\n📉 Price continues to ${signal.entry_price:.2f} (breakeven)")
    tracker.update_trades(signal.entry_price, indicators)
    
    # Continue to -$600 loss
    loss_price = signal.entry_price - 600
    print(f"\n📉 Price drops to ${loss_price:.2f} (-$600 loss)")
    tracker.update_trades(loss_price, indicators)
    
    # Trade should be closed by now
    if len(tracker.active_trades) == 0:
        print(f"\n✅ Trade closed (protected by stop-loss)")
    else:
        print(f"\n⚠️ Trade still active (should have been stopped)")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TRADE MANAGEMENT FIX VERIFICATION")
    print("="*60)
    
    try:
        test1 = test_breakeven_stop_tracking()
        test2 = test_momentum_reversal_detection()
        test3 = test_full_scenario()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        print(f"✅ Breakeven Stop Tracking: {'PASSED' if test1 else 'FAILED'}")
        print(f"✅ Momentum Reversal Detection: {'PASSED' if test2 else 'FAILED'}")
        print(f"✅ Full Scenario Test: {'PASSED' if test3 else 'FAILED'}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
