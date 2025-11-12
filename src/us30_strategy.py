"""
US30 Aggressive Momentum Strategy
Catches big directional moves with FVG, structure breaks, and momentum
"""
import logging
from typing import Optional
import pandas as pd
from datetime import datetime

from src.signal_detector import Signal
from src.fvg_detector import FVGDetector
from src.market_structure import MarketStructureAnalyzer
from src.symbol_context import SymbolContext

logger = logging.getLogger(__name__)


class US30Strategy:
    """
    Aggressive momentum strategy for US30 designed to catch big moves
    
    Entry Criteria:
    1. FVG detected OR Structure break (BOS/CHoCH)
    2. Strong momentum (ADX > 25)
    3. Volume confirmation (> 1.2x average)
    4. Price action confirmation (strong candle close)
    
    Exit Strategy:
    - Initial TP: 2.5 ATR (minimum)
    - Trail stop after 1.5 ATR profit
    - Partial exit at 2R, let rest run
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize US30 strategy
        
        Args:
            config: Strategy configuration
        """
        self.config = config or {}
        
        # Get US30-specific settings
        us30_config = self.config.get('us30_strategy', {})
        
        # FVG settings
        self.fvg_detector = FVGDetector(
            min_gap_percent=us30_config.get('min_fvg_percent', 0.05),  # 0.05% minimum gap
            max_lookback=us30_config.get('fvg_lookback', 20)
        )
        
        # Market structure settings
        self.structure_analyzer = MarketStructureAnalyzer(
            swing_lookback=us30_config.get('swing_lookback', 5),
            min_break_percent=us30_config.get('min_break_percent', 0.1)  # 0.1% minimum break
        )
        
        # Entry thresholds
        self.min_adx = us30_config.get('min_adx', 25)
        self.min_volume_ratio = us30_config.get('min_volume_ratio', 1.2)
        self.min_candle_body_percent = us30_config.get('min_candle_body_percent', 60)  # 60% body vs wick
        
        # Exit settings
        self.initial_tp_atr = us30_config.get('initial_tp_atr', 2.5)
        self.stop_loss_atr = us30_config.get('stop_loss_atr', 1.5)
        self.trail_after_atr = us30_config.get('trail_after_atr', 1.5)
        
        logger.info(f"US30Strategy initialized: ADX>{self.min_adx}, Vol>{self.min_volume_ratio}x, TP={self.initial_tp_atr}ATR")
    
    def _determine_hold_period(self, timeframe: str, structure_break, fvg, adx: float, volume_ratio: float) -> tuple:
        """
        Determine if this is a scalp, day trade, or multi-day swing trade
        
        Args:
            timeframe: Current timeframe
            structure_break: Structure break object (if any)
            fvg: FVG object (if any)
            adx: ADX value
            volume_ratio: Volume ratio
            
        Returns:
            Tuple of (hold_type, hold_days, reasoning)
        """
        # Multi-day swing criteria
        is_multi_day = False
        hold_days = 0
        reasons = []
        
        # Factor 1: Higher timeframe (15m+) = longer holds
        if timeframe in ['15m', '1h', '4h', '1d']:
            is_multi_day = True
            hold_days = 2 if timeframe in ['15m', '1h'] else 5
            reasons.append(f"{timeframe} timeframe")
        
        # Factor 2: Strong structure break = continuation potential
        if structure_break and structure_break.strength >= 4:
            is_multi_day = True
            hold_days = max(hold_days, 2)
            reasons.append(f"Strong {structure_break.break_type}")
        
        # Factor 3: Large FVG = big imbalance to fill
        if fvg and fvg.gap_percent >= 0.15:
            is_multi_day = True
            hold_days = max(hold_days, 2)
            reasons.append(f"Large FVG {fvg.gap_percent:.2f}%")
        
        # Factor 4: Very strong momentum (ADX > 35)
        if adx > 35:
            is_multi_day = True
            hold_days = max(hold_days, 3)
            reasons.append(f"Strong trend ADX {adx:.1f}")
        
        # Factor 5: Extreme volume (> 2x) = institutional activity
        if volume_ratio > 2.0:
            is_multi_day = True
            hold_days = max(hold_days, 2)
            reasons.append(f"High volume {volume_ratio:.1f}x")
        
        # Determine hold type
        if is_multi_day:
            if hold_days >= 3:
                hold_type = "SWING (3-5 days)"
            else:
                hold_type = "DAY TRADE (1-2 days)"
        else:
            hold_type = "SCALP (intraday)"
        
        reasoning = " | ".join(reasons) if reasons else "Standard setup"
        
        return hold_type, hold_days, reasoning
    
    def detect_signal(self, data: pd.DataFrame, timeframe: str) -> Optional[Signal]:
        """
        Detect US30 trading signal
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            
        Returns:
            Signal object if detected, None otherwise
        """
        if len(data) < 20:
            return None
        
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check required indicators
            required = ['atr', 'adx', 'volume', 'volume_ma', 'ema_50', 'rsi']
            if not all(ind in last.index for ind in required):
                logger.debug(f"[{timeframe}] Missing required indicators for US30 strategy")
                return None
            
            # Check for NaN values
            if pd.isna(last['atr']) or pd.isna(last['adx']):
                return None
            
            current_price = last['close']
            atr = last['atr']
            
            # 1. Check momentum (ADX)
            if last['adx'] < self.min_adx:
                logger.debug(f"[{timeframe}] ADX too low: {last['adx']:.1f} < {self.min_adx}")
                return None
            
            # 2. Check volume
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < self.min_volume_ratio:
                logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x < {self.min_volume_ratio}x")
                return None
            
            # 3. Check candle strength (body vs wick)
            candle_body = abs(last['close'] - last['open'])
            candle_range = last['high'] - last['low']
            body_percent = (candle_body / candle_range * 100) if candle_range > 0 else 0
            
            if body_percent < self.min_candle_body_percent:
                logger.debug(f"[{timeframe}] Weak candle: {body_percent:.1f}% body < {self.min_candle_body_percent}%")
                return None
            
            # 4. Detect FVG
            fvg = self.fvg_detector.detect_fvg(data)
            
            # 5. Detect structure break
            structure_break = self.structure_analyzer.detect_structure_break(data)
            
            # Need at least one trigger (FVG or structure break)
            if not fvg and not structure_break:
                logger.debug(f"[{timeframe}] No FVG or structure break detected")
                return None
            
            # Determine hold period (scalp vs day trade vs swing)
            hold_type, hold_days, hold_reasoning = self._determine_hold_period(
                timeframe, structure_break, fvg, last['adx'], volume_ratio
            )
            
            # Determine signal direction
            signal_type = None
            confidence = 3
            reasoning_parts = []
            strategy_name = f"US30 Momentum ({hold_type})"
            
            # Bullish signal
            if (fvg and fvg.gap_type == "bullish") or (structure_break and structure_break.direction == "bullish"):
                # Additional confirmation: price above EMA50 or strong bullish candle
                if last['close'] > last['ema_50'] or (last['close'] > last['open'] and body_percent > 70):
                    signal_type = "LONG"
                    
                    if fvg:
                        reasoning_parts.append(f"Bullish FVG {fvg.gap_percent:.2f}%")
                        confidence += 1
                    
                    if structure_break:
                        reasoning_parts.append(f"{structure_break.break_type} (strength {structure_break.strength}/5)")
                        confidence += 1
                    
                    reasoning_parts.append(f"ADX {last['adx']:.1f}")
                    reasoning_parts.append(f"Vol {volume_ratio:.2f}x")
                    reasoning_parts.append(f"Body {body_percent:.0f}%")
                    
                    # Calculate entry/exit levels
                    entry = current_price
                    stop_loss = entry - (atr * self.stop_loss_atr)
                    
                    # Adjust TP based on hold period
                    if hold_days >= 3:
                        # Swing trade: bigger target
                        take_profit = entry + (atr * self.initial_tp_atr * 1.5)  # 3.75 ATR
                    elif hold_days >= 1:
                        # Day trade: standard target
                        take_profit = entry + (atr * self.initial_tp_atr)  # 2.5 ATR
                    else:
                        # Scalp: smaller target
                        take_profit = entry + (atr * self.initial_tp_atr * 0.8)  # 2.0 ATR
                    
                    risk = entry - stop_loss
                    reward = take_profit - entry
                    risk_reward = reward / risk if risk > 0 else 0
                    
                    logger.info(f"[{timeframe}] 🚀 BULLISH US30 SIGNAL ({hold_type}): {', '.join(reasoning_parts)}")
                    logger.info(f"[{timeframe}] Entry: ${entry:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}, R:R: {risk_reward:.2f}")
                    if hold_days > 0:
                        logger.info(f"[{timeframe}] ⏰ Expected hold: {hold_days} days - {hold_reasoning}")
                    
                    signal = Signal(
                        timestamp=last['timestamp'],
                        signal_type=signal_type,
                        timeframe=timeframe,
                        symbol="US30",
                        symbol_context=SymbolContext.from_symbol("US30"),
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        atr=atr,
                        risk_reward=risk_reward,
                        market_bias="bullish",
                        confidence=min(confidence, 5),
                        indicators={
                            'adx': last['adx'],
                            'rsi': last['rsi'],
                            'volume_ratio': volume_ratio,
                            'body_percent': body_percent,
                            'ema_50': last['ema_50']
                        },
                        reasoning=" | ".join(reasoning_parts),
                        strategy=strategy_name,
                        strategy_metadata={
                            'hold_type': hold_type,
                            'hold_days': hold_days,
                            'hold_reasoning': hold_reasoning,
                            'fvg': {
                                'gap_type': fvg.gap_type,
                                'gap_low': fvg.gap_low,
                                'gap_high': fvg.gap_high,
                                'gap_percent': fvg.gap_percent
                            } if fvg else None,
                            'structure_break': {
                                'break_type': structure_break.break_type,
                                'direction': structure_break.direction,
                                'strength': structure_break.strength,
                                'previous_structure': structure_break.previous_structure
                            } if structure_break else None,
                            'trail_after_profit': atr * self.trail_after_atr
                        }
                    )
                    
                    return signal
            
            # Bearish signal
            elif (fvg and fvg.gap_type == "bearish") or (structure_break and structure_break.direction == "bearish"):
                # Additional confirmation: price below EMA50 or strong bearish candle
                if last['close'] < last['ema_50'] or (last['close'] < last['open'] and body_percent > 70):
                    signal_type = "SHORT"
                    
                    if fvg:
                        reasoning_parts.append(f"Bearish FVG {fvg.gap_percent:.2f}%")
                        confidence += 1
                    
                    if structure_break:
                        reasoning_parts.append(f"{structure_break.break_type} (strength {structure_break.strength}/5)")
                        confidence += 1
                    
                    reasoning_parts.append(f"ADX {last['adx']:.1f}")
                    reasoning_parts.append(f"Vol {volume_ratio:.2f}x")
                    reasoning_parts.append(f"Body {body_percent:.0f}%")
                    
                    # Calculate entry/exit levels
                    entry = current_price
                    stop_loss = entry + (atr * self.stop_loss_atr)
                    
                    # Adjust TP based on hold period
                    if hold_days >= 3:
                        # Swing trade: bigger target
                        take_profit = entry - (atr * self.initial_tp_atr * 1.5)  # 3.75 ATR
                    elif hold_days >= 1:
                        # Day trade: standard target
                        take_profit = entry - (atr * self.initial_tp_atr)  # 2.5 ATR
                    else:
                        # Scalp: smaller target
                        take_profit = entry - (atr * self.initial_tp_atr * 0.8)  # 2.0 ATR
                    
                    risk = stop_loss - entry
                    reward = entry - take_profit
                    risk_reward = reward / risk if risk > 0 else 0
                    
                    logger.info(f"[{timeframe}] 🔻 BEARISH US30 SIGNAL ({hold_type}): {', '.join(reasoning_parts)}")
                    logger.info(f"[{timeframe}] Entry: ${entry:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}, R:R: {risk_reward:.2f}")
                    if hold_days > 0:
                        logger.info(f"[{timeframe}] ⏰ Expected hold: {hold_days} days - {hold_reasoning}")
                    
                    signal = Signal(
                        timestamp=last['timestamp'],
                        signal_type=signal_type,
                        timeframe=timeframe,
                        symbol="US30",
                        symbol_context=SymbolContext.from_symbol("US30"),
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        atr=atr,
                        risk_reward=risk_reward,
                        market_bias="bearish",
                        confidence=min(confidence, 5),
                        indicators={
                            'adx': last['adx'],
                            'rsi': last['rsi'],
                            'volume_ratio': volume_ratio,
                            'body_percent': body_percent,
                            'ema_50': last['ema_50']
                        },
                        reasoning=" | ".join(reasoning_parts),
                        strategy=strategy_name,
                        strategy_metadata={
                            'hold_type': hold_type,
                            'hold_days': hold_days,
                            'hold_reasoning': hold_reasoning,
                            'fvg': {
                                'gap_type': fvg.gap_type,
                                'gap_low': fvg.gap_low,
                                'gap_high': fvg.gap_high,
                                'gap_percent': fvg.gap_percent
                            } if fvg else None,
                            'structure_break': {
                                'break_type': structure_break.break_type,
                                'direction': structure_break.direction,
                                'strength': structure_break.strength,
                                'previous_structure': structure_break.previous_structure
                            } if structure_break else None,
                            'trail_after_profit': atr * self.trail_after_atr
                        }
                    )
                    
                    return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in US30 strategy: {e}", exc_info=True)
            return None
