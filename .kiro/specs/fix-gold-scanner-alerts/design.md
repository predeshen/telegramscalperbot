# Design Document

## Overview

This design addresses the symbol labeling and price source issues in the Gold scanner. The solution involves:
1. Ensuring the symbol attribute is properly set and propagated through the signal creation pipeline
2. Adding data source transparency to alerts and configuration
3. Documenting price variance expectations

## Architecture

### Component Interaction Flow

```
GoldSignalDetector → Creates Signal with symbol="XAU/USD"
                  ↓
            Signal Object (with symbol attribute)
                  ↓
            TelegramAlerter → Formats message using signal.symbol
                  ↓
            Telegram Message (displays "XAU/USD LONG SIGNAL")
```

## Components and Interfaces

### 1. GoldSignalDetector

**Current Issue**: The `detect_signals()` method doesn't pass the symbol parameter when creating signals.

**Solution**: 
- Add `symbol` parameter to `detect_signals()` method signature
- Pass symbol to all internal signal creation methods
- Ensure `_create_gold_signal()` accepts and sets the symbol attribute

**Modified Interface**:
```python
def detect_signals(self, data: pd.DataFrame, timeframe: str, symbol: str = "XAU/USD") -> Optional[GoldSignal]:
    """
    Detect trading signals using appropriate strategy.
    
    Args:
        data: DataFrame with OHLCV and indicators
        timeframe: Timeframe string
        symbol: Trading symbol (default: "XAU/USD")
    """
```

### 2. Signal Creation Methods

All internal signal detection methods need to accept and pass the symbol:
- `_detect_momentum_shift()`
- `_detect_asian_range_breakout()`
- `_detect_ema_cloud_breakout()`
- `_detect_mean_reversion()`
- `_detect_trend_following()`

Each method should pass `symbol=symbol` to `_create_gold_signal()`.

### 3. _create_gold_signal() Helper

**Current Issue**: Method signature is incomplete in the truncated file.

**Solution**: Ensure the method accepts a `symbol` parameter and sets it on the GoldSignal object.

**Expected Interface**:
```python
def _create_gold_signal(
    self,
    timestamp: datetime,
    signal_type: str,
    timeframe: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    atr: float,
    indicators: pd.Series,
    strategy: str,
    symbol: str = "XAU/USD"
) -> GoldSignal:
    """Create a GoldSignal with all required attributes including symbol."""
```

### 4. Main Gold Scanner

**File**: `xauusd_scanner/main_gold.py`

**Current Issue**: Line 237 calls `signal_detector.detect_signals(candles, timeframe, symbol="XAU/USD")` but the method may not accept this parameter.

**Solution**: Verify the method signature matches and the symbol is properly passed.

### 5. TelegramAlerter

**Current State**: Already uses `signal.symbol` in the `_format_signal_message()` method with a fallback to "BTC/USD".

**Solution**: The alerter is correctly implemented. The issue is that signals don't have the symbol attribute set, so it falls back to the default.

**Code Location** (`src/alerter.py` line 186):
```python
symbol = getattr(signal, 'symbol', 'BTC/USD')  # Default to BTC/USD for backward compatibility
```

This will work correctly once signals have the symbol attribute set.

## Data Models

### Signal Object Enhancement

The base `Signal` class (from `src/signal_detector.py`) needs to include a `symbol` attribute:

```python
@dataclass
class Signal:
    """Trading signal with entry, stop loss, and take profit levels."""
    timestamp: datetime
    signal_type: str  # "LONG" or "SHORT"
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    atr: float
    risk_reward: float
    confidence: int
    market_bias: str
    reasoning: str
    indicators: dict
    symbol: str = "BTC/USD"  # Add with default for backward compatibility
```

### GoldSignal Extension

The `GoldSignal` class already extends `Signal` and should inherit the symbol attribute.

## Error Handling

### Missing Symbol Attribute

**Scenario**: Older code paths that don't set the symbol attribute.

**Handling**: The TelegramAlerter already has a fallback using `getattr(signal, 'symbol', 'BTC/USD')`. This provides backward compatibility.

### Data Source Variance

**Scenario**: Prices from Yahoo Finance differ from broker prices.

**Handling**: 
1. Add disclaimer in alerts about data source
2. Document expected variance in configuration
3. Log data source on startup

## Testing Strategy

### Unit Tests

1. **Test Symbol Propagation**
   - Create a signal with symbol="XAU/USD"
   - Verify the symbol is correctly set on the Signal object
   - Verify the alerter uses the correct symbol in the message

2. **Test Alert Formatting**
   - Mock a GoldSignal with symbol="XAU/USD"
   - Call `_format_signal_message()`
   - Assert the message contains "XAU/USD" and not "BTC/USD"

### Integration Tests

1. **End-to-End Signal Flow**
   - Run Gold scanner with test data
   - Capture generated signal
   - Verify symbol is "XAU/USD"
   - Verify alert message contains correct symbol

2. **Data Source Logging**
   - Start Gold scanner
   - Verify startup logs mention "Yahoo Finance - GC=F"
   - Verify configuration shows data source

### Manual Testing

1. **Live Alert Verification**
   - Run Gold scanner
   - Wait for signal
   - Check Telegram alert shows "XAU/USD"
   - Verify price is within expected range of broker price

## Configuration Changes

### Gold Scanner Config

Add data source documentation to `xauusd_scanner/config_gold.json`:

```json
{
  "exchange": {
    "name": "oanda",
    "symbol": "XAU/USD",
    "data_source": "Yahoo Finance (GC=F - Gold Futures)",
    "data_source_note": "Prices may differ slightly from spot XAU/USD. Typical variance: 0.1-0.5%",
    "timeframes": ["1m", "5m"]
  }
}
```

### Startup Message Enhancement

Modify the startup message in `main_gold.py` to include data source info:

```python
alerter.send_message(
    f"🟢 <b>XAU/USD Gold Scanner Started</b>\n\n"
    f"💰 Data Source: Yahoo Finance (GC=F)\n"
    f"📊 Symbol: XAU/USD\n"
    f"Session: {session_info['session']}\n"
    f"Strategy: {session_info['strategy_focus']}\n"
    f"Monitoring: {', '.join(config['exchange']['timeframes'])}\n\n"
    f"⚠️ Note: Prices may vary slightly from your broker\n"
    f"Ready to scan for Gold signals!"
)
```

## Implementation Notes

### Priority Order

1. **High Priority**: Fix symbol attribute (Requirement 1)
   - This is a simple fix that immediately resolves the confusion
   - Affects user experience directly

2. **Medium Priority**: Add data source transparency (Requirement 2 & 3)
   - Helps users understand price differences
   - Improves trust in the system

### Backward Compatibility

The changes maintain backward compatibility:
- Default symbol value in Signal class
- Fallback in TelegramAlerter using `getattr()`
- BTC scanner continues to work without changes

### Alternative Data Sources

**Future Enhancement**: If price variance is too large, consider:
1. Using OANDA API directly (requires API key)
2. Using a forex data provider (e.g., Alpha Vantage, Twelve Data)
3. Adding a price offset configuration parameter

For now, documenting the variance is sufficient since:
- Gold futures (GC=F) closely track spot prices
- Typical variance is 0.1-0.5% which is acceptable for signal generation
- Entry/exit decisions should still reference broker prices
