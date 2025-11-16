"""Trade tracking and management for open positions."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict
from collections import deque
import logging

from src.signal_detector import Signal


logger = logging.getLogger(__name__)


@dataclass
class TradeStatus:
    """Status of an active trade."""
    signal: Signal
    entry_time: datetime
    breakeven_notified: bool = False
    target_notified: bool = False
    stop_warning_sent: bool = False
    tp_extension_notified: bool = False
    momentum_reversal_notified: bool = False
    extended_tp: Optional[float] = None
    highest_price: float = 0.0  # Track highest price for LONG trades
    lowest_price: float = float('inf')  # Track lowest price for SHORT trades
    peak_profit_percent: float = 0.0  # Track peak profit percentage
    last_exit_signal_time: Optional[datetime] = None  # Track last exit signal time
    exit_signal_count: int = 0  # Count of exit signals sent
    status: str = "ACTIVE"  # ACTIVE, CLOSED_TP, CLOSED_SL, EXTENDED
    symbol: str = "BTC/USD"  # Trading symbol for per-symbol tracking


class TradeTracker:
    """
    Track active trades and send management updates.
    
    Monitors price movement and sends notifications for:
    - Breakeven level reached (move stop)
    - Target reached (close trade)
    - Stop-loss approaching (warning)
    - Trade closed (final P&L)
    
    Enhanced with:
    - Grace period enforcement (30 minutes before exit evaluation)
    - Minimum profit thresholds for exit signals
    - Per-symbol trade tracking
    - Strict exit conditions (no exits on negative P&L)
    """
    
    def __init__(
        self,
        alerter,
        grace_period_minutes: int = 5,
        min_profit_threshold_crypto: float = 1.0,
        min_profit_threshold_fx: float = 0.3,
        max_giveback_percent: float = 40.0,
        min_peak_profit_for_exit: float = 2.0,
        duplicate_exit_window_minutes: int = 10
    ):
        """
        Initialize trade tracker.
        
        Args:
            alerter: Alerter instance for sending updates
            grace_period_minutes: Minimum time before evaluating exit conditions (default: 5 minutes)
            min_profit_threshold_crypto: Minimum profit % for crypto exit signals
            min_profit_threshold_fx: Minimum profit % for FX exit signals
            max_giveback_percent: Maximum giveback % before exit signal
            min_peak_profit_for_exit: Minimum peak profit % required for exit evaluation
            duplicate_exit_window_minutes: Minimum time between duplicate exit signals
        """
        self.alerter = alerter
        self.active_trades: Dict[str, TradeStatus] = {}  # Per-symbol tracking
        self.closed_trades: deque = deque(maxlen=100)
        
        # Enhanced exit rules
        self.grace_period_minutes = grace_period_minutes
        self.min_profit_threshold_crypto = min_profit_threshold_crypto
        self.min_profit_threshold_fx = min_profit_threshold_fx
        
        # Win rate tracking per symbol
        self.symbol_trade_history: Dict[str, deque] = {}  # symbol -> deque of (win: bool, profit_pct: float)
        self.max_history_per_symbol = 20  # Track last 20 trades per symbol
        self.max_giveback_percent = max_giveback_percent
        self.min_peak_profit_for_exit = min_peak_profit_for_exit
        self.duplicate_exit_window_minutes = duplicate_exit_window_minutes
        
        logger.info(f"Initialized Enhanced TradeTracker (grace_period={grace_period_minutes}m, "
                   f"min_profit_crypto={min_profit_threshold_crypto}%, min_profit_fx={min_profit_threshold_fx}%)")
    
    def add_trade(self, signal: Signal, symbol: Optional[str] = None) -> None:
        """
        Add a new trade to tracking (per-symbol).
        
        Args:
            signal: Signal that was just generated
            symbol: Trading symbol (optional, extracted from signal if not provided)
        """
        # Extract symbol from signal or use provided
        if symbol is None:
            symbol = getattr(signal, 'symbol', 'BTC/USD')
        
        trade_id = f"{symbol}_{signal.signal_type}_{signal.timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        trade_status = TradeStatus(
            signal=signal,
            entry_time=datetime.now(),
            highest_price=signal.entry_price,  # Initialize with entry price
            lowest_price=signal.entry_price,   # Initialize with entry price
            symbol=symbol
        )
        
        self.active_trades[trade_id] = trade_status
        logger.info(f"Added trade to tracking: {trade_id} at ${signal.entry_price:.2f}")
    
    def update_trades(self, current_price: float, indicators: Optional[Dict] = None) -> None:
        """
        Update all active trades with current price and send notifications.
        
        Args:
            current_price: Current market price
            indicators: Optional dict with current RSI, ADX, volume_ratio for TP extension logic
        """
        for trade_id, trade in list(self.active_trades.items()):
            signal = trade.signal
            
            # Update price tracking for momentum reversal detection
            if signal.signal_type == "LONG":
                trade.highest_price = max(trade.highest_price, current_price)
            else:  # SHORT
                trade.lowest_price = min(trade.lowest_price, current_price)
            
            # Use extended TP if available
            target_price = trade.extended_tp if trade.extended_tp else signal.take_profit
            
            # Check if trade should be closed
            if self._check_target_hit_extended(signal, current_price, trade, target_price):
                self._close_trade(trade_id, "TARGET", current_price)
                continue
            
            if self._check_stop_hit(signal, current_price, trade):
                self._close_trade(trade_id, "STOP", current_price)
                continue
            
            # Check for TP extension opportunity (before hitting original TP)
            if not trade.tp_extension_notified and indicators:
                if self._should_extend_tp(signal, current_price, trade, indicators):
                    self._send_tp_extension_alert(signal, current_price, trade, indicators)
                    trade.tp_extension_notified = True
            
            # Check for momentum reversal (EXIT signal)
            if indicators and not trade.momentum_reversal_notified:
                if self._check_momentum_reversal(signal, current_price, trade, indicators):
                    self._send_momentum_reversal_alert(signal, current_price, indicators, trade)
                    trade.momentum_reversal_notified = True
            
            # Check for management updates
            if not trade.breakeven_notified:
                if self._check_breakeven_reached(signal, current_price):
                    self._send_breakeven_update(signal, current_price, trade)
                    trade.breakeven_notified = True
            
            if not trade.stop_warning_sent:
                if self._check_stop_approaching(signal, current_price):
                    self._send_stop_warning(signal, current_price)
                    trade.stop_warning_sent = True
    
    def _check_target_hit(self, signal: Signal, current_price: float, trade: TradeStatus) -> bool:
        """Check if take-profit target was hit."""
        if signal.signal_type == "LONG":
            return current_price >= signal.take_profit
        else:
            return current_price <= signal.take_profit
    
    def _check_target_hit_extended(self, signal: Signal, current_price: float, trade: TradeStatus, target_price: float) -> bool:
        """Check if take-profit target (original or extended) was hit."""
        if signal.signal_type == "LONG":
            return current_price >= target_price
        else:
            return current_price <= target_price
    
    def _check_stop_hit(self, signal: Signal, current_price: float, trade: TradeStatus) -> bool:
        """Check if stop-loss was hit."""
        if signal.signal_type == "LONG":
            return current_price <= signal.stop_loss
        else:
            return current_price >= signal.stop_loss
    
    def _check_breakeven_reached(self, signal: Signal, current_price: float) -> bool:
        """Check if price reached 50% to target (breakeven level)."""
        breakeven = signal.get_breakeven_price()
        
        if signal.signal_type == "LONG":
            return current_price >= breakeven
        else:
            return current_price <= breakeven
    
    def _check_stop_approaching(self, signal: Signal, current_price: float) -> bool:
        """Check if price is within 20% of stop-loss."""
        distance_to_stop = abs(current_price - signal.stop_loss)
        total_risk = abs(signal.entry_price - signal.stop_loss)
        
        return distance_to_stop < (total_risk * 0.2)
    
    def _check_momentum_reversal(self, signal: Signal, current_price: float, trade: TradeStatus, indicators: Dict) -> bool:
        """
        Check if momentum is reversing - signal to EXIT the trade.
        
        ENHANCED with strict exit rules:
        1. Grace period: Must wait 30 minutes after entry
        2. Minimum profit: Current profit must be positive and > threshold
        3. Peak profit: Peak profit must have exceeded minimum threshold
        4. Giveback: Only exit when giving back > 40% of peak profit
        5. Duplicate prevention: No duplicate exit signals within 10 minutes
        
        Original criteria for EXIT alert:
        1. Trade was in significant profit (reached 70%+ to target)
        2. Now giving back gains (dropped 50%+ from highest/lowest)
        3. RSI showing reversal (overbought for LONG, oversold for SHORT)
        4. RSI divergence (price higher but RSI lower for LONG, vice versa for SHORT)
        5. Volume declining significantly (< 0.8x average)
        
        Args:
            signal: Original signal
            current_price: Current price
            trade: Trade status
            indicators: Dict with 'rsi', 'prev_rsi', 'volume_ratio'
            
        Returns:
            True if momentum reversal detected
        """
        # STRICT RULE 1: Grace period enforcement
        time_since_entry = datetime.now() - trade.entry_time
        if time_since_entry < timedelta(minutes=self.grace_period_minutes):
            logger.debug(f"Grace period active: {time_since_entry.total_seconds()/60:.1f}m / {self.grace_period_minutes}m")
            return False
        
        # STRICT RULE 2: Check duplicate exit signal prevention
        if trade.last_exit_signal_time:
            time_since_last_exit = datetime.now() - trade.last_exit_signal_time
            if time_since_last_exit < timedelta(minutes=self.duplicate_exit_window_minutes):
                logger.debug(f"Duplicate exit signal suppressed: {time_since_last_exit.total_seconds()/60:.1f}m since last")
                return False
        
        # Calculate current profit
        if signal.signal_type == "LONG":
            current_profit_pct = ((current_price - signal.entry_price) / signal.entry_price) * 100
            peak_profit_pct = ((trade.highest_price - signal.entry_price) / signal.entry_price) * 100
        else:
            current_profit_pct = ((signal.entry_price - current_price) / signal.entry_price) * 100
            peak_profit_pct = ((signal.entry_price - trade.lowest_price) / signal.entry_price) * 100
        
        # Update peak profit tracking
        trade.peak_profit_percent = max(trade.peak_profit_percent, peak_profit_pct)
        
        # STRICT RULE 3: Current profit must be positive
        if current_profit_pct <= 0:
            logger.debug(f"Exit suppressed: Current profit is negative ({current_profit_pct:.2f}%)")
            return False
        
        # STRICT RULE 4: Peak profit must have exceeded minimum threshold
        # Determine threshold based on asset type (crypto vs fx)
        # For now, assume crypto (can be enhanced with asset type detection)
        min_threshold = self.min_profit_threshold_crypto
        if trade.peak_profit_percent < min_threshold:
            logger.debug(f"Exit suppressed: Peak profit {trade.peak_profit_percent:.2f}% < threshold {min_threshold}%")
            return False
        
        # STRICT RULE 5: Must be giving back significant gains
        giveback_pct = ((trade.peak_profit_percent - current_profit_pct) / trade.peak_profit_percent) * 100 if trade.peak_profit_percent > 0 else 0
        
        if giveback_pct < self.max_giveback_percent:
            logger.debug(f"Exit suppressed: Giveback {giveback_pct:.1f}% < threshold {self.max_giveback_percent}%")
            return False
        
        # If we reach here, strict rules are satisfied - now check momentum indicators
        rsi = indicators.get('rsi', 50)
        prev_rsi = indicators.get('prev_rsi', 50)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        
        reversal_detected = False
        
        if signal.signal_type == "LONG":
            # Check if trade reached significant profit
            profit_from_entry = trade.highest_price - signal.entry_price
            target_distance = signal.take_profit - signal.entry_price
            reached_pct = (profit_from_entry / target_distance) if target_distance > 0 else 0
            
            # Check if giving back gains
            drawdown_from_high = trade.highest_price - current_price
            giving_back_pct = (drawdown_from_high / profit_from_entry) if profit_from_entry > 0 else 0
            
            # CRITICAL: If trade reached 70%+ to target and now giving back 50%+ of gains
            if reached_pct >= 0.7 and giving_back_pct >= 0.5:
                reversal_detected = True
                logger.warning(f"Momentum reversal: Reached {reached_pct*100:.0f}% to target, giving back {giving_back_pct*100:.0f}% of gains")
            
            # Check for bearish reversal signals (even if back in loss)
            elif rsi > 70:  # Overbought
                reversal_detected = True
            elif rsi < prev_rsi - 5 and current_price > trade.highest_price * 0.95:  # RSI falling sharply
                reversal_detected = True
                
        else:  # SHORT
            # Check if trade reached significant profit
            profit_from_entry = signal.entry_price - trade.lowest_price
            target_distance = signal.entry_price - signal.take_profit
            reached_pct = (profit_from_entry / target_distance) if target_distance > 0 else 0
            
            # Check if giving back gains
            drawdown_from_low = current_price - trade.lowest_price
            giving_back_pct = (drawdown_from_low / profit_from_entry) if profit_from_entry > 0 else 0
            
            # CRITICAL: If trade reached 70%+ to target and now giving back 50%+ of gains
            if reached_pct >= 0.7 and giving_back_pct >= 0.5:
                reversal_detected = True
                logger.warning(f"Momentum reversal: Reached {reached_pct*100:.0f}% to target, giving back {giving_back_pct*100:.0f}% of gains")
            
            # Check for bullish reversal signals (even if back in loss)
            elif rsi < 30:  # Oversold
                reversal_detected = True
            elif rsi > prev_rsi + 5 and current_price < trade.lowest_price * 1.05:  # RSI rising sharply
                reversal_detected = True
        
        # Volume declining is a warning sign
        if volume_ratio < 0.8 and reached_pct >= 0.5:
            reversal_detected = True
        
        return reversal_detected
    
    def _send_momentum_reversal_alert(self, signal: Signal, current_price: float, indicators: Dict, trade: TradeStatus) -> None:
        """Send EXIT NOW alert when momentum reverses."""
        # Update exit signal tracking
        trade.last_exit_signal_time = datetime.now()
        trade.exit_signal_count += 1
        
        rsi = indicators.get('rsi', 0)
        volume_ratio = indicators.get('volume_ratio', 0)
        
        # Calculate current profit/loss
        if signal.signal_type == "LONG":
            profit_pct = ((current_price - signal.entry_price) / signal.entry_price) * 100
            best_profit = ((trade.highest_price - signal.entry_price) / signal.entry_price) * 100
            giving_back = best_profit - profit_pct
        else:
            profit_pct = ((signal.entry_price - current_price) / signal.entry_price) * 100
            best_profit = ((signal.entry_price - trade.lowest_price) / signal.entry_price) * 100
            giving_back = best_profit - profit_pct
        
        status_emoji = "💰" if profit_pct > 0 else "⚠️"
        
        message = f"""
🚨 *EXIT SIGNAL - MOMENTUM REVERSAL!*

{signal.signal_type} from ${signal.entry_price:,.2f}
Current Price: ${current_price:,.2f}
Current P&L: {profit_pct:+.2f}%

*📊 TRADE ANALYSIS:*
{status_emoji} Best Profit: +{best_profit:.2f}%
🔴 Giving Back: {giving_back:.2f}%
{'🔴 RSI Overbought: ' + f'{rsi:.1f}' if signal.signal_type == 'LONG' and rsi > 70 else ''}
{'🔴 RSI Oversold: ' + f'{rsi:.1f}' if signal.signal_type == 'SHORT' and rsi < 30 else ''}
🔴 Volume: {volume_ratio:.2f}x (momentum fading)

*🚪 RECOMMENDED ACTION:*
EXIT NOW at market price ${current_price:,.2f}

*⚠️ WHY EXIT:*
• Trade reached +{best_profit:.1f}% profit
• Now giving back {giving_back:.1f}% of gains
• Momentum has reversed
• Don't let a winner turn into a loser!

The smart move is to exit now and preserve capital for the next setup.

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        self.alerter.send_message(message)
        logger.info(f"Sent momentum reversal EXIT alert for {signal.signal_type} trade at ${current_price:,.2f} (Current: {profit_pct:+.2f}%, Best: +{best_profit:.2f}%)")
    
    def _should_extend_tp(self, signal: Signal, current_price: float, trade: TradeStatus, indicators: Dict) -> bool:
        """
        Check if TP should be extended based on strong continuation signals.
        
        Criteria for extension:
        1. Price within 80-95% of original TP (approaching but not hit yet)
        2. RSI still has room (not overbought/oversold)
        3. ADX > 25 (strong trend)
        4. Volume still elevated (> 1.0x average)
        5. RSI direction aligned with trade (rising for LONG, falling for SHORT)
        
        Args:
            signal: Original signal
            current_price: Current price
            trade: Trade status
            indicators: Dict with 'rsi', 'adx', 'volume_ratio', 'prev_rsi'
            
        Returns:
            True if TP should be extended
        """
        # Check if price is approaching TP (80-95% of the way)
        if signal.signal_type == "LONG":
            distance_to_tp = signal.take_profit - current_price
            total_move = signal.take_profit - signal.entry_price
            progress = 1 - (distance_to_tp / total_move) if total_move != 0 else 0
            
            if not (0.80 <= progress <= 0.95):
                return False
            
            # Check RSI has room (not overbought)
            rsi = indicators.get('rsi', 50)
            if rsi > 70:
                return False
            
            # Check RSI is rising
            prev_rsi = indicators.get('prev_rsi', rsi)
            if rsi <= prev_rsi:
                return False
            
        else:  # SHORT
            distance_to_tp = current_price - signal.take_profit
            total_move = signal.entry_price - signal.take_profit
            progress = 1 - (distance_to_tp / total_move) if total_move != 0 else 0
            
            if not (0.80 <= progress <= 0.95):
                return False
            
            # Check RSI has room (not oversold)
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                return False
            
            # Check RSI is falling
            prev_rsi = indicators.get('prev_rsi', rsi)
            if rsi >= prev_rsi:
                return False
        
        # Check ADX shows strong trend
        adx = indicators.get('adx', 0)
        if adx < 25:
            return False
        
        # Check volume still elevated
        volume_ratio = indicators.get('volume_ratio', 0)
        if volume_ratio < 1.0:
            return False
        
        logger.info(f"TP extension criteria met: RSI={rsi:.1f}, ADX={adx:.1f}, Volume={volume_ratio:.2f}x, Progress={progress*100:.1f}%")
        return True
    
    def _send_tp_extension_alert(self, signal: Signal, current_price: float, trade: TradeStatus, indicators: Dict) -> None:
        """Send alert to hold and extend TP."""
        # Calculate extended TP (add another 1.5x ATR)
        if signal.signal_type == "LONG":
            extended_tp = signal.take_profit + (signal.atr * 1.5)
        else:
            extended_tp = signal.take_profit - (signal.atr * 1.5)
        
        trade.extended_tp = extended_tp
        trade.status = "EXTENDED"
        
        rsi = indicators.get('rsi', 0)
        adx = indicators.get('adx', 0)
        volume_ratio = indicators.get('volume_ratio', 0)
        
        message = f"""
🚀 *TRADE UPDATE: EXTEND TARGET - HOLD!*

{signal.signal_type} from ${signal.entry_price:,.2f}
Current Price: ${current_price:,.2f}

*🎯 STRONG CONTINUATION DETECTED:*
✅ RSI: {rsi:.1f} - Still has room to run
✅ ADX: {adx:.1f} - Strong trend strength
✅ Volume: {volume_ratio:.2f}x - Institutional flow continues
✅ Price approaching TP with momentum

*📈 RECOMMENDED ACTION:*
🔸 Original TP: ${signal.take_profit:,.2f}
🔸 Extended TP: ${extended_tp:,.2f} (+{abs(extended_tp - signal.take_profit):.2f})

*💡 TRADE MANAGEMENT:*
• HOLD your position - don't close at original TP
• Move stop to ${signal.entry_price:,.2f} (breakeven) if not done
• New target: ${extended_tp:,.2f}
• Trail stop as price moves in your favor

This is a runner! The trend is strong and likely to continue past your original target.

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        self.alerter.send_message(message)
        logger.info(f"Sent TP extension alert for {signal.signal_type} trade: ${signal.take_profit:,.2f} -> ${extended_tp:,.2f}")
    
    def _send_breakeven_update(self, signal: Signal, current_price: float, trade: TradeStatus) -> None:
        """Send notification to move stop to breakeven."""
        breakeven = signal.get_breakeven_price()
        
        message = f"""
🎯 *TRADE UPDATE: Move Stop to Breakeven*

{signal.signal_type} from ${signal.entry_price:,.2f}
Current Price: ${current_price:,.2f}

✅ *ACTION REQUIRED:*
Move your stop-loss to ${signal.entry_price:,.2f} (breakeven)

This locks in a risk-free trade. If price reverses, you exit at breakeven. If it continues, you're still in for the full target at ${signal.take_profit:,.2f}.

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        self.alerter.send_message(message)
        
        # Update the signal's stop-loss to breakeven for tracking
        signal.stop_loss = signal.entry_price
        
        # Disable momentum exit signals after reaching breakeven
        trade.momentum_reversal_notified = True
        
        logger.info(f"Sent breakeven update for {signal.signal_type} trade - stop moved to ${signal.entry_price:,.2f}, momentum exits disabled")
    
    def _send_stop_warning(self, signal: Signal, current_price: float) -> None:
        """Send warning that stop-loss is approaching."""
        message = f"""
⚠️ *TRADE WARNING: Stop-Loss Approaching*

{signal.signal_type} from ${signal.entry_price:,.2f}
Current Price: ${current_price:,.2f}
Stop Loss: ${signal.stop_loss:,.2f}

Price is moving against your position. Prepare for potential stop-out.

💡 *Options:*
• Hold and let stop-loss protect you
• Close manually if you see weakness
• Do NOT move stop further away!

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        self.alerter.send_message(message)
        logger.info(f"Sent stop warning for {signal.signal_type} trade")
    
    def _close_trade(self, trade_id: str, reason: str, current_price: float) -> None:
        """
        Close a trade and send final update.
        
        Args:
            trade_id: Trade identifier
            reason: "TARGET" or "STOP"
            current_price: Price at close
        """
        trade = self.active_trades[trade_id]
        signal = trade.signal
        
        # Calculate P&L
        if signal.signal_type == "LONG":
            pnl_points = current_price - signal.entry_price
        else:
            pnl_points = signal.entry_price - current_price
        
        pnl_percent = (pnl_points / signal.entry_price) * 100
        
        # Determine emoji and message
        if reason == "TARGET":
            emoji = "🎉"
            status = "TARGET HIT - WINNER!"
            trade.status = "CLOSED_TP"
        else:
            emoji = "🛑"
            status = "STOP-LOSS HIT"
            trade.status = "CLOSED_SL"
        
        # Calculate hold time
        hold_time = datetime.now() - trade.entry_time
        minutes = int(hold_time.total_seconds() / 60)
        
        # Calculate R:R achieved (handle breakeven case where SL = entry)
        risk = abs(signal.entry_price - signal.stop_loss)
        rr_achieved = abs(pnl_points / risk) if risk > 0 else 0.0
        
        message = f"""
{emoji} *TRADE CLOSED: {status}*

{signal.signal_type} from ${signal.entry_price:,.2f}
Exit Price: ${current_price:,.2f}

*📊 RESULTS:*
P&L: ${pnl_points:,.2f} ({pnl_percent:+.2f}%)
Hold Time: {minutes} minutes
R:R Achieved: {rr_achieved:.2f}

*💡 NEXT STEPS:*
{"✅ Great trade! Wait for next setup." if reason == "TARGET" else "✅ Stop protected you. Wait for next setup."}

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        self.alerter.send_message(message)
        logger.info(f"Closed trade {trade_id}: {reason}, P&L: {pnl_percent:.2f}%")
        
        # Record trade result for win rate tracking
        is_win = (reason == "TARGET")
        self._record_trade_result(signal.symbol, is_win, pnl_percent)
        
        # Move to closed trades
        self.closed_trades.append(trade)
        del self.active_trades[trade_id]
    
    def get_active_count(self) -> int:
        """Get number of active trades."""
        return len(self.active_trades)
    
    def get_closed_count(self) -> int:
        """Get number of closed trades."""
        return len(self.closed_trades)

    def _record_trade_result(self, symbol: str, is_win: bool, profit_pct: float) -> None:
        """
        Record trade result for win rate tracking.
        
        Args:
            symbol: Trading symbol
            is_win: Whether trade was a winner
            profit_pct: Profit percentage
        """
        if symbol not in self.symbol_trade_history:
            self.symbol_trade_history[symbol] = deque(maxlen=self.max_history_per_symbol)
        
        self.symbol_trade_history[symbol].append((is_win, profit_pct))
        logger.debug(f"Recorded trade result for {symbol}: {'WIN' if is_win else 'LOSS'} ({profit_pct:.2f}%)")
    
    def get_symbol_win_rate(self, symbol: str) -> Optional[float]:
        """
        Get win rate for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Win rate as percentage (0-100) or None if insufficient data
        """
        if symbol not in self.symbol_trade_history:
            return None
        
        history = self.symbol_trade_history[symbol]
        if len(history) < 5:  # Need at least 5 trades for meaningful win rate
            return None
        
        wins = sum(1 for is_win, _ in history if is_win)
        total = len(history)
        win_rate = (wins / total) * 100
        
        return win_rate
    
    def get_dynamic_confidence_adjustment(self, symbol: str) -> int:
        """
        Get confidence adjustment based on recent win rate.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Confidence adjustment (-1, 0, or +1)
        """
        win_rate = self.get_symbol_win_rate(symbol)
        
        if win_rate is None:
            return 0  # No adjustment if insufficient data
        
        if win_rate > 60:
            return -1  # Reduce min_confidence (more lenient)
        elif win_rate < 40:
            return +1  # Increase min_confidence (more strict)
        else:
            return 0  # No adjustment
