# Requirements Document

## Introduction

This specification addresses critical signal detection failures across 8 trading scanners (BTC Scalp, BTC Swing, US30 Momentum, Multi-Crypto Scalp, Multi-Crypto Swing, Multi-FX Scalp, Multi-Mixed, and Gold scanners). The system is currently generating zero or invalid signals due to overly restrictive filtering, configuration issues, and strategy detection problems.

## Glossary

- **Scanner**: An automated trading signal detection system monitoring specific assets and timeframes
- **Signal**: A trading opportunity alert with entry, stop-loss, and take-profit levels
- **Confluence Factor**: A technical indicator or condition that must align for signal generation
- **Quality Filter**: A validation layer that evaluates signal quality before alerting
- **Strategy Detector**: A component that identifies specific trading patterns (EMA crossover, mean reversion, etc.)
- **Timeframe**: The candlestick interval being analyzed (1m, 5m, 15m, 1h, 4h, 1d)
- **ATR**: Average True Range - a volatility indicator
- **RSI**: Relative Strength Index - a momentum oscillator
- **ADX**: Average Directional Index - a trend strength indicator
- **EMA**: Exponential Moving Average - a trend-following indicator
- **VWAP**: Volume Weighted Average Price - a trading benchmark

## Requirements

### Requirement 1: Diagnostic Analysis System

**User Story:** As a trader, I want a comprehensive diagnostic tool that identifies why signals aren't being generated, so that I can understand and fix the root causes.

#### Acceptance Criteria

1. WHEN the diagnostic tool is executed, THE System SHALL analyze all 8 scanners and generate a detailed report
2. WHEN analyzing each scanner, THE System SHALL check data freshness, indicator calculations, strategy detection, and filter thresholds
3. WHEN a configuration issue is detected, THE System SHALL log the specific parameter causing signal suppression
4. WHEN the analysis completes, THE System SHALL output a prioritized list of issues with recommended fixes
5. THE System SHALL track signal detection attempts vs successful signals for each scanner

### Requirement 2: Relaxed Quality Filter Thresholds

**User Story:** As a trader, I want the quality filter to use more realistic thresholds, so that valid trading opportunities aren't suppressed.

#### Acceptance Criteria

1. THE Quality Filter SHALL reduce minimum confluence factors from 4 to 3
2. THE Quality Filter SHALL reduce minimum confidence score from 4 to 3
3. THE Quality Filter SHALL reduce minimum risk-reward ratio from 1.5 to 1.2
4. THE Quality Filter SHALL reduce minimum ADX threshold from 18 to 15
5. THE Quality Filter SHALL increase RSI range from 30-70 to 25-75 for trend signals

### Requirement 3: Strategy Detection Improvements

**User Story:** As a trader, I want each strategy detector to have properly calibrated thresholds, so that signals are generated when valid patterns occur.

#### Acceptance Criteria

1. WHEN detecting EMA crossover signals, THE System SHALL require EMA9 > EMA21 alignment without requiring EMA50 cascade
2. WHEN detecting mean reversion signals, THE System SHALL reduce overextension threshold from 1.8 ATR to 1.5 ATR
3. WHEN detecting trend alignment signals, THE System SHALL reduce ADX minimum from 19 to 15
4. WHEN detecting breakout signals, THE System SHALL reduce volume threshold from 1.5x to 1.3x
5. WHEN detecting momentum shift signals, THE System SHALL reduce RSI momentum threshold from 60 to 55

### Requirement 4: Volume Threshold Adjustments

**User Story:** As a trader, I want volume thresholds adjusted per asset class, so that signals aren't suppressed due to normal volume patterns.

#### Acceptance Criteria

1. THE System SHALL use 1.3x volume threshold for crypto scalping strategies
2. THE System SHALL use 1.2x volume threshold for crypto swing strategies
3. THE System SHALL use 1.5x volume threshold for US30 momentum strategies
4. THE System SHALL use 1.4x volume threshold for FX scalping strategies
5. THE System SHALL use 0.8x volume threshold for trend alignment strategies

### Requirement 5: Duplicate Detection Refinement

**User Story:** As a trader, I want duplicate detection to allow new signals when market conditions change significantly, so that I don't miss valid opportunities.

#### Acceptance Criteria

1. THE System SHALL increase duplicate time window from 5 minutes to 10 minutes for scalping
2. THE System SHALL increase duplicate price tolerance from 0.5% to 1.0%
3. WHEN price moves more than 1.5% from previous signal, THE System SHALL allow new signal regardless of time window
4. WHEN RSI changes by more than 15 points, THE System SHALL allow new signal
5. WHEN timeframe differs from previous signal, THE System SHALL not consider it a duplicate

### Requirement 6: Configuration Validation

**User Story:** As a trader, I want the system to validate all configuration files on startup, so that misconfigured parameters don't silently prevent signals.

#### Acceptance Criteria

1. WHEN a scanner starts, THE System SHALL validate all required configuration parameters exist
2. WHEN a threshold value is outside reasonable bounds, THE System SHALL log a warning with recommended value
3. WHEN strategy-specific configuration is missing, THE System SHALL use documented default values
4. THE System SHALL log the active configuration for each scanner on startup
5. WHEN configuration changes are detected, THE System SHALL reload and re-validate settings

### Requirement 7: Signal Generation Monitoring

**User Story:** As a trader, I want real-time monitoring of signal detection attempts, so that I can see when patterns are detected but filtered out.

#### Acceptance Criteria

1. THE System SHALL log each strategy detection attempt with pass/fail status
2. WHEN a signal is generated but filtered, THE System SHALL log the specific filter that rejected it
3. THE System SHALL track detection rate (attempts vs successful signals) per strategy
4. THE System SHALL send a daily summary of detection statistics via Telegram
5. WHEN no signals are generated for 4 hours, THE System SHALL send an alert notification

### Requirement 8: Emergency Bypass Mode

**User Story:** As a trader, I want an emergency bypass mode that temporarily disables quality filters, so that I can verify the core detection logic is working.

#### Acceptance Criteria

1. WHEN bypass mode is enabled via configuration, THE System SHALL skip quality filter validation
2. WHEN bypass mode is active, THE System SHALL prefix all alerts with "BYPASS MODE"
3. THE System SHALL log all signals that would have been filtered in bypass mode
4. WHEN bypass mode is enabled, THE System SHALL send a notification confirming the mode change
5. THE System SHALL automatically disable bypass mode after 2 hours for safety

### Requirement 9: Per-Scanner Threshold Customization

**User Story:** As a trader, I want each scanner to have independently tunable thresholds, so that I can optimize detection for different assets and timeframes.

#### Acceptance Criteria

1. THE System SHALL support asset-specific configuration overrides for BTC, XAUUSD, and US30
2. THE System SHALL support timeframe-specific threshold adjustments (scalp vs swing)
3. WHEN asset-specific config exists, THE System SHALL use it instead of global defaults
4. THE System SHALL log which configuration source is being used for each parameter
5. THE System SHALL validate that asset-specific overrides are within reasonable bounds

### Requirement 10: Data Quality Validation

**User Story:** As a trader, I want the system to validate data quality before attempting signal detection, so that stale or invalid data doesn't cause false negatives.

#### Acceptance Criteria

1. WHEN fetching market data, THE System SHALL verify timestamp freshness within expected interval
2. WHEN indicator calculations produce NaN values, THE System SHALL log the specific indicator and skip that iteration
3. THE System SHALL verify minimum candle count (50) before attempting strategy detection
4. WHEN volume data is zero or missing, THE System SHALL log a warning and skip volume-based strategies
5. THE System SHALL track data quality metrics and include them in diagnostic reports
