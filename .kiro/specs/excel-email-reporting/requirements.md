# Requirements Document

## Introduction

This feature adds Excel-based logging and email reporting capabilities to all trading scanners (BTC, US30, XAUUSD scalp and swing). Each scanner will append scan results to an Excel file and email reports at configurable intervals. This enables monitoring, debugging, and verification that scanners are running correctly and not missing alerts.

## Glossary

- **Scanner**: Any of the trading signal detection systems (BTC, US30 scalp/swing, XAUUSD scalp/swing)
- **Scan Result**: The output from a single scan cycle including timestamp, symbol, price, indicators, and any signals detected
- **Excel Report**: An Excel file (.xlsx) containing timestamped scan results with one row per scan cycle
- **Email Service**: The system component responsible for sending Excel reports via email
- **Report Interval**: The time period between automated email reports (default: 1 hour)
- **Initial Report**: The first email report sent shortly after scanner startup (within 5 minutes)
- **Config Toggle**: A configuration parameter that enables or disables the Excel reporting feature

## Requirements

### Requirement 1

**User Story:** As a trader, I want all scan results logged to an Excel file, so that I can review historical scanner activity and verify it's working correctly

#### Acceptance Criteria

1. WHEN a scan cycle completes, THE Scanner SHALL append the scan result to an Excel file with timestamp, symbol, price, all indicator values, and any signals detected
2. THE Scanner SHALL create a new Excel file if one does not exist at the configured file path
3. THE Scanner SHALL include column headers in the Excel file with descriptive names for all data fields
4. THE Scanner SHALL handle Excel file write errors without crashing the scanner
5. WHERE the Excel reporting feature is disabled in config, THE Scanner SHALL NOT write to Excel files

### Requirement 2

**User Story:** As a trader, I want to receive email reports with the Excel file every hour, so that I can monitor scanner activity remotely without accessing the server

#### Acceptance Criteria

1. WHILE the Excel reporting feature is enabled, THE Scanner SHALL send an email with the Excel file attached at the configured report interval
2. THE Scanner SHALL include a summary in the email body showing total scans, signals detected, and time range covered
3. THE Scanner SHALL use SMTP configuration from the config file including server, port, credentials, and recipient email
4. IF email sending fails, THEN THE Scanner SHALL log the error and continue normal operation
5. THE Scanner SHALL schedule the next email report based on the configured interval (default: 3600 seconds)

### Requirement 3

**User Story:** As a trader, I want to receive an initial email report within 5 minutes of starting the scanner, so that I can quickly verify it's running correctly

#### Acceptance Criteria

1. WHEN the scanner starts with Excel reporting enabled, THE Scanner SHALL schedule an initial email report to be sent within 5 minutes
2. THE Scanner SHALL send the initial report even if minimal scan data has been collected
3. THE Scanner SHALL include a startup notification in the initial email body indicating scanner start time
4. AFTER the initial report is sent, THE Scanner SHALL continue with regular interval-based reporting
5. WHERE the Excel reporting feature is disabled, THE Scanner SHALL NOT send any email reports

### Requirement 4

**User Story:** As a trader, I want to enable or disable Excel reporting through the config file, so that I can control this feature without modifying code

#### Acceptance Criteria

1. THE Scanner SHALL read an "excel_reporting" configuration section from the config file
2. THE Scanner SHALL check an "enabled" boolean flag to determine if Excel reporting is active
3. WHERE Excel reporting is disabled, THE Scanner SHALL skip all Excel writing and email sending operations
4. THE Scanner SHALL read Excel file path, email settings, and report interval from the config file
5. THE Scanner SHALL validate all required configuration parameters are present when Excel reporting is enabled and log warnings for missing values

### Requirement 5

**User Story:** As a developer, I want to review Excel files shared by users, so that I can diagnose issues with missing alerts or incorrect scanner behavior

#### Acceptance Criteria

1. THE Scanner SHALL include sufficient detail in each Excel row to reproduce the scanner state at that moment
2. THE Scanner SHALL format timestamps in a human-readable format (ISO 8601)
3. THE Scanner SHALL include a row identifier or sequence number for each scan result
4. THE Scanner SHALL preserve all decimal precision for price and indicator values
5. THE Scanner SHALL include a column indicating whether any signal was triggered during that scan
