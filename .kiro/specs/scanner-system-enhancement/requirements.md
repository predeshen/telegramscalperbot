# Scanner System Enhancement - Requirements Document

## Introduction

This specification covers a comprehensive enhancement of the trading scanner system to improve signal quality, data freshness, strategy effectiveness, and operational efficiency. The system currently operates 8 independent scanners (BTC Scalp, BTC Swing, Gold Scalp, Gold Swing, US30 Scalp, US30 Swing, US100, Multi-Crypto) with varying data sources and signal detection strategies. The enhancement aims to unify the architecture, implement proven trading strategies (Fibonacci Retracement, H4 HVG, Support/Resistance), improve data source reliability, and streamline deployment and operations.

## Glossary

- **Scanner**: An independent trading signal detection system monitoring a specific symbol and timeframe combination
- **Strategy**: A technical analysis approach for detecting trading signals (e.g., EMA Crossover, Fibonacci Retracement, H4 HVG)
- **Signal**: A trading opportunity identified by a scanner with entry, stop-loss, and take-profit levels
- **Data Source**: External API or service providing market data (Binance, Alpha Vantage, Twelve Data, MT5)
- **Confluence**: Multiple technical indicators aligning to confirm a trading signal
- **TP/SL**: Take-Profit and Stop-Loss levels calculated based on historical price action
- **H4 HVG**: 4-hour timeframe Higher Volume Gap detection strategy
- **Fibonacci Retracement**: Price retracement levels based on Fibonacci ratios (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- **Support/Resistance**: Key price levels where price historically reverses or consolidates
- **Live Signal**: Trading signal generated for current market conditions
- **Future Signal**: Predictive signal identifying potential opportunities in upcoming candles
- **Risk/Reward Ratio**: Relationship between potential profit and potential loss on a trade

## Requirements

### Requirement 1: Unified Scanner Architecture

**User Story:** As a system operator, I want all 8 scanners to share a common architecture and configuration structure, so that I can manage them consistently and reduce code duplication.

#### Acceptance Criteria

1. WHEN a scanner is initialized, THE system SHALL load configuration from a unified config structure that defines symbol, timeframes, strategies, and data sources
2. WHILE a scanner is running, THE system SHALL apply consistent signal detection logic across all symbols (BTC, XAUUSD, US30, US100, multi-crypto)
3. WHERE a scanner requires symbol-specific parameters, THE system SHALL allow asset-specific configuration overrides without duplicating core logic
4. IF a scanner detects a signal, THEN THE system SHALL format and send alerts using a unified alerting system (email, Telegram, Excel)
5. WHEN a scanner starts, THE system SHALL validate all required configuration parameters and fail fast with clear error messages if configuration is invalid

### Requirement 2: Data Source Validation and Freshness

**User Story:** As a trader, I want to ensure that all market data is fresh and accurate, so that signals are based on current market conditions and not stale data.

#### Acceptance Criteria

1. WHEN market data is fetched, THE system SHALL validate that data timestamps are within 5 minutes of current time
2. IF data is detected as stale, THEN THE system SHALL automatically retry with exponential backoff (1s, 2s, 4s, 8s) up to 3 attempts
3. WHILE data remains stale after retries, THE system SHALL log warnings and alert the operator after 3 consecutive stale data events
4. WHEN data freshness is restored, THE system SHALL send a recovery notification to the operator
5. WHERE multiple data sources are available (Alpha Vantage, Twelve Data, Binance), THE system SHALL implement fallback logic to switch sources if primary source fails

### Requirement 3: Enhanced Signal Detection - Fibonacci Retracement

**User Story:** As a trader, I want the system to identify Fibonacci retracement levels and generate signals when price bounces from these levels, so that I can trade high-probability reversals.

#### Acceptance Criteria

1. WHEN analyzing price data, THE system SHALL identify swing highs and lows over a configurable lookback period (default 50 candles)
2. THE system SHALL calculate Fibonacci retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%) from identified swing points
3. WHEN price approaches a Fibonacci level (within 0.5% tolerance), THE system SHALL monitor for reversal signals
4. IF price reverses at a Fibonacci level with volume confirmation (1.3x average), THEN THE system SHALL generate a trading signal
5. WHERE a reversal candle pattern is detected (pin bar, engulfing, doji) at a Fibonacci level, THE system SHALL increase signal confidence to 4/5

### Requirement 4: Enhanced Signal Detection - H4 HVG Strategy

**User Story:** As a trader, I want the system to detect 4-hour timeframe higher volume gaps and generate signals for gap fills, so that I can trade predictable mean reversion patterns.

#### Acceptance Criteria

1. WHEN analyzing 4-hour data, THE system SHALL identify gaps (difference between close and next open) exceeding 0.15% of price
2. IF a gap is detected with volume spike (1.5x average), THEN THE system SHALL track the gap as a potential trading opportunity
3. WHEN price approaches the gap fill level on lower timeframes (1m, 5m, 15m), THE system SHALL generate a signal with the gap fill as take-profit target
4. WHERE a gap is older than 3 candles, THE system SHALL deprioritize it in favor of fresher gaps
5. IF a gap fill signal is generated, THEN THE system SHALL calculate stop-loss at 1.5x ATR from entry and require minimum 1.5:1 risk/reward ratio

### Requirement 5: Enhanced Signal Detection - Support/Resistance Strategy

**User Story:** As a trader, I want the system to identify key support and resistance levels and generate signals when price bounces from these levels, so that I can trade established price levels.

#### Acceptance Criteria

1. WHEN analyzing price data, THE system SHALL identify support and resistance levels based on price touches (minimum 2 touches required)
2. THE system SHALL calculate level tolerance (0.3% by default) to group nearby price touches into single levels
3. WHEN price approaches a support/resistance level (within tolerance), THE system SHALL monitor for reversal signals
4. IF price reverses at a support/resistance level with volume confirmation (1.4x average), THEN THE system SHALL generate a trading signal
5. WHERE a reversal candle pattern is detected at a support/resistance level, THE system SHALL increase signal confidence to 4/5

### Requirement 6: Intelligent TP/SL Calculation Based on Historical Price Action

**User Story:** As a trader, I want stop-loss and take-profit levels to be calculated based on historical price action patterns, so that I can trade with realistic risk/reward ratios based on actual market behavior.

#### Acceptance Criteria

1. WHEN a signal is generated, THE system SHALL analyze all previous candles (minimum 100 candles) to identify common reversal points
2. THE system SHALL calculate the most common distance from entry price where reversals occur (mode of reversal distances)
3. THE system SHALL use this historical mode as the basis for stop-loss placement instead of fixed ATR multiples
4. WHEN calculating take-profit, THE system SHALL identify the most common profit-taking levels from historical data
5. IF historical analysis shows insufficient data, THEN THE system SHALL fall back to ATR-based calculation with 1.2x ATR for SL and 2.0x ATR for TP
6. WHERE a signal has a calculated risk/reward ratio below 1.2:1, THE system SHALL reject the signal as insufficient reward

### Requirement 7: Live and Future Signal Generation

**User Story:** As a trader, I want the system to generate both live signals (current candle) and future signals (upcoming candles), so that I can prepare for opportunities before they fully develop.

#### Acceptance Criteria

1. WHEN a signal is detected on the current candle, THE system SHALL classify it as a "LIVE" signal and send immediate alert
2. WHEN price action suggests a signal will likely form on the next 1-3 candles, THE system SHALL classify it as a "FUTURE" signal and send preparatory alert
3. WHERE a future signal is identified, THE system SHALL include predicted entry, stop-loss, and take-profit levels in the alert
4. IF a future signal does not materialize within 3 candles, THE system SHALL send a "Signal Cancelled" notification
5. WHEN a future signal materializes into a live signal, THE system SHALL send an updated alert with actual levels

### Requirement 8: Unified Deployment and Service Management

**User Story:** As a system operator, I want a single deployment script that installs and enables all 8 scanners as system services, so that I can quickly set up the entire system on new VMs.

#### Acceptance Criteria

1. WHEN running the fresh install script, THE system SHALL install all Python dependencies, create required directories, and set up all 8 scanner services
2. THE system SHALL create a single unified start script that starts all scanners with a single command
3. THE system SHALL create a single unified stop script that stops all scanners with a single command
4. THE system SHALL create a single unified restart script that restarts all scanners with a single command
5. WHERE a scanner fails to start, THE system SHALL log the error and continue starting remaining scanners

### Requirement 9: Codebase Cleanup and Consolidation

**User Story:** As a developer, I want the codebase to be clean and organized with minimal duplication, so that I can maintain and enhance the system efficiently.

#### Acceptance Criteria

1. WHEN reviewing the codebase, THE system SHALL have no unused .md documentation files (only README.md and DEPLOYMENT_GUIDE.md remain)
2. THE system SHALL have no unused .sh shell scripts (only fresh_install.sh, start_all_scanners.sh, stop_all_scanners.sh, restart_all_scanners.sh remain)
3. WHERE scanner-specific code exists, THE system SHALL consolidate it into a unified scanner module with symbol-specific configuration
4. IF duplicate strategy implementations exist across scanners, THEN THE system SHALL consolidate them into a single strategy module
5. WHEN the codebase is reviewed, THE system SHALL have clear separation between core logic (src/), scanner implementations (scanners/), and configuration (config/)

### Requirement 10: Strong and Early Signal Detection

**User Story:** As a trader, I want the system to generate strong, high-confidence signals with early detection, so that I can enter trades at optimal prices with minimal slippage.

#### Acceptance Criteria

1. WHEN a signal is generated, THE system SHALL require minimum 4 confluence factors (out of 7 possible) to be met
2. THE system SHALL assign confidence scores (1-5) based on number of confluence factors met
3. WHERE confluence factors include: trend alignment, volume confirmation, RSI range, support/resistance bounce, Fibonacci level, H4 HVG gap, and pattern recognition
4. IF a signal has fewer than 4 confluence factors, THEN THE system SHALL reject it as low-confidence
5. WHEN early signal detection is enabled, THE system SHALL identify signals forming on the current candle before close (future signals)

### Requirement 11: Data Source Reliability and Fallback

**User Story:** As a system operator, I want the system to automatically handle data source failures and switch to backup sources, so that scanners continue operating even if primary data sources fail.

#### Acceptance Criteria

1. WHEN a data source fails to return data, THE system SHALL log the failure and attempt the next available source
2. THE system SHALL maintain a priority list of data sources (Binance > Twelve Data > Alpha Vantage > MT5)
3. IF all primary sources fail, THEN THE system SHALL use cached data with a staleness warning
4. WHEN a failed data source recovers, THE system SHALL automatically switch back to it after 5 successful consecutive requests
5. WHERE data source switching occurs, THE system SHALL log the switch and alert the operator

### Requirement 12: Configuration Validation and Error Handling

**User Story:** As a system operator, I want the system to validate all configurations on startup and provide clear error messages, so that I can quickly identify and fix configuration issues.

#### Acceptance Criteria

1. WHEN a scanner starts, THE system SHALL validate all required configuration parameters
2. IF a required parameter is missing, THEN THE system SHALL fail fast with a clear error message indicating which parameter is missing
3. WHERE configuration values are out of acceptable ranges, THE system SHALL log warnings and use sensible defaults
4. IF SMTP credentials are invalid, THEN THE system SHALL disable email alerts and continue with Telegram only
5. WHEN configuration is successfully validated, THE system SHALL log a confirmation message with all active features

