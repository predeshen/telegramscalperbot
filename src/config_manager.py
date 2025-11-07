"""
Configuration Manager
Centralized configuration with validation and hot-reload support
"""
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.unified_data_source import DataSourceConfig, RetryConfig


logger = logging.getLogger(__name__)


@dataclass
class ScannerConfig:
    """Configuration for individual scanner"""
    symbol: str
    mode: str  # scalp or swing
    timeframes: List[str]
    strategy: str
    enabled: bool = True


@dataclass
class AlerterConfig:
    """Configuration for alerter"""
    telegram_enabled: bool = True
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email_enabled: bool = False
    smtp_config: Optional[Dict[str, Any]] = None


@dataclass
class HealthConfig:
    """Configuration for health monitoring"""
    max_consecutive_failures: int = 3
    heartbeat_interval_seconds: int = 5400  # 90 minutes
    data_quality_check_enabled: bool = True


@dataclass
class UnifiedConfig:
    """Unified configuration structure"""
    data_source: DataSourceConfig
    scanners: List[ScannerConfig]
    quality_filter: Optional[Dict[str, Any]] = None
    alerter: Optional[AlerterConfig] = None
    health_monitor: Optional[HealthConfig] = None
    news_calendar_file: str = "config/news_events.json"


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors"""
    pass


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ConfigurationManager:
    """
    Manages centralized configuration for all scanners
    """
    
    def __init__(self, config_path: str):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config: Optional[UnifiedConfig] = None
        self.last_modified: Optional[datetime] = None
        
        logger.info(f"Initialized ConfigurationManager with path: {config_path}")
    
    def load_config(self) -> UnifiedConfig:
        """
        Load and validate configuration
        
        Returns:
            UnifiedConfig instance
            
        Raises:
            ConfigValidationError: If required fields missing or invalid
            FileNotFoundError: If config file doesn't exist
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                config_dict = json.load(f)
            
            # Validate configuration
            validation_result = self.validate_config(config_dict)
            
            if not validation_result.is_valid:
                error_msg = "Configuration validation failed:\n" + "\n".join(validation_result.errors)
                raise ConfigValidationError(error_msg)
            
            # Log warnings
            for warning in validation_result.warnings:
                logger.warning(f"Config warning: {warning}")
            
            # Parse configuration
            self.config = self._parse_config(config_dict)
            self.last_modified = datetime.fromtimestamp(self.config_path.stat().st_mtime)
            
            logger.info(f"Configuration loaded successfully: {len(self.config.scanners)} scanners configured")
            return self.config
            
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Error loading configuration: {e}")
    
    def validate_config(self, config: Dict) -> ValidationResult:
        """
        Validate configuration structure and values
        
        Required fields:
        - data_source.provider
        - data_source.symbol_map
        - scanners (list of scanner configs)
        - Each scanner: symbol, timeframes, strategy
        
        Args:
            config: Configuration dictionary
            
        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        
        # Check data_source section
        if 'data_source' not in config:
            errors.append("Missing required section: data_source")
        else:
            ds = config['data_source']
            
            if 'provider' not in ds:
                errors.append("Missing required field: data_source.provider")
            
            if 'symbol_map' not in ds:
                errors.append("Missing required field: data_source.symbol_map")
            elif not isinstance(ds['symbol_map'], dict):
                errors.append("data_source.symbol_map must be a dictionary")
            elif len(ds['symbol_map']) == 0:
                warnings.append("data_source.symbol_map is empty")
        
        # Check scanners section
        if 'scanners' not in config:
            errors.append("Missing required section: scanners")
        else:
            scanners = config['scanners']
            
            if not isinstance(scanners, list):
                errors.append("scanners must be a list")
            elif len(scanners) == 0:
                warnings.append("No scanners configured")
            else:
                for i, scanner in enumerate(scanners):
                    if not isinstance(scanner, dict):
                        errors.append(f"Scanner {i} must be a dictionary")
                        continue
                    
                    # Check required scanner fields
                    required_fields = ['symbol', 'timeframes', 'strategy']
                    for field in required_fields:
                        if field not in scanner:
                            errors.append(f"Scanner {i} missing required field: {field}")
                    
                    # Validate timeframes
                    if 'timeframes' in scanner:
                        if not isinstance(scanner['timeframes'], list):
                            errors.append(f"Scanner {i} timeframes must be a list")
                        elif len(scanner['timeframes']) == 0:
                            errors.append(f"Scanner {i} has no timeframes configured")
        
        # Check optional sections
        if 'quality_filter' in config:
            qf = config['quality_filter']
            if 'min_confluence_factors' in qf and qf['min_confluence_factors'] < 1:
                warnings.append("quality_filter.min_confluence_factors should be >= 1")
        
        if 'alerter' in config:
            alerter = config['alerter']
            if not alerter.get('telegram_enabled') and not alerter.get('email_enabled'):
                warnings.append("No alerter enabled (telegram or email)")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def hot_reload(self) -> bool:
        """
        Check for config changes and reload if modified
        
        Returns:
            True if config was reloaded, False otherwise
        """
        if not self.config_path.exists():
            logger.error(f"Config file no longer exists: {self.config_path}")
            return False
        
        try:
            current_mtime = datetime.fromtimestamp(self.config_path.stat().st_mtime)
            
            if self.last_modified is None or current_mtime > self.last_modified:
                logger.info("Configuration file modified, reloading...")
                self.load_config()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking config modification: {e}")
            return False
    
    def get_scanner_config(self, symbol: str, mode: str) -> Optional[ScannerConfig]:
        """
        Get configuration for specific scanner
        
        Args:
            symbol: BTC, XAUUSD, US30
            mode: scalp or swing
            
        Returns:
            ScannerConfig if found, None otherwise
        """
        if self.config is None:
            logger.error("Configuration not loaded")
            return None
        
        for scanner in self.config.scanners:
            if scanner.symbol == symbol and scanner.mode == mode:
                return scanner
        
        logger.warning(f"No configuration found for {symbol} {mode}")
        return None
    
    def _parse_config(self, config_dict: Dict) -> UnifiedConfig:
        """
        Parse configuration dictionary into UnifiedConfig
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            UnifiedConfig instance
        """
        # Parse data source config
        ds_dict = config_dict['data_source']
        retry_config = RetryConfig()
        if 'retry_config' in ds_dict:
            rc = ds_dict['retry_config']
            retry_config = RetryConfig(
                max_retries=rc.get('max_retries', 5),
                initial_delay_seconds=rc.get('initial_delay_seconds', 1),
                max_delay_seconds=rc.get('max_delay_seconds', 60),
                exponential_base=rc.get('exponential_base', 2.0)
            )
        
        data_source = DataSourceConfig(
            provider=ds_dict['provider'],
            symbol_map=ds_dict['symbol_map'],
            retry_config=retry_config
        )
        
        # Parse scanners
        scanners = []
        for scanner_dict in config_dict['scanners']:
            scanners.append(ScannerConfig(
                symbol=scanner_dict['symbol'],
                mode=scanner_dict.get('mode', 'scalp'),
                timeframes=scanner_dict['timeframes'],
                strategy=scanner_dict['strategy'],
                enabled=scanner_dict.get('enabled', True)
            ))
        
        # Parse optional sections
        quality_filter = config_dict.get('quality_filter')
        
        alerter_config = None
        if 'alerter' in config_dict:
            ac = config_dict['alerter']
            alerter_config = AlerterConfig(
                telegram_enabled=ac.get('telegram_enabled', True),
                telegram_bot_token=ac.get('telegram_bot_token'),
                telegram_chat_id=ac.get('telegram_chat_id'),
                email_enabled=ac.get('email_enabled', False),
                smtp_config=ac.get('smtp_config')
            )
        
        health_config = None
        if 'health_monitor' in config_dict:
            hc = config_dict['health_monitor']
            health_config = HealthConfig(
                max_consecutive_failures=hc.get('max_consecutive_failures', 3),
                heartbeat_interval_seconds=hc.get('heartbeat_interval_seconds', 5400),
                data_quality_check_enabled=hc.get('data_quality_check_enabled', True)
            )
        
        return UnifiedConfig(
            data_source=data_source,
            scanners=scanners,
            quality_filter=quality_filter,
            alerter=alerter_config,
            health_monitor=health_config,
            news_calendar_file=config_dict.get('news_calendar_file', 'config/news_events.json')
        )
    
    def save_config(self, config: UnifiedConfig) -> bool:
        """
        Save configuration to file
        
        Args:
            config: UnifiedConfig to save
            
        Returns:
            True if saved successfully
        """
        try:
            # Convert to dictionary
            config_dict = {
                'data_source': {
                    'provider': config.data_source.provider,
                    'symbol_map': config.data_source.symbol_map,
                    'retry_config': {
                        'max_retries': config.data_source.retry_config.max_retries,
                        'initial_delay_seconds': config.data_source.retry_config.initial_delay_seconds,
                        'max_delay_seconds': config.data_source.retry_config.max_delay_seconds,
                        'exponential_base': config.data_source.retry_config.exponential_base
                    }
                },
                'scanners': [
                    {
                        'symbol': s.symbol,
                        'mode': s.mode,
                        'timeframes': s.timeframes,
                        'strategy': s.strategy,
                        'enabled': s.enabled
                    }
                    for s in config.scanners
                ],
                'news_calendar_file': config.news_calendar_file
            }
            
            if config.quality_filter:
                config_dict['quality_filter'] = config.quality_filter
            
            if config.alerter:
                config_dict['alerter'] = {
                    'telegram_enabled': config.alerter.telegram_enabled,
                    'telegram_bot_token': config.alerter.telegram_bot_token,
                    'telegram_chat_id': config.alerter.telegram_chat_id,
                    'email_enabled': config.alerter.email_enabled,
                    'smtp_config': config.alerter.smtp_config
                }
            
            if config.health_monitor:
                config_dict['health_monitor'] = {
                    'max_consecutive_failures': config.health_monitor.max_consecutive_failures,
                    'heartbeat_interval_seconds': config.health_monitor.heartbeat_interval_seconds,
                    'data_quality_check_enabled': config.health_monitor.data_quality_check_enabled
                }
            
            # Write to file
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            self.last_modified = datetime.fromtimestamp(self.config_path.stat().st_mtime)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
