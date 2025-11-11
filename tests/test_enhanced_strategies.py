"""
Integration Tests for Enhanced Strategies
Tests momentum shift, trend alignment, EMA cloud breakout, mean reversion, and H4 HVG strategies
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
import logging

from src.signal_detector import SignalDetector
from src.h4_hvg_detector import H4HVGDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def signal_detector():
    """Create signal detector with enhanced config"""
    detector = SignalDetector(
        volume_spike_threshold=1.5,
        rsi_min=30,
        rsi_max=70,
        stop_loss_atr_multiplier=1.5,
        take_profit_atr_multiplier=2.0,
        duplicate_time_window_minutes=5,
        duplicate_price_threshold_percent=0.3
    )
    
    # Set enhanced config with asset-specific thresholds
    detector.config = {
        'signal_rules': {
            'volume_momentum_shift': 1.2,
            'volume_trend_alignment': 0.8,
            'volume_ema_cloud_breakout': 1.5,
            'volume_mean_reversion': 1.5,
            'rsi_momentum_threshold': 3.0,
            'adx_min_momentum_shift': 18,
            'adx_min_trend_alignment': 19,
            'momentum_shift_sl_multiplier': 1.2,
            'momentum_shift_tp_multiplier': 2.0,
        },
        'asset_specific': {
            'BTC': {
                'adx_threshold': 20,
                'volume_thresholds': {
                    'momentum_shift': 1.2,
                    'trend_alignment': 0.8,
                    'breakout': 1.5,
                    'mean_reversion': 1.5
                },
                'rsi_momentum_threshold': 3.0
            },
            'XAUUSD': {
                'adx_threshold': 19,
                'volume_thresholds': {
                    'momentum_shift': 1.2,
                    'trend_alignment': 0.8,
                    'breakout': 1.5,
                    'mean_reversion': 1.5
                },
                'rsi_momentum_threshold': 2.5
            },
            'US30': {
                'adx_threshold': 22,
                'volume_thresholds': {
                    'momentum_shift': 0.8,
                    'trend_alignment': 0.8,
                    'breakout': 1.5,
                    'mean_reversion': 1.5
                },
                'rsi_momentum_threshold': 3.0
            }
        }
    }
    
    return detector


def create_test_data(num_candles=20, base_price=45000):
    """Create test market data with indicators"""
    timestamps = [datetime.now() - timedelta(minutes=5*i) for i in range(num_candles)]
    timestamps.reverse()
    
    data = {
        'timestamp': timestamps,
        'open': [base_price + i*10 for i in range(num_candles)],
        'high': [base_price + i*10 + 50 for i in range(num_candles)],
        'low': [base_price + i*10 - 50 for i in range(num_candles)],
        'close': [base_price + i*10 + 20 for i in range(num_candles)],
        'volume': [1000 + i*50 for i in range(num_candles)],
        'rsi': [50 + i*0.5 for i in range(num_candles)],
        'adx': [20 + i*0.2 for i in range(num_candles)],
        'ema_9': [base_price + i*9 for i in range(num_candles)],
        'ema_21': [base_price + i*8 for i in range(num_candles)],
        'ema_50': [base_price + i*7 for i in range(num_candles)],
        'atr': [150.0] * num_candles,
        'vwap': [base_price + i*10 for i in range(num_candles)],
        'volume_ma': [800.0] * num_candles
    }
    
    return pd.DataFrame(data)


class TestMomentumShiftStrategy:
    """Test Momentum Shift Strategy with trend validation"""
    
    def test_bullish_momentum_shift_with_trend_validation(self, signal_detector):
        """Test bullish momentum shift requires price > EMA50"""
        data = create_test_data(num_candles=15)
        
        # Set up bullish momentum shift conditions
        data.loc[data.index[-3], 'rsi'] = 45.0
        data.loc[data.index[-2], 'rsi'] = 48.0
        data.loc[data.index[-1], 'rsi'] = 52.0  # Rising RSI
        data.loc[data.index[-1], 'adx'] = 22.0  # Strong ADX
        data.loc[data.index[-1], 'volume'] = 1200.0  # Good volume
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        
        # Ensure price > EMA50 (uptrend)
        data.loc[data.index[-1], 'close'] = 45500.0
        data.loc[data.index[-1], 'ema_50'] = 45300.0
        
        signal = signal_detector._detect_momentum_shift(data, '5m', 'BTC/USD')
        
        assert signal is not None, "Should generate signal when trend aligned"
        assert signal.signal_type == "LONG"
        assert signal.strategy == "Momentum Shift (Bullish)"
    
    def test_momentum_shift_rejected_trend_conflict(self, signal_detector):
        """Test momentum shift rejected when trend conflicts"""
        data = create_test_data(num_candles=15)
        
        # Set up bullish RSI turn
        data.loc[data.index[-3], 'rsi'] = 45.0
        data.loc[data.index[-2], 'rsi'] = 48.0
        data.loc[data.index[-1], 'rsi'] = 52.0
        data.loc[data.index[-1], 'adx'] = 22.0
        data.loc[data.index[-1], 'volume'] = 1200.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        
        # BUT price < EMA50 (downtrend) - should reject
        data.loc[data.index[-1], 'close'] = 45000.0
        data.loc[data.index[-1], 'ema_50'] = 45300.0
        
        signal = signal_detector._detect_momentum_shift(data, '5m', 'BTC/USD')
        
        assert signal is None, "Should reject signal when trend conflicts"
    
    def test_rsi_momentum_threshold(self, signal_detector):
        """Test RSI momentum threshold requirement"""
        data = create_test_data(num_candles=15)
        
        # RSI change too small (< 3.0)
        data.loc[data.index[-3], 'rsi'] = 50.0
        data.loc[data.index[-2], 'rsi'] = 51.0
        data.loc[data.index[-1], 'rsi'] = 52.0  # Only 2.0 change
        data.loc[data.index[-1], 'adx'] = 22.0
        data.loc[data.index[-1], 'volume'] = 1200.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        data.loc[data.index[-1], 'close'] = 45500.0
        data.loc[data.index[-1], 'ema_50'] = 45300.0
        
        signal = signal_detector._detect_momentum_shift(data, '5m', 'BTC/USD')
        
        assert signal is None, "Should reject when RSI momentum insufficient"


class TestTrendAlignmentStrategy:
    """Test Trend Alignment Strategy with stricter ADX"""
    
    def test_trend_alignment_with_asset_specific_adx(self, signal_detector):
        """Test trend alignment uses asset-specific ADX thresholds"""
        data = create_test_data(num_candles=15)
        
        # Set up bullish cascade
        data.loc[data.index[-1], 'close'] = 45500.0
        data.loc[data.index[-1], 'ema_9'] = 45400.0
        data.loc[data.index[-1], 'ema_21'] = 45300.0
        data.loc[data.index[-1], 'ema_50'] = 45200.0
        data.loc[data.index[-1], 'rsi'] = 55.0
        data.loc[data.index[-2], 'rsi'] = 53.0  # Rising
        data.loc[data.index[-1], 'volume'] = 1000.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        
        # Test BTC with ADX = 20 (should pass)
        data.loc[data.index[-1], 'adx'] = 20.0
        signal = signal_detector._detect_trend_alignment(data, '5m', 'BTC/USD')
        assert signal is not None, "BTC should pass with ADX 20"
        
        # Test US30 with ADX = 20 (should fail, needs 22)
        data.loc[data.index[-1], 'adx'] = 20.0
        signal = signal_detector._detect_trend_alignment(data, '5m', 'US30')
        assert signal is None, "US30 should fail with ADX 20 (needs 22)"
        
        # Test US30 with ADX = 22 (should pass)
        data.loc[data.index[-1], 'adx'] = 22.0
        signal = signal_detector._detect_trend_alignment(data, '5m', 'US30')
        assert signal is not None, "US30 should pass with ADX 22"


class TestEMACloudBreakoutStrategy:
    """Test EMA Cloud Breakout with stricter requirements"""
    
    def test_breakout_requires_0_2_percent_above_high(self, signal_detector):
        """Test breakout requires 0.2% above recent high"""
        data = create_test_data(num_candles=15)
        
        # Set up bullish EMA alignment
        data.loc[data.index[-1], 'ema_21'] = 45300.0
        data.loc[data.index[-1], 'ema_50'] = 45200.0
        data.loc[data.index[-1], 'vwap'] = 45250.0
        data.loc[data.index[-1], 'rsi'] = 55.0
        data.loc[data.index[-1], 'volume'] = 1500.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        
        # Recent high = 45400
        for i in range(-11, -1):
            data.loc[data.index[i], 'high'] = 45400.0
        
        # Price just above high (not 0.2%) - should fail
        data.loc[data.index[-1], 'close'] = 45405.0
        signal = signal_detector._detect_ema_cloud_breakout(data, '5m', 'BTC/USD')
        assert signal is None, "Should reject breakout < 0.2%"
        
        # Price 0.2% above high - should pass
        data.loc[data.index[-1], 'close'] = 45491.0  # 0.2% above 45400
        signal = signal_detector._detect_ema_cloud_breakout(data, '5m', 'BTC/USD')
        assert signal is not None, "Should accept breakout >= 0.2%"
    
    def test_rsi_range_30_to_70(self, signal_detector):
        """Test RSI must be between 30-70"""
        data = create_test_data(num_candles=15)
        
        # Set up valid breakout conditions
        data.loc[data.index[-1], 'ema_21'] = 45300.0
        data.loc[data.index[-1], 'ema_50'] = 45200.0
        data.loc[data.index[-1], 'vwap'] = 45250.0
        data.loc[data.index[-1], 'close'] = 45500.0
        data.loc[data.index[-1], 'volume'] = 1500.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        
        for i in range(-11, -1):
            data.loc[data.index[i], 'high'] = 45400.0
        
        # RSI = 75 (too high) - should fail
        data.loc[data.index[-1], 'rsi'] = 75.0
        signal = signal_detector._detect_ema_cloud_breakout(data, '5m', 'BTC/USD')
        assert signal is None, "Should reject RSI > 70"
        
        # RSI = 25 (too low) - should fail
        data.loc[data.index[-1], 'rsi'] = 25.0
        signal = signal_detector._detect_ema_cloud_breakout(data, '5m', 'BTC/USD')
        assert signal is None, "Should reject RSI < 30"
        
        # RSI = 55 (good) - should pass
        data.loc[data.index[-1], 'rsi'] = 55.0
        signal = signal_detector._detect_ema_cloud_breakout(data, '5m', 'BTC/USD')
        assert signal is not None, "Should accept RSI 30-70"


class TestMeanReversionStrategy:
    """Test Mean Reversion with stricter requirements"""
    
    def test_vwap_distance_1_8_atr(self, signal_detector):
        """Test requires 1.8 ATR distance from VWAP"""
        data = create_test_data(num_candles=5)
        
        # Set up mean reversion conditions
        data.loc[data.index[-1], 'atr'] = 100.0
        data.loc[data.index[-1], 'vwap'] = 45000.0
        data.loc[data.index[-1], 'rsi'] = 15.0  # Oversold
        data.loc[data.index[-1], 'volume'] = 1500.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        data.loc[data.index[-2], 'close'] = 44900.0
        
        # Distance = 1.5 ATR (should fail, needs 1.8)
        data.loc[data.index[-1], 'close'] = 44850.0  # 150 away = 1.5 ATR
        # Create pin bar pattern
        data.loc[data.index[-1], 'open'] = 44850.0
        data.loc[data.index[-1], 'high'] = 44900.0
        data.loc[data.index[-1], 'low'] = 44700.0  # Long lower wick
        signal = signal_detector._detect_mean_reversion(data, '5m', 'BTC/USD')
        assert signal is None, "Should reject distance < 1.8 ATR"
        
        # Distance = 1.8 ATR (should pass)
        data.loc[data.index[-1], 'close'] = 44820.0  # 180 away = 1.8 ATR
        # Create pin bar pattern
        data.loc[data.index[-1], 'open'] = 44820.0
        data.loc[data.index[-1], 'high'] = 44870.0
        data.loc[data.index[-1], 'low'] = 44650.0  # Long lower wick (170 points)
        signal = signal_detector._detect_mean_reversion(data, '5m', 'BTC/USD')
        assert signal is not None, "Should accept distance >= 1.8 ATR"
    
    def test_rsi_extremes_20_and_80(self, signal_detector):
        """Test RSI must be < 20 or > 80"""
        data = create_test_data(num_candles=5)
        
        # Set up valid conditions
        data.loc[data.index[-1], 'atr'] = 100.0
        data.loc[data.index[-1], 'vwap'] = 45000.0
        data.loc[data.index[-1], 'close'] = 44820.0  # 1.8 ATR away
        data.loc[data.index[-1], 'volume'] = 1500.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        data.loc[data.index[-2], 'close'] = 44900.0
        
        # Create pin bar pattern
        data.loc[data.index[-1], 'open'] = 44820.0
        data.loc[data.index[-1], 'high'] = 44870.0
        data.loc[data.index[-1], 'low'] = 44650.0  # Long lower wick
        
        # RSI = 25 (not extreme enough) - should fail
        data.loc[data.index[-1], 'rsi'] = 25.0
        signal = signal_detector._detect_mean_reversion(data, '5m', 'BTC/USD')
        assert signal is None, "Should reject RSI 25 (needs < 20)"
        
        # RSI = 19 (extreme) - should pass
        data.loc[data.index[-1], 'rsi'] = 19.0
        signal = signal_detector._detect_mean_reversion(data, '5m', 'BTC/USD')
        assert signal is not None, "Should accept RSI < 20"


class TestH4HVGStrategy:
    """Test H4 HVG with enhanced gap validation"""
    
    def test_gap_size_0_3_percent(self):
        """Test minimum gap size of 0.3%"""
        detector = H4HVGDetector(symbol='BTC')
        
        data = create_test_data(num_candles=5, base_price=45000)
        
        # Gap of 0.2% (should fail)
        data.loc[data.index[-1], 'open'] = 45090.0  # 0.2% gap
        data.loc[data.index[-2], 'close'] = 45000.0
        data.loc[data.index[-1], 'volume'] = 2000.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        
        gap_info = detector.detect_hvg_pattern(data)
        assert gap_info is None, "Should reject gap < 0.3%"
        
        # Gap of 0.3% (should pass)
        data.loc[data.index[-1], 'open'] = 45135.0  # 0.3% gap
        gap_info = detector.detect_hvg_pattern(data)
        assert gap_info is not None, "Should accept gap >= 0.3%"
    
    def test_volume_spike_2x(self):
        """Test volume spike requirement of 2.0x"""
        detector = H4HVGDetector(symbol='BTC')
        
        data = create_test_data(num_candles=5, base_price=45000)
        
        # Valid gap size
        data.loc[data.index[-1], 'open'] = 45135.0  # 0.3% gap
        data.loc[data.index[-2], 'close'] = 45000.0
        
        # Volume = 1.5x (should fail, needs 2.0x)
        data.loc[data.index[-1], 'volume'] = 1200.0
        data.loc[data.index[-1], 'volume_ma'] = 800.0
        
        gap_info = detector.detect_hvg_pattern(data)
        assert gap_info is None, "Should reject volume < 2.0x"
        
        # Volume = 2.0x (should pass)
        data.loc[data.index[-1], 'volume'] = 1600.0
        gap_info = detector.detect_hvg_pattern(data)
        assert gap_info is not None, "Should accept volume >= 2.0x"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
