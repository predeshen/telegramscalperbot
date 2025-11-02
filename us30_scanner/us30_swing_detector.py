"""
US30 Swing Trading Signal Detector
Implements "Trend Reversal & Continuation" and "Moving Average Pullback" strategies
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
class US30SwingSignal(Signal):
    """Extended signal class for US30 swing trading."""
    strategy: str = ""
    macd_histogram: Optional[float] = None
    ema_200_distance: Optional[float] = None


class US30SwingDetector:
    """
    Detects swing trading signals for US30 (Dow Jones).
    
    Strategies:
    1. Trend Continuation Pullback - Enters on pullbacks in strong trends
    2. Major Trend Reversal - Catches trend changes with EMA crosses
    """
    
    def __init__(self, config: dict):
        """
        Initialize US30 Swing Detector.
        
        Args:
            config: Configuration dictionary with signal rules
        """
        self.config = config
        
        # Signal history for duplicate prevention
        self.recent_signals = []
        self.duplicate_window_minutes = config.get('duplicate_time_window_minutes', 240)
        
        logger.info("US30SwingDetector initialized")
    
    def detect_signals(self, data: pd.DataFrame, timeframe: str) -> Optional[US30SwingSignal]:
        """
        Detect swing trading signals.
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            
        Returns:
            US30SwingSignal if detected, None otherwise
        """
        if data.empty or len(data) < 200:  # Need more history for swing
            return None
        
        # Try trend continuation first (safer)
        signal = self._detect_trend_continuation(data, timeframe)
        
        if not signal:
            # Try trend reversal (higher risk/reward)
            signal = self._detect_trend_reversal(data, timeframe)
        
        # Check for duplicates
        if signal and not self._is_duplicate(signal):
            self.recent_signals.append(signal)
            logger.info(f"🎯 {signal.signal_type} signal: {signal.strategy} on {timeframe}")
            return signal
        
        return None
    
    def _detect_trend_continuation(self, data: pd.DataFrame, timeframe: str) -> Optional[US30SwingSignal]:
        """
        Detect Trend Continuation Pullback signals.
        
        Strategy:
        1. Price above/below EMA 200 (primary trend)
        2. Pullback to EMA 50 or key support/resistance
        3. MACD shows momentum loss then recovery
        4. Strong confirmation candle
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            
        Returns:
            US30SwingSignal if detected
        """
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check volume
            if last['volume'] < last['volume_ma'] * self.config['volume_spike_threshold']:
                return None
            
            # Bullish Trend Continuation
            if last['close'] > last['ema_200']:  # Above 200 EMA = bullish environment
                
                # Check if near EMA 50 (pullback zone)
                distance_to_ema50 = abs(last['close'] - last['ema_50']) / last['close']
                
                if distance_to_ema50 < 0.01:  # Within 1% of EMA 50
                    
                    # Check MACD for momentum recovery
                    if 'macd_histogram' in last:
                        # MACD histogram should be turning positive or increasing
                        if last['macd_histogram'] > prev['macd_histogram'] and last['macd_histogram'] > -50:
                            
                            # RSI confirmation
                            if last['rsi'] > 50:
                                
                                # Strong bullish candle
                                if last['close'] > last['open'] and (last['close'] - last['open']) > last['atr'] * 0.5:
                                    
                                    entry = last['close']
                                    stop_loss = entry - (last['atr'] * self.config['stop_loss_atr_multiplier'])
                                    take_profit = entry + (last['atr'] * self.config['take_profit_atr_multiplier'])
                                    
                                    signal = self._create_signal(
                                        timestamp=last['timestamp'],
                                        signal_type="LONG",
                                        timeframe=timeframe,
                                        entry_price=entry,
                                        stop_loss=stop_loss,
                                        take_profit=take_profit,
                                        indicators=last,
                                        strategy="Trend Continuation (Bullish)"
                                    )
                                    
                                    return signal
            
            # Bearish Trend Continuation
            elif last['close'] < last['ema_200']:  # Below 200 EMA = bearish environment
                
                # Check if near EMA 50 (pullback zone)
                distance_to_ema50 = abs(last['close'] - last['ema_50']) / last['close']
                
                if distance_to_ema50 < 0.01:  # Within 1% of EMA 50
                    
                    # Check MACD for momentum recovery
                    if 'macd_histogram' in last:
                        # MACD histogram should be turning negative or decreasing
                        if last['macd_histogram'] < prev['macd_histogram'] and last['macd_histogram'] < 50:
                            
                            # RSI confirmation
                            if last['rsi'] < 50:
                                
                                # Strong bearish candle
                                if last['close'] < last['open'] and (last['open'] - last['close']) > last['atr'] * 0.5:
                                    
                                    entry = last['close']
                                    stop_loss = entry + (last['atr'] * self.config['stop_loss_atr_multiplier'])
                                    take_profit = entry - (last['atr'] * self.config['take_profit_atr_multiplier'])
                                    
                                    signal = self._create_signal(
                                        timestamp=last['timestamp'],
                                        signal_type="SHORT",
                                        timeframe=timeframe,
                                        entry_price=entry,
                                        stop_loss=stop_loss,
                                        take_profit=take_profit,
                                        indicators=last,
                                        strategy="Trend Continuation (Bearish)"
                                    )
                                    
                                    return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in trend continuation detection: {e}")
            return None
    
    def _detect_trend_reversal(self, data: pd.DataFrame, timeframe: str) -> Optional[US30SwingSignal]:
        """
        Detect Major Trend Reversal signals.
        
        Strategy:
        1. EMA 50 crosses EMA 200 (Golden/Death Cross)
        2. MACD confirms with strong crossover
        3. Price breaks key trendline
        4. Volume surge
        
        Args:
            data: DataFrame with indicators
            timeframe: Timeframe string
            
        Returns:
            US30SwingSignal if detected
        """
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            prev2 = data.iloc[-3] if len(data) >= 3 else None
            
            if prev2 is None:
                return None
            
            # Check for Golden Cross (Bullish Reversal)
            if (prev['ema_50'] <= prev['ema_200'] and  # Was below
                last['ema_50'] > last['ema_200']):  # Now above
                
                # MACD confirmation
                if 'macd' in last and 'macd_signal' in last:
                    if last['macd'] > last['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                        
                        # Volume surge
                        if last['volume'] > last['volume_ma'] * 1.5:
                            
                            entry = last['close']
                            stop_loss = entry - (last['atr'] * self.config['stop_loss_atr_multiplier'])
                            take_profit = entry + (last['atr'] * self.config['take_profit_atr_multiplier'] * 1.5)  # Bigger target for reversal
                            
                            signal = self._create_signal(
                                timestamp=last['timestamp'],
                                signal_type="LONG",
                                timeframe=timeframe,
                                entry_price=entry,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                indicators=last,
                                strategy="Major Trend Reversal (Golden Cross)"
                            )
                            
                            return signal
            
            # Check for Death Cross (Bearish Reversal)
            elif (prev['ema_50'] >= prev['ema_200'] and  # Was above
                  last['ema_50'] < last['ema_200']):  # Now below
                
                # MACD confirmation
                if 'macd' in last and 'macd_signal' in last:
                    if last['macd'] < last['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                        
                        # Volume surge
                        if last['volume'] > last['volume_ma'] * 1.5:
                            
                            entry = last['close']
                            stop_loss = entry + (last['atr'] * self.config['stop_loss_atr_multiplier'])
                            take_profit = entry - (last['atr'] * self.config['take_profit_atr_multiplier'] * 1.5)
                            
                            signal = self._create_signal(
                                timestamp=last['timestamp'],
                                signal_type="SHORT",
                                timeframe=timeframe,
                                entry_price=entry,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                indicators=last,
                                strategy="Major Trend Reversal (Death Cross)"
                            )
                            
                            return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in trend reversal detection: {e}")
            return None
    
    def _create_signal(self, timestamp: datetime, signal_type: str, timeframe: str,
                      entry_price: float, stop_loss: float, take_profit: float,
                      indicators: pd.Series, strategy: str) -> US30SwingSignal:
        """Create a US30SwingSignal with full context."""
        risk_reward = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
        
        # Get market bias
        if indicators['close'] > indicators['ema_200']:
            market_bias = "bullish"
        elif indicators['close'] < indicators['ema_200']:
            market_bias = "bearish"
        else:
            market_bias = "neutral"
        
        # Calculate EMA 200 distance
        ema_200_distance = ((indicators['close'] - indicators['ema_200']) / indicators['ema_200']) * 100
        
        # Generate reasoning
        reasoning = self._generate_reasoning(signal_type, indicators, strategy, market_bias, ema_200_distance)
        
        signal = US30SwingSignal(
            timestamp=timestamp,
            signal_type=signal_type,
            timeframe=timeframe,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            atr=indicators['atr'],
            risk_reward=risk_reward,
            market_bias=market_bias,
            confidence=4,
            indicators={
                'ema_50': indicators['ema_50'],
                'ema_200': indicators['ema_200'],
                'macd': indicators.get('macd'),
                'macd_signal': indicators.get('macd_signal'),
                'macd_histogram': indicators.get('macd_histogram'),
                'rsi': indicators['rsi'],
                'volume': indicators['volume'],
                'volume_ma': indicators['volume_ma']
            },
            reasoning=reasoning,
            strategy=strategy,
            macd_histogram=indicators.get('macd_histogram'),
            ema_200_distance=ema_200_distance
        )
        
        return signal
    
    def _generate_reasoning(self, signal_type: str, indicators: pd.Series,
                           strategy: str, market_bias: str, ema_200_distance: float) -> str:
        """Generate detailed reasoning for US30 swing signal."""
        reasons = []
        
        reasons.append(f"🎯 STRATEGY: {strategy}")
        reasons.append(f"📊 US30 SWING TRADING SETUP")
        
        # Primary trend
        if signal_type == "LONG":
            reasons.append(f"📈 BULLISH ENVIRONMENT: Price {ema_200_distance:+.2f}% from EMA 200")
            reasons.append(f"   • Above 200 EMA - Primary uptrend intact")
        else:
            reasons.append(f"📉 BEARISH ENVIRONMENT: Price {ema_200_distance:+.2f}% from EMA 200")
            reasons.append(f"   • Below 200 EMA - Primary downtrend intact")
        
        # MACD
        if 'macd_histogram' in indicators:
            macd_hist = indicators['macd_histogram']
            if macd_hist > 0:
                reasons.append(f"⚡ MACD: Histogram +{macd_hist:.1f} - Bullish momentum")
            else:
                reasons.append(f"⚡ MACD: Histogram {macd_hist:.1f} - Bearish momentum")
        
        # RSI
        reasons.append(f"📊 RSI: {indicators['rsi']:.1f} - {'Bullish' if indicators['rsi'] > 50 else 'Bearish'} momentum")
        
        # Volume
        volume_ratio = indicators['volume'] / indicators['volume_ma']
        reasons.append(f"📊 VOLUME: {volume_ratio:.2f}x average - Strong institutional participation")
        
        # Why enter NOW
        reasons.append(f"\n💡 SWING TRADE EDGE:")
        reasons.append(f"   • {strategy} confirmed on {indicators.name if hasattr(indicators, 'name') else 'higher'} timeframe")
        reasons.append(f"   • Multi-day hold potential")
        reasons.append(f"   • Target: {self.config['take_profit_atr_multiplier']}x ATR")
        reasons.append(f"   • Risk/Reward: {abs(indicators['atr'] * self.config['take_profit_atr_multiplier']) / abs(indicators['atr'] * self.config['stop_loss_atr_multiplier']):.2f}:1")
        
        return "\n".join(reasons)
    
    def _is_duplicate(self, signal: US30SwingSignal) -> bool:
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
