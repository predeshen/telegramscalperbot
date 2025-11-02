# Requirements Document - XAU/USD Scalping Scanner

## Introduction

The XAU/USD Scalping Scanner is an automated trading signal detection system specifically designed for Gold (XAU/USD) scalping. Unlike cryptocurrency markets, Gold is a traditional safe-haven asset heavily influenced by USD strength, geopolitical events, and trading sessions. The system monitors real-time Gold price movements, identifies high-probability scalping opportunities using session-aware technical analysis, and delivers actionable trade alerts with detailed reasoning via Telegram.

## Glossary

- **Scanner**: The automated system that monitors XAU/USD market data and generates trade signals
- **Signal**: A trade opportunity identified by the Scanner with entry, stop-loss, take-profit, and reasoning
- **XAU/USD**: Gold spot price quoted in US Dollars
- **Session**: Trading session periods (Asian, London, New York) with different liquidity characteristics
- **Asian Range**: Price consolidation during low-volume Asian session (00:00-08:00 GMT)
- **London Open**: High-volume session start (08:00 GMT) often triggering breakouts
- **VWAP**: Volume Weighted Average Price - institutional fair value benchmark
- **EMA**: Exponential Moving Average - trend-following indicator
- **ATR**: Average True Range - volatility measure for stop/target sizing
- **RSI**: Relative Strength Index - momentum oscillator
- **Spread**: Bid-ask price difference (cost of trading)
- **Confluence**: Multiple independent technical signals confirming the same trade direction
- **Asian Range Breakout**: Strategy exploiting breakout from Asian session consolidation
- **Mean Reversion**: Price returning to average after extreme moves

## Requirements

### Requirement 1

**User Story:** As a Gold scalper, I want the Scanner to monitor XAU/USD price data in real-time on 1-minute and 5-minute timeframes during optimal trading sessions, so that I can capture fast-moving scalping opportunities.

#### Acceptance Criteria

1. WHEN the Scanner starts, THE Scanner SHALL connect to a forex/CFD data provider API and subscribe to XAU/USD price streams
2. THE Scanner SHALL process incoming 1-minute and 5-minute candlestick data with a maximum latency of 2 seconds
3. THE Scanner SHALL identify the current trading session (Asian, London, New York) based on GMT time
4. WHEN the current session is Asian (00:00-08:00 GMT), THE Scanner SHALL operate in range-tracking mode only
5. WHEN the current session is London (08:00-16:00 GMT) or New York (12:00-20:00 GMT), THE Scanner SHALL operate in active signal detection mode

### Requirement 2

**User Story:** As a Gold scalper, I want the Scanner to avoid trading during high-impact news events, so that I don't get stopped out by unpredictable volatility.

#### Acceptance Criteria

1. THE Scanner SHALL maintain a calendar of high-impact USD economic events (NFP, CPI, FOMC, GDP)
2. WHEN a high-impact event is scheduled within 30 minutes, THE Scanner SHALL pause signal generation
3. THE Scanner SHALL resume signal generation 15 minutes after the scheduled event time
4. THE Scanner SHALL log all news-related pauses with event name and time
5. THE Scanner SHALL send a Telegram notification when entering and exiting news pause mode

### Requirement 3

**User Story:** As a Gold scalper, I want the Scanner to detect Asian Range Breakout setups with re-test confirmation, so that I can trade high-probability breakouts during London/New York opens.

#### Acceptance Criteria

1. WHEN the Asian session ends (08:00 GMT), THE Scanner SHALL calculate and store the Asian range high and low
2. WHEN price breaks above the Asian high with a 5-minute candle close, THE Scanner SHALL mark a potential bullish breakout
3. WHEN price breaks below the Asian low with a 5-minute candle close, THE Scanner SHALL mark a potential bearish breakout
4. WHEN price re-tests the broken level and forms a confirmation candle, THE Scanner SHALL generate a signal
5. THE Scanner SHALL include the Asian range levels in the signal alert for context

### Requirement 4

**User Story:** As a Gold scalper, I want the Scanner to detect EMA cloud breakouts with VWAP and RSI confirmation, so that I can trade momentum moves aligned with institutional bias.

#### Acceptance Criteria

1. WHEN price is above EMA(20) and EMA(50) AND EMA(20) > EMA(50), THE Scanner SHALL classify market bias as bullish
2. WHEN price is below EMA(20) and EMA(50) AND EMA(20) < EMA(50), THE Scanner SHALL classify market bias as bearish
3. WHEN bullish bias exists AND price breaks above recent range high with volume > 1.2x average, THE Scanner SHALL generate a LONG signal
4. WHEN bearish bias exists AND price breaks below recent range low with volume > 1.2x average, THE Scanner SHALL generate a SHORT signal
5. THE Scanner SHALL validate RSI is between 25-75 to avoid overextended entries

### Requirement 5

**User Story:** As a Gold scalper, I want the Scanner to detect mean reversion opportunities when price deviates excessively from VWAP, so that I can profit from snap-back moves.

#### Acceptance Criteria

1. WHEN price moves more than 1.5x ATR away from VWAP, THE Scanner SHALL mark an overextension condition
2. WHEN overextension occurs AND RSI > 75, THE Scanner SHALL watch for bearish reversal candles
3. WHEN overextension occurs AND RSI < 25, THE Scanner SHALL watch for bullish reversal candles
4. WHEN a reversal candle forms (pin bar or engulfing), THE Scanner SHALL generate a mean reversion signal
5. THE Scanner SHALL set take-profit at VWAP for mean reversion trades

### Requirement 6

**User Story:** As a Gold scalper, I want signals to include detailed reasoning explaining why the trade setup is valid, so that I can understand and trust the signal logic.

#### Acceptance Criteria

1. THE Scanner SHALL include a "Reasoning" section in every signal alert
2. THE Scanner SHALL list all confluence factors that aligned (minimum 3 required)
3. THE Scanner SHALL explain the market bias (bullish/bearish/neutral) and why
4. THE Scanner SHALL describe the specific trigger (breakout, re-test, reversal, etc.)
5. THE Scanner SHALL include session context (e.g., "London open breakout" or "NY session momentum")

### Requirement 7

**User Story:** As a Gold scalper, I want the Scanner to provide trade management updates after I enter a position, so that I know when to close or continue holding.

#### Acceptance Criteria

1. WHEN a signal is generated, THE Scanner SHALL track the trade as "ACTIVE" with entry price and timestamp
2. WHEN price reaches 50% of take-profit distance, THE Scanner SHALL send an update: "Move stop to breakeven"
3. WHEN price reaches take-profit level, THE Scanner SHALL send an update: "Target reached - Close trade"
4. WHEN price moves against the trade and approaches stop-loss, THE Scanner SHALL send a warning: "Stop-loss approaching"
5. WHEN a trade is closed (TP or SL hit), THE Scanner SHALL send a final update with P&L percentage

### Requirement 8

**User Story:** As a Gold scalper, I want the Scanner to monitor spread conditions and only trade when spreads are tight, so that I don't lose money to excessive trading costs.

#### Acceptance Criteria

1. THE Scanner SHALL monitor the current bid-ask spread for XAU/USD
2. WHEN the spread exceeds 15 pips, THE Scanner SHALL pause signal generation
3. WHEN the spread returns below 10 pips, THE Scanner SHALL resume signal generation
4. THE Scanner SHALL include current spread in signal alerts
5. THE Scanner SHALL log spread violations and send a Telegram notification when spreads are too wide

### Requirement 9

**User Story:** As a Gold scalper, I want signals to include dynamic stop-loss and take-profit levels based on ATR, so that my risk management adapts to current volatility.

#### Acceptance Criteria

1. THE Scanner SHALL calculate stop-loss as entry ± (1.2 × ATR) for all signals
2. THE Scanner SHALL calculate take-profit as entry ± (1.5 × ATR) for breakout signals
3. THE Scanner SHALL calculate take-profit as VWAP for mean reversion signals
4. THE Scanner SHALL include risk-reward ratio in the signal alert
5. THE Scanner SHALL calculate position size recommendation based on 0.5% account risk

### Requirement 10

**User Story:** As a Gold scalper, I want the Scanner to respect major support and resistance levels, so that I can trade with institutional order flow.

#### Acceptance Criteria

1. THE Scanner SHALL identify daily high, daily low, and previous day close as key levels
2. THE Scanner SHALL identify psychological round numbers (e.g., 2350, 2400, 2450) as key levels
3. WHEN price approaches a key level within 5 pips, THE Scanner SHALL include level proximity in signal reasoning
4. THE Scanner SHALL prefer signals that align with key level bounces or breaks
5. THE Scanner SHALL include nearest key levels in signal alerts for context

### Requirement 11

**User Story:** As a system administrator, I want the Scanner to run reliably as a service with session-aware scheduling, so that it operates efficiently during optimal trading hours.

#### Acceptance Criteria

1. THE Scanner SHALL run continuously but adjust activity based on session
2. WHEN Asian session is active, THE Scanner SHALL reduce processing frequency to every 30 seconds
3. WHEN London or New York session is active, THE Scanner SHALL process every candle close
4. THE Scanner SHALL log session transitions and activity level changes
5. THE Scanner SHALL expose health metrics including session status and signal counts per session
