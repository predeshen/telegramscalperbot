# Requirements Document

## Introduction

The trading scanner system is generating good signals for XAU/USD but poor quality signals for BTC/USD and no signals at all for US30. Analysis shows that the Gold scanner uses multiple specialized strategies (Momentum Shift, Asian Range Breakout, EMA Cloud Breakout, Mean Reversion, Trend Following, and H4 HVG) while BTC and US30 rely on more restrictive confluence-based detection. This feature will improve signal detection for BTC/USD and US30 by adapting successful strategies from the Gold scanner while maintaining signal quality.

## Glossary

- **Scanner System**: The automated trading signal detection system that monitors BTC/USD, XAU/USD, and US30 across multiple timeframes
- **Signal Detector**: Component responsible for identifying trading opportunities based on technical indicators
- **Momentum Shift Strategy**: Detects RSI turning points with ADX confirmation and volume support
- **Trend Alignment Strategy**: Identifies cascade EMA alignment (Price > EMA9 > EMA21 > EMA50) with RSI confirmation
- **Confluence Detection**: Current BTC strategy requiring multiple factors (price vs VWAP, EMA crossover, volume spike, RSI range)
- **Gold Signal Detector**: The XAU/USD signal detector with multiple specialized strategies
- **US30 Swing Detector**: The US30 signal detector currently using trend continuation and reversal strategies
- **BTC Signal Detector**: The BTC/USD signal detector in src/signal_detector.py
- **RSI**: Relative Strength Index - momentum oscillator (using both RSI(7) and RSI(14))
- **ADX**: Average Directional Index - measures trend strength
- **EMA**: Exponential Moving Average - trend-following indicator
- **ATR**: Average True Range - volatility indicator
- **Volume Ratio**: Current volume divided by volume moving average

## Requirements

### Requirement 1

**User Story:** As a trader, I want BTC/USD to detect momentum shift signals like Gold does, so that I can catch trend changes early

#### Acceptance Criteria

1. WHEN RSI(14) increases over 3 consecutive candles AND ADX is above 18, THE BTC Signal Detector SHALL identify a bullish momentum shift
2. WHEN RSI(14) decreases over 3 consecutive candles AND ADX is above 18, THE BTC Signal Detector SHALL identify a bearish momentum shift
3. WHEN a momentum shift is detected AND volume is at least 1.2x average, THE BTC Signal Detector SHALL generate a signal with 2.0 ATR stop loss and 3.0 ATR take profit
4. WHEN a bullish momentum shift is detected, THE BTC Signal Detector SHALL verify price is above EMA(50) to confirm uptrend context
5. WHEN a bearish momentum shift is detected, THE BTC Signal Detector SHALL verify price is below EMA(50) to confirm downtrend context

### Requirement 2

**User Story:** As a trader, I want US30 to detect momentum shift signals, so that I can capture trend changes in the Dow Jones index

#### Acceptance Criteria

1. WHEN RSI(14) increases over 3 consecutive candles AND ADX is above 22, THE US30 Swing Detector SHALL identify a bullish momentum shift
2. WHEN RSI(14) decreases over 3 consecutive candles AND ADX is above 22, THE US30 Swing Detector SHALL identify a bearish momentum shift
3. WHEN a momentum shift is detected AND volume is at least 0.8x average, THE US30 Swing Detector SHALL generate a signal with configured ATR multipliers
4. WHEN a bullish momentum shift is detected, THE US30 Swing Detector SHALL verify RSI is rising to confirm momentum direction
5. WHEN a bearish momentum shift is detected, THE US30 Swing Detector SHALL verify RSI is falling to confirm momentum direction

### Requirement 3

**User Story:** As a trader, I want BTC/USD to detect trend alignment signals, so that I can enter trades when all EMAs are aligned

#### Acceptance Criteria

1. WHEN price is above EMA(9) AND EMA(9) is above EMA(21) AND EMA(21) is above EMA(50), THE BTC Signal Detector SHALL identify bullish cascade alignment
2. WHEN price is below EMA(9) AND EMA(9) is below EMA(21) AND EMA(21) is below EMA(50), THE BTC Signal Detector SHALL identify bearish cascade alignment
3. WHEN bullish cascade alignment exists AND RSI is above 50 AND ADX is above 19, THE BTC Signal Detector SHALL generate a LONG signal
4. WHEN bearish cascade alignment exists AND RSI is below 50 AND ADX is above 19, THE BTC Signal Detector SHALL generate a SHORT signal
5. WHEN trend alignment signal is generated, THE BTC Signal Detector SHALL require volume at least 0.8x average

### Requirement 4

**User Story:** As a trader, I want US30 trend alignment detection to work correctly, so that I can trade strong trends in the Dow Jones

#### Acceptance Criteria

1. WHEN US30 Swing Detector evaluates trend alignment, THE US30 Swing Detector SHALL log the current EMA cascade status for debugging
2. WHEN bullish cascade exists AND RSI is above 50 AND RSI is rising, THE US30 Swing Detector SHALL generate a LONG signal
3. WHEN bearish cascade exists AND RSI is below 50 AND RSI is falling, THE US30 Swing Detector SHALL generate a SHORT signal
4. WHEN trend alignment conditions are not met, THE US30 Swing Detector SHALL log which specific condition failed
5. WHEN ADX is below 19, THE US30 Swing Detector SHALL reject trend alignment signals due to weak trend strength

### Requirement 5

**User Story:** As a trader, I want BTC/USD to detect EMA cloud breakout signals, so that I can capture range breakouts with strong momentum

#### Acceptance Criteria

1. WHEN EMA(21) is above EMA(50) AND price is above VWAP, THE BTC Signal Detector SHALL identify bullish EMA cloud alignment
2. WHEN EMA(21) is below EMA(50) AND price is below VWAP, THE BTC Signal Detector SHALL identify bearish EMA cloud alignment
3. WHEN EMA cloud alignment exists AND price breaks recent 10-candle high/low, THE BTC Signal Detector SHALL detect a breakout
4. WHEN breakout is detected AND RSI is between 25 and 75 AND volume is at least 1.5x average, THE BTC Signal Detector SHALL generate a signal
5. WHEN EMA cloud breakout signal is generated, THE BTC Signal Detector SHALL use 1.2 ATR stop loss and 1.5 ATR take profit

### Requirement 6

**User Story:** As a trader, I want BTC/USD to detect mean reversion signals, so that I can profit from overextended price moves

#### Acceptance Criteria

1. WHEN price is more than 1.5 ATR away from VWAP, THE BTC Signal Detector SHALL identify price overextension
2. WHEN price is overextended AND RSI is below 25 (oversold) or above 75 (overbought), THE BTC Signal Detector SHALL check for reversal patterns
3. WHEN reversal candle pattern is detected (pin bar, doji, or engulfing), THE BTC Signal Detector SHALL identify potential reversal
4. WHEN reversal pattern exists AND volume is at least 1.3x average, THE BTC Signal Detector SHALL generate a mean reversion signal
5. WHEN mean reversion signal is generated, THE BTC Signal Detector SHALL target VWAP as take profit with 1.0 ATR stop loss

### Requirement 7

**User Story:** As a trader, I want US30 to detect EMA cloud breakout and mean reversion signals, so that I have more trading opportunities

#### Acceptance Criteria

1. WHEN US30 market data shows EMA cloud alignment and range breakout, THE US30 Swing Detector SHALL generate EMA cloud breakout signals
2. WHEN US30 price is overextended from VWAP with RSI extremes, THE US30 Swing Detector SHALL generate mean reversion signals
3. WHEN US30 Swing Detector detects reversal patterns, THE US30 Swing Detector SHALL use pin bar, doji, and engulfing candle detection
4. WHEN US30 EMA cloud breakout signal is generated, THE US30 Swing Detector SHALL use 1.2 ATR stop loss and 1.5 ATR take profit
5. WHEN US30 mean reversion signal is generated, THE US30 Swing Detector SHALL target VWAP with 1.0 ATR stop loss

### Requirement 8

**User Story:** As a trader, I want signal detection to try multiple strategies in priority order, so that valid setups are not missed

#### Acceptance Criteria

1. WHEN BTC Signal Detector evaluates market data, THE BTC Signal Detector SHALL check strategies in order: momentum shift, trend alignment, EMA cloud breakout, mean reversion, then existing strategies
2. WHEN US30 Swing Detector evaluates market data, THE US30 Swing Detector SHALL check strategies in order: H4 HVG, momentum shift, trend alignment, EMA cloud breakout, mean reversion, then existing strategies
3. WHEN any strategy generates a signal, THE Signal Detector SHALL stop evaluation and return that signal
4. WHEN all strategies fail to generate a signal, THE Signal Detector SHALL return None
5. WHEN strategy priority order is changed, THE Signal Detector SHALL log the evaluation sequence for debugging

### Requirement 9

**User Story:** As a trader, I want appropriate volume thresholds for each strategy and asset, so that signals match market characteristics

#### Acceptance Criteria

1. WHERE BTC Signal Detector checks volume for momentum shift, THE BTC Signal Detector SHALL require volume at least 1.2x average
2. WHERE BTC Signal Detector checks volume for trend alignment, THE BTC Signal Detector SHALL require volume at least 0.8x average
3. WHERE BTC Signal Detector checks volume for EMA cloud breakout, THE BTC Signal Detector SHALL require volume at least 1.5x average
4. WHERE BTC Signal Detector checks volume for mean reversion, THE BTC Signal Detector SHALL require volume at least 1.3x average
5. WHERE US30 Swing Detector checks volume, THE US30 Swing Detector SHALL use same thresholds as BTC for consistency

### Requirement 10

**User Story:** As a trader, I want RSI momentum thresholds to be configurable, so that signal sensitivity can be tuned per asset

#### Acceptance Criteria

1. WHEN BTC Signal Detector checks RSI momentum, THE BTC Signal Detector SHALL use a configurable threshold (default 3.0 points change over 2 candles)
2. WHEN US30 Swing Detector checks RSI momentum, THE US30 Swing Detector SHALL use a configurable threshold (default 3.0 points change over 2 candles)
3. WHERE configuration specifies rsi_momentum_threshold, THE Signal Detector SHALL use that value instead of the default
4. WHEN RSI change is below the threshold, THE Signal Detector SHALL reject the momentum shift signal
5. WHEN RSI change meets or exceeds the threshold, THE Signal Detector SHALL proceed with other momentum shift checks

### Requirement 11

**User Story:** As a system administrator, I want comprehensive logging of signal detection attempts, so that I can diagnose why signals are or are not generated

#### Acceptance Criteria

1. WHEN BTC Signal Detector evaluates any strategy, THE BTC Signal Detector SHALL log the strategy name and key indicator values
2. WHEN BTC Signal Detector evaluates trend alignment, THE BTC Signal Detector SHALL log EMA cascade status and RSI level
3. WHEN US30 Swing Detector rejects a signal, THE US30 Swing Detector SHALL log which specific condition failed (ADX, volume, RSI, etc.)
4. WHEN any strategy generates a signal, THE Signal Detector SHALL log the strategy name, signal type, and key indicator values
5. WHEN all strategies fail to generate a signal, THE Signal Detector SHALL log a summary of why each strategy was rejected

### Requirement 12

**User Story:** As a trader, I want existing confluence and trend-following strategies to remain available, so that proven strategies continue working

#### Acceptance Criteria

1. WHEN new strategies are added, THE BTC Signal Detector SHALL retain existing confluence detection logic
2. WHEN new strategies are added, THE BTC Signal Detector SHALL retain existing trend-following detection logic
3. WHEN new strategies are added, THE US30 Swing Detector SHALL retain existing trend continuation and reversal logic
4. WHEN multiple strategies are available, THE Signal Detector SHALL evaluate them in priority order (new strategies before existing)
5. WHERE a higher priority strategy generates a signal, THE Signal Detector SHALL not evaluate lower priority strategies

### Requirement 13

**User Story:** As a trader, I want signal quality to remain high, so that I don't receive false signals

#### Acceptance Criteria

1. WHEN any signal is generated, THE Signal Detector SHALL verify all required indicators have valid numeric values (not NaN)
2. WHEN momentum shift signal is generated, THE Signal Detector SHALL verify ADX confirms trend strength
3. WHEN trend alignment signal is generated, THE Signal Detector SHALL verify RSI confirms trend direction
4. WHEN mean reversion signal is generated, THE Signal Detector SHALL verify reversal candle pattern exists
5. WHEN any signal is generated, THE Signal Detector SHALL check for duplicates within the configured time window
