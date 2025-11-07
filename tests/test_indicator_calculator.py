"""Unit tests for IndicatorCalculator."""
import pytest
import pandas as pd
import numpy as np
from src.indicator_calculator import IndicatorCalculator


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    n = 100
    
    # Generate realistic price data
    base_price = 65000
    price_changes = np.random.randn(n) * 100
    close_prices = base_price + np.cumsum(price_changes)
    
    data = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='1min'),
        'open': close_prices + np.random.randn(n) * 50,
        'high': close_prices + np.abs(np.random.randn(n) * 100),
        'low': close_prices - np.abs(np.random.randn(n) * 100),
        'close': close_prices,
        'volume': np.random.randint(100, 1000, n)
    })
    
    return data


class TestIndicatorCalculator:
    """Test suite for IndicatorCalculator class."""
    
    def test_calculate_ema(self, sample_ohlcv_data):
        """Test EMA calculation."""
        ema = IndicatorCalculator.calculate_ema(sample_ohlcv_data, period=9)
        
        assert len(ema) == len(sample_ohlcv_data)
        assert not ema.isna().all()  # Should have some valid values
        assert ema.iloc[-1] > 0  # Last value should be positive (price-like)
        
        # EMA should be smoother than raw prices
        ema_volatility = ema.diff().std()
        price_volatility = sample_ohlcv_data['close'].diff().std()
        assert ema_volatility < price_volatility
    
    def test_calculate_ema_different_periods(self, sample_ohlcv_data):
        """Test that longer EMA periods are smoother."""
        ema_9 = IndicatorCalculator.calculate_ema(sample_ohlcv_data, period=9)
        ema_21 = IndicatorCalculator.calculate_ema(sample_ohlcv_data, period=21)
        
        # Longer period should be smoother (less volatile)
        volatility_9 = ema_9.diff().std()
        volatility_21 = ema_21.diff().std()
        assert volatility_21 < volatility_9
    
    def test_calculate_vwap(self, sample_ohlcv_data):
        """Test VWAP calculation."""
        vwap = IndicatorCalculator.calculate_vwap(sample_ohlcv_data, reset_daily=False)
        
        assert len(vwap) == len(sample_ohlcv_data)
        assert not vwap.isna().all()
        assert vwap.iloc[-1] > 0
        
        # VWAP should be within price range
        assert vwap.min() >= sample_ohlcv_data['low'].min()
        assert vwap.max() <= sample_ohlcv_data['high'].max()
    
    def test_calculate_atr(self, sample_ohlcv_data):
        """Test ATR calculation."""
        atr = IndicatorCalculator.calculate_atr(sample_ohlcv_data, period=14)
        
        assert len(atr) == len(sample_ohlcv_data)
        assert not atr.isna().all()
        
        # ATR should be positive
        valid_atr = atr.dropna()
        assert (valid_atr > 0).all()
        
        # ATR should be reasonable relative to price range
        price_range = sample_ohlcv_data['high'] - sample_ohlcv_data['low']
        assert atr.iloc[-1] <= price_range.max() * 2
    
    def test_calculate_rsi(self, sample_ohlcv_data):
        """Test RSI calculation."""
        rsi = IndicatorCalculator.calculate_rsi(sample_ohlcv_data, period=6)
        
        assert len(rsi) == len(sample_ohlcv_data)
        assert not rsi.isna().all()
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_calculate_rsi_boundaries(self):
        """Test RSI at extreme conditions."""
        # All prices going up - RSI should approach 100
        data_up = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=50, freq='1min'),
            'close': range(65000, 65050)
        })
        rsi_up = IndicatorCalculator.calculate_rsi(data_up, period=6)
        assert rsi_up.iloc[-1] > 80  # Should be high
        
        # All prices going down - RSI should approach 0
        data_down = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=50, freq='1min'),
            'close': range(65050, 65000, -1)
        })
        rsi_down = IndicatorCalculator.calculate_rsi(data_down, period=6)
        assert rsi_down.iloc[-1] < 20  # Should be low
    
    def test_calculate_volume_ma(self, sample_ohlcv_data):
        """Test volume moving average calculation."""
        volume_ma = IndicatorCalculator.calculate_volume_ma(sample_ohlcv_data, period=20)
        
        assert len(volume_ma) == len(sample_ohlcv_data)
        
        # Volume MA should be positive
        valid_volume_ma = volume_ma.dropna()
        assert (valid_volume_ma > 0).all()
        
        # Volume MA should be smoother than raw volume
        volume_ma_volatility = volume_ma.diff().std()
        volume_volatility = sample_ohlcv_data['volume'].diff().std()
        assert volume_ma_volatility < volume_volatility
    
    def test_calculate_all_indicators(self, sample_ohlcv_data):
        """Test calculating all indicators at once."""
        result = IndicatorCalculator.calculate_all_indicators(
            sample_ohlcv_data,
            ema_periods=[9, 21, 50],
            atr_period=14,
            rsi_period=6,
            volume_ma_period=20
        )
        
        # Check all indicator columns exist
        assert 'ema_9' in result.columns
        assert 'ema_21' in result.columns
        assert 'ema_50' in result.columns
        assert 'vwap' in result.columns
        assert 'atr' in result.columns
        assert 'rsi' in result.columns
        assert 'volume_ma' in result.columns
        
        # Result should have fewer rows due to NaN dropping
        assert len(result) <= len(sample_ohlcv_data)
        assert len(result) > 0
        
        # No NaN values in critical indicators
        assert not result['ema_9'].isna().any()
        assert not result['ema_21'].isna().any()
        assert not result['vwap'].isna().any()
        assert not result['atr'].isna().any()
        assert not result['rsi'].isna().any()
    
    def test_calculate_all_indicators_empty_data(self):
        """Test that empty DataFrame raises error (should never happen in production)."""
        empty_df = pd.DataFrame()
        
        # Should raise ValueError - this is a critical error that should never happen
        with pytest.raises(ValueError, match="Cannot calculate indicators on empty DataFrame"):
            IndicatorCalculator.calculate_all_indicators(empty_df)
    
    def test_calculate_all_indicators_insufficient_data(self):
        """Test that insufficient data raises error (should never happen in production)."""
        small_df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=5, freq='1min'),
            'open': [65000, 65100, 65050, 65150, 65200],
            'high': [65100, 65200, 65150, 65250, 65300],
            'low': [64900, 65000, 64950, 65050, 65100],
            'close': [65050, 65150, 65100, 65200, 65250],
            'volume': [100, 150, 120, 180, 200]
        })
        
        # Should raise ValueError - we always request 500 candles in production
        with pytest.raises(ValueError, match="Data validation failed"):
            IndicatorCalculator.calculate_all_indicators(small_df)
