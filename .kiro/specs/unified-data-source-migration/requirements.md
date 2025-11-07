# Requirements Document

## Introduction

This specification addresses critical issues with the trading scanner system where price alerts don't match live trading platforms, incorrect symbol labeling in alerts (showing "BTC" for all symbols), and missing signals from non-Gold scanners. The root cause is inconsistent data sources across scanners and improper symbol handling in signal generation.

## Glossary

- **Scanner System**: The multi-asset trading signal detection application that monitors BTC, XAU/USD (Gold), and US30 (Dow Jones)
- **Data Source**: The market data provider (currently split between Kraken, Binance, and Yahoo Finance)
- **Signal Detector**: Component that identifies trading opportunities based on technical indicators
- **Alerter**: Component that sends trading signals via Telegram/Email
- **Symbol Context**: The trading pair/asset being monitored (BTC/USDT, XAU/USD, US30)
- **Live Trading Platform**: The actual broker/exchange where user executes trades
- **Price Discrepancy**: Difference between scanner-reported prices and live platform prices

## Requirements

### Requirement 1: Unified Data Source with MT5-Compatible Pricing

**User Story:** As a trader using MT5 for execution, I want all scanners to use a consistent data source that provides pricing close to my MT5 broker, so that signals are actionable and price levels are relevant when I enter trades.

#### Acceptance Criteria

1. WHEN the Scanner System initializes, THE Scanner System SHALL use Yahoo Finance as the unified data source for all assets (BTC, XAU/USD, US30)
2. WHEN fetching market data, THE Scanner System SHALL use institutional-grade symbols (BTC-USD for Bitcoin, GC=F for Gold Futures, ^DJI for Dow Jones)
3. WHEN a price alert is generated, THE Scanner System SHALL include a disclaimer that prices are indicative and may differ from broker execution prices
4. WHEN market data is fetched, THE Scanner System SHALL validate that price data is within 0.5% of the previous candle to detect data quality issues
5. WHEN data source connection fails, THE Scanner System SHALL log the error with specific data source details and attempt reconnection with exponential backoff

### Requirement 2: Correct Symbol Identification

**User Story:** As a trader, I want each alert to clearly show which asset triggered the signal (BTC, Gold, or US30), so that I don't confuse signals between different markets.

#### Acceptance Criteria

1. WHEN a signal is detected, THE Signal Detector SHALL include the correct symbol name in the signal object
2. WHEN an alert is sent, THE Alerter SHALL display the symbol prominently in the alert header
3. WHEN multiple scanners are running, THE Scanner System SHALL maintain separate signal detection contexts for each symbol
4. WHEN logging scan results, THE Scanner System SHALL record the exact symbol being scanned
5. WHEN a signal object is created, THE Signal Detector SHALL validate that the symbol field is not null or empty

### Requirement 3: Enhanced Signal Quality

**User Story:** As a trader, I want to receive high-confidence signals from all scanners (not just Gold), so that I can trade multiple assets with confidence.

#### Acceptance Criteria

1. WHEN market conditions meet strategy criteria, THE Signal Detector SHALL generate signals for all configured assets
2. WHEN evaluating signal quality, THE Signal Detector SHALL require minimum confluence of 3 factors (trend alignment, volume confirmation, momentum)
3. WHEN a signal is generated, THE Signal Detector SHALL calculate and include a confidence score (1-5 scale)
4. WHEN duplicate signals are detected within the time window, THE Signal Detector SHALL suppress the duplicate and log the suppression reason
5. WHEN signal quality is below threshold, THE Signal Detector SHALL log the rejection reason with specific indicator values

### Requirement 4: Data Source Configuration

**User Story:** As a system administrator, I want a centralized configuration for data sources, so that I can easily switch providers or update symbols without modifying code.

#### Acceptance Criteria

1. WHEN the Scanner System starts, THE Scanner System SHALL load data source configuration from a central config file
2. WHEN a data source is configured, THE Scanner System SHALL validate that required fields (provider, symbol, timeframes) are present
3. WHEN symbol mapping is needed, THE Scanner System SHALL use a configurable symbol translation table
4. WHEN configuration is invalid, THE Scanner System SHALL fail fast with a clear error message indicating the configuration issue
5. WHEN data source settings change, THE Scanner System SHALL support hot-reload without full restart

### Requirement 5: Price Validation and Monitoring

**User Story:** As a trader, I want the system to detect and alert me when price data appears incorrect, so that I don't act on bad data.

#### Acceptance Criteria

1. WHEN new price data is received, THE Scanner System SHALL compare it against the previous candle for anomalies
2. WHEN price change exceeds 5% in a single candle, THE Scanner System SHALL flag the data as potentially anomalous and log a warning
3. WHEN volume is zero or negative, THE Scanner System SHALL reject the candle data and log an error
4. WHEN timestamp is in the future or more than 1 hour in the past, THE Scanner System SHALL reject the candle data
5. WHEN 3 consecutive data quality issues occur, THE Scanner System SHALL pause signal generation and send an alert to the administrator

### Requirement 6: Symbol-Specific Alert Formatting

**User Story:** As a trader, I want alerts formatted specifically for each asset type, so that I can quickly understand the context and market-specific factors.

#### Acceptance Criteria

1. WHEN a BTC signal is generated, THE Alerter SHALL include BTC-specific context (dominance, funding rates if available)
2. WHEN a Gold signal is generated, THE Alerter SHALL include Gold-specific context (session, spread, key levels)
3. WHEN a US30 signal is generated, THE Alerter SHALL include US30-specific context (market hours, trend strength)
4. WHEN any signal is sent, THE Alerter SHALL use a distinct emoji/icon for each asset type (₿ for BTC, 🥇 for Gold, 📊 for US30)
5. WHEN the alert is formatted, THE Alerter SHALL include the exact entry price with appropriate decimal precision (2 decimals for BTC/US30, 2 decimals for Gold)

### Requirement 7: Multi-Scanner Signal Coordination

**User Story:** As a trader, I want the system to coordinate signals across all scanners, so that I receive balanced alerts from all assets without overwhelming notifications.

#### Acceptance Criteria

1. WHEN multiple scanners detect signals simultaneously, THE Scanner System SHALL queue alerts with timestamps
2. WHEN sending queued alerts, THE Scanner System SHALL maintain a minimum 30-second gap between alerts
3. WHEN a scanner generates excessive signals (>5 per hour), THE Scanner System SHALL log a warning about potential over-trading
4. WHEN all scanners are active, THE Scanner System SHALL report health status for each scanner in heartbeat messages
5. WHEN a scanner fails to generate signals for 24 hours, THE Scanner System SHALL log a warning about potential configuration issues
