# Requirements Document

## Introduction

The BTC Scalping Scanner is an automated trading signal detection system that monitors BTC/USD price movements in real-time, identifies high-probability scalping opportunities using technical analysis and order flow principles, and delivers actionable trade alerts via email. The system runs continuously on a Linux VM and applies multiple confluence-based strategies to filter noise and maximize signal quality.

## Glossary

- **Scanner**: The automated system that monitors BTC/USD market data and generates trade signals
- **Signal**: A trade opportunity identified by the Scanner that meets all confluence criteria
- **VWAP**: Volume Weighted Average Price - a trading benchmark representing the average price weighted by volume
- **EMA**: Exponential Moving Average - a trend-following indicator that gives more weight to recent prices
- **ATR**: Average True Range - a volatility indicator measuring the average price movement range
- **RSI**: Relative Strength Index - a momentum oscillator measuring overbought/oversold conditions
- **Order Flow**: Real-time analysis of buy/sell volume and market depth to identify institutional activity
- **Confluence**: The alignment of multiple independent technical signals confirming the same trade direction
- **Scalping**: A trading strategy targeting small, quick profits from minor price movements
- **Session VWAP**: VWAP calculated from the start of the current trading session
- **Liquidity Zone**: Price levels where significant buy or sell orders are concentrated

## Requirements

### Requirement 1

**User Story:** As a scalp trader, I want the Scanner to monitor BTC/USD price data in real-time on 1-minute and 5-minute timeframes, so that I can capture fast-moving scalping opportunities.

#### Acceptance Criteria

1. WHEN the Scanner starts, THE Scanner SHALL connect to a cryptocurrency exchange API and subscribe to BTC/USD price data streams
2. THE Scanner SHALL process incoming 1-minute and 5-minute candlestick data with a maximum latency of 2 seconds from exchange timestamp
3. THE Scanner SHALL maintain a rolling buffer of at least 200 candlesticks per timeframe to support indicator calculations
4. IF the exchange connection fails, THEN THE Scanner SHALL attempt reconnection with exponential backoff up to 5 attempts
5. THE Scanner SHALL log all connection events and data processing timestamps for performance monitoring

### Requirement 2

**User Story:** As a scalp trader, I want the Scanner to calculate technical indicators (EMA, VWAP, ATR, RSI, Volume) accurately, so that signal detection is based on reliable data.

#### Acceptance Criteria

1. THE Scanner SHALL calculate EMA(9), EMA(21), EMA(50), EMA(100), and EMA(200) for each timeframe using standard exponential smoothing formulas
2. THE Scanner SHALL calculate session VWAP from the start of each UTC day using cumulative price-volume data
3. THE Scanner SHALL calculate ATR(14) using the true range formula over the previous 14 periods
4. THE Scanner SHALL calculate RSI(6) and RSI(8) using the standard Wilder smoothing method
5. THE Scanner SHALL calculate volume moving average over 20 periods for volume spike detection

### Requirement 3

**User Story:** As a scalp trader, I want the Scanner to detect bullish long signals using confluence of trend, momentum, and volume, so that I receive high-probability buy opportunities.

#### Acceptance Criteria

1. WHEN price is above session VWAP AND EMA(9) crosses above EMA(21), THE Scanner SHALL mark a potential bullish signal
2. WHEN a potential bullish signal occurs AND current candle volume exceeds 1.5 times the 20-period volume average, THE Scanner SHALL confirm bullish momentum
3. WHEN bullish momentum is confirmed AND RSI(6) is between 30 and 70, THE Scanner SHALL validate the signal as not overbought
4. WHEN price is above EMA(50) on the higher timeframe, THE Scanner SHALL classify the market bias as bullish
5. WHEN all bullish confluence criteria are met, THE Scanner SHALL generate a LONG signal with entry price, stop-loss at entry minus 1.5×ATR, and take-profit at entry plus 1.0×ATR

### Requirement 4

**User Story:** As a scalp trader, I want the Scanner to detect bearish short signals using confluence of trend, momentum, and volume, so that I receive high-probability sell opportunities.

#### Acceptance Criteria

1. WHEN price is below session VWAP AND EMA(9) crosses below EMA(21), THE Scanner SHALL mark a potential bearish signal
2. WHEN a potential bearish signal occurs AND current candle volume exceeds 1.5 times the 20-period volume average, THE Scanner SHALL confirm bearish momentum
3. WHEN bearish momentum is confirmed AND RSI(6) is between 30 and 70, THE Scanner SHALL validate the signal as not oversold
4. WHEN price is below EMA(50) on the higher timeframe, THE Scanner SHALL classify the market bias as bearish
5. WHEN all bearish confluence criteria are met, THE Scanner SHALL generate a SHORT signal with entry price, stop-loss at entry plus 1.5×ATR, and take-profit at entry minus 1.0×ATR

### Requirement 5

**User Story:** As a scalp trader, I want to receive email alerts immediately when signals are detected, so that I can act on opportunities without constantly monitoring charts.

#### Acceptance Criteria

1. WHEN the Scanner generates a signal, THE Scanner SHALL compose an email containing signal type, entry price, stop-loss, take-profit, timeframe, and timestamp
2. THE Scanner SHALL send the email via SMTP to the configured recipient address within 3 seconds of signal generation
3. THE Scanner SHALL connect to the SMTP server using SSL on port 465 with the configured credentials
4. IF email delivery fails, THEN THE Scanner SHALL retry up to 3 times with 5-second intervals between attempts
5. THE Scanner SHALL log all email delivery attempts and outcomes for audit purposes

### Requirement 6

**User Story:** As a scalp trader, I want the Scanner to avoid sending duplicate signals for the same setup, so that I don't receive redundant alerts.

#### Acceptance Criteria

1. WHEN the Scanner generates a signal, THE Scanner SHALL record the signal timestamp, type, and price level
2. THE Scanner SHALL NOT generate a new signal of the same type within 5 minutes of the previous signal
3. WHEN price moves more than 0.3% from the previous signal entry price, THE Scanner SHALL allow new signals of the same type
4. THE Scanner SHALL maintain a signal history buffer of the last 50 signals for duplicate detection
5. THE Scanner SHALL clear expired signals older than 30 minutes from the duplicate detection buffer

### Requirement 7

**User Story:** As a system administrator, I want the Scanner to run reliably as a Linux service with proper logging and error handling, so that it operates continuously without manual intervention.

#### Acceptance Criteria

1. THE Scanner SHALL run as a background process on Linux with automatic restart on failure
2. THE Scanner SHALL write structured logs to a rotating log file with daily rotation and 7-day retention
3. WHEN a critical error occurs, THE Scanner SHALL log the error details and send an alert email to the administrator
4. THE Scanner SHALL expose health check metrics including uptime, signal count, and last data update timestamp
5. THE Scanner SHALL load configuration from a JSON or YAML file at startup including SMTP settings and trading parameters

### Requirement 8

**User Story:** As a scalp trader, I want the Scanner to include risk management parameters in alerts, so that I can size positions appropriately and manage risk.

#### Acceptance Criteria

1. THE Scanner SHALL calculate risk-reward ratio as the ratio of (take-profit minus entry) to (entry minus stop-loss)
2. THE Scanner SHALL include the calculated ATR value in the email alert for volatility context
3. THE Scanner SHALL include the current market bias (bullish/bearish/neutral) based on higher timeframe EMA positioning
4. THE Scanner SHALL calculate the stop-loss distance as a percentage of entry price
5. THE Scanner SHALL include a confidence score based on the number of confluence factors met (3-5 factors)
