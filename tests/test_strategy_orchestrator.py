"""Tests for strategy orchestrator."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.strategy_orchestrator import StrategyOrchestrator
from src.strategy_helpers import MarketConditions


class TestStrategyOrchestrator:
    """Test StrategyOrchestrator functionality."""
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        config = {
            'strategy_priority': {
                'high_volatility': ['momentum_shift', 'liquidity_sweep'],
                'low_volatility': ['mean_reversion'],
                'strong_trend': ['trend_following'],
                'ranging': ['support_resistance_bounce']
            }
        }
        orchestrator = StrategyOrchestrator(config)
        
        assert orchestrator.config == config
        assert orchestrator.high_volatility_strategies == ['momentum_shift', 'liquidity_sweep']
        assert orchestrator.low_volatility_strategies == ['mean_reversion']
    
    def test_analyze_market_conditions_trending(self):
        """Test market analysis for trending market."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        # Create data with strong trend (high ADX)
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.linspace(45000, 50000, 50),
            'high': np.linspace(45100, 50100, 50),
            'low': np.linspace(44900, 49900, 50),
            'close': np.linspace(45000, 50000, 50),
            'volume': [1000] * 50,
            'adx': [28] * 50,  # Strong trend
            'atr': [500] * 50,
            'rsi': [60] * 50,  # Bullish
            'volume_ma': [900] * 50
        })
        
        conditions = orchestrator.analyze_market_conditions(data)
        
        assert conditions is not None
        assert conditions.trend_strength == 28
        assert bool(conditions.is_trending) is True
        assert bool(conditions.is_ranging) is False
        assert conditions.momentum == "bullish"
    
    def test_analyze_market_conditions_ranging(self):
        """Test market analysis for ranging market."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        # Create data with ranging market (low ADX)
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [45000] * 50,
            'high': [45200] * 50,
            'low': [44800] * 50,
            'close': [45000] * 50,
            'volume': [1000] * 50,
            'adx': [15] * 50,  # Ranging
            'atr': [200] * 50,
            'rsi': [50] * 50,  # Neutral
            'volume_ma': [1000] * 50
        })
        
        conditions = orchestrator.analyze_market_conditions(data)
        
        assert conditions is not None
        assert conditions.trend_strength == 15
        assert bool(conditions.is_trending) is False
        assert bool(conditions.is_ranging) is True
        assert conditions.momentum == "neutral"
    
    def test_analyze_market_conditions_high_volatility(self):
        """Test market analysis for high volatility and volume."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        # Create data with high volume
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [45000] * 50,
            'high': [45500] * 50,
            'low': [44500] * 50,
            'close': [45000] * 50,
            'volume': [2000] * 50,  # High volume (2x volume_ma)
            'adx': [22] * 50,
            'atr': [500] * 50,
            'rsi': [50] * 50,
            'volume_ma': [1000] * 50  # Volume is 2x this
        })
        
        conditions = orchestrator.analyze_market_conditions(data)
        
        assert conditions is not None
        # Volume is 2000, volume_ma is 1000, so ratio is 2.0 > 1.5 = high
        assert conditions.volume_profile == "high"
        # Volatility is calculated correctly
        assert conditions.volatility > 0
    
    def test_analyze_market_conditions_insufficient_data(self):
        """Test market analysis with insufficient data."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        # Create data with only 5 candles
        dates = pd.date_range(start='2024-01-01', periods=5, freq='1h')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [45000] * 5,
            'high': [45100] * 5,
            'low': [44900] * 5,
            'close': [45000] * 5,
            'volume': [1000] * 5
        })
        
        conditions = orchestrator.analyze_market_conditions(data)
        
        assert conditions is None
    
    def test_select_strategies_high_volatility(self):
        """Test strategy selection for high volatility."""
        config = {
            'strategy_priority': {
                'high_volatility': ['momentum_shift', 'liquidity_sweep'],
                'low_volatility': ['mean_reversion'],
                'strong_trend': ['trend_following'],
                'ranging': ['support_resistance_bounce']
            }
        }
        orchestrator = StrategyOrchestrator(config)
        
        conditions = MarketConditions(
            trend_strength=22,
            volatility=2.0,  # High volatility
            is_trending=True,
            is_ranging=False,
            momentum="bullish",
            volume_profile="high"
        )
        
        enabled = ['momentum_shift', 'liquidity_sweep', 'mean_reversion', 'trend_following']
        
        selected = orchestrator.select_strategies(conditions, enabled)
        
        # High volatility strategies should be first
        assert selected[0] in ['momentum_shift', 'liquidity_sweep']
        assert 'momentum_shift' in selected
        assert 'liquidity_sweep' in selected
    
    def test_select_strategies_strong_trend(self):
        """Test strategy selection for strong trend."""
        config = {
            'strategy_priority': {
                'high_volatility': ['momentum_shift'],
                'low_volatility': ['mean_reversion'],
                'strong_trend': ['trend_following', 'adx_rsi_momentum'],
                'ranging': ['support_resistance_bounce']
            }
        }
        orchestrator = StrategyOrchestrator(config)
        
        conditions = MarketConditions(
            trend_strength=28,  # Strong trend
            volatility=1.2,
            is_trending=True,
            is_ranging=False,
            momentum="bullish",
            volume_profile="normal"
        )
        
        enabled = ['trend_following', 'adx_rsi_momentum', 'mean_reversion']
        
        selected = orchestrator.select_strategies(conditions, enabled)
        
        # Trend following strategies should be prioritized
        assert 'trend_following' in selected[:2]
        assert 'adx_rsi_momentum' in selected[:2]
    
    def test_select_strategies_ranging_market(self):
        """Test strategy selection for ranging market."""
        config = {
            'strategy_priority': {
                'high_volatility': ['momentum_shift'],
                'low_volatility': ['mean_reversion'],
                'strong_trend': ['trend_following'],
                'ranging': ['support_resistance_bounce', 'asian_range_breakout']
            }
        }
        orchestrator = StrategyOrchestrator(config)
        
        conditions = MarketConditions(
            trend_strength=15,  # Ranging
            volatility=0.9,
            is_trending=False,
            is_ranging=True,
            momentum="neutral",
            volume_profile="normal"
        )
        
        enabled = ['support_resistance_bounce', 'asian_range_breakout', 'trend_following']
        
        selected = orchestrator.select_strategies(conditions, enabled)
        
        # Ranging strategies should be prioritized
        assert 'support_resistance_bounce' in selected[:2]
        assert 'asian_range_breakout' in selected[:2]
    
    def test_select_strategies_low_volatility(self):
        """Test strategy selection for low volatility."""
        config = {
            'strategy_priority': {
                'high_volatility': ['momentum_shift'],
                'low_volatility': ['mean_reversion', 'support_resistance_bounce'],
                'strong_trend': ['trend_following'],
                'ranging': ['asian_range_breakout']
            }
        }
        orchestrator = StrategyOrchestrator(config)
        
        conditions = MarketConditions(
            trend_strength=18,
            volatility=0.7,  # Low volatility
            is_trending=False,
            is_ranging=True,
            momentum="neutral",
            volume_profile="low"
        )
        
        enabled = ['mean_reversion', 'support_resistance_bounce', 'momentum_shift']
        
        selected = orchestrator.select_strategies(conditions, enabled)
        
        # Low volatility strategies should be prioritized
        assert 'mean_reversion' in selected[:2]
    
    def test_detect_conflicting_signals(self):
        """Test detecting conflicting signals."""
        from src.signal_detector import Signal
        from datetime import datetime
        
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        # Create conflicting signals
        signal1 = Signal(
            timestamp=datetime.now(),
            signal_type="LONG",
            timeframe="5m",
            entry_price=45000,
            stop_loss=44500,
            take_profit=46000,
            atr=500,
            risk_reward=2.0,
            market_bias="bullish",
            confidence=4,
            indicators={}
        )
        
        signal2 = Signal(
            timestamp=datetime.now(),
            signal_type="SHORT",
            timeframe="5m",
            entry_price=45000,
            stop_loss=45500,
            take_profit=44000,
            atr=500,
            risk_reward=2.0,
            market_bias="bearish",
            confidence=4,
            indicators={}
        )
        
        # Test conflicting signals
        assert orchestrator.detect_conflicting_signals([signal1, signal2]) is True
        
        # Test non-conflicting signals
        assert orchestrator.detect_conflicting_signals([signal1]) is False
        assert orchestrator.detect_conflicting_signals([signal1, signal1]) is False
    
    def test_should_skip_strategy_momentum_in_ranging(self):
        """Test skipping momentum strategy in ranging market."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        conditions = MarketConditions(
            trend_strength=15,  # Ranging
            volatility=1.0,
            is_trending=False,
            is_ranging=True,
            momentum="neutral",
            volume_profile="normal"
        )
        
        # Should skip momentum strategies in ranging market
        assert orchestrator.should_skip_strategy("momentum_shift", conditions) is True
        assert orchestrator.should_skip_strategy("adx_rsi_momentum", conditions) is True
    
    def test_should_skip_strategy_mean_reversion_in_trend(self):
        """Test skipping mean reversion in strong trend."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        conditions = MarketConditions(
            trend_strength=28,  # Strong trend
            volatility=1.2,
            is_trending=True,
            is_ranging=False,
            momentum="bullish",
            volume_profile="normal"
        )
        
        # Should skip mean reversion in strong trend
        assert orchestrator.should_skip_strategy("mean_reversion", conditions) is True
    
    def test_should_skip_strategy_trend_in_ranging(self):
        """Test skipping trend following in ranging market."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        conditions = MarketConditions(
            trend_strength=15,  # Ranging
            volatility=0.9,
            is_trending=False,
            is_ranging=True,
            momentum="neutral",
            volume_profile="normal"
        )
        
        # Should skip trend strategies in ranging market
        assert orchestrator.should_skip_strategy("trend_following", conditions) is True
    
    def test_should_skip_strategy_breakout_low_volume(self):
        """Test skipping breakout strategy in low volume."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        conditions = MarketConditions(
            trend_strength=22,
            volatility=1.1,
            is_trending=True,
            is_ranging=False,
            momentum="bullish",
            volume_profile="low"  # Low volume
        )
        
        # Should skip breakout strategies in low volume
        assert orchestrator.should_skip_strategy("ema_cloud_breakout", conditions) is True
    
    def test_get_strategy_confidence_multiplier(self):
        """Test getting confidence multiplier for strategies."""
        config = {'strategy_priority': {}}
        orchestrator = StrategyOrchestrator(config)
        
        # Momentum in trending market (boost)
        trending_conditions = MarketConditions(
            trend_strength=25,
            volatility=1.2,
            is_trending=True,
            is_ranging=False,
            momentum="bullish",
            volume_profile="normal"
        )
        
        multiplier = orchestrator.get_strategy_confidence_multiplier("momentum_shift", trending_conditions)
        assert multiplier > 1.0
        
        # Mean reversion in ranging market (boost)
        ranging_conditions = MarketConditions(
            trend_strength=15,
            volatility=0.9,
            is_trending=False,
            is_ranging=True,
            momentum="neutral",
            volume_profile="normal"
        )
        
        multiplier = orchestrator.get_strategy_confidence_multiplier("mean_reversion", ranging_conditions)
        assert multiplier > 1.0
        
        # Any strategy in low volume (reduce)
        low_volume_conditions = MarketConditions(
            trend_strength=20,
            volatility=1.0,
            is_trending=True,
            is_ranging=False,
            momentum="neutral",
            volume_profile="low"
        )
        
        multiplier = orchestrator.get_strategy_confidence_multiplier("any_strategy", low_volume_conditions)
        assert multiplier < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
