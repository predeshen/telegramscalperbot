"""
Price Validator
Detects anomalous price data and ensures data quality
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional
import pandas as pd


logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Validation thresholds"""
    max_normal_price_change_percent: float = 0.5
    max_anomaly_price_change_percent: float = 5.0
    max_timestamp_age_hours: int = 1
    min_volume: float = 0.0


@dataclass
class ValidationResult:
    """Result of price validation"""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    percent_change: Optional[float] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


class PriceValidator:
    """
    Validates price data for anomalies and quality issues
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize price validator
        
        Args:
            config: ValidationConfig with thresholds
        """
        self.config = config or ValidationConfig()
        logger.info(f"Initialized PriceValidator with thresholds: "
                   f"normal={self.config.max_normal_price_change_percent}%, "
                   f"anomaly={self.config.max_anomaly_price_change_percent}%")
    
    def validate_candle(self, current: pd.Series, previous: Optional[pd.Series] = None) -> ValidationResult:
        """
        Validate candle against previous candle
        
        Checks:
        - Price change within 0.5% (normal) or flags if >5% (anomaly)
        - Volume > 0
        - Timestamp within acceptable range (not future, not >1hr old)
        - OHLC relationships (high >= low, etc.)
        
        Args:
            current: Current candle as pandas Series
            previous: Previous candle as pandas Series (optional)
            
        Returns:
            ValidationResult with status and any warnings/errors
        """
        warnings = []
        errors = []
        percent_change = None
        
        # Validate OHLC relationships
        if not self._validate_ohlc_relationships(current):
            errors.append(f"Invalid OHLC relationships: H={current['high']}, L={current['low']}, O={current['open']}, C={current['close']}")
        
        # Validate volume
        if not self.check_volume(current['volume']):
            errors.append(f"Invalid volume: {current['volume']}")
        
        # Validate timestamp
        if not self.check_timestamp(current['timestamp']):
            errors.append(f"Invalid timestamp: {current['timestamp']}")
        
        # Validate price change if previous candle provided
        if previous is not None:
            is_valid_change, pct_change = self.check_price_change(
                current['close'],
                previous['close']
            )
            percent_change = pct_change
            
            if not is_valid_change:
                if abs(pct_change) > self.config.max_anomaly_price_change_percent:
                    errors.append(f"Extreme price change: {pct_change:.2f}% (threshold: {self.config.max_anomaly_price_change_percent}%)")
                else:
                    warnings.append(f"Large price change: {pct_change:.2f}% (normal threshold: {self.config.max_normal_price_change_percent}%)")
        
        # Determine overall validity
        is_valid = len(errors) == 0
        
        if errors:
            logger.error(f"Validation failed for candle at {current['timestamp']}: {errors}")
        elif warnings:
            logger.warning(f"Validation warnings for candle at {current['timestamp']}: {warnings}")
        
        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            percent_change=percent_change
        )
    
    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate entire DataFrame of candles
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (all_valid, list of ValidationResults)
        """
        if df.empty:
            logger.error("Cannot validate empty DataFrame")
            return False, []
        
        results = []
        all_valid = True
        
        for i in range(len(df)):
            current = df.iloc[i]
            previous = df.iloc[i-1] if i > 0 else None
            
            result = self.validate_candle(current, previous)
            results.append(result)
            
            if not result.is_valid:
                all_valid = False
        
        # Summary
        invalid_count = sum(1 for r in results if not r.is_valid)
        warning_count = sum(1 for r in results if r.warnings)
        
        if invalid_count > 0:
            logger.warning(f"Validation summary: {invalid_count}/{len(results)} candles invalid, {warning_count} with warnings")
        else:
            logger.info(f"Validation summary: All {len(results)} candles valid, {warning_count} with warnings")
        
        return all_valid, results
    
    def check_price_change(self, current_price: float, previous_price: float) -> Tuple[bool, float]:
        """
        Check if price change is within acceptable range
        
        Args:
            current_price: Current price
            previous_price: Previous price
            
        Returns:
            Tuple of (is_valid, percent_change)
        """
        if previous_price <= 0:
            logger.error(f"Invalid previous price: {previous_price}")
            return False, 0.0
        
        percent_change = ((current_price - previous_price) / previous_price) * 100
        
        # Check against normal threshold
        is_normal = abs(percent_change) <= self.config.max_normal_price_change_percent
        
        # Check against anomaly threshold (hard limit)
        is_not_anomaly = abs(percent_change) <= self.config.max_anomaly_price_change_percent
        
        # Valid if within anomaly threshold (may have warning if exceeds normal)
        is_valid = is_not_anomaly
        
        return is_valid, percent_change
    
    def check_volume(self, volume: float) -> bool:
        """
        Validate volume is positive
        
        Args:
            volume: Volume value
            
        Returns:
            True if valid
        """
        return volume >= self.config.min_volume
    
    def check_timestamp(self, timestamp: datetime) -> bool:
        """
        Validate timestamp is not in future or too old
        
        Args:
            timestamp: Timestamp to validate
            
        Returns:
            True if valid
        """
        # Ensure timezone aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        
        # Check if in future
        if timestamp > now:
            logger.error(f"Timestamp is in future: {timestamp} > {now}")
            return False
        
        # Check if too old
        max_age = timedelta(hours=self.config.max_timestamp_age_hours)
        age = now - timestamp
        
        if age > max_age:
            logger.warning(f"Timestamp is old: {timestamp} (age: {age})")
            # Don't fail for old timestamps, just warn
            # This is expected for historical data
        
        return True
    
    def _validate_ohlc_relationships(self, candle: pd.Series) -> bool:
        """
        Validate OHLC relationships
        
        Args:
            candle: Candle data as pandas Series
            
        Returns:
            True if relationships are valid
        """
        high = candle['high']
        low = candle['low']
        open_price = candle['open']
        close = candle['close']
        
        # High must be >= all other prices
        if high < low or high < open_price or high < close:
            return False
        
        # Low must be <= all other prices
        if low > high or low > open_price or low > close:
            return False
        
        # All prices must be positive
        if high <= 0 or low <= 0 or open_price <= 0 or close <= 0:
            return False
        
        return True
    
    def get_validation_summary(self, results: List[ValidationResult]) -> dict:
        """
        Get summary statistics from validation results
        
        Args:
            results: List of ValidationResults
            
        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'warnings': 0,
                'error_count': 0
            }
        
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = sum(1 for r in results if not r.is_valid)
        warning_count = sum(1 for r in results if r.warnings)
        total_errors = sum(len(r.errors) for r in results)
        
        # Calculate price change statistics
        price_changes = [r.percent_change for r in results if r.percent_change is not None]
        
        summary = {
            'total': len(results),
            'valid': valid_count,
            'invalid': invalid_count,
            'warnings': warning_count,
            'error_count': total_errors,
            'price_changes': {
                'count': len(price_changes),
                'max': max(price_changes) if price_changes else None,
                'min': min(price_changes) if price_changes else None,
                'avg': sum(price_changes) / len(price_changes) if price_changes else None
            }
        }
        
        return summary
