"""Strategy registry for managing and configuring trading strategies."""

from typing import Dict, List, Callable, Type, Optional, Any
import logging

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """
    Registry for managing trading strategies and their configurations.
    
    Handles strategy registration, asset-specific parameter loading,
    and enable/disable toggles per scanner.
    """
    
    def __init__(self, config: dict):
        """
        Initialize strategy registry.
        
        Args:
            config: Configuration dictionary with strategy settings
        """
        self.config = config
        self.strategies = {}  # strategy_name -> {class, default_params}
        self.asset_configs = {}  # strategy_name -> {asset -> params}
        self.enabled_strategies = {}  # scanner_type -> [strategy_names]
        self.execution_stats = {}  # strategy_name -> {count, success, failures}
        
        logger.info("StrategyRegistry initialized")
    
    def register_strategy(
        self, 
        name: str, 
        strategy_method_name: str,
        default_params: Optional[dict] = None
    ):
        """
        Register a strategy with default parameters.
        
        Args:
            name: Strategy name (e.g., "fibonacci_retracement")
            strategy_method_name: Name of the detection method (e.g., "_detect_fibonacci_retracement")
            default_params: Default parameters for the strategy
        """
        if default_params is None:
            default_params = {}
        
        self.strategies[name] = {
            'method_name': strategy_method_name,
            'default_params': default_params
        }
        
        # Initialize execution stats
        self.execution_stats[name] = {
            'count': 0,
            'success': 0,
            'failures': 0
        }
        
        logger.debug(f"Registered strategy: {name}")
    
    def get_strategy_method(
        self, 
        name: str, 
        signal_detector: Any
    ) -> Optional[Callable]:
        """
        Get strategy detection method from SignalDetector instance.
        
        Args:
            name: Strategy name
            signal_detector: SignalDetector instance
            
        Returns:
            Bound method from SignalDetector or None if not found
        """
        if name not in self.strategies:
            logger.warning(f"Strategy '{name}' not registered")
            return None
        
        method_name = self.strategies[name]['method_name']
        
        if not hasattr(signal_detector, method_name):
            logger.warning(f"SignalDetector does not have method '{method_name}'")
            return None
        
        return getattr(signal_detector, method_name)
    
    def is_enabled(self, strategy_name: str, scanner_type: str) -> bool:
        """
        Check if strategy is enabled for this scanner.
        
        Args:
            strategy_name: Name of the strategy
            scanner_type: Scanner type (e.g., "btc_scalp", "gold_swing")
            
        Returns:
            True if strategy is enabled, False otherwise
        """
        # Check if strategy exists
        if strategy_name not in self.strategies:
            return False
        
        # Load from config if not cached
        if scanner_type not in self.enabled_strategies:
            self._load_enabled_strategies(scanner_type)
        
        # Check if strategy is in enabled list for this scanner
        return strategy_name in self.enabled_strategies.get(scanner_type, [])
    
    def _load_enabled_strategies(self, scanner_type: str):
        """Load enabled strategies for scanner from config."""
        enabled = []
        
        # Check config for strategy settings
        strategies_config = self.config.get('strategies', {})
        
        for strategy_name, strategy_config in strategies_config.items():
            # Check if strategy is globally enabled
            if not strategy_config.get('enabled', True):
                continue
            
            # Check if strategy is enabled for this scanner
            scanners = strategy_config.get('scanners', [])
            if scanner_type in scanners or not scanners:  # Empty list means all scanners
                enabled.append(strategy_name)
        
        self.enabled_strategies[scanner_type] = enabled
        logger.debug(f"Loaded {len(enabled)} enabled strategies for {scanner_type}")
    
    def get_asset_params(self, strategy_name: str, asset: str) -> dict:
        """
        Get asset-specific parameters for strategy.
        
        Args:
            strategy_name: Name of the strategy
            asset: Asset type ("btc", "gold", "us30")
            
        Returns:
            Dictionary of parameters for this asset
        """
        # Get default params
        default_params = self.strategies.get(strategy_name, {}).get('default_params', {})
        
        # Get asset-specific params from config
        strategies_config = self.config.get('strategies', {})
        strategy_config = strategies_config.get(strategy_name, {})
        params_config = strategy_config.get('params', {})
        
        # Asset-specific params override defaults
        asset_lower = asset.lower()
        asset_params = params_config.get(asset_lower, {})
        
        # Merge default and asset-specific params
        merged_params = {**default_params, **asset_params}
        
        return merged_params
    
    def get_all_params(self, strategy_name: str) -> dict:
        """
        Get all parameters for strategy (not asset-specific).
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary of parameters
        """
        # Get default params
        default_params = self.strategies.get(strategy_name, {}).get('default_params', {})
        
        # Get params from config
        strategies_config = self.config.get('strategies', {})
        strategy_config = strategies_config.get(strategy_name, {})
        params_config = strategy_config.get('params', {})
        
        # Merge default and config params
        merged_params = {**default_params, **params_config}
        
        return merged_params
    
    def record_execution(self, strategy_name: str, success: bool):
        """
        Record strategy execution for statistics.
        
        Args:
            strategy_name: Name of the strategy
            success: Whether execution was successful
        """
        if strategy_name not in self.execution_stats:
            self.execution_stats[strategy_name] = {
                'count': 0,
                'success': 0,
                'failures': 0
            }
        
        self.execution_stats[strategy_name]['count'] += 1
        
        if success:
            self.execution_stats[strategy_name]['success'] += 1
        else:
            self.execution_stats[strategy_name]['failures'] += 1
    
    def get_execution_stats(self, strategy_name: str) -> dict:
        """
        Get execution statistics for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary with execution stats
        """
        return self.execution_stats.get(strategy_name, {
            'count': 0,
            'success': 0,
            'failures': 0
        })
    
    def get_all_stats(self) -> dict:
        """Get execution statistics for all strategies."""
        return self.execution_stats.copy()
    
    def get_enabled_strategies(self, scanner_type: str) -> List[str]:
        """
        Get list of enabled strategies for scanner.
        
        Args:
            scanner_type: Scanner type (e.g., "btc_scalp")
            
        Returns:
            List of enabled strategy names
        """
        if scanner_type not in self.enabled_strategies:
            self._load_enabled_strategies(scanner_type)
        
        return self.enabled_strategies.get(scanner_type, [])
    
    def reload_config(self, new_config: dict):
        """
        Reload configuration without restart.
        
        Args:
            new_config: New configuration dictionary
        """
        self.config = new_config
        self.enabled_strategies = {}  # Clear cache
        logger.info("Strategy registry configuration reloaded")
    
    def list_registered_strategies(self) -> List[str]:
        """Get list of all registered strategy names."""
        return list(self.strategies.keys())
    
    def get_strategy_info(self, strategy_name: str) -> Optional[dict]:
        """
        Get information about a registered strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary with strategy info or None
        """
        if strategy_name not in self.strategies:
            return None
        
        strategy_info = self.strategies[strategy_name].copy()
        strategy_info['stats'] = self.get_execution_stats(strategy_name)
        
        return strategy_info
