"""Tests for ADX+RSI+Momentum confluence strategy."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.signal_detector import SignalDetector


class TestADXRSIMomentum:
    """Test ADX+RSI+Momentum confluence strategy."""
    
    def test_detect_bullish_confluence(self):
        """Test detecting bullish ADX+RSI+Momentum signal."""
        detector = SignalDetector()
        
        # Create data with strong bullish confluence
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        
        # Rising prices (higher highs)
        prices = np.linspace(45000, 47000, 50)
        
        # Rising RSI above 50 with momentum
        # Need last 3 values to show: prev2 < prev < current, with current > 50
        rsi_values = [48] * 47 + [50, 54, 58]  # RSI accelerating above 50 at end
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 50,  # High volume
            'volume_ma': [1000] * 50,
            'rsi': rsi_values,
            'adx': [28] * 50,  # Strong trend
            'atr': [200] * 50
        })
        
        signal = detector._detect_adx_rsi_momentum_confluence(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            adx_min=20,
            adx_strong=25,
            rsi_momentum_threshold=3.0,
            volume_threshold=1.2
        )
        
        # Should detect bullish signal
        assert signal is not None
        assert signal.signal_type == "LONG"
        assert signal.strategy == "ADX+RSI+Momentum"
        assert signal.strategy_metadata is not None
        assert bool(signal.strategy_metadata['is_strong_trend']) is True
    
    def test_detect_bearish_confluence(self):
        """Test detecting bearish ADX+RSI+Momentum signal."""
        detector = SignalDetector()
        
        # Create data with strong bearish confluence
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        
        # Falling prices (lower lows)
        prices = np.linspace(47000, 45000, 50)
        
        # Falling RSI below 50 with momentum
        # Need last 3 values to show: prev2 > prev > current, with current < 50
        rsi_values = [52] * 47 + [50, 46, 42]  # RSI accelerating below 50 at end
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 50,
            'volume_ma': [1000] * 50,
            'rsi': rsi_values,
            'adx': [28] * 50,  # Strong trend
            'atr': [200] * 50
        })
        
        signal = detector._detect_adx_rsi_momentum_confluence(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            adx_min=20,
            adx_strong=25,
            rsi_momentum_threshold=3.0,
            volume_threshold=1.2
        )
        
        # Should detect bearish signal
        assert signal is not None
        assert signal.signal_type == "SHORT"
        assert signal.strategy == "ADX+RSI+Momentum"
        assert bool(signal.strategy_metadata['is_strong_trend']) is True
    
    def test_reject_low_adx(self):
        """Test rejecting signal when ADX is too low."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        prices = np.linspace(45000, 47000, 50)
        rsi_values = [48, 49, 50, 52, 55, 58] + [60] * 44
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 50,
            'volume_ma': [1000] * 50,
            'rsi': rsi_values,
            'adx': [15] * 50,  # ADX too low
            'atr': [200] * 50
        })
        
        signal = detector._detect_adx_rsi_momentum_confluence(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            adx_min=20
        )
        
        # Should reject due to low ADX
        assert signal is None
    
    def test_reject_low_rsi_momentum(self):
        """Test rejecting signal when RSI momentum is insufficient."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        prices = np.linspace(45000, 47000, 50)
        
        # RSI above 50 but not accelerating
        rsi_values = [50, 51, 51.5, 52, 52.5] + [53] * 45  # Slow RSI change
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 50,
            'volume_ma': [1000] * 50,
            'rsi': rsi_values,
            'adx': [28] * 50,
            'atr': [200] * 50
        })
        
        signal = detector._detect_adx_rsi_momentum_confluence(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            rsi_momentum_threshold=3.0
        )
        
        # Should reject due to low RSI momentum
        assert signal is None
    
    def test_reject_low_volume(self):
        """Test rejecting signal when volume is too low."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        prices = np.linspace(45000, 47000, 50)
        rsi_values = [48, 49, 50, 52, 55, 58] + [60] * 44
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [800] * 50,  # Low volume
            'volume_ma': [1000] * 50,
            'rsi': rsi_values,
            'adx': [28] * 50,
            'atr': [200] * 50
        })
        
        signal = detector._detect_adx_rsi_momentum_confluence(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            volume_threshold=1.2
        )
        
        # Should reject due to low volume
        assert signal is None
    
    def test_reject_no_price_momentum(self):
        """Test rejecting signal when price doesn't make higher highs/lower lows."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        
        # Flat prices (no higher highs)
        prices = [45000] * 50
        
        # RSI rising above 50
        rsi_values = [48, 49, 50, 52, 55, 58] + [60] * 44
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': [1500] * 50,
            'volume_ma': [1000] * 50,
            'rsi': rsi_values,
            'adx': [28] * 50,
            'atr': [200] * 50
        })
        
        signal = detector._detect_adx_rsi_momentum_confluence(
            data,
            timeframe="1h",
            symbol="BTC/USD"
        )
        
        # Should reject due to no price momentum
        assert signal is None
    
    def test_higher_confidence_strong_trend(self):
        """Test that strong trend (ADX > 25) increases confidence."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        prices = np.linspace(45000, 47000, 50)
        rsi_values = [48] * 47 + [50, 54, 58]  # RSI accelerating at end
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 50,
            'volume_ma': [1000] * 50,
            'rsi': rsi_values,
            'adx': [30] * 50,  # Very strong trend
            'atr': [200] * 50
        })
        
        signal = detector._detect_adx_rsi_momentum_confluence(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            adx_strong=25
        )
        
        # Should have high confidence
        assert signal is not None
        assert signal.confidence == 5
    
    def test_metadata_populated(self):
        """Test that strategy metadata is properly populated."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        prices = np.linspace(45000, 47000, 50)
        rsi_values = [48] * 47 + [50, 54, 58]  # RSI accelerating at end
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': [1500] * 50,
            'volume_ma': [1000] * 50,
            'rsi': rsi_values,
            'adx': [28] * 50,
            'atr': [200] * 50
        })
        
        signal = detector._detect_adx_rsi_momentum_confluence(
            data,
            timeframe="1h",
            symbol="BTC/USD"
        )
        
        assert signal is not None
        assert signal.strategy_metadata is not None
        assert 'adx' in signal.strategy_metadata
        assert 'adx_rising' in signal.strategy_metadata
        assert 'is_strong_trend' in signal.strategy_metadata
        assert 'rsi' in signal.strategy_metadata
        assert 'rsi_momentum' in signal.strategy_metadata
        assert 'price_momentum' in signal.strategy_metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
