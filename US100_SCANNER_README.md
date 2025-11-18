# US100/NASDAQ Scanner

## Overview
Comprehensive trading scanner for the NASDAQ-100 index (US100) using multiple strategies including H4-HVG, Momentum Shift, Trend Alignment, EMA Cloud Breakout, and Mean Reversion.

## Features

### Strategies Enabled:
1. **H4 HVG (High Volume Gap)** - 4-hour timeframe gap detection
2. **Momentum Shift** - RSI turning with ADX confirmation
3. **Trend Alignment** - EMA cascade with strong trend
4. **EMA Cloud Breakout** - Range breakouts with EMA alignment
5. **Mean Reversion** - Overextended price reversals
6. **EMA Crossover** - Classic EMA9/EMA21 crossovers

### Timeframes:
- **1m** - Ultra-short scalping
- **5m** - Short-term scalping
- **15m** - Intraday trading
- **4h** - Swing trading + H4-HVG detection

### Key Features:
- ✅ **Diagnostic System** - Full visibility into detection attempts
- ✅ **Quality Filtering** - Multi-layer signal validation
- ✅ **Trade Tracking** - Automatic TP/SL monitoring
- ✅ **Excel Reporting** - Automated scan logging
- ✅ **Telegram Alerts** - Real-time notifications
- ✅ **Bypass Mode** - Emergency testing capability

## Quick Start

### 1. Start the Scanner
```bash
# Windows
start_us100.bat

# Linux/Mac
python main_us100.py
```

### 2. Monitor Logs
```bash
tail -f logs/us100_scanner.log
```

### 3. Check Telegram
You'll receive:
- Startup notification
- Signal alerts
- Trade updates (TP/SL hits)
- Heartbeat every 90 minutes with diagnostics

## Configuration

### File: `config/us100_config.json`

### Key Settings:
```json
{
  "symbol": "^NDX",
  "timeframes": ["1m", "5m", "15m", "4h"],
  
  "signal_rules": {
    "volume_spike_threshold": 1.3,
    "rsi_min": 25,
    "rsi_max": 75,
    "adx_min_trend_alignment": 18,
    "duplicate_time_window_minutes": 10
  },
  
  "quality_filter": {
    "min_confluence_factors": 3,
    "min_confidence_score": 3,
    "min_risk_reward": 1.2
  },
  
  "h4_hvg": {
    "enabled": true,
    "min_gap_percent": 0.12,
    "volume_spike_threshold": 1.4
  }
}
```

## Asset-Specific Tuning

### US100 Characteristics:
- **Higher volatility** than US30
- **Tech-heavy** - reacts strongly to tech news
- **Volume patterns** - Different from indices
- **Gap behavior** - Frequent overnight gaps

### Optimized Thresholds:
- Volume: 1.3x (scalp), 1.2x (swing)
- ADX: 18 minimum (slightly higher than BTC)
- RSI: 25-75 range (wide for volatility)
- H4 Gap: 0.12% minimum (lower than US30's 0.15%)

## Strategies Explained

### 1. H4 HVG (High Volume Gap)
**When:** 4-hour timeframe only
**Detects:** Price gaps with volume confirmation
**Entry:** Gap fill or breakout continuation
**Target:** Gap closure or 2x ATR
**Best For:** Swing trades, overnight gaps

### 2. Momentum Shift
**When:** All timeframes
**Detects:** RSI turning over 3 candles with ADX confirmation
**Entry:** On momentum reversal
**Target:** 2.5x ATR
**Best For:** Catching trend changes early

### 3. Trend Alignment
**When:** All timeframes
**Detects:** EMA cascade (Price > EMA9 > EMA21 > EMA50)
**Entry:** On strong trend confirmation
**Target:** 2.0x ATR
**Best For:** Riding established trends

### 4. EMA Cloud Breakout
**When:** All timeframes
**Detects:** Price breaking recent range with EMA alignment
**Entry:** On breakout confirmation
**Target:** 1.5x ATR
**Best For:** Range breakouts

### 5. Mean Reversion
**When:** All timeframes
**Detects:** Price overextended from VWAP (>1.5 ATR)
**Entry:** On reversal candle pattern
**Target:** VWAP (mean)
**Best For:** Catching reversals

## Expected Performance

### Signal Generation:
- **1m timeframe:** 2-4 signals/day
- **5m timeframe:** 2-3 signals/day
- **15m timeframe:** 1-2 signals/day
- **4h timeframe:** 0-1 signals/day (H4-HVG)

**Total:** 5-10 signals/day

### Quality Metrics:
- **Confluence:** 3/7 factors minimum
- **Confidence:** 3/5 score minimum
- **Risk/Reward:** 1.2:1 minimum

## Diagnostic Features

### Real-Time Monitoring:
```
✓ Momentum Shift detected LONG signal on 5m
✗ Trend Alignment no signal
✓ Signal passed quality filter: 4/7 factors, confidence=3/5
```

### Heartbeat Reports (Every 90 min):
- Detection attempts per strategy
- Success rates
- Top rejection reasons
- Recommendations for tuning

### Daily Summary:
- Total signals generated
- Filter rejection breakdown
- Data quality issues
- Performance recommendations

## Tuning Guide

### If Not Enough Signals:
1. Reduce `min_confluence_factors` to 2
2. Reduce `volume_spike_threshold` to 1.0
3. Widen RSI range to 20-80
4. Reduce `min_risk_reward` to 1.0

### If Too Many Low-Quality Signals:
1. Increase `min_confluence_factors` to 4
2. Increase `min_confidence_score` to 4
3. Increase `volume_spike_threshold` to 1.5
4. Increase `min_risk_reward` to 1.5

### For H4-HVG Specifically:
```json
{
  "h4_hvg": {
    "min_gap_percent": 0.15,  // Increase for fewer, larger gaps
    "volume_spike_threshold": 1.6,  // Increase for stronger confirmation
    "min_risk_reward": 1.5  // Increase for better R:R
  }
}
```

## Trading Hours

### Best Times (US100):
- **Pre-Market:** 08:00-09:30 EST (gap plays)
- **Market Open:** 09:30-11:00 EST (high volatility)
- **Lunch:** 11:00-14:00 EST (lower volume)
- **Power Hour:** 15:00-16:00 EST (closing moves)

### Configuration:
```json
{
  "asset_specific": {
    "US100": {
      "trading_hours": ["NewYork"]
    }
  }
}
```

## Troubleshooting

### No Signals Generated:
1. Check logs: `grep "detection attempt" logs/us100_scanner.log`
2. Check data quality: `grep "Data quality" logs/us100_scanner.log`
3. Enable bypass mode temporarily
4. Review diagnostic report in heartbeat

### Data Issues:
1. Verify Yahoo Finance connection
2. Check symbol is correct: `^NDX`
3. Verify timeframes are supported
4. Check for NaN in indicators

### Quality Filter Too Strict:
1. Review rejection reasons in logs
2. Adjust thresholds in config
3. Check diagnostic recommendations
4. Consider bypass mode for testing

## Files

### Core Files:
- `main_us100.py` - Scanner application
- `config/us100_config.json` - Configuration
- `start_us100.bat` - Windows launcher
- `logs/us100_scanner.log` - Application logs
- `logs/us100_scans.xlsx` - Excel report

### Dependencies:
- `src/yfinance_client.py` - Data source
- `src/signal_detector.py` - Strategy detection
- `src/signal_quality_filter.py` - Quality filtering
- `src/signal_diagnostics.py` - Diagnostic tracking
- `src/h4_hvg_detector.py` - H4-HVG strategy

## Comparison with Other Scanners

### US100 vs US30:
- **Volatility:** US100 higher (tech-heavy)
- **Volume:** US100 typically higher
- **Gap Size:** US100 smaller gaps more frequent
- **Strategies:** Same strategies, different thresholds

### US100 vs BTC:
- **Market Hours:** US100 has defined hours
- **Volatility:** BTC higher 24/7
- **Volume Patterns:** US100 more predictable
- **Strategies:** Same core strategies

## Advanced Features

### Bypass Mode:
```json
{
  "bypass_mode": {
    "enabled": true,
    "auto_disable_after_hours": 2
  }
}
```
**Use Case:** Testing if core detection works without filters

### Excel Reporting:
- Automatic scan logging
- Hourly email reports
- Performance tracking
- Strategy analysis

### Trade Tracking:
- Automatic TP/SL monitoring
- Telegram notifications on hits
- Trailing stop support
- Performance metrics

## Support

### Check Status:
```bash
# View recent signals
grep "SIGNAL" logs/us100_scanner.log | tail -10

# View rejection reasons
grep "rejected" logs/us100_scanner.log | tail -10

# View diagnostic summary
grep "Diagnostic Report" logs/us100_scanner.log | tail -1
```

### Test Configuration:
```bash
python -c "import json; print(json.load(open('config/us100_config.json')))"
```

### Verify Components:
```bash
python -c "from src.signal_diagnostics import SignalDiagnostics; print('OK')"
python -c "from src.h4_hvg_detector import H4HVGDetector; print('OK')"
```

## Success Metrics

Track these to measure performance:
- **Signals/Day:** Target 5-10
- **Win Rate:** Target >50%
- **Avg R:R:** Target >1.5:1
- **Detection Rate:** % of patterns that pass filters
- **Data Quality:** % of clean data iterations

## Next Steps

1. **Start Scanner:** Run `start_us100.bat`
2. **Monitor for 1 Hour:** Check signal generation
3. **Review Diagnostics:** Check heartbeat report
4. **Tune Thresholds:** Based on recommendations
5. **Track Performance:** Monitor win rate and R:R

## 🎉 Ready to Trade!

The US100 scanner is configured with:
- ✅ Multiple proven strategies
- ✅ H4-HVG for gap trading
- ✅ Optimized thresholds for NASDAQ
- ✅ Full diagnostic visibility
- ✅ Quality filtering
- ✅ Trade tracking

**Start the scanner and let it find opportunities!**
