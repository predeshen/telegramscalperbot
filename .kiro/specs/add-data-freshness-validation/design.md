# Design Document

## Overview

This design addresses the critical issue of delayed trade notifications caused by stale market data. The scanner currently processes data without validating its freshness, leading to situations where TP/SL hits are detected hours after they actually occurred.

The solution implements:
1. **Data freshness validation** at the point of data retrieval
2. **Decoupled trade update logic** that runs independently of signal detection
3. **Automatic retry mechanisms** with exponential backoff
4. **Comprehensive alerting** for data quality issues
5. **Fallback strategies** to maintain trade monitoring even during data issues

## Architecture

### Current Flow (Problematic)
```
Main Loop (every 10s)
    ↓
Fetch Data → Process Data → Detect Signals → Update Trades
    ↓              ↓              ↓              ↓
  Stale?      Uses Stale    No Detection   Delayed Updates
```

**Problem:** If data is stale, everything downstream is affected, including trade updates.

### Proposed Flow (Improved)
```
Main Loop (every 10s)
    ↓
Fetch Data → Validate Freshness
    ↓              ↓
  Fresh?      Yes: Process → Detect Signals
    ↓         No: Retry (3x) → Alert
    ↓
ALWAYS: Update Trades (with best available price)
```

**Benefit:** Trade updates happen regardless of signal detection success.

## Components and Interfaces

### 1. MarketDataClient Enhancements

**New Method:**
```python
def validate_data_freshness(
    self, 
    df: pd.DataFrame, 
    timeframe: str, 
    max_age_seconds: Optional[int] = None
) -> tuple[bool, float]:
    """
    Validate that the latest candle is fresh enough for the given timeframe.
    
    Args:
        df: DataFrame with candlestick data
        timeframe: Timeframe string (e.g., '1m', '5m')
        max_age_seconds: Maximum acceptable age in seconds (optional, auto-calculated if None)
        
    Returns:
        Tuple of (is_fresh: bool, age_seconds: float)
    """
```

**Default Freshness Thresholds:**
```python
FRESHNESS_THRESHOLDS = {
    '1m': 90,      # 1.5 minutes
    '5m': 420,     # 7 minutes
    '15m': 1200,   # 20 minutes
    '1h': 5400,    # 90 minutes
    '4h': 18000,   # 5 hours
    '1d': 108000   # 30 hours
}
```

**Modified Method:**
```python
def get_latest_candles(
    self, 
    timeframe: str, 
    count: int = 500,
    validate_freshness: bool = True
) -> tuple[pd.DataFrame, bool]:
    """
    Fetch historical candlesticks with optional freshness validation.
    
    Returns:
        Tuple of (DataFrame, is_fresh: bool)
    """
```

### 2. Scanner Main Loop Restructuring

**New Helper Method:**
```python
def _get_current_price_for_trades(self) -> Optional[float]:
    """
    Get the most recent price for trade updates, using fallback strategies.
    
    Priority:
    1. Latest candle from primary timeframe (if fresh)
    2. Cached price from last successful fetch (if < 5 min old)
    3. None (skip trade updates)
    
    Returns:
        Current price or None if no valid price available
    """
```

**New Helper Method:**
```python
def _retry_fetch_with_backoff(
    self, 
    timeframe: str, 
    max_retries: int = 3
) -> tuple[Optional[pd.DataFrame], bool]:
    """
    Attempt to fetch fresh data with exponential backoff.
    
    Args:
        timeframe: Timeframe to fetch
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (DataFrame or None, is_fresh: bool)
    """
```

**Modified Main Loop Structure:**
```python
while self.running:
    try:
        # 1. Attempt to fetch data for each timeframe
        for timeframe in self.config.exchange.timeframes:
            df, is_fresh = self._fetch_and_validate_data(timeframe)
            
            if is_fresh:
                # Process normally: detect signals
                self._process_signals(df, timeframe)
            else:
                # Data is stale, retry with backoff
                df, is_fresh = self._retry_fetch_with_backoff(timeframe)
                
                if is_fresh:
                    self._process_signals(df, timeframe)
                else:
                    # Alert user after retries exhausted
                    self._send_stale_data_alert(timeframe)
        
        # 2. ALWAYS update trades (independent of signal detection)
        current_price = self._get_current_price_for_trades()
        if current_price:
            self.trade_tracker.update_trades(current_price, indicators)
        else:
            self._handle_trade_update_failure()
        
        time.sleep(10)
        
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        time.sleep(10)
```

### 3. State Tracking

**New Class Attributes:**
```python
class BTCScanner:
    def __init__(self):
        # ... existing attributes ...
        
        # Data freshness tracking
        self.last_fresh_data_time: Dict[str, datetime] = {}
        self.stale_data_count: Dict[str, int] = {}
        self.last_stale_alert_time: Dict[str, datetime] = {}
        
        # Trade update tracking
        self.last_trade_update_time: Optional[datetime] = None
        self.last_known_price: Optional[float] = None
        self.last_known_price_time: Optional[datetime] = None
        self.trade_update_failure_count: int = 0
```

## Data Models

### Data Freshness Result

```python
@dataclass
class DataFreshnessResult:
    """Result of data freshness validation."""
    is_fresh: bool
    age_seconds: float
    threshold_seconds: int
    timestamp: datetime
    timeframe: str
    
    def __str__(self) -> str:
        status = "FRESH" if self.is_fresh else "STALE"
        return f"{status}: {self.timeframe} data is {self.age_seconds:.1f}s old (threshold: {self.threshold_seconds}s)"
```

### Trade Update Status

```python
@dataclass
class TradeUpdateStatus:
    """Status of trade update attempt."""
    success: bool
    price_used: Optional[float]
    price_age_seconds: Optional[float]
    source: str  # "live", "cached", "failed"
    timestamp: datetime
```

## Error Handling

### Stale Data Detection

**Scenario:** Latest candle is older than threshold

**Handling:**
```python
if not is_fresh:
    logger.warning(
        f"Stale data detected for {timeframe}: "
        f"age={age_seconds:.1f}s, threshold={threshold}s"
    )
    
    # Increment stale counter
    self.stale_data_count[timeframe] += 1
    
    # Retry with backoff
    df, is_fresh = self._retry_fetch_with_backoff(timeframe)
    
    if not is_fresh:
        # Alert after 3 consecutive failures
        if self.stale_data_count[timeframe] >= 3:
            self._send_stale_data_alert(timeframe, age_seconds)
```

### Trade Update Failures

**Scenario:** Cannot get valid price for trade updates

**Handling:**
```python
if current_price is None:
    self.trade_update_failure_count += 1
    logger.error(
        f"Cannot update trades: no valid price available "
        f"(failures: {self.trade_update_failure_count})"
    )
    
    # Alert after 3 consecutive failures
    if self.trade_update_failure_count >= 3:
        self._send_trade_update_failure_alert()
```

### Exchange API Errors

**Scenario:** Exchange API returns error or timeout

**Handling:**
```python
try:
    df = self.market_client.get_latest_candles(timeframe, 500)
except ccxt.NetworkError as e:
    logger.error(f"Network error fetching {timeframe}: {e}")
    # Use cached data for trade updates
    return self._use_cached_data_for_trades()
except ccxt.ExchangeError as e:
    logger.error(f"Exchange error fetching {timeframe}: {e}")
    # Attempt reconnection
    self.market_client.reconnect()
```

## Alerting Strategy

### Stale Data Alert

**Trigger:** Data remains stale for 3+ consecutive attempts

**Message Format:**
```
⚠️ STALE DATA ALERT

Timeframe: 1m
Data Age: 15 minutes
Last Fresh: 08:30:00 UTC
Threshold: 90 seconds

The scanner is receiving outdated market data.
Trade monitoring may be delayed.

Actions:
• Check exchange API status
• Verify internet connection
• Scanner will continue retrying

⏰ 08:45:00 UTC
```

**Deduplication:** Max 1 alert per timeframe per 15 minutes

### Trade Update Failure Alert

**Trigger:** 3 consecutive failures to update trades

**Message Format:**
```
🚨 TRADE UPDATE FAILURE

Cannot update active trades due to stale data.
TP/SL notifications may be delayed.

Last Successful Update: 08:30:00 UTC
Active Trades: 2
Failure Count: 3

The scanner is attempting to recover.

⏰ 08:45:00 UTC
```

### Recovery Alert

**Trigger:** Data freshness restored after being stale

**Message Format:**
```
✅ DATA FRESHNESS RESTORED

Timeframe: 1m
Fresh data received after 15 minutes

Trade monitoring has resumed normally.

⏰ 08:45:30 UTC
```

## Testing Strategy

### Unit Tests

**Test: Data Freshness Validation**
```python
def test_validate_fresh_data():
    # Setup: Create DataFrame with recent timestamp
    # Action: Validate freshness
    # Assert: is_fresh = True, age < threshold

def test_validate_stale_data():
    # Setup: Create DataFrame with old timestamp
    # Action: Validate freshness
    # Assert: is_fresh = False, age > threshold
```

**Test: Retry Logic**
```python
def test_retry_with_backoff_success():
    # Setup: Mock fetch to fail twice, succeed third time
    # Action: Call retry_fetch_with_backoff
    # Assert: Returns fresh data, 3 attempts made

def test_retry_with_backoff_failure():
    # Setup: Mock fetch to always fail
    # Action: Call retry_fetch_with_backoff
    # Assert: Returns None, max retries reached
```

**Test: Trade Update Fallback**
```python
def test_trade_update_with_cached_price():
    # Setup: No fresh data, cached price < 5 min old
    # Action: Get current price for trades
    # Assert: Returns cached price

def test_trade_update_skip_old_cache():
    # Setup: No fresh data, cached price > 5 min old
    # Action: Get current price for trades
    # Assert: Returns None
```

### Integration Tests

**Test: End-to-End Stale Data Handling**
```python
def test_e2e_stale_data_recovery():
    # Setup: Scanner running, mock stale data
    # Action: Run main loop iterations
    # Assert: 
    #   - Stale data detected
    #   - Retries attempted
    #   - Alert sent
    #   - Trades still updated with cached price
```

**Test: Trade Updates During Data Issues**
```python
def test_trades_updated_despite_signal_failure():
    # Setup: Active trade, signal detection fails
    # Action: Run main loop
    # Assert: Trade still updated, TP detected
```

## Performance Considerations

### Validation Overhead

- Freshness check: O(1) - just timestamp comparison
- Minimal impact: < 1ms per check
- Performed once per timeframe per loop iteration

### Retry Delays

- First retry: 5 seconds
- Second retry: 10 seconds  
- Third retry: 30 seconds
- Total max delay: 45 seconds before giving up

**Trade-off:** Slight delay in signal detection vs. ensuring data quality

### Memory Usage

- New state tracking: ~1KB per timeframe
- Cached price data: negligible
- No significant memory impact

## Implementation Notes

### Backward Compatibility

- Existing scanner code continues to work
- Freshness validation can be disabled via flag
- No changes to signal detection logic required
- Trade tracker interface unchanged

### Configuration

Add to config file:
```python
[data_quality]
enable_freshness_validation = true
custom_thresholds = {
    "1m": 90,
    "5m": 420
}
alert_on_stale_data = true
max_cached_price_age_seconds = 300
```

### Logging Levels

- **DEBUG:** Every freshness check result
- **INFO:** Fresh data restored after being stale
- **WARNING:** Stale data detected, using cached price
- **ERROR:** Cannot update trades, all retries failed

### Deployment Strategy

1. Deploy to test environment first
2. Monitor logs for false positives (data flagged as stale incorrectly)
3. Adjust thresholds if needed based on exchange behavior
4. Roll out to production scanners gradually
5. Monitor alert frequency and adjust deduplication window
