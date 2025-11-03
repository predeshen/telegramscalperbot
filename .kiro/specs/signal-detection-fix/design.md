# Design Document: Signal Detection Fix and Infrastructure Improvement

## Overview

This design addresses critical issues in the trading scanner system where valid trading signals are not being detected despite clear market setups. The root causes are:

1. **Indicator Calculation Failures**: NaN values in calculated indicators due to insufficient data or calculation errors
2. **Data Fetching Issues**: Inconsistent candle counts and period calculations, especially for YFinance client
3. **Signal Detection Logic Gaps**: Missing validation of indicator values before applying signal rules
4. **Infrastructure Instability**: Running in screen sessions causes crashes; need systemd services with WebSocket support
5. **Insufficient Logging**: Difficult to diagnose why signals are missed

The solution involves fixing the data pipeline, improving indicator calculations, enhancing signal detection logic, and migrating to a stable systemd-based deployment with WebSocket support for Kraken.

## Architecture

### Current Architecture (Problematic)
```
[Exchange API] → [Market Data Client] → [Indicator Calculator] → [Signal Detector] → [Alerter]
     ↓                    ↓                       ↓                      ↓
  REST Polling      200 candles buffer      NaN values          Signals missed
  (every 10-60s)    (insufficient)         (no validation)     (logic fails)
```

### Improved Architecture
```
[Exchange API] ←WebSocket→ [Market Data Client] → [Indicator Calculator] → [Signal Detector] → [Alerter]
     ↓                           ↓                        ↓                       ↓
Real-time data          500+ candles buffer      Validated values         Signals detected
(Kraken WS)            (sufficient history)     (error handling)        (robust logic)
     ↓                           ↓                        ↓                       ↓
[systemd service]      [Data validation]        [NaN detection]         [Debug logging]
(auto-restart)         (column checks)          (fallback values)       (condition tracking)
```

## Components and Interfaces

### 1. Enhanced Indicator Calculator

**Purpose**: Calculate technical indicators with robust error handling and validation

**Key Improvements**:
- Validate input data before calculations (check for required columns, sufficient rows)
- Return explicit error states instead of silent NaN values
- Log warnings when data is insufficient for indicator periods
- Add minimum data requirements for each indicator

**Interface**:
```python
class IndicatorCalculator:
    @staticmethod
    def calculate_ema(data: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """
        Calculate EMA with validation.
        
        Raises:
            ValueError: If data has fewer rows than period
            KeyError: If column doesn't exist
        """
        
    @staticmethod
    def validate_data_for_indicators(data: pd.DataFrame, required_periods: List[int]) -> Tuple[bool, str]:
        """
        Validate that DataFrame has sufficient data for indicator calculations.
        
        Returns:
            (is_valid, error_message)
        """
```

### 2. Improved Market Data Clients

**Purpose**: Fetch and maintain sufficient historical data for all indicators

**Key Improvements**:
- Increase buffer size from 200 to 500 candles for swing trading
- Fix YFinance period calculation to ensure sufficient data retrieval
- Validate fetched data (check columns, non-empty, proper types)
- Add WebSocket support for Kraken exchange (real-time data)

**Interface**:
```python
class MarketDataClient:
    def __init__(self, exchange_name: str, symbol: str, timeframes: List[str], 
                 buffer_size: int = 500, use_websocket: bool = False):
        """
        Initialize with configurable buffer size and WebSocket option.
        """
    
    def get_latest_candles(self, timeframe: str, count: int = 500) -> pd.DataFrame:
        """
        Fetch candles with validation.
        
        Raises:
            DataValidationError: If fetched data is invalid
        """
    
    def start_websocket(self) -> bool:
        """
        Start WebSocket connection for real-time data (Kraken only).
        """

class YFinanceClient:
    def _calculate_period(self, timeframe: str, count: int) -> str:
        """
        Fixed period calculation ensuring sufficient data.
        
        For 200 candles of 1h data: needs ~8 days, returns '1mo' (not '5d')
        For 200 candles of 4h data: needs ~33 days, returns '3mo' (not '1mo')
        """
```

### 3. Enhanced Signal Detector

**Purpose**: Detect signals with robust validation and detailed logging

**Key Improvements**:
- Validate all indicator values before applying signal rules
- Skip signal detection if critical indicators are NaN
- Log which conditions passed/failed for each scan
- Add debug mode with detailed condition tracking

**Interface**:
```python
class SignalDetector:
    def detect_signals(self, data: pd.DataFrame, timeframe: str, 
                      debug: bool = False) -> Optional[Signal]:
        """
        Detect signals with validation and logging.
        
        Returns None if:
        - Data is insufficient
        - Critical indicators are NaN
        - No confluence conditions met
        """
    
    def _validate_indicators(self, last: pd.Series) -> Tuple[bool, List[str]]:
        """
        Validate that all required indicators have valid values.
        
        Returns:
            (is_valid, list_of_missing_indicators)
        """
    
    def _log_signal_conditions(self, last: pd.Series, prev: pd.Series, 
                               signal_type: str) -> None:
        """
        Log detailed information about signal conditions for debugging.
        """
```

### 4. WebSocket Streamer for Kraken

**Purpose**: Provide real-time data streaming for Kraken exchange

**Key Improvements**:
- Implement Kraken WebSocket API client
- Handle multiple timeframe subscriptions
- Automatic reconnection with exponential backoff
- Thread-safe buffer updates

**Interface**:
```python
class KrakenWebSocketStreamer:
    def __init__(self, symbol: str, timeframes: List[str], 
                 on_candle_callback: Callable):
        """
        Initialize Kraken WebSocket client.
        """
    
    def start(self) -> None:
        """
        Start WebSocket connection in background thread.
        """
    
    def stop(self) -> None:
        """
        Stop WebSocket and cleanup.
        """
    
    def is_connected(self) -> bool:
        """
        Check connection status.
        """
```

### 5. Systemd Service Configuration

**Purpose**: Run scanners as stable system services with automatic restart

**Key Improvements**:
- Create service files for each scanner (BTC scalp, BTC swing, Gold scalp, Gold swing, US30 scalp, US30 swing)
- Configure automatic restart on failure
- Set resource limits (memory, file descriptors)
- Handle graceful shutdown (SIGTERM/SIGINT)
- Wait for network before starting

**Service Files**:
- `btc-scalp-scanner.service`
- `btc-swing-scanner.service`
- `gold-scalp-scanner.service`
- `gold-swing-scanner.service`
- `us30-scalp-scanner.service`
- `us30-swing-scanner.service`

### 6. Windows Desktop Launcher

**Purpose**: Provide easy startup for Windows desktop users

**Key Features**:
- Batch files to start individual scanners
- Master batch file to start all scanners
- Separate console windows for each scanner
- Graceful shutdown handling

**Batch Files**:
- `start_btc_scalp.bat` - Start BTC scalping scanner
- `start_btc_swing.bat` - Start BTC swing scanner
- `start_gold_scalp.bat` - Start Gold scalping scanner
- `start_gold_swing.bat` - Start Gold swing scanner
- `start_us30_scalp.bat` - Start US30 scalping scanner
- `start_us30_swing.bat` - Start US30 swing scanner
- `start_all_scanners.bat` - Start all scanners at once
- `stop_all_scanners.bat` - Stop all running scanners

## Data Models

### Enhanced Signal Model
```python
@dataclass
class Signal:
    # ... existing fields ...
    
    # New fields for debugging
    indicator_snapshot: Dict[str, float]  # All indicator values at signal time
    conditions_met: List[str]  # Which conditions passed
    conditions_failed: List[str]  # Which conditions failed (for near-misses)
    data_quality_score: float  # 0-1 score based on data completeness
```

### Data Validation Result
```python
@dataclass
class DataValidationResult:
    is_valid: bool
    row_count: int
    missing_columns: List[str]
    nan_indicators: List[str]
    error_message: str
```

## Error Handling

### 1. Indicator Calculation Errors

**Strategy**: Fail fast with clear error messages

```python
def calculate_ema(data: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
    # Validate input
    if data.empty:
        raise ValueError("Cannot calculate EMA on empty DataFrame")
    
    if column not in data.columns:
        raise KeyError(f"Column '{column}' not found in DataFrame")
    
    if len(data) < period:
        raise ValueError(f"Insufficient data: need {period} rows, got {len(data)}")
    
    # Calculate
    try:
        ema = data[column].ewm(span=period, adjust=False).mean()
        
        # Validate output
        if ema.isna().all():
            raise ValueError(f"EMA calculation produced all NaN values")
        
        return ema
    except Exception as e:
        logger.error(f"EMA calculation failed: {e}")
        raise
```

### 2. Data Fetching Errors

**Strategy**: Retry with exponential backoff, fallback to cached data

```python
def get_latest_candles(self, timeframe: str, count: int = 500) -> pd.DataFrame:
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Fetch data
            df = self._fetch_from_exchange(timeframe, count)
            
            # Validate
            validation = self._validate_candle_data(df, count)
            if not validation.is_valid:
                raise DataValidationError(validation.error_message)
            
            return df
            
        except Exception as e:
            logger.warning(f"Fetch attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                # Final attempt failed, try cached data
                cached = self.get_buffer_data(timeframe)
                if not cached.empty:
                    logger.warning("Using cached data after fetch failures")
                    return cached
                raise
```

### 3. Signal Detection Errors

**Strategy**: Log and skip, don't crash the scanner

```python
def detect_signals(self, data: pd.DataFrame, timeframe: str) -> Optional[Signal]:
    try:
        # Validate data
        validation = self._validate_indicators(data.iloc[-1])
        if not validation.is_valid:
            logger.debug(f"Skipping signal detection: {validation.error_message}")
            return None
        
        # Detect signals
        signal = self._check_bullish_confluence(data, timeframe)
        if signal:
            return signal
        
        signal = self._check_bearish_confluence(data, timeframe)
        if signal:
            return signal
        
        return None
        
    except Exception as e:
        logger.error(f"Signal detection error on {timeframe}: {e}", exc_info=True)
        return None  # Don't crash, just skip this scan
```

### 4. WebSocket Connection Errors

**Strategy**: Automatic reconnection with exponential backoff

```python
def _run_websocket(self) -> None:
    retry_delay = 1
    max_delay = 60
    
    while self._running:
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            self.ws.run_forever()
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self._connected = False
        
        if self._running:
            logger.info(f"Reconnecting in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_delay)
```

## Testing Strategy

### 1. Unit Tests

**Indicator Calculator Tests**:
- Test each indicator with valid data
- Test with insufficient data (should raise ValueError)
- Test with missing columns (should raise KeyError)
- Test with edge cases (all zeros, all same values)

**Signal Detector Tests**:
- Test bullish/bearish confluence detection
- Test with NaN indicators (should return None)
- Test duplicate signal prevention
- Test trend-following detection

### 2. Integration Tests

**Data Pipeline Tests**:
- Test full flow: fetch → calculate → detect
- Test with real exchange data
- Test WebSocket connection and reconnection
- Test systemd service startup and shutdown

### 3. Manual Testing

**Signal Detection Verification**:
- Run scanner on historical data with known setups
- Verify signals are detected for clear bullish/bearish patterns
- Check Excel output for indicator values
- Verify no NaN values in logged scans

**Infrastructure Testing**:
- Test systemd service restart after crash
- Test WebSocket reconnection after network interruption
- Test graceful shutdown (Ctrl+C, SIGTERM)
- Monitor resource usage (memory, CPU)

## Implementation Notes

### Phase 1: Fix Data Pipeline (Priority: Critical)
1. Update YFinanceClient period calculation
2. Increase buffer sizes to 500 candles
3. Add data validation in market data clients
4. Fix indicator calculator error handling

### Phase 2: Enhance Signal Detection (Priority: High)
1. Add indicator validation in signal detector
2. Implement detailed condition logging
3. Add debug mode for troubleshooting
4. Test with historical data

### Phase 3: WebSocket Implementation (Priority: Medium)
1. Implement KrakenWebSocketStreamer
2. Add WebSocket option to MarketDataClient
3. Test real-time data streaming
4. Verify latency and reliability

### Phase 4: Systemd Migration (Priority: High)
1. Create service files for all scanners
2. Update installation script
3. Test service startup/restart/shutdown
4. Migrate from screen sessions to services

### Configuration Changes

**config.json additions**:
```json
{
  "exchange": {
    "name": "kraken",
    "use_websocket": true,
    "websocket_reconnect_delay": 5
  },
  "data_fetching": {
    "buffer_size": 500,
    "min_candles_for_signals": 200,
    "validation_enabled": true
  },
  "signal_detection": {
    "debug_mode": false,
    "log_conditions": true,
    "require_all_indicators": true
  },
  "logging": {
    "level": "INFO",
    "debug_signal_detection": false
  }
}
```

## Performance Considerations

### Memory Usage
- 500 candles × 6 timeframes × 8 bytes/float × 10 columns ≈ 240 KB per scanner
- Acceptable for systems with 512MB+ RAM

### API Rate Limits
- REST polling: 1 request per timeframe per interval (6 requests/minute for 6 timeframes)
- WebSocket: No rate limits, real-time updates
- YFinance: Rate limited, use caching and longer intervals

### CPU Usage
- Indicator calculations: O(n) where n = buffer size
- Signal detection: O(1) per scan
- Expected: <5% CPU usage per scanner

## Deployment Strategy

### Development Environment (Windows Desktop)
1. Test fixes locally with historical data
2. Verify signal detection improvements
3. Test with batch file launchers
4. Validate error handling and logging

**Windows Setup**:
```batch
REM Install Python dependencies
pip install -r requirements.txt

REM Set environment variables
set TELEGRAM_BOT_TOKEN=your_token
set TELEGRAM_CHAT_ID=your_chat_id

REM Start all scanners
start_all_scanners.bat
```

### Staging Environment (Linux VM)
1. Deploy to test VM
2. Run all scanners as systemd services
3. Monitor for 24 hours
4. Verify signal detection and stability

**Linux Setup**:
```bash
# Install as systemd services
sudo bash deployment/install_all_services.sh

# Start services
sudo systemctl start btc-scalp-scanner
sudo systemctl start btc-swing-scanner
# ... etc

# Monitor logs
sudo journalctl -u btc-scalp-scanner -f
```

### Production Deployment (Linux Server)
1. Stop existing screen sessions
2. Install systemd services
3. Start services one by one
4. Monitor logs and Telegram alerts
5. Verify Excel reports

### Rollback Plan
**Linux**:
If issues occur:
1. Stop systemd services: `sudo systemctl stop *-scanner`
2. Revert code changes: `git checkout previous-version`
3. Restart screen sessions: `./start_all_scanners.sh`
4. Investigate issues before retry

**Windows**:
If issues occur:
1. Close all scanner windows (or run `stop_all_scanners.bat`)
2. Revert code changes: `git checkout previous-version`
3. Restart scanners: `start_all_scanners.bat`
4. Check logs in `logs/` directory

## Monitoring and Observability

### Metrics to Track
- Signals detected per hour
- Indicator NaN rate (should be 0%)
- WebSocket connection uptime
- Service restart count
- Memory/CPU usage

### Logging Enhancements
- Log every scan with indicator values
- Log signal conditions (passed/failed)
- Log data validation results
- Log WebSocket connection events

### Alerts
- Telegram alert when service restarts
- Telegram alert when WebSocket disconnects
- Telegram alert when no signals detected for 24h (potential issue)
- Email report with scan statistics

## Security Considerations

### Systemd Service Hardening
- Run as dedicated user (not root)
- Restrict file system access
- Limit memory usage
- Disable privilege escalation
- Use private /tmp

### API Credentials
- Store in environment variables
- Never log credentials
- Use read-only API keys where possible

### Network Security
- Use TLS for WebSocket connections
- Validate SSL certificates
- Rate limit API requests

## Future Enhancements

### Short-term (Next Sprint)
- Add Stochastic oscillator to signal confluence
- Implement multi-timeframe confirmation
- Add backtesting framework

### Long-term (Future Sprints)
- Machine learning signal scoring
- Automated trade execution
- Portfolio management
- Risk management system
