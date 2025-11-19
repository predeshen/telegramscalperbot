"""
Mean Reversion Strategy
Detects overbought/oversold conditions for mean reversion trades.
"""
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class MeanReversion:
    """Mean Reversion strategy implementation"""
    
    def __init__(self, config: dict = None):
        """
        Initialize Mean Reversion strategy.
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.volume_threshold = self.config.get('volume_threshold', 1.3)
        self.bb_std_dev = self.config.get('bb_std_dev', 2.0)
    
    def detect_signal(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str
    ) -> Optional[any]:
        """
        Detect mean reversion signals.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if len(data) < 2:
                logger.debug("Insufficient data for mean reversion")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['rsi', 'close', 'volume', 'volume_ma', 'atr']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug("Missing required indicators for mean reversion")
                return None
            
            curr_rsi = last['rsi']
            
            # Overbought condition: RSI > 70
            overbought = curr_rsi > self.rsi_overbought
            
            # Oversold condition: RSI < 30
            oversold = curr_rsi < self.rsi_oversold
            
            if not (overbought or oversold):
                logger.debug(f"RSI not in extreme zone: {curr_rsi:.1f}")
                return None
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < self.volume_threshold:
                logger.debug(f"Volume too low: {volume_ratio:.2f}x")
                return None
            
            # Determine signal type (mean reversion trades opposite direction)
            signal_type = "SHORT" if overbought else "LONG"
            entry = last['close']
            stop_loss = entry + (last['atr'] * 1.5) if overbought else entry - (last['atr'] * 1.5)
            take_profit = entry - (last['atr'] * 2.0) if overbought else entry + (last['atr'] * 2.0)
            
            # Calculate risk/reward
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            risk_reward = reward / risk if risk > 0 else 0
            
            if risk_reward < 1.2:
                logger.debug(f"Risk/reward too low: {risk_reward:.2f}")
                return None
            
            logger.info(f"Mean Reversion signal: {signal_type}")
            
            # Create signal object
            from src.signal_detector import Signal
            from src.symbol_context import SymbolContext
            
            try:
                symbol_context = SymbolContext.from_symbol(symbol if symbol in ['BTC', 'XAUUSD', 'US30', 'US100'] else 'BTC')
            except:
                symbol_context = None
            
            condition = "overbought" if overbought else "oversold"
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
                market_bias="bearish" if overbought else "bullish",
                confidence=3,
                indicators={
                    'rsi': curr_rsi,
                    'volume': last['volume'],
                    'volume_ma': last['volume_ma']
                },
                reasoning=f"Mean reversion from {condition} RSI {curr_rsi:.1f}, Volume {volume_ratio:.2f}x",
                strategy="Mean Reversion"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in Mean Reversion strategy: {e}", exc_info=True)
            return None
