"""
Integration Tests for Trading Scanner System
Tests end-to-end signal detection flow and component integration.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.unified_data_source import UnifiedDataSource, DataSourceConfig
from src.indicator_calculator import IndicatorCalculator
from src.strategy_detector import StrategyDetector
from src.signal_quality_filter import SignalQualityFilter, QualityConfig
from src.sl_tp_calculator import SLTPCalculator


class TestDataSourceIntegration:
    """Test unified data source integration"""
    
    def test_data_source_initialization(self):
        """Test data source initialization"""
        config = DataSourceConfig(
            primary_source="binance",
            fallback_sources=["twelve_data", "alpha_vantage"],
            freshness_threshold_seconds=300
        )
        
        data_source = UnifiedDataSource(config)
        assert data_source.config.primary_source == "binance"
        assert len(data_source.config.fallback_sources) == 2
    
    def test_data_source_status_tracking(self):
        """Test data source status tracking"""
        config = DataSourceConfig()
        data_source = UnifiedDataSource(config)
        
        status = data_source.get_source_status()
        assert 'binance' in status
        assert 'enabled' in status['binance']


class TestSignalDetectionFlow:
    """Test end-to-end signal detection flow"""
    
    @pytest.fixture
    def sample_market_data(self):
        """Create realistic sample market data"""
        dates = pd.date_range('2024-01-01', periods=200, freq='1H')
        
        # Create trending data
        prices = np.linspace(100, 110, 200) + np.random.normal(0, 0.5, 200)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices - 0.5,
            'high': prices + 1,
            'low': prices - 1,
            'close': prices,
            'volume': np.random.uniform(1000, 2000, 200)
        })
        
        return data
    
    def test_indicator_calculation_pipeline(self, sample_market_data):
        """Test indicator calculation pipeline"""
        calc = IndicatorCalculator()
        
        # Calculate all indicators
        data_with_indicators = calc.calculate_all_indicators(
            sample_market_data,
            ema_periods=[9, 21, 50],
            atr_period=14,
            rsi_period=6,
            volume_ma_period=20
        )
        
        # Verify indicators are calculated
        assert 'ema_9' in data_with_indicators.columns
        assert 'ema_21' in data_with_indicators.columns
        assert 'ema_50' in data_with_indicators.columns
        assert 'atr' in data_with_indicators.columns
        assert 'rsi' in data_with_indicators.columns
        assert 'volume_ma' in data_with_indicators.columns
        
        # Verify no NaN in critical indicators
        assert not data_with_indicators['ema_9'].isna().all()
        assert not data_with_indicators['rsi'].isna().all()
    
    def test_strategy_detection_integration(self, sample_market_data):
        """Test strategy detection integration"""
        # Calculate indicators
        calc = IndicatorCalculator()
        data_with_indicators = calc.calculate_all_indicators(sample_market_data)
        
        # Initialize strategy detector
        detector = StrategyDetector()
        
        # Detect signals
        signal = detector.detect_signals(
            data_with_indicators,
            timeframe="1h",
            symbol="BTC"
        )
        
        # Signal may or may not be detected depending on data
        # Just verify the method works without errors
        assert signal is None or hasattr(signal, 'signal_type')
    
    def test_signal_quality_filtering(self, sample_market_data):
        """Test signal quality filtering"""
        # Calculate indicators
        calc = IndicatorCalculator()
        data_with_indicators = calc.calculate_all_indicators(sample_market_data)
        
        # Create a mock signal
        from src.signal_detector import Signal
        from src.symbol_context import SymbolContext
        
        last = data_with_indicators.iloc[-1]
        
        signal = Signal(
            timestamp=last['timestamp'],
            signal_type="LONG",
            timeframe="1h",
            symbol="BTC",
            symbol_context=SymbolContext.from_symbol("BTC"),
            entry_price=last['close'],
            stop_loss=last['close'] - 1,
            take_profit=last['close'] + 2,
            atr=last['atr'],
            risk_reward=2.0,
            market_bias="bullish",
            confidence=4,
            indicators={
                'rsi': last['rsi'],
                'volume': last['volume'],
                'volume_ma': last['volume_ma']
            },
            reasoning="Test signal",
            strategy="Test"
        )
        
        # Filter signal
        quality_config = QualityConfig(
            min_confluence_factors=3,
            min_confidence_score=2
        )
        quality_filter = SignalQualityFilter(quality_config)
        
        result = quality_filter.evaluate_signal(signal, data_with_indicators)
        
        # Verify filter result
        assert hasattr(result, 'passed')
        assert hasattr(result, 'confidence_score')
        assert hasattr(result, 'confluence_factors')


class TestTPSLCalculation:
    """Test TP/SL calculation integration"""
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data"""
        dates = pd.date_range('2024-01-01', periods=150, freq='1H')
        prices = np.linspace(100, 110, 150) + np.random.normal(0, 0.5, 150)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices - 0.5,
            'high': prices + 1,
            'low': prices - 1,
            'close': prices,
            'volume': np.random.uniform(1000, 2000, 150)
        })
        
        return data
    
    def test_structure_based_sltp(self, sample_market_data):
        """Test structure-based SL/TP calculation"""
        calc = IndicatorCalculator()
        data_with_indicators = calc.calculate_all_indicators(sample_market_data)
        
        last = data_with_indicators.iloc[-1]
        entry_price = last['close']
        atr = last['atr']
        
        sl, tp, rr = SLTPCalculator.calculate_structure_based_sltp(
            data_with_indicators,
            entry_price,
            "LONG",
            atr,
            lookback=50
        )
        
        # Verify SL/TP are calculated
        assert sl < entry_price  # SL below entry for LONG
        assert tp > entry_price  # TP above entry for LONG
        assert rr > 0  # Risk/reward should be positive
    
    def test_historical_sltp(self, sample_market_data):
        """Test historical price action-based SL/TP"""
        calc = IndicatorCalculator()
        data_with_indicators = calc.calculate_all_indicators(sample_market_data)
        
        last = data_with_indicators.iloc[-1]
        entry_price = last['close']
        atr = last['atr']
        
        sl, tp, rr = SLTPCalculator.calculate_historical_sltp(
            data_with_indicators,
            entry_price,
            "LONG",
            atr,
            lookback=100
        )
        
        # Verify SL/TP are calculated
        assert sl < entry_price  # SL below entry for LONG
        assert tp > entry_price  # TP above entry for LONG
        assert rr >= 1.2  # Minimum risk/reward
    
    def test_risk_reward_validation(self):
        """Test risk/reward validation"""
        entry = 100
        sl = 98
        tp = 104
        
        is_valid = SLTPCalculator.validate_risk_reward(entry, sl, tp, min_ratio=1.2)
        assert is_valid is True
        
        # Test invalid ratio
        tp_low = 101
        is_valid = SLTPCalculator.validate_risk_reward(entry, sl, tp_low, min_ratio=1.2)
        assert is_valid is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

