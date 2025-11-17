# Requirements Document

## Introduction

The trading scanner currently fetches market data without validating its freshness, which can lead to delayed trade notifications when stale data is received from the exchange API. This creates a critical issue where take-profit or stop-loss levels may be hit in real-time, but the scanner doesn't detect them for extended periods (1+ hours) because it's processing outdated price data.

## Glossary

- **Data Freshness**: The time difference between the current system time and the timestamp of the most recent candle received from the exchange
- **Stale Data**: Market data that is older than an acceptable threshold for the given timeframe
- **MarketDataClient**: The system component responsible for fetching candlestick data from cryptocurrency exchanges
- **Scanner Main Loop**: The primary execution loop that fetches data, detects signals, and updates active trades
- **Timeframe**: The candlestick interval (e.g., 1m, 5m, 1h) being monitored

## Requirements

### Requirement 1

**User Story:** As a trader, I want the scanner to validate that market data is fresh before using it for trade decisions, so that I receive timely notifications when my TP/SL levels are hit.

#### Acceptance Criteria

1. WHEN the scanner fetches market data, THE MarketDataClient SHALL validate that the latest candle timestamp is within an acceptable freshness threshold
2. WHEN data is stale (exceeds freshness threshold), THE MarketDataClient SHALL log a warning with the data age and timeframe
3. WHEN data is stale, THE Scanner SHALL skip processing that data and attempt to refetch
4. WHEN data remains stale after retry, THE Scanner SHALL send an alert notification to the user
5. THE freshness threshold SHALL be configurable per timeframe (e.g., 1m = 90 seconds, 5m = 7 minutes, 1h = 90 minutes)

### Requirement 2

**User Story:** As a trader, I want the scanner to continue updating active trades even when signal detection fails, so that my TP/SL notifications are not delayed by data fetching issues.

#### Acceptance Criteria

1. WHEN the scanner fails to fetch fresh data for signal detection, THE Scanner SHALL still attempt to update active trades with the last known good price
2. WHEN updating trades with last known price, THE Scanner SHALL log that it is using cached data
3. WHEN the last known price is older than 5 minutes, THE Scanner SHALL not update trades and SHALL log a warning
4. WHEN trades cannot be updated due to stale data, THE Scanner SHALL send an alert after 3 consecutive failures
5. THE Scanner SHALL track the timestamp of the last successful trade update

### Requirement 3

**User Story:** As a developer, I want comprehensive logging of data freshness issues, so that I can diagnose why trade notifications are delayed.

#### Acceptance Criteria

1. WHEN data is fetched, THE MarketDataClient SHALL log the data timestamp and age in seconds
2. WHEN data exceeds the freshness threshold, THE MarketDataClient SHALL log a WARNING with the timeframe, expected threshold, and actual age
3. WHEN the scanner skips stale data, THE Scanner SHALL log the skip event with the reason
4. WHEN the scanner uses cached data for trade updates, THE Scanner SHALL log the cache age
5. WHEN data freshness is restored after being stale, THE MarketDataClient SHALL log an INFO message

### Requirement 4

**User Story:** As a trader, I want to be alerted when the scanner is processing stale data for an extended period, so that I know my trade monitoring may be delayed.

#### Acceptance Criteria

1. WHEN data remains stale for more than 3 consecutive fetch attempts, THE Scanner SHALL send a Telegram alert
2. THE alert SHALL include the timeframe, data age, and last successful update time
3. WHEN data freshness is restored, THE Scanner SHALL send a recovery alert
4. THE Scanner SHALL not send duplicate stale data alerts within a 15-minute window
5. THE alert SHALL include actionable information (e.g., "Check exchange API status")

### Requirement 5

**User Story:** As a trader, I want the scanner to automatically attempt recovery when stale data is detected, so that trade monitoring resumes without manual intervention.

#### Acceptance Criteria

1. WHEN stale data is detected, THE Scanner SHALL wait 5 seconds and retry fetching data
2. WHEN the first retry fails, THE Scanner SHALL wait 10 seconds and retry again
3. WHEN the second retry fails, THE Scanner SHALL wait 30 seconds and retry a third time
4. WHEN all retries fail, THE Scanner SHALL continue with the main loop but skip signal detection for that timeframe
5. THE Scanner SHALL continue attempting to fetch fresh data on subsequent loop iterations
