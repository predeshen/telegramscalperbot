# Quick Start Guide - Signal Detection Fix

## 🚀 Immediate Actions

### 1. Test the BTC Scalp Scanner (Already Integrated)
```bash
python main.py
```

**What to Look For:**
- ✅ "Diagnostic system initialized" in logs
- ✅ "Config: ..." warnings (if any thresholds are out of bounds)
- ✅ Strategy detection attempts logged
- ✅ Signals being generated

### 2. Check the Logs
```bash
tail -f logs/scanner.log
```

**Look for these patterns:**
```
✓ EMA Crossover detected LONG signal on 5m
✗ Trend Alignment no signal
✓ Signal passed quality filter: 4/7 factors, confidence=3/5
```

### 3. Monitor for 1 Hour
- Count how many signals are generated
- Check if they're being filtered (and why)
- Review diagnostic output

## 📊 What Changed

### Thresholds (More Lenient):
| Parameter | Before | After | Change |
|-----------|--------|-------|--------|
| Confluence | 4/7 | 3/7 | -25% |
| Confidence | 4/5 | 3/5 | -25% |
| Volume | 1.5x | 1.3x | -13% |
| RSI Range | 30-70 | 25-75 | +67% |
| ADX Min | 18-19 | 15 | -20% |
| Duplicate Window | 5min | 10min | +100% |
| Price Tolerance | 0.5% | 1.0% | +100% |

### New Features:
- ✅ **Diagnostic Tracking** - See every detection attempt
- ✅ **Config Validation** - Warns about bad thresholds
- ✅ **Data Quality Checks** - Validates before detection
- ✅ **Bypass Mode** - Emergency testing mode

## 🔧 Quick Tuning

### If You Want MORE Signals:
Edit `config/config.json`:
```json
{
  "quality_filter": {
    "min_confluence_factors": 2,
    "min_confidence_score": 2,
    "min_risk_reward": 1.0
  }
}
```

### If You Want FEWER (Higher Quality) Signals:
```json
{
  "quality_filter": {
    "min_confluence_factors": 4,
    "min_confidence_score": 4,
    "min_risk_reward": 1.5
  }
}
```

### Emergency Testing (Bypass All Filters):
```json
{
  "bypass_mode": {
    "enabled": true,
    "auto_disable_after_hours": 2
  }
}
```
**⚠️ Use only for testing! Auto-disables after 2 hours.**

## 🎯 Next Scanners to Update

The same changes need to be applied to:
1. `main_swing.py` (BTC Swing)
2. `main_us30.py` (US30 Momentum)
3. `main_multi_symbol.py` (Multi-Symbol)

**Pattern to follow (from main.py):**
```python
# 1. Add imports
from src.signal_diagnostics import SignalDiagnostics
from src.config_validator import ConfigValidator
from src.bypass_mode import BypassMode

# 2. Initialize in __init__
self.diagnostics = SignalDiagnostics("Scanner-Name")
validator = ConfigValidator()
self.bypass_mode = BypassMode(config_dict, None)

# 3. Pass to components
self.signal_detector = SignalDetector(..., diagnostics=self.diagnostics)
self.quality_filter = SignalQualityFilter(config, diagnostics=self.diagnostics)

# 4. Set alerter
self.bypass_mode.alerter = self.alerter
```

## 📈 Expected Results

### Realistic Expectations:
- **BTC Scalp (1m, 5m, 15m):** 3-5 signals/day
- **BTC Swing (15m, 1h, 4h, 1d):** 1-3 signals/day
- **US30 Momentum (1m, 5m, 15m):** 2-4 signals/day
- **Multi-Symbol (per symbol):** 1-2 signals/day

### Total Across 8 Scanners:
- **Before:** 0-2 signals/day
- **After:** 10-20 signals/day (estimated)

## 🐛 Troubleshooting

### Still No Signals?
1. **Check data quality:**
   ```
   grep "Data quality issues" logs/scanner.log
   ```

2. **Check rejection reasons:**
   ```
   grep "Signal rejected" logs/scanner.log
   ```

3. **Enable bypass mode** (temporarily):
   - Edit config.json
   - Set `bypass_mode.enabled: true`
   - Restart scanner
   - Check if signals are generated

4. **Review diagnostic output:**
   ```
   grep "detection attempt" logs/scanner.log
   ```

### Too Many Signals?
1. Increase thresholds gradually
2. Check signal quality (win rate)
3. Review confluence factors being met

### Diagnostic System Not Working?
1. Verify imports in scanner file
2. Check `diagnostics` is passed to components
3. Restart scanner to reload code

## 📞 Support

### Check Implementation Status:
```bash
# Verify diagnostic files exist
ls -la src/signal_diagnostics.py
ls -la src/config_validator.py
ls -la src/bypass_mode.py

# Check config updates
grep "min_confluence_factors" config/config.json
grep "diagnostics" config/config.json
```

### Review Diagnostic Output:
```bash
# See detection attempts
grep "✓\|✗" logs/scanner.log | tail -20

# See rejection reasons
grep "rejected" logs/scanner.log | tail -10

# See data quality issues
grep "Data quality" logs/scanner.log | tail -10
```

## ✅ Success Checklist

After starting the scanner, verify:
- [ ] "Diagnostic system initialized" appears in logs
- [ ] Config validation runs (warnings if any)
- [ ] Strategy detection attempts are logged
- [ ] Signals are being generated (or clear rejection reasons shown)
- [ ] Quality filter evaluations are logged
- [ ] No Python errors or crashes

## 🎉 You're Ready!

The system is now configured to:
1. ✅ Generate more signals (relaxed thresholds)
2. ✅ Show you why signals are/aren't generated (diagnostics)
3. ✅ Validate data quality before detection
4. ✅ Allow easy tuning per asset

**Start with main.py and monitor for 1 hour to see the difference!**
