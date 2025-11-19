# Scanner System Enhancement - Design Document

## Overview

The scanner system enhancement implements a unified architecture for 8 independent trading scanners with improved signal detection strategies, data source reliability, and operational efficiency. The design consolidates duplicate code, implements proven trading strategies (Fibonacci Retracement, H4 HVG, Support/Resistance), and provides intelligent TP/SL calculation based on historical price action.

### Key Design Principles

1. **Unified Architecture**: Single codebase with symbol-specific configuration
2. **Strategy Modularity**: Pluggable strategy system allowing easy addition of new strategies
3. **Data Source Abstraction**: Unified data client with automatic fallback between sources
4. **Signal Quality**: Minimum 4 confluence factors with confidence scoring
5. **Operational Simplicity**: Single deployment and management scripts
6. **Reliability**: Automatic error recovery and data freshness validation

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scanner System Enhancement                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Configuration Management                     │  │
│  │  - Unified config structure (config.json)                │  │
│  │  - Symbol-specific overrides (asset_specific)            │  │
│  │  - Strategy configuration                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Data Source Management Layer                    │  │
│  │  - Unified Data Client (abstraction)                     │  │
│  │  - Binance WebSocket/REST                                │  │
│  │  - Twelve Data API                                       │  │
│  │  - Alpha Vantage API                                     │  │
│  │  - MT5 Connection                                        │  │
│  │  - Automatic fallback & retry logic                      │  │
│  │  - Data freshness validation                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Indicator Calculation Engine                      │  │
│  │  - EMA (9, 21, 50, 100, 200)                             │  │
│  │  - RSI, ADX, VWAP, ATR                                   │  │
│  │  - Volume MA, Bollinger Bands                            │  │
│  │  - Fibonacci Levels                                      │  │
│  │  - Support/Resistance Levels                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Unified Strategy Detection Engine                │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Strategy Modules (pluggable)                       │ │  │
│  │  │ - EMA Crossover                                    │ │  │
│  │  │ - Fibonacci Retracement                            │ │  │
│  │  │ - H4 HVG (Higher Volume Gap)                       │ │  │
│  │  │ - Support/Resistance Bounce                        │ │  │
│  │  │ - Mean Reversion                                   │ │  │
│  │  │ - Trend Alignment                                  │ │  │
│  │  │ - ADX/RSI Momentum                                 │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Signal Quality Filter                              │ │  │
│  │  │ - Confluence factor validation (min 4/7)           │ │  │
│  │  │ - Confidence scoring (1-5)                         │ │  │
│  │  │ - Duplicate detection                              │ │  │
│  │  │ - Risk/Reward validation (min 1.2:1)               │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      Intelligent TP/SL Calculation Engine                │  │
│  │  - Historical price action analysis (100+ candles)       │  │
│  │  - Mode-based SL/TP placement                            │  │
│  │  - Fallback to ATR-based calculation                     │  │
│  │  - Risk/Reward validation                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Unified Alerting System                          │  │
│  │  - Email (SMTP)                                          │  │
│  │  - Telegram Bot                                          │  │
│  │  - Excel Reporting                                       │  │
│  │  - Trade Tracking                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Scanner Orchestrator                             │  │
│  │  - Manages 8 scanner instances                           │  │
│  │  - Polling loop (10-second intervals)                    │  │
│  │  - Health monitoring                                     │  │
│  │  - Error recovery                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Unified Configuration System

**File**: `src/config_loader.py` (enhanced)

**Responsibilities**:
- Load configuration from JSON files
- Validate all required parameters
- Apply symbol-specific overrides
- Provide configuration to all components

**Key Methods**:
```python
class ConfigLoader:
    @staticmethod
    def load(config_path: str) -> Config
    @staticmethod
    def validate_config(config: dict) -> List[str]  # Returns warnings
    def get_asset_config(symbol: str) -> dict
    def get_strategy_config(strategy_name: str) -> dict
```

**Configuration Structure**:
```json
{
  "exchange": {
    "name": "hybrid",
    "symbol": "BTC/USD",
    "timeframes": ["1m", "5m", "15m", "4h"]
  },
  "data_providers": {
    "primary": "binance",
    "fallback": ["twelve_data", "alpha_vantage"],
    "retry_config": {
      "max_attempts": 3,
      "backoff_multiplier": 2,
      "initial_delay_seconds": 1
    }
  },
  "strategies": {
    "fibonacci_retracement": {
      "enabled": true,
      "swing_lookback": 50,
      "level_tolerance_percent": 0.5,
      "volume_threshold": 1.3
    },
    "h4_hvg": {
      "enabled": true,
      "min_gap_percent": 0.15,
      "volume_spike_threshold": 1.5
    },
    "support_resistance": {
      "enabled": true,
      "lookback_candles": 100,
      "min_touches": 2,
      "level_tolerance_percent": 0.3
    }
  },
  "asset_specific": {
    "BTC": {
      "min_confluence_factors": 4,
      "volume_thresholds": {...}
    },
    "XAUUSD": {...},
    "US30": {...}
  }
}
```

### 2. Unified Data Source Management

**File**: `src/unified_data_source.py` (new/enhanced)

**Responsibilities**:
- Abstract data source selection
- Implement automatic fallback logic
- Validate data freshness
- Handle retry logic with exponential backoff
- Cache data for fallback scenarios

**Key Methods**:
```python
class UnifiedDataClient:
    def get_latest_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = 500,
        validate_freshness: bool = True
    ) -> Tuple[pd.DataFrame, bool]  # Returns (data, is_fresh)
    
    def validate_data_freshness(
        self, 
        df: pd.DataFrame, 
        timeframe: str
    ) -> Tuple[bool, int]  # Returns (is_fresh, age_seconds)
    
    def _retry_with_backoff(
        self, 
        source: str, 
        max_attempts: int = 3
    ) -> Optional[pd.DataFrame]
    
    def _switch_data_source(self) -> bool
```

**Data Source Priority**:
1. Binance (primary, real-time)
2. Twelve Data (backup, reliable)
3. Alpha Vantage (fallback, slower)
4. MT5 (fallback, local)
5. Cached data (last resort)

### 3. Indicator Calculation Engine

**File**: `src/indicator_calculator.py` (enhanced)

**Responsibilities**:
- Calculate all technical indicators
- Add Fibonacci level calculation
- Add Support/Resistance level identification
- Optimize for performance

**New Methods**:
```python
class IndicatorCalculator:
    def calculate_fibonacci_levels(
        self, 
        df: pd.DataFrame, 
        lookback: int = 50
    ) -> Dict[str, float]
    
    def identify_support_resistance(
        self, 
        df: pd.DataFrame, 
        lookback: int = 100,
        tolerance_percent: float = 0.3
    ) -> Dict[str, List[float]]
    
    def calculate_swing_points(
        self, 
        df: pd.DataFrame, 
        lookback: int = 50
    ) -> Tuple[List[float], List[float]]  # (highs, lows)
```

### 4. Strategy Detection Engine

**File**: `src/strategy_detector.py` (new)

**Responsibilities**:
- Implement pluggable strategy system
- Coordinate multiple strategies
- Manage strategy priority based on market conditions
- Return highest-confidence signals

**Key Methods**:
```python
class StrategyDetector:
    def detect_signals(
        self, 
        data: pd.DataFrame, 
        timeframe: str,
        symbol: str,
        enabled_strategies: List[str]
    ) -> Optional[Signal]
    
    def _detect_fibonacci_retracement(
        self, 
        data: pd.DataFrame, 
        timeframe: str,
        symbol: str
    ) -> Optional[Signal]
    
    def _detect_h4_hvg(
        self, 
        data: pd.DataFrame, 
        timeframe: str,
        symbol: str
    ) -> Optional[Signal]
    
    def _detect_support_resistance(
        self, 
        data: pd.DataFrame, 
        timeframe: str,
        symbol: str
    ) -> Optional[Signal]
    
    def _get_strategy_priority(
        self, 
        market_conditions: Dict
    ) -> List[str]
```

**Strategy Priority Logic**:
- High volatility (ADX > 25): ADX/RSI Momentum, Momentum Shift, EMA Cloud Breakout
- Low volatility (ADX < 15): Mean Reversion, Support/Resistance, Fibonacci
- Strong trend (ADX > 20, EMA aligned): ADX/RSI Momentum, Trend Alignment, Key Level Break
- Ranging (ADX < 15, price between EMAs): Support/Resistance, Mean Reversion

### 5. Intelligent TP/SL Calculator

**File**: `src/sl_tp_calculator.py` (enhanced)

**Responsibilities**:
- Analyze historical price action
- Calculate mode-based SL/TP placement
- Validate risk/reward ratios
- Fall back to ATR-based calculation

**Key Methods**:
```python
class SLTPCalculator:
    def calculate_tp_sl(
        self, 
        entry_price: float,
        signal_type: str,  # "LONG" or "SHORT"
        data: pd.DataFrame,
        atr: float,
        strategy: str = "historical"  # "historical" or "atr"
    ) -> Tuple[float, float, float]  # (stop_loss, take_profit, risk_reward)
    
    def _analyze_historical_reversals(
        self, 
        data: pd.DataFrame,
        signal_type: str
    ) -> Dict[str, float]  # Returns mode distances
    
    def _calculate_mode_distance(
        self, 
        distances: List[float]
    ) -> float
    
    def _validate_risk_reward(
        self, 
        entry: float,
        sl: float,
        tp: float,
        min_ratio: float = 1.2
    ) -> bool
```

**Historical Analysis Algorithm**:
1. Analyze last 100+ candles
2. Identify all reversal points (local highs/lows)
3. Calculate distance from entry to each reversal
4. Find mode (most common distance)
5. Use mode as SL/TP basis
6. Validate minimum 1.2:1 risk/reward
7. Fall back to ATR if insufficient data

### 6. Signal Quality Filter

**File**: `src/signal_quality_filter.py` (enhanced)

**Responsibilities**:
- Validate confluence factors (minimum 4/7)
- Calculate confidence scores
- Detect and filter duplicates
- Validate risk/reward ratios

**Confluence Factors** (7 total):
1. Trend alignment (EMA cascade)
2. Volume confirmation (1.3x+ average)
3. RSI range validation (30-70)
4. Support/Resistance bounce
5. Fibonacci level proximity
6. H4 HVG gap fill
7. Reversal candle pattern (pin bar, engulfing, doji)

**Confidence Scoring**:
- 4 factors: Confidence 3/5
- 5 factors: Confidence 4/5
- 6+ factors: Confidence 5/5

### 7. Live and Future Signal Detection

**File**: `src/signal_detector.py` (enhanced)

**Responsibilities**:
- Detect live signals (current candle)
- Predict future signals (next 1-3 candles)
- Track signal materialization
- Send preparatory alerts for future signals

**Key Methods**:
```python
class SignalDetector:
    def detect_live_signals(
        self, 
        data: pd.DataFrame, 
        timeframe: str,
        symbol: str
    ) -> Optional[Signal]
    
    def predict_future_signals(
        self, 
        data: pd.DataFrame, 
        timeframe: str,
        symbol: str,
        lookahead_candles: int = 3
    ) -> List[FutureSignal]
    
    def track_future_signal_materialization(
        self, 
        future_signal: FutureSignal,
        current_data: pd.DataFrame
    ) -> Optional[Signal]
```

**Future Signal Prediction**:
- Analyze current candle formation
- Identify likely next candle patterns
- Calculate predicted entry/SL/TP
- Assign confidence based on pattern strength
- Send preparatory alert with "FUTURE" label
- Track for 3 candles, cancel if not materialized

### 8. Unified Scanner Orchestrator

**File**: `src/scanner_orchestrator.py` (new/enhanced)

**Responsibilities**:
- Manage 8 scanner instances
- Coordinate polling loop
- Handle health monitoring
- Manage error recovery

**Key Methods**:
```python
class ScannerOrchestrator:
    def __init__(self, config_path: str)
    
    def start_all_scanners(self) -> bool
    
    def stop_all_scanners(self) -> bool
    
    def restart_all_scanners(self) -> bool
    
    def get_scanner_status(self, scanner_name: str) -> Dict
    
    def get_all_scanner_status(self) -> Dict[str, Dict]
    
    def _polling_loop(self, scanner: Scanner) -> None
    
    def _health_check_loop(self) -> None
```

**Polling Loop** (10-second intervals):
1. Fetch latest data for each timeframe
2. Validate data freshness
3. Calculate indicators
4. Run strategy detection
5. Filter signals by quality
6. Send alerts
7. Update trade tracking
8. Log results to Excel

## Data Models

### Signal Data Model

```python
@dataclass
class Signal:
    timestamp: datetime
    signal_type: str  # "LONG" or "SHORT"
    timeframe: str
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    atr: float
    risk_reward: float
    market_bias: str  # "bullish", "bearish", "neutral"
    confidence: int  # 1-5
    indicators: Dict[str, float]
    strategy: str  # Strategy name
    confluence_factors: List[str]  # Factors that passed
    strategy_metadata: Dict  # Strategy-specific data
    signal_classification: str  # "LIVE" or "FUTURE"
```

### FutureSignal Data Model

```python
@dataclass
class FutureSignal:
    timestamp: datetime
    predicted_entry: float
    predicted_stop_loss: float
    predicted_take_profit: float
    confidence: float  # 0-1
    pattern_type: str  # Pattern that triggered prediction
    lookahead_candles: int
    materialized: bool = False
    materialized_signal: Optional[Signal] = None
```

## Error Handling

### Data Source Failures

```
Data Fetch Attempt
    ↓
Success? → Return Data
    ↓ No
Retry with Backoff (1s, 2s, 4s)
    ↓
Success? → Return Data
    ↓ No
Switch to Fallback Source
    ↓
Success? → Return Data (log switch)
    ↓ No
Use Cached Data (with staleness warning)
    ↓
Alert Operator (after 3 consecutive failures)
```

### Signal Detection Failures

```
Signal Detection
    ↓
Exception Caught? → Log Error
    ↓ Yes
Continue to Next Strategy
    ↓
All Strategies Failed? → Log "No signals detected"
    ↓ Yes
Continue Polling
```

### Configuration Validation

```
Load Configuration
    ↓
Validate Required Parameters
    ↓
Missing? → Fail Fast with Error Message
    ↓ No
Validate Parameter Ranges
    ↓
Out of Range? → Log Warning, Use Default
    ↓ No
Validate Data Source Availability
    ↓
No Sources? → Fail Fast
    ↓ No
Configuration Valid → Proceed
```

## Testing Strategy

### Unit Tests
- Indicator calculations (EMA, RSI, Fibonacci, S/R)
- Strategy detection logic
- TP/SL calculation (historical and ATR-based)
- Signal quality filtering
- Configuration validation

### Integration Tests
- End-to-end signal detection flow
- Data source fallback logic
- Multi-scanner coordination
- Alert delivery (email, Telegram)
- Trade tracking

### System Tests
- Full scanner operation (24+ hours)
- Data freshness validation
- Error recovery scenarios
- Performance under load
- Memory usage monitoring

## Deployment Architecture

### Directory Structure

```
/opt/trading-scanners/
├── src/                          # Core modules
│   ├── config_loader.py
│   ├── unified_data_source.py
│   ├── indicator_calculator.py
│   ├── strategy_detector.py
│   ├── signal_detector.py
│   ├── sl_tp_calculator.py
│   ├── signal_quality_filter.py
│   ├── alerter.py
│   ├── trade_tracker.py
│   └── ...
├── scanners/                     # Scanner implementations
│   ├── btc_scalp_scanner.py
│   ├── btc_swing_scanner.py
│   ├── gold_scalp_scanner.py
│   ├── gold_swing_scanner.py
│   ├── us30_scalp_scanner.py
│   ├── us30_swing_scanner.py
│   ├── us100_scanner.py
│   └── multi_crypto_scanner.py
├── config/                       # Configuration files
│   ├── config.json              # Main config
│   ├── config_btc_scalp.json    # Scanner-specific overrides
│   ├── config_btc_swing.json
│   └── ...
├── deployment/                   # Deployment scripts
│   ├── fresh_install.sh         # Install all services
│   ├── start_all_scanners.sh    # Start all scanners
│   ├── stop_all_scanners.sh     # Stop all scanners
│   └── restart_all_scanners.sh  # Restart all scanners
├── logs/                         # Log files
│   ├── scanner.log
│   ├── btc_scalp_scans.xlsx
│   └── ...
└── tests/                        # Test suite
    ├── test_strategies.py
    ├── test_data_sources.py
    ├── test_signal_quality.py
    └── ...
```

### Service Management

Each scanner runs as a systemd service:
- `btc-scalp-scanner.service`
- `btc-swing-scanner.service`
- `gold-scalp-scanner.service`
- `gold-swing-scanner.service`
- `us30-scalp-scanner.service`
- `us30-swing-scanner.service`
- `us100-scanner.service`
- `multi-crypto-scanner.service`

## Performance Considerations

### Data Processing
- Polling interval: 10 seconds
- Indicator calculation: < 100ms per timeframe
- Strategy detection: < 200ms per timeframe
- Signal quality filtering: < 50ms per signal
- Alert delivery: < 500ms per alert

### Memory Usage
- Target: < 500MB per scanner
- Data buffer: 500 candles per timeframe
- Signal history: 50 signals (deque)
- Indicator cache: 1000 values

### Network
- Data fetch: ~1KB per request
- Alert delivery: ~5KB per alert
- Polling frequency: 10 seconds
- Expected bandwidth: < 100KB/hour per scanner

## Security Considerations

- Configuration file permissions: 600 (owner read/write only)
- Credentials stored in environment variables or encrypted config
- No inbound network ports (outbound only)
- SSL/TLS for SMTP and API connections
- Service runs as dedicated non-root user
- Audit logging for all trades and alerts

