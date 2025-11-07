# Design Document

## Overview

This design addresses the critical issues in the multi-asset trading scanner system by implementing a unified data source architecture, fixing symbol identification throughout the signal pipeline, and enhancing signal quality with confidence scoring. The solution migrates all scanners from mixed data sources (Kraken, Binance) to Yahoo Finance for consistency, implements proper symbol context propagation, and adds validation layers to ensure signal quality and MT5 compatibility.

**Design Rationale**: Yahoo Finance was chosen as the unified data source because it provides institutional-grade pricing for all three assets (BTC, Gold, US30) and offers pricing closer to MT5 broker feeds than crypto-specific exchanges. This addresses the core issue of price discrepancies between scanner alerts and live trading platforms.

## Architecture

### Current Architecture Issues

1. **Fragmented Data Sources**: BTC scalp scanner uses Kraken/Binance, while swing/Gold/US30 use Yahoo Finance
2. **Symbol Context Loss**: Signal objects don't properly carry symbol information through the pipeline
3. **Inconsistent Signal Quality**: Different scanners have different quality thresholds
4. **No Price Validation**: System accepts any price data without anomaly detection
5. **MT5 Price Mismatch**: Crypto exchange prices differ significantly from broker prices

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Scanner Orchestrator                      │
│  (Manages multiple asset scanners with unified config)      │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────────┬────────────────┐
        │                     │              │                │
┌───────▼────────┐   ┌────────▼──────┐  ┌───▼──────────┐  ┌──▼──────────┐
│  BTC Scanner   │   │  Gold Scanner │  │ US30 Scanner │  │ Config Mgr  │
│  (Scalp/Swing) │   │ (Scalp/Swing) │  │(Scalp/Swing) │  │             │
└───────┬────────┘   └────────┬──────┘  └───┬──────────┘  └──┬──────────┘
        │                     │              │                │
        └──────────┬──────────┴──────────────┘                │
                   │                                           │
        ┌──────────▼───────────────────────────────────────────▼──┐
        │         Unified Data Source Layer                       │
        │  (YFinanceClient with symbol mapping & validation)      │
        │  - BTC-USD, GC=F, ^DJI                                  │
        │  - Connection retry with exponential backoff            │
        └──────────┬──────────────────────────────────────────────┘
                   │
        ┌──────────▼──────────┬──────────────┬────────────────┬────────────┐
        │                     │              │                │            │
┌───────▼────────┐   ┌────────▼──────┐  ┌───▼──────────┐  ┌──▼──────────┐  ┌──▼──────────┐
│  Indicator     │   │ Signal        │  │ Price        │  │ Symbol      │  │ News        │
│  Calculator    │   │ Detector      │  │ Validator    │  │ Context     │  │ Calendar    │
│                │   │ (w/ symbol)   │  │ (anomaly)    │  │ Manager     │  │ (shared)    │
└───────┬────────┘   └────────┬──────┘  └───┬──────────┘  └──┬──────────┘  └──┬──────────┘
        │                     │              │                │                │
        └──────────┬──────────┴──────────────┴────────────────┴────────────────┘
                   │
        ┌──────────▼──────────────────────────────────────────┐
        │         Signal Quality Filter                        │
        │  (Confidence scoring, duplicate detection)           │
        │  - Min 3-factor confluence                           │
        │  - 1-5 confidence scale                              │
        │  - Duplicate suppression                             │
        └──────────┬──────────────────────────────────────────┘
                   │
        ┌──────────▼──────────┬──────────────┬────────────────┐
        │                     │              │                │
┌───────▼────────┐   ┌────────▼──────┐  ┌───▼──────────┐  ┌──▼──────────┐
│  Alerter       │   │ Trade Tracker │  │ Excel        │  │ Health      │
│  (Telegram)    │   │               │  │ Reporter     │  │ Monitor     │
│  Asset-specific│   │               │  │              │  │             │
└────────────────┘   └───────────────┘  └──────────────┘  └─────────────┘
```

## Components and Interfaces

### 1. Unified Data Source Layer

**Purpose**: Provide consistent market data across all scanners with validation and MT5-compatible pricing

**Design Rationale**: Centralizing data source logic eliminates inconsistencies and allows for unified validation, retry logic, and symbol mapping. Using Yahoo Finance institutional symbols (BTC-USD, GC=F, ^DJI) provides pricing closer to broker feeds than crypto exchanges.

**Interface**:
```python
class UnifiedDataSource:
    """
    Unified data source interface for all scanners
    """
    def __init__(self, config: DataSourceConfig):
        self.provider = "yfinance"
        self.symbol_map = config.symbol_map  # Maps internal symbols to YF symbols
        self.retry_config = config.retry_config
        self.validator = PriceValidator()
        
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        """
        Fetch OHLCV data with validation and retry logic
        
        Args:
            symbol: Internal symbol (BTC, XAUUSD, US30)
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            
        Returns:
            List of validated Candle objects with symbol context
            
        Raises:
            DataSourceError: If connection fails after retries
            ValidationError: If data quality checks fail
        """
        pass
        
    def get_yfinance_symbol(self, internal_symbol: str) -> str:
        """
        Map internal symbol to Yahoo Finance symbol
        
        BTC -> BTC-USD
        XAUUSD -> GC=F (Gold Futures)
        US30 -> ^DJI (Dow Jones Industrial Average)
        """
        pass
        
    def reconnect_with_backoff(self, max_retries: int = 5) -> bool:
        """
        Attempt reconnection with exponential backoff
        """
        pass

class DataSourceConfig:
    """Configuration for unified data source"""
    provider: str = "yfinance"
    symbol_map: Dict[str, str] = {
        "BTC": "BTC-USD",
        "XAUUSD": "GC=F",
        "US30": "^DJI"
    }
    retry_config: RetryConfig
    validation_config: ValidationConfig
```

### 2. Price Validator

**Purpose**: Detect anomalous price data and ensure data quality

**Design Rationale**: Price validation prevents bad data from generating false signals. The 0.5% threshold for normal candles and 5% for anomaly flagging balances sensitivity with crypto/index volatility. Three consecutive failures trigger a safety pause to prevent cascading errors.

**Interface**:
```python
class PriceValidator:
    """
    Validates price data for anomalies and quality issues
    """
    def validate_candle(self, current: Candle, previous: Candle) -> ValidationResult:
        """
        Validate candle against previous candle
        
        Checks:
        - Price change within 0.5% (normal) or flags if >5% (anomaly)
        - Volume > 0
        - Timestamp within acceptable range (not future, not >1hr old)
        - OHLC relationships (high >= low, etc.)
        
        Returns:
            ValidationResult with status and any warnings/errors
        """
        pass
        
    def check_price_change(self, current_price: float, previous_price: float) -> Tuple[bool, float]:
        """
        Check if price change is within acceptable range
        Returns: (is_valid, percent_change)
        """
        pass
        
    def check_volume(self, volume: float) -> bool:
        """Validate volume is positive"""
        pass
        
    def check_timestamp(self, timestamp: datetime) -> bool:
        """Validate timestamp is not in future or too old"""
        pass

class ValidationResult:
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    percent_change: float
```

### 3. Symbol Context Manager

**Purpose**: Ensure symbol information is properly propagated through the entire signal pipeline

**Design Rationale**: Symbol context loss was a critical bug causing all alerts to show "BTC". By making symbol a required, validated field in signal objects and tracking it through the pipeline, we ensure accurate alert labeling.

**Interface**:
```python
class SymbolContext:
    """
    Manages symbol context throughout signal pipeline
    """
    def __init__(self, symbol: str, display_name: str, asset_type: str):
        self.symbol = symbol  # Internal symbol (BTC, XAUUSD, US30)
        self.display_name = display_name  # Display name for alerts
        self.asset_type = asset_type  # crypto, commodity, index
        self.yf_symbol = None  # Yahoo Finance symbol
        self.emoji = self._get_emoji()
        
    def _get_emoji(self) -> str:
        """Get asset-specific emoji for alerts"""
        emoji_map = {
            "BTC": "₿",
            "XAUUSD": "🥇",
            "US30": "📊"
        }
        return emoji_map.get(self.symbol, "📈")
        
    def validate(self) -> bool:
        """Ensure symbol is not null or empty"""
        return bool(self.symbol and self.symbol.strip())

class Signal:
    """
    Enhanced signal object with symbol context
    """
    symbol_context: SymbolContext  # Required field
    direction: str  # LONG or SHORT
    entry_price: float
    confidence_score: int  # 1-5
    indicators: Dict[str, Any]
    timestamp: datetime
    
    def __post_init__(self):
        """Validate symbol context on creation"""
        if not self.symbol_context.validate():
            raise ValueError("Signal must have valid symbol context")
```

### 4. Signal Quality Filter

**Purpose**: Ensure only high-quality signals are sent to traders

**Design Rationale**: The 3-factor confluence requirement (trend + volume + momentum) reduces false signals. Confidence scoring (1-5) helps traders prioritize signals. Duplicate suppression within time windows prevents alert fatigue.

**Interface**:
```python
class SignalQualityFilter:
    """
    Filters signals based on quality criteria and confidence scoring
    """
    def __init__(self, config: QualityConfig):
        self.min_confluence_factors = 3
        self.min_confidence_score = 3
        self.duplicate_window_seconds = 300  # 5 minutes
        self.recent_signals = {}  # Track recent signals per symbol
        
    def evaluate_signal(self, signal: Signal, market_data: Dict) -> FilterResult:
        """
        Evaluate signal quality and calculate confidence score
        
        Confluence factors:
        - Trend alignment (price above/below key MAs)
        - Volume confirmation (volume > average)
        - Momentum (RSI, MACD alignment)
        - Support/Resistance proximity
        - Multi-timeframe confirmation
        
        Returns:
            FilterResult with pass/fail and confidence score
        """
        pass
        
    def calculate_confidence_score(self, confluence_factors: List[str]) -> int:
        """
        Calculate 1-5 confidence score based on confluence
        
        1-2: Weak (2 factors) - Not sent
        3: Moderate (3 factors) - Sent with caution
        4: Strong (4 factors) - Good signal
        5: Very Strong (5+ factors) - High probability
        """
        pass
        
    def check_duplicate(self, signal: Signal) -> bool:
        """
        Check if similar signal was sent recently for this symbol
        """
        pass
        
    def suppress_duplicate(self, signal: Signal, reason: str):
        """
        Log duplicate suppression with reason
        """
        pass

class QualityConfig:
    min_confluence_factors: int = 3
    min_confidence_score: int = 3
    duplicate_window_seconds: int = 300
    confluence_weights: Dict[str, float]  # Weight each factor
```

### 5. Asset-Specific Alerter

**Purpose**: Format alerts with asset-specific context and proper symbol identification

**Design Rationale**: Different assets have different relevant context (BTC dominance vs Gold session vs US30 market hours). Asset-specific formatting makes alerts more actionable. Distinct emojis provide quick visual identification.

**Interface**:
```python
class AssetSpecificAlerter:
    """
    Formats and sends alerts with asset-specific context
    """
    def __init__(self, telegram_config: TelegramConfig):
        self.telegram = TelegramClient(telegram_config)
        self.formatters = {
            "BTC": BTCAlertFormatter(),
            "XAUUSD": GoldAlertFormatter(),
            "US30": US30AlertFormatter()
        }
        
    def send_alert(self, signal: Signal):
        """
        Send alert with asset-specific formatting
        """
        formatter = self.formatters.get(signal.symbol_context.symbol)
        alert_text = formatter.format(signal)
        self.telegram.send_message(alert_text)
        
class BTCAlertFormatter:
    """Format BTC-specific alerts"""
    def format(self, signal: Signal) -> str:
        """
        Format BTC alert with:
        - ₿ emoji
        - BTC dominance (if available)
        - Entry price (2 decimals)
        - Confidence score
        - Disclaimer about indicative pricing
        """
        pass

class GoldAlertFormatter:
    """Format Gold-specific alerts"""
    def format(self, signal: Signal) -> str:
        """
        Format Gold alert with:
        - 🥇 emoji
        - Trading session (Asian/London/NY)
        - Spread status
        - Key levels proximity
        - Entry price (2 decimals)
        - Confidence score
        """
        pass

class US30AlertFormatter:
    """Format US30-specific alerts"""
    def format(self, signal: Signal) -> str:
        """
        Format US30 alert with:
        - 📊 emoji
        - Market hours status
        - Trend strength
        - Entry price (2 decimals)
        - Confidence score
        """
        pass
```

### 6. Configuration Manager

**Purpose**: Centralized configuration with validation and hot-reload support

**Design Rationale**: Centralized config eliminates code changes for symbol updates. Validation prevents runtime errors from bad config. Hot-reload allows adjustments without full restart, critical for production systems.

**Interface**:
```python
class ConfigurationManager:
    """
    Manages centralized configuration for all scanners
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.last_modified = None
        
    def load_config(self) -> UnifiedConfig:
        """
        Load and validate configuration
        
        Raises:
            ConfigValidationError: If required fields missing or invalid
        """
        pass
        
    def validate_config(self, config: Dict) -> ValidationResult:
        """
        Validate configuration structure and values
        
        Required fields:
        - data_source.provider
        - data_source.symbol_map
        - scanners (list of scanner configs)
        - Each scanner: symbol, timeframes, strategy
        """
        pass
        
    def hot_reload(self) -> bool:
        """
        Check for config changes and reload if modified
        Returns: True if config was reloaded
        """
        pass
        
    def get_scanner_config(self, symbol: str, mode: str) -> ScannerConfig:
        """
        Get configuration for specific scanner
        
        Args:
            symbol: BTC, XAUUSD, US30
            mode: scalp or swing
        """
        pass

class UnifiedConfig:
    """Unified configuration structure"""
    data_source: DataSourceConfig
    scanners: List[ScannerConfig]
    quality_filter: QualityConfig
    alerter: AlerterConfig
    health_monitor: HealthConfig
```

### 7. Multi-Scanner Coordinator

**Purpose**: Coordinate signal generation across multiple scanners to prevent alert flooding

**Design Rationale**: The 30-second gap between alerts prevents overwhelming traders. The 5 signals/hour threshold detects potential over-trading conditions. Health monitoring ensures all scanners are functioning properly.

**Interface**:
```python
class MultiScannerCoordinator:
    """
    Coordinates multiple scanners and manages alert flow
    """
    def __init__(self, config: CoordinatorConfig):
        self.scanners = {}  # symbol -> scanner instance
        self.alert_queue = PriorityQueue()  # Timestamp-ordered queue
        self.min_alert_gap_seconds = 30
        self.max_signals_per_hour = 5
        self.signal_history = {}  # Track signals per scanner
        
    def register_scanner(self, symbol: str, scanner: Scanner):
        """Register a scanner instance"""
        pass
        
    def queue_alert(self, signal: Signal):
        """
        Add signal to alert queue with timestamp
        """
        pass
        
    def process_alert_queue(self):
        """
        Process queued alerts with minimum gap enforcement
        """
        pass
        
    def check_signal_rate(self, symbol: str) -> Tuple[bool, int]:
        """
        Check if scanner is generating excessive signals
        Returns: (is_excessive, signals_last_hour)
        """
        pass
        
    def get_health_status(self) -> Dict[str, ScannerHealth]:
        """
        Get health status for all scanners
        
        Checks:
        - Last signal time (warn if >24h)
        - Error count
        - Data source connection status
        """
        pass
        
    def send_heartbeat(self):
        """
        Send periodic heartbeat with all scanner statuses
        """
        pass

class ScannerHealth:
    symbol: str
    status: str  # healthy, warning, error
    last_signal_time: datetime
    signals_24h: int
    error_count: int
    data_source_connected: bool
```

### 8. News Calendar Integration

**Purpose**: Pause trading around high-impact economic events to avoid volatile, unpredictable price action

**Design Rationale**: High-impact USD news (NFP, FOMC, CPI) causes extreme volatility across all assets (BTC, Gold, US30). The current implementation only protects Gold scanners, but BTC and US30 are equally affected by USD news. Extending news calendar to all scanners prevents losses during news spikes. The 30-minute pre-news pause and 5-minute post-news delay provide safety buffers.

**Current State**: News calendar exists only for Gold (xauusd_scanner/news_calendar.py) and needs to be generalized for all assets.

**Interface**:
```python
class NewsCalendar:
    """
    Manages economic calendar and trading pauses around news events
    Currently Gold-specific, needs to be asset-agnostic
    """
    def __init__(self, events_file: str = "news_events.json"):
        self.events_file = Path(events_file)
        self.events: List[NewsEvent] = []
        self.pause_window_minutes = 30  # Pause 30 min before news
        self.resume_delay_minutes = 5   # Resume 5 min after news
        
    def load_events(self) -> None:
        """Load news events from JSON file"""
        pass
        
    def is_news_imminent(self, current_time: Optional[datetime] = None,
                        impact_filter: Optional[List[str]] = None) -> Tuple[bool, Optional[NewsEvent]]:
        """
        Check if high-impact news is imminent (within pause window)
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            impact_filter: List of impact levels to check (defaults to ['high'])
            
        Returns:
            Tuple of (is_imminent, event)
        """
        pass
        
    def should_pause_trading(self, current_time: Optional[datetime] = None) -> Tuple[bool, Optional[str]]:
        """
        Determine if trading should be paused due to news
        
        Returns:
            Tuple of (should_pause, reason)
        """
        pass
        
    def get_news_status(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get comprehensive news status including upcoming events
        """
        pass
        
    def cleanup_past_events(self, days_old: int = 7) -> int:
        """Remove events older than specified days"""
        pass

class NewsEvent:
    """Represents a single news event"""
    title: str
    datetime_gmt: datetime
    impact: str  # low, medium, high
    currency: str  # USD, EUR, GBP, etc.
    description: str
    
class NewsUpdater:
    """
    Utilities for updating and managing news events
    Provides manual event addition and cleanup
    """
    def add_manual_event(self, title: str, date_str: str, time_str: str,
                        impact: str = "high", currency: str = "USD") -> None:
        """Add a manual event to the calendar"""
        pass
        
    def add_weekly_events(self) -> None:
        """Add common weekly recurring events (e.g., NFP on first Friday)"""
        pass
        
    def cleanup_old_events(self, days_old: int = 7) -> int:
        """Remove events older than specified days"""
        pass
```

**Migration Plan for News Calendar**:
1. Move news_calendar.py from xauusd_scanner/ to src/ (make it shared)
2. Update all scanners (BTC, Gold, US30) to use NewsCalendar
3. Centralize news_events.json in config/ directory
4. Add news calendar check to MultiScannerCoordinator
5. Ensure news pause applies to all assets, not just Gold

**Asset-Specific News Considerations**:
- **BTC**: Affected by USD news (FOMC, CPI, NFP) but also crypto-specific events (ETF decisions, regulatory news)
- **Gold**: Affected by USD news, geopolitical events, central bank decisions
- **US30**: Affected by USD news, earnings seasons, economic data

For this migration, focus on USD news that affects all assets. Asset-specific news can be added later.

### 9. Health Monitor

**Purpose**: Monitor system health and detect issues before they impact trading

**Design Rationale**: Proactive monitoring prevents silent failures. The 3 consecutive failures threshold triggers safety pause to prevent bad data from generating false signals. Administrator alerts ensure issues are addressed quickly.

**Interface**:
```python
class HealthMonitor:
    """
    Monitors system health and data quality
    """
    def __init__(self, config: HealthConfig):
        self.data_quality_failures = {}  # Track failures per scanner
        self.max_consecutive_failures = 3
        self.paused_scanners = set()
        
    def record_data_quality_issue(self, symbol: str, issue: str):
        """
        Record data quality issue and check if pause needed
        """
        pass
        
    def should_pause_scanner(self, symbol: str) -> bool:
        """
        Check if scanner should be paused due to consecutive failures
        """
        pass
        
    def pause_scanner(self, symbol: str, reason: str):
        """
        Pause scanner and send administrator alert
        """
        pass
        
    def resume_scanner(self, symbol: str):
        """
        Resume paused scanner after manual intervention
        """
        pass
        
    def send_admin_alert(self, message: str, severity: str):
        """
        Send alert to system administrator
        """
        pass
```

## Data Models

### Candle
```python
@dataclass
class Candle:
    """OHLCV candle with symbol context"""
    symbol: str  # Required - internal symbol
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str
    
    def validate_ohlc(self) -> bool:
        """Validate OHLC relationships"""
        return (self.high >= self.low and 
                self.high >= self.open and 
                self.high >= self.close and
                self.low <= self.open and 
                self.low <= self.close)
```

### Signal
```python
@dataclass
class Signal:
    """Trading signal with full context"""
    symbol_context: SymbolContext
    direction: str  # LONG or SHORT
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence_score: int  # 1-5
    confluence_factors: List[str]
    indicators: Dict[str, Any]
    timestamp: datetime
    timeframe: str
    
    def get_precision(self) -> int:
        """Get decimal precision for entry price based on asset"""
        precision_map = {
            "BTC": 2,
            "XAUUSD": 2,
            "US30": 2
        }
        return precision_map.get(self.symbol_context.symbol, 2)
```

### Configuration Models
```python
@dataclass
class ScannerConfig:
    """Configuration for individual scanner"""
    symbol: str
    mode: str  # scalp or swing
    timeframes: List[str]
    strategy: str
    enabled: bool = True
    
@dataclass
class RetryConfig:
    """Retry configuration for data source"""
    max_retries: int = 5
    initial_delay_seconds: int = 1
    max_delay_seconds: int = 60
    exponential_base: float = 2.0
    
@dataclass
class ValidationConfig:
    """Validation thresholds"""
    max_normal_price_change_percent: float = 0.5
    max_anomaly_price_change_percent: float = 5.0
    max_timestamp_age_hours: int = 1
    min_volume: float = 0.0
```

## Error Handling

### Error Categories

1. **Data Source Errors**
   - Connection failures: Retry with exponential backoff
   - Invalid data: Log and skip candle
   - Rate limiting: Respect limits and queue requests

2. **Validation Errors**
   - Price anomalies: Flag and log, continue with warning
   - Volume issues: Reject candle
   - Timestamp issues: Reject candle
   - 3 consecutive failures: Pause scanner and alert admin

3. **Configuration Errors**
   - Missing required fields: Fail fast with clear error message
   - Invalid values: Fail fast with validation details
   - File not found: Fail fast with path information

4. **Signal Processing Errors**
   - Missing symbol context: Reject signal and log error
   - Invalid confidence score: Default to minimum (3)
   - Duplicate detection failure: Log and continue

### Error Recovery Strategies

**Data Source Connection Loss**:
```python
def handle_connection_loss(self, error: Exception):
    """
    1. Log error with full context
    2. Attempt reconnection with exponential backoff
    3. If max retries exceeded, pause scanner
    4. Send admin alert if paused
    """
    pass
```

**Data Quality Issues**:
```python
def handle_data_quality_issue(self, issue: ValidationResult):
    """
    1. Log issue with specific details
    2. Increment failure counter for scanner
    3. If <3 failures, continue with next candle
    4. If 3 consecutive failures, pause scanner and alert admin
    """
    pass
```

**Configuration Errors**:
```python
def handle_config_error(self, error: ConfigValidationError):
    """
    1. Log error with specific field and issue
    2. Do not start scanner
    3. Exit with error code
    4. Provide clear fix instructions in error message
    """
    pass
```

## Testing Strategy

### Unit Tests

1. **Data Source Layer**
   - Symbol mapping (BTC -> BTC-USD, etc.)
   - Retry logic with exponential backoff
   - Error handling for connection failures

2. **Price Validator**
   - Price change validation (0.5%, 5% thresholds)
   - Volume validation
   - Timestamp validation
   - OHLC relationship validation

3. **Symbol Context**
   - Symbol validation (not null/empty)
   - Emoji mapping
   - Display name formatting

4. **Signal Quality Filter**
   - Confluence factor counting
   - Confidence score calculation
   - Duplicate detection within time window

5. **Alert Formatters**
   - Asset-specific formatting (BTC, Gold, US30)
   - Price precision (2 decimals)
   - Emoji inclusion

### Integration Tests

1. **End-to-End Signal Flow**
   - Data fetch -> Validation -> Signal detection -> Quality filter -> Alert
   - Verify symbol context maintained throughout
   - Verify confidence scoring applied

2. **Multi-Scanner Coordination**
   - Multiple scanners generating signals
   - Alert queue processing with 30s gaps
   - Signal rate limiting (5/hour)

3. **Error Recovery**
   - Connection loss and reconnection
   - Data quality issues and scanner pause
   - Configuration reload

4. **Configuration Management**
   - Load valid configuration
   - Reject invalid configuration
   - Hot-reload on file change

### Manual Testing

1. **Price Accuracy Verification**
   - Compare scanner prices with MT5 broker prices
   - Verify <0.5% difference for normal conditions
   - Test with BTC, Gold, US30

2. **Alert Verification**
   - Verify correct symbol in alerts
   - Verify asset-specific context included
   - Verify confidence scores displayed

3. **Health Monitoring**
   - Trigger data quality issues
   - Verify scanner pause after 3 failures
   - Verify admin alerts sent

## Migration Strategy

### Phase 1: Data Source Migration
1. Update BTC scalp scanner to use YFinanceClient
2. Implement symbol mapping (BTC -> BTC-USD)
3. Add price validation layer
4. Test price accuracy against MT5

### Phase 2: Symbol Context Fix
1. Add SymbolContext to Signal objects
2. Update all signal detectors to include symbol
3. Validate symbol propagation through pipeline
4. Update alert formatters to use symbol context

### Phase 3: News Calendar Integration
1. Move news_calendar.py from xauusd_scanner/ to src/ (make it shared)
2. Move news_events.json to config/ directory
3. Update all scanners (BTC, Gold, US30) to integrate NewsCalendar
4. Test news pause functionality across all assets
5. Add news status to heartbeat messages

### Phase 4: Quality Enhancement
1. Implement SignalQualityFilter
2. Add confidence scoring
3. Add duplicate detection
4. Test signal quality improvements

### Phase 5: Multi-Scanner Coordination
1. Implement MultiScannerCoordinator
2. Add alert queue with gap enforcement
3. Add signal rate monitoring
4. Implement health monitoring
5. Integrate news calendar with coordinator

### Rollback Plan
- Keep existing data source code until Phase 1 validated
- Feature flags for quality filter (can disable if issues)
- Configuration-based scanner enable/disable
- Separate deployment per scanner (can rollback individually)
- News calendar can be disabled per scanner via config