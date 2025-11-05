# Requirements Document

## Introduction

This spec addresses two critical issues with the Gold (XAU/USD) scanner alerts:
1. Price discrepancies between scanner alerts and broker platform (Vantage Markets)
2. Incorrect symbol labeling in alerts (showing "BTC/USD" instead of "XAU/USD")

## Glossary

- **Scanner**: The automated trading signal detection system
- **Alerter**: The component responsible for sending Telegram/email notifications
- **Signal**: A trading opportunity detected by the scanner
- **Data Source**: The market data provider (currently Yahoo Finance)
- **Broker Platform**: Vantage Markets - the user's trading platform
- **Symbol**: The trading instrument identifier (e.g., XAU/USD, BTC/USD)

## Requirements

### Requirement 1: Correct Symbol Display in Alerts

**User Story:** As a trader, I want to see the correct symbol (XAU/USD) in my Gold scanner alerts, so that I can immediately identify which instrument the signal is for.

#### Acceptance Criteria

1. WHEN the Gold scanner detects a signal, THE Alerter SHALL display "XAU/USD" in the alert message header
2. WHEN the Gold scanner sends a Telegram alert, THE alert subject line SHALL contain "XAU/USD" instead of "BTC/USD"
3. WHEN the signal is created by the Gold signal detector, THE Signal object SHALL have the symbol attribute set to "XAU/USD"
4. WHEN formatting the alert message, THE Alerter SHALL use the symbol from the Signal object rather than a hardcoded value

### Requirement 2: Price Source Alignment with Broker

**User Story:** As a trader, I want the scanner to use price data that matches my broker's prices, so that I can execute trades at the prices shown in the alerts.

#### Acceptance Criteria

1. WHEN the Gold scanner fetches market data, THE system SHALL document the current data source and its typical price variance from Vantage Markets
2. WHEN a signal is generated, THE alert SHALL include a disclaimer about potential price differences between data sources
3. THE system SHALL provide configuration options to adjust for known price offsets between data sources
4. THE documentation SHALL explain the price source (Yahoo Finance Gold Futures) and expected variance from spot XAU/USD prices

### Requirement 3: Data Source Configuration

**User Story:** As a trader, I want to understand which data source is being used and how it differs from my broker, so that I can make informed trading decisions.

#### Acceptance Criteria

1. THE Gold scanner configuration SHALL clearly document the data source being used
2. THE startup message SHALL indicate the data source (e.g., "Yahoo Finance - GC=F Gold Futures")
3. THE system SHALL log the data source on scanner initialization
4. THE alert messages SHALL optionally include the data source identifier when configured
