"""
Asset Configuration Manager
Manages symbol-specific configurations with validation and hot-reload support.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class AssetConfigManager:
    """Manages asset-specific configurations for multi-symbol scanning."""
    
    # Required fields for symbol configuration
    REQUIRED_FIELDS = [
        'enabled', 'asset_type', 'display_name', 'timeframes', 'signal_rules'
    ]
    
    # Valid asset types
    VALID_ASSET_TYPES = ['crypto', 'fx', 'index', 'commodity']
    
    # Valid timeframes
    VALID_TIMEFRAMES = ['1m', '2m', '5m', '15m', '30m', '1h', '90m', '4h', '1d', '5d', '1wk', '1mo']
    
    def __init__(self, config_path: str):
        """
        Initialize Asset Config Manager.
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = Path(config_path)
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.global_settings: Dict[str, Any] = {}
        self.last_load_time: Optional[datetime] = None
        self.load_errors: List[str] = []
        
        logger.info(f"Initializing AssetConfigManager with config: {config_path}")
        self.load_configs()
    
    def load_configs(self) -> None:
        """Load configurations from JSON file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            # Extract global settings
            self.global_settings = data.get('global_settings', {})
            
            # Extract symbol configurations
            symbols_data = data.get('symbols', {})
            
            # Clear previous configs and errors
            self.configs.clear()
            self.load_errors.clear()
            
            # Load and validate each symbol
            for symbol, config in symbols_data.items():
                is_valid, errors = self.validate_config(symbol, config)
                
                if is_valid:
                    self.configs[symbol] = config
                    logger.info(f"Loaded configuration for {symbol} ({config.get('display_name', symbol)})")
                else:
                    error_msg = f"Invalid configuration for {symbol}: {', '.join(errors)}"
                    self.load_errors.append(error_msg)
                    logger.error(error_msg)
            
            self.last_load_time = datetime.now()
            
            logger.info(f"Successfully loaded {len(self.configs)} symbol configurations")
            if self.load_errors:
                logger.warning(f"Encountered {len(self.load_errors)} configuration errors")
            
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            raise
    
    def validate_config(self, symbol: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a symbol configuration.
        
        Args:
            symbol: Symbol identifier
            config: Configuration dictionary
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # If missing required fields, return early
        if errors:
            return False, errors
        
        # Validate asset_type
        asset_type = config.get('asset_type', '')
        if asset_type not in self.VALID_ASSET_TYPES:
            errors.append(f"Invalid asset_type '{asset_type}'. Must be one of: {', '.join(self.VALID_ASSET_TYPES)}")
        
        # Validate timeframes
        timeframes = config.get('timeframes', [])
        if not isinstance(timeframes, list) or len(timeframes) == 0:
            errors.append("timeframes must be a non-empty list")
        else:
            invalid_tfs = [tf for tf in timeframes if tf not in self.VALID_TIMEFRAMES]
            if invalid_tfs:
                errors.append(f"Invalid timeframes: {', '.join(invalid_tfs)}")
        
        # Validate signal_rules
        signal_rules = config.get('signal_rules', {})
        if not isinstance(signal_rules, dict):
            errors.append("signal_rules must be a dictionary")
        else:
            # Check for required signal rule fields
            required_signal_fields = [
                'volume_spike_threshold', 'rsi_min', 'rsi_max',
                'stop_loss_atr_multiplier', 'take_profit_atr_multiplier'
            ]
            for field in required_signal_fields:
                if field not in signal_rules:
                    errors.append(f"Missing required signal_rules field: {field}")
                elif not isinstance(signal_rules[field], (int, float)):
                    errors.append(f"signal_rules.{field} must be a number")
        
        # Validate exit_rules if present
        if 'exit_rules' in config:
            exit_rules = config['exit_rules']
            if not isinstance(exit_rules, dict):
                errors.append("exit_rules must be a dictionary")
            else:
                # Validate exit rule fields
                if 'grace_period_minutes' in exit_rules:
                    if not isinstance(exit_rules['grace_period_minutes'], (int, float)) or exit_rules['grace_period_minutes'] < 0:
                        errors.append("exit_rules.grace_period_minutes must be a non-negative number")
                
                if 'min_profit_threshold_percent' in exit_rules:
                    if not isinstance(exit_rules['min_profit_threshold_percent'], (int, float)):
                        errors.append("exit_rules.min_profit_threshold_percent must be a number")
        
        # Validate trading_sessions for FX
        if asset_type == 'fx' and 'trading_sessions' in config:
            sessions = config['trading_sessions']
            if not isinstance(sessions, dict):
                errors.append("trading_sessions must be a dictionary")
            else:
                valid_sessions = ['Asian', 'London', 'NewYork']
                if 'primary' in sessions:
                    if not isinstance(sessions['primary'], list):
                        errors.append("trading_sessions.primary must be a list")
                    else:
                        invalid_sessions = [s for s in sessions['primary'] if s not in valid_sessions]
                        if invalid_sessions:
                            errors.append(f"Invalid trading sessions: {', '.join(invalid_sessions)}")
        
        return len(errors) == 0, errors
    
    def get_symbol_config(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific symbol.
        
        Args:
            symbol: Symbol identifier
            
        Returns:
            Configuration dictionary or None if not found
        """
        return self.configs.get(symbol)
    
    def get_enabled_symbols(self) -> List[str]:
        """
        Get list of enabled symbols.
        
        Returns:
            List of symbol identifiers
        """
        return [symbol for symbol, config in self.configs.items() if config.get('enabled', False)]
    
    def get_symbols_by_type(self, asset_type: str) -> List[str]:
        """
        Get all symbols of a specific type.
        
        Args:
            asset_type: Type of asset ('crypto', 'fx', 'index', 'commodity')
            
        Returns:
            List of symbol identifiers
        """
        return [
            symbol for symbol, config in self.configs.items()
            if config.get('asset_type') == asset_type and config.get('enabled', False)
        ]
    
    def get_all_symbols(self) -> List[str]:
        """
        Get all configured symbols (enabled and disabled).
        
        Returns:
            List of symbol identifiers
        """
        return list(self.configs.keys())
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a global setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.global_settings.get(key, default)
    
    def reload_configs(self) -> Tuple[bool, List[str]]:
        """
        Hot-reload configurations without restart.
        
        Returns:
            (success, list_of_errors)
        """
        logger.info("Reloading configurations...")
        
        try:
            # Store old configs for rollback
            old_configs = self.configs.copy()
            old_global = self.global_settings.copy()
            
            # Attempt to load new configs
            self.load_configs()
            
            if self.load_errors:
                logger.warning(f"Reload completed with {len(self.load_errors)} errors")
                return False, self.load_errors
            
            logger.info("Configuration reload successful")
            return True, []
            
        except Exception as e:
            # Rollback on error
            logger.error(f"Failed to reload configurations: {e}")
            self.configs = old_configs
            self.global_settings = old_global
            return False, [str(e)]
    
    def get_load_errors(self) -> List[str]:
        """
        Get list of errors from last load attempt.
        
        Returns:
            List of error messages
        """
        return self.load_errors.copy()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get summary of loaded configurations.
        
        Returns:
            Dictionary with configuration statistics
        """
        enabled_count = len(self.get_enabled_symbols())
        
        type_counts = {}
        for asset_type in self.VALID_ASSET_TYPES:
            type_counts[asset_type] = len(self.get_symbols_by_type(asset_type))
        
        return {
            'total_symbols': len(self.configs),
            'enabled_symbols': enabled_count,
            'disabled_symbols': len(self.configs) - enabled_count,
            'by_type': type_counts,
            'last_load_time': self.last_load_time.isoformat() if self.last_load_time else None,
            'load_errors': len(self.load_errors),
            'config_file': str(self.config_path)
        }
    
    def create_default_config_template(self, output_path: str) -> None:
        """
        Create a default configuration template file.
        
        Args:
            output_path: Path where template should be saved
        """
        template = {
            "symbols": {
                "BTC-USD": {
                    "enabled": True,
                    "asset_type": "crypto",
                    "display_name": "Bitcoin",
                    "emoji": "₿",
                    "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
                    "signal_rules": {
                        "volume_spike_threshold": 0.8,
                        "rsi_min": 30,
                        "rsi_max": 70,
                        "stop_loss_atr_multiplier": 1.5,
                        "take_profit_atr_multiplier": 2.0,
                        "min_confluence_factors": 4,
                        "min_confidence_score": 4
                    },
                    "exit_rules": {
                        "grace_period_minutes": 30,
                        "min_profit_threshold_percent": 1.0,
                        "max_giveback_percent": 40,
                        "min_peak_profit_for_exit": 2.0
                    },
                    "volatility_thresholds": {
                        "min_atr_percent": 0.5,
                        "max_atr_percent": 10.0
                    }
                },
                "ETH-USD": {
                    "enabled": True,
                    "asset_type": "crypto",
                    "display_name": "Ethereum",
                    "emoji": "Ξ",
                    "timeframes": ["1m", "5m", "15m", "1h", "4h"],
                    "signal_rules": {
                        "volume_spike_threshold": 0.9,
                        "rsi_min": 30,
                        "rsi_max": 70,
                        "stop_loss_atr_multiplier": 1.8,
                        "take_profit_atr_multiplier": 2.2,
                        "min_confluence_factors": 4,
                        "min_confidence_score": 4
                    },
                    "exit_rules": {
                        "grace_period_minutes": 30,
                        "min_profit_threshold_percent": 1.2,
                        "max_giveback_percent": 40,
                        "min_peak_profit_for_exit": 2.0
                    }
                },
                "EURUSD=X": {
                    "enabled": False,
                    "asset_type": "fx",
                    "display_name": "EUR/USD",
                    "emoji": "💱",
                    "timeframes": ["5m", "15m", "1h", "4h"],
                    "signal_rules": {
                        "volume_spike_threshold": 1.2,
                        "rsi_min": 35,
                        "rsi_max": 65,
                        "stop_loss_atr_multiplier": 1.2,
                        "take_profit_atr_multiplier": 1.5,
                        "min_confluence_factors": 5,
                        "min_confidence_score": 4
                    },
                    "exit_rules": {
                        "grace_period_minutes": 45,
                        "min_profit_threshold_percent": 0.3,
                        "max_giveback_percent": 35,
                        "min_peak_profit_for_exit": 0.5
                    },
                    "trading_sessions": {
                        "primary": ["London", "NewYork"],
                        "secondary": ["Asian"],
                        "require_primary_session": True
                    }
                }
            },
            "global_settings": {
                "polling_interval_seconds": 60,
                "max_concurrent_symbols": 10,
                "signal_conflict_window_minutes": 5,
                "duplicate_signal_window_minutes": 10
            }
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(template, f, indent=2)
        
        logger.info(f"Created default configuration template at: {output_path}")
    
    def check_symbol_availability(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if a symbol is available on Yahoo Finance.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            
            # Try to fetch recent data
            hist = ticker.history(period="1d")
            
            if hist.empty:
                return False, f"No data available for {symbol}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error checking {symbol}: {str(e)}"
    
    def validate_all_symbols(self) -> Dict[str, Tuple[bool, str]]:
        """
        Validate availability of all configured symbols.
        
        Returns:
            Dictionary mapping symbol to (is_available, error_message)
        """
        results = {}
        
        for symbol in self.configs.keys():
            is_available, error_msg = self.check_symbol_availability(symbol)
            results[symbol] = (is_available, error_msg)
            
            if not is_available:
                logger.warning(f"Symbol {symbol} is not available: {error_msg}")
            else:
                logger.info(f"Symbol {symbol} is available")
        
        return results


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create a test configuration template
    manager = AssetConfigManager.__new__(AssetConfigManager)
    manager.create_default_config_template("config/multi_symbol_template.json")
    
    print("Default configuration template created at: config/multi_symbol_template.json")
