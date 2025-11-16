"""Tests for AssetConfigManager."""
import pytest
import json
import tempfile
from pathlib import Path
from src.asset_config_manager import AssetConfigManager


class TestAssetConfigManager:
    """Test suite for AssetConfigManager."""
    
    @pytest.fixture
    def valid_config(self):
        """Create a valid configuration."""
        return {
            "symbols": {
                "BTC-USD": {
                    "enabled": True,
                    "asset_type": "crypto",
                    "display_name": "Bitcoin",
                    "timeframes": ["1m", "5m", "15m"],
                    "signal_rules": {
                        "volume_spike_threshold": 0.8,
                        "rsi_min": 30,
                        "rsi_max": 70,
                        "stop_loss_atr_multiplier": 1.5,
                        "take_profit_atr_multiplier": 2.0
                    }
                },
                "ETH-USD": {
                    "enabled": False,
                    "asset_type": "crypto",
                    "display_name": "Ethereum",
                    "timeframes": ["5m", "15m"],
                    "signal_rules": {
                        "volume_spike_threshold": 0.9,
                        "rsi_min": 30,
                        "rsi_max": 70,
                        "stop_loss_atr_multiplier": 1.8,
                        "take_profit_atr_multiplier": 2.2
                    }
                }
            },
            "global_settings": {
                "polling_interval_seconds": 60,
                "max_concurrent_symbols": 10
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, valid_config):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_config, f)
            return f.name
    
    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid configuration."""
        manager = AssetConfigManager(temp_config_file)
        
        assert len(manager.configs) == 2
        assert "BTC-USD" in manager.configs
        assert "ETH-USD" in manager.configs
        assert len(manager.load_errors) == 0
    
    def test_get_enabled_symbols(self, temp_config_file):
        """Test getting enabled symbols."""
        manager = AssetConfigManager(temp_config_file)
        
        enabled = manager.get_enabled_symbols()
        assert len(enabled) == 1
        assert "BTC-USD" in enabled
        assert "ETH-USD" not in enabled
    
    def test_get_symbols_by_type(self, temp_config_file):
        """Test getting symbols by asset type."""
        manager = AssetConfigManager(temp_config_file)
        
        crypto_symbols = manager.get_symbols_by_type("crypto")
        assert len(crypto_symbols) == 1  # Only enabled BTC-USD
        assert "BTC-USD" in crypto_symbols
    
    def test_get_symbol_config(self, temp_config_file):
        """Test getting configuration for a specific symbol."""
        manager = AssetConfigManager(temp_config_file)
        
        btc_config = manager.get_symbol_config("BTC-USD")
        assert btc_config is not None
        assert btc_config["display_name"] == "Bitcoin"
        assert btc_config["asset_type"] == "crypto"
        
        invalid_config = manager.get_symbol_config("INVALID")
        assert invalid_config is None
    
    def test_validate_missing_required_fields(self, temp_config_file):
        """Test validation with missing required fields."""
        manager = AssetConfigManager(temp_config_file)
        
        invalid_config = {
            "enabled": True,
            "asset_type": "crypto"
            # Missing display_name, timeframes, signal_rules
        }
        
        is_valid, errors = manager.validate_config("TEST", invalid_config)
        assert not is_valid
        assert len(errors) > 0
        assert any("display_name" in err for err in errors)
    
    def test_validate_invalid_asset_type(self, temp_config_file):
        """Test validation with invalid asset type."""
        manager = AssetConfigManager(temp_config_file)
        
        invalid_config = {
            "enabled": True,
            "asset_type": "invalid_type",
            "display_name": "Test",
            "timeframes": ["1m"],
            "signal_rules": {
                "volume_spike_threshold": 0.8,
                "rsi_min": 30,
                "rsi_max": 70,
                "stop_loss_atr_multiplier": 1.5,
                "take_profit_atr_multiplier": 2.0
            }
        }
        
        is_valid, errors = manager.validate_config("TEST", invalid_config)
        assert not is_valid
        assert any("asset_type" in err for err in errors)
    
    def test_validate_invalid_timeframes(self, temp_config_file):
        """Test validation with invalid timeframes."""
        manager = AssetConfigManager(temp_config_file)
        
        invalid_config = {
            "enabled": True,
            "asset_type": "crypto",
            "display_name": "Test",
            "timeframes": ["1m", "invalid_tf"],
            "signal_rules": {
                "volume_spike_threshold": 0.8,
                "rsi_min": 30,
                "rsi_max": 70,
                "stop_loss_atr_multiplier": 1.5,
                "take_profit_atr_multiplier": 2.0
            }
        }
        
        is_valid, errors = manager.validate_config("TEST", invalid_config)
        assert not is_valid
        assert any("timeframes" in err for err in errors)
    
    def test_get_global_setting(self, temp_config_file):
        """Test getting global settings."""
        manager = AssetConfigManager(temp_config_file)
        
        polling_interval = manager.get_global_setting("polling_interval_seconds")
        assert polling_interval == 60
        
        default_value = manager.get_global_setting("nonexistent", default=100)
        assert default_value == 100
    
    def test_get_config_summary(self, temp_config_file):
        """Test getting configuration summary."""
        manager = AssetConfigManager(temp_config_file)
        
        summary = manager.get_config_summary()
        assert summary["total_symbols"] == 2
        assert summary["enabled_symbols"] == 1
        assert summary["disabled_symbols"] == 1
        assert summary["by_type"]["crypto"] == 1
    
    def test_reload_configs(self, temp_config_file, valid_config):
        """Test hot-reload of configurations."""
        manager = AssetConfigManager(temp_config_file)
        
        # Verify initial state
        assert len(manager.get_enabled_symbols()) == 1
        
        # Modify config file
        valid_config["symbols"]["ETH-USD"]["enabled"] = True
        with open(temp_config_file, 'w') as f:
            json.dump(valid_config, f)
        
        # Reload
        success, errors = manager.reload_configs()
        assert success
        assert len(errors) == 0
        
        # Verify updated state
        assert len(manager.get_enabled_symbols()) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
