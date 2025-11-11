"""
Signal Quality Filter
Ensures only high-quality signals are sent to traders
Enhanced with confluence evaluation, confidence scoring, and risk-reward validation
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
    min_confluence_factors: int = 4  # Increased from 3 to 4
    min_confidence_score: int = 4  # Increased from 3 to 4
    duplicate_window_seconds: int = 300  # 5 minutes for scalp
    duplicate_price_tolerance_pct: float = 0.5  # 0.5% price tolerance
    significant_price_move_pct: float = 1.0  # 1.0% move allows new signal
    min_risk_reward: float = 1.5  # Minimum risk-reward ratio
    confluence_weights: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        if self.confluence_weights is None:
            # Updated weights based on design document
            # Critical factors: 3 points each
            # Supporting factors: 2 points each
            # Context factors: 1 point each
            self.confluence_weights = {
                'trend': 3.0,  # Critical
                'momentum': 3.0,  # Critical
                'volume': 2.0,  # Supporting
                'price_action': 2.0,  # Supporting
                'support_resistance': 2.0,  # Supporting
                'multi_timeframe': 1.0,  # Context
                'volatility': 1.0  # Context
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
        
        Evaluates 7 confluence factors:
        1. Trend alignment (price vs EMA50, EMA cascade)
        2. Momentum confirmation (RSI direction, ADX strength)
        3. Volume support (volume ratio vs threshold)
        4. Price action confirmation (recent candle patterns)
        5. Support/resistance proximity (distance from key levels)
        6. Multi-timeframe alignment (higher TF trend)
        7. Volatility context (ATR relative to average)
        
        Args:
            signal: Signal to evaluate
            market_data: Optional DataFrame with market context
            
        Returns:
            FilterResult with pass/fail and confidence score
        """
        # Calculate confluence factors
        confluence_dict = self.calculate_confluence_factors(signal, market_data)
        
        # Get list of factors that passed
        confluence_factors = [k for k, v in confluence_dict.items() if v]
        
        # Calculate confidence score with risk-reward adjustment
        confidence_score = self.calculate_confidence_score(confluence_dict)
        
        # Validate risk-reward ratio
        rr_valid, rr_ratio = self.validate_risk_reward(signal)
        
        if not rr_valid:
            logger.info(f"Signal rejected - poor risk-reward: {rr_ratio:.2f} < {self.config.min_risk_reward}")
            return FilterResult(
                passed=False,
                confidence_score=confidence_score,
                confluence_factors=confluence_factors,
                rejection_reason=f"Risk-reward ratio too low: {rr_ratio:.2f} < {self.config.min_risk_reward}"
            )
        
        # Adjust confidence score based on risk-reward
        if rr_ratio >= 2.5:
            confidence_score = min(5, confidence_score + 1)
            logger.debug(f"Confidence score increased for excellent R:R {rr_ratio:.2f}: {confidence_score}")
        elif rr_ratio < 2.0:
            confidence_score = max(1, confidence_score - 1)
            logger.debug(f"Confidence score decreased for low R:R {rr_ratio:.2f}: {confidence_score}")
        
        # Check if signal passes minimum confluence threshold
        if len(confluence_factors) < self.config.min_confluence_factors:
            logger.info(f"Signal rejected - insufficient confluence: {len(confluence_factors)} < {self.config.min_confluence_factors}")
            logger.info(f"Missing factors: {[k for k, v in confluence_dict.items() if not v]}")
            return FilterResult(
                passed=False,
                confidence_score=confidence_score,
                confluence_factors=confluence_factors,
                rejection_reason=f"Insufficient confluence factors: {len(confluence_factors)}/{self.config.min_confluence_factors} (missing: {', '.join([k for k, v in confluence_dict.items() if not v])})"
            )
        
        # Check if signal passes minimum confidence threshold
        if confidence_score < self.config.min_confidence_score:
            logger.info(f"Signal rejected - low confidence: {confidence_score} < {self.config.min_confidence_score}")
            return FilterResult(
                passed=False,
                confidence_score=confidence_score,
                confluence_factors=confluence_factors,
                rejection_reason=f"Low confidence score: {confidence_score} < {self.config.min_confidence_score}"
            )
        
        # Check for duplicates
        if self.check_duplicate(signal):
            logger.info(f"Signal rejected - duplicate within time window")
            return FilterResult(
                passed=False,
                confidence_score=confidence_score,
                confluence_factors=confluence_factors,
                rejection_reason="Duplicate signal within time window"
            )
        
        # Signal passed all checks
        logger.info(f"✓ Signal passed quality filter: {len(confluence_factors)}/7 factors, confidence={confidence_score}/5, R:R={rr_ratio:.2f}")
        logger.info(f"  Factors met: {', '.join(confluence_factors)}")
        
        return FilterResult(
            passed=True,
            confidence_score=confidence_score,
            confluence_factors=confluence_factors
        )
    
    def calculate_confluence_factors(self, signal: Signal, market_data: Optional[pd.DataFrame] = None) -> Dict[str, bool]:
        """
        Calculate all 7 confluence factors for a signal
        
        Returns dict with factor name -> True/False
        
        Args:
            signal: Signal to evaluate
            market_data: Optional DataFrame with market context
            
        Returns:
            Dictionary of confluence factors with boolean values
        """
        factors = {
            'trend': False,
            'momentum': False,
            'volume': False,
            'price_action': False,
            'support_resistance': False,
            'multi_timeframe': False,
            'volatility': False
        }
        
        # If no market data, try to use signal's indicator data
        if market_data is None or market_data.empty:
            if hasattr(signal, 'indicators') and signal.indicators:
                # Use indicators from signal
                factors['trend'] = self._check_trend_from_indicators(signal)
                factors['momentum'] = self._check_momentum_from_indicators(signal)
                factors['volume'] = self._check_volume_from_indicators(signal)
                
                logger.debug(f"Evaluated factors from signal indicators: {sum(factors.values())}/7")
                return factors
            else:
                logger.warning("No market data or indicators available for confluence evaluation")
                return factors
        
        last = market_data.iloc[-1]
        
        # Factor 1: Trend alignment
        factors['trend'] = self._check_trend_alignment(signal, last)
        
        # Factor 2: Momentum confirmation
        factors['momentum'] = self._check_momentum_alignment(signal, last)
        
        # Factor 3: Volume support
        factors['volume'] = self._check_volume_confirmation(signal, last)
        
        # Factor 4: Price action confirmation
        factors['price_action'] = self._check_price_action(signal, market_data)
        
        # Factor 5: Support/Resistance proximity
        factors['support_resistance'] = self._check_support_resistance(signal, last)
        
        # Factor 6: Multi-timeframe alignment (placeholder - would need higher TF data)
        factors['multi_timeframe'] = self._check_multi_timeframe(signal, market_data)
        
        # Factor 7: Volatility context
        factors['volatility'] = self._check_volatility_context(signal, last)
        
        logger.debug(f"Confluence factors: {sum(factors.values())}/7 met - {factors}")
        
        return factors
    
    def calculate_confidence_score(self, confluence_factors: Dict[str, bool]) -> int:
        """
        Calculate 1-5 confidence score based on weighted confluence factors
        
        Scoring:
        - Critical factors (trend, momentum): 3 points each
        - Supporting factors (volume, price_action, support_resistance): 2 points each
        - Context factors (multi_timeframe, volatility): 1 point each
        - Total possible: 15 points
        - Score mapping: 0-3pts=1, 4-6pts=2, 7-9pts=3, 10-12pts=4, 13-15pts=5
        
        Args:
            confluence_factors: Dictionary of factor name -> bool
            
        Returns:
            Confidence score (1-5)
        """
        # Calculate weighted score
        weighted_score = 0.0
        for factor, passed in confluence_factors.items():
            if passed:
                weight = self.config.confluence_weights.get(factor, 1.0)
                weighted_score += weight
        
        logger.debug(f"Weighted confluence score: {weighted_score:.1f}/15")
        
        # Map weighted score to 1-5 scale
        if weighted_score <= 3.0:
            return 1
        elif weighted_score <= 6.0:
            return 2
        elif weighted_score <= 9.0:
            return 3
        elif weighted_score <= 12.0:
            return 4
        else:
            return 5
    
    def validate_risk_reward(self, signal: Signal) -> Tuple[bool, float]:
        """
        Validate risk-reward ratio meets minimum threshold
        
        Args:
            signal: Signal to validate
            
        Returns:
            Tuple of (valid: bool, rr_ratio: float)
        """
        try:
            # Calculate risk-reward ratio
            if signal.signal_type == "LONG":
                risk = signal.entry_price - signal.stop_loss
                reward = signal.take_profit - signal.entry_price
            else:  # SHORT
                risk = signal.stop_loss - signal.entry_price
                reward = signal.entry_price - signal.take_profit
            
            if risk <= 0:
                logger.warning(f"Invalid risk calculation: {risk}")
                return False, 0.0
            
            rr_ratio = reward / risk
            
            # Check against minimum threshold
            is_valid = rr_ratio >= self.config.min_risk_reward
            
            logger.debug(f"Risk-reward: {rr_ratio:.2f} (min: {self.config.min_risk_reward}) - {'✓' if is_valid else '✗'}")
            
            return is_valid, rr_ratio
            
        except Exception as e:
            logger.error(f"Error calculating risk-reward: {e}")
            return False, 0.0
    
    def check_duplicate(self, signal: Signal) -> bool:
        """
        Check if similar signal was sent recently for this symbol
        
        Considers signals duplicate if:
        - Same signal type (LONG/SHORT)
        - Entry price within tolerance (0.5%)
        - Within time window
        
        Allows new signals if:
        - Price moved significantly (>1.0%)
        
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
                # Check price proximity (within tolerance)
                price_diff_pct = abs(signal.entry_price - prev_signal.entry_price) / prev_signal.entry_price * 100
                
                # Allow new signal if price moved significantly
                if price_diff_pct >= self.config.significant_price_move_pct:
                    logger.debug(f"Significant price move ({price_diff_pct:.2f}%), allowing new signal")
                    continue
                
                # Check if within duplicate tolerance
                if price_diff_pct < self.config.duplicate_price_tolerance_pct:
                    logger.info(f"Duplicate signal detected for {symbol}: {signal.signal_type} within {time_diff.seconds}s, price diff {price_diff_pct:.2f}%")
                    logger.info(f"  Previous: {prev_signal.entry_price:.2f} @ {timestamp}")
                    logger.info(f"  Current:  {signal.entry_price:.2f} @ {signal.timestamp}")
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
        """
        Check if signal aligns with trend (price vs EMA50, EMA cascade)
        
        For LONG: price > EMA50 and ideally EMA9 > EMA21 > EMA50
        For SHORT: price < EMA50 and ideally EMA9 < EMA21 < EMA50
        """
        try:
            # Check price vs EMA50 (critical)
            if 'ema_50' in last_candle.index:
                if signal.signal_type == "LONG":
                    if last_candle['close'] <= last_candle['ema_50']:
                        return False
                elif signal.signal_type == "SHORT":
                    if last_candle['close'] >= last_candle['ema_50']:
                        return False
            else:
                return False
            
            # Check EMA cascade (bonus)
            if 'ema_9' in last_candle.index and 'ema_21' in last_candle.index:
                if signal.signal_type == "LONG":
                    cascade = (last_candle['ema_9'] > last_candle['ema_21'] and 
                              last_candle['ema_21'] > last_candle['ema_50'])
                    logger.debug(f"Trend check (LONG): price > EMA50 ✓, cascade: {cascade}")
                    return True  # Price > EMA50 is sufficient
                else:
                    cascade = (last_candle['ema_9'] < last_candle['ema_21'] and 
                              last_candle['ema_21'] < last_candle['ema_50'])
                    logger.debug(f"Trend check (SHORT): price < EMA50 ✓, cascade: {cascade}")
                    return True  # Price < EMA50 is sufficient
            
            return True  # Price vs EMA50 check passed
            
        except Exception as e:
            logger.debug(f"Error checking trend alignment: {e}")
            return False
    
    def _check_trend_from_indicators(self, signal: Signal) -> bool:
        """Check trend alignment from signal's indicator data"""
        try:
            if not signal.indicators:
                return False
            
            if 'ema_50' not in signal.indicators:
                return False
            
            entry = signal.entry_price
            ema50 = signal.indicators['ema_50']
            
            if signal.signal_type == "LONG":
                return entry > ema50
            else:
                return entry < ema50
                
        except Exception as e:
            logger.debug(f"Error checking trend from indicators: {e}")
            return False
    
    def _check_volume_confirmation(self, signal: Signal, last_candle: pd.Series) -> bool:
        """
        Check if volume confirms the signal (volume ratio vs threshold)
        
        Volume should be above average (>1.0x)
        """
        try:
            if 'volume' not in last_candle.index or 'volume_ma' not in last_candle.index:
                return False
            
            volume_ratio = last_candle['volume'] / last_candle['volume_ma']
            
            # Volume should be above average
            if volume_ratio >= 1.0:
                logger.debug(f"Volume check: {volume_ratio:.2f}x ✓")
                return True
            else:
                logger.debug(f"Volume check: {volume_ratio:.2f}x < 1.0 ✗")
                return False
                
        except Exception as e:
            logger.debug(f"Error checking volume confirmation: {e}")
            return False
    
    def _check_volume_from_indicators(self, signal: Signal) -> bool:
        """Check volume confirmation from signal's indicator data"""
        try:
            if not signal.indicators:
                return False
            
            if 'volume' not in signal.indicators or 'volume_ma' not in signal.indicators:
                return False
            
            volume_ratio = signal.indicators['volume'] / signal.indicators['volume_ma']
            return volume_ratio >= 1.0
                
        except Exception as e:
            logger.debug(f"Error checking volume from indicators: {e}")
            return False
    
    def _check_momentum_alignment(self, signal: Signal, last_candle: pd.Series) -> bool:
        """
        Check if momentum indicators align with signal (RSI direction, ADX strength)
        
        For LONG: RSI > 50 and ADX >= 18
        For SHORT: RSI < 50 and ADX >= 18
        """
        try:
            # Check RSI direction
            if 'rsi' not in last_candle.index:
                return False
            
            rsi = last_candle['rsi']
            
            if signal.signal_type == "LONG":
                if rsi <= 50:
                    logger.debug(f"Momentum check (LONG): RSI {rsi:.1f} <= 50 ✗")
                    return False
            else:
                if rsi >= 50:
                    logger.debug(f"Momentum check (SHORT): RSI {rsi:.1f} >= 50 ✗")
                    return False
            
            # Check ADX strength (if available)
            if 'adx' in last_candle.index:
                adx = last_candle['adx']
                if adx < 18:
                    logger.debug(f"Momentum check: ADX {adx:.1f} < 18 ✗")
                    return False
                logger.debug(f"Momentum check: RSI {rsi:.1f}, ADX {adx:.1f} ✓")
            else:
                logger.debug(f"Momentum check: RSI {rsi:.1f} ✓ (no ADX)")
            
            return True
            
        except Exception as e:
            logger.debug(f"Error checking momentum alignment: {e}")
            return False
    
    def _check_momentum_from_indicators(self, signal: Signal) -> bool:
        """Check momentum alignment from signal's indicator data"""
        try:
            if not signal.indicators or 'rsi' not in signal.indicators:
                return False
            
            rsi = signal.indicators['rsi']
            
            if signal.signal_type == "LONG":
                return rsi > 50
            else:
                return rsi < 50
                
        except Exception as e:
            logger.debug(f"Error checking momentum from indicators: {e}")
            return False
    
    def _check_price_action(self, signal: Signal, market_data: pd.DataFrame) -> bool:
        """
        Check if recent price action confirms signal direction
        
        For LONG: Recent candles should show upward bias
        For SHORT: Recent candles should show downward bias
        """
        try:
            if len(market_data) < 5:
                return False
            
            # Check last 5 candles
            recent = market_data.iloc[-5:]
            
            if signal.signal_type == "LONG":
                # Check for higher lows or upward momentum
                lows = recent['low'].values
                higher_lows = sum(1 for i in range(1, len(lows)) if lows[i] >= lows[i-1])
                
                if higher_lows >= 3:  # At least 3 out of 4 comparisons
                    logger.debug(f"Price action check (LONG): {higher_lows}/4 higher lows ✓")
                    return True
                else:
                    logger.debug(f"Price action check (LONG): {higher_lows}/4 higher lows ✗")
                    return False
            else:
                # Check for lower highs or downward momentum
                highs = recent['high'].values
                lower_highs = sum(1 for i in range(1, len(highs)) if highs[i] <= highs[i-1])
                
                if lower_highs >= 3:  # At least 3 out of 4 comparisons
                    logger.debug(f"Price action check (SHORT): {lower_highs}/4 lower highs ✓")
                    return True
                else:
                    logger.debug(f"Price action check (SHORT): {lower_highs}/4 lower highs ✗")
                    return False
                    
        except Exception as e:
            logger.debug(f"Error checking price action: {e}")
            return False
    
    def _check_support_resistance(self, signal: Signal, last_candle: pd.Series) -> bool:
        """
        Check if signal is near support/resistance (distance from key levels)
        
        Uses VWAP as a key level - price should be near it (within 1.0%)
        """
        try:
            # Check if price is near VWAP (within 1.0%)
            if 'vwap' in last_candle.index:
                distance_pct = abs(last_candle['close'] - last_candle['vwap']) / last_candle['vwap'] * 100
                
                if distance_pct <= 1.0:
                    logger.debug(f"S/R check: {distance_pct:.2f}% from VWAP ✓")
                    return True
                else:
                    logger.debug(f"S/R check: {distance_pct:.2f}% from VWAP (>1.0%) ✗")
                    return False
        except Exception as e:
            logger.debug(f"Error checking support/resistance: {e}")
        
        return False
    
    def _check_multi_timeframe(self, signal: Signal, market_data: pd.DataFrame) -> bool:
        """
        Check if higher timeframe trend aligns with signal
        
        Placeholder - would need higher TF data to implement fully
        For now, returns True if signal has strong confluence on current TF
        """
        try:
            # Placeholder: Check if signal has strong indicators
            if hasattr(signal, 'confidence') and signal.confidence >= 4:
                logger.debug(f"MTF check: Signal confidence {signal.confidence} >= 4 ✓")
                return True
            
            logger.debug(f"MTF check: Insufficient data ✗")
            return False
            
        except Exception as e:
            logger.debug(f"Error checking multi-timeframe: {e}")
            return False
    
    def _check_volatility_context(self, signal: Signal, last_candle: pd.Series) -> bool:
        """
        Check if volatility is in normal range (ATR relative to average)
        
        ATR should not be extremely high or low
        """
        try:
            if 'atr' not in last_candle.index:
                return False
            
            # Check if ATR is reasonable (not NaN or zero)
            atr = last_candle['atr']
            if pd.isna(atr) or atr <= 0:
                logger.debug(f"Volatility check: Invalid ATR ✗")
                return False
            
            # Simple check: ATR exists and is valid
            # Could be enhanced with ATR moving average comparison
            logger.debug(f"Volatility check: ATR {atr:.2f} valid ✓")
            return True
            
        except Exception as e:
            logger.debug(f"Error checking volatility context: {e}")
            return False
