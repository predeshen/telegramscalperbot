# Requirements Document

## Introduction

The trading scanner system is currently failing to detect valid trading signals despite clear market setups being present. Analysis of Excel output files shows that scanners are running (421+ scans for BTC, 92 for XAUUSD scalp, etc.) but detecting 0 signals, even when bearish/bullish setups are clearly present (e.g., price below all EMAs with bearish alignment and RSI in oversold/overbought zones). The root cause appears to be NaN (Not a Number) values in calculated indicators, which causes the signal detection logic to fail.

## Glossary

- **Scanner System**: The automated trading signal detection system that monitors multiple assets (BTC, XAUUSD, US30) across multiple timeframes
- **Signal Detector**: Component responsible for identifying trading opportunities based on technical indicators
- **Indicator Calculator**: Component that calculates technical indicators (EMA, RSI, ATR, VWAP, etc.)
- **Market Data Client**: Component that fetches candlestick data from exchanges
- **YFinance Client**: Component that fetches candlestick data from Yahoo Finance for assets like Gold
- **Candle Buffer**: In-memory storage of recent candlestick data (currently set to 200 candles)
- **NaN Values**: "Not a Number" values that indicate missing or invalid data in calculations
- **EMA**: Exponential Moving Average - a trend-following indicator
- **RSI**: Relative Strength Index - a momentum oscillator
- **ATR**: Average True Range - a volatility indicator
- **VWAP**: Volume Weighted Average Price - a trading benchmark

## Requirements

### Requirement 1

**User Story:** As a trader, I want the scanner to detect valid trading signals when clear market setups are present, so that I don't miss profitable trading opportunities

#### Acceptance Criteria

1. WHEN THE Scanner System processes candlestick data with sufficient history, THE Indicator Calculator SHALL produce valid numeric values for all technical indicators without NaN values
2. WHEN price is below all EMAs with bearish alignment and RSI indicates oversold conditions, THE Signal Detector SHALL identify and report a SHORT signal opportunity
3. WHEN price is above all EMAs with bullish alignment and RSI indicates overbought conditions, THE Signal Detector SHALL identify and report a LONG signal opportunity
4. WHEN THE Scanner System completes a scan cycle, THE Excel Reporter SHALL log indicator values that are numeric and not NaN
5. WHERE indicator calculation requires minimum data points, THE Indicator Calculator SHALL verify sufficient data exists before attempting calculation

### Requirement 2

**User Story:** As a system administrator, I want to understand why indicators are returning NaN values, so that I can fix the root cause of signal detection failures

#### Acceptance Criteria

1. WHEN THE Indicator Calculator receives insufficient candlestick data, THE Indicator Calculator SHALL log a warning message indicating the specific indicator and required data points
2. WHEN THE Market Data Client fetches candles, THE Market Data Client SHALL verify that the returned DataFrame contains all required columns (open, high, low, close, volume, timestamp)
3. IF THE Market Data Client receives empty or invalid data from the exchange, THEN THE Market Data Client SHALL log an error and attempt reconnection
4. WHEN THE Scanner System initializes, THE Scanner System SHALL fetch sufficient historical candles to support all indicator calculations (minimum 200 candles for EMA-200)
5. WHEN indicator calculation fails, THE Indicator Calculator SHALL return a default value or raise an exception rather than silently producing NaN values

### Requirement 3

**User Story:** As a trader, I want the scanner to use an appropriate amount of historical data for each timeframe, so that signals are based on statistically significant patterns

#### Acceptance Criteria

1. WHERE THE Scanner System operates on swing trading timeframes (15m, 1h, 4h, 1d), THE Market Data Client SHALL fetch at least 500 candles to ensure sufficient data for long-period indicators
2. WHERE THE Scanner System operates on scalping timeframes (1m, 5m), THE Market Data Client SHALL fetch at least 200 candles to balance data sufficiency with API rate limits
3. WHEN THE YFinance Client calculates the period parameter, THE YFinance Client SHALL ensure the period covers enough time to retrieve the requested number of candles
4. WHEN THE Market Data Client updates candle buffers, THE Market Data Client SHALL maintain the configured buffer size without data loss
5. IF THE Market Data Client cannot fetch the requested number of candles, THEN THE Market Data Client SHALL log a warning and proceed with available data

### Requirement 4

**User Story:** As a trader, I want the signal detection logic to properly evaluate all indicator conditions, so that valid setups are not missed due to logic errors

#### Acceptance Criteria

1. WHEN THE Signal Detector evaluates a potential signal, THE Signal Detector SHALL verify that all required indicators have valid numeric values before applying signal rules
2. WHEN THE Signal Detector identifies a bearish setup (price below EMAs, EMA 9 < EMA 21, RSI < 50), THE Signal Detector SHALL generate a SHORT signal with appropriate entry, stop loss, and take profit levels
3. WHEN THE Signal Detector identifies a bullish setup (price above EMAs, EMA 9 > EMA 21, RSI > 50), THE Signal Detector SHALL generate a LONG signal with appropriate entry, stop loss, and take profit levels
4. WHEN THE Signal Detector processes multiple timeframes, THE Signal Detector SHALL apply timeframe-appropriate signal rules (stricter for swing, more lenient for scalp)
5. WHERE THE Signal Detector uses volume confirmation, THE Signal Detector SHALL verify volume_ma is valid before comparing current volume

### Requirement 5

**User Story:** As a system administrator, I want comprehensive logging of the signal detection process, so that I can diagnose why signals are or are not being generated

#### Acceptance Criteria

1. WHEN THE Scanner System completes a scan cycle, THE Scanner System SHALL log the current price, all indicator values, and whether a signal was detected
2. WHEN THE Signal Detector evaluates signal conditions, THE Signal Detector SHALL log which conditions passed and which failed
3. WHEN THE Indicator Calculator produces NaN values, THE Indicator Calculator SHALL log the specific indicator, input data shape, and reason for failure
4. WHEN THE Excel Reporter logs scan results, THE Excel Reporter SHALL include all indicator values to enable post-analysis
5. WHERE debugging is enabled, THE Signal Detector SHALL log detailed information about EMA alignments, RSI levels, volume ratios, and trend direction

### Requirement 6

**User Story:** As a system administrator, I want the scanner to run as a systemd service with WebSocket connections, so that it remains stable and receives real-time data efficiently

#### Acceptance Criteria

1. WHEN THE Scanner System is deployed on a Linux server, THE Scanner System SHALL be configured as a systemd service with automatic restart on failure
2. WHERE THE Market Data Client connects to Kraken exchange, THE Market Data Client SHALL use WebSocket connections for real-time data streaming instead of REST API polling
3. WHEN THE WebSocket connection is established, THE Market Data Client SHALL subscribe to candlestick updates for all configured timeframes
4. IF THE WebSocket connection drops, THEN THE Market Data Client SHALL automatically reconnect with exponential backoff
5. WHEN THE Scanner System runs as a service, THE Scanner System SHALL handle SIGTERM and SIGINT signals gracefully to ensure clean shutdown
6. WHEN THE systemd service starts, THE systemd service SHALL wait for network connectivity before attempting exchange connections
7. WHERE THE Scanner System encounters fatal errors, THE systemd service SHALL restart the scanner automatically after a configured delay
