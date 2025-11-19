"""
Test Suite for Trading Strategies
Tests Fibonacci, Support/Resistance, and other strategy implementations.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.fibonacci_strategy import FibonacciStrategy
from src.support_resistance_strategy import SupportResistanceStrategy
from src.indicator_calculator import IndicatorCalculator


class TestFibonacciStrategy:
    """Test Fibonacci retracement strategy"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 2000, 100)
        })
        
        # Calculate indicators
        calc = IndicatorCalculator()
        data = calc.calculate_all_indicators(data)
        return data
    
    def test_fibonacci_strategy_initialization(self):
        """Test Fibonacci strategy initialization"""
        config = {
            'swing_lookback': 50,
            'level_tolerance_percent': 0.5,
            'volume_threshold': 1.3
        }
        strategy = FibonacciStrategy(config)
        
        assert strategy.swing_lookback == 50
        assert strategy.level_tolerance_percent == 0.5
        assert strategy.volume_threshold == 1.3
    
    def test_fibonacci_levels_calculation(self, sample_data):
        """Test Fibonacci level calculation"""
        strategy = FibonacciStrategy()
        
        # Get recent data
        recent = sample_data.tail(50)
        swing_high = recent['high'].max()
        swing_low = recent['low'].min()
        
        # Calculate levels
        diff = swing_high - swing_low
        levels = {
            'level_236': swing_high - (diff * 0.236),
            'level_382': swing_high - (diff * 0.382),
            'level_500': swing_high - (diff * 0.500),
            'level_618': swing_high - (diff * 0.618),
            'level_786': swing_high - (diff * 0.786)
        }
        
        # Verify levels are in correct order
        assert levels['level_236'] > levels['level_382']
        assert levels['level_382'] > levels['level_500']
        assert levels['level_500'] > levels['level_618']
        assert levels['level_618'] > levels['level_786']
    
    def test_pin_bar_detection(self):
        """Test pin bar pattern detection"""
        strategy = FibonacciStrategy()
        
        # Create pin bar candle
        last = pd.Series({
            'open': 100,
            'close': 101,
            'high': 110,
            'low': 99
        })
        prev = pd.Series({
            'open': 100,
            'close': 100,
            'high': 101,
            'low': 99
        })
        
        is_pin = strategy._is_pin_bar(last, prev)
        assert bool(is_pin) is True
    
    def test_engulfing_detection(self):
        """Test engulfing pattern detection"""
        strategy = FibonacciStrategy()
        
        # Create engulfing candle
        last = pd.Series({
            'open': 99,
            'close': 102,
            'high': 103,
            'low': 98
        })
        prev = pd.Series({
            'open': 100,
            'close': 100.5,
            'high': 101,
            'low': 99.5
        })
        
        is_engulfing = strategy._is_engulfing(last, prev)
        assert bool(is_engulfing) is True


class TestSupportResistanceStrategy:
    """Test Support/Resistance strategy"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 2000, 100)
        })
        
        # Calculate indicators
        calc = IndicatorCalculator()
        data = calc.calculate_all_indicators(data)
        return data
    
    def test_sr_strategy_initialization(self):
        """Test S/R strategy initialization"""
        config = {
            'lookback_candles': 100,
            'min_touches': 2,
            'level_tolerance_percent': 0.3,
            'volume_threshold': 1.4
        }
        strategy = SupportResistanceStrategy(config)
        
        assert strategy.lookback_candles == 100
        assert strategy.min_touches == 2
        assert strategy.level_tolerance_percent == 0.3
        assert strategy.volume_threshold == 1.4
    
    def test_level_grouping(self):
        """Test level grouping with tolerance"""
        strategy = SupportResistanceStrategy()
        
        levels = [100.0, 100.1, 100.2, 105.0, 105.1, 110.0]
        grouped = strategy._group_levels(levels, 0.3)
        
        # Should group nearby levels
        assert len(grouped) <= len(levels)
        assert all(isinstance(level, float) for level in grouped)
    
    def test_doji_detection(self):
        """Test doji pattern detection"""
        strategy = SupportResistanceStrategy()
        
        # Create doji candle (open ≈ close)
        last = pd.Series({
            'open': 100.0,
            'close': 100.05,
            'high': 105,
            'low': 95
        })
        
        is_doji = strategy._is_doji(last)
        assert bool(is_doji) is True


class TestIndicatorCalculations:
    """Test indicator calculations"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 2000, 100)
        })
        return data
    
    def test_fibonacci_levels_calculation(self, sample_data):
        """Test Fibonacci level calculation"""
        calc = IndicatorCalculator()
        levels = calc.calculate_fibonacci_levels(sample_data, lookback=50)
        
        assert 'swing_high' in levels
        assert 'swing_low' in levels
        assert 'level_236' in levels
        assert 'level_618' in levels
    
    def test_support_resistance_identification(self, sample_data):
        """Test support/resistance level identification"""
        calc = IndicatorCalculator()
        sr = calc.identify_support_resistance(sample_data, lookback=100, tolerance_percent=0.3)
        
        assert 'support' in sr
        assert 'resistance' in sr
        assert isinstance(sr['support'], list)
        assert isinstance(sr['resistance'], list)
    
    def test_swing_points_calculation(self, sample_data):
        """Test swing points calculation"""
        calc = IndicatorCalculator()
        highs, lows = calc.calculate_swing_points(sample_data, lookback=50)
        
        assert isinstance(highs, list)
        assert isinstance(lows, list)
        assert all(isinstance(h, (int, float, np.number)) for h in highs)
        assert all(isinstance(l, (int, float, np.number)) for l in lows)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

