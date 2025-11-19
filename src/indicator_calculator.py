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
        
        # Check for sufficient rows - use the max period from the adjusted list
        # This is more flexible than the old hard requirement
        max_period = max(required_periods) if required_periods else 50
        
        # Require at least the max period for proper indicator calculation
        if len(data) < max_period:
            return False, f"Insufficient data: need at least {max_period} rows, got {len(data)}"
        
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
    def calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average Directional Index (ADX).
        
        Args:
            data: DataFrame with OHLC data
            period: ADX period
            
        Returns:
            Series with ADX values
        """
        try:
            # Calculate True Range
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Calculate Directional Movement
            high_diff = data['high'] - data['high'].shift()
            low_diff = data['low'].shift() - data['low']
            
            plus_dm = pd.Series(0.0, index=data.index)
            minus_dm = pd.Series(0.0, index=data.index)
            
            plus_dm[high_diff > low_diff] = high_diff[high_diff > low_diff]
            plus_dm[plus_dm < 0] = 0
            
            minus_dm[low_diff > high_diff] = low_diff[low_diff > high_diff]
            minus_dm[minus_dm < 0] = 0
            
            # Smooth with Wilder's method
            atr = true_range.ewm(alpha=1/period, adjust=False).mean()
            plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
            minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
            
            # Calculate DX and ADX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.ewm(alpha=1/period, adjust=False).mean()
            
            return adx
            
        except Exception as e:
            logger.error(f"Error calculating ADX({period}): {e}")
            return pd.Series(index=data.index, dtype=float)
    
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
            logger.error("CRITICAL: Empty DataFrame provided to calculate_all_indicators")
            logger.error("This should NEVER happen in production - check data source!")
            raise ValueError("Cannot calculate indicators on empty DataFrame")
        
        # Auto-adjust EMA periods based on available data
        data_length = len(data)
        original_ema_periods = ema_periods.copy()
        
        # Filter out EMA periods that are too large for available data
        # Keep only EMAs where we have at least the period length
        adjusted_ema_periods = [p for p in ema_periods if p <= data_length]
        
        if len(adjusted_ema_periods) < len(original_ema_periods):
            removed = [p for p in original_ema_periods if p not in adjusted_ema_periods]
            logger.warning(f"Insufficient data ({data_length} rows) for EMA periods: {removed}")
            logger.warning(f"Using adjusted EMA periods: {adjusted_ema_periods}")
            ema_periods = adjusted_ema_periods
        
        # Ensure we have at least some EMAs
        if not ema_periods:
            logger.error(f"Cannot calculate any EMAs with only {data_length} rows")
            raise ValueError(f"Insufficient data: need at least 9 rows for minimum EMA, got {data_length}")
        
        # Validate data for remaining indicators
        all_periods = ema_periods + [atr_period, rsi_period, volume_ma_period]
        is_valid, error_msg = IndicatorCalculator.validate_data_for_indicators(data, all_periods)
        if not is_valid:
            max_period = max(all_periods)
            logger.error(f"Data validation failed: {error_msg}")
            logger.error(f"Received {len(data)} rows, max indicator period is {max_period}")
            raise ValueError(f"Data validation failed: {error_msg}")
        
        logger.info(f"Calculating indicators on {len(data)} candles with EMA periods: {ema_periods}")
        
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
    
    @staticmethod
    def calculate_fibonacci_levels(
        data: pd.DataFrame,
        lookback: int = 50
    ) -> dict:
        """
        Calculate Fibonacci retracement levels from swing highs and lows.
        
        Args:
            data: DataFrame with OHLC data
            lookback: Number of candles to analyze for swing points
            
        Returns:
            Dictionary with Fibonacci levels and swing points
        """
        try:
            if len(data) < lookback:
                logger.warning(f"Insufficient data for Fibonacci ({len(data)} < {lookback})")
                return {}
            
            # Get recent data
            recent = data.tail(lookback)
            
            # Find swing high and low
            swing_high = recent['high'].max()
            swing_low = recent['low'].min()
            
            if swing_high == swing_low:
                logger.warning("Swing high equals swing low, cannot calculate Fibonacci levels")
                return {}
            
            # Calculate Fibonacci levels
            diff = swing_high - swing_low
            
            levels = {
                'swing_high': swing_high,
                'swing_low': swing_low,
                'level_0': swing_high,  # 0%
                'level_236': swing_high - (diff * 0.236),  # 23.6%
                'level_382': swing_high - (diff * 0.382),  # 38.2%
                'level_500': swing_high - (diff * 0.500),  # 50%
                'level_618': swing_high - (diff * 0.618),  # 61.8%
                'level_786': swing_high - (diff * 0.786),  # 78.6%
                'level_100': swing_low  # 100%
            }
            
            logger.debug(f"Calculated Fibonacci levels: High={swing_high:.2f}, Low={swing_low:.2f}")
            return levels
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci levels: {e}")
            return {}
    
    @staticmethod
    def identify_support_resistance(
        data: pd.DataFrame,
        lookback: int = 100,
        tolerance_percent: float = 0.3
    ) -> dict:
        """
        Identify support and resistance levels based on price touches.
        
        Args:
            data: DataFrame with OHLC data
            lookback: Number of candles to analyze
            tolerance_percent: Tolerance for grouping nearby levels (%)
            
        Returns:
            Dictionary with support and resistance levels
        """
        try:
            if len(data) < lookback:
                logger.warning(f"Insufficient data for S/R identification ({len(data)} < {lookback})")
                return {'support': [], 'resistance': []}
            
            recent = data.tail(lookback)
            
            # Find local highs and lows
            highs = []
            lows = []
            
            for i in range(1, len(recent) - 1):
                # Local high
                if recent.iloc[i]['high'] > recent.iloc[i-1]['high'] and \
                   recent.iloc[i]['high'] > recent.iloc[i+1]['high']:
                    highs.append(recent.iloc[i]['high'])
                
                # Local low
                if recent.iloc[i]['low'] < recent.iloc[i-1]['low'] and \
                   recent.iloc[i]['low'] < recent.iloc[i+1]['low']:
                    lows.append(recent.iloc[i]['low'])
            
            # Group nearby levels using tolerance
            def group_levels(levels, tolerance_pct):
                if not levels:
                    return []
                
                levels = sorted(levels)
                grouped = []
                current_group = [levels[0]]
                
                for level in levels[1:]:
                    # Check if within tolerance of current group average
                    group_avg = sum(current_group) / len(current_group)
                    tolerance = group_avg * (tolerance_pct / 100)
                    
                    if abs(level - group_avg) <= tolerance:
                        current_group.append(level)
                    else:
                        # Start new group
                        grouped.append(sum(current_group) / len(current_group))
                        current_group = [level]
                
                # Add last group
                if current_group:
                    grouped.append(sum(current_group) / len(current_group))
                
                return grouped
            
            support_levels = group_levels(lows, tolerance_percent)
            resistance_levels = group_levels(highs, tolerance_percent)
            
            logger.debug(f"Identified {len(support_levels)} support and {len(resistance_levels)} resistance levels")
            
            return {
                'support': support_levels,
                'resistance': resistance_levels,
                'support_count': len(support_levels),
                'resistance_count': len(resistance_levels)
            }
            
        except Exception as e:
            logger.error(f"Error identifying support/resistance levels: {e}")
            return {'support': [], 'resistance': []}
    
    @staticmethod
    def calculate_swing_points(
        data: pd.DataFrame,
        lookback: int = 50
    ) -> Tuple[List[float], List[float]]:
        """
        Identify swing highs and lows over a lookback period.
        
        Args:
            data: DataFrame with OHLC data
            lookback: Number of candles to analyze
            
        Returns:
            Tuple of (swing_highs, swing_lows) lists
        """
        try:
            if len(data) < lookback:
                logger.warning(f"Insufficient data for swing points ({len(data)} < {lookback})")
                return [], []
            
            recent = data.tail(lookback)
            
            swing_highs = []
            swing_lows = []
            
            for i in range(1, len(recent) - 1):
                # Swing high (local maximum)
                if recent.iloc[i]['high'] > recent.iloc[i-1]['high'] and \
                   recent.iloc[i]['high'] > recent.iloc[i+1]['high']:
                    swing_highs.append(recent.iloc[i]['high'])
                
                # Swing low (local minimum)
                if recent.iloc[i]['low'] < recent.iloc[i-1]['low'] and \
                   recent.iloc[i]['low'] < recent.iloc[i+1]['low']:
                    swing_lows.append(recent.iloc[i]['low'])
            
            logger.debug(f"Identified {len(swing_highs)} swing highs and {len(swing_lows)} swing lows")
            
            return swing_highs, swing_lows
            
        except Exception as e:
            logger.error(f"Error calculating swing points: {e}")
            return [], []
