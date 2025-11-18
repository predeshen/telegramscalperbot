"""
Configuration Validator
Validates configuration parameters and warns about out-of-bounds values
"""
import logging
from typing import Dict, List, Any, Optional, Tuple


logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration parameters and logs warnings"""
    
    # Reasonable bounds for configuration parameters
    # Format: parameter_name: (min_value, max_value, recommended_value)
    REASONABLE_BOUNDS = {
        'volume_spike_threshold': (0.5, 3.0, 1.3),
        'volume_momentum_shift': (0.5, 3.0, 1.3),
        'volume_trend_alignment': (0.5, 2.0, 0.8),
        'volume_ema_cloud_breakout': (0.8, 3.0, 1.3),
        'volume_mean_reversion': (0.8, 3.0, 1.5),
        'rsi_min': (10, 40, 25),
        'rsi_max': (60, 90, 75),
        'adx_min_momentum_shift': (10, 30, 15),
        'adx_min_trend_alignment': (10, 30, 15),
        'adx_min_trend': (10, 30, 15),
        'adx_threshold': (10, 30, 15),
        'adx_minimum': (10, 30, 15),
        'min_risk_reward': (0.8, 3.0, 1.2),
        'min_confluence_factors': (2, 5, 3),
        'min_confidence_score': (2, 5, 3),
        'duplicate_time_window_minutes': (1, 120, 10),
        'duplicate_price_threshold_percent': (0.1, 3.0, 1.0),
        'duplicate_window_seconds': (60, 7200, 600),
        'duplicate_price_tolerance_pct': (0.1, 3.0, 1.0),
        'significant_price_move_pct': (0.5, 5.0, 1.5),
        'stop_loss_atr_multiplier': (0.5, 5.0, 1.5),
        'take_profit_atr_multiplier': (0.5, 5.0, 2.0),
        'rsi_momentum_threshold': (1.0, 10.0, 55.0)
    }
    
    def __init__(self):
        """Initialize configuration validator"""
        logger.info("ConfigValidator initialized")
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration and return list of warnings
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Validate signal_rules section
        if 'signal_rules' in config:
            warnings.extend(self._validate_section(config['signal_rules'], 'signal_rules'))
        
        # Validate quality_filter section
        if 'quality_filter' in config:
            warnings.extend(self._validate_section(config['quality_filter'], 'quality_filter'))
        
        # Validate asset_specific sections
        if 'asset_specific' in config:
            for asset, asset_config in config['asset_specific'].items():
                warnings.extend(self._validate_section(asset_config, f'asset_specific.{asset}'))
                
                # Validate nested volume_thresholds
                if 'volume_thresholds' in asset_config:
                    warnings.extend(self._validate_section(
                        asset_config['volume_thresholds'], 
                        f'asset_specific.{asset}.volume_thresholds'
                    ))
        
        # Validate us30_strategy section (if present)
        if 'us30_strategy' in config:
            warnings.extend(self._validate_us30_strategy(config['us30_strategy']))
        
        # Log warnings
        if warnings:
            logger.warning(f"Configuration validation found {len(warnings)} warnings:")
            for warning in warnings:
                logger.warning(f"  {warning}")
        else:
            logger.info("✓ Configuration validation passed with no warnings")
        
        return warnings
    
    def _validate_section(self, section: Dict[str, Any], section_name: str) -> List[str]:
        """
        Validate a configuration section
        
        Args:
            section: Configuration section dictionary
            section_name: Name of the section for logging
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        for param, value in section.items():
            # Skip non-numeric values
            if not isinstance(value, (int, float)):
                continue
            
            # Check if parameter has defined bounds
            if param in self.REASONABLE_BOUNDS:
                min_val, max_val, recommended = self.REASONABLE_BOUNDS[param]
                
                if value < min_val or value > max_val:
                    warnings.append(
                        f"{section_name}.{param}={value} is outside reasonable range "
                        f"[{min_val}, {max_val}]. Recommended: {recommended}"
                    )
        
        return warnings
    
    def _validate_us30_strategy(self, us30_config: Dict[str, Any]) -> List[str]:
        """
        Validate US30-specific strategy configuration
        
        Args:
            us30_config: US30 strategy configuration
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # US30-specific bounds
        us30_bounds = {
            'min_fvg_percent': (0.01, 0.5, 0.05),
            'min_adx': (15, 35, 25),
            'min_volume_ratio': (0.8, 3.0, 1.2),
            'min_candle_body_percent': (40, 80, 60),
            'initial_tp_atr': (1.0, 5.0, 2.5),
            'stop_loss_atr': (0.5, 3.0, 1.5)
        }
        
        for param, value in us30_config.items():
            if not isinstance(value, (int, float)):
                continue
            
            if param in us30_bounds:
                min_val, max_val, recommended = us30_bounds[param]
                
                if value < min_val or value > max_val:
                    warnings.append(
                        f"us30_strategy.{param}={value} is outside reasonable range "
                        f"[{min_val}, {max_val}]. Recommended: {recommended}"
                    )
        
        return warnings
    
    def _get_nested_value(self, config: Dict[str, Any], param: str) -> Optional[Any]:
        """
        Get nested configuration value using dot notation
        
        Args:
            config: Configuration dictionary
            param: Parameter name (can use dot notation like 'signal_rules.rsi_min')
            
        Returns:
            Parameter value or None if not found
        """
        keys = param.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def validate_required_fields(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate that required configuration fields exist
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of error messages for missing required fields
        """
        errors = []
        
        # Required top-level fields
        required_fields = ['signal_rules']
        
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required configuration section: {field}")
        
        # Required signal_rules fields
        if 'signal_rules' in config:
            required_signal_rules = [
                'volume_spike_threshold',
                'rsi_min',
                'rsi_max',
                'duplicate_time_window_minutes',
                'duplicate_price_threshold_percent'
            ]
            
            for field in required_signal_rules:
                if field not in config['signal_rules']:
                    errors.append(f"Missing required field: signal_rules.{field}")
        
        if errors:
            logger.error(f"Configuration validation found {len(errors)} errors:")
            for error in errors:
                logger.error(f"  {error}")
        
        return errors
    
    def get_effective_value(
        self, 
        config: Dict[str, Any], 
        param: str, 
        asset: Optional[str] = None,
        default: Any = None
    ) -> Tuple[Any, str]:
        """
        Get effective configuration value with source tracking
        
        Checks asset-specific overrides first, then global config, then default
        
        Args:
            config: Configuration dictionary
            param: Parameter name
            asset: Asset symbol for asset-specific lookup (optional)
            default: Default value if not found
            
        Returns:
            Tuple of (value, source) where source is 'asset_specific', 'global', or 'default'
        """
        # Check asset-specific override
        if asset and 'asset_specific' in config and asset in config['asset_specific']:
            asset_config = config['asset_specific'][asset]
            if param in asset_config:
                return asset_config[param], f'asset_specific.{asset}'
        
        # Check global signal_rules
        if 'signal_rules' in config and param in config['signal_rules']:
            return config['signal_rules'][param], 'signal_rules'
        
        # Check quality_filter
        if 'quality_filter' in config and param in config['quality_filter']:
            return config['quality_filter'][param], 'quality_filter'
        
        # Return default
        return default, 'default'
    
    def log_active_configuration(self, config: Dict[str, Any], asset: Optional[str] = None):
        """
        Log active configuration values with their sources
        
        Args:
            config: Configuration dictionary
            asset: Asset symbol for asset-specific logging (optional)
        """
        logger.info("=" * 60)
        logger.info(f"Active Configuration{f' for {asset}' if asset else ''}")
        logger.info("=" * 60)
        
        # Key parameters to log
        key_params = [
            'volume_spike_threshold',
            'rsi_min',
            'rsi_max',
            'min_confluence_factors',
            'min_confidence_score',
            'min_risk_reward',
            'adx_min_trend_alignment',
            'duplicate_time_window_minutes',
            'duplicate_price_threshold_percent'
        ]
        
        for param in key_params:
            value, source = self.get_effective_value(config, param, asset)
            if value is not None:
                logger.info(f"  {param}: {value} (from {source})")
        
        logger.info("=" * 60)
    
    def suggest_improvements(self, config: Dict[str, Any]) -> List[str]:
        """
        Suggest configuration improvements based on best practices
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Check if diagnostics is enabled
        if not config.get('diagnostics', {}).get('enabled', False):
            suggestions.append(
                "💡 Enable diagnostics to track signal detection performance: "
                "diagnostics.enabled = true"
            )
        
        # Check if quality filter thresholds are too strict
        quality_filter = config.get('quality_filter', {})
        if quality_filter.get('min_confluence_factors', 0) > 3:
            suggestions.append(
                "💡 Consider reducing min_confluence_factors to 3 for more signals"
            )
        
        if quality_filter.get('min_confidence_score', 0) > 3:
            suggestions.append(
                "💡 Consider reducing min_confidence_score to 3 for more signals"
            )
        
        # Check volume thresholds
        signal_rules = config.get('signal_rules', {})
        if signal_rules.get('volume_spike_threshold', 0) > 1.5:
            suggestions.append(
                "💡 Consider reducing volume_spike_threshold to 1.3 for crypto scalping"
            )
        
        # Check RSI range
        rsi_min = signal_rules.get('rsi_min', 30)
        rsi_max = signal_rules.get('rsi_max', 70)
        if rsi_max - rsi_min < 40:
            suggestions.append(
                f"💡 RSI range ({rsi_min}-{rsi_max}) is narrow. "
                f"Consider expanding to 25-75 for more opportunities"
            )
        
        return suggestions


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    validator = ConfigValidator()
    
    # Example configuration
    test_config = {
        'signal_rules': {
            'volume_spike_threshold': 1.3,
            'rsi_min': 25,
            'rsi_max': 75,
            'min_confluence_factors': 3,
            'duplicate_time_window_minutes': 10,
            'duplicate_price_threshold_percent': 1.0
        },
        'quality_filter': {
            'min_risk_reward': 1.2,
            'min_confidence_score': 3
        }
    }
    
    # Validate configuration
    warnings = validator.validate_config(test_config)
    print(f"\nValidation warnings: {len(warnings)}")
    
    # Check required fields
    errors = validator.validate_required_fields(test_config)
    print(f"Validation errors: {len(errors)}")
    
    # Get suggestions
    suggestions = validator.suggest_improvements(test_config)
    print(f"\nSuggestions:")
    for suggestion in suggestions:
        print(f"  {suggestion}")
