# Design Document

## Overview

This design addresses the US30 swing scanner's failure to detect trading signals by fixing missing indicator calculations and implementing more realistic signal detection logic. The solution maintains the existing architecture while enhancing the US30-specific detector to catch legitimate trading opportunities that are currently being missed.

### Root Causes Identified

1. **Missing Indicator Calculations**: EMA 9, VWAP, and Stochastic indicators are not being calculated in the US30 scanner
2. **Overly Restrictive Signal Logic**: Current detector requires very specific conditions (EMA crossovers, exact price proximity to EMAs, high volume spikes) that rarely occur
3. **Infrequent Scanning**: Long intervals between checks (4 hours for 4h timeframe) miss time-sensitive opportunities
4. **Strict Volume Requirements**: 1.3x-1.5x volume spike threshold filters out valid signals in lower-volume periods

### Design Goals

- Calculate all required indicators (EMA 9, VWAP, Stochastic) for complete market analysis
- Implement trend-following signal detection that catches strong directional moves
- Reduce volume requirements to realistic levels (0.8x-1.2x average)
- Increase scan frequency to catch signals in a timely manner
- Add comprehensive diagnostic logging for troubleshooting
- Maintain backward compatibility with existing signal structure

## Architecture

### Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     US30 Swing Scanner                          │
│                    (main_us30_swing.py)                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──► YFinanceClient: Fetch market data
             │
             ├──► IndicatorCalculator: Calculate ALL indicators
             │    ├─ EMA 9, 21, 50, 200
             │    ├─ VWAP
             │    ├─ Stochastic (K, D)
             │    ├─ ATR, RSI, Volume MA
             │    └─ MACD
             │
             ├──► US30SwingDetector: Detect signals
             │    ├─ Check trend alignment (EMA cascade)
             │    ├─ Validate volume (0.8x-1.2x threshold)
             │    ├─ Confirm RSI momentum
             │    ├─ Check for duplicates
             │    └─ Generate signal with reasoning
             │
             ├──► ExcelReporter: Log all scans
             │    └─ Include ALL indicator values
             │
             └──► TelegramAlerter: Send signal alerts
```

### Data Flow

```
Market Data (OHLCV)
    ↓
Indicator Calculation (with EMA 9, VWAP, Stochastic)
    ↓
Signal Detection (trend alignment + volume + RSI)
    ↓
Duplicate Check (120min window, 0.3% price threshold)
    ↓
Excel Logging + Telegram Alert
```

## Components and Interfaces

### 1. Indicator Calculator Enhancement

**File**: `src/indicator_calculator.py`

**Changes**: None required - already supports all needed indicators

**Usage Pattern**:
```python
# Calculate EMA 9 (currently missing)
candles['ema_9'] = indicator_calc.calculate_ema(candles, 9)

# Calculate VWAP (currently missing)
candles['vwap'] = indicator_calc.calculate_vwap(candles)

# Calculate Stochastic (currently missing)
stoch_k, stoch_d = indicator_calc.calculate_stochastic(candles, k_period=14, d_period=3, smooth_k=3)
candles['stoch_k'] = stoch_k
candles['stoch_d'] = stoch_d
```

### 2. US30 Swing Detector Redesign

**File**: `us30_scanner/us30_swing_detector.py`

**Current Issues**:
- Requires EMA 50/200 crossovers (rare events)
- Requires price within 1% of EMA 50 (too restrictive)
- Requires 1.3x-1.5x volume spike (too high)
- Only checks at long intervals

**New Design**:

#### Signal Detection Strategy: Trend Alignment

Instead of waiting for rare crossovers, detect when price is already in a strong trend:

**Bullish Trend Alignment**:
1. Price > EMA 9 > EMA 21 > EMA 50 (cascade alignment)
2. RSI > 50 (bullish momentum)
3. Volume >= 0.8x average (realistic threshold)
4. Not a duplicate signal (120min window, 0.3% price threshold)

**Bearish Trend Alignment**:
1. Price < EMA 9 < EMA 21 < EMA 50 (cascade alignment)
2. RSI < 50 (bearish momentum)
3. Volume >= 0.8x average (realistic threshold)
4. Not a duplicate signal (120min window, 0.3% price threshold)

#### Method Structure

```python
class US30SwingDetector:
    def detect_signals(self, data, timeframe, symbol="US30"):
        """Main entry point - try multiple strategies"""
        # 1. Try trend alignment (new, primary strategy)
        signal = self._detect_trend_alignment(data, timeframe, symbol)
        if signal and not self._is_duplicate(signal):
            return signal
        
        # 2. Try trend continuation (existing, secondary)
        signal = self._detect_trend_continuation(data, timeframe)
        if signal and not self._is_duplicate(signal):
            return signal
        
        # 3. Try trend reversal (existing, tertiary)
        signal = self._detect_trend_reversal(data, timeframe)
        if signal and not self._is_duplicate(signal):
            return signal
        
        return None
    
    def _detect_trend_alignment(self, data, timeframe, symbol):
        """NEW: Detect strong trend alignment signals"""
        # Check bullish alignment
        # Check bearish alignment
        # Validate volume
        # Create signal
    
    def _log_scan_diagnostics(self, data, timeframe):
        """NEW: Log why signals are/aren't generated"""
        # Log trend alignment status
        # Log volume ratio
        # Log RSI level
        # Log which conditions passed/failed
```

### 3. Main Scanner Loop Enhancement

**File**: `us30_scanner/main_us30_swing.py`

**Changes**:

#### Indicator Calculation
Add missing indicators to the calculation pipeline:

```python
# Existing indicators
candles['ema_21'] = indicator_calc.calculate_ema(candles, 21)
candles['ema_50'] = indicator_calc.calculate_ema(candles, 50)
candles['ema_200'] = indicator_calc.calculate_ema(candles, 200)

# NEW: Add EMA 9
candles['ema_9'] = indicator_calc.calculate_ema(candles, 9)

# NEW: Add VWAP
candles['vwap'] = indicator_calc.calculate_vwap(candles)

# NEW: Add Stochastic
stoch_k, stoch_d = indicator_calc.calculate_stochastic(candles, 14, 3, 3)
candles['stoch_k'] = stoch_k
candles['stoch_d'] = stoch_d
```

#### Scan Frequency
Remove the time-based check interval logic that prevents frequent scanning:

```python
# REMOVE THIS:
if last_check is None or (current_time - last_check).total_seconds() >= interval:
    # scan logic

# REPLACE WITH:
# Always scan on each polling interval (300 seconds)
# Let duplicate detection handle filtering
```

#### Excel Logging
Ensure all indicators are logged:

```python
scan_data = {
    'indicators': {
        'ema_9': last_row.get('ema_9', None),  # NEW
        'ema_21': last_row.get('ema_21', None),
        'ema_50': last_row.get('ema_50', None),
        'ema_100': last_row.get('ema_100', None),
        'ema_200': last_row.get('ema_200', None),
        'rsi': last_row.get('rsi', None),
        'atr': last_row.get('atr', None),
        'volume_ma': last_row.get('volume_ma', None),
        'vwap': last_row.get('vwap', None),  # NEW
        'stoch_k': last_row.get('stoch_k', None),  # NEW
        'stoch_d': last_row.get('stoch_d', None)  # NEW
    }
}
```

## Data Models

### Signal Structure

The existing `Signal` dataclass already supports all required fields:

```python
@dataclass
class US30SwingSignal(Signal):
    """Extended signal for US30 swing trading"""
    strategy: str  # "Trend Alignment", "Trend Continuation", "Trend Reversal"
    macd_histogram: Optional[float]
    ema_200_distance: Optional[float]
    trend_alignment: Optional[str]  # NEW: "bullish_cascade", "bearish_cascade", "mixed"
```

### Configuration Updates

**File**: `us30_scanner/config_us30_swing.json`

```json
{
  "signal_rules": {
    "volume_spike_threshold": 0.8,  // CHANGED: from 1.3 to 0.8
    "volume_reversal_threshold": 1.2,  // NEW: higher threshold for reversals
    "rsi_min": 30,
    "rsi_max": 70,
    "stop_loss_atr_multiplier": 2.0,
    "take_profit_atr_multiplier": 3.0,
    "duplicate_time_window_minutes": 120,  // CHANGED: from 240 to 120
    "duplicate_price_threshold_percent": 0.3  // CHANGED: from 0.5 to 0.3
  },
  "polling_interval_seconds": 300  // Keep at 5 minutes
}
```

## Error Handling

### Indicator Calculation Failures

```python
try:
    candles['ema_9'] = indicator_calc.calculate_ema(candles, 9)
except Exception as e:
    logger.error(f"Failed to calculate EMA 9: {e}")
    # Continue with other indicators, log to Excel with NaN
```

### Missing Data Handling

```python
# Check for required indicators before signal detection
required_indicators = ['ema_9', 'ema_21', 'ema_50', 'rsi', 'volume_ma']
if not all(ind in candles.columns for ind in required_indicators):
    logger.error(f"Missing required indicators for signal detection")
    return None
```

### Signal Detection Failures

```python
try:
    signal = signal_detector.detect_signals(candles, timeframe, symbol="US30")
except Exception as e:
    logger.error(f"Signal detection failed: {e}", exc_info=True)
    signal = None
```

## Testing Strategy

### Unit Tests

**Test Indicator Calculations**:
```python
def test_ema_9_calculation():
    """Verify EMA 9 is calculated correctly"""
    data = create_sample_data(100)
    ema_9 = indicator_calc.calculate_ema(data, 9)
    assert not ema_9.isna().all()
    assert len(ema_9) == len(data)

def test_vwap_calculation():
    """Verify VWAP is calculated correctly"""
    data = create_sample_data(100)
    vwap = indicator_calc.calculate_vwap(data)
    assert not vwap.isna().all()
```

**Test Trend Alignment Detection**:
```python
def test_bullish_trend_alignment():
    """Verify bullish trend alignment is detected"""
    data = create_bullish_trend_data()
    detector = US30SwingDetector(config)
    signal = detector._detect_trend_alignment(data, "4h", "US30")
    assert signal is not None
    assert signal.signal_type == "LONG"
    assert signal.strategy == "Trend Alignment"

def test_bearish_trend_alignment():
    """Verify bearish trend alignment is detected"""
    data = create_bearish_trend_data()
    detector = US30SwingDetector(config)
    signal = detector._detect_trend_alignment(data, "4h", "US30")
    assert signal is not None
    assert signal.signal_type == "SHORT"
    assert signal.strategy == "Trend Alignment"
```

**Test Volume Thresholds**:
```python
def test_volume_threshold_realistic():
    """Verify 0.8x volume threshold allows signals"""
    data = create_trend_data_with_volume(volume_ratio=0.85)
    detector = US30SwingDetector(config)
    signal = detector._detect_trend_alignment(data, "4h", "US30")
    assert signal is not None  # Should pass with 0.85x volume

def test_volume_threshold_too_low():
    """Verify signals rejected below 0.8x volume"""
    data = create_trend_data_with_volume(volume_ratio=0.5)
    detector = US30SwingDetector(config)
    signal = detector._detect_trend_alignment(data, "4h", "US30")
    assert signal is None  # Should fail with 0.5x volume
```

### Integration Tests

**Test Full Scan Cycle**:
```python
def test_full_scan_with_all_indicators():
    """Verify complete scan cycle calculates all indicators"""
    # Mock YFinanceClient
    # Run one scan iteration
    # Verify all indicators present in Excel log
    # Verify no NaN values in critical indicators
```

**Test Signal Generation End-to-End**:
```python
def test_signal_generation_and_logging():
    """Verify signal is detected, logged, and alerted"""
    # Create mock data with strong trend
    # Run scanner
    # Verify signal detected
    # Verify Excel log entry
    # Verify Telegram alert sent
```

### Manual Testing

**Test with Historical Data**:
1. Load US30 data from the 4:30 downtrend period mentioned by user
2. Run detector on that data
3. Verify SHORT signal is generated
4. Verify signal reasoning explains the downtrend

**Test with Live Data**:
1. Run scanner for 1 hour
2. Monitor logs for diagnostic messages
3. Verify indicators are calculated every 5 minutes
4. Verify signals are generated when trends occur
5. Verify duplicate detection prevents spam

## Diagnostic Logging

### Scan-Level Logging

```python
logger.info(f"[{timeframe}] Scan complete - Price: ${last['close']:.2f}")
logger.info(f"[{timeframe}] Trend: EMA9={last['ema_9']:.2f}, EMA21={last['ema_21']:.2f}, EMA50={last['ema_50']:.2f}")
logger.info(f"[{timeframe}] Volume: {last['volume']:,.0f} ({volume_ratio:.2f}x avg)")
logger.info(f"[{timeframe}] RSI: {last['rsi']:.1f}")
```

### Signal Detection Logging

```python
# When checking trend alignment
if is_bullish_cascade:
    logger.info(f"[{timeframe}] Bullish cascade detected: Price > EMA9 > EMA21 > EMA50")
else:
    logger.debug(f"[{timeframe}] No bullish cascade: Price={price:.2f}, EMA9={ema9:.2f}, EMA21={ema21:.2f}")

# When volume check fails
if volume_ratio < 0.8:
    logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x (need >= 0.8x)")
```

### Duplicate Detection Logging

```python
if is_duplicate:
    logger.info(f"[{timeframe}] Duplicate signal blocked: {signal_type} at ${entry:.2f} (previous: ${prev_entry:.2f} at {time_diff}min ago)")
```

## Performance Considerations

### Calculation Efficiency

- Indicator calculations are vectorized (pandas operations)
- No performance impact from adding EMA 9, VWAP, Stochastic
- Expected calculation time: < 100ms for 500 candles

### Memory Usage

- Additional indicators add ~3 columns to DataFrame
- Memory increase: negligible (< 1MB per timeframe)

### Scan Frequency

- Current: Every 300 seconds (5 minutes)
- No change needed - duplicate detection handles filtering
- Network calls to yfinance: 2 per 5 minutes (4h + 1d timeframes)

## Migration and Rollback

### Deployment Steps

1. Backup current configuration and code
2. Update `us30_scanner/us30_swing_detector.py` with new detection logic
3. Update `us30_scanner/main_us30_swing.py` with indicator calculations
4. Update `us30_scanner/config_us30_swing.json` with new thresholds
5. Restart US30 swing scanner service
6. Monitor logs for 1 hour to verify signals

### Rollback Plan

If issues occur:
1. Stop scanner service
2. Restore backed-up files
3. Restart scanner service
4. Investigate logs to identify issue

### Backward Compatibility

- Signal structure unchanged (uses existing `Signal` dataclass)
- Excel logging format unchanged (adds new indicator columns)
- Telegram alert format unchanged
- Configuration keys are additive (old configs still work)

## Security Considerations

No security changes required - this is a pure logic enhancement.

## Dependencies

No new dependencies required. All functionality uses existing libraries:
- pandas (indicator calculations)
- numpy (mathematical operations)
- logging (diagnostics)

## Future Enhancements

Potential improvements for future iterations:

1. **Adaptive Volume Thresholds**: Adjust volume requirements based on time of day (higher during market open)
2. **Multi-Timeframe Confirmation**: Require trend alignment on both 4h and 1d timeframes
3. **Volatility-Based Targets**: Adjust take-profit based on ATR percentile (higher targets in high volatility)
4. **Machine Learning**: Train model to identify optimal entry points within trends
5. **Backtesting Framework**: Automated backtesting to validate signal quality over historical data
