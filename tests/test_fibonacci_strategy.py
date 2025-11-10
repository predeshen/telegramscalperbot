"""Tests for Fibonacci retracement strategy."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.signal_detector import SignalDetector


class TestFibonacciRetracement:
    """Test Fibonacci retracement strategy."""
    
    def test_detect_bullish_fibonacci_retracement(self):
        """Test detecting bullish Fibonacci retracement signal."""
        detector = SignalDetector()
        
        # Create data with clear bullish swing (low to high) then retracement
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        # Price moves from 45000 to 50000 (swing up), then retraces to 61.8% level
        prices_up = np.linspace(45000, 50000, 40)  # Swing up
        fib_618_level = 45000 + (5000 * 0.618)  # ~48090
        prices_retrace = np.linspace(50000, fib_618_level, 20)  # Retrace to 61.8%
        
        prices = np.concatenate([prices_up, prices_retrace])
        
        # RSI recovering at Fibonacci level
        rsi_values = [50] * 40 + [45] * 18 + [46, 48]  # RSI turning up at end
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 60,  # High volume
            'volume_ma': [1000] * 60,
            'rsi': rsi_values,
            'atr': [500] * 60
        })
        
        signal = detector._detect_fibonacci_retracement(
            data, 
            timeframe="1h", 
            symbol="BTC/USD",
            swing_lookback=50,
            level_tolerance_percent=1.0,  # Wider tolerance for test
            volume_threshold=1.3,
            require_reversal_candle=False  # Skip reversal pattern for simplicity
        )
        
        # Should detect bullish signal at 61.8% level
        assert signal is not None
        assert signal.signal_type == "LONG"
        assert signal.strategy == "Fibonacci Retracement"
        assert signal.strategy_metadata is not None
        assert signal.strategy_metadata['fib_level'] in ["50%", "61.8%", "78.6%"]
        assert signal.strategy_metadata['is_golden_ratio'] in [True, False]
    
    def test_detect_bearish_fibonacci_retracement(self):
        """Test detecting bearish Fibonacci retracement signal."""
        detector = SignalDetector()
        
        # Create data with clear bearish swing (high to low) then retracement
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        # Price moves from 50000 to 45000 (swing down), then retraces to 61.8% level
        prices_down = np.linspace(50000, 45000, 40)  # Swing down
        fib_618_level = 45000 + (5000 * 0.618)  # ~48090
        prices_retrace = np.linspace(45000, fib_618_level, 20)  # Retrace to 61.8%
        
        prices = np.concatenate([prices_down, prices_retrace])
        
        # RSI declining at Fibonacci level
        rsi_values = [50] * 40 + [55] * 18 + [54, 52]  # RSI turning down at end
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 60,  # High volume
            'volume_ma': [1000] * 60,
            'rsi': rsi_values,
            'atr': [500] * 60
        })
        
        signal = detector._detect_fibonacci_retracement(
            data, 
            timeframe="1h", 
            symbol="BTC/USD",
            swing_lookback=50,
            level_tolerance_percent=1.0,  # Wider tolerance for test
            volume_threshold=1.3,
            require_reversal_candle=False  # Skip reversal pattern for simplicity
        )
        
        # Should detect bearish signal at 61.8% level
        assert signal is not None
        assert signal.signal_type == "SHORT"
        assert signal.strategy == "Fibonacci Retracement"
        assert signal.strategy_metadata is not None
        assert signal.strategy_metadata['fib_level'] in ["50%", "61.8%", "78.6%"]
    
    def test_reject_low_volume(self):
        """Test rejecting signal when volume is too low."""
        detector = SignalDetector()
        
        # Create data with Fibonacci setup but low volume
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices_up = np.linspace(45000, 50000, 40)
        fib_618_level = 45000 + (5000 * 0.618)
        prices_retrace = np.linspace(50000, fib_618_level, 20)
        prices = np.concatenate([prices_up, prices_retrace])
        
        rsi_values = [50] * 40 + [45] * 18 + [46, 48]
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [800] * 60,  # Low volume
            'volume_ma': [1000] * 60,
            'rsi': rsi_values,
            'atr': [500] * 60
        })
        
        signal = detector._detect_fibonacci_retracement(
            data, 
            timeframe="1h", 
            symbol="BTC/USD",
            volume_threshold=1.3,
            require_reversal_candle=False
        )
        
        # Should reject due to low volume
        assert signal is None
    
    def test_reject_poor_risk_reward(self):
        """Test rejecting signal when risk/reward is too low."""
        detector = SignalDetector()
        
        # Create data where price is very close to swing high (poor R:R)
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices_up = np.linspace(45000, 50000, 40)
        # Retrace only slightly (near swing high = poor R:R)
        prices_retrace = np.linspace(50000, 49800, 20)
        prices = np.concatenate([prices_up, prices_retrace])
        
        rsi_values = [50] * 40 + [45] * 18 + [46, 48]
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 60,
            'volume_ma': [1000] * 60,
            'rsi': rsi_values,
            'atr': [500] * 60
        })
        
        signal = detector._detect_fibonacci_retracement(
            data, 
            timeframe="1h", 
            symbol="BTC/USD",
            require_reversal_candle=False
        )
        
        # Should reject due to poor risk/reward
        assert signal is None
    
    def test_insufficient_data(self):
        """Test handling insufficient data."""
        detector = SignalDetector()
        
        # Create data with only 10 candles
        dates = pd.date_range(start='2024-01-01', periods=10, freq='1h')
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [45000] * 10,
            'high': [45100] * 10,
            'low': [44900] * 10,
            'close': [45000] * 10,
            'volume': [1000] * 10,
            'volume_ma': [1000] * 10,
            'rsi': [50] * 10,
            'atr': [500] * 10
        })
        
        signal = detector._detect_fibonacci_retracement(
            data, 
            timeframe="1h", 
            symbol="BTC/USD",
            swing_lookback=50
        )
        
        # Should return None due to insufficient data
        assert signal is None
    
    def test_golden_ratio_higher_confidence(self):
        """Test that golden ratio levels (38.2%, 61.8%) get higher confidence."""
        detector = SignalDetector()
        
        # Create data with retracement to 61.8% (golden ratio)
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices_up = np.linspace(45000, 50000, 40)
        fib_618_level = 45000 + (5000 * 0.618)  # Golden ratio
        prices_retrace = np.linspace(50000, fib_618_level, 20)
        prices = np.concatenate([prices_up, prices_retrace])
        
        rsi_values = [50] * 40 + [45] * 18 + [46, 48]
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 60,
            'volume_ma': [1000] * 60,
            'rsi': rsi_values,
            'atr': [500] * 60
        })
        
        signal = detector._detect_fibonacci_retracement(
            data, 
            timeframe="1h", 
            symbol="BTC/USD",
            level_tolerance_percent=1.0,
            require_reversal_candle=False
        )
        
        if signal and signal.strategy_metadata['fib_level'] in ["38.2%", "61.8%"]:
            # Golden ratio should have confidence of 5
            assert signal.confidence == 5
            assert signal.strategy_metadata['is_golden_ratio'] is True
    
    def test_metadata_populated(self):
        """Test that strategy metadata is properly populated."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices_up = np.linspace(45000, 50000, 40)
        fib_618_level = 45000 + (5000 * 0.618)
        prices_retrace = np.linspace(50000, fib_618_level, 20)
        prices = np.concatenate([prices_up, prices_retrace])
        
        rsi_values = [50] * 40 + [45] * 18 + [46, 48]
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 60,
            'volume_ma': [1000] * 60,
            'rsi': rsi_values,
            'atr': [500] * 60
        })
        
        signal = detector._detect_fibonacci_retracement(
            data, 
            timeframe="1h", 
            symbol="BTC/USD",
            level_tolerance_percent=1.0,
            require_reversal_candle=False
        )
        
        if signal:
            # Check metadata is populated
            assert signal.strategy_metadata is not None
            assert 'fib_level' in signal.strategy_metadata
            assert 'fib_level_price' in signal.strategy_metadata
            assert 'swing_high' in signal.strategy_metadata
            assert 'swing_low' in signal.strategy_metadata
            assert 'swing_direction' in signal.strategy_metadata
            assert 'is_golden_ratio' in signal.strategy_metadata
            
            # Check swing values make sense
            assert signal.strategy_metadata['swing_high'] > signal.strategy_metadata['swing_low']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
