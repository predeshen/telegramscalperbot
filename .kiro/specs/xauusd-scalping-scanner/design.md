# Design Document - XAU/USD Scalping Scanner

## Overview

The XAU/USD Scalping Scanner is a session-aware, news-conscious trading signal detection system specifically designed for Gold scalping. Unlike the BTC scanner, this system accounts for Gold's unique characteristics: session-based liquidity patterns, USD correlation, news sensitivity, and respect for technical levels. The scanner operates in different modes based on trading sessions and automatically pauses during high-impact news events.

### Key Design Principles

- **Session-Aware Operation**: Different strategies for Asian (range tracking) vs London/NY (active trading)
- **News Avoidance**: Automatic pause before/after high-impact USD events
- **Spread Consciousness**: Only trade when spreads are tight (< 10 pips)
- **Level Respect**: Honor daily highs/lows and psychological round numbers
- **Multiple Strategies**: Asian Range Breakout, EMA Cloud Breakout, Mean Reversion
- **Detailed Reasoning**: Every signal explains the setup with institutional context

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                  XAU/USD Scalping Scanner                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Market     │─────▶│  Session     │─────▶│  Strategy │ │
│  │   Data       │      │  Manager     │      │  Selector │ │
│  │   Client     │      └──────────────┘      └─────┬─────┘ │
│  └──────┬───────┘                                   │       │
│         │                                            │       │
│         │      ┌──────────────┐                     │       │
│         │─────▶│    News      │                     │       │
│         │      │   Calendar   │                     │       │
│         │      └──────────────┘                     │       │
│         │                                            │       │
│         │      ┌──────────────┐                     │       │
│         │─────▶│    Spread    │                     │       │
│         │      │   Monitor    │                     │       │
│         │      └──────────────┘                     │       │
│         │                                            ▼       │
│         │                                    ┌───────────┐  │
│         │                                    │  Signal   │  │
│         │                                    │ Detector  │  │
│         │                                    └─────┬─────┘  │
│         │                                          │        │
│         │                                          ▼        │
│         │                                    ┌───────────┐  │
│         │                                    │   Trade   │  │
│         │                                    │  Tracker  │  │
│         │                                    └─────┬─────┘  │
│         │                                          │        │
│         │                                          ▼        │
│         │                                    ┌───────────┐  │
│         │                                    │ Telegram  │  │
│         │                                    │  Alerter  │  │
│         │                                    └───────────┘  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │   Health     │                                           │
│  │   Monitor    │                                           │
│  └──────────────┘                                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Language**: Python 3.9+
- **Data Provider**: CCXT (supports forex/CFD brokers with XAU/USD)
- **WebSocket**: Real-time Gold price streaming
- **Technical Indicators**: pandas-ta + custom implementations
- **Alerts**: Telegram (python-telegram-bot)
- **News Calendar**: Custom implementation with configurable events
- **Logging**: Python logging with session-aware formatting

## Components and Interfaces

### 1. Session Manager

**Responsibility**: Determine current trading session and adjust scanner behavior.

**Interface**:
```python
class SessionManager:
    def get_current_session() -> str  # "ASIAN", "LONDON", "NEW_YORK"
    def is_active_session() -> bool  # True if London or NY
    def get_asian_range() -> tuple  # (high, low) from Asian session
    def should_trade() -> bool  # False during Asian or news
```

**Implementation Details**:
- Track GMT time to determine session
- Asian: 00:00-08:00 GMT (range tracking only)
- London: 08:00-16:00 GMT (active trading)
- New York: 12:00-20:00 GMT (active trading)
- Overlap: 12:00-16:00 GMT (highest liquidity)
- Store Asian range high/low for breakout detection

### 2. News Calendar

**Responsibility**: Track high-impact USD economic events and pause trading.

**Interface**:
```python
class NewsCalendar:
    def add_event(date: datetime, name: str, impact: str) -> None
    def is_news_imminent(minutes: int = 30) -> bool
    def get_next_event() -> Optional[NewsEvent]
    def should_pause_trading() -> bool
```

**Implementation Details**:
- Maintain list of high-impact events (NFP, CPI, FOMC, GDP)
- Check if event within 30 minutes
- Auto-pause 30 min before, resume 15 min after
- Send Telegram notification on pause/resume
- Events stored in JSON config file

**Event Format**:
```json
{
  "events": [
    {
      "date": "2025-11-08T13:30:00Z",
      "name": "Non-Farm Payrolls (NFP)",
      "impact": "HIGH"
    }
  ]
}
```

### 3. Spread Monitor

**Responsibility**: Monitor bid-ask spread and pause when too wide.

**Interface**:
```python
class SpreadMonitor:
    def update_spread(bid: float, ask: float) -> None
    def get_current_spread_pips() -> float
    def is_spread_acceptable() -> bool  # < 10 pips
    def should_pause_trading() -> bool  # > 15 pips
```

**Implementation Details**:
- Calculate spread in pips: (ask - bid) * 10 (for Gold)
- Acceptable: < 10 pips
- Warning: 10-15 pips
- Pause: > 15 pips
- Log spread violations
- Include spread in all signal alerts

### 4. Strategy Selector

**Responsibility**: Choose appropriate strategy based on session and market conditions.

**Interface**:
```python
class StrategySelector:
    def select_strategy(session: str, market_state: dict) -> str
    # Returns: "ASIAN_RANGE_BREAKOUT", "EMA_CLOUD", "MEAN_REVERSION"
```

**Strategy Selection Logic**:
- **Asian Session**: Range tracking only (no signals)
- **London Open (08:00-10:00 GMT)**: Asian Range Breakout preferred
- **London/NY Active**: EMA Cloud Breakout primary
- **Overextension (>1.5x ATR from VWAP)**: Mean Reversion
- **Normal conditions**: EMA Cloud Breakout

### 5. Gold Signal Detector

**Responsibility**: Detect signals using Gold-specific strategies.

**Interface**:
```python
class GoldSignalDetector:
    def detect_asian_range_breakout(data: DataFrame) -> Optional[Signal]
    def detect_ema_cloud_breakout(data: DataFrame) -> Optional[Signal]
    def detect_mean_reversion(data: DataFrame) -> Optional[Signal]
    def check_key_levels(price: float) -> dict
```

**Signal Strategies**:

#### Asian Range Breakout
```python
# Conditions:
1. Asian range defined (high/low from 00:00-08:00 GMT)
2. Price breaks above/below range with 5m candle close
3. Price re-tests broken level
4. Confirmation candle (pin bar or engulfing)
5. Volume > 1.2x average

# Entry: On confirmation candle close
# Stop: Just beyond broken level (tight)
# Target: 1.5x ATR or next key level
```

#### EMA Cloud Breakout
```python
# Conditions:
1. Price above/below EMA(20) and EMA(50)
2. EMA(20) above/below EMA(50) (trend alignment)
3. Price above/below VWAP (institutional bias)
4. Price breaks recent range high/low
5. Volume > 1.2x average
6. RSI 25-75 (not overextended)

# Entry: On breakout candle close
# Stop: 1.2x ATR beyond entry
# Target: 1.5x ATR
```

#### Mean Reversion
```python
# Conditions:
1. Price > 1.5x ATR away from VWAP
2. RSI > 75 (overbought) or < 25 (oversold)
3. Reversal candle forms (pin bar, doji, engulfing)
4. Volume confirms reversal

# Entry: On reversal candle close
# Stop: Beyond reversal candle wick
# Target: VWAP (mean reversion)
```

### 6. Key Level Tracker

**Responsibility**: Track and respect major support/resistance levels.

**Interface**:
```python
class KeyLevelTracker:
    def update_daily_levels(high: float, low: float, close: float) -> None
    def get_psychological_levels() -> List[float]  # 2350, 2400, etc.
    def get_nearest_level(price: float) -> tuple  # (level, distance)
    def is_near_level(price: float, threshold_pips: int = 5) -> bool
```

**Implementation Details**:
- Track daily high, low, previous close
- Generate psychological levels (50-pip intervals)
- Calculate distance to nearest level
- Include in signal reasoning when near level
- Prefer signals that align with level bounces/breaks

## Data Models

### Signal Data Structure (Enhanced for Gold)

```python
@dataclass
class GoldSignal(Signal):
    """Gold-specific signal with additional context."""
    strategy: str  # "ASIAN_RANGE_BREAKOUT", "EMA_CLOUD", "MEAN_REVERSION"
    session: str  # "LONDON", "NEW_YORK"
    spread_pips: float
    asian_range_high: Optional[float]
    asian_range_low: Optional[float]
    nearest_key_level: Optional[float]
    distance_to_level_pips: Optional[float]
```

### Configuration Schema (Gold-Specific)

```json
{
  "exchange": {
    "name": "oanda",
    "symbol": "XAU/USD",
    "timeframes": ["1m", "5m"]
  },
  "indicators": {
    "ema_fast": 20,
    "ema_slow": 50,
    "atr_period": 14,
    "rsi_period": 14,
    "volume_ma_period": 20
  },
  "signal_rules": {
    "volume_spike_threshold": 1.2,
    "rsi_min": 25,
    "rsi_max": 75,
    "stop_loss_atr_multiplier": 1.2,
    "take_profit_atr_multiplier": 1.5,
    "mean_reversion_atr_threshold": 1.5,
    "max_spread_pips": 15,
    "acceptable_spread_pips": 10
  },
  "sessions": {
    "asian_start_gmt": "00:00",
    "asian_end_gmt": "08:00",
    "london_start_gmt": "08:00",
    "london_end_gmt": "16:00",
    "newyork_start_gmt": "12:00",
    "newyork_end_gmt": "20:00"
  },
  "news_calendar_file": "config/news_events.json",
  "telegram": {
    "enabled": true,
    "bot_token": "YOUR_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  }
}
```

## Alert Format (Gold-Specific)

```
🟢 GOLD LONG SIGNAL - Asian Range Breakout

📍 ENTRY LEVELS
Entry: $2,403.50
Stop Loss: $2,402.40 (-0.05%, 11 pips)
Take Profit: $2,405.90 (+0.10%, 24 pips)
Breakeven: $2,404.70 (move SL here at 50%)

📊 TRADE INFO
Strategy: Asian Range Breakout
Session: London Open (High Liquidity)
R:R: 1:2.18 | TF: 5m
Spread: 8 pips ✓ | ATR: $0.80

🎯 REASONING
📈 ASIAN RANGE BREAKOUT SETUP
   • Asian Range: $2,398.20 - $2,402.80 (4.6 pips)
   • Breakout above $2,402.80 at London open
   • Re-test confirmed at $2,403.00 with bullish pin bar
   
✓ CONFLUENCE FACTORS (5/5):
   1. Clean break above Asian high with volume
   2. Bullish pin bar rejection at re-test level
   3. Volume spike: 1.45x average (genuine breakout)
   4. EMA(20) > EMA(50): Uptrend confirmed
   5. Price above VWAP: Institutional buyers active

💡 WHY BUY NOW:
   • London open provides liquidity for breakout
   • Asian range acted as accumulation zone
   • Re-test confirms level flip (resistance → support)
   • Volume confirms institutional participation
   • Tight stop due to clear invalidation level

📊 KEY LEVELS
   • Nearest Support: $2,400.00 (psychological)
   • Nearest Resistance: $2,410.00 (daily high)
   • Trading 3.5 pips above support level

📈 TRADE MANAGEMENT
1️⃣ Enter at $2,403.50
2️⃣ At $2,404.70: Move stop to breakeven
3️⃣ At $2,405.90: Close 50%, trail rest
4️⃣ If stopped: Wait for next London/NY setup

⚠️ RISK NOTES
   • Avoid if NFP/FOMC within 30 minutes
   • Exit if spread widens > 15 pips
   • Session ends at 16:00 GMT

⏰ 08:15:33 GMT | Session: London Open
```

## Testing Strategy

### Unit Tests
- Session detection accuracy
- News calendar event matching
- Spread calculation
- Asian range tracking
- Key level identification
- Each strategy signal detection

### Integration Tests
- Full signal flow with session awareness
- News pause/resume functionality
- Spread-based trading pause
- Multi-strategy selection

### Live Testing
- Paper trade during London/NY sessions
- Verify news avoidance
- Confirm spread monitoring
- Validate session transitions

## Deployment

### Additional Requirements for Gold
- Forex/CFD broker API access (OANDA, FXCM, etc.)
- News calendar maintenance (weekly updates)
- Session time zone handling (GMT conversion)
- Spread monitoring infrastructure

### Performance Targets
- Session detection: < 1ms
- News check: < 10ms
- Spread check: < 5ms
- Signal detection: < 2s (same as BTC)

## Security & Risk Management

### Gold-Specific Risks
1. **Spread Risk**: Wide spreads can invalidate setups
2. **News Risk**: Extreme volatility during events
3. **Session Risk**: Low liquidity in Asian session
4. **Slippage Risk**: Fast moves during London open

### Mitigation
- Automatic spread monitoring and pause
- News calendar with 30-min buffer
- Session-aware strategy selection
- ATR-based dynamic stops

## Future Enhancements

- DXY (Dollar Index) correlation analysis
- Real yields integration
- Multi-timeframe confluence
- Order flow/DOM integration
- Automated position sizing based on volatility
- Session-specific parameter optimization
