"""
Signal Filter
Filters signals to prevent conflicts and duplicates across timeframes and symbols.
"""
import logging
import logging.handlers
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
from pathlib import Path


logger = logging.getLogger(__name__)


class SignalFilter:
    """Filters signals to prevent conflicts and duplicates."""
    
    # Timeframe hierarchy for conflict resolution (higher value = higher priority)
    TIMEFRAME_HIERARCHY = {
        '1d': 6,
        '4h': 5,
        '1h': 4,
        '15m': 3,
        '5m': 2,
        '1m': 1
    }
    
    def __init__(
        self,
        conflict_window_minutes: int = 5,
        duplicate_window_minutes: int = 10
    ):
        """
        Initialize Signal Filter.
        
        Args:
            conflict_window_minutes: Time window for checking conflicting signals
            duplicate_window_minutes: Time window for checking duplicate signals
        """
        self.conflict_window_minutes = conflict_window_minutes
        self.duplicate_window_minutes = duplicate_window_minutes
        
        # Track recent signals per symbol
        self.recent_signals: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Track active trades per symbol
        self.active_trades: Dict[str, any] = {}  # symbol -> Signal
        
        # Track suppressed signals for logging
        self.suppressed_signals: List[Dict] = []
        
        # Setup suppressed signals logger
        self._setup_suppressed_logger()
        
        logger.info(f"SignalFilter initialized (conflict_window={conflict_window_minutes}m, duplicate_window={duplicate_window_minutes}m)")
    
    def _setup_suppressed_logger(self) -> None:
        """Setup logger for suppressed signals."""
        try:
            # Create logs directory
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Create suppressed signals logger
            self.suppressed_logger = logging.getLogger("signal_filter.suppressed")
            self.suppressed_logger.setLevel(logging.INFO)
            
            # Remove existing handlers
            self.suppressed_logger.handlers = []
            
            # Add rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "suppressed_signals.log",
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3
            )
            file_handler.setLevel(logging.INFO)
            
            # Format
            formatter = logging.Formatter(
                '%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.suppressed_logger.addHandler(file_handler)
            
            logger.info("Setup suppressed signals logging")
            
        except Exception as e:
            logger.error(f"Failed to setup suppressed logger: {e}")
            self.suppressed_logger = logger
    
    def should_suppress_signal(
        self,
        symbol: str,
        signal: any,  # Signal object
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Determine if signal should be suppressed.
        
        Args:
            symbol: Trading symbol
            signal: Signal object to evaluate
            current_time: Current time (defaults to now)
            
        Returns:
            (should_suppress, reason)
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Get recent signals for this symbol
        recent = self._get_recent_signals(symbol, current_time)
        
        # Check for timeframe conflicts
        has_conflict, conflict_reason = self.check_timeframe_conflicts(signal, recent, current_time)
        if has_conflict:
            self._log_suppression(symbol, signal, conflict_reason)
            return True, conflict_reason
        
        # Check for active trade conflicts
        has_trade_conflict, trade_reason = self.check_active_trade_conflict(symbol, signal)
        if has_trade_conflict:
            self._log_suppression(symbol, signal, trade_reason)
            return True, trade_reason
        
        # Check for duplicate signals
        is_duplicate, dup_reason = self.check_duplicate_signal(symbol, signal, recent, current_time)
        if is_duplicate:
            self._log_suppression(symbol, signal, dup_reason)
            return True, dup_reason
        
        # Check for signals too close together (within 15 minutes of same type)
        is_too_close, close_reason = self.check_signal_proximity(symbol, signal, recent, current_time)
        if is_too_close:
            self._log_suppression(symbol, signal, close_reason)
            return True, close_reason
        
        # Signal passed all filters
        return False, ""
    
    def check_timeframe_conflicts(
        self,
        signal: any,
        recent_signals: List[any],
        current_time: datetime
    ) -> Tuple[bool, str]:
        """
        Check for conflicting signals across timeframes.
        
        Args:
            signal: Signal to check
            recent_signals: List of recent signals for the same symbol
            current_time: Current time
            
        Returns:
            (has_conflict, reason)
        """
        signal_timeframe = signal.timeframe
        signal_type = signal.signal_type
        signal_rank = self.TIMEFRAME_HIERARCHY.get(signal_timeframe, 0)
        
        # Check recent signals within conflict window
        conflict_cutoff = current_time - timedelta(minutes=self.conflict_window_minutes)
        
        for recent in recent_signals:
            # Skip if outside conflict window
            if recent.timestamp < conflict_cutoff:
                continue
            
            recent_rank = self.TIMEFRAME_HIERARCHY.get(recent.timeframe, 0)
            
            # Check if signals conflict (opposite directions)
            if signal_type != recent.signal_type:
                # Higher timeframe takes priority
                if recent_rank > signal_rank:
                    reason = (
                        f"Conflicting signal: {recent.timeframe} {recent.signal_type} "
                        f"(higher priority) vs {signal_timeframe} {signal_type}"
                    )
                    return True, reason
                elif recent_rank == signal_rank:
                    # Same timeframe, conflicting signals - suppress both
                    reason = (
                        f"Conflicting signals on same timeframe {signal_timeframe}: "
                        f"{recent.signal_type} vs {signal_type}"
                    )
                    return True, reason
        
        return False, ""
    
    def check_active_trade_conflict(
        self,
        symbol: str,
        signal: any
    ) -> Tuple[bool, str]:
        """
        Check if signal conflicts with active trade.
        
        Args:
            symbol: Trading symbol
            signal: Signal to check
            
        Returns:
            (has_conflict, reason)
        """
        if symbol not in self.active_trades:
            return False, ""
        
        active_trade = self.active_trades[symbol]
        
        # Check if new signal is opposite direction
        if signal.signal_type != active_trade.signal_type:
            reason = (
                f"Active {active_trade.signal_type} trade exists, "
                f"suppressing opposite {signal.signal_type} signal"
            )
            return True, reason
        
        return False, ""
    
    def check_signal_proximity(
        self,
        symbol: str,
        signal: any,
        recent_signals: List[any],
        current_time: datetime,
        proximity_minutes: int = 15
    ) -> Tuple[bool, str]:
        """
        Check if signal is too close to another signal of the same type.
        
        Args:
            symbol: Trading symbol
            signal: Signal to check
            recent_signals: List of recent signals
            current_time: Current time
            proximity_minutes: Minimum minutes between signals of same type
            
        Returns:
            (is_too_close, reason)
        """
        proximity_cutoff = current_time - timedelta(minutes=proximity_minutes)
        
        for recent in recent_signals:
            # Skip if outside proximity window
            if recent.timestamp < proximity_cutoff:
                continue
            
            # Check if same signal type (LONG or SHORT)
            if signal.signal_type == recent.signal_type:
                time_diff = (current_time - recent.timestamp).total_seconds() / 60
                reason = (
                    f"Signal too close to recent {signal.signal_type}: "
                    f"{time_diff:.1f} minutes ago (minimum {proximity_minutes} minutes required)"
                )
                return True, reason
        
        return False, ""
    
    def check_duplicate_signal(
        self,
        symbol: str,
        signal: any,
        recent_signals: List[any],
        current_time: datetime
    ) -> Tuple[bool, str]:
        """
        Check for duplicate signals.
        
        Args:
            symbol: Trading symbol
            signal: Signal to check
            recent_signals: List of recent signals
            current_time: Current time
            
        Returns:
            (is_duplicate, reason)
        """
        duplicate_cutoff = current_time - timedelta(minutes=self.duplicate_window_minutes)
        
        for recent in recent_signals:
            # Skip if outside duplicate window
            if recent.timestamp < duplicate_cutoff:
                continue
            
            # Check if signals are similar
            if (signal.signal_type == recent.signal_type and
                signal.timeframe == recent.timeframe):
                
                # Check price proximity (within 0.5%)
                price_diff_percent = abs(signal.entry_price - recent.entry_price) / recent.entry_price * 100
                
                if price_diff_percent < 0.5:
                    reason = (
                        f"Duplicate signal: {signal.timeframe} {signal.signal_type} "
                        f"at ${signal.entry_price:.2f} (similar to recent at ${recent.entry_price:.2f})"
                    )
                    return True, reason
        
        return False, ""
    
    def add_signal_to_history(self, symbol: str, signal: any) -> None:
        """
        Add signal to recent history.
        
        Args:
            symbol: Trading symbol
            signal: Signal object
        """
        self.recent_signals[symbol].append(signal)
        logger.debug(f"Added signal to history: {symbol} {signal.timeframe} {signal.signal_type}")
    
    def set_active_trade(self, symbol: str, signal: any) -> None:
        """
        Mark a signal as an active trade.
        
        Args:
            symbol: Trading symbol
            signal: Signal object
        """
        self.active_trades[symbol] = signal
        logger.info(f"Set active trade: {symbol} {signal.signal_type} at ${signal.entry_price:.2f}")
    
    def clear_active_trade(self, symbol: str) -> None:
        """
        Clear active trade for a symbol.
        
        Args:
            symbol: Trading symbol
        """
        if symbol in self.active_trades:
            trade = self.active_trades.pop(symbol)
            logger.info(f"Cleared active trade: {symbol} {trade.signal_type}")
    
    def _get_recent_signals(
        self,
        symbol: str,
        current_time: datetime,
        max_age_minutes: int = 60
    ) -> List[any]:
        """
        Get recent signals for a symbol.
        
        Args:
            symbol: Trading symbol
            current_time: Current time
            max_age_minutes: Maximum age of signals to return
            
        Returns:
            List of recent Signal objects
        """
        if symbol not in self.recent_signals:
            return []
        
        cutoff_time = current_time - timedelta(minutes=max_age_minutes)
        
        return [
            sig for sig in self.recent_signals[symbol]
            if sig.timestamp >= cutoff_time
        ]
    
    def _log_suppression(self, symbol: str, signal: any, reason: str) -> None:
        """
        Log a suppressed signal.
        
        Args:
            symbol: Trading symbol
            signal: Suppressed signal
            reason: Reason for suppression
        """
        suppression_record = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'timeframe': signal.timeframe,
            'signal_type': signal.signal_type,
            'entry_price': signal.entry_price,
            'reason': reason
        }
        
        self.suppressed_signals.append(suppression_record)
        
        # Keep only last 100 suppressions
        if len(self.suppressed_signals) > 100:
            self.suppressed_signals = self.suppressed_signals[-100:]
        
        # Log to both main logger and suppressed signals file
        logger.info(f"Signal suppressed: {symbol} {signal.timeframe} {signal.signal_type} - {reason}")
        
        # Log to suppressed signals file with more detail
        self.suppressed_logger.info(
            f"{symbol} | {signal.timeframe} | {signal.signal_type} | "
            f"Entry: ${signal.entry_price:.2f} | Reason: {reason}"
        )
    
    def get_suppressed_signals(self, symbol: Optional[str] = None, max_count: int = 50) -> List[Dict]:
        """
        Get recent suppressed signals.
        
        Args:
            symbol: Filter by symbol (optional)
            max_count: Maximum number of records to return
            
        Returns:
            List of suppression records
        """
        records = self.suppressed_signals
        
        if symbol:
            records = [r for r in records if r['symbol'] == symbol]
        
        return records[-max_count:]
    
    def get_statistics(self) -> Dict:
        """
        Get filter statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_signals = sum(len(signals) for signals in self.recent_signals.values())
        
        # Count suppressions by reason
        suppression_reasons = defaultdict(int)
        for record in self.suppressed_signals:
            reason_type = record['reason'].split(':')[0]
            suppression_reasons[reason_type] += 1
        
        return {
            'total_signals_tracked': total_signals,
            'symbols_tracked': len(self.recent_signals),
            'active_trades': len(self.active_trades),
            'total_suppressions': len(self.suppressed_signals),
            'suppression_by_reason': dict(suppression_reasons)
        }
    
    def cleanup_old_data(self, max_age_hours: int = 24) -> None:
        """
        Clean up old signal data.
        
        Args:
            max_age_hours: Maximum age of data to keep
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Clean up recent signals
        for symbol in list(self.recent_signals.keys()):
            signals = self.recent_signals[symbol]
            # Filter out old signals
            recent = [sig for sig in signals if sig.timestamp >= cutoff_time]
            
            if recent:
                self.recent_signals[symbol] = deque(recent, maxlen=100)
            else:
                del self.recent_signals[symbol]
        
        # Clean up suppressed signals
        self.suppressed_signals = [
            record for record in self.suppressed_signals
            if record['timestamp'] >= cutoff_time
        ]
        
        logger.info(f"Cleaned up old data (older than {max_age_hours}h)")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    filter = SignalFilter()
    
    # Test statistics
    stats = filter.get_statistics()
    print(f"Filter statistics: {stats}")
