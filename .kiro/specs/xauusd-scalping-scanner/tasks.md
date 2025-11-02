# Implementation Plan - XAU/USD Scalping Scanner

- [x] 1. Set up Gold-specific project structure and configuration


  - Create `xauusd_scanner/` directory structure
  - Implement Gold-specific configuration loader
  - Create `config_gold.json` with XAU/USD parameters
  - Create `news_events.json` template for economic calendar
  - _Requirements: 11.5_

- [ ] 2. Implement Session Manager
  - [ ] 2.1 Create SessionManager class with GMT time handling
    - Implement `get_current_session()` to identify Asian/London/NY
    - Implement `is_active_session()` to determine if trading allowed
    - Add session transition logging and notifications
    - _Requirements: 1.3, 1.4, 1.5_
  
  - [ ] 2.2 Implement Asian range tracking
    - Track price high/low during Asian session (00:00-08:00 GMT)
    - Store Asian range at session end
    - Implement `get_asian_range()` to retrieve stored range
    - Reset range daily at Asian session start
    - _Requirements: 3.1_

- [ ] 3. Implement News Calendar
  - [ ] 3.1 Create NewsCalendar class with event management
    - Load events from JSON file
    - Implement `add_event()` for manual event addition
    - Implement `is_news_imminent()` to check 30-min window
    - Implement `should_pause_trading()` logic
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ] 3.2 Add news pause/resume notifications
    - Send Telegram alert when entering news pause
    - Send Telegram alert when resuming after news
    - Log all news-related pauses with event details
    - _Requirements: 2.4, 2.5_

- [ ] 4. Implement Spread Monitor
  - [ ] 4.1 Create SpreadMonitor class
    - Implement `update_spread()` to track bid-ask
    - Calculate spread in pips for Gold (multiply by 10)
    - Implement `is_spread_acceptable()` (< 10 pips)
    - Implement `should_pause_trading()` (> 15 pips)
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ] 4.2 Add spread monitoring to signal flow
    - Check spread before generating signals
    - Include current spread in all alerts
    - Send notification when spread too wide
    - Log spread violations
    - _Requirements: 8.4, 8.5_

- [ ] 5. Implement Key Level Tracker
  - [ ] 5.1 Create KeyLevelTracker class
    - Track daily high, low, previous close
    - Generate psychological round numbers (2350, 2400, 2450, etc.)
    - Implement `get_nearest_level()` to find closest level
    - Implement `is_near_level()` with 5-pip threshold
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 5.2 Integrate levels into signal reasoning
    - Include nearest key levels in signal alerts
    - Add level proximity to reasoning when within 5 pips
    - Prefer signals that align with level bounces/breaks
    - _Requirements: 10.4, 10.5_

- [ ] 6. Implement Strategy Selector
  - [ ] 6.1 Create StrategySelector class
    - Implement session-based strategy selection
    - Prioritize Asian Range Breakout during London open
    - Use EMA Cloud as primary during active sessions
    - Detect overextension for Mean Reversion opportunities
    - _Requirements: 3.1, 4.1, 5.1_

- [ ] 7. Implement Gold Signal Detector
  - [ ] 7.1 Create GoldSignalDetector base class
    - Extend from base SignalDetector
    - Add Gold-specific signal dataclass
    - Implement strategy routing logic
    - Add spread and session validation
    - _Requirements: 3.1, 4.1, 5.1_
  
  - [ ] 7.2 Implement Asian Range Breakout strategy
    - Detect breakout above/below Asian range
    - Wait for re-test of broken level
    - Confirm with pin bar or engulfing candle
    - Validate volume > 1.2x average
    - Calculate entry, stop (tight), target (1.5x ATR)
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 7.3 Implement EMA Cloud Breakout strategy
    - Check EMA(20) and EMA(50) alignment
    - Validate price vs VWAP for institutional bias
    - Detect range breakout with volume confirmation
    - Validate RSI 25-75 range
    - Calculate entry, stop (1.2x ATR), target (1.5x ATR)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 7.4 Implement Mean Reversion strategy
    - Detect overextension (> 1.5x ATR from VWAP)
    - Check RSI extremes (> 75 or < 25)
    - Wait for reversal candle (pin bar, doji, engulfing)
    - Validate volume confirms reversal
    - Set target at VWAP for mean reversion
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 7.5 Generate Gold-specific reasoning
    - Include strategy name and session context
    - Explain Asian range if applicable
    - List all confluence factors with details
    - Add key level proximity information
    - Explain why to enter NOW with institutional context
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 8. Implement Trade Management for Gold
  - [ ] 8.1 Extend TradeTracker for Gold-specific features
    - Track strategy type for each trade
    - Monitor session changes during trade
    - Check spread widening during trade
    - Add session-end warnings
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 8.2 Add Gold-specific trade updates
    - Breakeven notification with spread check
    - Target approach with session time remaining
    - Stop warning with spread status
    - Session-end warning if trade still open
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 9. Implement Dynamic Risk Management
  - [ ] 9.1 Create RiskCalculator for Gold
    - Calculate stop-loss as entry ± (1.2 × ATR)
    - Calculate take-profit as entry ± (1.5 × ATR) for breakouts
    - Calculate take-profit as VWAP for mean reversion
    - Calculate risk-reward ratio
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ] 9.2 Add position sizing recommendations
    - Calculate position size for 0.5% account risk
    - Include in signal alerts
    - Adjust for spread cost
    - _Requirements: 9.5_

- [ ] 10. Create main Gold scanner application
  - [ ] 10.1 Implement main orchestrator
    - Initialize all Gold-specific components
    - Integrate SessionManager into main loop
    - Add NewsCalendar checks before signal detection
    - Add SpreadMonitor checks before signal detection
    - Route to appropriate strategy based on session
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ] 10.2 Add session-aware processing
    - Reduce frequency during Asian session (30s intervals)
    - Full-speed processing during London/NY (every candle)
    - Log session transitions
    - Send session change notifications
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [ ] 10.3 Implement graceful shutdown
    - Close all connections cleanly
    - Save Asian range state
    - Log final session summary
    - _Requirements: 11.5_

- [ ] 11. Create deployment artifacts for Gold
  - [ ] 11.1 Write systemd service file for Gold scanner
    - Create `xauusd-scanner.service`
    - Configure for Gold-specific paths
    - Set appropriate restart policy
    - _Requirements: 11.1_
  
  - [ ] 11.2 Create installation script
    - Install Gold-specific dependencies
    - Set up news calendar file
    - Configure session time zones
    - _Requirements: 11.5_
  
  - [ ] 11.3 Write Gold-specific README
    - Document session trading hours
    - Explain news calendar maintenance
    - Provide spread monitoring guide
    - Include strategy descriptions
    - _Requirements: 11.5_

- [ ] 12. Create test suite for Gold scanner
  - [ ] 12.1 Write unit tests for session management
    - Test session detection at various GMT times
    - Test Asian range tracking and storage
    - Test session transition logic
    - _Requirements: 1.3, 1.4, 1.5_
  
  - [ ] 12.2 Write unit tests for news calendar
    - Test event loading from JSON
    - Test news imminence detection
    - Test pause/resume logic
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ] 12.3 Write unit tests for spread monitoring
    - Test spread calculation in pips
    - Test acceptable/unacceptable thresholds
    - Test pause logic
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ] 12.4 Write unit tests for each strategy
    - Test Asian Range Breakout detection
    - Test EMA Cloud Breakout detection
    - Test Mean Reversion detection
    - Test strategy selection logic
    - _Requirements: 3.1-3.5, 4.1-4.5, 5.1-5.5_
  
  - [ ] 12.5 Write integration test for full Gold signal flow
    - Mock Gold market data with session transitions
    - Test news pause functionality
    - Test spread-based pause
    - Verify Telegram alerts with Gold-specific formatting
    - _Requirements: 1.1, 2.1, 8.1_

- [ ] 13. Integration and validation
  - [ ] 13.1 Deploy to test environment
    - Run during London session
    - Verify session detection
    - Confirm news calendar works
    - Check spread monitoring
    - _Requirements: 11.1, 11.2_
  
  - [ ] 13.2 Validate signal quality
    - Review Asian Range Breakout signals
    - Review EMA Cloud signals
    - Review Mean Reversion signals
    - Verify reasoning quality
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 13.3 Test trade management
    - Verify breakeven notifications
    - Verify target/stop notifications
    - Test session-end warnings
    - Validate P&L calculations
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
