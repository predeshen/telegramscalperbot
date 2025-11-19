"""
Momentum Shift Strategy
Detects shifts in market momentum using RSI and volume analysis.
"""
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class MomentumShift:
    """Momentum Shift strategy implementation"""
    
    def __init__(self, config: dict = None):
        """
        Initialize Momentum Shift strategy.
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.rsi_threshold = self.config.get('rsi_threshold', 30)
        self.volume_threshold = self.config.get('volume_threshold', 1.3)
        self.lookback = self.config.get('lookback', 5)
    
    def detect_signal(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str
    ) -> Optional[any]:
        """
        Detect momentum shift signals.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if len(data) < self.lookback + 1:
                logger.debug("Insufficient data for momentum shift")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['rsi', 'close', 'volume', 'volume_ma', 'atr']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug("Missing required indicators for momentum shift")
                return None
            
            # Check for RSI reversal
            prev_rsi = prev['rsi']
            curr_rsi = last['rsi']
            
            # Oversold bounce: RSI was below 30, now rising
            oversold_bounce = prev_rsi < self.rsi_threshold and curr_rsi > prev_rsi
            
            # Overbought drop: RSI was above 70, now falling
            overbought_drop = prev_rsi > (100 - self.rsi_threshold) and curr_rsi < prev_rsi
            
            if not (oversold_bounce or overbought_drop):
                return None
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < self.volume_threshold:
                logger.debug(f"Volume too low: {volume_ratio:.2f}x")
                return None
            
            # Determine signal type
            signal_type = "LONG" if oversold_bounce else "SHORT"
            entry = last['close']
            stop_loss = entry - (last['atr'] * 1.5) if oversold_bounce else entry + (last['atr'] * 1.5)
            take_profit = entry + (last['atr'] * 2.0) if oversold_bounce else entry - (last['atr'] * 2.0)
            
            # Calculate risk/reward
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            risk_reward = reward / risk if risk > 0 else 0
            
            if risk_reward < 1.2:
                logger.debug(f"Risk/reward too low: {risk_reward:.2f}")
                return None
            
            logger.info(f"Momentum Shift signal: {signal_type}")
            
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
                market_bias="bullish" if oversold_bounce else "bearish",
                confidence=3,
                indicators={
                    'rsi': curr_rsi,
                    'prev_rsi': prev_rsi,
                    'volume': last['volume'],
                    'volume_ma': last['volume_ma']
                },
                reasoning=f"RSI momentum shift from {prev_rsi:.1f} to {curr_rsi:.1f}, Volume {volume_ratio:.2f}x",
                strategy="Momentum Shift"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in Momentum Shift strategy: {e}", exc_info=True)
            return None
