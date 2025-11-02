"""Technical indicator calculations for trading signals."""
import pandas as pd
import numpy as np
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    Calculate technical indicators for trading signal detection.
    
    Implements EMA, VWAP, ATR, RSI, and volume moving average calculations.
    """
    
    @staticmethod
    def calculate_ema(data: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            data: DataFrame with price data
            period: EMA period
            column: Column name to calculate EMA on
            
        Returns:
            Series with EMA values
        """
        try:
            ema = data[column].ewm(span=period, adjust=False).mean()
            return ema
        except Exception as e:
            logger.error(f"Error calculating EMA({period}): {e}")
            return pd.Series(index=data.index, dtype=float)
    
    @staticmethod
    def calculate_vwap(data: pd.DataFrame, reset_daily: bool = True) -> pd.Series:
        """
        Calculate Volume Weighted Average Price.
        
        Args:
            data: DataFrame with OHLCV data
            reset_daily: If True, reset VWAP calculation at start of each day
            
        Returns:
            Series with VWAP values
        """
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
                
                return pd.Series(vwap_values, index=data.index)
            else:
                # Simple VWAP without daily reset
                cumulative_tp_volume = (typical_price * data['volume']).cumsum()
                cumulative_volume = data['volume'].cumsum()
                vwap = cumulative_tp_volume / cumulative_volume
                return vwap
                
        except Exception as e:
            logger.error(f"Error calculating VWAP: {e}")
            return pd.Series(index=data.index, dtype=float)
    
    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range using Wilder's smoothing.
        
        Args:
            data: DataFrame with OHLC data
            period: ATR period
            
        Returns:
            Series with ATR values
        """
        try:
            # Calculate True Range
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Wilder's smoothing (similar to EMA with alpha = 1/period)
            atr = true_range.ewm(alpha=1/period, adjust=False).mean()
            
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR({period}): {e}")
            return pd.Series(index=data.index, dtype=float)
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Calculate Relative Strength Index using Wilder's smoothing.
        
        Args:
            data: DataFrame with price data
            period: RSI period
            column: Column name to calculate RSI on
            
        Returns:
            Series with RSI values (0-100)
        """
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
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI({period}): {e}")
            return pd.Series(index=data.index, dtype=float)
    
    @staticmethod
    def calculate_volume_ma(data: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate simple moving average of volume.
        
        Args:
            data: DataFrame with volume data
            period: Moving average period
            
        Returns:
            Series with volume MA values
        """
        try:
            volume_ma = data['volume'].rolling(window=period).mean()
            return volume_ma
        except Exception as e:
            logger.error(f"Error calculating Volume MA({period}): {e}")
            return pd.Series(index=data.index, dtype=float)
    
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
        rsi_period: int = 6,
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
        Calculate all indicators and append to DataFrame.
        
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
        """
        if data.empty:
            logger.warning("Empty DataFrame provided to calculate_all_indicators")
            return data
        
        try:
            result = data.copy()
            
            # Calculate EMAs
            for period in ema_periods:
                result[f'ema_{period}'] = IndicatorCalculator.calculate_ema(data, period)
            
            # Calculate VWAP
            result['vwap'] = IndicatorCalculator.calculate_vwap(data)
            
            # Calculate ATR
            result['atr'] = IndicatorCalculator.calculate_atr(data, atr_period)
            
            # Calculate RSI
            result['rsi'] = IndicatorCalculator.calculate_rsi(data, rsi_period)
            
            # Calculate Volume MA
            result['volume_ma'] = IndicatorCalculator.calculate_volume_ma(data, volume_ma_period)
            
            # Calculate Stochastic (optional)
            if include_stochastic:
                stoch_k, stoch_d = IndicatorCalculator.calculate_stochastic(
                    data, stoch_k_period, stoch_d_period, stoch_smooth
                )
                result['stoch_k'] = stoch_k
                result['stoch_d'] = stoch_d
            
            # Calculate MACD (optional)
            if include_macd:
                macd, signal, histogram = IndicatorCalculator.calculate_macd(
                    data, macd_fast, macd_slow, macd_signal
                )
                result['macd'] = macd
                result['macd_signal'] = signal
                result['macd_histogram'] = histogram
            
            # Drop rows with NaN values in critical indicators
            # (first few rows will have NaN due to indicator warmup)
            result = result.dropna(subset=['ema_9', 'ema_21', 'vwap', 'atr', 'rsi'])
            
            logger.debug(f"Calculated all indicators, {len(result)} valid rows")
            return result
            
        except Exception as e:
            logger.error(f"Error in calculate_all_indicators: {e}")
            return data
