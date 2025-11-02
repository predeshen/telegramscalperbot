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
    status: str = "ACTIVE"  # ACTIVE, CLOSED_TP, CLOSED_SL


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
            entry_time=datetime.now()
        )
        
        self.active_trades[trade_id] = trade_status
        logger.info(f"Added trade to tracking: {trade_id}")
    
    def update_trades(self, current_price: float) -> None:
        """
        Update all active trades with current price and send notifications.
        
        Args:
            current_price: Current market price
        """
        for trade_id, trade in list(self.active_trades.items()):
            signal = trade.signal
            
            # Check if trade should be closed
            if self._check_target_hit(signal, current_price, trade):
                self._close_trade(trade_id, "TARGET", current_price)
                continue
            
            if self._check_stop_hit(signal, current_price, trade):
                self._close_trade(trade_id, "STOP", current_price)
                continue
            
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
