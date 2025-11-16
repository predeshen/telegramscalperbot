# Design Document

## Overview

This design extends the existing BTC scanner architecture to support multiple cryptocurrency and FX symbols simultaneously. The solution maintains backward compatibility with existing BTC scanners while introducing a multi-symbol orchestrator that manages parallel scanning, asset-specific configurations, and intelligent signal filtering to prevent conflicting signals and premature exits.

### Key Design Principles

1. **Minimal Code Changes**: Leverage existing components (YFinanceClient, SignalDetector, IndicatorCalculator)
2. **Parallel Processing**: Scan multiple symbols concurrently without blocking
3. **Asset-Specific Optimization**: Each symbol has tailored parameters based on its characteristics
4. **Intelligent Filtering**: Prevent conflicting signals across timeframes and premature exit signals
5. **Configuration-Driven**: Add/remove symbols via JSON config without code changes

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Symbol Scanner                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Symbol Orchestrator (NEW)                         │  │
│  │  - Manages multiple symbol scanners                       │  │
│  │  - Coordinates signal filtering                           │  │
│  │  - Handles timeframe conflict resolution                  │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                      │
│           ├──────────┬──────────┬──────────┬──────────┐        │
│           ▼          ▼          ▼          ▼          ▼        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐│
│  │ BTC Scanner │ │ ETH Scanner │ │ SOL Scanner │ │ EUR/USD  ││
│  │             │ │             │ │             │ │ Scanner  ││
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └────┬─────┘│
│         │               │               │              │       │
│         └───────────────┴───────────────┴──────────────┘       │
│                         │                                       │
│                         ▼                                       │
│         ┌───────────────────────────────┐                      │
│         │  Enhanced Trade Tracker (MOD) │                      │
│         │  - Grace period enforcement   │                      │
│         │  - Exit signal filtering      │                      │
│         │  - Per-symbol trade tracking  │                      │
│         └───────────────┬───────────────┘                      │
│                         │                                       │
│                         ▼                                       │
│         ┌───────────────────────────────┐                      │
│         │    Signal Filter (NEW)        │                      │
│         │  - Timeframe conflict check   │                      │
│         │  - Duplicate suppression      │                      │
│         │  - Session validation (FX)    │                      │
│         └───────────────┬───────────────┘                      │
│                         │                                       │
│                         ▼                                       │
│         ┌───────────────────────────────┐                      │
│         │      Multi Alerter            │                      │
│         │  - Symbol-specific formatting │                      │
│         │  - Emoji indicators           │                      │
│         └───────────────────────────────┘                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. Symbol Orchestrator (NEW)
- Initializes and manages multiple SymbolScanner instances
- Coordinates signal filtering across all symbols
- Resolves timeframe conflicts using hierarchy
- Aggregates metrics for reporting

#### 2. SymbolScanner (NEW)
- Wraps existing scanner logic for a single symbol
- Maintains YFinanceClient, SignalDetector, IndicatorCalculator per symbol
- Applies asset-specific configuration
- Reports signals to orchestrator for filtering

#### 3. Enhanced Trade Tracker (MODIFIED)
- Tracks trades per symbol separately
- Enforces grace period (30 minutes) before exit evaluation
- Validates exit conditions (profit thresholds, giveback percentage)
- Prevents duplicate exit signals

#### 4. Signal Filter (NEW)
- Checks for conflicting signals across timeframes
- Suppresses lower timeframe signals when conflicts exist
- Validates FX trading sessions
- Maintains signal history for duplicate detection

#### 5. Asset Config Manager (NEW)
- Loads and validates symbol configurations
- Provides asset-specific parameters to scanners
- Supports hot-reload of configuration changes
- Categorizes symbols by type (crypto, fx, commodity)

#### 6. FVG Detector (NEW)
- Detects Fair Value Gaps on higher timeframes (4h, 1d)
- Identifies inverse FVGs (bearish) and regular FVGs (bullish)
- Tracks unfilled FVG zones and monitors for price re-entry
- Detects lower timeframe market structure shifts within FVG zones
- Calculates targets based on liquidity pools and swing points

#### 7. NWOG Detector (NEW)
- Detects New Week Opening Gaps for indices (US30, Nasdaq, S&P500)
- Compares Friday close to Monday open to identify gaps
- Tracks NWOG zones as key institutional levels
- Monitors for price rejection at NWOG zones
- Generates signals when NWOG is respected as support/resistance

#### 8. Divergence Analyzer (NEW)
- Tracks correlated indices (US30, S&P500, Nasdaq) simultaneously
- Detects inter-market divergence (one index makes new high/low, others don't)
- Calculates divergence strength and duration
- Enhances signal confidence when divergence aligns with key levels
- Provides divergence context in signal alerts

## Components and Interfaces

### SymbolOrchestrator

```python
class SymbolOrchestrator:
    """Manages multiple symbol scanners and coordinates signal filtering."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config: Master configuration containing all symbol configs
        """
        self.config = config
        self.scanners: Dict[str, SymbolScanner] = {}
        self.signal_filter = SignalFilter()
        self.trade_tracker = EnhancedTradeTracker()
        self.alerter = MultiAlerter()
        
    def add_symbol(self, symbol: str, symbol_config: Dict[str, Any]) -> None:
        """Add a new symbol scanner."""
        
    def remove_symbol(self, symbol: str) -> None:
        """Remove a symbol scanner."""
        
    def start(self) -> None:
        """Start all symbol scanners."""
        
    def stop(self) -> None:
        """Stop all symbol scanners gracefully."""
        
    def on_signal_detected(self, symbol: str, signal: Signal) -> None:
        """
        Handle signal from a symbol scanner.
        Applies filtering before sending alerts.
        """
```

### SymbolScanner

```python
class SymbolScanner:
    """Scanner for a single symbol with asset-specific configuration."""
    
    def __init__(
        self,
        symbol: str,
        asset_type: str,  # 'crypto', 'fx', 'commodity'
        timeframes: List[str],
        asset_config: Dict[str, Any],
        signal_callback: Callable
    ):
        """
        Initialize symbol scanner.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USD', 'EURUSD=X')
            asset_type: Type of asset for specific handling
            timeframes: List of timeframes to monitor
            asset_config: Asset-specific parameters
            signal_callback: Function to call when signal detected
        """
        self.symbol = symbol
        self.asset_type = asset_type
        self.timeframes = timeframes
        self.config = asset_config
        self.signal_callback = signal_callback
        
        # Initialize components
        self.market_client = YFinanceClient(symbol, timeframes)
        self.indicator_calc = IndicatorCalculator()
        self.signal_detector = SignalDetector(**asset_config['signal_rules'])
        
    def scan_timeframe(self, timeframe: str) -> Optional[Signal]:
        """Scan a single timeframe for signals."""
        
    def run(self) -> None:
        """Main scanning loop."""
```

### SignalFilter

```python
class SignalFilter:
    """Filters signals to prevent conflicts and duplicates."""
    
    # Timeframe hierarchy for conflict resolution
    TIMEFRAME_HIERARCHY = {
        '1d': 6,
        '4h': 5,
        '1h': 4,
        '15m': 3,
        '5m': 2,
        '1m': 1
    }
    
    def __init__(self):
        self.recent_signals: Dict[str, List[Signal]] = {}  # symbol -> signals
        self.active_trades: Dict[str, Signal] = {}  # symbol -> active signal
        
    def should_suppress_signal(
        self,
        symbol: str,
        signal: Signal,
        all_recent_signals: List[Signal]
    ) -> Tuple[bool, str]:
        """
        Determine if signal should be suppressed.
        
        Returns:
            (should_suppress, reason)
        """
        
    def check_timeframe_conflicts(
        self,
        signal: Signal,
        recent_signals: List[Signal]
    ) -> Tuple[bool, str]:
        """Check for conflicting signals across timeframes."""
        
    def check_active_trade_conflict(
        self,
        symbol: str,
        signal: Signal
    ) -> Tuple[bool, str]:
        """Check if signal conflicts with active trade."""
        
    def add_signal_to_history(self, symbol: str, signal: Signal) -> None:
        """Add signal to recent history."""
```

### EnhancedTradeTracker

```python
class EnhancedTradeTracker:
    """Enhanced trade tracker with grace period and strict exit rules."""
    
    def __init__(self, alerter: Optional[Any] = None):
        self.alerter = alerter
        self.active_trades: Dict[str, Dict[str, Any]] = {}  # symbol -> trade_data
        self.exit_signal_history: Dict[str, datetime] = {}  # trade_id -> last_exit_time
        
    def add_trade(self, symbol: str, signal: Signal) -> None:
        """Add a new trade for tracking."""
        
    def update_trades(self, symbol: str, current_price: float, indicators: Dict) -> None:
        """Update trade status and check exit conditions."""
        
    def should_send_exit_signal(
        self,
        trade_data: Dict[str, Any],
        current_price: float,
        indicators: Dict
    ) -> Tuple[bool, str]:
        """
        Determine if exit signal should be sent.
        
        Enforces:
        - Grace period (30 minutes)
        - Minimum profit thresholds
        - Giveback percentage limits
        - Duplicate prevention
        
        Returns:
            (should_exit, reason)
        """
```

### AssetConfigManager

```python
class AssetConfigManager:
    """Manages asset-specific configurations."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.load_configs()
        
    def load_configs(self) -> None:
        """Load configurations from JSON file."""
        
    def get_symbol_config(self, symbol: str) -> Dict[str, Any]:
        """Get configuration for a specific symbol."""
        
    def get_symbols_by_type(self, asset_type: str) -> List[str]:
        """Get all symbols of a specific type."""
        
    def validate_config(self, symbol_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a symbol configuration."""
        
    def reload_configs(self) -> None:
        """Hot-reload configurations without restart."""
```

### FVGDetector

```python
@dataclass
class FVGZone:
    """Represents a Fair Value Gap zone."""
    fvg_type: str  # 'inverse' (bearish) or 'regular' (bullish)
    timeframe: str
    high: float  # Upper boundary of gap
    low: float  # Lower boundary of gap
    created_at: datetime
    candle_index: int
    filled: bool = False
    filled_at: Optional[datetime] = None
    
class FVGDetector:
    """Detects Fair Value Gaps and liquidity voids."""
    
    def __init__(self, min_gap_percent: float = 0.2):
        """
        Initialize FVG detector.
        
        Args:
            min_gap_percent: Minimum gap size as percentage of price
        """
        self.min_gap_percent = min_gap_percent
        self.active_fvgs: Dict[str, List[FVGZone]] = {}  # timeframe -> zones
        
    def detect_fvgs(self, df: pd.DataFrame, timeframe: str) -> List[FVGZone]:
        """
        Detect Fair Value Gaps in candlestick data.
        
        An FVG exists when:
        - Inverse FVG (bearish): candle[i-1].low > candle[i+1].high
        - Regular FVG (bullish): candle[i-1].high < candle[i+1].low
        
        Returns:
            List of newly detected FVG zones
        """
        
    def check_fvg_reentry(
        self,
        current_price: float,
        fvg_zone: FVGZone
    ) -> bool:
        """Check if price has re-entered an FVG zone."""
        
    def detect_lower_tf_shift(
        self,
        df_lower: pd.DataFrame,
        fvg_zone: FVGZone
    ) -> Tuple[bool, str]:
        """
        Detect market structure shift on lower timeframe within FVG zone.
        
        For inverse FVG (bearish):
        - Look for break of structure (BOS) to downside
        - Confirm with lower high formation
        
        For regular FVG (bullish):
        - Look for break of structure (BOS) to upside
        - Confirm with higher low formation
        
        Returns:
            (shift_detected, shift_description)
        """
        
    def calculate_fvg_targets(
        self,
        df: pd.DataFrame,
        fvg_zone: FVGZone,
        lookback: int = 50
    ) -> Tuple[float, float]:
        """
        Calculate target levels based on swing points and liquidity.
        
        Returns:
            (target1, target2) - Two target levels
        """
        
    def mark_fvg_filled(self, fvg_zone: FVGZone, current_time: datetime) -> None:
        """Mark an FVG zone as filled when price fully retraces through it."""
        
    def get_active_fvgs(self, timeframe: str) -> List[FVGZone]:
        """Get all active (unfilled) FVG zones for a timeframe."""
```

### NWOGDetector

```python
@dataclass
class NWOGZone:
    """Represents a New Week Opening Gap zone."""
    gap_type: str  # 'bullish' (gap up) or 'bearish' (gap down)
    friday_close: float
    monday_open: float
    gap_high: float  # Upper boundary
    gap_low: float  # Lower boundary
    gap_size_percent: float
    created_at: datetime
    week_number: int
    respected: bool = False  # Has price respected this level?
    respect_count: int = 0  # Number of times price respected this zone
    
class NWOGDetector:
    """Detects New Week Opening Gaps for indices."""
    
    def __init__(self, min_gap_percent: float = 0.1):
        """
        Initialize NWOG detector.
        
        Args:
            min_gap_percent: Minimum gap size as percentage of price
        """
        self.min_gap_percent = min_gap_percent
        self.active_nwogs: List[NWOGZone] = []
        
    def detect_nwog(self, df: pd.DataFrame) -> Optional[NWOGZone]:
        """
        Detect New Week Opening Gap.
        
        Identifies gap between Friday close and Monday open.
        
        Args:
            df: DataFrame with daily or 4h data including day of week
            
        Returns:
            NWOGZone if gap detected, None otherwise
        """
        
    def check_nwog_respect(
        self,
        current_price: float,
        nwog_zone: NWOGZone,
        df_lower: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if price is respecting NWOG zone as support/resistance.
        
        For bearish NWOG (gap down):
        - Price should reject at gap high (resistance)
        - Look for bearish reversal patterns
        
        For bullish NWOG (gap up):
        - Price should reject at gap low (support)
        - Look for bullish reversal patterns
        
        Returns:
            (is_respected, rejection_description)
        """
        
    def calculate_nwog_targets(
        self,
        nwog_zone: NWOGZone,
        df: pd.DataFrame
    ) -> Tuple[float, float]:
        """
        Calculate target levels from NWOG zone.
        
        Targets based on:
        - Previous week's swing points
        - Liquidity pools below/above NWOG
        
        Returns:
            (target1, target2)
        """
        
    def get_active_nwogs(self, max_age_weeks: int = 4) -> List[NWOGZone]:
        """Get active NWOG zones (not older than max_age_weeks)."""
```

### DivergenceAnalyzer

```python
@dataclass
class DivergenceSignal:
    """Represents an inter-market divergence."""
    primary_symbol: str  # e.g., 'US30'
    reference_symbols: List[str]  # e.g., ['SPX', 'NDX']
    divergence_type: str  # 'bullish' or 'bearish'
    strength: float  # 0-100, based on magnitude
    detected_at: datetime
    primary_price: float
    primary_direction: str  # 'new_high', 'new_low', 'flat'
    reference_directions: Dict[str, str]  # symbol -> direction
    description: str
    
class DivergenceAnalyzer:
    """Analyzes inter-market divergence between correlated indices."""
    
    def __init__(self, correlation_threshold: float = 0.7):
        """
        Initialize divergence analyzer.
        
        Args:
            correlation_threshold: Minimum correlation to consider indices related
        """
        self.correlation_threshold = correlation_threshold
        self.price_history: Dict[str, List[float]] = {}  # symbol -> recent prices
        self.divergences: List[DivergenceSignal] = []
        
    def add_price_data(self, symbol: str, price: float, timestamp: datetime) -> None:
        """Add price data for a symbol."""
        
    def detect_divergence(
        self,
        primary_symbol: str,
        reference_symbols: List[str],
        lookback_periods: int = 20
    ) -> Optional[DivergenceSignal]:
        """
        Detect divergence between primary symbol and reference symbols.
        
        Divergence occurs when:
        - Primary makes new high but references don't (bearish divergence)
        - Primary makes new low but references don't (bullish divergence)
        
        Args:
            primary_symbol: The symbol to analyze (e.g., 'US30')
            reference_symbols: Symbols to compare against (e.g., ['SPX', 'NDX'])
            lookback_periods: Number of periods to look back for highs/lows
            
        Returns:
            DivergenceSignal if divergence detected, None otherwise
        """
        
    def calculate_divergence_strength(
        self,
        primary_move: float,
        reference_moves: List[float]
    ) -> float:
        """
        Calculate divergence strength (0-100).
        
        Higher strength when:
        - Primary move is large
        - Reference moves are small or opposite direction
        """
        
    def get_recent_divergences(self, max_age_hours: int = 24) -> List[DivergenceSignal]:
        """Get divergences detected within max_age_hours."""
```

## Data Models

### Symbol Configuration Schema

```json
{
  "symbols": {
    "BTC-USD": {
      "enabled": true,
      "asset_type": "crypto",
      "display_name": "Bitcoin",
      "emoji": "₿",
      "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
      "signal_rules": {
        "volume_spike_threshold": 0.8,
        "rsi_min": 30,
        "rsi_max": 70,
        "stop_loss_atr_multiplier": 1.5,
        "take_profit_atr_multiplier": 2.0,
        "min_confluence_factors": 4,
        "min_confidence_score": 4
      },
      "exit_rules": {
        "grace_period_minutes": 30,
        "min_profit_threshold_percent": 1.0,
        "max_giveback_percent": 40,
        "min_peak_profit_for_exit": 2.0
      },
      "volatility_thresholds": {
        "min_atr_percent": 0.5,
        "max_atr_percent": 10.0
      }
    },
    "ETH-USD": {
      "enabled": true,
      "asset_type": "crypto",
      "display_name": "Ethereum",
      "emoji": "Ξ",
      "timeframes": ["1m", "5m", "15m", "1h", "4h"],
      "signal_rules": {
        "volume_spike_threshold": 0.9,
        "rsi_min": 30,
        "rsi_max": 70,
        "stop_loss_atr_multiplier": 1.8,
        "take_profit_atr_multiplier": 2.2,
        "min_confluence_factors": 4,
        "min_confidence_score": 4
      },
      "exit_rules": {
        "grace_period_minutes": 30,
        "min_profit_threshold_percent": 1.2,
        "max_giveback_percent": 40,
        "min_peak_profit_for_exit": 2.0
      }
    },
    "EURUSD=X": {
      "enabled": true,
      "asset_type": "fx",
      "display_name": "EUR/USD",
      "emoji": "💱",
      "timeframes": ["5m", "15m", "1h", "4h"],
      "signal_rules": {
        "volume_spike_threshold": 1.2,
        "rsi_min": 35,
        "rsi_max": 65,
        "stop_loss_atr_multiplier": 1.2,
        "take_profit_atr_multiplier": 1.5,
        "min_confluence_factors": 5,
        "min_confidence_score": 4
      },
      "exit_rules": {
        "grace_period_minutes": 45,
        "min_profit_threshold_percent": 0.3,
        "max_giveback_percent": 35,
        "min_peak_profit_for_exit": 0.5
      },
      "trading_sessions": {
        "primary": ["London", "NewYork"],
        "secondary": ["Asian"],
        "require_primary_session": true
      }
    }
  },
  "global_settings": {
    "polling_interval_seconds": 60,
    "max_concurrent_symbols": 10,
    "signal_conflict_window_minutes": 5,
    "duplicate_signal_window_minutes": 10
  }
}
```

### Enhanced Signal Model

```python
@dataclass
class Signal:
    """Enhanced signal with symbol and timeframe context."""
    signal_type: str  # 'LONG' or 'SHORT'
    symbol: str  # e.g., 'BTC-USD'
    display_name: str  # e.g., 'Bitcoin'
    emoji: str  # e.g., '₿'
    asset_type: str  # 'crypto', 'fx', 'commodity'
    timeframe: str
    timestamp: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    breakeven: float
    atr: float
    risk_reward: float
    confidence: int
    strategy: str
    reasoning: str
    market_bias: str
    indicators: Dict[str, float]
    
    # New fields for filtering
    timeframe_rank: int  # From TIMEFRAME_HIERARCHY
    trading_session: Optional[str] = None  # For FX
    suppressed: bool = False
    suppression_reason: Optional[str] = None
```

### Trade Data Model

```python
@dataclass
class TradeData:
    """Enhanced trade tracking data."""
    trade_id: str
    symbol: str
    signal: Signal
    entry_time: datetime
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    breakeven: float
    
    # P&L tracking
    current_pnl_percent: float
    peak_pnl_percent: float
    peak_price: float
    peak_time: datetime
    
    # Exit signal tracking
    last_exit_signal_time: Optional[datetime] = None
    exit_signal_count: int = 0
    
    # Status
    status: str  # 'active', 'at_breakeven', 'closed'
    moved_to_breakeven: bool = False
```

## Error Handling

### Symbol Connection Failures

```python
def handle_symbol_connection_failure(symbol: str, error: Exception) -> None:
    """
    Handle connection failure for a symbol.
    
    Strategy:
    1. Log error with symbol context
    2. Attempt reconnection with exponential backoff
    3. If reconnection fails after 5 attempts, disable symbol temporarily
    4. Send alert to admin about disabled symbol
    5. Continue scanning other symbols
    """
```

### Invalid Configuration

```python
def handle_invalid_config(symbol: str, errors: List[str]) -> None:
    """
    Handle invalid symbol configuration.
    
    Strategy:
    1. Log validation errors
    2. Skip symbol initialization
    3. Continue with valid symbols
    4. Send alert about configuration issues
    """
```

### Signal Processing Errors

```python
def handle_signal_processing_error(
    symbol: str,
    timeframe: str,
    error: Exception
) -> None:
    """
    Handle error during signal processing.
    
    Strategy:
    1. Log error with full context
    2. Skip this scan iteration
    3. Continue with next timeframe/symbol
    4. Track error rate per symbol
    5. If error rate exceeds threshold, pause symbol temporarily
    """
```

## Testing Strategy

### Unit Tests

1. **SignalFilter Tests**
   - Test timeframe conflict detection
   - Test active trade conflict detection
   - Test duplicate signal suppression
   - Test FX session validation

2. **EnhancedTradeTracker Tests**
   - Test grace period enforcement
   - Test profit threshold validation
   - Test giveback percentage calculation
   - Test duplicate exit signal prevention

3. **AssetConfigManager Tests**
   - Test configuration loading
   - Test configuration validation
   - Test hot-reload functionality
   - Test symbol categorization

### Integration Tests

1. **Multi-Symbol Scanning**
   - Test parallel scanning of multiple symbols
   - Test signal coordination across symbols
   - Test resource usage with 10+ symbols

2. **Conflict Resolution**
   - Test LONG 15m + SHORT 1d scenario
   - Test multiple conflicting signals
   - Test timeframe hierarchy enforcement

3. **Exit Signal Filtering**
   - Test premature exit prevention
   - Test negative P&L exit suppression
   - Test grace period enforcement

### End-to-End Tests

1. **Full Scanner Lifecycle**
   - Start scanner with multiple symbols
   - Generate signals across timeframes
   - Track trades through lifecycle
   - Verify proper exit signal handling
   - Graceful shutdown

2. **Configuration Changes**
   - Add new symbol via config
   - Modify existing symbol parameters
   - Disable symbol
   - Verify hot-reload works correctly

## Performance Considerations

### Parallel Processing

- Use `threading` for concurrent symbol scanning
- Each SymbolScanner runs in its own thread
- Shared SignalFilter uses thread-safe data structures
- Maximum 10 concurrent symbols (configurable)

### Memory Management

- Limit candle buffer size per symbol (500 candles)
- Prune old signals from history (keep last 100 per symbol)
- Clear closed trades after 24 hours

### API Rate Limiting

- Yahoo Finance has no strict rate limits but implement backoff
- Stagger initial data fetches across symbols (1-second delay)
- Use polling interval of 60 seconds minimum

## Migration Path

### Phase 1: Add New Components (No Breaking Changes)
1. Create SymbolOrchestrator, SymbolScanner, SignalFilter
2. Create AssetConfigManager
3. Enhance TradeTracker with new exit logic
4. Add multi-symbol configuration file

### Phase 2: Create New Entry Points
1. Create `main_multi_symbol.py` for multi-symbol scanning
2. Create `start_multi_crypto.bat` and `start_multi_fx.bat`
3. Keep existing `main.py` and `main_swing.py` unchanged

### Phase 3: Testing and Validation
1. Run multi-symbol scanner alongside existing scanners
2. Compare signal quality and performance
3. Validate exit signal improvements

### Phase 4: Gradual Migration
1. Users can choose to use new multi-symbol scanner
2. Existing single-symbol scanners remain available
3. Eventually deprecate old scanners once validated

## Configuration Examples

### Crypto-Only Configuration

```json
{
  "scanner_type": "crypto_scalp",
  "symbols": {
    "BTC-USD": { "enabled": true, "timeframes": ["1m", "5m", "15m"] },
    "ETH-USD": { "enabled": true, "timeframes": ["1m", "5m", "15m"] },
    "SOL-USD": { "enabled": true, "timeframes": ["5m", "15m"] }
  }
}
```

### FX-Only Configuration

```json
{
  "scanner_type": "fx_scalp",
  "symbols": {
    "EURUSD=X": { "enabled": true, "timeframes": ["5m", "15m", "1h"] },
    "GBPUSD=X": { "enabled": true, "timeframes": ["5m", "15m", "1h"] },
    "USDJPY=X": { "enabled": true, "timeframes": ["5m", "15m", "1h"] }
  }
}
```

### Mixed Configuration

```json
{
  "scanner_type": "mixed_swing",
  "symbols": {
    "BTC-USD": { "enabled": true, "timeframes": ["15m", "1h", "4h", "1d"] },
    "ETH-USD": { "enabled": true, "timeframes": ["15m", "1h", "4h"] },
    "EURUSD=X": { "enabled": true, "timeframes": ["1h", "4h"] }
  }
}
```

### Indices Configuration with NWOG and Divergence

```json
{
  "scanner_type": "indices_swing",
  "symbols": {
    "^DJI": {
      "enabled": true,
      "display_name": "US30",
      "asset_type": "index",
      "timeframes": ["1h", "4h", "1d"],
      "enable_nwog": true,
      "enable_fvg": true,
      "nwog_config": {
        "min_gap_percent": 0.1,
        "max_age_weeks": 4
      }
    },
    "^GSPC": {
      "enabled": true,
      "display_name": "S&P500",
      "asset_type": "index",
      "timeframes": ["1h", "4h", "1d"],
      "enable_nwog": true,
      "enable_fvg": true
    },
    "^IXIC": {
      "enabled": true,
      "display_name": "Nasdaq",
      "asset_type": "index",
      "timeframes": ["1h", "4h", "1d"],
      "enable_nwog": true,
      "enable_fvg": true
    }
  },
  "divergence_analysis": {
    "enabled": true,
    "correlation_groups": [
      {
        "primary": "^DJI",
        "references": ["^GSPC", "^IXIC"],
        "lookback_periods": 20
      }
    ]
  }
}
```
