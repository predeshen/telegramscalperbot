"""H4 HVG (4-Hour High Volume Gap) Detection Module."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from collections import deque
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class GapInfo:
    """Information about detected price gap."""
    gap_size: float  # Absolute gap size in price units
    gap_percent: float  # Gap size as percentage of previous close
    gap_direction: str  # "up" or "down"
    gap_high: float  # Highest point of the gap
    gap_low: float  # Lowest point of the gap
    volume_ratio: float  # Current volume / volume MA
    candles_ago: int  # How many candles ago the gap occurred
    previous_close: float  # Close price before the gap
    gap_open: float  # Open price that created the gap
    timestamp: datetime  # When the gap occurred


class H4HVGDetector:
    """Detects High Volume Gap patterns on 4-hour timeframes."""
    
    # Market-specific configurations
    MARKET_CONFIGS = {
        'BTC': {
            'min_gap_percent': 0.15,
            'volume_spike_threshold': 1.5,
            'atr_multiplier_sl': 1.5
        },
        'XAU': {
            'min_gap_percent': 0.10,
            'volume_spike_threshold': 1.3,
            'atr_multiplier_sl': 1.2
        },
        'US30': {
            'min_gap_percent': 0.08,
            'volume_spike_threshold': 1.4,
            'atr_multiplier_sl': 1.3
        }
    }
    
    def __init__(self, config: dict = None, symbol: str = "BTC"):
        """
        Initialize H4 HVG detector.
        
        Args:
            config: Configuration dictionary with H4 HVG parameters
            symbol: Trading symbol to determine market-specific settings
        """
        # Determine market type from symbol
        self.market_type = self._get_market_type(symbol)
        market_config = self.MARKET_CONFIGS.get(self.market_type, self.MARKET_CONFIGS['BTC'])
        
        # Load configuration with market-specific defaults
        if config is None:
            config = {}
            
        self.min_gap_percent = config.get('min_gap_percent', market_config['min_gap_percent'])
        self.volume_spike_threshold = config.get('volume_spike_threshold', market_config['volume_spike_threshold'])
        self.atr_multiplier_sl = config.get('atr_multiplier_sl', market_config['atr_multiplier_sl'])
        self.gap_target_multiplier = config.get('gap_target_multiplier', 2.0)
        self.min_risk_reward = config.get('min_risk_reward', 1.5)
        self.max_gap_age_candles = config.get('max_gap_age_candles', 3)
        self.rsi_min = config.get('rsi_min', 30)
        self.rsi_max = config.get('rsi_max', 70)
        self.require_ema_confluence = config.get('require_ema_confluence', True)
        
        # Duplicate signal prevention
        self.duplicate_time_window_minutes = config.get('duplicate_time_window_minutes', 240)  # 4 hours
        self.duplicate_price_threshold_percent = config.get('duplicate_price_threshold_percent', 0.5)
        self.signal_history: deque = deque(maxlen=50)
        
        logger.info(f"H4HVGDetector initialized for {self.market_type} market")
        logger.info(f"Min gap: {self.min_gap_percent}%, Volume threshold: {self.volume_spike_threshold}x")
    
    def _get_market_type(self, symbol: str) -> str:
        """Determine market type from symbol."""
        symbol_upper = symbol.upper()
        if 'BTC' in symbol_upper or 'BITCOIN' in symbol_upper:
            return 'BTC'
        elif 'XAU' in symbol_upper or 'GOLD' in symbol_upper or 'GC=' in symbol_upper:
            return 'XAU'
        elif 'US30' in symbol_upper or 'DOW' in symbol_upper or 'YM=' in symbol_upper:
            return 'US30'
        else:
            # Default to BTC settings for unknown symbols
            return 'BTC'
    
    def detect_hvg_pattern(self, data: pd.DataFrame) -> Optional[GapInfo]:
        """
        Detect H4 HVG pattern in 4-hour data.
        
        Args:
            data: DataFrame with OHLCV and indicators
            
        Returns:
            GapInfo object if pattern detected, None otherwise
        """
        if data.empty or len(data) < 4:
            return None
        
        try:
            # Look for gaps in the last few candles
            for i in range(1, min(self.max_gap_age_candles + 1, len(data))):
                gap_info = self._analyze_gap_at_index(data, -i)
                if gap_info:
                    return gap_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting HVG pattern: {e}")
            return None
    
    def _analyze_gap_at_index(self, data: pd.DataFrame, index: int) -> Optional[GapInfo]:
        """
        Analyze potential gap at specific index.
        
        Args:
            data: DataFrame with OHLCV data
            index: Index to analyze (negative for from end)
            
        Returns:
            GapInfo if valid gap found, None otherwise
        """
        try:
            current_candle = data.iloc[index]
            previous_candle = data.iloc[index - 1]
            
            # Calculate gap
            gap_size = current_candle['open'] - previous_candle['close']
            gap_percent = abs(gap_size) / previous_candle['close'] * 100
            
            # Check if gap meets minimum size requirement
            if gap_percent < self.min_gap_percent:
                return None
            
            # Validate volume spike
            if not self._validate_volume_spike(current_candle):
                return None
            
            # Determine gap direction and levels
            if gap_size > 0:
                # Gap up (bullish)
                gap_direction = "up"
                gap_low = previous_candle['close']
                gap_high = current_candle['open']
            else:
                # Gap down (bearish)
                gap_direction = "down"
                gap_high = previous_candle['close']
                gap_low = current_candle['open']
            
            # Calculate volume ratio
            volume_ratio = current_candle['volume'] / current_candle['volume_ma'] if current_candle['volume_ma'] > 0 else 0
            
            # Calculate candles ago (convert negative index to positive age)
            candles_ago = abs(index) if index < 0 else len(data) - index - 1
            
            gap_info = GapInfo(
                gap_size=abs(gap_size),
                gap_percent=gap_percent,
                gap_direction=gap_direction,
                gap_high=gap_high,
                gap_low=gap_low,
                volume_ratio=volume_ratio,
                candles_ago=candles_ago,
                previous_close=previous_candle['close'],
                gap_open=current_candle['open'],
                timestamp=current_candle['timestamp']
            )
            
            logger.debug(f"Gap detected: {gap_direction} {gap_percent:.2f}% with {volume_ratio:.1f}x volume")
            return gap_info
            
        except Exception as e:
            logger.error(f"Error analyzing gap at index {index}: {e}")
            return None
    
    def _validate_volume_spike(self, candle: pd.Series) -> bool:
        """
        Validate volume spike for the candle.
        
        Args:
            candle: Candle data with volume and volume_ma
            
        Returns:
            True if volume spike is valid, False otherwise
        """
        try:
            if candle['volume_ma'] <= 0:
                return False
            
            volume_ratio = candle['volume'] / candle['volume_ma']
            return volume_ratio >= self.volume_spike_threshold
            
        except Exception as e:
            logger.error(f"Error validating volume spike: {e}")
            return False
    
    def validate_confluence(self, data: pd.DataFrame, gap_info: GapInfo) -> Tuple[bool, List[str], int]:
        """
        Validate confluence factors for the gap pattern.
        
        Args:
            data: DataFrame with indicators
            gap_info: Gap information
            
        Returns:
            Tuple of (is_valid, confluence_factors, confidence_score)
        """
        if data.empty:
            return False, [], 0
        
        try:
            last_candle = data.iloc[-1]
            confluence_factors = []
            confidence_score = 0
            
            # Factor 1: EMA trend confirmation
            if self.require_ema_confluence:
                ema_50 = last_candle.get('ema_50')
                if ema_50 is not None and not pd.isna(ema_50):
                    if gap_info.gap_direction == "up" and last_candle['close'] > ema_50:
                        confluence_factors.append("Bullish EMA trend (price > EMA 50)")
                        confidence_score += 1
                    elif gap_info.gap_direction == "down" and last_candle['close'] < ema_50:
                        confluence_factors.append("Bearish EMA trend (price < EMA 50)")
                        confidence_score += 1
                    else:
                        # EMA confluence required but not met
                        return False, confluence_factors, confidence_score
            
            # Factor 2: RSI range validation
            rsi = last_candle.get('rsi')
            if rsi is not None and not pd.isna(rsi):
                if self.rsi_min <= rsi <= self.rsi_max:
                    confluence_factors.append(f"RSI in healthy range ({rsi:.1f})")
                    confidence_score += 1
                else:
                    # RSI outside acceptable range
                    return False, confluence_factors, confidence_score
            
            # Factor 3: Gap recency
            if gap_info.candles_ago <= self.max_gap_age_candles:
                confluence_factors.append(f"Recent gap ({gap_info.candles_ago} candles ago)")
                confidence_score += 1
            else:
                return False, confluence_factors, confidence_score
            
            # Factor 4: Volume confirmation
            if gap_info.volume_ratio >= self.volume_spike_threshold:
                confluence_factors.append(f"Strong volume ({gap_info.volume_ratio:.1f}x average)")
                confidence_score += 1
            
            # Factor 5: Gap size significance
            if gap_info.gap_percent >= self.min_gap_percent * 1.5:  # 1.5x minimum for extra confidence
                confluence_factors.append(f"Significant gap size ({gap_info.gap_percent:.2f}%)")
                confidence_score += 1
            
            # Minimum confidence required
            is_valid = confidence_score >= 3
            
            return is_valid, confluence_factors, confidence_score
            
        except Exception as e:
            logger.error(f"Error validating confluence: {e}")
            return False, [], 0
    
    def calculate_signal_levels(self, gap_info: GapInfo, current_price: float, atr: float) -> Dict:
        """
        Calculate entry, stop-loss, and take-profit levels.
        
        Args:
            gap_info: Gap information
            current_price: Current market price
            atr: Average True Range value
            
        Returns:
            Dictionary with signal levels and risk-reward ratio
        """
        try:
            entry_price = current_price
            
            if gap_info.gap_direction == "up":
                # LONG signal
                stop_loss = gap_info.gap_low - (atr * self.atr_multiplier_sl)
                take_profit = entry_price + (gap_info.gap_size * self.gap_target_multiplier)
                signal_type = "LONG"
            else:
                # SHORT signal
                stop_loss = gap_info.gap_high + (atr * self.atr_multiplier_sl)
                take_profit = entry_price - (gap_info.gap_size * self.gap_target_multiplier)
                signal_type = "SHORT"
            
            # Calculate risk-reward ratio
            if signal_type == "LONG":
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
            
            risk_reward = reward / risk if risk > 0 else 0
            
            # Validate minimum risk-reward ratio
            if risk_reward < self.min_risk_reward:
                logger.debug(f"Risk-reward ratio {risk_reward:.2f} below minimum {self.min_risk_reward}")
                return None
            
            return {
                'signal_type': signal_type,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward': risk_reward,
                'atr': atr
            }
            
        except Exception as e:
            logger.error(f"Error calculating signal levels: {e}")
            return None
    
    def generate_reasoning(self, gap_info: GapInfo, confluence_factors: List[str], 
                          signal_levels: Dict) -> str:
        """
        Generate detailed reasoning for H4 HVG signal.
        
        Args:
            gap_info: Gap information
            confluence_factors: List of confluence factors
            signal_levels: Signal levels dictionary
            
        Returns:
            Formatted reasoning string
        """
        try:
            reasons = []
            
            # Strategy introduction
            reasons.append("STRATEGY: H4 HVG (4-Hour High Volume Gap)")
            reasons.append("")
            
            # Gap pattern description
            direction_text = "upward" if gap_info.gap_direction == "up" else "downward"
            reasons.append(f"GAP PATTERN DETECTED:")
            reasons.append(f"    Direction: {direction_text.upper()} gap")
            reasons.append(f"    Size: ${gap_info.gap_size:.2f} ({gap_info.gap_percent:.2f}% of previous close)")
            reasons.append(f"    Gap Range: ${gap_info.gap_low:.2f} - ${gap_info.gap_high:.2f}")
            reasons.append(f"    Occurred: {gap_info.candles_ago} candle(s) ago")
            reasons.append("")
            
            # Volume confirmation
            reasons.append(f"VOLUME CONFIRMATION:")
            reasons.append(f"    Volume Spike: {gap_info.volume_ratio:.1f}x average volume")
            reasons.append(f"    Threshold: {self.volume_spike_threshold}x (✓ PASSED)")
            reasons.append(f"    Indicates: Institutional interest and genuine breakout")
            reasons.append("")
            
            # Confluence factors
            reasons.append(f"CONFLUENCE FACTORS ({len(confluence_factors)} confirmed):")
            for i, factor in enumerate(confluence_factors, 1):
                reasons.append(f"    {i}. {factor}")
            reasons.append("")
            
            # Signal logic
            signal_type = signal_levels['signal_type']
            reasons.append(f"SIGNAL LOGIC:")
            if signal_type == "LONG":
                reasons.append(f"    Gap up with volume suggests bullish continuation")
                reasons.append(f"    Entry at current price to catch momentum")
                reasons.append(f"    Stop below gap low protects against false breakout")
                reasons.append(f"    Target based on gap size projection")
            else:
                reasons.append(f"    Gap down with volume suggests bearish continuation")
                reasons.append(f"    Entry at current price to catch momentum")
                reasons.append(f"    Stop above gap high protects against false breakdown")
                reasons.append(f"    Target based on gap size projection")
            reasons.append("")
            
            # Risk management
            reasons.append(f"RISK MANAGEMENT:")
            reasons.append(f"    Entry: ${signal_levels['entry_price']:.2f}")
            reasons.append(f"    Stop Loss: ${signal_levels['stop_loss']:.2f}")
            reasons.append(f"    Take Profit: ${signal_levels['take_profit']:.2f}")
            reasons.append(f"    Risk:Reward = 1:{signal_levels['risk_reward']:.2f}")
            reasons.append("")
            
            # Why enter now
            reasons.append(f"WHY ENTER NOW:")
            reasons.append(f"    ✓ Significant gap ({gap_info.gap_percent:.2f}%) with institutional volume")
            reasons.append(f"    ✓ All confluence factors aligned for high probability setup")
            reasons.append(f"    ✓ Gap provides clear levels for risk management")
            reasons.append(f"    ✓ Early entry captures maximum potential from gap fill/continuation")
            
            return "\n".join(reasons)
            
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return f"H4 HVG {gap_info.gap_direction} signal with {gap_info.gap_percent:.2f}% gap and {gap_info.volume_ratio:.1f}x volume"
    
    def generate_h4_hvg_signal(self, data: pd.DataFrame, timeframe: str, symbol: str) -> Optional['Signal']:
        """
        Generate H4 HVG signal from 4-hour data.
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string (should be '4h')
            symbol: Trading symbol
            
        Returns:
            Signal object if H4 HVG pattern detected, None otherwise
        """
        # Import here to avoid circular imports
        from src.signal_detector import Signal
        
        try:
            # Only process 4-hour timeframe
            if timeframe != '4h':
                return None
            
            # Detect HVG pattern
            gap_info = self.detect_hvg_pattern(data)
            if not gap_info:
                return None
            
            # Validate confluence factors
            is_valid, confluence_factors, confidence_score = self.validate_confluence(data, gap_info)
            if not is_valid:
                logger.debug(f"H4 HVG pattern failed confluence validation")
                return None
            
            # Get current market data
            last_candle = data.iloc[-1]
            current_price = last_candle['close']
            atr = last_candle.get('atr', 0)
            
            if atr <= 0:
                logger.warning("ATR not available or zero, cannot calculate signal levels")
                return None
            
            # Calculate signal levels
            signal_levels = self.calculate_signal_levels(gap_info, current_price, atr)
            if not signal_levels:
                logger.debug("Signal levels calculation failed")
                return None
            
            # Generate reasoning
            reasoning = self.generate_reasoning(gap_info, confluence_factors, signal_levels)
            
            # Determine market bias
            market_bias = "bullish" if gap_info.gap_direction == "up" else "bearish"
            
            # Create indicators snapshot
            indicators = {
                'ema_50': last_candle.get('ema_50'),
                'rsi': last_candle.get('rsi'),
                'atr': atr,
                'volume': last_candle['volume'],
                'volume_ma': last_candle['volume_ma'],
                'gap_size': gap_info.gap_size,
                'gap_percent': gap_info.gap_percent,
                'volume_spike_ratio': gap_info.volume_ratio
            }
            
            # Create Signal object
            signal = Signal(
                timestamp=last_candle['timestamp'],
                signal_type=signal_levels['signal_type'],
                timeframe=timeframe,
                symbol=symbol,
                entry_price=signal_levels['entry_price'],
                stop_loss=signal_levels['stop_loss'],
                take_profit=signal_levels['take_profit'],
                atr=atr,
                risk_reward=signal_levels['risk_reward'],
                market_bias=market_bias,
                confidence=confidence_score,
                indicators=indicators,
                reasoning=reasoning,
                strategy="H4 HVG",
                gap_info=gap_info,
                volume_spike_ratio=gap_info.volume_ratio,
                confluence_factors=confluence_factors
            )
            
            logger.info(f"H4 HVG {signal_levels['signal_type']} signal generated: {gap_info.gap_percent:.2f}% gap with {confidence_score} confluence factors")
            return signal
            
        except Exception as e:
            logger.error(f"Error generating H4 HVG signal: {e}")
            return None
    
    def is_duplicate_signal(self, signal) -> bool:
        """
        Check if signal is a duplicate of recent H4 HVG signal.
        
        Args:
            signal: Signal object to check
            
        Returns:
            True if duplicate, False otherwise
        """
        try:
            # Clean expired signals first
            self._clean_expired_signals()
            
            time_threshold = timedelta(minutes=self.duplicate_time_window_minutes)
            
            for prev_signal in self.signal_history:
                # Check same signal type
                if prev_signal.signal_type != signal.signal_type:
                    continue
                
                # Check same strategy
                if prev_signal.strategy != "H4 HVG":
                    continue
                
                # Check time window
                time_diff = signal.timestamp - prev_signal.timestamp
                if time_diff < time_threshold:
                    # Check price movement
                    price_change_percent = abs(
                        signal.entry_price - prev_signal.entry_price
                    ) / prev_signal.entry_price * 100
                    
                    if price_change_percent < self.duplicate_price_threshold_percent:
                        logger.debug(f"Duplicate H4 HVG signal blocked: {signal.signal_type} within {time_diff.total_seconds()/60:.1f} minutes")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking duplicate signal: {e}")
            return False
    
    def add_signal_to_history(self, signal) -> None:
        """
        Add signal to history for duplicate detection.
        
        Args:
            signal: Signal object to add
        """
        try:
            if signal.strategy == "H4 HVG":
                self.signal_history.append(signal)
                logger.debug(f"Added H4 HVG signal to history: {signal.signal_type} at {signal.entry_price}")
        except Exception as e:
            logger.error(f"Error adding signal to history: {e}")
    
    def _clean_expired_signals(self) -> None:
        """Remove signals older than 24 hours from history."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            # Filter out expired signals
            self.signal_history = deque(
                [s for s in self.signal_history if s.timestamp > cutoff_time],
                maxlen=50
            )
        except Exception as e:
            logger.error(f"Error cleaning expired signals: {e}")