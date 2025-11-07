"""Trade tracking and management for open positions."""
from dataclasses import dataclass
from datetime import datetime
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
    status: str = "ACTIVE"  # ACTIVE, CLOSED_TP, CLOSED_SL, EXTENDED


class TradeTracker:
    """
    Track active trades and send management updates.
    
    Monitors price movement and sends notifications for:
    - Breakeven level reached (move stop)
    - Target reached (close trade)
    - Stop-loss approaching (warning)
    - Trade closed (final P&L)
    """
    
    def __init__(self, alerter):
        """
        Initialize trade tracker.
        
        Args:
            alerter: Alerter instance for sending updates
        """
        self.alerter = alerter
        self.active_trades: Dict[str, TradeStatus] = {}
        self.closed_trades: deque = deque(maxlen=100)
        
        logger.info("Initialized TradeTracker")
    
    def add_trade(self, signal: Signal) -> None:
        """
        Add a new trade to tracking.
        
        Args:
            signal: Signal that was just generated
        """
        trade_id = f"{signal.signal_type}_{signal.timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        trade_status = TradeStatus(
            signal=signal,
            entry_time=datetime.now(),
            highest_price=signal.entry_price,  # Initialize with entry price
            lowest_price=signal.entry_price    # Initialize with entry price
        )
        
        self.active_trades[trade_id] = trade_status
        logger.info(f"Added trade to tracking: {trade_id}")
    
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
                    self._send_momentum_reversal_alert(signal, current_price, indicators)
                    trade.momentum_reversal_notified = True
            
            # Check for management updates
            if not trade.breakeven_notified:
                if self._check_breakeven_reached(signal, current_price):
                    self._send_breakeven_update(signal, current_price)
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
        
        Criteria for EXIT alert:
        1. Trade is in profit (past breakeven)
        2. RSI showing reversal (overbought for LONG, oversold for SHORT)
        3. RSI divergence (price higher but RSI lower for LONG, vice versa for SHORT)
        4. Volume declining significantly (< 0.8x average)
        
        Args:
            signal: Original signal
            current_price: Current price
            trade: Trade status
            indicators: Dict with 'rsi', 'prev_rsi', 'volume_ratio'
            
        Returns:
            True if momentum reversal detected
        """
        # Only check if trade is in profit
        if signal.signal_type == "LONG":
            if current_price <= signal.entry_price:
                return False
        else:
            if current_price >= signal.entry_price:
                return False
        
        rsi = indicators.get('rsi', 50)
        prev_rsi = indicators.get('prev_rsi', 50)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        
        reversal_detected = False
        
        if signal.signal_type == "LONG":
            # Check for bearish reversal signals
            if rsi > 70:  # Overbought
                reversal_detected = True
            elif rsi < prev_rsi and current_price > trade.highest_price * 0.99:  # RSI falling while price flat/up
                reversal_detected = True
        else:  # SHORT
            # Check for bullish reversal signals
            if rsi < 30:  # Oversold
                reversal_detected = True
            elif rsi > prev_rsi and current_price < trade.lowest_price * 1.01:  # RSI rising while price flat/down
                reversal_detected = True
        
        # Volume declining is a warning sign
        if volume_ratio < 0.8:
            reversal_detected = True
        
        return reversal_detected
    
    def _send_momentum_reversal_alert(self, signal: Signal, current_price: float, indicators: Dict) -> None:
        """Send EXIT NOW alert when momentum reverses."""
        rsi = indicators.get('rsi', 0)
        volume_ratio = indicators.get('volume_ratio', 0)
        
        # Calculate current profit
        if signal.signal_type == "LONG":
            profit_pct = ((current_price - signal.entry_price) / signal.entry_price) * 100
        else:
            profit_pct = ((signal.entry_price - current_price) / signal.entry_price) * 100
        
        message = f"""
🚨 *EXIT SIGNAL - MOMENTUM REVERSAL DETECTED!*

{signal.signal_type} from ${signal.entry_price:,.2f}
Current Price: ${current_price:,.2f}
Current Profit: {profit_pct:+.2f}%

*⚠️ REVERSAL SIGNALS:*
{'🔴 RSI Overbought: ' + f'{rsi:.1f}' if signal.signal_type == 'LONG' and rsi > 70 else ''}
{'🔴 RSI Oversold: ' + f'{rsi:.1f}' if signal.signal_type == 'SHORT' and rsi < 30 else ''}
🔴 Volume Declining: {volume_ratio:.2f}x (momentum fading)
🔴 Price action showing exhaustion

*📉 RECOMMENDED ACTION:*
🚪 EXIT NOW at market price
💰 Lock in your {profit_pct:+.2f}% profit
⚠️ Momentum is reversing - don't give back gains!

*Why exit now?*
The indicators that got you into this trade are now showing reversal. The smart move is to take profit and wait for the next high-probability setup.

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        self.alerter.send_message(message)
        logger.info(f"Sent momentum reversal EXIT alert for {signal.signal_type} trade at ${current_price:,.2f} ({profit_pct:+.2f}%)")
    
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
    
    def _send_breakeven_update(self, signal: Signal, current_price: float) -> None:
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
        logger.info(f"Sent breakeven update for {signal.signal_type} trade")
    
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
        
        message = f"""
{emoji} *TRADE CLOSED: {status}*

{signal.signal_type} from ${signal.entry_price:,.2f}
Exit Price: ${current_price:,.2f}

*📊 RESULTS:*
P&L: ${pnl_points:,.2f} ({pnl_percent:+.2f}%)
Hold Time: {minutes} minutes
R:R Achieved: {abs(pnl_points / (signal.entry_price - signal.stop_loss)):.2f}

*💡 NEXT STEPS:*
{"✅ Great trade! Wait for next setup." if reason == "TARGET" else "✅ Stop protected you. Wait for next setup."}

⏰ {datetime.now().strftime('%H:%M:%S UTC')}
"""
        
        self.alerter.send_message(message)
        logger.info(f"Closed trade {trade_id}: {reason}, P&L: {pnl_percent:.2f}%")
        
        # Move to closed trades
        self.closed_trades.append(trade)
        del self.active_trades[trade_id]
    
    def get_active_count(self) -> int:
        """Get number of active trades."""
        return len(self.active_trades)
    
    def get_closed_count(self) -> int:
        """Get number of closed trades."""
        return len(self.closed_trades)
