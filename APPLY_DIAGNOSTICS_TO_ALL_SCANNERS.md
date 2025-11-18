# Apply Diagnostic System to All Scanners

## Status
- ✅ main.py (BTC Scalp) - COMPLETE
- ✅ main_swing.py (BTC Swing) - COMPLETE  
- ✅ main_us100.py (US100/NASDAQ) - COMPLETE
- ✅ main_us30.py (US30 Momentum) - COMPLETE
- ✅ main_multi_symbol.py (Multi-Symbol) - COMPLETE
- ✅ Gold scanners - N/A (Handled by multi-symbol scanner)

## Pattern to Apply

For each scanner file, make these changes:

### 1. Add Imports (at top of file)
```python
from src.signal_quality_filter import SignalQualityFilter, QualityConfig
from src.signal_diagnostics import SignalDiagnostics
from src.config_validator import ConfigValidator
from src.bypass_mode import BypassMode
```

### 2. Initialize Diagnostic System (before market_client)
```python
# Initialize diagnostic system
diagnostics = SignalDiagnostics("Scanner-Name")  # Use appropriate name
logger.info("Diagnostic system initialized")

# Validate configuration
validator = ConfigValidator()
warnings = validator.validate_config(config)
if warnings:
    for warning in warnings:
        logger.warning(f"Config: {warning}")

# Initialize bypass mode
bypass_mode = BypassMode(config, None)  # Will set alerter later
```

### 3. Pass Diagnostics to SignalDetector
```python
signal_detector = SignalDetector(
    ...,
    diagnostics=diagnostics  # ADD THIS LINE
)
```

### 4. Set Alerter for Bypass Mode (after alerter is created)
```python
# Set alerter for bypass mode
bypass_mode.alerter = alerter
```

### 5. Initialize Quality Filter (after alerter)
```python
# Initialize quality filter
quality_filter_config = config.get('quality_filter', {})
quality_config = QualityConfig(
    min_confluence_factors=quality_filter_config.get('min_confluence_factors', 3),
    min_confidence_score=quality_filter_config.get('min_confidence_score', 3),
    duplicate_window_seconds=quality_filter_config.get('duplicate_window_seconds', 600),
    duplicate_price_tolerance_pct=quality_filter_config.get('duplicate_price_tolerance_pct', 1.0),
    significant_price_move_pct=quality_filter_config.get('significant_price_move_pct', 1.5),
    min_risk_reward=quality_filter_config.get('min_risk_reward', 1.2)
)
quality_filter = SignalQualityFilter(quality_config, diagnostics=diagnostics)
logger.info("Signal Quality Filter initialized")
```

### 6. Apply Quality Filter to Signals (in main loop)
```python
if detected_signal:
    # Apply quality filter (unless bypass mode)
    if bypass_mode.should_bypass_filters():
        logger.warning("⚠️ BYPASS MODE - Skipping quality filter")
        signal_to_send = detected_signal
    else:
        filter_result = quality_filter.evaluate_signal(detected_signal, candles)
        
        if filter_result.passed:
            logger.info(f"✓ Signal passed quality filter")
            signal_to_send = detected_signal
        else:
            logger.info(f"✗ Signal rejected: {filter_result.rejection_reason}")
            signal_to_send = None
    
    # Send alert if signal passed
    if signal_to_send and alerter:
        alerter.send_signal_alert(signal_to_send)
        quality_filter.add_signal_to_history(signal_to_send)
```

## Scanner-Specific Names

Use these names for SignalDiagnostics:
- main.py: "BTC-Scalp"
- main_swing.py: "BTC-Swing"
- main_us30.py: "US30-Momentum"
- main_us100.py: "US100-Scanner"
- main_multi_symbol.py: Create per-symbol (e.g., "BTC-Multi", "ETH-Multi")
- Gold scanners: "Gold-Scalp", "Gold-Swing"

## Files Already Updated
1. ✅ main.py - Full integration complete
2. ✅ main_swing.py - Full integration complete
3. ✅ main_us30.py - Full integration complete
4. ✅ main_us100.py - Full integration complete
5. ✅ main_multi_symbol.py - Full integration complete
6. ✅ All 8 config files - Relaxed thresholds applied
7. ✅ src/signal_detector.py - Diagnostics integrated
8. ✅ src/signal_quality_filter.py - Diagnostics integrated
9. ✅ src/symbol_orchestrator.py - Diagnostics support added

## Remaining Work

### main_us30.py
Apply the pattern above with scanner name "US30-Momentum"

### main_multi_symbol.py
- More complex - needs per-symbol diagnostics
- Create diagnostics instance for each symbol scanner
- Pass to SymbolScanner instances

### Gold Scanners
If you have separate gold scanner files, apply the same pattern with:
- "Gold-Scalp" for scalping
- "Gold-Swing" for swing trading

## Testing After Updates

For each scanner:
1. Start the scanner
2. Check logs for "Diagnostic system initialized"
3. Verify no Python errors
4. Monitor for signal generation
5. Check diagnostic output in logs

## Quick Test Command
```bash
# Test imports
python -c "from src.signal_diagnostics import SignalDiagnostics; print('OK')"

# Test scanner startup
python main_swing.py  # Should see diagnostic initialization
```

## Service Integration

All scanners are already added to:
- ✅ restart_scanners.sh
- ✅ status_scanners.sh  
- ✅ clean_and_restart.sh
- ✅ US100 service file created

## Summary

The diagnostic system provides:
- ✅ Detection attempt tracking
- ✅ Filter rejection logging
- ✅ Data quality monitoring
- ✅ Configuration validation
- ✅ Bypass mode for testing
- ✅ Actionable recommendations

Once applied to all scanners, you'll have full visibility into why signals are/aren't being generated across your entire trading system.
