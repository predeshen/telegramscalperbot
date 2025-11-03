"""
Strategy Selector for Gold Trading
Selects appropriate strategy based on session and market conditions
"""
from enum import Enum
from typing import Optional
import pandas as pd
import logging

from xauusd_scanner.session_manager import SessionManager, TradingSession
from src.trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class GoldStrategy(Enum):
    """Available trading strategies for Gold."""
    ASIAN_RANGE_BREAKOUT = "Asian Range Breakout"
    EMA_CLOUD_BREAKOUT = "EMA Cloud Breakout"
    MEAN_REVERSION = "Mean Reversion"
    TREND_FOLLOWING = "Trend Following"
    NO_TRADE = "No Trade"


class StrategySelector:
    """
    Selects the most appropriate trading strategy based on:
    - Current trading session
    - Market conditions
    - Price action
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize Strategy Selector.
        
        Args:
            session_manager: SessionManager instance for session detection
        """
        self.session_manager = session_manager
        logger.info("StrategySelector initialized")
    
    def select_strategy(self, data: pd.DataFrame, current_session: Optional[TradingSession] = None) -> GoldStrategy:
        """
        Select the best strategy for current conditions.
        
        Args:
            data: DataFrame with OHLCV and indicators
            current_session: Optional current session (will detect if not provided)
            
        Returns:
            GoldStrategy enum value
        """
        if data.empty or len(data) < 50:
            return GoldStrategy.NO_TRADE
        
        # Get current session
        if current_session is None:
            current_session = self.session_manager.get_current_session()
        
        # No trading during closed session
        if current_session == TradingSession.CLOSED:
            return GoldStrategy.NO_TRADE
        
        last = data.iloc[-1]
        
        # Priority 1: Trend Following (during strong trending markets in London/NY)
        if current_session in [TradingSession.LONDON, TradingSession.NEW_YORK, TradingSession.OVERLAP_LONDON_NY]:
            if self._is_strong_trend(data):
                logger.debug("Selected: Trend Following")
                return GoldStrategy.TREND_FOLLOWING
        
        # Priority 2: Asian Range Breakout (during London open)
        if current_session in [TradingSession.LONDON, TradingSession.OVERLAP_LONDON_NY]:
            asian_range = self.session_manager.get_asian_range()
            
            if asian_range and not asian_range['is_tracking']:
                # Asian range is finalized, look for breakouts
                if self._is_range_breakout_setup(data, asian_range):
                    logger.debug("Selected: Asian Range Breakout")
                    return GoldStrategy.ASIAN_RANGE_BREAKOUT
        
        # Priority 3: Mean Reversion (when overextended)
        if self._is_overextended(data):
            logger.debug("Selected: Mean Reversion")
            return GoldStrategy.MEAN_REVERSION
        
        # Priority 4: EMA Cloud Breakout (default for active sessions)
        if current_session in [TradingSession.LONDON, TradingSession.NEW_YORK, TradingSession.OVERLAP_LONDON_NY]:
            if self._is_trending_market(data):
                logger.debug("Selected: EMA Cloud Breakout")
                return GoldStrategy.EMA_CLOUD_BREAKOUT
        
        # During Asian session, reduce trading (range-bound)
        if current_session == TradingSession.ASIAN:
            # Only trade clear setups during Asian
            if self._is_very_strong_setup(data):
                return GoldStrategy.EMA_CLOUD_BREAKOUT
            return GoldStrategy.NO_TRADE
        
        # Default to EMA Cloud for active sessions
        return GoldStrategy.EMA_CLOUD_BREAKOUT
    
    def _is_strong_trend(self, data: pd.DataFrame) -> bool:
        """
        Check if market is in a strong trend (good for Trend Following).
        
        Args:
            data: DataFrame with indicators
            
        Returns:
            True if strong trend detected
        """
        try:
            if len(data) < 50:
                return False
            
            # Detect swing points
            swing_data = TrendAnalyzer.detect_swing_points(data, lookback=5)
            
            # Check for uptrend or downtrend with at least 3 swing points
            is_uptrend = TrendAnalyzer.is_uptrend(swing_data, min_swings=3)
            is_downtrend = TrendAnalyzer.is_downtrend(swing_data, min_swings=3)
            
            if not (is_uptrend or is_downtrend):
                return False
            
            # Verify EMA alignment
            trend_direction = "uptrend" if is_uptrend else "downtrend"
            if not TrendAnalyzer.is_ema_aligned(data, trend_direction):
                return False
            
            # Check not consolidating
            if TrendAnalyzer.is_consolidating(data, periods=3):
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking strong trend: {e}")
            return False
    
    def _is_range_breakout_setup(self, data: pd.DataFrame, asian_range: dict) -> bool:
        """
        Check if conditions favor Asian range breakout.
        
        Args:
            data: DataFrame with price data
            asian_range: Asian range dictionary
            
        Returns:
            True if breakout setup detected
        """
        last = data.iloc[-1]
        current_price = last['close']
        
        # Check if price has broken out of Asian range
        is_above = self.session_manager.is_breakout_above_asian_range(current_price, buffer_pips=2.0)
        is_below = self.session_manager.is_breakout_below_asian_range(current_price, buffer_pips=2.0)
        
        return is_above or is_below
    
    def _is_overextended(self, data: pd.DataFrame) -> bool:
        """
        Check if price is overextended from VWAP (mean reversion opportunity).
        
        Args:
            data: DataFrame with indicators
            
        Returns:
            True if overextended
        """
        try:
            last = data.iloc[-1]
            
            # Check distance from VWAP
            distance_from_vwap = abs(last['close'] - last['vwap'])
            atr = last['atr']
            
            # Overextended if > 1.5x ATR from VWAP
            if distance_from_vwap > (atr * 1.5):
                # Also check RSI extremes
                if last['rsi'] > 75 or last['rsi'] < 25:
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking overextension: {e}")
            return False
    
    def _is_trending_market(self, data: pd.DataFrame) -> bool:
        """
        Check if market is in a trending state (good for EMA Cloud).
        
        Args:
            data: DataFrame with indicators
            
        Returns:
            True if trending
        """
        try:
            last = data.iloc[-1]
            
            # Check EMA alignment
            ema_20 = last.get('ema_20', last.get('ema_21'))  # Fallback to ema_21
            ema_50 = last['ema_50']
            
            # Trending if EMAs are separated
            ema_separation = abs(ema_20 - ema_50)
            atr = last['atr']
            
            # EMAs should be at least 0.5x ATR apart for trending
            return ema_separation > (atr * 0.5)
        
        except Exception as e:
            logger.error(f"Error checking trend: {e}")
            return True  # Default to allowing EMA Cloud
    
    def _is_very_strong_setup(self, data: pd.DataFrame) -> bool:
        """
        Check for very strong setup (for Asian session trading).
        
        Args:
            data: DataFrame with indicators
            
        Returns:
            True if very strong setup
        """
        try:
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Require strong volume
            if last['volume'] < (last['volume_ma'] * 2.0):
                return False
            
            # Require clear EMA alignment
            if not (last['ema_9'] > last['ema_21'] > last['ema_50'] or
                   last['ema_9'] < last['ema_21'] < last['ema_50']):
                return False
            
            # Require RSI in good range
            if last['rsi'] < 35 or last['rsi'] > 65:
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking strong setup: {e}")
            return False
    
    def get_strategy_description(self, strategy: GoldStrategy) -> str:
        """
        Get description of strategy.
        
        Args:
            strategy: GoldStrategy enum
            
        Returns:
            Strategy description
        """
        descriptions = {
            GoldStrategy.ASIAN_RANGE_BREAKOUT: "Trading breakout of Asian session range with re-test confirmation",
            GoldStrategy.EMA_CLOUD_BREAKOUT: "Trading EMA cloud breakouts with VWAP and volume confirmation",
            GoldStrategy.MEAN_REVERSION: "Trading reversals when price is overextended from VWAP",
            GoldStrategy.TREND_FOLLOWING: "Trading pullbacks within established trends with swing point confirmation",
            GoldStrategy.NO_TRADE: "No trading - waiting for better conditions"
        }
        
        return descriptions.get(strategy, "Unknown strategy")
    
    def get_strategy_parameters(self, strategy: GoldStrategy) -> dict:
        """
        Get recommended parameters for strategy.
        
        Args:
            strategy: GoldStrategy enum
            
        Returns:
            Dictionary with strategy parameters
        """
        parameters = {
            GoldStrategy.ASIAN_RANGE_BREAKOUT: {
                'stop_loss_atr_multiplier': 1.0,  # Tight stop at range boundary
                'take_profit_atr_multiplier': 1.5,
                'volume_threshold': 1.2,
                'requires_retest': True
            },
            GoldStrategy.EMA_CLOUD_BREAKOUT: {
                'stop_loss_atr_multiplier': 1.2,
                'take_profit_atr_multiplier': 1.5,
                'volume_threshold': 1.5,
                'requires_retest': False
            },
            GoldStrategy.MEAN_REVERSION: {
                'stop_loss_atr_multiplier': 1.0,
                'take_profit_atr_multiplier': 1.0,  # Target VWAP
                'volume_threshold': 1.3,
                'requires_reversal_candle': True
            },
            GoldStrategy.TREND_FOLLOWING: {
                'stop_loss_atr_multiplier': 1.5,
                'take_profit_atr_multiplier': 2.5,  # 3.0 for strong trends
                'volume_threshold': 1.2,
                'requires_pullback': True
            },
            GoldStrategy.NO_TRADE: {
                'stop_loss_atr_multiplier': 0,
                'take_profit_atr_multiplier': 0,
                'volume_threshold': 0,
                'requires_retest': False
            }
        }
        
        return parameters.get(strategy, {})
