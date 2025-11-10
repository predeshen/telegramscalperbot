"""Tests for strategy registry."""

import pytest
from src.strategy_registry import StrategyRegistry


class MockSignalDetector:
    """Mock SignalDetector for testing."""
    
    def _detect_fibonacci_retracement(self):
        """Mock Fibonacci detection method."""
        return "fibonacci_signal"
    
    def _detect_support_resistance_bounce(self):
        """Mock support/resistance detection method."""
        return "sr_signal"


class TestStrategyRegistry:
    """Test StrategyRegistry functionality."""
    
    def test_initialization(self):
        """Test registry initialization."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        assert registry.config == config
        assert registry.strategies == {}
        assert registry.execution_stats == {}
    
    def test_register_strategy(self):
        """Test strategy registration."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        registry.register_strategy(
            name="fibonacci_retracement",
            strategy_method_name="_detect_fibonacci_retracement",
            default_params={'lookback': 50}
        )
        
        assert "fibonacci_retracement" in registry.strategies
        assert registry.strategies["fibonacci_retracement"]['method_name'] == "_detect_fibonacci_retracement"
        assert registry.strategies["fibonacci_retracement"]['default_params'] == {'lookback': 50}
        assert "fibonacci_retracement" in registry.execution_stats
    
    def test_get_strategy_method(self):
        """Test getting strategy method from SignalDetector."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        registry.register_strategy(
            name="fibonacci_retracement",
            strategy_method_name="_detect_fibonacci_retracement"
        )
        
        detector = MockSignalDetector()
        method = registry.get_strategy_method("fibonacci_retracement", detector)
        
        assert method is not None
        assert callable(method)
        assert method() == "fibonacci_signal"
    
    def test_get_strategy_method_not_found(self):
        """Test getting non-existent strategy method."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        detector = MockSignalDetector()
        method = registry.get_strategy_method("nonexistent", detector)
        
        assert method is None
    
    def test_is_enabled_with_config(self):
        """Test checking if strategy is enabled."""
        config = {
            'strategies': {
                'fibonacci_retracement': {
                    'enabled': True,
                    'scanners': ['btc_scalp', 'gold_scalp']
                },
                'support_resistance_bounce': {
                    'enabled': False,
                    'scanners': ['btc_scalp']
                }
            }
        }
        registry = StrategyRegistry(config)
        
        registry.register_strategy("fibonacci_retracement", "_detect_fibonacci_retracement")
        registry.register_strategy("support_resistance_bounce", "_detect_support_resistance_bounce")
        
        # Fibonacci is enabled for btc_scalp
        assert registry.is_enabled("fibonacci_retracement", "btc_scalp") is True
        
        # Fibonacci is enabled for gold_scalp
        assert registry.is_enabled("fibonacci_retracement", "gold_scalp") is True
        
        # Fibonacci is not enabled for us30_scalp (not in scanners list)
        assert registry.is_enabled("fibonacci_retracement", "us30_scalp") is False
        
        # Support/resistance is globally disabled
        assert registry.is_enabled("support_resistance_bounce", "btc_scalp") is False
    
    def test_is_enabled_all_scanners(self):
        """Test strategy enabled for all scanners (empty scanners list)."""
        config = {
            'strategies': {
                'fibonacci_retracement': {
                    'enabled': True,
                    'scanners': []  # Empty means all scanners
                }
            }
        }
        registry = StrategyRegistry(config)
        
        registry.register_strategy("fibonacci_retracement", "_detect_fibonacci_retracement")
        
        # Should be enabled for any scanner
        assert registry.is_enabled("fibonacci_retracement", "btc_scalp") is True
        assert registry.is_enabled("fibonacci_retracement", "gold_swing") is True
        assert registry.is_enabled("fibonacci_retracement", "us30_scalp") is True
    
    def test_get_asset_params(self):
        """Test getting asset-specific parameters."""
        config = {
            'strategies': {
                'fibonacci_retracement': {
                    'enabled': True,
                    'params': {
                        'btc': {
                            'lookback': 50,
                            'tolerance': 0.5
                        },
                        'gold': {
                            'lookback': 40,
                            'tolerance': 0.3
                        }
                    }
                }
            }
        }
        registry = StrategyRegistry(config)
        
        registry.register_strategy(
            "fibonacci_retracement",
            "_detect_fibonacci_retracement",
            default_params={'lookback': 30, 'tolerance': 0.4}
        )
        
        # BTC params override defaults
        btc_params = registry.get_asset_params("fibonacci_retracement", "btc")
        assert btc_params['lookback'] == 50
        assert btc_params['tolerance'] == 0.5
        
        # Gold params override defaults
        gold_params = registry.get_asset_params("fibonacci_retracement", "gold")
        assert gold_params['lookback'] == 40
        assert gold_params['tolerance'] == 0.3
        
        # US30 uses defaults (no asset-specific params)
        us30_params = registry.get_asset_params("fibonacci_retracement", "us30")
        assert us30_params['lookback'] == 30
        assert us30_params['tolerance'] == 0.4
    
    def test_get_all_params(self):
        """Test getting all parameters for strategy."""
        config = {
            'strategies': {
                'fibonacci_retracement': {
                    'enabled': True,
                    'params': {
                        'volume_threshold': 1.3,
                        'require_reversal': True
                    }
                }
            }
        }
        registry = StrategyRegistry(config)
        
        registry.register_strategy(
            "fibonacci_retracement",
            "_detect_fibonacci_retracement",
            default_params={'lookback': 50}
        )
        
        params = registry.get_all_params("fibonacci_retracement")
        
        assert params['lookback'] == 50  # From defaults
        assert params['volume_threshold'] == 1.3  # From config
        assert params['require_reversal'] is True  # From config
    
    def test_record_execution(self):
        """Test recording strategy execution statistics."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        registry.register_strategy("fibonacci_retracement", "_detect_fibonacci_retracement")
        
        # Record successful executions
        registry.record_execution("fibonacci_retracement", success=True)
        registry.record_execution("fibonacci_retracement", success=True)
        
        # Record failed execution
        registry.record_execution("fibonacci_retracement", success=False)
        
        stats = registry.get_execution_stats("fibonacci_retracement")
        
        assert stats['count'] == 3
        assert stats['success'] == 2
        assert stats['failures'] == 1
    
    def test_get_execution_stats_nonexistent(self):
        """Test getting stats for non-existent strategy."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        stats = registry.get_execution_stats("nonexistent")
        
        assert stats['count'] == 0
        assert stats['success'] == 0
        assert stats['failures'] == 0
    
    def test_get_all_stats(self):
        """Test getting all execution statistics."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        registry.register_strategy("fibonacci_retracement", "_detect_fibonacci_retracement")
        registry.register_strategy("support_resistance_bounce", "_detect_support_resistance_bounce")
        
        registry.record_execution("fibonacci_retracement", success=True)
        registry.record_execution("support_resistance_bounce", success=False)
        
        all_stats = registry.get_all_stats()
        
        assert "fibonacci_retracement" in all_stats
        assert "support_resistance_bounce" in all_stats
        assert all_stats["fibonacci_retracement"]['success'] == 1
        assert all_stats["support_resistance_bounce"]['failures'] == 1
    
    def test_get_enabled_strategies(self):
        """Test getting list of enabled strategies."""
        config = {
            'strategies': {
                'fibonacci_retracement': {
                    'enabled': True,
                    'scanners': ['btc_scalp']
                },
                'support_resistance_bounce': {
                    'enabled': True,
                    'scanners': ['btc_scalp', 'gold_scalp']
                },
                'mean_reversion': {
                    'enabled': False,
                    'scanners': ['btc_scalp']
                }
            }
        }
        registry = StrategyRegistry(config)
        
        registry.register_strategy("fibonacci_retracement", "_detect_fibonacci_retracement")
        registry.register_strategy("support_resistance_bounce", "_detect_support_resistance_bounce")
        registry.register_strategy("mean_reversion", "_detect_mean_reversion")
        
        enabled = registry.get_enabled_strategies("btc_scalp")
        
        assert "fibonacci_retracement" in enabled
        assert "support_resistance_bounce" in enabled
        assert "mean_reversion" not in enabled  # Disabled
    
    def test_reload_config(self):
        """Test reloading configuration."""
        config1 = {
            'strategies': {
                'fibonacci_retracement': {
                    'enabled': True,
                    'scanners': ['btc_scalp']
                }
            }
        }
        registry = StrategyRegistry(config1)
        
        registry.register_strategy("fibonacci_retracement", "_detect_fibonacci_retracement")
        
        # Initially enabled
        assert registry.is_enabled("fibonacci_retracement", "btc_scalp") is True
        
        # Reload with new config (disabled)
        config2 = {
            'strategies': {
                'fibonacci_retracement': {
                    'enabled': False,
                    'scanners': ['btc_scalp']
                }
            }
        }
        registry.reload_config(config2)
        
        # Now disabled
        assert registry.is_enabled("fibonacci_retracement", "btc_scalp") is False
    
    def test_list_registered_strategies(self):
        """Test listing all registered strategies."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        registry.register_strategy("fibonacci_retracement", "_detect_fibonacci_retracement")
        registry.register_strategy("support_resistance_bounce", "_detect_support_resistance_bounce")
        
        strategies = registry.list_registered_strategies()
        
        assert len(strategies) == 2
        assert "fibonacci_retracement" in strategies
        assert "support_resistance_bounce" in strategies
    
    def test_get_strategy_info(self):
        """Test getting strategy information."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        registry.register_strategy(
            "fibonacci_retracement",
            "_detect_fibonacci_retracement",
            default_params={'lookback': 50}
        )
        
        registry.record_execution("fibonacci_retracement", success=True)
        
        info = registry.get_strategy_info("fibonacci_retracement")
        
        assert info is not None
        assert info['method_name'] == "_detect_fibonacci_retracement"
        assert info['default_params'] == {'lookback': 50}
        assert info['stats']['count'] == 1
        assert info['stats']['success'] == 1
    
    def test_get_strategy_info_nonexistent(self):
        """Test getting info for non-existent strategy."""
        config = {'strategies': {}}
        registry = StrategyRegistry(config)
        
        info = registry.get_strategy_info("nonexistent")
        
        assert info is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
