# Design Document: Unified Strategy Arsenal

## Overview

This design implements a unified strategy framework that makes all trading strategies available to all 6 scanners (BTC Scalp, BTC Swing, Gold Scalp, Gold Swing, US30 Scalp, US30 Swing). The architecture promotes code reuse, maintains backward compatibility, and adds 4 new advanced strategies while unifying 3 existing strategies across all scanners.

### Design Goals

1. **Unified Strategy Base**: Create a common strategy detection framework in `SignalDetector` that all scanners can use
2. **Asset-Specific Adaptation**: Allow strategies to adapt parameters based on asset characteristics (BTC, Gold, US30)
3. **Strategy Registry**: Implement a registry pattern for dynamic strategy loading and configuration
4. **Backward Compatibility**: Preserve existing signal quality and behavior
5. **Performance**: Minimize computational overhead by intelligent strategy selection

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Scanner Layer                            │
│  (BTC/Gold/US30 Scalp/Swing Scanners)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Strategy Orchestrator                           │
│  - Strategy Selection Logic                                  │
│  - Market Condition Analysis                                 │
│  - Priority Management                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Strategy Registry                               │
│  - Strategy Factory                                          │
│  - Configuration Management                                  │
│  - Enable/Disable Toggles                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Base Strategy Implementations                   │
│  (SignalDetector class)                                      │
│                                                              │
│  Existing Strategies:          New Strategies:              │
│  • Momentum Shift              • Fibonacci Retracement      │
│  • Mean Reversion              • Support/Resistance Bounce  │
│  • EMA Cloud Breakout          • Key Level Break & Retest  │
│  • Trend Alignment             • ADX+RSI+Momentum           │
│  • H4 HVG                                                    │
│                                                              │
│  Unified Strategies:                                         │
│  • Asian Range Breakout (all assets)                        │
│  • Liquidity Sweep (all assets)                             │
│  • Trend Following (all assets)                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
Scanner.detect_signals()
    │
    ├─> StrategyOrchestrator.select_strategies()
    │       │
    │       ├─> Analyze market conditions (ADX, ATR, volatility)
    │       ├─> Filter enabled strategies from config
    │       └─> Return prioritized strategy list
    │
    ├─> For each strategy in priority order:
    │       │
    │       ├─> StrategyRegistry.get_strategy(name, asset)
    │       │       │
    │       │       └─> Return strategy with asset-specific params
    │       │
    │       ├─> strategy.detect(data, timeframe, symbol)
    │       │       │
    │       │       ├─> Validate market conditions
    │       │       ├─> Check confluence factors
    │       │       ├─> Calculate entry/SL/TP levels
    │       │       └─> Return Signal or None
    │       │
    │       └─> If signal found, break loop
    │
    └─> Return signal (or None if no strategy triggered)
```

## Components and Interfaces

### 1. Strategy Orchestrator

**Purpose**: Intelligently select and prioritize strategies based on market conditions.

**Location**: `src/strategy_orchestrator.py` (new file)

**Key Methods**:

```python
class StrategyOrchestrator:
    def __init__(self, config: dict):
        """Initialize with configuration"""
        
    def analyze_market_conditions(self, data: pd.DataFrame) -> MarketConditions:
        """
        Analyze current market state
        Returns: MarketConditions(
            trend_strength: float,  # ADX value
            volatility: float,      # ATR ratio
            is_trending: bool,      # ADX > 20
            is_ranging: bool,       # ADX < 20
            momentum: str           # "bullish", "bearish", "neutral"
        )
        """
        
    def select_strategies(
        self, 
        market_conditions: MarketConditions,
        enabled_strategies: List[str]
    ) -> List[str]:
        """
        Return prioritized list of strategies for current conditions
        
        Priority Rules:
        - High volatility (ATR > 1.5x): Momentum, Breakout, Liquidity Sweep
        - Low volatility (ATR < 0.8x): Mean Reversion, Support/Resistance
        - Strong trend (ADX > 25): Trend Following, ADX+RSI+Momentum
        - Ranging (ADX < 20): Support/Resistance, Asian Range, Key Levels
        """
```

### 2. Strategy Registry

**Purpose**: Manage strategy instances and configuration.

**Location**: `src/strategy_registry.py` (new file)

**Key Methods**:

```python
class StrategyRegistry:
    def __init__(self, config: dict):
        """Initialize registry with configuration"""
        self.strategies = {}
        self.asset_configs = {}  # Asset-specific parameters
        
    def register_strategy(
        self, 
        name: str, 
        strategy_class: Type,
        default_params: dict
    ):
        """Register a strategy with default parameters"""
        
    def get_strategy(
        self, 
        name: str, 
        asset: str,
        signal_detector: SignalDetector
    ) -> Callable:
        """
        Get strategy detection function with asset-specific params
        
        Returns: Bound method from SignalDetector with adapted parameters
        """
        
    def is_enabled(self, strategy_name: str, scanner_type: str) -> bool:
        """Check if strategy is enabled for this scanner"""
        
    def get_asset_params(self, strategy_name: str, asset: str) -> dict:
        """Get asset-specific parameters for strategy"""
```

### 3. Enhanced SignalDetector

**Purpose**: Implement all strategy detection methods in base class.

**Location**: `src/signal_detector.py` (enhanced)

**New Methods to Add**:

```python
class SignalDetector:
    # Existing methods remain unchanged
    
    # NEW: Unified strategies (adapt for all assets)
    def _detect_asian_range_breakout(
        self, 
        data: pd.DataFrame, 
        timeframe: str, 
        symbol: str,
        asian_range: dict,
        buffer_percent: float = 0.3
    ) -> Optional[Signal]:
        """Detect Asian Range Breakout (unified for BTC/Gold/US30)"""
        
    def _detect_liquidity_sweep(
        self, 
        data: pd.DataFrame, 
        timeframe: str, 
        symbol: str,
        lookback_candles: int = 15
    ) -> Optional[Signal]:
        """Detect Liquidity Sweep patterns (unified for BTC/Gold/US30)"""
        
    def _detect_trend_following_pullback(
        self, 
        data: pd.DataFrame, 
        timeframe: str, 
        symbol: str,
        min_swings: int = 3
    ) -> Optional[Signal]:
        """Detect Trend Following pullback entries (unified for BTC/Gold/US30)"""
    
    # NEW: Advanced strategies
    def _detect_fibonacci_retracement(
        self, 
        data: pd.DataFrame, 
        timeframe: str, 
        symbol: str,
        swing_lookback: int = 50
    ) -> Optional[Signal]:
        """
        Detect Fibonacci retracement signals
        
        Steps:
        1. Identify significant swing (high to low or low to high)
        2. Calculate Fib levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
        3. Check if price is near a Fib level (within 0.5%)
        4. Look for reversal candle pattern
        5. Validate with volume and RSI
        6. Set SL beyond next Fib level
        """
        
    def _detect_support_resistance_bounce(
        self, 
        data: pd.DataFrame, 
        timeframe: str, 
        symbol: str,
        lookback_candles: int = 100,
        min_touches: int = 2
    ) -> Optional[Signal]:
        """
        Detect support/resistance bounce signals
        
        Steps:
        1. Identify support/resistance levels from historical data
        2. Find levels with at least min_touches
        3. Check if price is near a level (within 0.3%)
        4. Look for reversal candle pattern (pin bar, engulfing, doji)
        5. Validate with volume
        6. Increase confidence for round numbers
        """
        
    def _detect_key_level_break_retest(
        self, 
        data: pd.DataFrame, 
        timeframe: str, 
        symbol: str,
        key_levels: List[float]
    ) -> Optional[Signal]:
        """
        Detect key level break and retest signals
        
        Steps:
        1. Identify key levels (round numbers, prev highs/lows)
        2. Detect break with volume
        3. Wait for retest (within 5-10 candles)
        4. Validate retest holds with volume
        5. Generate continuation signal
        """
        
    def _detect_adx_rsi_momentum_confluence(
        self, 
        data: pd.DataFrame, 
        timeframe: str, 
        symbol: str,
        adx_min: float = 20,
        adx_strong: float = 25
    ) -> Optional[Signal]:
        """
        Detect ADX + RSI + Momentum confluence signals
        
        Steps:
        1. Check ADX > adx_min (trend forming)
        2. Check RSI directional (>50 bullish, <50 bearish)
        3. Detect RSI momentum acceleration (change > 3 points)
        4. Validate price momentum alignment
        5. Require volume > 1.2x average
        6. Increase confidence if ADX rising
        """
```

### 4. Helper Classes and Utilities

**Location**: `src/strategy_helpers.py` (new file)

```python
@dataclass
class MarketConditions:
    """Market condition analysis result"""
    trend_strength: float  # ADX value
    volatility: float      # ATR ratio vs average
    is_trending: bool      # ADX > 20
    is_ranging: bool       # ADX < 20
    momentum: str          # "bullish", "bearish", "neutral"
    volume_profile: str    # "high", "normal", "low"

@dataclass
class FibonacciLevels:
    """Fibonacci retracement levels"""
    swing_high: float
    swing_low: float
    level_236: float  # 23.6%
    level_382: float  # 38.2%
    level_500: float  # 50%
    level_618: float  # 61.8%
    level_786: float  # 78.6%
    direction: str    # "retracement_up" or "retracement_down"

@dataclass
class SupportResistanceLevel:
    """Support or resistance level"""
    price: float
    level_type: str    # "support" or "resistance"
    touches: int       # Number of times price touched this level
    strength: float    # 0-1 score based on touches and recency
    is_round_number: bool
    last_touch_candles_ago: int

class FibonacciCalculator:
    """Calculate Fibonacci retracement levels"""
    
    @staticmethod
    def find_swing(data: pd.DataFrame, lookback: int = 50) -> Tuple[float, float, str]:
        """Find most significant swing in recent data"""
        
    @staticmethod
    def calculate_levels(swing_high: float, swing_low: float) -> FibonacciLevels:
        """Calculate Fibonacci levels from swing"""
        
    @staticmethod
    def is_near_level(price: float, level: float, tolerance_percent: float = 0.5) -> bool:
        """Check if price is near a Fibonacci level"""

class SupportResistanceFinder:
    """Identify support and resistance levels"""
    
    @staticmethod
    def find_levels(
        data: pd.DataFrame, 
        lookback: int = 100,
        min_touches: int = 2,
        tolerance_percent: float = 0.3
    ) -> List[SupportResistanceLevel]:
        """Find support/resistance levels in historical data"""
        
    @staticmethod
    def is_round_number(price: float, asset: str) -> bool:
        """Check if price is a round number for the asset"""
        
    @staticmethod
    def get_nearest_level(
        price: float, 
        levels: List[SupportResistanceLevel],
        max_distance_percent: float = 0.5
    ) -> Optional[SupportResistanceLevel]:
        """Get nearest support/resistance level to current price"""

class KeyLevelTracker:
    """Track and identify key price levels"""
    
    def __init__(self, asset: str):
        self.asset = asset
        self.key_levels = []
        
    def update_levels(self, data: pd.DataFrame):
        """Update key levels from recent data"""
        
    def get_round_numbers(self, current_price: float, range_percent: float = 5.0) -> List[float]:
        """Get round numbers near current price"""
        
    def detect_break(self, current_candle: pd.Series, prev_candle: pd.Series) -> Optional[dict]:
        """Detect if a key level was broken"""
```

## Data Models

### Strategy Configuration Schema

```json
{
  "strategies": {
    "asian_range_breakout": {
      "enabled": true,
      "scanners": ["btc_scalp", "btc_swing", "gold_scalp", "gold_swing", "us30_scalp", "us30_swing"],
      "params": {
        "btc": {
          "buffer_percent": 0.3,
          "volume_threshold": 1.5,
          "retest_candles": 5
        },
        "gold": {
          "buffer_pips": 2.0,
          "volume_threshold": 1.2,
          "retest_candles": 5
        },
        "us30": {
          "buffer_points": 15,
          "volume_threshold": 1.5,
          "retest_candles": 5
        }
      }
    },
    "liquidity_sweep": {
      "enabled": true,
      "scanners": ["btc_scalp", "btc_swing", "gold_scalp", "gold_swing", "us30_scalp", "us30_swing"],
      "params": {
        "lookback_candles": 15,
        "volume_threshold": 1.5,
        "require_vwap_confirmation": true
      }
    },
    "trend_following": {
      "enabled": true,
      "scanners": ["btc_scalp", "btc_swing", "gold_scalp", "gold_swing", "us30_scalp", "us30_swing"],
      "params": {
        "min_swings": 3,
        "max_pullback_percent": 61.8,
        "volume_threshold": 1.2,
        "rsi_range_uptrend": [40, 80],
        "rsi_range_downtrend": [20, 60]
      }
    },
    "fibonacci_retracement": {
      "enabled": true,
      "scanners": ["btc_scalp", "btc_swing", "gold_scalp", "gold_swing", "us30_scalp", "us30_swing"],
      "params": {
        "swing_lookback": 50,
        "level_tolerance_percent": 0.5,
        "volume_threshold": 1.3,
        "priority_levels": [0.382, 0.618],
        "require_reversal_candle": true
      }
    },
    "support_resistance_bounce": {
      "enabled": true,
      "scanners": ["btc_scalp", "btc_swing", "gold_scalp", "gold_swing", "us30_scalp", "us30_swing"],
      "params": {
        "lookback_candles": 100,
        "min_touches": 2,
        "level_tolerance_percent": 0.3,
        "volume_threshold": 1.4,
        "round_number_bonus": true
      }
    },
    "key_level_break_retest": {
      "enabled": true,
      "scanners": ["btc_scalp", "btc_swing", "gold_scalp", "gold_swing", "us30_scalp", "us30_swing"],
      "params": {
        "retest_window_candles": [5, 10],
        "volume_threshold_break": 1.5,
        "volume_threshold_retest": 0.8,
        "major_level_volume_multiplier": 1.5
      }
    },
    "adx_rsi_momentum": {
      "enabled": true,
      "scanners": ["btc_scalp", "btc_swing", "gold_scalp", "gold_swing", "us30_scalp", "us30_swing"],
      "params": {
        "adx_min": 20,
        "adx_strong": 25,
        "rsi_momentum_threshold": 3.0,
        "volume_threshold": 1.2,
        "require_adx_rising": false
      }
    }
  },
  "strategy_priority": {
    "high_volatility": [
      "adx_rsi_momentum",
      "liquidity_sweep",
      "ema_cloud_breakout",
      "momentum_shift"
    ],
    "low_volatility": [
      "mean_reversion",
      "support_resistance_bounce",
      "fibonacci_retracement"
    ],
    "strong_trend": [
      "trend_following",
      "adx_rsi_momentum",
      "key_level_break_retest"
    ],
    "ranging": [
      "support_resistance_bounce",
      "asian_range_breakout",
      "mean_reversion"
    ]
  }
}
```

### Enhanced Signal Data Model

```python
@dataclass
class Signal:
    # Existing fields...
    
    # NEW: Strategy-specific metadata
    strategy_metadata: Optional[Dict] = None
    """
    Strategy-specific data:
    - fibonacci_retracement: {level: 0.618, swing_high: X, swing_low: Y}
    - support_resistance: {level_price: X, touches: 3, strength: 0.8}
    - key_level: {level: X, break_candles_ago: 2, is_round_number: True}
    - adx_rsi_momentum: {adx: 28, rsi_change: 4.2, momentum_score: 0.9}
    """
```

## Error Handling

### Strategy Detection Errors

```python
class StrategyError(Exception):
    """Base exception for strategy errors"""
    pass

class InsufficientDataError(StrategyError):
    """Not enough data to run strategy"""
    pass

class InvalidParametersError(StrategyError):
    """Strategy parameters are invalid"""
    pass

# Error handling in strategy detection
try:
    signal = strategy.detect(data, timeframe, symbol)
except InsufficientDataError as e:
    logger.debug(f"Strategy {strategy_name} skipped: {e}")
    continue  # Try next strategy
except InvalidParametersError as e:
    logger.error(f"Strategy {strategy_name} misconfigured: {e}")
    continue
except Exception as e:
    logger.error(f"Unexpected error in {strategy_name}: {e}", exc_info=True)
    continue
```

## Testing Strategy

### Unit Tests

**Location**: `tests/test_strategy_*.py`

```python
# Test each strategy independently
class TestFibonacciRetracement:
    def test_calculate_levels(self):
        """Test Fibonacci level calculation"""
        
    def test_detect_near_618_level(self):
        """Test detection at golden ratio"""
        
    def test_reject_weak_reversal(self):
        """Test rejection when no reversal candle"""

class TestSupportResistanceBounce:
    def test_find_support_levels(self):
        """Test support level identification"""
        
    def test_detect_bounce_at_support(self):
        """Test bounce signal at support"""
        
    def test_round_number_priority(self):
        """Test round number gets higher priority"""

class TestADXRSIMomentum:
    def test_detect_bullish_confluence(self):
        """Test bullish signal with all indicators aligned"""
        
    def test_reject_low_adx(self):
        """Test rejection when ADX < 20"""
        
    def test_momentum_acceleration(self):
        """Test RSI momentum acceleration detection"""
```

### Integration Tests

```python
class TestStrategyOrchestrator:
    def test_strategy_selection_trending_market(self):
        """Test correct strategies selected in trending market"""
        
    def test_strategy_selection_ranging_market(self):
        """Test correct strategies selected in ranging market"""
        
    def test_strategy_priority_order(self):
        """Test strategies tried in correct priority order"""

class TestUnifiedStrategies:
    def test_asian_range_btc(self):
        """Test Asian Range works for BTC"""
        
    def test_asian_range_gold(self):
        """Test Asian Range works for Gold"""
        
    def test_asian_range_us30(self):
        """Test Asian Range works for US30"""
```

### Performance Tests

```python
class TestStrategyPerformance:
    def test_strategy_execution_time(self):
        """Ensure each strategy completes within 100ms"""
        
    def test_full_scan_time(self):
        """Ensure full scan with all strategies < 500ms"""
```

## Migration Strategy

### Phase 1: Add New Infrastructure (No Breaking Changes)

1. Create `strategy_orchestrator.py`
2. Create `strategy_registry.py`
3. Create `strategy_helpers.py`
4. Add new strategy methods to `SignalDetector`
5. Add configuration schema to all config files

### Phase 2: Integrate with Existing Scanners

1. Update `SignalDetector.__init__()` to accept `StrategyRegistry`
2. Modify `detect_signals()` to use `StrategyOrchestrator`
3. Keep existing strategy calls as fallback
4. Add feature flag: `use_unified_strategies: false` (default)

### Phase 3: Enable Unified Strategies

1. Test thoroughly with `use_unified_strategies: true`
2. Compare signal quality with existing implementation
3. Gradually enable per scanner
4. Monitor performance and signal quality

### Phase 4: Cleanup (Optional)

1. Remove duplicate strategy code from asset-specific detectors
2. Deprecate old strategy methods
3. Update documentation

## Performance Considerations

### Optimization Strategies

1. **Lazy Calculation**: Only calculate indicators needed for enabled strategies
2. **Caching**: Cache Fibonacci levels, support/resistance levels for multiple candles
3. **Early Exit**: Stop trying strategies once a high-confidence signal is found
4. **Parallel Detection**: Consider running independent strategies in parallel (future enhancement)

### Memory Management

1. **Sliding Window**: Keep only necessary historical data for level detection
2. **Level Pruning**: Remove old/weak support/resistance levels periodically
3. **Signal History**: Limit signal history to last 50 signals per strategy

## Security Considerations

1. **Configuration Validation**: Validate all strategy parameters on load
2. **Input Sanitization**: Validate data inputs to prevent injection attacks
3. **Rate Limiting**: Prevent excessive strategy execution if misconfigured
4. **Logging**: Log all strategy decisions for audit trail

## Monitoring and Observability

### Metrics to Track

```python
# Per-strategy metrics
strategy_execution_count
strategy_signal_count
strategy_execution_time_ms
strategy_error_count

# Signal quality metrics
signal_win_rate_by_strategy
signal_avg_risk_reward_by_strategy
signal_avg_confidence_by_strategy

# System metrics
total_scan_time_ms
strategies_evaluated_per_scan
cache_hit_rate
```

### Logging Strategy

```python
# Strategy selection
logger.info(f"Market conditions: ADX={adx}, ATR_ratio={atr_ratio}, selecting strategies: {selected}")

# Strategy execution
logger.debug(f"Trying strategy: {strategy_name}")
logger.info(f"Signal detected: {strategy_name} - {signal.signal_type} at {signal.entry_price}")

# Performance
logger.debug(f"Strategy {strategy_name} completed in {elapsed_ms}ms")
```

## Future Enhancements

1. **Machine Learning Integration**: Use ML to optimize strategy selection based on historical performance
2. **Multi-Timeframe Confluence**: Combine signals from multiple timeframes
3. **Adaptive Parameters**: Auto-tune strategy parameters based on market conditions
4. **Strategy Backtesting**: Built-in backtesting framework for strategy validation
5. **Custom Strategy Plugin System**: Allow users to add custom strategies via plugins
