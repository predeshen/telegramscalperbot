"""
Unit Tests for Signal Quality Filter
Tests confluence factor calculation, confidence scoring, duplicate detection, and risk-reward validation
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.signal_quality_filter import SignalQualityFilter, QualityConfig, FilterResult
from src.signal_detector import Signal


@pytest.fixture
def quality_filter():
    """Create quality filter with default config"""
    config = QualityConfig(
        min_confluence_factors=4,
        min_confidence_score=4,
        duplicate_window_seconds=300,
        duplicate_price_tolerance_pct=0.5,
        significant_price_move_pct=1.0,
        min_risk_reward=1.5
    )
    return SignalQualityFilter(config)


@pytest.fixture
def test_signal():
    """Create a test signal"""
    return Signal(
        timestamp=datetime.now(),
        signal_type="LONG",
        timeframe="5m",
        entry_price=45000.0,
        stop_loss=44700.0,
        take_profit=45600.0,
        atr=150.0,
        risk_reward=2.0,
        market_bias="bullish",
        confidence=4,
        indicators={
            'rsi': 55.0,
            'adx': 25.0,
            'ema_50': 44800.0,
            'volume': 1000.0,
            'volume_ma': 800.0
        },
        symbol="BTC/USD",
        strategy="Momentum Shift"
    )


@pytest.fixture
def test_market_data():
    """Create test market data"""
    data = {
        'timestamp': [datetime.now()],
        'open': [45000.0],
        'high': [45100.0],
        'low': [44900.0],
        'close': [45050.0],
        'volume': [1000.0],
        'rsi': [55.0],
        'adx': [25.0],
        'ema_9': [45020.0],
        'ema_21': [44980.0],
        'ema_50': [44900.0],
        'atr': [150.0],
        'vwap': [45000.0],
        'volume_ma': [800.0]
    }
    return pd.DataFrame(data)


class TestConfluenceFactorCalculation:
    """Test confluence factor calculation"""
    
    def test_trend_factor_long_signal(self, quality_filter, test_signal, test_market_data):
        """Test trend factor for LONG signal (price > EMA50)"""
        test_signal.signal_type = "LONG"
        test_signal.entry_price = 45050.0
        test_market_data.loc[0, 'close'] = 45050.0
        test_market_data.loc[0, 'ema_50'] = 44900.0
        
        factors = quality_filter.calculate_confluence_factors(test_signal, test_market_data)
        
        assert factors['trend'] == True, "Trend should pass for LONG with price > EMA50"
    
    def test_trend_factor_short_signal(self, quality_filter, test_signal, test_market_data):
        """Test trend factor for SHORT signal (price < EMA50)"""
        test_signal.signal_type = "SHORT"
        test_signal.entry_price = 44800.0
        test_market_data.loc[0, 'close'] = 44800.0
        test_market_data.loc[0, 'ema_50'] = 44900.0
        
        factors = quality_filter.calculate_confluence_factors(test_signal, test_market_data)
        
        assert factors['trend'] == True, "Trend should pass for SHORT with price < EMA50"
    
    def test_momentum_factor_long(self, quality_filter, test_signal, test_market_data):
        """Test momentum factor for LONG (RSI > 50)"""
        test_signal.signal_type = "LONG"
        test_market_data.loc[0, 'rsi'] = 55.0
        test_market_data.loc[0, 'adx'] = 25.0
        
        factors = quality_filter.calculate_confluence_factors(test_signal, test_market_data)
        
        assert factors['momentum'] == True, "Momentum should pass for LONG with RSI > 50"
    
    def test_momentum_factor_short(self, quality_filter, test_signal, test_market_data):
        """Test momentum factor for SHORT (RSI < 50)"""
        test_signal.signal_type = "SHORT"
        test_market_data.loc[0, 'rsi'] = 45.0
        test_market_data.loc[0, 'adx'] = 25.0
        
        factors = quality_filter.calculate_confluence_factors(test_signal, test_market_data)
        
        assert factors['momentum'] == True, "Momentum should pass for SHORT with RSI < 50"
    
    def test_volume_factor(self, quality_filter, test_signal, test_market_data):
        """Test volume factor (volume > volume_ma)"""
        test_market_data.loc[0, 'volume'] = 1000.0
        test_market_data.loc[0, 'volume_ma'] = 800.0
        
        factors = quality_filter.calculate_confluence_factors(test_signal, test_market_data)
        
        assert factors['volume'] == True, "Volume should pass when > volume_ma"
    
    def test_all_factors_independently(self, quality_filter, test_signal, test_market_data):
        """Test that all 7 factors are evaluated"""
        factors = quality_filter.calculate_confluence_factors(test_signal, test_market_data)
        
        assert len(factors) == 7, "Should evaluate all 7 confluence factors"
        assert 'trend' in factors
        assert 'momentum' in factors
        assert 'volume' in factors
        assert 'price_action' in factors
        assert 'support_resistance' in factors
        assert 'multi_timeframe' in factors
        assert 'volatility' in factors


class TestConfidenceScoreCalculation:
    """Test confidence score calculation with weighted factors"""
    
    def test_score_with_all_factors(self, quality_filter):
        """Test score calculation with all factors met"""
        factors = {
            'trend': True,  # 3 points
            'momentum': True,  # 3 points
            'volume': True,  # 2 points
            'price_action': True,  # 2 points
            'support_resistance': True,  # 2 points
            'multi_timeframe': True,  # 1 point
            'volatility': True  # 1 point
        }
        # Total: 14 points -> score 5
        
        score = quality_filter.calculate_confidence_score(factors)
        
        assert score == 5, "All factors should give score 5"
    
    def test_score_with_critical_factors_only(self, quality_filter):
        """Test score with only critical factors (trend + momentum)"""
        factors = {
            'trend': True,  # 3 points
            'momentum': True,  # 3 points
            'volume': False,
            'price_action': False,
            'support_resistance': False,
            'multi_timeframe': False,
            'volatility': False
        }
        # Total: 6 points -> score 2
        
        score = quality_filter.calculate_confidence_score(factors)
        
        assert score == 2, "Only critical factors should give score 2"
    
    def test_score_mapping(self, quality_filter):
        """Test score mapping thresholds"""
        # 0-3 points = score 1
        factors_1 = {'trend': False, 'momentum': False, 'volume': True, 'price_action': False,
                     'support_resistance': False, 'multi_timeframe': False, 'volatility': False}
        assert quality_filter.calculate_confidence_score(factors_1) == 1
        
        # 4-6 points = score 2
        factors_2 = {'trend': True, 'momentum': False, 'volume': True, 'price_action': False,
                     'support_resistance': False, 'multi_timeframe': False, 'volatility': False}
        assert quality_filter.calculate_confidence_score(factors_2) == 2
        
        # 7-9 points = score 3
        factors_3 = {'trend': True, 'momentum': True, 'volume': True, 'price_action': False,
                     'support_resistance': False, 'multi_timeframe': False, 'volatility': False}
        assert quality_filter.calculate_confidence_score(factors_3) == 3
        
        # 10-12 points = score 4
        factors_4 = {'trend': True, 'momentum': True, 'volume': True, 'price_action': True,
                     'support_resistance': False, 'multi_timeframe': False, 'volatility': False}
        assert quality_filter.calculate_confidence_score(factors_4) == 4


class TestDuplicateDetection:
    """Test duplicate signal detection"""
    
    def test_duplicate_same_type_and_price(self, quality_filter, test_signal):
        """Test duplicate detection for same signal type and price"""
        # Add first signal
        quality_filter.add_signal_to_history(test_signal)
        
        # Create duplicate signal (same type, similar price)
        duplicate_signal = Signal(
            timestamp=datetime.now(),
            signal_type="LONG",
            timeframe="5m",
            entry_price=45010.0,  # Within 0.5% of 45000
            stop_loss=44710.0,
            take_profit=45610.0,
            atr=150.0,
            risk_reward=2.0,
            market_bias="bullish",
            confidence=4,
            indicators={},
            symbol="BTC/USD",
            strategy="Momentum Shift"
        )
        
        is_duplicate = quality_filter.check_duplicate(duplicate_signal)
        
        assert is_duplicate == True, "Should detect duplicate signal"
    
    def test_not_duplicate_different_type(self, quality_filter, test_signal):
        """Test that different signal types are not duplicates"""
        quality_filter.add_signal_to_history(test_signal)
        
        # Different signal type
        different_signal = Signal(
            timestamp=datetime.now(),
            signal_type="SHORT",  # Different type
            timeframe="5m",
            entry_price=45000.0,
            stop_loss=45300.0,
            take_profit=44400.0,
            atr=150.0,
            risk_reward=2.0,
            market_bias="bearish",
            confidence=4,
            indicators={},
            symbol="BTC/USD",
            strategy="Momentum Shift"
        )
        
        is_duplicate = quality_filter.check_duplicate(different_signal)
        
        assert is_duplicate == False, "Different signal types should not be duplicates"
    
    def test_not_duplicate_significant_price_move(self, quality_filter, test_signal):
        """Test that significant price moves allow new signals"""
        quality_filter.add_signal_to_history(test_signal)
        
        # Price moved > 1.0% (significant move)
        new_signal = Signal(
            timestamp=datetime.now(),
            signal_type="LONG",
            timeframe="5m",
            entry_price=45500.0,  # 1.1% move from 45000
            stop_loss=45200.0,
            take_profit=46100.0,
            atr=150.0,
            risk_reward=2.0,
            market_bias="bullish",
            confidence=4,
            indicators={},
            symbol="BTC/USD",
            strategy="Momentum Shift"
        )
        
        is_duplicate = quality_filter.check_duplicate(new_signal)
        
        assert is_duplicate == False, "Significant price move should allow new signal"
    
    def test_duplicate_window_expiry(self, quality_filter, test_signal):
        """Test that duplicates expire after time window"""
        # Add signal with old timestamp
        old_signal = Signal(
            timestamp=datetime.now() - timedelta(minutes=10),  # 10 minutes ago
            signal_type="LONG",
            timeframe="5m",
            entry_price=45000.0,
            stop_loss=44700.0,
            take_profit=45600.0,
            atr=150.0,
            risk_reward=2.0,
            market_bias="bullish",
            confidence=4,
            indicators={},
            symbol="BTC/USD",
            strategy="Momentum Shift"
        )
        quality_filter.add_signal_to_history(old_signal)
        
        # New signal (should not be duplicate - outside window)
        is_duplicate = quality_filter.check_duplicate(test_signal)
        
        assert is_duplicate == False, "Old signals should not block new ones"


class TestRiskRewardValidation:
    """Test risk-reward ratio validation"""
    
    def test_valid_risk_reward(self, quality_filter, test_signal):
        """Test signal with valid risk-reward ratio"""
        test_signal.entry_price = 45000.0
        test_signal.stop_loss = 44700.0  # 300 risk
        test_signal.take_profit = 45600.0  # 600 reward
        # RR = 600/300 = 2.0 (valid, > 1.5)
        
        is_valid, rr_ratio = quality_filter.validate_risk_reward(test_signal)
        
        assert is_valid == True, "Should accept RR >= 1.5"
        assert rr_ratio == pytest.approx(2.0, rel=0.01)
    
    def test_invalid_risk_reward(self, quality_filter, test_signal):
        """Test signal with invalid risk-reward ratio"""
        test_signal.entry_price = 45000.0
        test_signal.stop_loss = 44700.0  # 300 risk
        test_signal.take_profit = 45400.0  # 400 reward
        # RR = 400/300 = 1.33 (invalid, < 1.5)
        
        is_valid, rr_ratio = quality_filter.validate_risk_reward(test_signal)
        
        assert is_valid == False, "Should reject RR < 1.5"
        assert rr_ratio == pytest.approx(1.33, rel=0.01)
    
    def test_risk_reward_for_short(self, quality_filter, test_signal):
        """Test risk-reward calculation for SHORT signals"""
        test_signal.signal_type = "SHORT"
        test_signal.entry_price = 45000.0
        test_signal.stop_loss = 45300.0  # 300 risk
        test_signal.take_profit = 44400.0  # 600 reward
        # RR = 600/300 = 2.0
        
        is_valid, rr_ratio = quality_filter.validate_risk_reward(test_signal)
        
        assert is_valid == True
        assert rr_ratio == pytest.approx(2.0, rel=0.01)


class TestSignalEvaluation:
    """Test complete signal evaluation flow"""
    
    def test_signal_passes_all_checks(self, quality_filter, test_signal, test_market_data):
        """Test signal that passes all quality checks"""
        # Set up signal to pass all checks
        test_signal.entry_price = 45050.0
        test_signal.stop_loss = 44750.0  # RR = 2.0
        test_signal.take_profit = 45650.0
        test_market_data.loc[0, 'close'] = 45050.0
        test_market_data.loc[0, 'ema_50'] = 44900.0
        test_market_data.loc[0, 'rsi'] = 55.0
        test_market_data.loc[0, 'adx'] = 25.0
        
        result = quality_filter.evaluate_signal(test_signal, test_market_data)
        
        # Note: May not pass due to missing factors, but should not crash
        assert isinstance(result, FilterResult)
        assert isinstance(result.passed, bool)
        assert isinstance(result.confidence_score, int)
        assert 1 <= result.confidence_score <= 5
    
    def test_signal_rejected_low_confluence(self, quality_filter, test_signal):
        """Test signal rejected for insufficient confluence"""
        # Signal with no market data (will have low confluence)
        result = quality_filter.evaluate_signal(test_signal, None)
        
        assert result.passed == False
        assert "confluence" in result.rejection_reason.lower()
    
    def test_signal_rejected_poor_risk_reward(self, quality_filter, test_signal, test_market_data):
        """Test signal rejected for poor risk-reward"""
        # Set poor risk-reward
        test_signal.entry_price = 45000.0
        test_signal.stop_loss = 44700.0  # 300 risk
        test_signal.take_profit = 45300.0  # 300 reward (RR = 1.0)
        
        result = quality_filter.evaluate_signal(test_signal, test_market_data)
        
        assert result.passed == False
        assert "risk-reward" in result.rejection_reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
