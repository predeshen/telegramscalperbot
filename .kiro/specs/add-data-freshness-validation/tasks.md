# Implementation Plan

- [x] 1. Add data freshness validation to MarketDataClient


  - Define FRESHNESS_THRESHOLDS dictionary with default thresholds for each timeframe
  - Create `validate_data_freshness()` method that checks if latest candle is within threshold
  - Calculate data age by comparing latest candle timestamp to current time
  - Return tuple of (is_fresh: bool, age_seconds: float)
  - Add logging for freshness check results (DEBUG level)
  - _Requirements: 1.1, 1.2, 3.1, 3.2_

- [x] 2. Modify get_latest_candles to include freshness validation


  - Add optional `validate_freshness` parameter (default: True)
  - Call `validate_data_freshness()` after fetching data
  - Return tuple of (DataFrame, is_fresh: bool) instead of just DataFrame
  - Log WARNING when stale data is detected with age and threshold
  - Maintain backward compatibility by making validation optional
  - _Requirements: 1.1, 1.2, 3.1, 3.2_

- [x] 3. Add state tracking attributes to scanner class


  - Add `last_fresh_data_time: Dict[str, datetime]` to track last fresh data per timeframe
  - Add `stale_data_count: Dict[str, int]` to count consecutive stale data occurrences
  - Add `last_stale_alert_time: Dict[str, datetime]` for alert deduplication
  - Add `last_trade_update_time: Optional[datetime]` to track trade update success
  - Add `last_known_price`, `last_known_price_time` for price caching
  - Add `trade_update_failure_count: int` to track consecutive failures
  - _Requirements: 2.2, 2.5, 4.4_

- [x] 4. Implement retry logic with exponential backoff


  - Create `_retry_fetch_with_backoff()` method with delays [5s, 10s, 30s]
  - Attempt to fetch data up to 3 times with increasing delays
  - Log each retry attempt with attempt number and delay
  - Return tuple of (DataFrame or None, is_fresh: bool)
  - Break early if fresh data is obtained
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 5. Create helper method to get current price for trade updates

  - Create `_get_current_price_for_trades()` method
  - Priority 1: Use latest candle from primary timeframe if fresh
  - Priority 2: Use cached price if less than 5 minutes old
  - Priority 3: Return None if no valid price available
  - Log which price source is being used (live, cached, or failed)
  - Update `last_known_price` and `last_known_price_time` when using live data
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 6. Restructure main loop to decouple trade updates from signal detection

  - Move trade update logic outside of signal detection block
  - Call `_get_current_price_for_trades()` to get best available price
  - Update trades even if signal detection fails or is skipped
  - Track `last_trade_update_time` on successful updates
  - Increment `trade_update_failure_count` on failures
  - Reset failure count to 0 on successful update
  - _Requirements: 2.1, 2.5_

- [x] 7. Implement stale data alert system


  - Create `_send_stale_data_alert()` method
  - Check if 3+ consecutive stale data occurrences for timeframe
  - Check deduplication: no alert sent within last 15 minutes
  - Format alert message with timeframe, data age, last fresh time, threshold
  - Include actionable information (check exchange API, verify connection)
  - Update `last_stale_alert_time` after sending alert
  - _Requirements: 1.4, 4.1, 4.2, 4.4, 4.5_

- [x] 8. Implement trade update failure alert system

  - Create `_send_trade_update_failure_alert()` method
  - Trigger after 3 consecutive trade update failures
  - Include last successful update time and active trade count
  - Send alert via Telegram alerter
  - Log alert sending at INFO level
  - _Requirements: 2.4_

- [x] 9. Implement recovery alert system

  - Create `_send_recovery_alert()` method for data freshness restoration
  - Trigger when fresh data is received after being stale
  - Include timeframe and duration of stale period
  - Reset `stale_data_count` to 0 for that timeframe
  - Log recovery at INFO level
  - _Requirements: 3.5, 4.3_

- [x] 10. Update main loop to integrate freshness validation


  - Modify data fetching to use new tuple return from `get_latest_candles()`
  - Check `is_fresh` flag before processing signals
  - Call `_retry_fetch_with_backoff()` when stale data detected
  - Call `_send_stale_data_alert()` after exhausted retries
  - Update `last_fresh_data_time` when fresh data received
  - Call `_send_recovery_alert()` when transitioning from stale to fresh
  - _Requirements: 1.3, 5.5_

- [x] 11. Add comprehensive logging for data freshness


  - Log data age and freshness status at DEBUG level for every fetch
  - Log WARNING when data exceeds threshold
  - Log INFO when skipping stale data
  - Log INFO when using cached data for trade updates
  - Log cache age when using cached price
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 12. Add unit tests for data freshness validation



  - Test `validate_data_freshness()` with fresh data (age < threshold)
  - Test `validate_data_freshness()` with stale data (age > threshold)
  - Test threshold calculation for different timeframes
  - Test edge case: data exactly at threshold
  - Test with missing or invalid timestamps
  - _Requirements: 1.1, 1.2_

- [x] 13. Add unit tests for retry logic


  - Test retry succeeds on first attempt
  - Test retry succeeds on second attempt after first fails
  - Test retry succeeds on third attempt after two failures
  - Test all retries fail and returns None
  - Test backoff delays are correct [5s, 10s, 30s]
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 14. Add unit tests for trade update fallback

  - Test using live price when available
  - Test using cached price when live unavailable and cache < 5 min
  - Test skipping update when cache > 5 min old
  - Test failure count increments correctly
  - Test failure count resets on success
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 15. Add integration test for end-to-end stale data handling


  - Simulate scanner receiving stale data
  - Verify retries are attempted with correct delays
  - Verify stale data alert is sent after 3 failures
  - Verify trades are still updated with cached price
  - Verify recovery alert sent when fresh data restored
  - _Requirements: 1.3, 1.4, 2.1, 4.1, 4.3_
