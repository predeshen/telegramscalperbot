# Quick Start: Unified Strategy Arsenal

## 🚀 Get Started in 5 Minutes

### Step 1: Run All Tests (Verify Everything Works)

```bash
# Run all strategy tests
python -m pytest tests/test_strategy_helpers.py -v
python -m pytest tests/test_strategy_registry.py -v
python -m pytest tests/test_strategy_orchestrator.py -v
python -m pytest tests/test_fibonacci_strategy.py -v
python -m pytest tests/test_support_resistance_strategy.py -v
python -m pytest tests/test_key_level_strategy.py -v
python -m pytest tests/test_adx_rsi_momentum_strategy.py -v

# Or run all at once
python -m pytest tests/test_*strategy*.py -v
```

**Expected Result**: 81 tests passing, 0 failures

### Step 2: Enable Unified Strategies

Edit `config/config.json`:

```json
{
  "use_unified_strategies": true
}
```

### Step 3: Test with BTC Scanner

The configuration is already set up for BTC scalp and swing scanners. Just run your scanner:

```bash
python main.py  # or your BTC scanner start command
```

### Step 4: Monitor Signals

Watch for new strategy names in your alerts:
- "Fibonacci Retracement"
- "Support/Resistance Bounce"
- "Key Level Break & Retest"
- "ADX+RSI+Momentum"

## 📊 Available Strategies

### 1. Fibonacci Retracement
**Best For**: Trending markets with clear swings
**Signals**: Bounces at 38.2%, 50%, 61.8% levels
**Confidence**: 5 for golden ratios (38.2%, 61.8%)

### 2. Support/Resistance Bounce
**Best For**: Ranging markets, consolidation
**Signals**: Bounces at historically proven levels
**Confidence**: 5 for 3+ touches or round numbers

### 3. Key Level Break & Retest
**Best For**: Breakout trading, trend continuation
**Signals**: Successful retests after level breaks
**Confidence**: 5 for major round numbers

### 4. ADX+RSI+Momentum
**Best For**: Strong trending markets
**Signals**: Triple confluence of ADX, RSI, and price momentum
**Confidence**: 5 for ADX > 25 (strong trend)

## ⚙️ Configuration Examples

### Enable Only High-Confidence Strategies

```json
{
  "strategies": {
    "fibonacci_retracement": {
      "enabled": true,
      "params": {
        "swing_lookback": 50,
        "level_tolerance_percent": 0.3,
        "require_reversal_candle": true
      }
    },
    "support_resistance_bounce": {
      "enabled": false
    },
    "key_level_break_retest": {
      "enabled": true
    },
    "adx_rsi_momentum": {
      "enabled": true,
      "params": {
        "adx_min": 25,
        "rsi_momentum_threshold": 4.0
      }
    }
  }
}
```

### Aggressive Settings (More Signals)

```json
{
  "strategies": {
    "fibonacci_retracement": {
      "params": {
        "level_tolerance_percent": 1.0,
        "volume_threshold": 1.0,
        "require_reversal_candle": false
      }
    },
    "support_resistance_bounce": {
      "params": {
        "min_touches": 1,
        "volume_threshold": 1.0
      }
    }
  }
}
```

### Conservative Settings (Fewer, Higher Quality Signals)

```json
{
  "strategies": {
    "fibonacci_retracement": {
      "params": {
        "level_tolerance_percent": 0.3,
        "volume_threshold": 1.5,
        "require_reversal_candle": true
      }
    },
    "adx_rsi_momentum": {
      "params": {
        "adx_min": 25,
        "rsi_momentum_threshold": 5.0,
        "volume_threshold": 1.5
      }
    }
  }
}
```

## 🎯 Strategy Priority by Market Condition

The orchestrator automatically selects strategies based on market conditions:

### When ADX > 25 (Strong Trend)
Priority: ADX+RSI+Momentum → Key Level Break & Retest → Trend Alignment

### When ADX < 20 (Ranging)
Priority: Support/Resistance Bounce → Mean Reversion

### When ATR > 1.5x (High Volatility)
Priority: ADX+RSI+Momentum → Momentum Shift → EMA Cloud Breakout

### When ATR < 0.8x (Low Volatility)
Priority: Mean Reversion → Support/Resistance Bounce → Fibonacci Retracement

## 🔍 Understanding Signal Metadata

Each signal includes detailed metadata. Example:

```python
# Fibonacci Signal
{
  'fib_level': '61.8%',
  'swing_high': 50000.0,
  'swing_low': 45000.0,
  'is_golden_ratio': True
}

# Support/Resistance Signal
{
  'level_type': 'support',
  'level_price': 45000.0,
  'touches': 3,
  'is_round_number': True
}

# Key Level Signal
{
  'level': 50000.0,
  'break_direction': 'up',
  'break_candles_ago': 7,
  'break_volume_ratio': 2.1
}

# ADX+RSI+Momentum Signal
{
  'adx': 28.5,
  'is_strong_trend': True,
  'rsi_momentum': 4.2,
  'price_momentum': 'higher_highs'
}
```

## 🐛 Troubleshooting

### No Signals Generated

1. Check `use_unified_strategies` is `true`
2. Verify strategies are enabled in config
3. Check ADX/ATR values - market might not meet conditions
4. Review volume - might be below thresholds

### Too Many Signals

1. Increase volume thresholds
2. Enable `require_reversal_candle: true`
3. Increase `adx_min` for ADX+RSI+Momentum
4. Reduce `level_tolerance_percent` for Fibonacci

### Signals Not Matching Market

1. Adjust asset-specific parameters
2. Review `strategy_priority` configuration
3. Check if market conditions match strategy requirements

## 📈 Performance Tips

1. **Start Conservative**: Use default settings first
2. **Monitor 24-48 Hours**: Collect data before adjusting
3. **One Strategy at a Time**: Enable strategies gradually
4. **Track Metadata**: Use signal metadata to understand why signals triggered
5. **Adjust Per Asset**: BTC, Gold, and US30 may need different parameters

## 🎓 Learning Resources

- **Test Files**: See `tests/test_*_strategy.py` for usage examples
- **Implementation**: Check `src/signal_detector.py` for strategy logic
- **Helpers**: Review `src/strategy_helpers.py` for calculation details
- **Summary**: Read `UNIFIED_STRATEGY_IMPLEMENTATION_SUMMARY.md` for complete overview

## ✅ Verification Checklist

- [ ] All 81 tests passing
- [ ] `use_unified_strategies: true` in config
- [ ] At least one strategy enabled
- [ ] Scanner running without errors
- [ ] Receiving signals with new strategy names
- [ ] Signal metadata populated correctly

## 🎉 You're Ready!

The unified strategy system is now active. Monitor your signals and adjust parameters as needed. Happy trading! 🚀
