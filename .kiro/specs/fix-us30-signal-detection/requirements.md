# Requirements Document

## Introduction

The US30 swing scanner is failing to detect trading signals despite significant market movements. Analysis of scan data reveals missing indicator calculations (EMA 9, VWAP, Stochastic) and overly restrictive signal detection logic that prevents the system from identifying valid trading opportunities. This feature will improve signal detection reliability while maintaining quality trade setups.

## Glossary

- **Scanner**: The automated system that monitors US30 (Dow Jones Industrial Average) price data and generates trading signals
- **Signal**: A trading opportunity alert (LONG or SHORT) with entry price, stop loss, and take profit levels
- **EMA**: Exponential Moving Average - a trend-following indicator
- **VWAP**: Volume Weighted Average Price - shows average price weighted by volume
- **Stochastic**: Momentum oscillator comparing closing price to price range over time
- **ATR**: Average True Range - measures market volatility
- **Timeframe**: The candlestick period being analyzed (4h, 1d)
- **Indicator Calculator**: Component that computes technical indicators from price data
- **Signal Detector**: Component that analyzes indicators to identify trading opportunities

## Requirements

### Requirement 1

**User Story:** As a trader, I want all technical indicators to be calculated correctly, so that the scanner has complete data for signal detection

#### Acceptance Criteria

1. WHEN THE Scanner fetches market data, THE Indicator Calculator SHALL compute EMA 9 values for all candles
2. WHEN THE Scanner fetches market data, THE Indicator Calculator SHALL compute VWAP values for all candles
3. WHEN THE Scanner fetches market data, THE Indicator Calculator SHALL compute Stochastic K and D values for all candles
4. WHEN THE Scanner logs scan results to Excel, THE System SHALL include all calculated indicator values without NaN entries
5. WHEN THE Scanner initializes, THE System SHALL verify that all required indicators are present in the data

### Requirement 2

**User Story:** As a trader, I want the scanner to detect strong downtrends, so that I can capture SHORT opportunities during bearish market conditions

#### Acceptance Criteria

1. WHEN price is below EMA 9 AND EMA 9 is below EMA 21 AND EMA 21 is below EMA 50, THE Signal Detector SHALL identify a bearish trend alignment
2. WHEN a bearish trend alignment exists AND RSI is below 50, THE Signal Detector SHALL generate a SHORT signal
3. WHEN a SHORT signal is generated, THE System SHALL calculate stop loss at entry price plus 2.0 times ATR
4. WHEN a SHORT signal is generated, THE System SHALL calculate take profit at entry price minus 3.0 times ATR
5. WHEN a SHORT signal is generated, THE System SHALL include trend direction as "bearish" in signal metadata

### Requirement 3

**User Story:** As a trader, I want the scanner to detect strong uptrends, so that I can capture LONG opportunities during bullish market conditions

#### Acceptance Criteria

1. WHEN price is above EMA 9 AND EMA 9 is above EMA 21 AND EMA 21 is above EMA 50, THE Signal Detector SHALL identify a bullish trend alignment
2. WHEN a bullish trend alignment exists AND RSI is above 50, THE Signal Detector SHALL generate a LONG signal
3. WHEN a LONG signal is generated, THE System SHALL calculate stop loss at entry price minus 2.0 times ATR
4. WHEN a LONG signal is generated, THE System SHALL calculate take profit at entry price plus 3.0 times ATR
5. WHEN a LONG signal is generated, THE System SHALL include trend direction as "bullish" in signal metadata

### Requirement 4

**User Story:** As a trader, I want volume requirements to be realistic, so that valid signals are not filtered out due to overly strict volume thresholds

#### Acceptance Criteria

1. WHEN evaluating a potential signal, THE Signal Detector SHALL require volume to be at least 0.8 times the volume moving average
2. WHEN volume is below 0.8 times the volume moving average, THE Signal Detector SHALL reject the signal
3. WHEN volume meets the threshold, THE Signal Detector SHALL include volume ratio in signal metadata
4. THE Signal Detector SHALL NOT require volume spikes above 1.3 times average for trend-following signals
5. WHERE a trend reversal signal is detected, THE Signal Detector SHALL require volume to be at least 1.2 times the volume moving average

### Requirement 5

**User Story:** As a trader, I want the scanner to check for signals more frequently, so that I don't miss time-sensitive trading opportunities

#### Acceptance Criteria

1. WHEN scanning the 4h timeframe, THE Scanner SHALL check for new signals every 300 seconds
2. WHEN scanning the 1d timeframe, THE Scanner SHALL check for new signals every 3600 seconds
3. WHEN a timeframe check interval elapses, THE Scanner SHALL fetch latest market data and recalculate all indicators
4. THE Scanner SHALL NOT skip signal detection checks based on arbitrary time windows
5. WHEN a signal is detected, THE Scanner SHALL log the detection time and timeframe to the system log

### Requirement 6

**User Story:** As a trader, I want duplicate signal prevention to be balanced, so that legitimate new signals are not blocked while avoiding spam

#### Acceptance Criteria

1. WHEN a signal is generated, THE System SHALL check for duplicate signals within the previous 120 minutes
2. WHEN comparing signals for duplication, THE System SHALL consider signals duplicate if they have the same signal type AND entry price within 0.3 percent
3. WHEN a duplicate signal is detected, THE System SHALL log the duplicate detection and skip sending the alert
4. WHEN a signal is not duplicate, THE System SHALL add it to the recent signals history
5. THE System SHALL remove signals from the duplicate check history after 240 minutes

### Requirement 7

**User Story:** As a trader, I want clear diagnostic logging, so that I can understand why signals are or are not being generated

#### Acceptance Criteria

1. WHEN the Scanner evaluates market conditions, THE System SHALL log the current trend alignment status
2. WHEN a signal condition is not met, THE System SHALL log which specific condition failed
3. WHEN a signal is generated, THE System SHALL log all indicator values that contributed to the signal
4. WHEN a signal is blocked as duplicate, THE System SHALL log the previous signal details
5. THE System SHALL log indicator calculation completion for each timeframe with value ranges
