# Requirements Document

## Introduction

The trade tracking system is failing to properly detect and notify when take-profit targets are hit. Users are experiencing situations where their trades reach the TP level but no "TARGET HIT" notification is sent. Instead, the system sends conflicting notifications including stop-loss hits for different positions and breakeven updates. This creates confusion and prevents proper trade management.

## Glossary

- **TradeTracker**: The system component responsible for monitoring active trades and sending management notifications
- **TP (Take Profit)**: The target price level where a trade should be closed for profit
- **SL (Stop Loss)**: The price level where a trade should be closed to limit losses
- **Trade ID**: Unique identifier for each tracked trade, formatted as `{symbol}_{signal_type}_{timestamp}`
- **Signal**: A trading opportunity with entry, stop-loss, and take-profit levels
- **Trade Status**: The current state of an active trade (ACTIVE, CLOSED_TP, CLOSED_SL, EXTENDED)

## Requirements

### Requirement 1

**User Story:** As a trader, I want to receive accurate "TARGET HIT" notifications when my take-profit level is reached, so that I know when to close my winning trades.

#### Acceptance Criteria

1. WHEN the current price reaches or exceeds the take-profit level for a LONG trade, THE TradeTracker SHALL send a "TARGET HIT - WINNER!" notification with the final P&L
2. WHEN the current price reaches or falls below the take-profit level for a SHORT trade, THE TradeTracker SHALL send a "TARGET HIT - WINNER!" notification with the final P&L
3. WHEN a take-profit notification is sent, THE TradeTracker SHALL remove the trade from active tracking to prevent duplicate notifications
4. WHEN a take-profit is hit, THE TradeTracker SHALL calculate and display the actual profit percentage and R:R achieved
5. WHEN a take-profit notification is sent, THE TradeTracker SHALL include the hold time in minutes

### Requirement 2

**User Story:** As a trader, I want each trade to be tracked with a unique identifier, so that multiple trades on the same symbol don't interfere with each other.

#### Acceptance Criteria

1. WHEN a new trade is added, THE TradeTracker SHALL generate a unique trade ID using the format `{symbol}_{signal_type}_{timestamp}`
2. WHEN multiple trades exist for the same symbol, THE TradeTracker SHALL track each trade independently using its unique trade ID
3. WHEN updating trade status, THE TradeTracker SHALL use the trade ID to ensure the correct trade is updated
4. WHEN closing a trade, THE TradeTracker SHALL use the trade ID to ensure only the correct trade is closed
5. THE TradeTracker SHALL log all trade ID operations for debugging purposes

### Requirement 3

**User Story:** As a trader, I want to see only relevant notifications for each trade, so that I'm not confused by duplicate or conflicting messages.

#### Acceptance Criteria

1. WHEN a trade is closed (TP or SL hit), THE TradeTracker SHALL not send any further notifications for that trade
2. WHEN a breakeven notification is sent, THE TradeTracker SHALL mark the trade to prevent duplicate breakeven notifications
3. WHEN a stop-loss warning is sent, THE TradeTracker SHALL mark the trade to prevent duplicate warnings
4. WHEN a trade reaches take-profit, THE TradeTracker SHALL not send stop-loss or breakeven notifications
5. THE TradeTracker SHALL validate that a trade exists in active_trades before sending any notification

### Requirement 4

**User Story:** As a trader, I want the system to correctly detect when price levels are hit, so that I receive timely and accurate notifications.

#### Acceptance Criteria

1. WHEN checking if TP is hit for a LONG trade, THE TradeTracker SHALL compare current_price >= take_profit
2. WHEN checking if TP is hit for a SHORT trade, THE TradeTracker SHALL compare current_price <= take_profit
3. WHEN checking if SL is hit for a LONG trade, THE TradeTracker SHALL compare current_price <= stop_loss
4. WHEN checking if SL is hit for a SHORT trade, THE TradeTracker SHALL compare current_price >= stop_loss
5. WHEN using extended TP, THE TradeTracker SHALL check against the extended_tp value instead of the original take_profit

### Requirement 5

**User Story:** As a developer, I want comprehensive logging of trade tracking operations, so that I can debug issues when notifications fail.

#### Acceptance Criteria

1. WHEN a trade is added, THE TradeTracker SHALL log the trade ID, entry price, and symbol
2. WHEN checking price levels, THE TradeTracker SHALL log the current price and comparison results
3. WHEN a notification is sent, THE TradeTracker SHALL log the notification type and trade ID
4. WHEN a trade is closed, THE TradeTracker SHALL log the reason, P&L, and trade ID
5. WHEN an error occurs during trade tracking, THE TradeTracker SHALL log the error with full context
