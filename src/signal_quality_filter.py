"""
Signal Quality Filter
Ensures only high-quality signals are sent to traders
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.signal_detector import Signal


logger = logging.getLogger(__name__)


@dataclass
class QualityConfig:
    """Configuration for signal quality filter"""
    min_confluence_factors: int = 3
    min_confidence_score: int = 3
    duplicate_window_seconds: int = 300  # 5 minutes
    confluence_weights: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        if self.confluence_weights is None:
            self.confluence_weights = {
                'trend': 1.0,
                'volume': 1.0,
                'momentum': 1.0,
                'support_resistance': 0.8,
                'multi_timeframe': 1.2
            }


@dataclass
class FilterResult:
    """Result of signal quality filtering"""
    passed: bool
    confidence_score: int
    confluence_factors: List[str]
    rejection_reason: Optional[str] = None


class SignalQualityFilter:
    """
    Filters signals based on quality criteria and confidence scoring
    """
    
    def __init__(self, config: Optional[QualityConfig] = None):
        """
        Initialize signal quality filter
        
        Args:
            config: QualityConfig with filtering thresholds
        """
        self.config = config or QualityConfig()
        self.recent_signals: Dict[str, List[Tuple[datetime, Signal]]] = {}
        
        logger.info(f"Initialized SignalQualityFilter: "
                   f"min_confluence={self.config.min_confluence_factors}, "
                   f"min_confidence={self.config.min_confidence_score}")
    
    def evaluate_signal(self, signal: Signal, market_data: Optional[pd.DataFrame] = None) -> FilterResult:
        """
        Evaluate signal quality and calculate confidence score
        
        Confluence factors:
        - Trend alignment (price above/below key MAs)
        - Volume confirmation (volume > average)
        - Momentum (RSI, MACD alignment)
        - Support/Resistance proximity
        - Multi-timeframe confirmation
        
        Args:
            signal: Signal to evaluate
            market_data: Optional DataFrame with market context
            
        Returns:
            FilterResult with pass/fail and confidence score
        """
        confluence_factors = []
        
        # Check existing confluence factors from signal
        if hasattr(signal, 'confluence_factors') and signal.confluence_factors:
            confluence_factors.extend(signal.confluence_factors)
        
        # Evaluate additional confluence factors from market data
        if market_data is not None and not market_data.empty:
            last = market_data.iloc[-1]
            
            # Factor 1: Trend alignment
            if self._check_trend_alignment(signal, last):
                confluence_factors.append('trend_alignment')
            
            # Factor 2: Volume confirmation
            if self._check_volume_confirmation(signal, last):
                confluence_factors.append('volume_confirmation')
            
            # Factor 3: Momentum alignment
            if self._check_momentum_alignment(signal, last):
                confluence_factors.append('momentum_alignment')
            
            # Factor 4: Support/Resistance proximity
            if self._check_support_resistance(signal, last):
                confluence_factors.append('support_resistance')
        
        # Remove duplicates
        confluence_factors = list(set(confluence_factors))
        
        # Calculate confidence score
        confidence_score = self.calculate_confidence_score(confluence_factors)
        
        # Check if signal passes minimum thresholds
        if len(confluence_factors) < self.config.min_confluence_factors:
            return FilterResult(
                passed=False,
                confidence_score=confidence_score,
                confluence_factors=confluence_factors,
                rejection_reason=f"Insufficient confluence factors: {len(confluence_factors)} < {self.config.min_confluence_factors}"
            )
        
        if confidence_score < self.config.min_confidence_score:
            return FilterResult(
                passed=False,
                confidence_score=confidence_score,
                confluence_factors=confluence_factors,
                rejection_reason=f"Low confidence score: {confidence_score} < {self.config.min_confidence_score}"
            )
        
        # Check for duplicates
        if self.check_duplicate(signal):
            return FilterResult(
                passed=False,
                confidence_score=confidence_score,
                confluence_factors=confluence_factors,
                rejection_reason="Duplicate signal within time window"
            )
        
        # Signal passed all checks
        logger.info(f"Signal passed quality filter: {len(confluence_factors)} factors, confidence={confidence_score}")
        return FilterResult(
            passed=True,
            confidence_score=confidence_score,
            confluence_factors=confluence_factors
        )
    
    def calculate_confidence_score(self, confluence_factors: List[str]) -> int:
        """
        Calculate 1-5 confidence score based on confluence
        
        1-2: Weak (2 factors) - Not sent
        3: Moderate (3 factors) - Sent with caution
        4: Strong (4 factors) - Good signal
        5: Very Strong (5+ factors) - High probability
        
        Args:
            confluence_factors: List of confluence factor names
            
        Returns:
            Confidence score (1-5)
        """
        # Calculate weighted score
        weighted_score = 0.0
        for factor in confluence_factors:
            # Extract base factor name (remove suffixes like _alignment, _confirmation)
            base_factor = factor.split('_')[0]
            weight = self.config.confluence_weights.get(base_factor, 1.0)
            weighted_score += weight
        
        # Map weighted score to 1-5 scale
        if weighted_score < 2.0:
            return 1
        elif weighted_score < 3.0:
            return 2
        elif weighted_score < 4.0:
            return 3
        elif weighted_score < 5.0:
            return 4
        else:
            return 5
    
    def check_duplicate(self, signal: Signal) -> bool:
        """
        Check if similar signal was sent recently for this symbol
        
        Args:
            signal: Signal to check
            
        Returns:
            True if duplicate, False otherwise
        """
        # Get symbol from signal
        symbol = signal.symbol
        if hasattr(signal, 'symbol_context') and signal.symbol_context:
            symbol = signal.symbol_context.symbol
        
        # Clean expired signals
        self._clean_expired_signals()
        
        # Check recent signals for this symbol
        if symbol not in self.recent_signals:
            self.recent_signals[symbol] = []
            return False
        
        time_threshold = timedelta(seconds=self.config.duplicate_window_seconds)
        
        for timestamp, prev_signal in self.recent_signals[symbol]:
            # Check same signal type
            if prev_signal.signal_type != signal.signal_type:
                continue
            
            # Check time window
            time_diff = signal.timestamp - timestamp
            if time_diff < time_threshold:
                # Check price proximity (within 0.5%)
                price_diff_pct = abs(signal.entry_price - prev_signal.entry_price) / prev_signal.entry_price * 100
                
                if price_diff_pct < 0.5:
                    logger.debug(f"Duplicate signal detected for {symbol}: {signal.signal_type} within {time_diff.seconds}s")
                    return True
        
        return False
    
    def suppress_duplicate(self, signal: Signal, reason: str):
        """
        Log duplicate suppression with reason
        
        Args:
            signal: Signal that was suppressed
            reason: Reason for suppression
        """
        symbol = signal.symbol
        if hasattr(signal, 'symbol_context') and signal.symbol_context:
            symbol = signal.symbol_context.symbol
        
        logger.info(f"Signal suppressed for {symbol}: {reason}")
    
    def add_signal_to_history(self, signal: Signal):
        """
        Add signal to recent history for duplicate detection
        
        Args:
            signal: Signal to add
        """
        symbol = signal.symbol
        if hasattr(signal, 'symbol_context') and signal.symbol_context:
            symbol = signal.symbol_context.symbol
        
        if symbol not in self.recent_signals:
            self.recent_signals[symbol] = []
        
        self.recent_signals[symbol].append((signal.timestamp, signal))
        
        # Keep only recent signals (last 10 per symbol)
        self.recent_signals[symbol] = self.recent_signals[symbol][-10:]
    
    def _clean_expired_signals(self):
        """Remove signals older than duplicate window from history"""
        cutoff_time = datetime.now() - timedelta(seconds=self.config.duplicate_window_seconds * 2)
        
        for symbol in list(self.recent_signals.keys()):
            self.recent_signals[symbol] = [
                (ts, sig) for ts, sig in self.recent_signals[symbol]
                if ts > cutoff_time
            ]
            
            # Remove empty symbol entries
            if not self.recent_signals[symbol]:
                del self.recent_signals[symbol]
    
    def _check_trend_alignment(self, signal: Signal, last_candle: pd.Series) -> bool:
        """Check if signal aligns with trend"""
        try:
            # For LONG signals, price should be above key MAs
            if signal.signal_type == "LONG":
                if 'ema_50' in last_candle.index:
                    return last_candle['close'] > last_candle['ema_50']
            # For SHORT signals, price should be below key MAs
            elif signal.signal_type == "SHORT":
                if 'ema_50' in last_candle.index:
                    return last_candle['close'] < last_candle['ema_50']
        except Exception as e:
            logger.debug(f"Error checking trend alignment: {e}")
        
        return False
    
    def _check_volume_confirmation(self, signal: Signal, last_candle: pd.Series) -> bool:
        """Check if volume confirms the signal"""
        try:
            if 'volume' in last_candle.index and 'volume_ma' in last_candle.index:
                return last_candle['volume'] > last_candle['volume_ma']
        except Exception as e:
            logger.debug(f"Error checking volume confirmation: {e}")
        
        return False
    
    def _check_momentum_alignment(self, signal: Signal, last_candle: pd.Series) -> bool:
        """Check if momentum indicators align with signal"""
        try:
            if 'rsi' in last_candle.index:
                # For LONG signals, RSI should be in bullish range (40-80)
                if signal.signal_type == "LONG":
                    return 40 <= last_candle['rsi'] <= 80
                # For SHORT signals, RSI should be in bearish range (20-60)
                elif signal.signal_type == "SHORT":
                    return 20 <= last_candle['rsi'] <= 60
        except Exception as e:
            logger.debug(f"Error checking momentum alignment: {e}")
        
        return False
    
    def _check_support_resistance(self, signal: Signal, last_candle: pd.Series) -> bool:
        """Check if signal is near support/resistance"""
        try:
            # Check if price is near VWAP (within 0.5%)
            if 'vwap' in last_candle.index:
                distance_pct = abs(last_candle['close'] - last_candle['vwap']) / last_candle['vwap'] * 100
                return distance_pct < 0.5
        except Exception as e:
            logger.debug(f"Error checking support/resistance: {e}")
        
        return False
