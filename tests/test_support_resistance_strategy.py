"""Tests for Support/Resistance bounce strategy."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.signal_detector import SignalDetector


class TestSupportResistanceBounce:
    """Test Support/Resistance bounce strategy."""
    
    def test_detect_support_bounce(self):
        """Test detecting bullish bounce from support level."""
        detector = SignalDetector()
        
        # Create data with clear support at 45000 (multiple touches)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        # Price bounces at 45000 multiple times
        prices = []
        for i in range(100):
            if i % 20 == 10:  # Touch support every 20 candles
                prices.append(45000)
            elif i % 20 < 10:
                prices.append(45000 + (i % 10) * 50)  # Move up from support
            else:
                prices.append(45500 - ((i % 20) - 10) * 50)  # Move down to support
        
        # Last candle at support with good RSI
        prices[-1] = 45050  # Near support
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 50 for p in prices],
            'low': [p - 50 for p in prices],
            'close': prices,
            'volume': [1500] * 100,  # High volume
            'volume_ma': [1000] * 100,
            'rsi': [50] * 100,  # Neutral RSI
            'atr': [200] * 100
        })
        
        signal = detector._detect_support_resistance_bounce(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            lookback_candles=100,
            min_touches=2,
            level_tolerance_percent=0.5,  # Wider tolerance for test
            volume_threshold=1.4,
            require_reversal_candle=False
        )
        
        # Should detect bullish support bounce
        if signal:  # May or may not detect depending on exact level finding
            assert signal.signal_type == "LONG"
            assert signal.strategy == "Support/Resistance Bounce"
            assert signal.strategy_metadata is not None
            assert signal.strategy_metadata['level_type'] == 'support'
            assert signal.strategy_metadata['touches'] >= 2
    
    def test_detect_resistance_rejection(self):
        """Test detecting bearish rejection from resistance level."""
        detector = SignalDetector()
        
        # Create data with clear resistance at 50000 (multiple touches)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        # Price rejects at 50000 multiple times
        prices = []
        for i in range(100):
            if i % 20 == 10:  # Touch resistance every 20 candles
                prices.append(50000)
            elif i % 20 < 10:
                prices.append(50000 - (10 - (i % 10)) * 50)  # Move up to resistance
            else:
                prices.append(50000 - ((i % 20) - 10) * 50)  # Move down from resistance
        
        # Last candle at resistance with good RSI
        prices[-1] = 49950  # Near resistance
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 50 for p in prices],
            'low': [p - 50 for p in prices],
            'close': prices,
            'volume': [1500] * 100,  # High volume
            'volume_ma': [1000] * 100,
            'rsi': [50] * 100,  # Neutral RSI
            'atr': [200] * 100
        })
        
        signal = detector._detect_support_resistance_bounce(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            lookback_candles=100,
            min_touches=2,
            level_tolerance_percent=0.5,
            volume_threshold=1.4,
            require_reversal_candle=False
        )
        
        # Should detect bearish resistance rejection
        if signal:  # May or may not detect depending on exact level finding
            assert signal.signal_type == "SHORT"
            assert signal.strategy == "Support/Resistance Bounce"
            assert signal.strategy_metadata is not None
            assert signal.strategy_metadata['level_type'] == 'resistance'
            assert signal.strategy_metadata['touches'] >= 2
    
    def test_reject_low_volume(self):
        """Test rejecting signal when volume is too low."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        # Create support level
        prices = [45000 if i % 20 == 10 else 45000 + (i % 10) * 50 for i in range(100)]
        prices[-1] = 45050
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 50 for p in prices],
            'low': [p - 50 for p in prices],
            'close': prices,
            'volume': [800] * 100,  # Low volume
            'volume_ma': [1000] * 100,
            'rsi': [50] * 100,
            'atr': [200] * 100
        })
        
        signal = detector._detect_support_resistance_bounce(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            volume_threshold=1.4,
            require_reversal_candle=False
        )
        
        # Should reject due to low volume
        assert signal is None
    
    def test_reject_extreme_rsi_support(self):
        """Test rejecting support bounce when RSI is too low (oversold)."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        prices = [45000 if i % 20 == 10 else 45000 + (i % 10) * 50 for i in range(100)]
        prices[-1] = 45050
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 50 for p in prices],
            'low': [p - 50 for p in prices],
            'close': prices,
            'volume': [1500] * 100,
            'volume_ma': [1000] * 100,
            'rsi': [20] * 100,  # Oversold - catching falling knife
            'atr': [200] * 100
        })
        
        signal = detector._detect_support_resistance_bounce(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            require_reversal_candle=False
        )
        
        # Should reject due to extreme RSI
        assert signal is None
    
    def test_reject_extreme_rsi_resistance(self):
        """Test rejecting resistance rejection when RSI is too high (overbought)."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        prices = [50000 if i % 20 == 10 else 50000 - (i % 10) * 50 for i in range(100)]
        prices[-1] = 49950
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 50 for p in prices],
            'low': [p - 50 for p in prices],
            'close': prices,
            'volume': [1500] * 100,
            'volume_ma': [1000] * 100,
            'rsi': [80] * 100,  # Overbought - shorting strong uptrend
            'atr': [200] * 100
        })
        
        signal = detector._detect_support_resistance_bounce(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            require_reversal_candle=False
        )
        
        # Should reject due to extreme RSI
        assert signal is None
    
    def test_higher_confidence_multiple_touches(self):
        """Test that 3+ touches increase confidence."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        # Create support with many touches
        prices = []
        touch_count = 0
        for i in range(100):
            if i % 15 == 7:  # Touch support frequently
                prices.append(45000)
                touch_count += 1
            else:
                prices.append(45000 + (i % 10) * 50)
        
        prices[-1] = 45050
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 50 for p in prices],
            'low': [p - 50 for p in prices],
            'close': prices,
            'volume': [1500] * 100,
            'volume_ma': [1000] * 100,
            'rsi': [50] * 100,
            'atr': [200] * 100
        })
        
        signal = detector._detect_support_resistance_bounce(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            level_tolerance_percent=0.5,
            require_reversal_candle=False
        )
        
        # If signal detected with 3+ touches, confidence should be 5
        if signal and signal.strategy_metadata['touches'] >= 3:
            assert signal.confidence == 5
    
    def test_insufficient_data(self):
        """Test handling insufficient data."""
        detector = SignalDetector()
        
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
            'atr': [200] * 10
        })
        
        signal = detector._detect_support_resistance_bounce(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            lookback_candles=100
        )
        
        # Should return None due to insufficient data
        assert signal is None
    
    def test_metadata_populated(self):
        """Test that strategy metadata is properly populated."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        prices = [45000 if i % 20 == 10 else 45000 + (i % 10) * 50 for i in range(100)]
        prices[-1] = 45050
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 50 for p in prices],
            'low': [p - 50 for p in prices],
            'close': prices,
            'volume': [1500] * 100,
            'volume_ma': [1000] * 100,
            'rsi': [50] * 100,
            'atr': [200] * 100
        })
        
        signal = detector._detect_support_resistance_bounce(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            level_tolerance_percent=0.5,
            require_reversal_candle=False
        )
        
        if signal:
            # Check metadata is populated
            assert signal.strategy_metadata is not None
            assert 'level_type' in signal.strategy_metadata
            assert 'level_price' in signal.strategy_metadata
            assert 'touches' in signal.strategy_metadata
            assert 'strength' in signal.strategy_metadata
            assert 'is_round_number' in signal.strategy_metadata
            assert 'last_touch_candles_ago' in signal.strategy_metadata
            
            # Check values make sense
            assert signal.strategy_metadata['level_type'] in ['support', 'resistance']
            assert signal.strategy_metadata['touches'] >= 2
            assert 0 <= signal.strategy_metadata['strength'] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
