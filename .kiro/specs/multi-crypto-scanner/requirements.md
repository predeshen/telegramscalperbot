# Requirements Document

## Introduction

This feature extends the existing BTC signal scanner to support multiple high-volatility cryptocurrency symbols including ETHUSD and other profitable crypto assets, as well as major FX currency pairs. The system will maintain the existing BTC scanner functionality while adding parallel scanners for additional symbols, each with optimized signal detection parameters based on the asset's characteristics and market type (crypto vs FX).

## Glossary

- **Scanner**: The signal detection system that monitors market data and generates trading alerts
- **Symbol**: A tradable cryptocurrency pair (e.g., BTC-USD, ETH-USD)
- **Timeframe**: The candlestick interval being monitored (e.g., 1m, 5m, 15m, 1h, 4h, 1d)
- **Signal**: A trading opportunity detected by the scanner based on technical indicators
- **YFinanceClient**: The market data client that fetches cryptocurrency price data from Yahoo Finance
- **Volatility**: The degree of price variation over time, measured by ATR and price movement
- **Confluence**: Multiple technical indicators aligning to confirm a signal
- **FX Pair**: A foreign exchange currency pair (e.g., EUR/USD, GBP/USD)
- **Trading Session**: Time-based market activity periods (Asian, London, New York) relevant for FX trading

## Requirements

### Requirement 1

**User Story:** As a trader, I want to scan ETHUSD in addition to BTCUSD, so that I can capture trading opportunities across multiple major cryptocurrencies

#### Acceptance Criteria

1. WHEN the Scanner starts, THE Scanner SHALL fetch market data for ETH-USD from Yahoo Finance
2. THE Scanner SHALL calculate technical indicators for ETH-USD using the same indicator set as BTC-USD
3. THE Scanner SHALL detect signals for ETH-USD using asset-specific parameters
4. WHEN a signal is detected for ETH-USD, THE Scanner SHALL send alerts via Telegram with the symbol clearly identified
5. THE Scanner SHALL maintain separate Excel reporting for ETH-USD signals

### Requirement 2

**User Story:** As a trader, I want the scanner to support additional high-volatility cryptocurrencies beyond BTC and ETH, so that I can maximize profit opportunities across the crypto market

#### Acceptance Criteria

1. THE Scanner SHALL support the following additional cryptocurrency symbols: SOL-USD, AVAX-USD, MATIC-USD, LINK-USD
2. WHEN adding a new symbol, THE Scanner SHALL validate that the symbol is available on Yahoo Finance
3. THE Scanner SHALL allow enabling or disabling individual symbols via configuration
4. THE Scanner SHALL process all enabled symbols in parallel without blocking
5. WHEN multiple symbols generate signals simultaneously, THE Scanner SHALL send separate alerts for each symbol

### Requirement 3

**User Story:** As a trader, I want each cryptocurrency to have optimized signal detection parameters, so that signals are tailored to each asset's unique volatility and trading characteristics

#### Acceptance Criteria

1. THE Scanner SHALL maintain asset-specific configuration for volume thresholds, RSI ranges, and ATR multipliers
2. WHEN detecting signals for ETH-USD, THE Scanner SHALL use ETH-specific volume spike thresholds
3. WHEN detecting signals for high-volatility altcoins, THE Scanner SHALL use adjusted stop-loss and take-profit multipliers
4. THE Scanner SHALL allow configuration of minimum confidence scores per asset
5. THE Scanner SHALL log which asset-specific parameters were used for each signal

### Requirement 4

**User Story:** As a trader, I want to run separate scanner instances for scalping and swing trading across multiple cryptocurrencies, so that I can capture both short-term and long-term opportunities

#### Acceptance Criteria

1. THE Scanner SHALL support running multiple instances with different timeframe configurations
2. WHEN running a scalp scanner, THE Scanner SHALL use timeframes 1m, 5m, and 15m for all enabled symbols
3. WHEN running a swing scanner, THE Scanner SHALL use timeframes 15m, 1h, 4h, and 1d for all enabled symbols
4. THE Scanner SHALL maintain separate log files for scalp and swing scanner instances
5. THE Scanner SHALL include the scanner type (scalp/swing) in all alert messages

### Requirement 5

**User Story:** As a trader, I want the scanner to automatically identify and prioritize the most volatile and liquid cryptocurrencies, so that I focus on assets with the best profit potential

#### Acceptance Criteria

1. THE Scanner SHALL calculate 24-hour volatility (ATR percentage) for each enabled symbol
2. THE Scanner SHALL calculate average volume for each enabled symbol
3. WHEN volatility exceeds a configured threshold, THE Scanner SHALL increase signal sensitivity for that symbol
4. WHEN volume falls below a minimum threshold, THE Scanner SHALL pause signal detection for that symbol
5. THE Scanner SHALL log volatility and volume metrics in the Excel report

### Requirement 6

**User Story:** As a trader, I want clear identification of which cryptocurrency generated each signal, so that I can quickly act on opportunities without confusion

#### Acceptance Criteria

1. WHEN sending a Telegram alert, THE Scanner SHALL include the symbol name in the message title
2. WHEN logging to Excel, THE Scanner SHALL include the symbol in a dedicated column
3. WHEN multiple signals occur for the same symbol within the duplicate window, THE Scanner SHALL filter duplicates per symbol
4. THE Scanner SHALL use symbol-specific emoji indicators in alerts (₿ for BTC, Ξ for ETH, etc.)
5. THE Scanner SHALL include the current price and 24h change percentage for the symbol in alerts

### Requirement 7

**User Story:** As a trader, I want to scan major FX currency pairs in addition to cryptocurrencies, so that I can capture opportunities across both crypto and forex markets

#### Acceptance Criteria

1. THE Scanner SHALL support the following FX pairs: EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD
2. WHEN scanning FX pairs, THE Scanner SHALL use FX-specific symbol formats compatible with Yahoo Finance
3. THE Scanner SHALL apply FX-specific parameters including tighter stop-loss multipliers and session-based filtering
4. WHEN an FX pair generates a signal outside its primary trading session, THE Scanner SHALL reduce the confidence score
5. THE Scanner SHALL clearly distinguish FX signals from crypto signals in alerts and reports

### Requirement 8

**User Story:** As a trader, I want FX signals to respect trading session times, so that I avoid low-liquidity periods and focus on high-activity sessions

#### Acceptance Criteria

1. THE Scanner SHALL identify the current trading session (Asian, London, New York, or overlap)
2. WHEN scanning EUR/USD or GBP/USD, THE Scanner SHALL prioritize signals during London and New York sessions
3. WHEN scanning USD/JPY, THE Scanner SHALL prioritize signals during Asian and London sessions
4. THE Scanner SHALL include the active trading session in FX signal alerts
5. WHEN liquidity is low (outside major sessions), THE Scanner SHALL increase the minimum confluence requirement for FX pairs

### Requirement 9

**User Story:** As a trader, I want to avoid premature exit signals that trigger immediately after entry, so that my trades have time to develop and reach their profit targets

#### Acceptance Criteria

1. WHEN a trade is entered, THE Scanner SHALL wait a minimum grace period of 5 minutes before evaluating exit conditions
2. THE Scanner SHALL NOT send exit signals when current profit is negative or less than 1.0% for crypto or 0.3% for FX
3. WHEN momentum reverses but profit is minimal, THE Scanner SHALL continue monitoring the trade
4. THE Scanner SHALL only trigger exit signals when giving back more than 40% of peak profit AND peak profit exceeded 2.0%
5. WHEN a trade reaches 50% of take-profit target, THE Scanner SHALL move stop-loss to breakeven and disable momentum exit signals

### Requirement 10

**User Story:** As a trader, I want to avoid conflicting signals from different timeframes, so that I don't receive a LONG signal on 15m and a SHORT signal on 1d simultaneously

#### Acceptance Criteria

1. WHEN multiple timeframes generate conflicting signals within 5 minutes, THE Scanner SHALL only send the signal from the highest timeframe
2. THE Scanner SHALL check for active trades before generating new signals in the opposite direction
3. WHEN a LONG signal is detected on a lower timeframe AND a SHORT signal exists on a higher timeframe, THE Scanner SHALL suppress the lower timeframe signal
4. THE Scanner SHALL include a timeframe hierarchy (1d > 4h > 1h > 15m > 5m > 1m) for conflict resolution
5. THE Scanner SHALL log suppressed signals with the reason for suppression

### Requirement 11

**User Story:** As a trader, I want improved signal filtering to reduce false signals and whipsaws, so that I only receive high-quality trading opportunities

#### Acceptance Criteria

1. THE Scanner SHALL require a minimum candle confirmation period before generating signals
2. WHEN price action shows conflicting signals within a short timeframe, THE Scanner SHALL suppress both signals
3. THE Scanner SHALL increase confluence requirements during ranging or choppy market conditions
4. WHEN ADX is below 20, THE Scanner SHALL require additional confirmation factors
5. THE Scanner SHALL track signal win rate per symbol and adjust sensitivity based on recent performance

### Requirement 12

**User Story:** As a trader, I want exit signals to only trigger when I'm actually in profit and giving back significant gains, so that I don't exit losing trades prematurely

#### Acceptance Criteria

1. WHEN current P&L is negative, THE Scanner SHALL NOT send momentum reversal exit signals
2. WHEN best profit is 0.0%, THE Scanner SHALL NOT send exit signals regardless of momentum
3. THE Scanner SHALL only evaluate exit conditions when peak profit exceeds 1.5% for crypto or 0.5% for FX
4. WHEN giving back gains, THE Scanner SHALL calculate the percentage as (peak_profit - current_profit) / peak_profit
5. THE Scanner SHALL NOT send duplicate exit signals within 10 minutes for the same trade

### Requirement 13

**User Story:** As a trader, I want the scanner to detect Fair Value Gaps (FVG) and liquidity voids on higher timeframes, so that I can identify institutional supply/demand zones for high-probability reversal trades

#### Acceptance Criteria

1. THE Scanner SHALL detect inverse FVGs on daily and 4-hour timeframes where gap between candle wicks exceeds minimum threshold
2. WHEN an inverse FVG is detected, THE Scanner SHALL mark the zone boundaries (high of lower candle, low of upper candle)
3. THE Scanner SHALL monitor for price returning to FVG zones and detect lower timeframe shift in structure
4. WHEN price enters an FVG zone AND lower timeframe shows shift in market structure, THE Scanner SHALL generate a signal
5. THE Scanner SHALL identify liquidity voids (unfilled gaps) and include them in signal reasoning

### Requirement 14

**User Story:** As a trader, I want signals that combine higher timeframe FVG zones with lower timeframe confirmation, so that I enter trades with institutional backing and clear targets

#### Acceptance Criteria

1. WHEN detecting FVG signals, THE Scanner SHALL require confirmation from a lower timeframe (e.g., 1h shift for 1d FVG)
2. THE Scanner SHALL calculate targets based on previous swing lows/highs and liquidity pools
3. THE Scanner SHALL include FVG zone boundaries in the signal alert
4. THE Scanner SHALL mark FVG zones as "filled" once price fully retraces through the gap
5. THE Scanner SHALL prioritize FVG signals over standard EMA crossover signals when both occur

### Requirement 15

**User Story:** As a trader, I want the scanner to detect New Week Opening Gaps (NWOG) for indices like US30, so that I can trade institutional levels that form at weekly opens

#### Acceptance Criteria

1. THE Scanner SHALL detect NWOG by comparing Friday close price to Monday open price
2. WHEN an NWOG gap exceeds minimum threshold, THE Scanner SHALL mark the gap zone as a key level
3. THE Scanner SHALL monitor for price returning to NWOG zones and respecting them as support or resistance
4. WHEN price approaches an NWOG zone AND shows rejection, THE Scanner SHALL generate a signal
5. THE Scanner SHALL include NWOG zone boundaries and targets in signal alerts

### Requirement 16

**User Story:** As a trader, I want the scanner to detect inter-market divergence between indices, so that I can identify when US30 is diverging from S&P500 and anticipate reversals

#### Acceptance Criteria

1. THE Scanner SHALL track price movements of correlated indices (US30, S&P500, Nasdaq)
2. WHEN US30 makes a new high/low but S&P500 does not, THE Scanner SHALL flag a divergence
3. THE Scanner SHALL calculate divergence strength based on the magnitude of difference
4. WHEN divergence is detected AND price is at a key level, THE Scanner SHALL increase signal confidence
5. THE Scanner SHALL include divergence information in signal alerts for index symbols

### Requirement 17

**User Story:** As a system administrator, I want easy configuration management for adding or removing cryptocurrency and FX symbols, so that I can adapt to changing market conditions without code changes

#### Acceptance Criteria

1. THE Scanner SHALL read symbol configurations from a JSON configuration file
2. WHEN the configuration file is updated, THE Scanner SHALL reload settings without requiring a restart
3. THE Scanner SHALL validate all symbol configurations on startup and log any errors
4. WHEN a symbol configuration is invalid, THE Scanner SHALL skip that symbol and continue with valid symbols
5. THE Scanner SHALL provide a configuration template with recommended settings for common cryptocurrencies and FX pairs
6. THE Scanner SHALL categorize symbols by asset type (crypto, fx, commodity) in the configuration
