# Requirements Document

## Introduction

The trading scanner system is experiencing critical signal quality issues across multiple assets. US30 is generating zero signals despite market movements, while XAU/USD and BTC/USD are producing too many weak signals that result in trading losses. Analysis shows that existing signal detection strategies lack proper quality filtering, trend validation, and risk management controls. This feature will enhance signal quality through stricter confluence requirements, improved trend validation, and adaptive filtering mechanisms to ensure only high-probability setups generate alerts.

## Glossary

- **Scanner System**: The automated trading signal detection system monitoring BTC/USD, XAU/USD, and US30 across multiple timeframes
- **Signal Quality Filter**: Component that evaluates signal strength using confluence factors and confidence scoring
- **Confluence Factors**: Multiple technical conditions that must align to validate a trading signal (trend, volume, momentum, support/resistance)
- **Confidence Score**: Numerical rating (1-5) indicating signal strength based on confluence factors
- **Momentum Shift Strategy**: Detects RSI turning points with ADX confirmation and volume support
- **Trend Alignment Strategy**: Identifies cascade EMA alignment with RSI confirmation
- **Signal Detector**: Component responsible for identifying trading opportunities based on technical indicators
- **RSI**: Relative Strength Index - momentum oscillator (using RSI(7) for Gold, RSI(14) for BTC/US30)
- **ADX**: Average Directional Index - measures trend strength (minimum 18-22 depending on asset)
- **EMA**: Exponential Moving Average - trend-following indicator (using EMA 9, 21, 50)
- **ATR**: Average True Range - volatility indicator used for stop-loss and take-profit calculations
- **Volume Ratio**: Current volume divided by volume moving average
- **VWAP**: Volume Weighted Average Price - institutional trading benchmark
- **Duplicate Detection**: Mechanism to prevent sending similar signals within a time window

## Requirements

### Requirement 1

**User Story:** As a trader, I want US30 signals to be generated when valid setups exist, so that I don't miss profitable trading opportunities in the Dow Jones index

#### Acceptance Criteria

1. WHEN US30 market data shows momentum shift conditions (RSI turning with ADX above 22), THE US30 Signal Detector SHALL generate signals with appropriate entry, stop-loss, and take-profit levels
2. WHEN US30 market data shows trend alignment conditions (cascade EMA alignment with RSI confirmation), THE US30 Signal Detector SHALL generate signals with volume at least 0.8x average
3. WHEN US30 Signal Detector evaluates market conditions, THE US30 Signal Detector SHALL log detailed diagnostic information including which conditions passed and which failed
4. WHEN US30 Signal Detector checks for signals, THE US30 Signal Detector SHALL verify all required indicators have valid numeric values without NaN entries
5. WHEN US30 Signal Detector generates a signal, THE System SHALL verify the signal passes quality filters before sending alerts

### Requirement 2

**User Story:** As a trader, I want only high-quality signals for XAU/USD and BTC/USD, so that I avoid weak setups that result in trading losses

#### Acceptance Criteria

1. WHEN any signal is generated for XAU/USD or BTC/USD, THE Signal Quality Filter SHALL require minimum 4 confluence factors for signal approval
2. WHEN Signal Quality Filter evaluates a signal, THE Signal Quality Filter SHALL calculate a confidence score from 1 to 5 based on weighted confluence factors
3. WHEN a signal has confidence score below 4, THE Signal Quality Filter SHALL reject the signal and log the rejection reason
4. WHEN a signal passes quality filters, THE System SHALL include the confidence score and confluence factors in the alert message
5. WHEN Signal Quality Filter rejects a signal, THE System SHALL log which specific confluence factors were missing or weak

### Requirement 3

**User Story:** As a trader, I want momentum shift signals to confirm actual trend direction, so that I don't receive counter-trend signals that fail

#### Acceptance Criteria

1. WHEN Momentum Shift Strategy detects bullish RSI turn for any asset, THE Signal Detector SHALL verify price is above EMA(50) to confirm uptrend context
2. WHEN Momentum Shift Strategy detects bearish RSI turn for any asset, THE Signal Detector SHALL verify price is below EMA(50) to confirm downtrend context
3. WHEN Momentum Shift Strategy detects RSI turn, THE Signal Detector SHALL verify price action over last 10 candles aligns with signal direction
4. WHEN price is below EMA(50) and bullish RSI turn is detected, THE Signal Detector SHALL reject the signal and log trend conflict
5. WHEN price is above EMA(50) and bearish RSI turn is detected, THE Signal Detector SHALL reject the signal and log trend conflict

### Requirement 4

**User Story:** As a trader, I want trend alignment signals to have stronger ADX requirements, so that I only trade in established trends with momentum

#### Acceptance Criteria

1. WHEN Trend Alignment Strategy evaluates BTC/USD signals, THE Signal Detector SHALL require ADX at least 20 for trend confirmation
2. WHEN Trend Alignment Strategy evaluates XAU/USD signals, THE Signal Detector SHALL require ADX at least 19 for trend confirmation
3. WHEN Trend Alignment Strategy evaluates US30 signals, THE Signal Detector SHALL require ADX at least 22 for trend confirmation
4. WHEN ADX is below the required threshold, THE Signal Detector SHALL reject trend alignment signals and log ADX value
5. WHEN ADX meets threshold, THE Signal Detector SHALL include ADX value in signal metadata for trader reference

### Requirement 5

**User Story:** As a trader, I want volume requirements to be asset-specific and strategy-specific, so that signals match each market's characteristics

#### Acceptance Criteria

1. WHERE Momentum Shift Strategy generates signals for XAU/USD, THE Signal Detector SHALL require volume at least 1.2x average
2. WHERE Momentum Shift Strategy generates signals for BTC/USD, THE Signal Detector SHALL require volume at least 1.2x average
3. WHERE Momentum Shift Strategy generates signals for US30, THE Signal Detector SHALL require volume at least 0.8x average
4. WHERE Trend Alignment Strategy generates signals for any asset, THE Signal Detector SHALL require volume at least 0.8x average
5. WHEN volume is below required threshold, THE Signal Detector SHALL reject the signal and log volume ratio

### Requirement 6

**User Story:** As a trader, I want RSI momentum thresholds to be more conservative, so that I only receive signals with clear momentum shifts

#### Acceptance Criteria

1. WHEN Momentum Shift Strategy checks RSI change for BTC/USD or US30, THE Signal Detector SHALL require RSI change of at least 3.0 points over 2 consecutive candles
2. WHEN Momentum Shift Strategy checks RSI change for XAU/USD, THE Signal Detector SHALL require RSI change of at least 2.5 points over 2 consecutive candles
3. WHEN RSI change is below threshold, THE Signal Detector SHALL reject momentum shift signal and log RSI values
4. WHEN RSI change meets threshold, THE Signal Detector SHALL verify RSI direction matches signal type (rising for LONG, falling for SHORT)
5. WHERE configuration specifies custom rsi_momentum_threshold, THE Signal Detector SHALL use that value instead of defaults

### Requirement 7

**User Story:** As a trader, I want duplicate signal prevention to be more intelligent, so that legitimate new signals are not blocked while avoiding spam

#### Acceptance Criteria

1. WHEN a signal is generated, THE Signal Quality Filter SHALL check for duplicate signals within asset-specific time windows (5 minutes for scalp, 60 minutes for swing)
2. WHEN comparing signals for duplication, THE Signal Quality Filter SHALL consider signals duplicate if they have same signal type AND entry price within 0.5 percent
3. WHEN a duplicate signal is detected, THE Signal Quality Filter SHALL log the duplicate detection with previous signal timestamp and skip sending alert
4. WHEN market conditions change significantly (price moves more than 1.0 percent), THE Signal Quality Filter SHALL allow new signals even within duplicate window
5. WHEN a signal is not duplicate, THE Signal Quality Filter SHALL add it to recent signals history with timestamp and price

### Requirement 8

**User Story:** As a trader, I want EMA cloud breakout signals to have stricter breakout confirmation, so that I avoid false breakouts

#### Acceptance Criteria

1. WHEN EMA Cloud Breakout Strategy detects potential breakout, THE Signal Detector SHALL verify price breaks recent 10-candle high or low by at least 0.2 percent
2. WHEN EMA Cloud Breakout Strategy generates signal, THE Signal Detector SHALL require volume at least 1.5x average for breakout confirmation
3. WHEN EMA Cloud Breakout Strategy checks RSI, THE Signal Detector SHALL require RSI between 30 and 70 to avoid extremes
4. WHEN price breaks range but volume is weak, THE Signal Detector SHALL reject the signal and log volume ratio
5. WHEN breakout is confirmed, THE Signal Detector SHALL use tighter stop-loss (1.2 ATR) and conservative take-profit (1.5 ATR)

### Requirement 9

**User Story:** As a trader, I want mean reversion signals to have stricter reversal pattern requirements, so that I only trade clear reversals

#### Acceptance Criteria

1. WHEN Mean Reversion Strategy detects price overextension, THE Signal Detector SHALL require price at least 1.8 ATR away from VWAP (increased from 1.5 ATR)
2. WHEN Mean Reversion Strategy checks RSI extremes, THE Signal Detector SHALL require RSI below 20 for oversold or above 80 for overbought (stricter than 25/75)
3. WHEN Mean Reversion Strategy evaluates reversal patterns, THE Signal Detector SHALL require clear pin bar, engulfing, or doji candle formation
4. WHEN Mean Reversion Strategy generates signal, THE Signal Detector SHALL require volume at least 1.5x average (increased from 1.3x)
5. WHEN reversal pattern is weak or volume insufficient, THE Signal Detector SHALL reject the signal and log specific failure reason

### Requirement 10

**User Story:** As a trader, I want signal quality metrics to be tracked and logged, so that I can analyze which strategies and confluence factors produce winning trades

#### Acceptance Criteria

1. WHEN any signal is generated, THE System SHALL log the strategy name, confidence score, and all confluence factors that contributed
2. WHEN Signal Quality Filter evaluates a signal, THE System SHALL log the weighted confluence score calculation with individual factor weights
3. WHEN a signal is rejected, THE System SHALL log the rejection reason with specific thresholds that were not met
4. WHEN a signal is sent to trader, THE System SHALL include quality metrics in alert message (confidence score, key confluence factors)
5. WHEN scanner completes a scan cycle, THE System SHALL log summary statistics including signals generated, signals rejected, and rejection reasons

### Requirement 11

**User Story:** As a trader, I want H4 HVG signals to have additional quality validation, so that gap-based signals are high probability

#### Acceptance Criteria

1. WHEN H4 HVG Strategy detects a gap, THE H4 HVG Detector SHALL verify gap size is at least 0.3 percent of price for significance
2. WHEN H4 HVG Strategy generates signal, THE H4 HVG Detector SHALL require volume spike at least 2.0x average at gap formation
3. WHEN H4 HVG Strategy evaluates gap fill, THE H4 HVG Detector SHALL verify price approaches gap with momentum (RSI confirming direction)
4. WHEN H4 HVG signal is generated, THE Signal Quality Filter SHALL apply same confluence requirements as other strategies (minimum 4 factors)
5. WHEN H4 HVG gap is too small or volume insufficient, THE H4 HVG Detector SHALL reject the signal and log gap metrics

### Requirement 12

**User Story:** As a trader, I want configurable quality thresholds per asset, so that signal filtering can be tuned to each market's characteristics

#### Acceptance Criteria

1. WHERE configuration specifies min_confluence_factors for an asset, THE Signal Quality Filter SHALL use that value instead of default 4
2. WHERE configuration specifies min_confidence_score for an asset, THE Signal Quality Filter SHALL use that value instead of default 4
3. WHERE configuration specifies asset-specific ADX thresholds, THE Signal Detector SHALL use those values for trend validation
4. WHERE configuration specifies asset-specific volume thresholds, THE Signal Detector SHALL use those values for volume confirmation
5. WHEN configuration is updated, THE System SHALL log the new thresholds and apply them to subsequent signal evaluations

### Requirement 13

**User Story:** As a system administrator, I want comprehensive diagnostic logging for signal generation, so that I can troubleshoot why signals are or are not being generated

#### Acceptance Criteria

1. WHEN Signal Detector evaluates any strategy, THE System SHALL log the strategy name, timeframe, and current market conditions (price, EMAs, RSI, ADX, volume)
2. WHEN Signal Detector checks confluence factors, THE System SHALL log each factor evaluation with pass/fail status and actual values
3. WHEN Signal Quality Filter rejects a signal, THE System SHALL log detailed rejection reason including which thresholds were not met
4. WHEN Signal Detector generates a signal, THE System SHALL log complete signal details including all indicator values and confluence factors
5. WHEN scanner completes a scan cycle with no signals, THE System SHALL log summary of why each strategy did not generate signals

### Requirement 14

**User Story:** As a trader, I want risk-reward ratios to be validated before signals are sent, so that I only receive trades with favorable risk-reward profiles

#### Acceptance Criteria

1. WHEN any signal is generated, THE Signal Detector SHALL calculate risk-reward ratio as (take_profit - entry) / (entry - stop_loss) for LONG or (entry - take_profit) / (stop_loss - entry) for SHORT
2. WHEN risk-reward ratio is below 1.5, THE Signal Quality Filter SHALL reject the signal and log the calculated ratio
3. WHEN risk-reward ratio is between 1.5 and 2.0, THE Signal Quality Filter SHALL reduce confidence score by 1 point
4. WHEN risk-reward ratio is above 2.5, THE Signal Quality Filter SHALL increase confidence score by 1 point (maximum 5)
5. WHEN signal is sent to trader, THE System SHALL include risk-reward ratio in alert message for trader evaluation

### Requirement 15

**User Story:** As a trader, I want signals to avoid trading during low-liquidity periods, so that I don't receive signals when spreads are wide and execution is poor

#### Acceptance Criteria

1. WHEN current time is during known low-liquidity periods (weekends, major holidays), THE Signal Detector SHALL suppress all signal generation
2. WHEN XAU/USD scanner evaluates signals outside London or New York sessions, THE Signal Quality Filter SHALL increase minimum confluence requirement to 5 factors
3. WHEN volume moving average is below asset-specific minimum threshold, THE Signal Detector SHALL suppress signal generation and log low liquidity warning
4. WHERE configuration specifies trading_hours for an asset, THE Signal Detector SHALL only generate signals during those hours
5. WHEN low-liquidity condition is detected, THE System SHALL log the condition and time until normal liquidity resumes
