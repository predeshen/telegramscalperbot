"""
Data Validation and Error Handling
Centralized validation for market data and signals
"""
import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Optional
import pandas as pd
import math

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates market data and handles errors"""
    
    def __init__(self, max_consecutive_errors: int = 10):
        """
        Initialize data validator
        
        Args:
            max_consecutive_errors: Maximum consecutive errors before alerting admin
        """
        self.max_consecutive_errors = max_consecutive_errors
        self.consecutive_errors = 0
        self.last_error_time = None
    
    def validate_market_data(self, data: pd.DataFrame, asset: str) -> Tuple[bool, List[str]]:
        """
        Validate market data and return (valid, error_messages)
        
        Args:
            data: DataFrame with market data and indicators
            asset: Asset symbol for logging
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        if data.empty:
            errors.append("DataFrame is empty")
            self._record_error()
            return False, errors
        
        last = data.iloc[-1]
        
        # Check for required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                errors.append(f"Missing required column: {col}")
        
        if errors:
            self._record_error()
            return False, errors
        
        # Check for NaN values in indicators
        indicator_columns = ['rsi', 'adx', 'ema_9', 'ema_21', 'ema_50', 'atr', 'vwap', 'volume_ma']
        for col in indicator_columns:
            if col in last.index:
                value = last[col]
                if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
                    errors.append(f"NaN value in {col}")
                elif value <= 0 and col != 'rsi':  # RSI can be any value
                    errors.append(f"Invalid {col} value: {value}")
        
        # Check for stale data (>5 minutes old)
        if 'timestamp' in last.index:
            try:
                data_age = datetime.now() - last['timestamp']
                if data_age > timedelta(minutes=5):
                    errors.append(f"Stale data: {data_age.seconds // 60} minutes old")
            except Exception as e:
                logger.debug(f"Could not check data age: {e}")
        
        # Check price data validity
        if last['close'] <= 0 or last['high'] <= 0 or last['low'] <= 0:
            errors.append(f"Invalid price data: close={last['close']}, high={last['high']}, low={last['low']}")
        
        # Check volume
        if last['volume'] < 0:
            errors.append(f"Invalid volume: {last['volume']}")
        
        if errors:
            self._record_error()
            logger.warning(f"Market data validation failed for {asset}: {', '.join(errors)}")
            return False, errors
        
        # Reset error counter on success
        self.consecutive_errors = 0
        return True, []
    
    def _record_error(self):
        """Record a validation error and check if admin alert needed"""
        self.consecutive_errors += 1
        self.last_error_time = datetime.now()
        
        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.error(f"⚠️ ALERT: {self.consecutive_errors} consecutive data validation errors!")
            logger.error(f"Last error at: {self.last_error_time}")
            # In production, this would trigger an admin alert (email, SMS, etc.)
    
    def safe_evaluate_signal(self, signal_func, *args, **kwargs) -> Optional[any]:
        """
        Safely evaluate signal with error handling
        
        Args:
            signal_func: Function to call for signal evaluation
            *args: Positional arguments for signal_func
            **kwargs: Keyword arguments for signal_func
            
        Returns:
            Result from signal_func or None if error
        """
        try:
            result = signal_func(*args, **kwargs)
            return result
        except KeyError as e:
            logger.error(f"Missing indicator in signal evaluation: {e}")
            self._record_error()
            return None
        except ValueError as e:
            logger.error(f"Invalid value in signal evaluation: {e}")
            self._record_error()
            return None
        except Exception as e:
            logger.error(f"Unexpected error in signal evaluation: {e}", exc_info=True)
            self._record_error()
            return None
    
    def validate_configuration(self, config: dict) -> Tuple[bool, List[str]]:
        """
        Validate configuration on startup
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        warnings = []
        
        # Check for required sections
        if 'signal_rules' not in config:
            errors.append("Missing 'signal_rules' section in configuration")
        
        # Check asset_specific configuration
        if 'asset_specific' in config:
            for asset, asset_config in config['asset_specific'].items():
                # Check required fields
                if 'adx_threshold' not in asset_config:
                    warnings.append(f"Missing 'adx_threshold' for {asset}, using default")
                
                if 'volume_thresholds' not in asset_config:
                    warnings.append(f"Missing 'volume_thresholds' for {asset}, using defaults")
                
                # Validate threshold values
                if 'min_confluence_factors' in asset_config:
                    if asset_config['min_confluence_factors'] < 1 or asset_config['min_confluence_factors'] > 7:
                        errors.append(f"Invalid min_confluence_factors for {asset}: {asset_config['min_confluence_factors']} (must be 1-7)")
                
                if 'min_confidence_score' in asset_config:
                    if asset_config['min_confidence_score'] < 1 or asset_config['min_confidence_score'] > 5:
                        errors.append(f"Invalid min_confidence_score for {asset}: {asset_config['min_confidence_score']} (must be 1-5)")
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Config warning: {warning}")
        
        if errors:
            logger.error(f"Configuration validation failed: {', '.join(errors)}")
            return False, errors
        
        logger.info("Configuration validation passed")
        return True, []
    
    def get_error_stats(self) -> dict:
        """
        Get error statistics
        
        Returns:
            Dictionary with error stats
        """
        return {
            'consecutive_errors': self.consecutive_errors,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'needs_admin_alert': self.consecutive_errors >= self.max_consecutive_errors
        }
