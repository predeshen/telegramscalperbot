"""
EMA Crossover Strategy
Detects trading signals based on EMA crossovers and trend alignment.
"""
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class EMACrossover:
    """EMA Crossover strategy implementation"""
    
    def __init__(self, config: dict = None):
        """
        Initialize EMA Crossover strategy.
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.fast_ema = self.config.get('fast_ema', 9)
        self.slow_ema = self.config.get('slow_ema', 21)
        self.trend_ema = self.config.get('trend_ema', 50)
        self.volume_threshold = self.config.get('volume_threshold', 1.3)
    
    def detect_signal(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str
    ) -> Optional[any]:
        """
        Detect EMA crossover signals.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if len(data) < 2:
                logger.debug("Insufficient data for EMA crossover")
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = [f'ema_{self.fast_ema}', f'ema_{self.slow_ema}', 'close', 'volume', 'volume_ma', 'atr']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug("Missing required EMA indicators")
                return None
            
            fast_ema_key = f'ema_{self.fast_ema}'
            slow_ema_key = f'ema_{self.slow_ema}'
            
            # Check for crossover
            prev_fast = prev[fast_ema_key]
            prev_slow = prev[slow_ema_key]
            curr_fast = last[fast_ema_key]
            curr_slow = last[slow_ema_key]
            
            # Bullish crossover: fast crosses above slow
            bullish_cross = prev_fast <= prev_slow and curr_fast > curr_slow
            
            # Bearish crossover: fast crosses below slow
            bearish_cross = prev_fast >= prev_slow and curr_fast < curr_slow
            
            if not (bullish_cross or bearish_cross):
                return None
            
            # Check volume confirmation
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < self.volume_threshold:
                logger.debug(f"Volume too low: {volume_ratio:.2f}x")
                return None
            
            # Determine signal type
            signal_type = "LONG" if bullish_cross else "SHORT"
            entry = last['close']
            stop_loss = entry - (last['atr'] * 1.5) if bullish_cross else entry + (last['atr'] * 1.5)
            take_profit = entry + (last['atr'] * 2.0) if bullish_cross else entry - (last['atr'] * 2.0)
            
            # Calculate risk/reward
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            risk_reward = reward / risk if risk > 0 else 0
            
            if risk_reward < 1.2:
                logger.debug(f"Risk/reward too low: {risk_reward:.2f}")
                return None
            
            logger.info(f"EMA Crossover signal: {signal_type}")
            
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
                market_bias="bullish" if bullish_cross else "bearish",
                confidence=3,
                indicators={
                    'fast_ema': curr_fast,
                    'slow_ema': curr_slow,
                    'volume': last['volume'],
                    'volume_ma': last['volume_ma']
                },
                reasoning=f"EMA {self.fast_ema}/{self.slow_ema} crossover, Volume {volume_ratio:.2f}x",
                strategy="EMA Crossover"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in EMA Crossover strategy: {e}", exc_info=True)
            return None
