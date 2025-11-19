"""
Pluggable Strategy Detection Framework
Coordinates multiple trading strategies with market-condition-based priority.
"""
import logging
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class MarketConditions:
    """Current market conditions for strategy selection"""
    volatility: float  # ADX value
    trend_strength: str  # "strong", "moderate", "weak"
    market_regime: str  # "trending", "ranging", "volatile"
    volume_trend: str  # "increasing", "decreasing", "stable"
    price_position: str  # "overbought", "oversold", "neutral"


class StrategyRegistry:
    """Registry for pluggable trading strategies"""
    
    def __init__(self):
        """Initialize strategy registry"""
        self.strategies: Dict[str, Callable] = {}
        self.strategy_metadata: Dict[str, Dict] = {}
    
    def register(
        self,
        name: str,
        strategy_func: Callable,
        priority: int = 0,
        description: str = "",
        enabled: bool = True
    ) -> None:
        """
        Register a strategy.
        
        Args:
            name: Strategy name
            strategy_func: Strategy detection function
            priority: Strategy priority (higher = more important)
            description: Strategy description
            enabled: Whether strategy is enabled
        """
        self.strategies[name] = strategy_func
        self.strategy_metadata[name] = {
            'priority': priority,
            'description': description,
            'enabled': enabled
        }
        logger.info(f"Registered strategy: {name} (priority: {priority})")
    
    def unregister(self, name: str) -> None:
        """Unregister a strategy"""
        if name in self.strategies:
            del self.strategies[name]
            del self.strategy_metadata[name]
            logger.info(f"Unregistered strategy: {name}")
    
    def get_strategy(self, name: str) -> Optional[Callable]:
        """Get strategy function by name"""
        return self.strategies.get(name)
    
    def get_enabled_strategies(self) -> List[str]:
        """Get list of enabled strategies"""
        return [
            name for name, meta in self.strategy_metadata.items()
            if meta.get('enabled', True)
        ]
    
    def set_strategy_enabled(self, name: str, enabled: bool) -> None:
        """Enable or disable a strategy"""
        if name in self.strategy_metadata:
            self.strategy_metadata[name]['enabled'] = enabled
            logger.info(f"Strategy {name} {'enabled' if enabled else 'disabled'}")


class StrategyDetector:
    """
    Coordinates multiple trading strategies with market-condition-based priority.
    """
    
    # Strategy priority by market condition
    STRATEGY_PRIORITY = {
        'high_volatility': [
            'adx_rsi_momentum',
            'momentum_shift',
            'ema_cloud_breakout'
        ],
        'low_volatility': [
            'mean_reversion',
            'support_resistance_bounce',
            'fibonacci_retracement'
        ],
        'strong_trend': [
            'adx_rsi_momentum',
            'trend_alignment',
            'key_level_break_retest'
        ],
        'ranging': [
            'support_resistance_bounce',
            'mean_reversion',
            'fibonacci_retracement'
        ]
    }
    
    def __init__(self):
        """Initialize strategy detector"""
        self.registry = StrategyRegistry()
        self.config = {}
    
    def register_strategy(
        self,
        name: str,
        strategy_func: Callable,
        priority: int = 0,
        description: str = "",
        enabled: bool = True
    ) -> None:
        """
        Register a trading strategy.
        
        Args:
            name: Strategy name
            strategy_func: Strategy detection function
            priority: Strategy priority
            description: Strategy description
            enabled: Whether strategy is enabled
        """
        self.registry.register(name, strategy_func, priority, description, enabled)
    
    def detect_signals(
        self,
        data: pd.DataFrame,
        timeframe: str,
        symbol: str,
        enabled_strategies: Optional[List[str]] = None
    ) -> Optional[any]:
        """
        Detect signals using enabled strategies with market-condition-based priority.
        
        Args:
            data: DataFrame with indicator data
            timeframe: Candle timeframe
            symbol: Trading symbol
            enabled_strategies: List of strategies to use (None = all enabled)
            
        Returns:
            Signal object if detected, None otherwise
        """
        if data.empty:
            logger.warning("Cannot detect signals: DataFrame is empty")
            return None
        
        # Determine market conditions
        conditions = self._analyze_market_conditions(data)
        logger.debug(f"Market conditions: {conditions}")
        
        # Get strategy priority for current conditions
        priority_list = self._get_strategy_priority(conditions)
        logger.debug(f"Strategy priority: {priority_list}")
        
        # Filter to enabled strategies
        if enabled_strategies:
            priority_list = [s for s in priority_list if s in enabled_strategies]
        else:
            priority_list = [s for s in priority_list if s in self.registry.get_enabled_strategies()]
        
        # Try each strategy in priority order
        for strategy_name in priority_list:
            try:
                strategy_func = self.registry.get_strategy(strategy_name)
                if strategy_func is None:
                    logger.debug(f"Strategy not found: {strategy_name}")
                    continue
                
                logger.debug(f"Attempting strategy: {strategy_name}")
                signal = strategy_func(data, timeframe, symbol)
                
                if signal is not None:
                    logger.info(f"Signal detected using strategy: {strategy_name}")
                    return signal
                    
            except Exception as e:
                logger.error(f"Error in strategy {strategy_name}: {e}")
                continue
        
        logger.debug("No signals detected from any strategy")
        return None
    
    def _analyze_market_conditions(self, data: pd.DataFrame) -> MarketConditions:
        """
        Analyze current market conditions.
        
        Args:
            data: DataFrame with indicator data
            
        Returns:
            MarketConditions object
        """
        try:
            last = data.iloc[-1]
            
            # Get ADX for volatility/trend strength
            adx = last.get('adx', 20)
            
            # Determine trend strength
            if adx > 25:
                trend_strength = "strong"
            elif adx > 15:
                trend_strength = "moderate"
            else:
                trend_strength = "weak"
            
            # Determine market regime
            if adx > 25:
                market_regime = "trending"
            elif adx < 15:
                market_regime = "ranging"
            else:
                market_regime = "volatile"
            
            # Determine volume trend
            if len(data) >= 2:
                vol_ratio = last.get('volume', 0) / last.get('volume_ma', 1)
                if vol_ratio > 1.3:
                    volume_trend = "increasing"
                elif vol_ratio < 0.7:
                    volume_trend = "decreasing"
                else:
                    volume_trend = "stable"
            else:
                volume_trend = "stable"
            
            # Determine price position
            rsi = last.get('rsi', 50)
            if rsi > 70:
                price_position = "overbought"
            elif rsi < 30:
                price_position = "oversold"
            else:
                price_position = "neutral"
            
            return MarketConditions(
                volatility=adx,
                trend_strength=trend_strength,
                market_regime=market_regime,
                volume_trend=volume_trend,
                price_position=price_position
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            # Return neutral conditions
            return MarketConditions(
                volatility=20,
                trend_strength="moderate",
                market_regime="volatile",
                volume_trend="stable",
                price_position="neutral"
            )
    
    def _get_strategy_priority(self, conditions: MarketConditions) -> List[str]:
        """
        Get strategy priority based on market conditions.
        
        Args:
            conditions: Current market conditions
            
        Returns:
            List of strategy names in priority order
        """
        # Determine which priority list to use
        if conditions.volatility > 25:
            regime = 'high_volatility'
        elif conditions.volatility < 15:
            regime = 'low_volatility'
        elif conditions.trend_strength == 'strong':
            regime = 'strong_trend'
        else:
            regime = 'ranging'
        
        logger.debug(f"Using strategy priority for regime: {regime}")
        return self.STRATEGY_PRIORITY.get(regime, [])
    
    def get_strategy_status(self) -> Dict[str, Dict]:
        """
        Get status of all registered strategies.
        
        Returns:
            Dictionary with strategy status
        """
        status = {}
        for name, meta in self.registry.strategy_metadata.items():
            status[name] = {
                'enabled': meta.get('enabled', True),
                'priority': meta.get('priority', 0),
                'description': meta.get('description', '')
            }
        return status
    
    def enable_strategy(self, name: str) -> None:
        """Enable a strategy"""
        self.registry.set_strategy_enabled(name, True)
    
    def disable_strategy(self, name: str) -> None:
        """Disable a strategy"""
        self.registry.set_strategy_enabled(name, False)

