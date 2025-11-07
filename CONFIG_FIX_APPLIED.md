# Configuration Fix Applied

## Problem
All scanners were crashing on startup with the error:
```
SignalRulesConfig.__init__() got an unexpected keyword argument 'adx_min_trend'
```

## Root Cause
The configuration files (`config/config.json`, `us30_scanner/config_us30_swing.json`, etc.) contained additional fields in the `signal_rules` section that were not defined in the `SignalRulesConfig` dataclass in `src/config_loader.py`.

## Solution
Updated `src/config_loader.py` to add all missing optional fields to the `SignalRulesConfig` dataclass:

### Added Fields:
- `adx_min_trend` - ADX minimum trend threshold
- `enable_extreme_rsi_signals` - Enable extreme RSI signal detection
- `adx_min_momentum_shift` - ADX minimum for momentum shift detection
- `adx_min_trend_alignment` - ADX minimum for trend alignment
- `rsi_momentum_threshold` - RSI momentum change threshold
- `require_price_confirmation` - Require price confirmation for signals
- `volume_reversal_threshold` - Volume threshold for reversal detection
- `mean_reversion_atr_threshold` - ATR threshold for mean reversion
- `max_spread_pips` - Maximum acceptable spread in pips
- `acceptable_spread_pips` - Acceptable spread in pips
- `key_level_threshold_pips` - Key level threshold in pips
- `stoch_oversold` - Stochastic oversold level
- `stoch_overbought` - Stochastic overbought level
- `stop_loss_points` - Stop loss in points
- `take_profit_points_quick` - Quick take profit in points
- `take_profit_points_extended` - Extended take profit in points

All fields are marked as `Optional` with default value `None` to maintain backward compatibility.

### Additional Fix:
Relaxed the `volume_spike_threshold` validation from requiring > 1.0 to requiring > 0, as some strategies use thresholds below 1.0.

## Status
✅ Configuration loading now works correctly
✅ All scanners should start without errors

## Next Steps
Restart the scanners on your Linux server:
```bash
./restart_scanners.sh
```

Then check status:
```bash
./status_scanners.sh
```
