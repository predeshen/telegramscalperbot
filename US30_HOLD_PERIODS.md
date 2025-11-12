# US30 Hold Period Classification

## Overview

The US30 Momentum Scanner now automatically classifies trades into **3 categories** based on setup strength and timeframe:

1. **SCALP** (intraday) - Quick moves, 2.0 ATR target
2. **DAY TRADE** (1-2 days) - Standard moves, 2.5 ATR target  
3. **SWING** (3-5 days) - Big moves, 3.75 ATR target

This helps you know upfront if you're looking at a quick scalp or a multi-day hold like your R2000 → R22000 example.

---

## Classification Criteria

### SWING TRADE (3-5 days) 🚀
**Target: 3.75 ATR** (~750-1500 points on US30)

Triggered when **2+ of these factors** are present:

1. **Higher Timeframe**: 15m, 1h, 4h, or 1d
2. **Strong Structure Break**: BOS/CHoCH with strength ≥ 4/5
3. **Large FVG**: Gap ≥ 0.15% (significant imbalance)
4. **Very Strong Momentum**: ADX > 35
5. **Extreme Volume**: > 2.0x average (institutional activity)

**Example Signal:**
```
🚀 LONG Signal - US30 (15m)
Strategy: US30 Momentum (SWING (3-5 days))
Confidence: ⭐⭐⭐⭐⭐ (5/5)

💰 Entry: 47,184.00
🛑 Stop Loss: 46,984.00
🎯 Take Profit: 47,934.00  ← 3.75 ATR
📊 Risk/Reward: 3.75

⏰ HOLD: SWING (3-5 days) (5 days)

✅ Confluence: Bullish FVG 0.18% | BOS (strength 5/5) | ADX 38.5 | Vol 2.3x
```

---

### DAY TRADE (1-2 days) 📅
**Target: 2.5 ATR** (~500-1000 points on US30)

Triggered when **1 factor** is present:

1. **Medium Timeframe**: 5m or 15m with strong setup
2. **Moderate Structure Break**: BOS/CHoCH with strength 3-4/5
3. **Medium FVG**: Gap 0.05-0.15%
4. **Strong Momentum**: ADX 25-35
5. **High Volume**: 1.5-2.0x average

**Example Signal:**
```
🚀 LONG Signal - US30 (5m)
Strategy: US30 Momentum (DAY TRADE (1-2 days))
Confidence: ⭐⭐⭐⭐ (4/5)

💰 Entry: 47,184.00
🛑 Stop Loss: 46,984.00
🎯 Take Profit: 47,684.00  ← 2.5 ATR
📊 Risk/Reward: 2.5

📅 HOLD: DAY TRADE (1-2 days) (2 days)

✅ Confluence: Bullish FVG 0.12% | BOS (strength 4/5) | ADX 28.5 | Vol 1.8x
```

---

### SCALP (intraday) ⚡
**Target: 2.0 ATR** (~400-800 points on US30)

Triggered when **no multi-day factors** are present:

- Lower timeframe (1m, 5m)
- Basic FVG or structure break
- Standard momentum (ADX 25-30)
- Normal volume (1.2-1.5x)

**Example Signal:**
```
🚀 LONG Signal - US30 (1m)
Strategy: US30 Momentum (SCALP (intraday))
Confidence: ⭐⭐⭐ (3/5)

💰 Entry: 47,184.00
🛑 Stop Loss: 46,984.00
🎯 Take Profit: 47,584.00  ← 2.0 ATR
📊 Risk/Reward: 2.0

✅ Confluence: Bullish FVG 0.08% | ADX 26.5 | Vol 1.3x
```

---

## Target Adjustments

| Hold Type | ATR Multiplier | Typical Points | Expected Duration |
|-----------|----------------|----------------|-------------------|
| **SCALP** | 2.0 ATR | 400-800 | Minutes to hours |
| **DAY TRADE** | 2.5 ATR | 500-1000 | 1-2 days |
| **SWING** | 3.75 ATR | 750-1500 | 3-5 days |

---

## Your R2000 → R22000 Example

Based on the charts you showed, that trade would have been classified as:

**SWING TRADE (3-5 days)**

Why?
- ✅ **15m timeframe** (higher timeframe)
- ✅ **Large FVG** (visible green box on chart)
- ✅ **Strong BOS** (broke previous high with conviction)
- ✅ **High volume** (institutional buying)
- ✅ **Strong ADX** (clear momentum)

**Signal would have shown:**
```
🚀 LONG Signal - US30 (15m)
Strategy: US30 Momentum (SWING (3-5 days))
Confidence: ⭐⭐⭐⭐⭐ (5/5)

💰 Entry: 47,000
🛑 Stop Loss: 46,800
🎯 Take Profit: 47,750  ← 3.75 ATR (R15,000)
📊 Risk/Reward: 3.75

⏰ HOLD: SWING (3-5 days) (5 days)

✅ Confluence: Bullish FVG 0.18% | BOS (strength 5/5) | ADX 38.5 | Vol 2.3x | 15m timeframe
```

**With trailing stop**, you would have caught the full R22,000 move!

---

## How to Use This Information

### For Scalps (Intraday)
- ✅ Take profit at target (2.0 ATR)
- ✅ Close before end of day
- ✅ Don't hold overnight
- ✅ Quick in, quick out

### For Day Trades (1-2 days)
- ✅ Take profit at target (2.5 ATR)
- ✅ Can hold overnight
- ✅ Trail stop after 1.5 ATR profit
- ✅ Monitor daily close

### For Swings (3-5 days)
- ✅ Initial target 3.75 ATR
- ✅ **Trail stop aggressively** after 2 ATR
- ✅ Let winners run (can go 5-10 ATR!)
- ✅ Monitor daily/4h closes
- ✅ **This is where R22,000 moves happen!**

---

## Configuration

You can adjust the classification thresholds in `config/us30_config.json`:

```json
{
  "us30_strategy": {
    "min_fvg_percent": 0.05,        // Minimum FVG for any signal
    "min_adx": 25,                  // Minimum ADX for entry
    "min_volume_ratio": 1.2,        // Minimum volume
    "initial_tp_atr": 2.5,          // Base TP (adjusted by hold type)
    "stop_loss_atr": 1.5,           // Stop loss
    "trail_after_atr": 1.5          // When to start trailing
  }
}
```

**For more swing trades:**
- Lower `min_adx` to 20
- Lower `min_fvg_percent` to 0.03
- Increase `initial_tp_atr` to 3.0

**For more scalps:**
- Increase `min_adx` to 30
- Increase `min_volume_ratio` to 1.5
- Keep `initial_tp_atr` at 2.5

---

## Telegram Alert Format

All signals now show the hold period:

**Scalp:**
```
⚡ HOLD: SCALP (intraday)
```

**Day Trade:**
```
📅 HOLD: DAY TRADE (1-2 days) (2 days)
```

**Swing:**
```
⏰ HOLD: SWING (3-5 days) (5 days)
```

This tells you immediately what kind of trade you're looking at!

---

## Key Takeaway

**The scanner now tells you upfront if this is a quick scalp or a multi-day swing trade.**

- **Scalps**: Quick profits, close same day
- **Day Trades**: Hold 1-2 days, standard targets
- **Swings**: Hold 3-5 days, **BIG TARGETS** (this is where R22,000 moves happen!)

When you see **"SWING (3-5 days)"** with 5-star confidence, that's your signal to let it run with a trailing stop! 🚀
