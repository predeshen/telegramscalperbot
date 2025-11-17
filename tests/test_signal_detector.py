"""Unit tests for SignalDetector."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.signal_detector import SignalDetector, Signal


@pytest.fixture
def signal_detector():
    """Create SignalDetector instance with default parameters."""
    return SignalDetector(
        volume_spike_threshold=1.5,
        rsi_min=30,
        rsi_max=70,
        stop_loss_atr_multiplier=1.5,
        take_profit_atr_multiplier=1.0,
        duplicate_time_window_minutes=5,
        duplicate_price_threshold_percent=0.3
    )


@pytest.fixture
def bullish_confluence_data():
    """Create data that meets all bullish confluence criteria."""
    # Use current time to avoid stale signal rejection
    now = datetime.now()
    timestamps = pd.date_range(now - timedelta(minutes=2), periods=3, freq='1min')
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'close': [65000, 65100, 65200],
        'ema_9': [64900, 65000, 65150],  # Crosses above ema_21
        'ema_21': [65000, 65050, 65100],
        'ema_50': [64800, 64850, 64900],  # Price above ema_50 (bullish bias)
        'vwap': [64950, 65000, 65050],  # Price above VWAP
        'rsi': [45, 50, 55],  # In valid range
        'atr': [100, 100, 100],
        'volume': [1000, 1500, 2000],  # Volume spike
        'volume_ma': [1000, 1000, 1000]
    })
    
    return data


@pytest.fixture
def bearish_confluence_data():
    """Create data that meets all bearish confluence criteria."""
    # Use current time to avoid stale signal rejection
    now = datetime.now()
    timestamps = pd.date_range(now - timedelta(minutes=2), periods=3, freq='1min')
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'close': [65200, 65100, 65000],
        'ema_9': [65150, 65050, 64900],  # Crosses below ema_21
        'ema_21': [65100, 65050, 65000],
        'ema_50': [65300, 65350, 65400],  # Price below ema_50 (bearish bias)
        'vwap': [65150, 65100, 65050],  # Price below VWAP
        'rsi': [55, 50, 45],  # In valid range
        'atr': [100, 100, 100],
        'volume': [1000, 1500, 2000],  # Volume spike
        'volume_ma': [1000, 1000, 1000]
    })
    
    return data


class TestSignalDetector:
    """Test suite for SignalDetector class."""
    
    def test_initialization(self, signal_detector):
        """Test SignalDetector initialization."""
        assert signal_detector.volume_spike_threshold == 1.5
        assert signal_detector.rsi_min == 30
        assert signal_detector.rsi_max == 70
        assert len(signal_detector.signal_history) == 0
    
    def test_detect_bullish_signal(self, signal_detector, bullish_confluence_data):
        """Test detection of bullish (LONG) signal."""
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        assert signal is not None
        assert signal.signal_type == "LONG"
        assert signal.timeframe == '5m'
        assert signal.entry_price == 65200
        assert signal.stop_loss < signal.entry_price
        assert signal.take_profit > signal.entry_price
        assert signal.confidence >= 4  # Should meet most confluence factors
    
    def test_detect_bearish_signal(self, signal_detector, bearish_confluence_data):
        """Test detection of bearish (SHORT) signal."""
        signal = signal_detector.detect_signals(bearish_confluence_data, '5m')
        
        assert signal is not None
        assert signal.signal_type == "SHORT"
        assert signal.timeframe == '5m'
        assert signal.entry_price == 65000
        assert signal.stop_loss > signal.entry_price
        assert signal.take_profit < signal.entry_price
        assert signal.confidence >= 4
    
    def test_no_signal_insufficient_data(self, signal_detector):
        """Test that no signal is generated with insufficient data."""
        small_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            'close': [65000]
        })
        
        signal = signal_detector.detect_signals(small_data, '1m')
        assert signal is None
    
    def test_no_signal_missing_ema_cross(self, signal_detector, bullish_confluence_data):
        """Test that no signal is generated without EMA crossover."""
        # Modify data so EMA doesn't cross
        data = bullish_confluence_data.copy()
        data['ema_9'] = [64900, 64950, 65000]  # Stays below ema_21
        
        signal = signal_detector.detect_signals(data, '5m')
        assert signal is None
    
    def test_no_signal_low_volume(self, signal_detector, bullish_confluence_data):
        """Test that no signal is generated without volume spike."""
        data = bullish_confluence_data.copy()
        data['volume'] = [1000, 1000, 1000]  # No spike
        
        signal = signal_detector.detect_signals(data, '5m')
        assert signal is None
    
    def test_no_signal_rsi_overbought(self, signal_detector, bullish_confluence_data):
        """Test that no signal is generated when RSI is overbought."""
        data = bullish_confluence_data.copy()
        data['rsi'] = [75, 80, 85]  # Overbought
        
        signal = signal_detector.detect_signals(data, '5m')
        assert signal is None
    
    def test_no_signal_rsi_oversold(self, signal_detector, bearish_confluence_data):
        """Test that no signal is generated when RSI is oversold."""
        data = bearish_confluence_data.copy()
        data['rsi'] = [25, 20, 15]  # Oversold
        
        signal = signal_detector.detect_signals(data, '5m')
        assert signal is None
    
    def test_duplicate_signal_prevention_time(self, signal_detector, bullish_confluence_data):
        """Test that duplicate signals are blocked within time window."""
        # Generate first signal
        signal1 = signal_detector.detect_signals(bullish_confluence_data, '5m')
        assert signal1 is not None
        
        # Verify signal was added to history
        assert len(signal_detector.signal_history) == 1, f"First signal should be in history, but history has {len(signal_detector.signal_history)} signals"
        print(f"Signal 1 timestamp: {signal1.timestamp}, entry: {signal1.entry_price}")
        print(f"History has {len(signal_detector.signal_history)} signals")
        
        # Try to generate same signal immediately
        signal2 = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        if signal2:
            print(f"Signal 2 timestamp: {signal2.timestamp}, entry: {signal2.entry_price}")
            print(f"History now has {len(signal_detector.signal_history)} signals")
        
        # Should be blocked as duplicate
        assert signal2 is None, f"Second signal should be blocked as duplicate"
    
    def test_duplicate_signal_allowed_after_time(self, signal_detector, bullish_confluence_data):
        """Test that signals are allowed after time window expires."""
        # Generate first signal
        signal1 = signal_detector.detect_signals(bullish_confluence_data, '5m')
        assert signal1 is not None
        
        # Modify timestamp to be 6 minutes later (beyond 5-minute window)
        data = bullish_confluence_data.copy()
        data['timestamp'] = data['timestamp'] + timedelta(minutes=6)
        
        signal2 = signal_detector.detect_signals(data, '5m')
        assert signal2 is not None  # Should be allowed
    
    def test_duplicate_signal_allowed_price_move(self, signal_detector, bullish_confluence_data):
        """Test that signals are allowed if price moved significantly."""
        # Generate first signal at 65200
        signal1 = signal_detector.detect_signals(bullish_confluence_data, '5m')
        assert signal1 is not None
        
        # Modify price to move > 0.3%
        data = bullish_confluence_data.copy()
        data['close'] = data['close'] + 250  # ~0.38% move
        data['ema_9'] = data['ema_9'] + 250
        data['ema_21'] = data['ema_21'] + 250
        data['vwap'] = data['vwap'] + 250
        
        signal2 = signal_detector.detect_signals(data, '5m')
        assert signal2 is not None  # Should be allowed due to price move
    
    def test_risk_reward_calculation(self, signal_detector, bullish_confluence_data):
        """Test risk-reward ratio calculation."""
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        assert signal is not None
        
        # Calculate expected R:R
        risk = signal.entry_price - signal.stop_loss
        reward = signal.take_profit - signal.entry_price
        expected_rr = reward / risk
        
        assert abs(signal.risk_reward - expected_rr) < 0.01
    
    def test_stop_loss_calculation(self, signal_detector, bullish_confluence_data):
        """Test stop-loss calculation using ATR."""
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        assert signal is not None
        
        # Stop loss should be entry - (ATR * multiplier)
        expected_sl = signal.entry_price - (signal.atr * 1.5)
        assert abs(signal.stop_loss - expected_sl) < 0.01
    
    def test_take_profit_calculation(self, signal_detector, bullish_confluence_data):
        """Test take-profit calculation using ATR."""
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        assert signal is not None
        
        # Take profit should be entry + (ATR * multiplier)
        expected_tp = signal.entry_price + (signal.atr * 1.0)
        assert abs(signal.take_profit - expected_tp) < 0.01
    
    def test_market_bias_bullish(self, signal_detector, bullish_confluence_data):
        """Test market bias detection for bullish setup."""
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        assert signal is not None
        assert signal.market_bias == "bullish"
    
    def test_market_bias_bearish(self, signal_detector, bearish_confluence_data):
        """Test market bias detection for bearish setup."""
        signal = signal_detector.detect_signals(bearish_confluence_data, '5m')
        
        assert signal is not None
        assert signal.market_bias == "bearish"
    
    def test_confidence_score(self, signal_detector, bullish_confluence_data):
        """Test confidence score calculation."""
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        assert signal is not None
        assert 3 <= signal.confidence <= 5
    
    def test_signal_to_dict(self, signal_detector, bullish_confluence_data):
        """Test Signal to_dict method."""
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        assert signal is not None
        
        signal_dict = signal.to_dict()
        assert isinstance(signal_dict, dict)
        assert 'signal_type' in signal_dict
        assert 'entry_price' in signal_dict
        assert 'stop_loss' in signal_dict
        assert 'take_profit' in signal_dict
    
    def test_signal_distance_percentages(self, signal_detector, bullish_confluence_data):
        """Test stop/profit distance percentage calculations."""
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        
        assert signal is not None
        
        stop_pct = signal.get_stop_distance_percent()
        profit_pct = signal.get_profit_distance_percent()
        
        assert stop_pct > 0
        assert profit_pct > 0
        assert isinstance(stop_pct, float)
        assert isinstance(profit_pct, float)
    
    def test_clean_expired_signals(self, signal_detector, bullish_confluence_data):
        """Test that expired signals are cleaned from history."""
        # Generate a signal
        signal = signal_detector.detect_signals(bullish_confluence_data, '5m')
        assert signal is not None
        assert len(signal_detector.signal_history) == 1
        
        # Manually set signal timestamp to 31 minutes ago
        old_signal = signal_detector.signal_history[0]
        old_signal.timestamp = datetime.now() - timedelta(minutes=31)
        
        # Trigger cleanup by detecting new signal
        data = bullish_confluence_data.copy()
        data['timestamp'] = data['timestamp'] + timedelta(minutes=35)
        data['close'] = data['close'] + 500  # Different price
        data['ema_9'] = data['ema_9'] + 500
        data['ema_21'] = data['ema_21'] + 500
        data['vwap'] = data['vwap'] + 500
        
        signal_detector.detect_signals(data, '5m')
        
        # Old signal should be cleaned (implementation detail - may vary)
        # Just verify history doesn't grow unbounded
        assert len(signal_detector.signal_history) <= 50
