# Design Document

## Overview

This design addresses critical bugs in the trade tracking system that prevent accurate detection and notification of take-profit hits. The root causes include:

1. **Price comparison logic issues**: The TP detection may not be firing correctly due to timing or comparison logic
2. **Trade state management**: Multiple trades on the same symbol may be interfering with each other
3. **Notification flow**: The notification system may be sending conflicting messages due to race conditions or improper state checks

The solution focuses on:
- Improving TP detection reliability with better logging and validation
- Ensuring proper trade isolation using unique trade IDs
- Adding defensive checks to prevent duplicate/conflicting notifications
- Enhanced debugging capabilities to diagnose future issues

## Architecture

### Current Flow
```
Signal Generated → add_trade() → TradeTracker.active_trades[trade_id]
                                          ↓
Price Update → update_trades() → Check TP/SL/Breakeven
                                          ↓
                                   Send Notification
                                          ↓
                                   Close Trade (if TP/SL hit)
```

### Issues Identified

1. **Trade ID Generation**: Currently uses `{symbol}_{signal_type}_{timestamp}` but timestamp precision may cause collisions
2. **Price Check Timing**: `update_trades()` is called once per scan cycle, may miss exact TP hits
3. **State Management**: No validation that trade exists before sending notifications
4. **Logging Gaps**: Insufficient logging to debug why TP detection fails

### Proposed Improvements

1. **Enhanced Trade ID**: Add microseconds to timestamp for uniqueness
2. **Defensive Checks**: Validate trade exists in active_trades before all operations
3. **Improved Logging**: Log every price check with comparison details
4. **Notification Guards**: Check trade status before sending any notification
5. **TP Detection Priority**: Check TP/SL before other notifications (breakeven, warnings)

## Components and Interfaces

### TradeTracker Class

**Modified Methods:**

```python
def add_trade(self, signal: Signal, symbol: Optional[str] = None) -> str:
    """
    Add a new trade to tracking.
    
    Returns:
        trade_id: Unique identifier for the trade
    """
    # Generate unique trade ID with microseconds
    # Log trade addition with full details
    # Return trade_id for reference
```

```python
def update_trades(self, current_price: float, indicators: Optional[Dict] = None) -> None:
    """
    Update all active trades with current price.
    
    Enhanced with:
    - Defensive checks for trade existence
    - Priority ordering: TP/SL checks before other notifications
    - Detailed logging of all price comparisons
    """
```

```python
def _check_target_hit_extended(self, signal: Signal, current_price: float, 
                               trade: TradeStatus, target_price: float) -> bool:
    """
    Check if TP is hit with enhanced logging.
    
    Logs:
    - Current price vs target price
    - Signal type and comparison logic used
    - Result of comparison
    """
```

```python
def _close_trade(self, trade_id: str, reason: str, current_price: float) -> None:
    """
    Close trade with validation.
    
    Enhanced with:
    - Validation that trade_id exists in active_trades
    - Logging of closure reason and P&L
    - Proper cleanup from active_trades
    """
```

**New Methods:**

```python
def _validate_trade_exists(self, trade_id: str, operation: str) -> bool:
    """
    Validate that a trade exists before performing operations.
    
    Args:
        trade_id: Trade identifier
        operation: Description of operation being attempted
        
    Returns:
        True if trade exists, False otherwise (with error log)
    """
```

```python
def get_trade_status(self, trade_id: str) -> Optional[Dict]:
    """
    Get current status of a trade for debugging.
    
    Returns:
        Dict with trade details or None if not found
    """
```

### TradeStatus Dataclass

**No changes needed** - current structure is adequate:
- `signal`: Original signal
- `entry_time`: When trade was opened
- `breakeven_notified`: Flag for breakeven notification
- `target_notified`: Flag for TP notification (currently unused - will be utilized)
- `stop_warning_sent`: Flag for SL warning
- `status`: Trade status (ACTIVE, CLOSED_TP, CLOSED_SL, EXTENDED)

## Data Models

### Trade ID Format

**Current:**
```
{symbol}_{signal_type}_{timestamp}
Example: BTC/USD_LONG_20251117_082900
```

**Enhanced:**
```
{symbol}_{signal_type}_{timestamp_with_microseconds}
Example: BTC/USD_LONG_20251117_082900_123456
```

### Notification State Tracking

Each `TradeStatus` tracks notification flags:
- `breakeven_notified`: bool
- `target_notified`: bool (will be set when TP notification sent)
- `stop_warning_sent`: bool
- `tp_extension_notified`: bool
- `momentum_reversal_notified`: bool

### Trade Lifecycle States

```
ACTIVE → Price monitoring → TP hit → CLOSED_TP
                         → SL hit → CLOSED_SL
                         → Extended → EXTENDED → TP hit → CLOSED_TP
```

## Error Handling

### Missing Trade Errors

**Scenario**: Attempting to update/close a trade that doesn't exist

**Handling**:
```python
if trade_id not in self.active_trades:
    logger.error(f"Trade {trade_id} not found in active trades. Operation: {operation}")
    logger.debug(f"Active trades: {list(self.active_trades.keys())}")
    return False
```

### Price Data Errors

**Scenario**: Invalid or missing price data in update_trades()

**Handling**:
```python
if current_price is None or current_price <= 0:
    logger.error(f"Invalid current price: {current_price}")
    return
```

### Notification Failures

**Scenario**: Alerter fails to send notification

**Handling**:
- Log the failure but don't prevent trade closure
- Trade state should still be updated correctly
- Consider retry logic for critical notifications (TP/SL)

## Testing Strategy

### Unit Tests

**Test: TP Detection for LONG trades**
```python
def test_tp_hit_long_trade():
    # Setup: Create LONG trade at $4,058.80 with TP at $4,066.56
    # Action: Update with price $4,066.56
    # Assert: _check_target_hit_extended returns True
    # Assert: _close_trade is called with reason="TARGET"
```

**Test: TP Detection for SHORT trades**
```python
def test_tp_hit_short_trade():
    # Setup: Create SHORT trade at $4,062.80 with TP at $4,050.00
    # Action: Update with price $4,050.00
    # Assert: _check_target_hit_extended returns True
    # Assert: _close_trade is called with reason="TARGET"
```

**Test: Trade ID Uniqueness**
```python
def test_unique_trade_ids():
    # Setup: Create two trades on same symbol within milliseconds
    # Assert: Both trades have unique IDs
    # Assert: Both trades tracked independently
```

**Test: Notification Deduplication**
```python
def test_no_duplicate_notifications():
    # Setup: Create trade and reach breakeven
    # Action: Update multiple times at breakeven price
    # Assert: Only one breakeven notification sent
```

### Integration Tests

**Test: End-to-End TP Hit Flow**
```python
def test_e2e_tp_hit_notification():
    # Setup: Create real signal, add to tracker
    # Action: Simulate price updates leading to TP
    # Assert: "TARGET HIT" notification sent
    # Assert: Trade removed from active_trades
    # Assert: Trade added to closed_trades
```

**Test: Multiple Concurrent Trades**
```python
def test_multiple_trades_same_symbol():
    # Setup: Create 2 LONG trades on XAU/USD
    # Action: First trade hits TP, second still active
    # Assert: Only first trade closed
    # Assert: Second trade still in active_trades
    # Assert: Correct notifications for each trade
```

### Manual Testing Scenarios

1. **Real-time TP Hit**: Run scanner with live data, verify TP notification when price reaches target
2. **Extended TP**: Verify extended TP detection works correctly
3. **Rapid Price Movement**: Test with volatile market to ensure no missed notifications
4. **Multiple Symbols**: Run multi-symbol scanner and verify independent tracking

## Debugging Enhancements

### Logging Levels

**DEBUG**: Every price comparison
```
DEBUG: Checking TP for LONG trade: current=$4,066.56 >= target=$4,066.56 → True
```

**INFO**: Trade lifecycle events
```
INFO: Added trade to tracking: XAU/USD_LONG_20251117_082900_123456 at $4,058.80
INFO: Sent breakeven update for LONG trade
INFO: Closed trade XAU/USD_LONG_20251117_082900_123456: TARGET, P&L: +0.19%
```

**WARNING**: Unexpected conditions
```
WARNING: Attempted to update non-existent trade: XAU/USD_LONG_20251117_082900_123456
```

**ERROR**: Critical failures
```
ERROR: Failed to close trade: XAU/USD_LONG_20251117_082900_123456 not in active_trades
```

### Debug Methods

```python
def debug_active_trades(self) -> str:
    """Return formatted string of all active trades for debugging."""
    
def debug_trade_details(self, trade_id: str) -> str:
    """Return detailed information about a specific trade."""
```

## Implementation Notes

### Priority Order in update_trades()

1. **First**: Check TP/SL (trade closure)
2. **Second**: Check TP extension (if approaching TP)
3. **Third**: Check momentum reversal (exit signals)
4. **Fourth**: Check breakeven (management update)
5. **Last**: Check stop warning (risk alert)

This ensures that if TP is hit, the trade is closed immediately without sending other notifications.

### Backward Compatibility

- Existing trade tracking code continues to work
- No changes to Signal dataclass required
- No changes to main.py, main_swing.py, main_us30.py required
- Only internal TradeTracker improvements

### Performance Considerations

- Trade ID generation with microseconds: negligible overhead
- Additional logging: minimal impact (only when trades active)
- Validation checks: O(1) dictionary lookups
- No impact on signal detection performance
