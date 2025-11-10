"""Strategy orchestrator for intelligent strategy selection based on market conditions."""

from typing import List, Optional
import pandas as pd
import logging

from src.strategy_helpers import MarketConditions

logger = logging.getLogger(__name__)


class StrategyOrchestrator:
    """
    Orchestrates strategy selection based on market conditions.
    
    Analyzes market state (trend strength, volatility, momentum) and
    selects appropriate strategies with priority ordering.
    """
    
    def __init__(self, config: dict):
        """
        Initialize strategy orchestrator.
        
        Args:
            config: Configuration dictionary with strategy priority settings
        """
        self.config = config
        
        # Load strategy priorities from config
        priority_config = config.get('strategy_priority', {})
        self.high_volatility_strategies = priority_config.get('high_volatility', [])
        self.low_volatility_strategies = priority_config.get('low_volatility', [])
        self.strong_trend_strategies = priority_config.get('strong_trend', [])
        self.ranging_strategies = priority_config.get('ranging', [])
        
        logger.info("StrategyOrchestrator initialized")
    
    def analyze_market_conditions(self, data: pd.DataFrame) -> Optional[MarketConditions]:
        """
        Analyze current market state.
        
        Args:
            data: DataFrame with OHLCV and indicators
            
        Returns:
            MarketConditions object or None if insufficient data
        """
        try:
            if data.empty or len(data) < 20:
                logger.warning("Insufficient data for market analysis")
                return None
            
            last = data.iloc[-1]
            
            # Get ADX (trend strength)
            trend_strength = last.get('adx', 0)
            
            # Calculate ATR ratio (volatility)
            atr = last.get('atr', 0)
            atr_ma = data['atr'].iloc[-20:].mean() if len(data) >= 20 else atr
            volatility = atr / atr_ma if atr_ma > 0 else 1.0
            
            # Determine if trending or ranging
            is_trending = trend_strength > 20
            is_ranging = trend_strength < 20
            
            # Determine momentum direction
            momentum = "neutral"
            if 'rsi' in last:
                rsi = last['rsi']
                if rsi > 55:
                    momentum = "bullish"
                elif rsi < 45:
                    momentum = "bearish"
            
            # Determine volume profile
            volume_profile = "normal"
            if 'volume' in last and 'volume_ma' in last:
                volume_ratio = last['volume'] / last['volume_ma'] if last['volume_ma'] > 0 else 1.0
                if volume_ratio > 1.5:
                    volume_profile = "high"
                elif volume_ratio < 0.7:
                    volume_profile = "low"
            
            conditions = MarketConditions(
                trend_strength=trend_strength,
                volatility=volatility,
                is_trending=is_trending,
                is_ranging=is_ranging,
                momentum=momentum,
                volume_profile=volume_profile
            )
            
            logger.debug(
                f"Market conditions: ADX={trend_strength:.1f}, "
                f"Volatility={volatility:.2f}x, Momentum={momentum}, "
                f"Volume={volume_profile}"
            )
            
            return conditions
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return None
    
    def select_strategies(
        self, 
        market_conditions: MarketConditions,
        enabled_strategies: List[str]
    ) -> List[str]:
        """
        Return prioritized list of strategies for current conditions.
        
        Args:
            market_conditions: Current market conditions
            enabled_strategies: List of enabled strategy names
            
        Returns:
            Prioritized list of strategy names to try
        """
        try:
            prioritized = []
            
            # High volatility strategies (ATR > 1.5x average)
            if market_conditions.volatility > 1.5:
                logger.debug("High volatility detected, prioritizing momentum/breakout strategies")
                prioritized.extend(self._filter_enabled(
                    self.high_volatility_strategies, 
                    enabled_strategies
                ))
            
            # Low volatility strategies (ATR < 0.8x average)
            elif market_conditions.volatility < 0.8:
                logger.debug("Low volatility detected, prioritizing mean reversion strategies")
                prioritized.extend(self._filter_enabled(
                    self.low_volatility_strategies, 
                    enabled_strategies
                ))
            
            # Strong trend strategies (ADX > 25)
            if market_conditions.trend_strength > 25:
                logger.debug("Strong trend detected, prioritizing trend-following strategies")
                prioritized.extend(self._filter_enabled(
                    self.strong_trend_strategies, 
                    enabled_strategies
                ))
            
            # Ranging market strategies (ADX < 20)
            elif market_conditions.is_ranging:
                logger.debug("Ranging market detected, prioritizing support/resistance strategies")
                prioritized.extend(self._filter_enabled(
                    self.ranging_strategies, 
                    enabled_strategies
                ))
            
            # Add remaining enabled strategies not yet in list
            for strategy in enabled_strategies:
                if strategy not in prioritized:
                    prioritized.append(strategy)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_prioritized = []
            for strategy in prioritized:
                if strategy not in seen:
                    seen.add(strategy)
                    unique_prioritized.append(strategy)
            
            logger.debug(f"Selected {len(unique_prioritized)} strategies in priority order")
            return unique_prioritized
            
        except Exception as e:
            logger.error(f"Error selecting strategies: {e}")
            return enabled_strategies  # Fallback to all enabled strategies
    
    def _filter_enabled(self, priority_list: List[str], enabled_list: List[str]) -> List[str]:
        """
        Filter priority list to only include enabled strategies.
        
        Args:
            priority_list: List of strategies in priority order
            enabled_list: List of enabled strategies
            
        Returns:
            Filtered list maintaining priority order
        """
        return [s for s in priority_list if s in enabled_list]
    
    def detect_conflicting_signals(self, signals: List) -> bool:
        """
        Detect if multiple signals are conflicting (LONG vs SHORT).
        
        Args:
            signals: List of Signal objects
            
        Returns:
            True if signals conflict, False otherwise
        """
        if len(signals) < 2:
            return False
        
        signal_types = set(s.signal_type for s in signals)
        
        # Conflict if we have both LONG and SHORT signals
        has_conflict = "LONG" in signal_types and "SHORT" in signal_types
        
        if has_conflict:
            logger.warning("Conflicting signals detected (LONG and SHORT)")
        
        return has_conflict
    
    def should_skip_strategy(
        self, 
        strategy_name: str, 
        market_conditions: MarketConditions
    ) -> bool:
        """
        Determine if a strategy should be skipped based on market conditions.
        
        Args:
            strategy_name: Name of the strategy
            market_conditions: Current market conditions
            
        Returns:
            True if strategy should be skipped, False otherwise
        """
        # Skip momentum strategies in ranging markets
        if "momentum" in strategy_name.lower() and market_conditions.is_ranging:
            logger.debug(f"Skipping {strategy_name}: market is ranging (ADX < 20)")
            return True
        
        # Skip mean reversion in strong trends
        if "mean_reversion" in strategy_name.lower() and market_conditions.trend_strength > 25:
            logger.debug(f"Skipping {strategy_name}: strong trend detected (ADX > 25)")
            return True
        
        # Skip trend following in ranging markets
        if "trend" in strategy_name.lower() and market_conditions.is_ranging:
            logger.debug(f"Skipping {strategy_name}: market is ranging")
            return True
        
        # Skip breakout strategies in low volume
        if "breakout" in strategy_name.lower() and market_conditions.volume_profile == "low":
            logger.debug(f"Skipping {strategy_name}: low volume environment")
            return True
        
        return False
    
    def get_strategy_confidence_multiplier(
        self, 
        strategy_name: str, 
        market_conditions: MarketConditions
    ) -> float:
        """
        Get confidence multiplier for strategy based on market conditions.
        
        Args:
            strategy_name: Name of the strategy
            market_conditions: Current market conditions
            
        Returns:
            Confidence multiplier (0.5 to 1.5)
        """
        multiplier = 1.0
        
        # Boost momentum strategies in trending markets
        if "momentum" in strategy_name.lower() and market_conditions.is_trending:
            multiplier = 1.3
        
        # Boost mean reversion in ranging markets
        if "mean_reversion" in strategy_name.lower() and market_conditions.is_ranging:
            multiplier = 1.2
        
        # Boost trend following in strong trends
        if "trend" in strategy_name.lower() and market_conditions.trend_strength > 25:
            multiplier = 1.4
        
        # Boost breakout strategies in high volume
        if "breakout" in strategy_name.lower() and market_conditions.volume_profile == "high":
            multiplier = 1.3
        
        # Reduce confidence in low volume
        if market_conditions.volume_profile == "low":
            multiplier *= 0.8
        
        # Clamp between 0.5 and 1.5
        return max(0.5, min(1.5, multiplier))
    
    def log_market_summary(self, market_conditions: MarketConditions):
        """
        Log a summary of current market conditions.
        
        Args:
            market_conditions: Current market conditions
        """
        logger.info(
            f"📊 Market Summary: "
            f"ADX={market_conditions.trend_strength:.1f} "
            f"({'Trending' if market_conditions.is_trending else 'Ranging'}), "
            f"Volatility={market_conditions.volatility:.2f}x, "
            f"Momentum={market_conditions.momentum}, "
            f"Volume={market_conditions.volume_profile}"
        )
