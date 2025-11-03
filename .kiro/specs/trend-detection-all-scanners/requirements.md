# Requirements Document

## Introduction

All swing trading scanners (BTC, US30, and XAUUSD) currently miss simple uptrends and downtrends. The XAUUSD scanner uses three specific strategies (Asian Range Breakout, EMA Cloud Breakout, and Mean Reversion), while BTC and US30 scanners use basic signal detection. This feature will add a **Trend Following** strategy to all scanners to capture sustained directional moves, and ensure all scan data is properly logged to Excel reports.

## Glossary

- **Scanner**: Trading scanners that monitor BTC, US30, and XAUUSD price movements
- **Trend Following Strategy**: A trading strategy that identifies and follows sustained directional price movements
- **EMA (Exponential Moving Average)**: A technical indicator that gives more weight to recent prices
- **Higher Highs/Higher Lows**: Price pattern where each peak and trough is higher than the previous one (uptrend)
- **Lower Highs/Lower Lows**: Price pattern where each peak and trough is lower than the previous one (downtrend)
- **ATR (Average True Range)**: A volatility indicator used for stop-loss and take-profit calculations
- **Signal Detector**: The component responsible for identifying trading opportunities
- **GoldSignalDetector**: The class that implements signal detection logic for XAUUSD
- **ExcelReporter**: The component that logs scan results and sends email reports
- **Scan Data**: All market data, indicators, and signal information collected during each scan cycle

## Requirements

### Requirement 1: Trend Detection for All Scanners

**User Story:** As a trader, I want all scanners (BTC, US30, XAUUSD) to detect sustained uptrends and downtrends, so that I can capture trending moves that the current strategies miss.

#### Acceptance Criteria

1. WHEN THE BTC Scanner analyzes price data, THE SignalDetector SHALL identify uptrends by detecting at least 3 consecutive higher highs and higher lows
2. WHEN THE US30 Scanner analyzes price data, THE SignalDetector SHALL identify uptrends by detecting at least 3 consecutive higher highs and higher lows
3. WHEN THE XAUUSD Scanner analyzes price data, THE GoldSignalDetector SHALL identify uptrends by detecting at least 3 consecutive higher highs and higher lows
4. WHEN any Scanner analyzes price data, THE SignalDetector SHALL identify downtrends by detecting at least 3 consecutive lower highs and lower lows
5. WHEN an uptrend is detected, THE SignalDetector SHALL verify that price is above EMA(50) and EMA(50) is rising
6. WHEN a downtrend is detected, THE SignalDetector SHALL verify that price is below EMA(50) and EMA(50) is falling
7. WHEN a trend is confirmed, THE SignalDetector SHALL check that RSI is between 40-80 for uptrends or 20-60 for downtrends

### Requirement 2: Trend Entry Signals for All Scanners

**User Story:** As a trader, I want all scanners to identify optimal entry points within established trends, so that I can enter trades with favorable risk-reward ratios.

#### Acceptance Criteria

1. WHEN an uptrend is established, THE SignalDetector SHALL generate a LONG signal when price pulls back to EMA(21) and bounces
2. WHEN a downtrend is established, THE SignalDetector SHALL generate a SHORT signal when price rallies to EMA(21) and rejects
3. WHEN generating a trend-following signal, THE SignalDetector SHALL require volume to be at least 1.2x the volume moving average
4. WHEN a pullback entry is detected, THE SignalDetector SHALL verify that the pullback is less than 50% of the previous trend leg
5. WHEN price action confirms the entry, THE SignalDetector SHALL set stop-loss at 1.5x ATR from entry price

### Requirement 3: Risk Management for Trend Signals

**User Story:** As a trader, I want trend-following signals to have appropriate stop-loss and take-profit levels, so that I can manage risk effectively.

#### Acceptance Criteria

1. WHEN a LONG trend signal is generated, THE SignalDetector SHALL place stop-loss at entry minus 1.5x ATR
2. WHEN a SHORT trend signal is generated, THE SignalDetector SHALL place stop-loss at entry plus 1.5x ATR
3. WHEN calculating take-profit, THE SignalDetector SHALL target 2.5x ATR from entry for a minimum 1.67:1 risk-reward ratio
4. WHEN the trend is strong (RSI > 60 for longs, RSI < 40 for shorts), THE SignalDetector SHALL extend take-profit to 3.0x ATR
5. WHEN stop-loss or take-profit levels are calculated, THE SignalDetector SHALL ensure they respect key support/resistance levels

### Requirement 4: Strategy Integration for All Scanners

**User Story:** As a system administrator, I want the trend-following strategy to integrate seamlessly with existing strategies, so that all scanners operate cohesively.

#### Acceptance Criteria

1. WHEN THE XAUUSD StrategySelector evaluates market conditions, THE StrategySelector SHALL add TREND_FOLLOWING as a fourth strategy option
2. WHEN THE BTC SignalDetector evaluates market conditions, THE SignalDetector SHALL add trend-following detection capability
3. WHEN THE US30 SignalDetector evaluates market conditions, THE SignalDetector SHALL add trend-following detection capability
4. WHEN multiple strategies are applicable in XAUUSD, THE StrategySelector SHALL prioritize TREND_FOLLOWING during strong trending markets
5. WHEN THE GoldSignalDetector detects signals, THE GoldSignalDetector SHALL route trend-following detection to a new method _detect_trend_following
6. WHEN THE SignalDetector detects signals for BTC/US30, THE SignalDetector SHALL route trend-following detection to a new method _detect_trend_following
7. WHEN a trend-following signal is generated, THE SignalDetector SHALL include strategy name "Trend Following" in the signal metadata
8. WHEN logging signals, THE Scanner SHALL record trend-following signals with the same format as existing strategies

### Requirement 5: Signal Quality and Filtering

**User Story:** As a trader, I want trend-following signals to be high quality and avoid false signals, so that I can trade with confidence.

#### Acceptance Criteria

1. WHEN evaluating a potential trend signal, THE SignalDetector SHALL reject signals if the trend has fewer than 3 swing points
2. WHEN price is consolidating (ATR declining for 3+ periods), THE SignalDetector SHALL not generate trend-following signals
3. WHEN a pullback exceeds 61.8% of the previous trend leg, THE SignalDetector SHALL wait for trend re-establishment
4. WHEN volume is declining during the trend, THE SignalDetector SHALL reduce signal confidence or skip the signal
5. WHEN a trend-following signal is generated, THE SignalDetector SHALL apply duplicate detection with a 60-minute window

### Requirement 6: Trend Context and Reasoning

**User Story:** As a trader, I want detailed reasoning for trend-following signals, so that I can understand why the signal was generated.

#### Acceptance Criteria

1. WHEN a trend-following signal is created, THE SignalDetector SHALL include the number of higher highs/lows in the reasoning
2. WHEN generating signal reasoning, THE SignalDetector SHALL describe the pullback depth and EMA bounce confirmation
3. WHEN volume confirms the trend, THE SignalDetector SHALL include volume ratio in the reasoning
4. WHEN RSI supports the trend, THE SignalDetector SHALL include RSI level and momentum description
5. WHEN key levels align with the trend, THE SignalDetector SHALL include support/resistance context in the reasoning

### Requirement 7: Complete Excel Data Logging

**User Story:** As a trader and analyst, I want all scan data to be logged to Excel files with complete information, so that I can review historical scans and analyze scanner performance.

#### Acceptance Criteria

1. WHEN THE ExcelReporter logs a scan result, THE ExcelReporter SHALL record timestamp, scanner name, symbol, timeframe, price, and volume
2. WHEN THE ExcelReporter logs indicator data, THE ExcelReporter SHALL record all calculated indicators (EMA 9/21/50/100/200, RSI, ATR, VWAP, Volume MA)
3. WHEN THE ExcelReporter logs a signal, THE ExcelReporter SHALL record signal type (LONG/SHORT), entry price, stop loss, take profit, and risk-reward ratio
4. WHEN THE ExcelReporter logs a signal, THE ExcelReporter SHALL record strategy name, confidence level, and market bias
5. WHEN THE ExcelReporter logs XAUUSD signals, THE ExcelReporter SHALL record session information (Asian/London/NY) and spread data
6. WHEN THE ExcelReporter logs trend-following signals, THE ExcelReporter SHALL record trend strength (number of swing points) and pullback depth
7. WHEN THE ExcelReporter creates Excel files, THE ExcelReporter SHALL use proper column headers and formatting for all data fields
8. WHEN THE ExcelReporter sends email reports, THE ExcelReporter SHALL include summary statistics (total scans, signals detected, signal types)

### Requirement 8: Excel File Structure and Completeness

**User Story:** As a data analyst, I want Excel files to have a consistent structure with all relevant columns, so that I can easily analyze scanner data.

#### Acceptance Criteria

1. WHEN THE ExcelReporter creates an Excel file, THE ExcelReporter SHALL include columns: Timestamp, Scanner, Symbol, Timeframe, Price, Volume
2. WHEN THE ExcelReporter creates an Excel file, THE ExcelReporter SHALL include indicator columns: EMA_9, EMA_21, EMA_50, EMA_100, EMA_200, RSI, ATR, VWAP, Volume_MA
3. WHEN THE ExcelReporter creates an Excel file, THE ExcelReporter SHALL include signal columns: Signal_Detected, Signal_Type, Entry_Price, Stop_Loss, Take_Profit, Risk_Reward
4. WHEN THE ExcelReporter creates an Excel file, THE ExcelReporter SHALL include strategy columns: Strategy_Name, Confidence, Market_Bias, Reasoning
5. WHEN THE ExcelReporter creates an Excel file for XAUUSD, THE ExcelReporter SHALL include session columns: Session, Spread_Pips, Asian_Range_High, Asian_Range_Low
6. WHEN THE ExcelReporter creates an Excel file for trend signals, THE ExcelReporter SHALL include trend columns: Trend_Direction, Swing_Points, Pullback_Depth_Percent
7. WHEN THE ExcelReporter writes data, THE ExcelReporter SHALL handle missing values by writing "N/A" or null appropriately
8. WHEN THE ExcelReporter writes numeric data, THE ExcelReporter SHALL format prices with 2 decimal places and percentages with 1 decimal place
