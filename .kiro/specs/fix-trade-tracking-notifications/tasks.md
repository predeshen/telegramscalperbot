# Implementation Plan

- [x] 1. Enhance trade ID generation with microseconds for uniqueness


  - Modify `add_trade()` method to include microseconds in timestamp
  - Update trade ID format from `{symbol}_{signal_type}_{YYYYMMDD_HHMMSS}` to `{symbol}_{signal_type}_{YYYYMMDD_HHMMSS_microseconds}`
  - Return the generated trade_id from `add_trade()` method
  - Add logging of generated trade ID
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 2. Add defensive validation for trade existence


  - Create `_validate_trade_exists()` helper method that checks if trade_id is in active_trades
  - Add validation calls at the start of `_close_trade()`, `_send_breakeven_update()`, `_send_stop_warning()`
  - Log error with active trade IDs when validation fails
  - Return early from methods if validation fails
  - _Requirements: 2.3, 2.4, 3.5, 5.5_

- [x] 3. Improve TP/SL detection with enhanced logging


  - Add DEBUG level logging in `_check_target_hit_extended()` showing comparison details
  - Log: signal type, current price, target price, comparison operator, and result
  - Add DEBUG level logging in `_check_stop_hit()` with same details
  - Add INFO level logging when TP or SL conditions are met
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.3, 4.4, 5.2, 5.3_

- [x] 4. Reorder notification checks to prioritize TP/SL


  - Restructure `update_trades()` to check TP/SL first before other notifications
  - Ensure `_check_target_hit_extended()` is called before breakeven/warning checks
  - Use `continue` statement after closing trade to skip remaining checks
  - Add comment explaining priority order
  - _Requirements: 1.3, 3.1, 3.4_

- [x] 5. Utilize target_notified flag to prevent duplicate TP notifications


  - Set `trade.target_notified = True` in `_close_trade()` when reason is "TARGET"
  - Check `trade.target_notified` before sending TP notification
  - Add logging when duplicate TP notification is prevented
  - _Requirements: 1.3, 3.2_

- [x] 6. Enhance _close_trade() with validation and logging


  - Add validation that trade_id exists in active_trades at start of method
  - Log detailed closure information: trade_id, reason, current_price, P&L, hold_time
  - Ensure trade is removed from active_trades after notification sent
  - Add error handling for missing trades
  - _Requirements: 1.4, 1.5, 2.4, 5.4_

- [x] 7. Add debug helper methods for troubleshooting


  - Create `debug_active_trades()` method that returns formatted string of all active trades
  - Create `get_trade_status()` method that returns trade details dict for a given trade_id
  - Include trade_id, entry_price, current status, notification flags in output
  - Add logging of active trade count in `update_trades()`
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 8. Add unit tests for TP detection


  - Write test for LONG trade TP hit detection
  - Write test for SHORT trade TP hit detection
  - Write test for extended TP detection
  - Write test for trade ID uniqueness
  - Write test for notification deduplication
  - _Requirements: 1.1, 1.2, 2.1, 3.2, 4.5_

- [x] 9. Add integration test for end-to-end TP flow



  - Create test that simulates full trade lifecycle from signal to TP hit
  - Verify "TARGET HIT" notification is sent
  - Verify trade is removed from active_trades
  - Verify trade is added to closed_trades with correct status
  - Test multiple concurrent trades on same symbol
  - _Requirements: 1.1, 1.2, 1.3, 2.2, 3.1_
