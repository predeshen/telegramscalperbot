# Requirements Document

## Introduction

This document outlines the requirements for implementing the H4 HVG (4-Hour High Volume Gap) trading strategy across all six existing scanners (BTC Scalp, BTC Swing, Gold Scalp, Gold Swing, US30 Scalp, US30 Swing). The H4 HVG strategy identifies high-probability trading opportunities by detecting significant price gaps on the 4-hour timeframe that are accompanied by volume spikes, indicating institutional interest and potential continuation or reversal patterns.

## Glossary

- **Scanner**: A trading system that monitors market data and generates trading signals based on technical analysis
- **H4**: 4-hour timeframe candlestick chart
- **HVG (High Volume Gap)**: A price gap between consecutive candles accompanied by volume significantly above average
- **Gap**: The difference between the close price of one candle and the open price of the next candle
- **Volume Spike**: Trading volume that exceeds the moving average by a specified threshold
- **Fair Value Gap (FVG)**: A three-candle pattern where the middle candle creates a gap that price may return to fill
- **Imbalance**: An area on the chart where price moved quickly with minimal trading, creating inefficiency
- **Signal Detector**: Component responsible for identifying trading opportunities based on strategy rules
- **Confluence**: Multiple technical factors aligning to support a trading decision
- **ATR (Average True Range)**: Volatility indicator used for stop-loss and take-profit calculations

## Requirements

### Requirement 1

**User Story:** As a trader, I want the Scanner to detect H4 HVG patterns on the 4-hour timeframe, so that I can identify high-probability trading opportunities based on institutional volume and price gaps.

#### Acceptance Criteria

1. WHEN THE Scanner processes 4-hour candlestick data, THE Scanner SHALL calculate the gap size between consecutive candles as the absolute difference between the previous candle close and current candle open
2. WHEN THE Scanner identifies a gap, THE Scanner SHALL verify that the current candle volume exceeds the 20-period volume moving average by at least 1.5x
3. WHEN THE Scanner detects both a gap and volume spike, THE Scanner SHALL classify the gap direction as bullish (gap up) or bearish (gap down)
4. WHEN THE Scanner validates an H4 HVG pattern, THE Scanner SHALL calculate the gap size as a percentage of the previous candle close price
5. WHERE the gap size percentage is less than 0.1%, THE Scanner SHALL reject the pattern as insignificant

### Requirement 2

**User Story:** As a trader, I want the Scanner to generate LONG signals for bullish H4 HVG patterns with proper entry, stop-loss, and take-profit levels, so that I can execute trades with defined risk management.

#### Acceptance Criteria

1. WHEN THE Scanner detects a bullish H4 HVG pattern, THE Scanner SHALL generate a LONG signal with signal_type set to "LONG"
2. WHEN THE Scanner creates a LONG signal, THE Scanner SHALL set the entry price to the current candle close price
3. WHEN THE Scanner calculates stop-loss for a LONG signal, THE Scanner SHALL place the stop-loss at the gap low minus 1.5 times the ATR value
4. WHEN THE Scanner calculates take-profit for a LONG signal, THE Scanner SHALL set the initial target at the entry price plus 2.0 times the gap size
5. WHEN THE Scanner validates a LONG signal, THE Scanner SHALL verify that the risk-reward ratio is at least 1.5:1 before generating the signal

### Requirement 3

**User Story:** As a trader, I want the Scanner to generate SHORT signals for bearish H4 HVG patterns with proper entry, stop-loss, and take-profit levels, so that I can execute short trades with defined risk management.

#### Acceptance Criteria

1. WHEN THE Scanner detects a bearish H4 HVG pattern, THE Scanner SHALL generate a SHORT signal with signal_type set to "SHORT"
2. WHEN THE Scanner creates a SHORT signal, THE Scanner SHALL set the entry price to the current candle close price
3. WHEN THE Scanner calculates stop-loss for a SHORT signal, THE Scanner SHALL place the stop-loss at the gap high plus 1.5 times the ATR value
4. WHEN THE Scanner calculates take-profit for a SHORT signal, THE Scanner SHALL set the initial target at the entry price minus 2.0 times the gap size
5. WHEN THE Scanner validates a SHORT signal, THE Scanner SHALL verify that the risk-reward ratio is at least 1.5:1 before generating the signal

### Requirement 4

**User Story:** As a trader, I want the Scanner to apply confluence filters to H4 HVG signals, so that only high-quality setups with multiple confirming factors are generated.

#### Acceptance Criteria

1. WHEN THE Scanner evaluates a bullish H4 HVG pattern, THE Scanner SHALL verify that the current price is above the 50-period EMA on the 4-hour timeframe
2. WHEN THE Scanner evaluates a bearish H4 HVG pattern, THE Scanner SHALL verify that the current price is below the 50-period EMA on the 4-hour timeframe
3. WHEN THE Scanner validates an H4 HVG signal, THE Scanner SHALL confirm that the RSI value is between 30 and 70 to avoid overextended conditions
4. WHEN THE Scanner detects an H4 HVG pattern, THE Scanner SHALL verify that the gap occurred within the last 3 candles to ensure relevance
5. WHEN THE Scanner calculates confidence score, THE Scanner SHALL assign a value between 3 and 5 based on the number of confluence factors met

### Requirement 5

**User Story:** As a trader, I want the Scanner to prevent duplicate H4 HVG signals, so that I am not alerted multiple times for the same trading opportunity.

#### Acceptance Criteria

1. WHEN THE Scanner generates an H4 HVG signal, THE Scanner SHALL record the signal timestamp, price, and direction in the signal history
2. WHEN THE Scanner evaluates a new H4 HVG pattern, THE Scanner SHALL check if a similar signal was generated within the last 240 minutes (4 hours)
3. WHEN THE Scanner compares signals, THE Scanner SHALL calculate the price difference as a percentage of the previous signal entry price
4. WHEN THE price difference is less than 0.5%, THE Scanner SHALL reject the new signal as a duplicate
5. WHEN THE Scanner maintains signal history, THE Scanner SHALL remove signals older than 24 hours to prevent memory growth

### Requirement 6

**User Story:** As a trader, I want the Scanner to integrate H4 HVG detection into all six existing scanners, so that the strategy is available across all trading instruments and timeframes.

#### Acceptance Criteria

1. WHEN THE Scanner initializes, THE Scanner SHALL include "4h" in the list of monitored timeframes if not already present
2. WHEN THE Scanner processes market data, THE Scanner SHALL invoke H4 HVG detection for the 4-hour timeframe data
3. WHEN THE Scanner detects an H4 HVG signal, THE Scanner SHALL set the strategy field to "H4 HVG" in the Signal object
4. WHEN THE Scanner generates an H4 HVG alert, THE Scanner SHALL include the gap size, volume ratio, and confluence factors in the alert message
5. WHEN THE Scanner logs scan results to Excel, THE Scanner SHALL record H4 HVG-specific metrics including gap_size_percent and volume_spike_ratio

### Requirement 7

**User Story:** As a trader, I want the Scanner to provide detailed reasoning for H4 HVG signals, so that I can understand why the signal was generated and make informed trading decisions.

#### Acceptance Criteria

1. WHEN THE Scanner generates an H4 HVG signal, THE Scanner SHALL create a reasoning string that explains the pattern detection
2. WHEN THE Scanner builds the reasoning, THE Scanner SHALL include the gap size in both absolute price and percentage terms
3. WHEN THE Scanner documents the signal, THE Scanner SHALL describe the volume spike magnitude relative to the moving average
4. WHEN THE Scanner explains confluence, THE Scanner SHALL list all technical factors that support the signal direction
5. WHEN THE Scanner formats the reasoning, THE Scanner SHALL structure the text with clear sections for pattern, volume, trend, and entry logic

### Requirement 8

**User Story:** As a trader, I want the Scanner to handle H4 HVG signals consistently across different market instruments (BTC, Gold, US30), so that the strategy adapts to each market's characteristics.

#### Acceptance Criteria

1. WHEN THE Scanner operates on BTC markets, THE Scanner SHALL use a minimum gap size threshold of 0.15% of price
2. WHEN THE Scanner operates on Gold markets, THE Scanner SHALL use a minimum gap size threshold of 0.10% of price
3. WHEN THE Scanner operates on US30 markets, THE Scanner SHALL use a minimum gap size threshold of 0.08% of price
4. WHEN THE Scanner calculates stop-loss distances, THE Scanner SHALL use the instrument-specific ATR multiplier from the configuration
5. WHEN THE Scanner generates signals, THE Scanner SHALL include the symbol field (BTC/USD, XAU/USD, US30) in the Signal object
