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
    def calculate_all_indicators(
        data: pd.DataFrame,
        ema_periods: list = [9, 21, 50, 100, 200],
        atr_period: int = 14,
        rsi_period: int = 6,
        volume_ma_period: int = 20
    ) -> pd.DataFrame:
        """
        Calculate all indicators and append to DataFrame.
        
        Args:
            data: DataFrame with OHLCV data
            ema_periods: List of EMA periods to calculate
            atr_period: ATR period
            rsi_period: RSI period
            volume_ma_period: Volume MA period
            
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
            
            # Drop rows with NaN values in critical indicators
            # (first few rows will have NaN due to indicator warmup)
            result = result.dropna(subset=['ema_9', 'ema_21', 'vwap', 'atr', 'rsi'])
            
            logger.debug(f"Calculated all indicators, {len(result)} valid rows")
            return result
            
        except Exception as e:
            logger.error(f"Error in calculate_all_indicators: {e}")
            return data
