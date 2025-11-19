"""
Live and Future Signal Detection
Detects both current candle signals (LIVE) and predicted upcoming signals (FUTURE).
"""
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FutureSignal:
    """Predicted signal for upcoming candles"""
    timestamp: datetime
    signal_type: str  # "LONG" or "SHORT"
    timeframe: str
    symbol: str
    predicted_entry: float
    predicted_stop_loss: float
    predicted_take_profit: float
    confidence: float  # 0-1
    pattern_type: str  # Pattern that triggered prediction
    lookahead_candles: int  # How many candles ahead
    materialized: bool = False
    materialized_signal: Optional[any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class FutureSignalDetector:
    """Detects live and future trading signals"""
    
    def __init__(self):
        """Initialize future signal detector"""
        self.pending_future_signals: List[FutureSignal] = []
        self.materialized_signals: List[FutureSignal] = []
    
    def detect_live_signals(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str,
        strategy_detector: any
    ) -> Optional[any]:
        """
        Detect live signals on current candle.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            strategy_detector: Strategy detector instance
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if data.empty:
                logger.debug("Cannot detect live signals: DataFrame is empty")
                return None
            
            # Use strategy detector to find signals
            signal = strategy_detector.detect_signals(data, timeframe, symbol)
            
            if signal:
                logger.info(f"LIVE signal detected: {signal.signal_type} on {timeframe}")
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting live signals: {e}")
            return None
    
    def predict_future_signals(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str,
        lookahead_candles: int = 3
    ) -> List[FutureSignal]:
        """
        Predict future signals for upcoming candles.
        
        Analyzes current candle formation to predict likely next candle patterns.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            lookahead_candles: Number of candles to look ahead (1-3)
            
        Returns:
            List of predicted future signals
        """
        try:
            if len(data) < 5:
                logger.debug("Insufficient data for future signal prediction")
                return []
            
            future_signals = []
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for forming patterns that suggest future signals
            
            # Pattern 1: Forming pin bar (long wick forming)
            if self._is_forming_pin_bar(last, prev):
                signal = self._create_future_signal_from_pin_bar(
                    data, timeframe, symbol, lookahead_candles
                )
                if signal:
                    future_signals.append(signal)
                    logger.info(f"FUTURE signal predicted: Pin bar pattern forming")
            
            # Pattern 2: Forming engulfing (large body forming)
            if self._is_forming_engulfing(last, prev):
                signal = self._create_future_signal_from_engulfing(
                    data, timeframe, symbol, lookahead_candles
                )
                if signal:
                    future_signals.append(signal)
                    logger.info(f"FUTURE signal predicted: Engulfing pattern forming")
            
            # Pattern 3: Price approaching key level
            if self._is_approaching_key_level(last, data):
                signal = self._create_future_signal_from_key_level(
                    data, timeframe, symbol, lookahead_candles
                )
                if signal:
                    future_signals.append(signal)
                    logger.info(f"FUTURE signal predicted: Approaching key level")
            
            # Pattern 4: Momentum building (RSI trending)
            if self._is_momentum_building(last, prev, data):
                signal = self._create_future_signal_from_momentum(
                    data, timeframe, symbol, lookahead_candles
                )
                if signal:
                    future_signals.append(signal)
                    logger.info(f"FUTURE signal predicted: Momentum building")
            
            return future_signals
            
        except Exception as e:
            logger.error(f"Error predicting future signals: {e}")
            return []
    
    def track_future_signal_materialization(
        self,
        future_signal: FutureSignal,
        current_data: pd.DataFrame
    ) -> Optional[any]:
        """
        Track if a future signal materializes into a live signal.
        
        Args:
            future_signal: Future signal to track
            current_data: Current market data
            
        Returns:
            Materialized signal if it occurs, None otherwise
        """
        try:
            if future_signal.materialized:
                return future_signal.materialized_signal
            
            # Check if signal has expired (3 candles passed)
            age_candles = (datetime.now() - future_signal.created_at).total_seconds() / 60
            if age_candles > (future_signal.lookahead_candles * 5):  # Assuming 5-min candles
                logger.info(f"Future signal expired: {future_signal.pattern_type}")
                return None
            
            # Check if predicted entry price is being approached
            if len(current_data) > 0:
                last = current_data.iloc[-1]
                current_price = last['close']
                
                # Check if price is within 0.5% of predicted entry
                tolerance = future_signal.predicted_entry * 0.005
                
                if abs(current_price - future_signal.predicted_entry) <= tolerance:
                    logger.info(f"Future signal materializing: {future_signal.pattern_type}")
                    future_signal.materialized = True
                    
                    # Create materialized signal
                    from src.signal_detector import Signal
                    from src.symbol_context import SymbolContext
                    
                    try:
                        symbol_context = SymbolContext.from_symbol(
                            future_signal.symbol if future_signal.symbol in ['BTC', 'XAUUSD', 'US30', 'US100'] else 'BTC'
                        )
                    except:
                        symbol_context = None
                    
                    materialized = Signal(
                        timestamp=last['timestamp'],
                        signal_type=future_signal.signal_type,
                        timeframe=future_signal.timeframe,
                        symbol=future_signal.symbol,
                        symbol_context=symbol_context,
                        entry_price=future_signal.predicted_entry,
                        stop_loss=future_signal.predicted_stop_loss,
                        take_profit=future_signal.predicted_take_profit,
                        atr=last.get('atr', 0),
                        risk_reward=self._calculate_rr(
                            future_signal.predicted_entry,
                            future_signal.predicted_stop_loss,
                            future_signal.predicted_take_profit
                        ),
                        market_bias="neutral",
                        confidence=4,
                        indicators={
                            'pattern': future_signal.pattern_type,
                            'predicted_confidence': future_signal.confidence
                        },
                        reasoning=f"Future signal materialized: {future_signal.pattern_type}",
                        strategy=f"Future Signal - {future_signal.pattern_type}"
                    )
                    
                    future_signal.materialized_signal = materialized
                    return materialized
            
            return None
            
        except Exception as e:
            logger.error(f"Error tracking future signal materialization: {e}")
            return None
    
    @staticmethod
    def _is_forming_pin_bar(last: pd.Series, prev: pd.Series) -> bool:
        """Check if pin bar pattern is forming"""
        try:
            body = abs(last['close'] - last['open'])
            wick_up = last['high'] - max(last['open'], last['close'])
            wick_down = min(last['open'], last['close']) - last['low']
            total_range = last['high'] - last['low']
            
            if total_range > 0:
                wick_ratio = max(wick_up, wick_down) / total_range
                body_ratio = body / total_range
                
                # Forming: wick is developing (>0.4) and body is small (<0.4)
                return wick_ratio > 0.4 and body_ratio < 0.4
            
            return False
        except:
            return False
    
    @staticmethod
    def _is_forming_engulfing(last: pd.Series, prev: pd.Series) -> bool:
        """Check if engulfing pattern is forming"""
        try:
            # Engulfing: current candle is larger than previous
            current_range = last['high'] - last['low']
            prev_range = prev['high'] - prev['low']
            
            # Forming: current range is at least 1.5x previous
            return current_range >= (prev_range * 1.5)
        except:
            return False
    
    @staticmethod
    def _is_approaching_key_level(last: pd.Series, data: pd.DataFrame) -> bool:
        """Check if price is approaching a key level"""
        try:
            if 'vwap' not in last.index:
                return False
            
            # Check if price is within 0.5% of VWAP
            distance_pct = abs(last['close'] - last['vwap']) / last['vwap'] * 100
            return distance_pct <= 0.5
        except:
            return False
    
    @staticmethod
    def _is_momentum_building(last: pd.Series, prev: pd.Series, data: pd.DataFrame) -> bool:
        """Check if momentum is building"""
        try:
            if 'rsi' not in last.index or 'rsi' not in prev.index:
                return False
            
            # RSI trending in one direction
            rsi_diff = last['rsi'] - prev['rsi']
            
            # Building momentum: RSI moving significantly (>5 points)
            return abs(rsi_diff) > 5
        except:
            return False
    
    @staticmethod
    def _create_future_signal_from_pin_bar(
        data: pd.DataFrame,
        timeframe: str,
        symbol: str,
        lookahead_candles: int
    ) -> Optional[FutureSignal]:
        """Create future signal from forming pin bar"""
        try:
            last = data.iloc[-1]
            
            # Determine direction based on wick position
            wick_up = last['high'] - max(last['open'], last['close'])
            wick_down = min(last['open'], last['close']) - last['low']
            
            if wick_up > wick_down:
                # Upper wick: expect bounce down (SHORT)
                signal_type = "SHORT"
                predicted_entry = last['high']
                predicted_stop_loss = last['high'] + (last['atr'] * 0.5)
                predicted_take_profit = last['close'] - (last['atr'] * 1.0)
            else:
                # Lower wick: expect bounce up (LONG)
                signal_type = "LONG"
                predicted_entry = last['low']
                predicted_stop_loss = last['low'] - (last['atr'] * 0.5)
                predicted_take_profit = last['close'] + (last['atr'] * 1.0)
            
            return FutureSignal(
                timestamp=datetime.now(),
                signal_type=signal_type,
                timeframe=timeframe,
                symbol=symbol,
                predicted_entry=predicted_entry,
                predicted_stop_loss=predicted_stop_loss,
                predicted_take_profit=predicted_take_profit,
                confidence=0.7,
                pattern_type="Pin Bar",
                lookahead_candles=lookahead_candles
            )
        except Exception as e:
            logger.debug(f"Error creating pin bar future signal: {e}")
            return None
    
    @staticmethod
    def _create_future_signal_from_engulfing(
        data: pd.DataFrame,
        timeframe: str,
        symbol: str,
        lookahead_candles: int
    ) -> Optional[FutureSignal]:
        """Create future signal from forming engulfing"""
        try:
            last = data.iloc[-1]
            
            # Determine direction based on close position
            if last['close'] > last['open']:
                # Bullish engulfing: expect continuation up (LONG)
                signal_type = "LONG"
                predicted_entry = last['close']
                predicted_stop_loss = last['low'] - (last['atr'] * 0.5)
                predicted_take_profit = last['close'] + (last['atr'] * 1.5)
            else:
                # Bearish engulfing: expect continuation down (SHORT)
                signal_type = "SHORT"
                predicted_entry = last['close']
                predicted_stop_loss = last['high'] + (last['atr'] * 0.5)
                predicted_take_profit = last['close'] - (last['atr'] * 1.5)
            
            return FutureSignal(
                timestamp=datetime.now(),
                signal_type=signal_type,
                timeframe=timeframe,
                symbol=symbol,
                predicted_entry=predicted_entry,
                predicted_stop_loss=predicted_stop_loss,
                predicted_take_profit=predicted_take_profit,
                confidence=0.75,
                pattern_type="Engulfing",
                lookahead_candles=lookahead_candles
            )
        except Exception as e:
            logger.debug(f"Error creating engulfing future signal: {e}")
            return None
    
    @staticmethod
    def _create_future_signal_from_key_level(
        data: pd.DataFrame,
        timeframe: str,
        symbol: str,
        lookahead_candles: int
    ) -> Optional[FutureSignal]:
        """Create future signal from approaching key level"""
        try:
            last = data.iloc[-1]
            
            # Determine direction based on position relative to VWAP
            if last['close'] < last['vwap']:
                # Below VWAP: expect bounce up (LONG)
                signal_type = "LONG"
                predicted_entry = last['vwap']
                predicted_stop_loss = last['low'] - (last['atr'] * 0.5)
                predicted_take_profit = last['vwap'] + (last['atr'] * 1.0)
            else:
                # Above VWAP: expect bounce down (SHORT)
                signal_type = "SHORT"
                predicted_entry = last['vwap']
                predicted_stop_loss = last['high'] + (last['atr'] * 0.5)
                predicted_take_profit = last['vwap'] - (last['atr'] * 1.0)
            
            return FutureSignal(
                timestamp=datetime.now(),
                signal_type=signal_type,
                timeframe=timeframe,
                symbol=symbol,
                predicted_entry=predicted_entry,
                predicted_stop_loss=predicted_stop_loss,
                predicted_take_profit=predicted_take_profit,
                confidence=0.65,
                pattern_type="Key Level Approach",
                lookahead_candles=lookahead_candles
            )
        except Exception as e:
            logger.debug(f"Error creating key level future signal: {e}")
            return None
    
    @staticmethod
    def _create_future_signal_from_momentum(
        data: pd.DataFrame,
        timeframe: str,
        symbol: str,
        lookahead_candles: int
    ) -> Optional[FutureSignal]:
        """Create future signal from building momentum"""
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Determine direction based on RSI trend
            if last['rsi'] > prev['rsi']:
                # RSI rising: expect continuation up (LONG)
                signal_type = "LONG"
                predicted_entry = last['close']
                predicted_stop_loss = last['low'] - (last['atr'] * 0.5)
                predicted_take_profit = last['close'] + (last['atr'] * 1.5)
            else:
                # RSI falling: expect continuation down (SHORT)
                signal_type = "SHORT"
                predicted_entry = last['close']
                predicted_stop_loss = last['high'] + (last['atr'] * 0.5)
                predicted_take_profit = last['close'] - (last['atr'] * 1.5)
            
            return FutureSignal(
                timestamp=datetime.now(),
                signal_type=signal_type,
                timeframe=timeframe,
                symbol=symbol,
                predicted_entry=predicted_entry,
                predicted_stop_loss=predicted_stop_loss,
                predicted_take_profit=predicted_take_profit,
                confidence=0.6,
                pattern_type="Momentum Building",
                lookahead_candles=lookahead_candles
            )
        except Exception as e:
            logger.debug(f"Error creating momentum future signal: {e}")
            return None
    
    @staticmethod
    def _calculate_rr(entry: float, sl: float, tp: float) -> float:
        """Calculate risk/reward ratio"""
        try:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            return reward / risk if risk > 0 else 0
        except:
            return 0

