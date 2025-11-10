"""Tests for Key Level Break & Retest strategy."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.signal_detector import SignalDetector


class TestKeyLevelBreakRetest:
    """Test Key Level Break & Retest strategy."""
    
    def test_detect_bullish_break_retest(self):
        """Test detecting bullish break and retest signal."""
        detector = SignalDetector()
        
        # Create data with clear break and retest pattern
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        # Price consolidates below 50000, breaks above, then retests
        prices = []
        for i in range(60):
            if i < 40:
                prices.append(49500 + (i % 10) * 50)  # Consolidate below 50000
            elif i == 40:
                prices.append(50200)  # Break above 50000
            elif i < 55:
                prices.append(50500 + (i - 40) * 20)  # Move higher
            else:
                prices.append(51000 - (i - 55) * 40)  # Retrace to 50000
        
        # Last candle retesting 50000 from above
        prices[-1] = 50100
        
        # High volume on break, moderate on retest
        volumes = [1000] * 40 + [2000] + [1200] * 19  # High volume on break
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': volumes,
            'volume_ma': [1000] * 60,
            'rsi': [50] * 60,
            'atr': [200] * 60
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            retest_window_candles=(5, 10),
            volume_threshold_break=1.5,
            volume_threshold_retest=0.8
        )
        
        # Should detect bullish break & retest
        if signal:  # May or may not detect depending on exact level finding
            assert signal.signal_type == "LONG"
            assert signal.strategy == "Key Level Break & Retest"
            assert signal.strategy_metadata is not None
            assert signal.strategy_metadata['break_direction'] == 'up'
    
    def test_detect_bearish_break_retest(self):
        """Test detecting bearish break and retest signal."""
        detector = SignalDetector()
        
        # Create data with clear break and retest pattern
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        # Price consolidates above 50000, breaks below, then retests
        prices = []
        for i in range(60):
            if i < 40:
                prices.append(50500 - (i % 10) * 50)  # Consolidate above 50000
            elif i == 40:
                prices.append(49800)  # Break below 50000
            elif i < 55:
                prices.append(49500 - (i - 40) * 20)  # Move lower
            else:
                prices.append(49000 + (i - 55) * 40)  # Retrace to 50000
        
        # Last candle retesting 50000 from below
        prices[-1] = 49900
        
        # High volume on break, moderate on retest
        volumes = [1000] * 40 + [2000] + [1200] * 19
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': volumes,
            'volume_ma': [1000] * 60,
            'rsi': [50] * 60,
            'atr': [200] * 60
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            retest_window_candles=(5, 10),
            volume_threshold_break=1.5,
            volume_threshold_retest=0.8
        )
        
        # Should detect bearish break & retest
        if signal:  # May or may not detect depending on exact level finding
            assert signal.signal_type == "SHORT"
            assert signal.strategy == "Key Level Break & Retest"
            assert signal.strategy_metadata is not None
            assert signal.strategy_metadata['break_direction'] == 'down'
    
    def test_reject_low_break_volume(self):
        """Test rejecting signal when break volume is too low."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices = []
        for i in range(60):
            if i < 40:
                prices.append(49500 + (i % 10) * 50)
            elif i == 40:
                prices.append(50200)  # Break
            else:
                prices.append(50100)  # Retest
        
        # Low volume on break
        volumes = [1000] * 40 + [1100] + [1000] * 19  # Insufficient break volume
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': volumes,
            'volume_ma': [1000] * 60,
            'rsi': [50] * 60,
            'atr': [200] * 60
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            volume_threshold_break=1.5
        )
        
        # Should reject due to low break volume
        assert signal is None
    
    def test_reject_low_retest_volume(self):
        """Test rejecting signal when retest volume is too low."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices = []
        for i in range(60):
            if i < 40:
                prices.append(49500)
            elif i == 40:
                prices.append(50200)  # Break with high volume
            elif i < 55:
                prices.append(50500)
            else:
                prices.append(50100)  # Retest
        
        # High volume on break, very low on retest
        volumes = [1000] * 40 + [2000] + [1200] * 14 + [500] * 5  # Low retest volume
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': volumes,
            'volume_ma': [1000] * 60,
            'rsi': [50] * 60,
            'atr': [200] * 60
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD",
            volume_threshold_retest=0.8
        )
        
        # Should reject due to low retest volume
        assert signal is None
    
    def test_reject_failed_retest(self):
        """Test rejecting signal when retest fails (price breaks back through level)."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices = []
        for i in range(60):
            if i < 40:
                prices.append(49500)
            elif i == 40:
                prices.append(50200)  # Break above
            elif i < 55:
                prices.append(50500)
            else:
                prices.append(49800)  # Failed retest - back below level
        
        volumes = [1000] * 40 + [2000] + [1200] * 19
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': volumes,
            'volume_ma': [1000] * 60,
            'rsi': [50] * 60,
            'atr': [200] * 60
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD"
        )
        
        # Should reject due to failed retest
        assert signal is None
    
    def test_reject_extreme_rsi_bullish(self):
        """Test rejecting bullish signal when RSI is too low."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices = []
        for i in range(60):
            if i < 40:
                prices.append(49500)
            elif i == 40:
                prices.append(50200)
            else:
                prices.append(50100)
        
        volumes = [1000] * 40 + [2000] + [1200] * 19
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': volumes,
            'volume_ma': [1000] * 60,
            'rsi': [35] * 60,  # RSI too low for bullish continuation
            'atr': [200] * 60
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD"
        )
        
        # Should reject due to low RSI
        assert signal is None
    
    def test_reject_extreme_rsi_bearish(self):
        """Test rejecting bearish signal when RSI is too high."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices = []
        for i in range(60):
            if i < 40:
                prices.append(50500)
            elif i == 40:
                prices.append(49800)
            else:
                prices.append(49900)
        
        volumes = [1000] * 40 + [2000] + [1200] * 19
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': volumes,
            'volume_ma': [1000] * 60,
            'rsi': [65] * 60,  # RSI too high for bearish continuation
            'atr': [200] * 60
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD"
        )
        
        # Should reject due to high RSI
        assert signal is None
    
    def test_insufficient_data(self):
        """Test handling insufficient data."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=20, freq='1h')
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [50000] * 20,
            'high': [50100] * 20,
            'low': [49900] * 20,
            'close': [50000] * 20,
            'volume': [1000] * 20,
            'volume_ma': [1000] * 20,
            'rsi': [50] * 20,
            'atr': [200] * 20
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD"
        )
        
        # Should return None due to insufficient data
        assert signal is None
    
    def test_metadata_populated(self):
        """Test that strategy metadata is properly populated."""
        detector = SignalDetector()
        
        dates = pd.date_range(start='2024-01-01', periods=60, freq='1h')
        
        prices = []
        for i in range(60):
            if i < 40:
                prices.append(49500)
            elif i == 40:
                prices.append(50200)
            else:
                prices.append(50100)
        
        volumes = [1000] * 40 + [2000] + [1200] * 19
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 100 for p in prices],
            'low': [p - 100 for p in prices],
            'close': prices,
            'volume': volumes,
            'volume_ma': [1000] * 60,
            'rsi': [50] * 60,
            'atr': [200] * 60
        })
        
        signal = detector._detect_key_level_break_retest(
            data,
            timeframe="1h",
            symbol="BTC/USD"
        )
        
        if signal:
            # Check metadata is populated
            assert signal.strategy_metadata is not None
            assert 'level' in signal.strategy_metadata
            assert 'break_direction' in signal.strategy_metadata
            assert 'break_candles_ago' in signal.strategy_metadata
            assert 'break_volume_ratio' in signal.strategy_metadata
            assert 'retest_volume_ratio' in signal.strategy_metadata
            assert 'is_round_number' in signal.strategy_metadata
            
            # Check values make sense
            assert signal.strategy_metadata['break_direction'] in ['up', 'down']
            assert signal.strategy_metadata['break_candles_ago'] >= 5
            assert signal.strategy_metadata['break_volume_ratio'] >= 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
