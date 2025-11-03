"""Technical indicator calculations for trading signals."""
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
import logging


logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    Calculate technical indicators for trading signal detection.
    
    Implements EMA, VWAP, ATR, RSI, and volume moving average calculations.
    """
    
    @staticmethod
    def validate_data_for_indicators(data: pd.DataFrame, required_periods: List[int]) -> Tuple[bool, str]:
        """
        Validate that DataFrame has sufficient data for indicator calculations.
        
        Args:
            data: DataFrame to validate
            required_periods: List of periods that will be used for indicators
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if data.empty:
            return False, "DataFrame is empty"
        
        # Check for required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Check for sufficient rows
        max_period = max(required_periods) if required_periods else 200
        if len(data) < max_period:
            return False, f"Insufficient data: need {max_period} rows, got {len(data)}"
        
        # Check for NaN values in OHLCV columns
        ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in ohlcv_cols:
            if data[col].isna().any():
                nan_count = data[col].isna().sum()
                return False, f"Column '{col}' contains {nan_count} NaN values"
        
        return True, ""
    
    @staticmethod
    def calculate_ema(data: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """
        Calculate Exponential Moving Average with validation.
        
        Args:
            data: DataFrame with price data
            period: EMA period
            column: Column name to calculate EMA on
            
        Returns:
            Series with EMA values
            
        Raises:
            ValueError: If data has fewer rows than period or is empty
            KeyError: If column doesn't exist
        """
        # Validate input
        if data.empty:
            logger.error(f"Cannot calculate EMA({period}): DataFrame is empty")
            raise ValueError("Cannot calculate EMA on empty DataFrame")
        
        if column not in data.columns:
            logger.error(f"Cannot calculate EMA({period}): Column '{column}' not found")
            raise KeyError(f"Column '{column}' not found in DataFrame")
        
        if len(data) < period:
            logger.warning(f"EMA({period}): Insufficient data (need {period} rows, got {len(data)})")
            # Don't raise error, but log warning - EMA can still be calculated with fewer rows
        
        try:
            ema = data[column].ewm(span=period, adjust=False).mean()
            
            # Validate output
            if ema.isna().all():
                logger.error(f"EMA({period}) calculation produced all NaN values")
                raise ValueError(f"EMA calculation produced all NaN values")
            
            return ema
            
        except Exception as e:
            logger.error(f"Error calculating EMA({period}) on column '{column}': {e}")
            raise
    
    @staticmethod
    def calculate_vwap(data: pd.DataFrame, reset_daily: bool = True) -> pd.Series:
        """
        Calculate Volume Weighted Average Price with validation.
        
        Args:
            data: DataFrame with OHLCV data
            reset_daily: If True, reset VWAP calculation at start of each day
            
        Returns:
            Series with VWAP values
            
        Raises:
            ValueError: If data is empty
            KeyError: If required columns are missing
        """
        # Validate input
        if data.empty:
            logger.error("Cannot calculate VWAP: DataFrame is empty")
            raise ValueError("Cannot calculate VWAP on empty DataFrame")
        
        required_cols = ['high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            logger.error(f"Cannot calculate VWAP: Missing columns {missing_cols}")
            raise KeyError(f"Missing required columns for VWAP: {', '.join(missing_cols)}")
        
        try:
            # Typical price
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            
            if reset_daily and 'timestamp' in data.columns:
                # Reset VWAP daily
                data_copy = data.copy()
                data_copy['date'] = pd.to_datetime(data_copy['timestamp']).dt.date
                
                vwap_values = []
                for date, group in data_copy.groupby('date'):
                    tp = (group['high'] + group['low'] + group['close']) / 3
                    cumulative_tp_volume = (tp * group['volume']).cumsum()
                    cumulative_volume = group['volume'].cumsum()
                    vwap = cumulative_tp_volume / cumulative_volume
                    vwap_values.extend(vwap.values)
                
                result = pd.Series(vwap_values, index=data.index)
            else:
                # Simple VWAP without daily reset
                cumulative_tp_volume = (typical_price * data['volume']).cumsum()
                cumulative_volume = data['volume'].cumsum()
                result = cumulative_tp_volume / cumulative_volume
            
            # Validate output
            if result.isna().all():
                logger.error("VWAP calculation produced all NaN values")
                raise ValueError("VWAP calculation produced all NaN values")
            
            return result
                
        except Exception as e:
            logger.error(f"Error calculating VWAP: {e}")
            raise
    
    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range using Wilder's smoothing with validation.
        
        Args:
            data: DataFrame with OHLC data
            period: ATR period
            
        Returns:
            Series with ATR values
            
        Raises:
            ValueError: If data is empty or insufficient
            KeyError: If required columns are missing
        """
        # Validate input
        if data.empty:
            logger.error(f"Cannot calculate ATR({period}): DataFrame is empty")
            raise ValueError("Cannot calculate ATR on empty DataFrame")
        
        required_cols = ['high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            logger.error(f"Cannot calculate ATR({period}): Missing columns {missing_cols}")
            raise KeyError(f"Missing required columns for ATR: {', '.join(missing_cols)}")
        
        if len(data) < period:
            logger.warning(f"ATR({period}): Insufficient data (need {period} rows, got {len(data)})")
        
        try:
            # Calculate True Range
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Wilder's smoothing (similar to EMA with alpha = 1/period)
            atr = true_range.ewm(alpha=1/period, adjust=False).mean()
            
            # Validate output
            if atr.isna().all():
                logger.error(f"ATR({period}) calculation produced all NaN values")
                raise ValueError(f"ATR calculation produced all NaN values")
            
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR({period}): {e}")
            raise
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Calculate Relative Strength Index using Wilder's smoothing with validation.
        
        Args:
            data: DataFrame with price data
            period: RSI period
            column: Column name to calculate RSI on
            
        Returns:
            Series with RSI values (0-100)
            
        Raises:
            ValueError: If data is empty or insufficient
            KeyError: If column doesn't exist
        """
        # Validate input
        if data.empty:
            logger.error(f"Cannot calculate RSI({period}): DataFrame is empty")
            raise ValueError("Cannot calculate RSI on empty DataFrame")
        
        if column not in data.columns:
            logger.error(f"Cannot calculate RSI({period}): Column '{column}' not found")
            raise KeyError(f"Column '{column}' not found in DataFrame")
        
        if len(data) < period + 1:  # Need period + 1 for diff()
            logger.warning(f"RSI({period}): Insufficient data (need {period + 1} rows, got {len(data)})")
        
        try:
            # Calculate price changes
            delta = data[column].diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Wilder's smoothing
            avg_gains = gains.ewm(alpha=1/period, adjust=False).mean()
            avg_losses = losses.ewm(alpha=1/period, adjust=False).mean()
            
            # Calculate RS and RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            # Validate output
            if rsi.isna().all():
                logger.error(f"RSI({period}) calculation produced all NaN values")
                raise ValueError(f"RSI calculation produced all NaN values")
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI({period}) on column '{column}': {e}")
            raise
    
    @staticmethod
    def calculate_volume_ma(data: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate simple moving average of volume with validation.
        
        Args:
            data: DataFrame with volume data
            period: Moving average period
            
        Returns:
            Series with volume MA values
            
        Raises:
            ValueError: If data is empty or insufficient
            KeyError: If volume column doesn't exist
        """
        # Validate input
        if data.empty:
            logger.error(f"Cannot calculate Volume MA({period}): DataFrame is empty")
            raise ValueError("Cannot calculate Volume MA on empty DataFrame")
        
        if 'volume' not in data.columns:
            logger.error(f"Cannot calculate Volume MA({period}): 'volume' column not found")
            raise KeyError("'volume' column not found in DataFrame")
        
        if len(data) < period:
            logger.warning(f"Volume MA({period}): Insufficient data (need {period} rows, got {len(data)})")
        
        try:
            volume_ma = data['volume'].rolling(window=period).mean()
            
            # Validate output
            if volume_ma.isna().all():
                logger.error(f"Volume MA({period}) calculation produced all NaN values")
                raise ValueError(f"Volume MA calculation produced all NaN values")
            
            return volume_ma
            
        except Exception as e:
            logger.error(f"Error calculating Volume MA({period}): {e}")
            raise
    
    @staticmethod
    def calculate_stochastic(data: pd.DataFrame, k_period: int = 14, 
                           d_period: int = 3, smooth_k: int = 3) -> tuple:
        """
        Calculate Stochastic Oscillator (%K and %D).
        
        Args:
            data: DataFrame with OHLC data
            k_period: Period for %K calculation
            d_period: Period for %D (signal line) calculation
            smooth_k: Smoothing period for %K
            
        Returns:
            Tuple of (stoch_k, stoch_d) Series
        """
        try:
            # Calculate raw %K
            lowest_low = data['low'].rolling(window=k_period).min()
            highest_high = data['high'].rolling(window=k_period).max()
            
            raw_k = 100 * (data['close'] - lowest_low) / (highest_high - lowest_low)
            
            # Smooth %K
            stoch_k = raw_k.rolling(window=smooth_k).mean()
            
            # Calculate %D (signal line)
            stoch_d = stoch_k.rolling(window=d_period).mean()
            
            return stoch_k, stoch_d
            
        except Exception as e:
            logger.error(f"Error calculating Stochastic({k_period},{d_period},{smooth_k}): {e}")
            return pd.Series(index=data.index, dtype=float), pd.Series(index=data.index, dtype=float)
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, fast_period: int = 12, 
                      slow_period: int = 26, signal_period: int = 9,
                      column: str = 'close') -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            data: DataFrame with price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            column: Column name to calculate MACD on
            
        Returns:
            Tuple of (macd, signal, histogram) Series
        """
        try:
            # Calculate fast and slow EMAs
            fast_ema = data[column].ewm(span=fast_period, adjust=False).mean()
            slow_ema = data[column].ewm(span=slow_period, adjust=False).mean()
            
            # MACD line
            macd = fast_ema - slow_ema
            
            # Signal line
            signal = macd.ewm(span=signal_period, adjust=False).mean()
            
            # Histogram
            histogram = macd - signal
            
            return macd, signal, histogram
            
        except Exception as e:
            logger.error(f"Error calculating MACD({fast_period},{slow_period},{signal_period}): {e}")
            empty = pd.Series(index=data.index, dtype=float)
            return empty, empty, empty
    
    @staticmethod
    def calculate_all_indicators(
        data: pd.DataFrame,
        ema_periods: list = [9, 21, 50, 100, 200],
        atr_period: int = 14,
        rsi_period: int = 14,
        volume_ma_period: int = 20,
        include_stochastic: bool = False,
        stoch_k_period: int = 14,
        stoch_d_period: int = 3,
        stoch_smooth: int = 3,
        include_macd: bool = False,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9
    ) -> pd.DataFrame:
        """
        Calculate all indicators and append to DataFrame with validation.
        
        Args:
            data: DataFrame with OHLCV data
            ema_periods: List of EMA periods to calculate
            atr_period: ATR period
            rsi_period: RSI period
            volume_ma_period: Volume MA period
            include_stochastic: Whether to calculate Stochastic
            stoch_k_period: Stochastic %K period
            stoch_d_period: Stochastic %D period
            stoch_smooth: Stochastic smoothing period
            include_macd: Whether to calculate MACD
            macd_fast: MACD fast period
            macd_slow: MACD slow period
            macd_signal: MACD signal period
            
        Returns:
            DataFrame with all indicator columns added
            
        Raises:
            ValueError: If data validation fails
        """
        if data.empty:
            logger.error("Empty DataFrame provided to calculate_all_indicators")
            raise ValueError("Cannot calculate indicators on empty DataFrame")
        
        # Validate data before calculations
        all_periods = ema_periods + [atr_period, rsi_period, volume_ma_period]
        is_valid, error_msg = IndicatorCalculator.validate_data_for_indicators(data, all_periods)
        if not is_valid:
            logger.error(f"Data validation failed: {error_msg}")
            raise ValueError(f"Data validation failed: {error_msg}")
        
        logger.info(f"Calculating indicators on {len(data)} candles")
        
        try:
            result = data.copy()
            
            # Calculate EMAs
            for period in ema_periods:
                try:
                    result[f'ema_{period}'] = IndicatorCalculator.calculate_ema(data, period)
                    logger.debug(f"Calculated EMA({period})")
                except Exception as e:
                    logger.error(f"Failed to calculate EMA({period}): {e}")
                    raise
            
            # Calculate VWAP
            try:
                result['vwap'] = IndicatorCalculator.calculate_vwap(data)
                logger.debug("Calculated VWAP")
            except Exception as e:
                logger.error(f"Failed to calculate VWAP: {e}")
                raise
            
            # Calculate ATR
            try:
                result['atr'] = IndicatorCalculator.calculate_atr(data, atr_period)
                logger.debug(f"Calculated ATR({atr_period})")
            except Exception as e:
                logger.error(f"Failed to calculate ATR: {e}")
                raise
            
            # Calculate RSI
            try:
                result['rsi'] = IndicatorCalculator.calculate_rsi(data, rsi_period)
                logger.debug(f"Calculated RSI({rsi_period})")
            except Exception as e:
                logger.error(f"Failed to calculate RSI: {e}")
                raise
            
            # Calculate Volume MA
            try:
                result['volume_ma'] = IndicatorCalculator.calculate_volume_ma(data, volume_ma_period)
                logger.debug(f"Calculated Volume MA({volume_ma_period})")
            except Exception as e:
                logger.error(f"Failed to calculate Volume MA: {e}")
                raise
            
            # Calculate Stochastic (optional)
            if include_stochastic:
                try:
                    stoch_k, stoch_d = IndicatorCalculator.calculate_stochastic(
                        data, stoch_k_period, stoch_d_period, stoch_smooth
                    )
                    result['stoch_k'] = stoch_k
                    result['stoch_d'] = stoch_d
                    logger.debug(f"Calculated Stochastic({stoch_k_period},{stoch_d_period},{stoch_smooth})")
                except Exception as e:
                    logger.warning(f"Failed to calculate Stochastic (optional): {e}")
            
            # Calculate MACD (optional)
            if include_macd:
                try:
                    macd, signal, histogram = IndicatorCalculator.calculate_macd(
                        data, macd_fast, macd_slow, macd_signal
                    )
                    result['macd'] = macd
                    result['macd_signal'] = signal
                    result['macd_histogram'] = histogram
                    logger.debug(f"Calculated MACD({macd_fast},{macd_slow},{macd_signal})")
                except Exception as e:
                    logger.warning(f"Failed to calculate MACD (optional): {e}")
            
            # Drop rows with NaN values in critical indicators
            # (first few rows will have NaN due to indicator warmup)
            critical_indicators = ['ema_9', 'ema_21', 'vwap', 'atr', 'rsi']
            before_count = len(result)
            result = result.dropna(subset=critical_indicators)
            after_count = len(result)
            
            if after_count == 0:
                logger.error("All rows dropped after removing NaN values in critical indicators")
                raise ValueError("All rows contain NaN values in critical indicators")
            
            dropped_count = before_count - after_count
            if dropped_count > 0:
                logger.info(f"Dropped {dropped_count} rows with NaN values (indicator warmup period)")
            
            logger.info(f"Successfully calculated all indicators, {len(result)} valid rows")
            return result
            
        except Exception as e:
            logger.error(f"Error in calculate_all_indicators: {e}", exc_info=True)
            raise
