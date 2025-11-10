# Requirements Document

## Introduction

This feature will unify and expand the trading strategy arsenal across all 6 scanners (BTC Scalp, BTC Swing, Gold Scalp, Gold Swing, US30 Scalp, US30 Swing) to ensure consistent signal detection capabilities. The goal is to make all strategies available to all scanners while adding new advanced strategies like Fibonacci retracements and support/resistance bounces.

## Glossary

- **Scanner**: A trading signal detection system for a specific asset and timeframe (e.g., BTC Scalp, Gold Swing)
- **Strategy**: A specific trading signal detection algorithm (e.g., Momentum Shift, Asian Range Breakout)
- **Signal**: A trading opportunity with entry, stop-loss, and take-profit levels
- **Confluence**: Multiple technical indicators confirming the same trading direction
- **SignalDetector**: The base class that implements core strategy detection logic
- **Asset-Specific Detector**: Scanner-specific detector classes (GoldSignalDetector, US30ScalpDetector)
- **Fibonacci Retracement**: Technical analysis tool using 23.6%, 38.2%, 50%, 61.8% levels to identify potential reversal zones
- **Support/Resistance**: Price levels where the market has historically reversed or consolidated
- **Key Level**: Significant price points (round numbers, previous highs/lows, psychological levels)

## Requirements

### Requirement 1: Unify Existing Strategies Across All Scanners

**User Story:** As a trader, I want all 6 scanners to have access to the same proven strategies, so that I don't miss opportunities due to scanner-specific limitations.

#### Acceptance Criteria

1. WHEN the system initializes, THE Scanner SHALL load all available strategies for its asset type
2. WHEN market conditions favor a specific strategy, THE Scanner SHALL detect signals using that strategy
3. WHERE a strategy is asset-specific (e.g., Asian Range Breakout), THE Scanner SHALL adapt the strategy parameters for the asset's characteristics
4. WHEN multiple strategies detect signals simultaneously, THE Scanner SHALL prioritize based on confidence score and market conditions
5. WHILE a scanner is running, THE Scanner SHALL attempt signal detection using all applicable strategies in priority order

### Requirement 2: Implement Asian Range Breakout for BTC and US30

**User Story:** As a trader, I want BTC and US30 scanners to detect Asian Range Breakout signals, so that I can capitalize on breakouts during the London and New York sessions.

#### Acceptance Criteria

1. WHEN the Asian session completes, THE Scanner SHALL record the session's high and low price range
2. WHEN price breaks above the Asian range high with volume confirmation, THE Scanner SHALL generate a LONG signal
3. WHEN price breaks below the Asian range low with volume confirmation, THE Scanner SHALL generate a SHORT signal
4. WHEN a breakout occurs, THE Scanner SHALL wait for a retest of the broken level before confirming the signal
5. WHERE the asset is BTC, THE Scanner SHALL use a buffer of 0.3% for breakout confirmation
6. WHERE the asset is US30, THE Scanner SHALL use a buffer of 15 points for breakout confirmation

### Requirement 3: Implement Liquidity Sweep Strategy for BTC and Gold

**User Story:** As a trader, I want BTC and Gold scanners to detect liquidity sweep patterns, so that I can enter trades after stop-loss hunts complete.

#### Acceptance Criteria

1. WHEN price sweeps below a recent swing low and reverses, THE Scanner SHALL detect a bullish liquidity sweep
2. WHEN price sweeps above a recent swing high and reverses, THE Scanner SHALL detect a bearish liquidity sweep
3. WHEN a liquidity sweep occurs, THE Scanner SHALL require volume spike of at least 1.5x average
4. WHEN a sweep is detected, THE Scanner SHALL require price to close back above/below VWAP for confirmation
5. WHEN EMA alignment confirms the reversal direction, THE Scanner SHALL generate the signal

### Requirement 4: Implement Trend Following Strategy for BTC and US30

**User Story:** As a trader, I want BTC and US30 scanners to detect trend-following pullback entries, so that I can enter established trends at optimal prices.

#### Acceptance Criteria

1. WHEN the system detects at least 3 swing highs/lows in the same direction, THE Scanner SHALL identify a trend
2. WHEN price pulls back to EMA(21) in an uptrend, THE Scanner SHALL monitor for bullish bounce signals
3. WHEN price pulls back to EMA(21) in a downtrend, THE Scanner SHALL monitor for bearish bounce signals
4. WHEN pullback depth exceeds 61.8%, THE Scanner SHALL reject the signal as too deep
5. WHEN volume confirms the bounce with at least 1.2x average, THE Scanner SHALL generate the signal
6. WHEN RSI is between 40-80 for uptrends or 20-60 for downtrends, THE Scanner SHALL validate the signal

### Requirement 5: Implement Fibonacci Retracement Strategy

**User Story:** As a trader, I want all scanners to detect Fibonacci retracement signals, so that I can enter trades at key retracement levels with high probability.

#### Acceptance Criteria

1. WHEN the system identifies a significant price swing (at least 2x ATR), THE Scanner SHALL calculate Fibonacci retracement levels at 23.6%, 38.2%, 50%, 61.8%, and 78.6%
2. WHEN price approaches within 0.5% of a Fibonacci level, THE Scanner SHALL monitor for reversal signals
3. WHEN price touches a Fibonacci level and forms a reversal candle pattern, THE Scanner SHALL detect a potential entry
4. WHEN volume confirms the reversal with at least 1.3x average, THE Scanner SHALL validate the signal
5. WHEN RSI shows divergence at the Fibonacci level, THE Scanner SHALL increase confidence score
6. WHERE the retracement is at 38.2% or 61.8% (golden ratios), THE Scanner SHALL assign higher priority
7. WHEN the signal is generated, THE Scanner SHALL set stop-loss beyond the next Fibonacci level

### Requirement 6: Implement Support/Resistance Bounce Strategy

**User Story:** As a trader, I want all scanners to detect support and resistance bounces, so that I can trade reversals at proven price levels.

#### Acceptance Criteria

1. WHEN the system analyzes historical data, THE Scanner SHALL identify support levels where price has bounced at least 2 times
2. WHEN the system analyzes historical data, THE Scanner SHALL identify resistance levels where price has reversed at least 2 times
3. WHEN price approaches within 0.3% of a support level, THE Scanner SHALL monitor for bullish reversal signals
4. WHEN price approaches within 0.3% of a resistance level, THE Scanner SHALL monitor for bearish reversal signals
5. WHEN price touches a support/resistance level and forms a pin bar, engulfing, or doji pattern, THE Scanner SHALL detect a reversal
6. WHEN volume confirms the bounce with at least 1.4x average, THE Scanner SHALL generate the signal
7. WHEN multiple touches strengthen the level (3+ touches), THE Scanner SHALL increase confidence score
8. WHERE the level aligns with round numbers (e.g., $30,000 for BTC, $2,000 for Gold), THE Scanner SHALL increase priority

### Requirement 7: Implement Key Level Break and Retest Strategy

**User Story:** As a trader, I want all scanners to detect key level breaks with retests, so that I can enter high-probability breakout trades.

#### Acceptance Criteria

1. WHEN the system identifies round numbers, previous highs/lows, or psychological levels, THE Scanner SHALL mark them as key levels
2. WHEN price breaks above a key resistance level with volume, THE Scanner SHALL monitor for a retest
3. WHEN price breaks below a key support level with volume, THE Scanner SHALL monitor for a retest
4. WHEN price retests the broken level and holds, THE Scanner SHALL generate a continuation signal
5. WHEN the retest occurs within 5-10 candles of the break, THE Scanner SHALL validate the signal
6. WHEN volume on the retest is at least 0.8x the breakout volume, THE Scanner SHALL confirm the signal
7. WHERE the key level is a major round number, THE Scanner SHALL require stronger confirmation (1.5x volume)

### Requirement 8: Implement ADX + RSI + Momentum Confluence Strategy

**User Story:** As a trader, I want all scanners to detect signals when ADX, RSI, and momentum align, so that I can enter trades with strong directional conviction and trend strength.

#### Acceptance Criteria

1. WHEN ADX is above 20, THE Scanner SHALL identify that a trend is forming or established
2. WHEN ADX is above 25, THE Scanner SHALL classify the trend as strong
3. WHEN RSI crosses above 50 in an uptrend, THE Scanner SHALL detect bullish momentum
4. WHEN RSI crosses below 50 in a downtrend, THE Scanner SHALL detect bearish momentum
5. WHEN RSI shows momentum acceleration (RSI change > 3 points over 2 candles), THE Scanner SHALL increase signal confidence
6. WHEN price momentum aligns with RSI direction (higher highs for bullish, lower lows for bearish), THE Scanner SHALL confirm the signal
7. WHEN volume exceeds 1.2x average, THE Scanner SHALL validate institutional participation
8. WHERE ADX is rising (current ADX > previous ADX), THE Scanner SHALL prioritize the signal as trend is strengthening
9. WHEN all three indicators align (ADX > 20, RSI directional, momentum confirmed), THE Scanner SHALL generate a high-confidence signal
10. WHEN ADX is below 18, THE Scanner SHALL reject momentum signals as market is too flat
11. WHERE RSI is in extreme zones (< 30 or > 70), THE Scanner SHALL require additional confirmation to avoid false signals

### Requirement 9: Implement Strategy Priority and Selection Logic

**User Story:** As a trader, I want the scanner to intelligently select the best strategy for current market conditions, so that I receive the highest quality signals.

#### Acceptance Criteria

1. WHEN multiple strategies detect signals simultaneously, THE Scanner SHALL evaluate each signal's confidence score
2. WHEN evaluating signals, THE Scanner SHALL prioritize strategies with higher confluence factors
3. WHEN market volatility is high (ATR > 1.5x average), THE Scanner SHALL prioritize momentum and breakout strategies
4. WHEN market volatility is low (ATR < 0.8x average), THE Scanner SHALL prioritize mean reversion and range strategies
5. WHEN a trend is established (ADX > 25), THE Scanner SHALL prioritize trend-following and ADX+RSI+Momentum strategies
6. WHEN market is ranging (ADX < 20), THE Scanner SHALL prioritize support/resistance and mean reversion strategies
7. WHEN the scanner detects conflicting signals, THE Scanner SHALL reject both signals to avoid whipsaws

### Requirement 10: Implement Strategy Configuration and Toggles

**User Story:** As a trader, I want to enable or disable specific strategies per scanner, so that I can customize signal detection based on my trading preferences.

#### Acceptance Criteria

1. WHEN the system loads configuration, THE Scanner SHALL read strategy enable/disable flags for each strategy
2. WHEN a strategy is disabled in configuration, THE Scanner SHALL skip that strategy during signal detection
3. WHEN all strategies are enabled, THE Scanner SHALL attempt detection using all strategies
4. WHEN configuration is updated, THE Scanner SHALL reload strategy settings without restart
5. WHERE strategy-specific parameters exist (e.g., Fibonacci levels, support/resistance lookback), THE Scanner SHALL load them from configuration

### Requirement 11: Maintain Backward Compatibility and Signal Quality

**User Story:** As a trader, I want new strategies to integrate seamlessly without degrading existing signal quality, so that my current trading setup remains reliable.

#### Acceptance Criteria

1. WHEN new strategies are added, THE Scanner SHALL maintain existing strategy behavior unchanged
2. WHEN generating signals, THE Scanner SHALL apply the same duplicate detection logic across all strategies
3. WHEN a signal is generated, THE Scanner SHALL include strategy name and reasoning in the alert
4. WHEN signal quality metrics are calculated, THE Scanner SHALL track performance per strategy
5. WHEN a strategy consistently produces low-quality signals, THE Scanner SHALL log warnings for review
