"""
Unified Configuration Loader
Loads and validates the unified configuration file with environment variable support.
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class UnifiedConfigLoader:
    """Load and manage unified configuration with environment variable overrides."""
    
    def __init__(self, config_path: str = "config/unified_config.json"):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to unified config file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> bool:
        """
        Load configuration from file and apply environment overrides.
        
        Returns:
            True if loaded successfully
        """
        try:
            if not self.config_path.exists():
                logger.error(f"Config file not found: {self.config_path}")
                return False
            
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Apply environment variable overrides
            self._apply_env_overrides()
            
            logger.info(f"✓ Configuration loaded from {self.config_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to sensitive data."""
        env_mappings = {
            'ALPHA_VANTAGE_KEY': ['data_providers', 'credentials', 'alpha_vantage_key'],
            'TWELVE_DATA_KEY': ['data_providers', 'credentials', 'twelve_data_key'],
            'BINANCE_API_KEY': ['data_providers', 'credentials', 'binance_api_key'],
            'BINANCE_API_SECRET': ['data_providers', 'credentials', 'binance_api_secret'],
            'SMTP_PASSWORD': ['communication', 'smtp', 'password'],
            'TELEGRAM_BOT_TOKEN': ['communication', 'telegram', 'bot_token'],
            'TELEGRAM_CHAT_ID': ['communication', 'telegram', 'chat_id'],
        }
        
        for env_var, path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(path, value)
                logger.debug(f"Applied environment override: {env_var}")
    
    def _set_nested_value(self, path: list, value: Any):
        """Set a value in nested dictionary using path."""
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Key path (e.g., 'communication.smtp.server')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def get_asset_config(self, asset: str) -> Optional[Dict]:
        """
        Get asset-specific configuration.
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'XAUUSD')
            
        Returns:
            Asset config dict or None
        """
        return self.config.get('asset_specific', {}).get(asset)
    
    def get_scanner_config(self, scanner_id: str) -> Optional[Dict]:
        """
        Get scanner-specific configuration.
        
        Args:
            scanner_id: Scanner identifier
            
        Returns:
            Scanner config dict or None
        """
        return self.config.get('scanners', {}).get(scanner_id)
    
    def get_strategy_config(self, strategy_name: str) -> Optional[Dict]:
        """
        Get strategy configuration.
        
        Args:
            strategy_name: Strategy name
            
        Returns:
            Strategy config dict or None
        """
        return self.config.get('strategies', {}).get(strategy_name)
    
    def get_enabled_scanners(self) -> list:
        """
        Get list of enabled scanner IDs.
        
        Returns:
            List of enabled scanner IDs
        """
        scanners = self.config.get('scanners', {})
        return [sid for sid, cfg in scanners.items() if cfg.get('enabled', False)]
    
    def get_enabled_assets(self) -> list:
        """
        Get list of enabled asset symbols.
        
        Returns:
            List of enabled asset symbols
        """
        assets = self.config.get('asset_specific', {})
        return [asset for asset, cfg in assets.items() if cfg.get('enabled', False)]
    
    def get_enabled_strategies(self) -> list:
        """
        Get list of enabled strategy names.
        
        Returns:
            List of enabled strategy names
        """
        strategies = self.config.get('strategies', {})
        return [name for name, cfg in strategies.items() if cfg.get('enabled', False)]
    
    def validate(self) -> tuple[bool, list]:
        """
        Validate configuration completeness.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required top-level sections
        required_sections = [
            'application', 'data_providers', 'communication',
            'indicators', 'signal_rules', 'scanners'
        ]
        
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
        
        # Check SMTP configuration
        smtp = self.config.get('communication', {}).get('smtp', {})
        if smtp.get('enabled'):
            required_smtp = ['server', 'port', 'user', 'password', 'from_email', 'to_email']
            for field in required_smtp:
                if not smtp.get(field):
                    errors.append(f"SMTP missing required field: {field}")
        
        # Check Telegram configuration
        telegram = self.config.get('communication', {}).get('telegram', {})
        if telegram.get('enabled'):
            if not telegram.get('bot_token'):
                errors.append("Telegram missing bot_token")
            if not telegram.get('chat_id'):
                errors.append("Telegram missing chat_id")
        
        # Check at least one scanner is enabled
        enabled_scanners = self.get_enabled_scanners()
        if not enabled_scanners:
            errors.append("No scanners are enabled")
        
        # Check at least one strategy is enabled
        enabled_strategies = self.get_enabled_strategies()
        if not enabled_strategies:
            errors.append("No strategies are enabled")
        
        # Check data provider credentials
        credentials = self.config.get('data_providers', {}).get('credentials', {})
        if not any(credentials.values()):
            errors.append("No data provider credentials configured")
        
        return len(errors) == 0, errors
    
    def print_summary(self):
        """Print configuration summary."""
        print("\n" + "="*80)
        print("CONFIGURATION SUMMARY")
        print("="*80)
        
        print(f"\nApplication: {self.config.get('application', {}).get('name')}")
        print(f"Version: {self.config.get('application', {}).get('version')}")
        
        print(f"\nEnabled Scanners: {len(self.get_enabled_scanners())}")
        for scanner in self.get_enabled_scanners():
            print(f"  - {scanner}")
        
        print(f"\nEnabled Assets: {len(self.get_enabled_assets())}")
        for asset in self.get_enabled_assets():
            print(f"  - {asset}")
        
        print(f"\nEnabled Strategies: {len(self.get_enabled_strategies())}")
        for strategy in self.get_enabled_strategies():
            print(f"  - {strategy}")
        
        print(f"\nCommunication:")
        smtp = self.config.get('communication', {}).get('smtp', {})
        print(f"  SMTP: {'✓ Enabled' if smtp.get('enabled') else '✗ Disabled'}")
        telegram = self.config.get('communication', {}).get('telegram', {})
        print(f"  Telegram: {'✓ Enabled' if telegram.get('enabled') else '✗ Disabled'}")
        
        print("\n" + "="*80 + "\n")
    
    def export_for_scanner(self, scanner_id: str) -> Dict:
        """
        Export configuration for specific scanner.
        
        Args:
            scanner_id: Scanner identifier
            
        Returns:
            Configuration dict for scanner
        """
        scanner_cfg = self.get_scanner_config(scanner_id)
        if not scanner_cfg:
            return {}
        
        # Build scanner-specific config
        config = {
            'scanner': scanner_cfg,
            'indicators': self.config.get('indicators', {}),
            'signal_rules': self.config.get('signal_rules', {}),
            'quality_filter': self.config.get('quality_filter', {}),
            'communication': self.config.get('communication', {}),
            'logging': self.config.get('logging', {}),
            'diagnostics': self.config.get('diagnostics', {}),
        }
        
        # Add asset-specific configs
        if 'symbol' in scanner_cfg:
            asset = scanner_cfg['symbol'].split('/')[0]
            asset_cfg = self.get_asset_config(asset)
            if asset_cfg:
                config['asset_specific'] = asset_cfg
        
        # Add strategy configs
        config['strategies'] = {}
        for strategy_name in scanner_cfg.get('strategies', []):
            strategy_cfg = self.get_strategy_config(strategy_name)
            if strategy_cfg:
                config['strategies'][strategy_name] = strategy_cfg
        
        return config


# Global config instance
_config_instance: Optional[UnifiedConfigLoader] = None


def get_config(config_path: str = "config/unified_config.json") -> UnifiedConfigLoader:
    """
    Get or create global config instance.
    
    Args:
        config_path: Path to config file
        
    Returns:
        UnifiedConfigLoader instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = UnifiedConfigLoader(config_path)
    
    return _config_instance


if __name__ == "__main__":
    # Test configuration loading
    logging.basicConfig(level=logging.INFO)
    
    config = UnifiedConfigLoader()
    
    # Validate
    is_valid, errors = config.validate()
    if is_valid:
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration has errors:")
        for error in errors:
            print(f"  - {error}")
    
    # Print summary
    config.print_summary()
    
    # Test scanner export
    for scanner_id in config.get_enabled_scanners()[:2]:
        print(f"\nScanner config for {scanner_id}:")
        scanner_config = config.export_for_scanner(scanner_id)
        print(json.dumps(scanner_config, indent=2)[:500] + "...")
