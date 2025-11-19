"""
Trend Alignment Strategy
Detects signals aligned with the primary trend using EMA cascade.
"""
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class TrendAlignment:
    """Trend Alignment strategy implementation"""
    
    def __init__(self, config: dict = None):
        """
        Initialize Trend Alignment strategy.
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.volume_threshold = self.config.get('volume_threshold', 1.3)
        self.min_adx = self.config.get('min_adx', 20)
    
    def detect_signal(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str
    ) -> Optional[any]:
        """
        Detect trend alignment signals.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if len(data) < 2:
                logger.debug("Insufficient data for trend alignment")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['ema_9', 'ema_21', 'ema_50', 'ema_100', 'ema_200', 'close', 'volume', 'volume_ma', 'atr', 'adx']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug("Missing required indicators for trend alignment")
                return None
            
            # Check ADX for trend strength
            if last['adx'] < self.min_adx:
                logger.debug(f"ADX too low: {last['adx']:.1f} (need >= {self.min_adx})")
                return None
            
            # Check EMA cascade for bullish trend
            bullish_trend = (last['ema_9'] > last['ema_21'] > last['ema_50'] > last['ema_100'] > last['ema_200'])
            
            # Check EMA cascade for bearish trend
            bearish_trend = (last['ema_9'] < last['ema_21'] < last['ema_50'] < last['ema_100'] < last['ema_200'])
            
            if not (bullish_trend or bearish_trend):
                logger.debug("No clear trend alignment")
                return None
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < self.volume_threshold:
                logger.debug(f"Volume too low: {volume_ratio:.2f}x")
                return None
            
            # Determine signal type
            signal_type = "LONG" if bullish_trend else "SHORT"
            entry = last['close']
            stop_loss = entry - (last['atr'] * 1.5) if bullish_trend else entry + (last['atr'] * 1.5)
            take_profit = entry + (last['atr'] * 2.5) if bullish_trend else entry - (last['atr'] * 2.5)
            
            # Calculate risk/reward
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            risk_reward = reward / risk if risk > 0 else 0
            
            if risk_reward < 1.2:
                logger.debug(f"Risk/reward too low: {risk_reward:.2f}")
                return None
            
            logger.info(f"Trend Alignment signal: {signal_type}")
            
            # Create signal object
            from src.signal_detector import Signal
            from src.symbol_context import SymbolContext
            
            try:
                symbol_context = SymbolContext.from_symbol(symbol if symbol in ['BTC', 'XAUUSD', 'US30', 'US100'] else 'BTC')
            except:
                symbol_context = None
            
            signal = Signal(
                timestamp=last['timestamp'],
                signal_type=signal_type,
                timeframe=timeframe,
                symbol=symbol,
                symbol_context=symbol_context,
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                atr=last['atr'],
                risk_reward=risk_reward,
                market_bias="bullish" if bullish_trend else "bearish",
                confidence=4,
                indicators={
                    'ema_9': last['ema_9'],
                    'ema_21': last['ema_21'],
                    'ema_50': last['ema_50'],
                    'ema_100': last['ema_100'],
                    'ema_200': last['ema_200'],
                    'adx': last['adx'],
                    'volume': last['volume'],
                    'volume_ma': last['volume_ma']
                },
                reasoning=f"EMA cascade aligned, ADX {last['adx']:.1f}, Volume {volume_ratio:.2f}x",
                strategy="Trend Alignment"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in Trend Alignment strategy: {e}", exc_info=True)
            return None
