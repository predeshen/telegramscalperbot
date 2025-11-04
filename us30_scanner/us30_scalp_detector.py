"""
US30 Scalping Signal Detector
Implements "Liquidity Sweep + Impulse Confirmation" and "Trend Pullback" strategies
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict
import pandas as pd
import numpy as np
import logging

from src.signal_detector import Signal

logger = logging.getLogger(__name__)


@dataclass
class US30ScalpSignal(Signal):
    """Extended signal class for US30 scalping."""
    strategy: str = ""
    stochastic_value: Optional[float] = None
    vwap_distance: Optional[float] = None


class US30ScalpDetector:
    """
    Detects scalping signals for US30 (Dow Jones).
    
    Strategies:
    1. Liquidity Sweep + Impulse - Catches post-sweep momentum
    2. Trend Pullback - Enters on pullbacks to dynamic support/resistance
    """
    
    def __init__(self, config: dict):
        """
        Initialize US30 Scalp Detector.
        
        Args:
            config: Configuration dictionary with signal rules
        """
        self.config = config
        
        # Signal history for duplicate prevention
        self.recent_signals = []
        self.duplicate_window_minutes = config.get('duplicate_time_window_minutes', 15)
        
        logger.info("US30ScalpDetector initialized")
    
    def detect_signals(self, data: pd.DataFrame, timeframe: str) -> Optional[US30ScalpSignal]:
        """
        Detect scalping signals.
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            
        Returns:
            US30ScalpSignal if detected, None otherwise
        """
        if data.empty or len(data) < 50:
            return None
        
        # Try momentum shift first (catches RSI turning with ADX > 18)
        signal = self._detect_momentum_shift(data, timeframe)
        
        if not signal:
            # Try liquidity sweep strategy
            signal = self._detect_liquidity_sweep(data, timeframe)
        
        if not signal:
            # Try trend pullback strategy
            signal = self._detect_trend_pullback(data, timeframe)
        
        # Check for duplicates
        if signal and not self._is_duplicate(signal):
            self.recent_signals.append(signal)
            logger.info(f"🎯 {signal.signal_type} signal: {signal.strategy} on {timeframe}")
            return signal
        
        return None
    
    def _detect_momentum_shift(self, data: pd.DataFrame, timeframe: str) -> Optional[US30ScalpSignal]:
        """
        Detect Momentum Shift signals - catches RSI turning with building momentum.
        
        Strategy (matches manual trading approach):
        - Bullish: RSI turning up (increasing over last 2-3 candles)
        - Bearish: RSI turning down (decreasing over last 2-3 candles)
        - ADX > 18 (trend forming, not flat)
        - Volume >= 1.5x average (scalping needs strong volume)
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            
        Returns:
            US30ScalpSignal if detected, None otherwise
        """
        try:
            if len(data) < 4:
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            prev2 = data.iloc[-3]
            
            # Check for required indicators (use RSI(7) for faster momentum detection)
            required_indicators = ['rsi_7', 'volume', 'volume_ma', 'atr', 'adx']
            if not all(ind in last.index for ind in required_indicators):
                logger.debug(f"[{timeframe}] Missing required indicators for momentum shift detection")
                return None
            
            # Check ADX > 18 (trend forming)
            if last['adx'] < 18:
                logger.debug(f"[{timeframe}] ADX too low: {last['adx']:.1f} (need >= 18 for momentum shift)")
                return None
            
            # Calculate volume ratio
            volume_ratio = last['volume'] / last['volume_ma']
            
            # Check volume threshold (1.5x for scalping)
            if volume_ratio < self.config.get('volume_spike_threshold', 1.5):
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= {self.config.get('volume_spike_threshold', 1.5)}x)")
                return None
            
            # Check for RSI(7) turning up (bullish momentum shift)
            rsi_7_current = last['rsi_7']
            rsi_7_prev = prev['rsi_7']
            rsi_7_prev2 = prev2['rsi_7']
            
            # Bullish Momentum Shift: RSI(7) turning up
            if rsi_7_current > rsi_7_prev and rsi_7_prev > rsi_7_prev2:
                logger.info(f"[{timeframe}] Bullish momentum shift detected - RSI(7): {rsi_7_prev2:.1f} -> {rsi_7_prev:.1f} -> {rsi_7_current:.1f} (turning up)")
                logger.info(f"[{timeframe}] ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry - self.config['stop_loss_points']
                take_profit = entry + self.config['take_profit_points_quick']
                
                signal = self._create_signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    indicators=last,
                    strategy="Momentum Shift (Bullish)"
                )
                
                return signal
            
            # Bearish Momentum Shift: RSI(7) turning down
            elif rsi_7_current < rsi_7_prev and rsi_7_prev < rsi_7_prev2:
                logger.info(f"[{timeframe}] Bearish momentum shift detected - RSI(7): {rsi_7_prev2:.1f} -> {rsi_7_prev:.1f} -> {rsi_7_current:.1f} (turning down)")
                logger.info(f"[{timeframe}] ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry + self.config['stop_loss_points']
                take_profit = entry - self.config['take_profit_points_quick']
                
                signal = self._create_signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    indicators=last,
                    strategy="Momentum Shift (Bearish)"
                )
                
                return signal
            
            else:
                logger.debug(f"[{timeframe}] No momentum shift: RSI(7) {rsi_7_prev2:.1f} -> {rsi_7_prev:.1f} -> {rsi_7_current:.1f}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in momentum shift detection: {e}", exc_info=True)
            return None
    
    def _detect_liquidity_sweep(self, data: pd.DataFrame, timeframe: str) -> Optional[US30ScalpSignal]:
        """
        Detect Liquidity Sweep + Impulse signals.
        
        Strategy:
        1. Price sweeps below recent low (or above recent high)
        2. Forms rejection candle with high volume
        3. Closes back above/below VWAP
        4. EMA alignment confirms
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            
        Returns:
            US30ScalpSignal if detected
        """
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            prev2 = data.iloc[-3] if len(data) >= 3 else None
            
            if prev2 is None:
                return None
            
            # Calculate recent swing points (last 15 bars)
            lookback = min(15, len(data) - 1)
            recent_data = data.iloc[-lookback-1:-1]
            recent_low = recent_data['low'].min()
            recent_high = recent_data['high'].max()
            
            # Check volume spike
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < self.config['volume_spike_threshold']:
                return None
            
            # Bullish Liquidity Sweep
            if (prev['low'] < recent_low and  # Swept below recent low
                last['close'] > last['open'] and  # Bullish candle
                last['close'] > last['vwap'] and  # Above VWAP
                last['ema_8'] > last['ema_21']):  # EMA alignment
                
                entry = last['close']
                stop_loss = entry - self.config['stop_loss_points']
                take_profit = entry + self.config['take_profit_points_quick']
                
                signal = self._create_signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    indicators=last,
                    strategy="Liquidity Sweep (Bullish)"
                )
                
                return signal
            
            # Bearish Liquidity Sweep
            elif (prev['high'] > recent_high and  # Swept above recent high
                  last['close'] < last['open'] and  # Bearish candle
                  last['close'] < last['vwap'] and  # Below VWAP
                  last['ema_8'] < last['ema_21']):  # EMA alignment
                
                entry = last['close']
                stop_loss = entry + self.config['stop_loss_points']
                take_profit = entry - self.config['take_profit_points_quick']
                
                signal = self._create_signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    indicators=last,
                    strategy="Liquidity Sweep (Bearish)"
                )
                
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in liquidity sweep detection: {e}")
            return None
    
    def _detect_trend_pullback(self, data: pd.DataFrame, timeframe: str) -> Optional[US30ScalpSignal]:
        """
        Detect Trend Pullback signals.
        
        Strategy:
        1. Identify trend (EMA 8 > 21 > 50 for uptrend)
        2. Wait for pullback to EMA 21 or VWAP
        3. Stochastic shows oversold/overbought and hooks back
        4. Enter on confirmation candle
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            
        Returns:
            US30ScalpSignal if detected
        """
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check volume
            if last['volume'] < last['volume_ma']:
                return None
            
            # Bullish Trend Pullback
            if (last['close'] > last['ema_21'] > last['ema_50'] and  # Uptrend
                last['ema_8'] > last['ema_21'] and  # Momentum
                abs(last['close'] - last['ema_21']) / last['close'] < 0.002):  # Near EMA 21
                
                # Check stochastic
                if 'stoch_k' in last and last['stoch_k'] < self.config['stoch_oversold']:
                    # Check for hook up
                    if prev['stoch_k'] < last['stoch_k']:  # Hooking up
                        
                        # Bullish confirmation candle
                        if last['close'] > last['open']:
                            entry = last['close']
                            stop_loss = entry - self.config['stop_loss_points']
                            take_profit = entry + self.config['take_profit_points_extended']
                            
                            signal = self._create_signal(
                                timestamp=last['timestamp'],
                                signal_type="LONG",
                                timeframe=timeframe,
                                entry_price=entry,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                indicators=last,
                                strategy="Trend Pullback (Bullish)"
                            )
                            
                            return signal
            
            # Bearish Trend Pullback
            elif (last['close'] < last['ema_21'] < last['ema_50'] and  # Downtrend
                  last['ema_8'] < last['ema_21'] and  # Momentum
                  abs(last['close'] - last['ema_21']) / last['close'] < 0.002):  # Near EMA 21
                
                # Check stochastic
                if 'stoch_k' in last and last['stoch_k'] > self.config['stoch_overbought']:
                    # Check for hook down
                    if prev['stoch_k'] > last['stoch_k']:  # Hooking down
                        
                        # Bearish confirmation candle
                        if last['close'] < last['open']:
                            entry = last['close']
                            stop_loss = entry + self.config['stop_loss_points']
                            take_profit = entry - self.config['take_profit_points_extended']
                            
                            signal = self._create_signal(
                                timestamp=last['timestamp'],
                                signal_type="SHORT",
                                timeframe=timeframe,
                                entry_price=entry,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                indicators=last,
                                strategy="Trend Pullback (Bearish)"
                            )
                            
                            return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in trend pullback detection: {e}")
            return None
    
    def _create_signal(self, timestamp: datetime, signal_type: str, timeframe: str,
                      entry_price: float, stop_loss: float, take_profit: float,
                      indicators: pd.Series, strategy: str) -> US30ScalpSignal:
        """Create a US30ScalpSignal with full context."""
        risk_reward = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
        
        # Get market bias
        if indicators['ema_8'] > indicators['ema_21'] > indicators['ema_50']:
            market_bias = "strong bullish"
        elif indicators['ema_8'] > indicators['ema_21']:
            market_bias = "bullish"
        elif indicators['ema_8'] < indicators['ema_21'] < indicators['ema_50']:
            market_bias = "strong bearish"
        elif indicators['ema_8'] < indicators['ema_21']:
            market_bias = "bearish"
        else:
            market_bias = "neutral"
        
        # Calculate VWAP distance
        vwap_distance = ((indicators['close'] - indicators['vwap']) / indicators['vwap']) * 100
        
        # Generate reasoning
        reasoning = self._generate_reasoning(signal_type, indicators, strategy, market_bias, vwap_distance)
        
        signal = US30ScalpSignal(
            timestamp=timestamp,
            signal_type=signal_type,
            timeframe=timeframe,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            atr=indicators.get('atr', 0),
            risk_reward=risk_reward,
            market_bias=market_bias,
            confidence=4,
            indicators={
                'ema_8': indicators.get('ema_8'),
                'ema_21': indicators.get('ema_21'),
                'ema_50': indicators.get('ema_50'),
                'vwap': indicators['vwap'],
                'rsi': indicators.get('rsi'),
                'stoch_k': indicators.get('stoch_k'),
                'volume': indicators['volume'],
                'volume_ma': indicators['volume_ma']
            },
            reasoning=reasoning,
            strategy=strategy,
            stochastic_value=indicators.get('stoch_k'),
            vwap_distance=vwap_distance
        )
        
        return signal
    
    def _generate_reasoning(self, signal_type: str, indicators: pd.Series,
                           strategy: str, market_bias: str, vwap_distance: float) -> str:
        """Generate detailed reasoning for US30 scalp signal."""
        reasons = []
        
        reasons.append(f"🎯 STRATEGY: {strategy}")
        reasons.append(f"📊 US30 SCALPING SETUP")
        
        # Market structure
        if signal_type == "LONG":
            reasons.append(f"📈 BULLISH MOMENTUM: Price above VWAP (+{vwap_distance:.2f}%)")
            reasons.append(f"   • EMA 8 > EMA 21 - Short-term momentum strong")
        else:
            reasons.append(f"📉 BEARISH MOMENTUM: Price below VWAP ({vwap_distance:.2f}%)")
            reasons.append(f"   • EMA 8 < EMA 21 - Short-term momentum weak")
        
        # Volume confirmation
        volume_ratio = indicators['volume'] / indicators['volume_ma']
        reasons.append(f"📊 VOLUME: {volume_ratio:.2f}x average - {('Strong' if volume_ratio > 1.5 else 'Moderate')} participation")
        
        # Stochastic
        if 'stoch_k' in indicators:
            stoch = indicators['stoch_k']
            if stoch < 20:
                reasons.append(f"⚡ STOCHASTIC: {stoch:.1f} - Oversold, ready for bounce")
            elif stoch > 80:
                reasons.append(f"⚡ STOCHASTIC: {stoch:.1f} - Overbought, ready for reversal")
            else:
                reasons.append(f"⚡ STOCHASTIC: {stoch:.1f} - Momentum confirmed")
        
        # Why enter NOW
        reasons.append(f"\n💡 SCALPING EDGE:")
        reasons.append(f"   • {strategy} pattern fully formed")
        reasons.append(f"   • Volume confirms institutional participation")
        reasons.append(f"   • Quick profit target: {self.config['take_profit_points_quick']} points")
        reasons.append(f"   • Tight stop: {self.config['stop_loss_points']} points")
        
        return "\n".join(reasons)
    
    def _is_duplicate(self, signal: US30ScalpSignal) -> bool:
        """Check if signal is duplicate of recent signal."""
        cutoff_time = signal.timestamp - timedelta(minutes=self.duplicate_window_minutes)
        
        for prev_signal in self.recent_signals:
            if prev_signal.timestamp < cutoff_time:
                continue
            
            if prev_signal.signal_type != signal.signal_type:
                continue
            
            price_diff_pct = abs(signal.entry_price - prev_signal.entry_price) / prev_signal.entry_price * 100
            if price_diff_pct < self.config['duplicate_price_threshold_percent']:
                logger.debug(f"Duplicate signal blocked: {signal.signal_type}")
                return True
        
        return False
