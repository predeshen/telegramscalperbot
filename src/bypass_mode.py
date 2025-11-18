"""
Bypass Mode
Emergency testing mode that temporarily disables quality filters
"""
import logging
from datetime import datetime, timedelta
from typing import Optional


logger = logging.getLogger(__name__)


class BypassMode:
    """Emergency bypass mode for testing signal detection without filters"""
    
    def __init__(self, config: dict, alerter=None):
        """
        Initialize bypass mode
        
        Args:
            config: Configuration dictionary with bypass_mode section
            alerter: Alerter instance for sending notifications (optional)
        """
        bypass_config = config.get('bypass_mode', {})
        self.enabled = bypass_config.get('enabled', False)
        self.auto_disable_hours = bypass_config.get('auto_disable_after_hours', 2)
        self.enabled_at: Optional[datetime] = None
        self.alerter = alerter
        
        if self.enabled:
            logger.warning("⚠️ BYPASS MODE IS ENABLED IN CONFIGURATION")
            self.enable()
        else:
            logger.info("Bypass mode initialized (disabled)")
    
    def enable(self):
        """Enable bypass mode"""
        if self.enabled:
            logger.warning("Bypass mode already enabled")
            return
        
        self.enabled = True
        self.enabled_at = datetime.now()
        
        msg = (
            "⚠️ <b>BYPASS MODE ENABLED</b>\n\n"
            "Quality filters are temporarily disabled.\n"
            f"Will auto-disable in {self.auto_disable_hours} hours.\n\n"
            "⚠️ All signals will be prefixed with 'BYPASS MODE'\n\n"
            "This mode is for testing only. Signals may be low quality."
        )
        
        logger.warning("=" * 60)
        logger.warning("BYPASS MODE ENABLED - Quality filters disabled")
        logger.warning(f"Auto-disable in {self.auto_disable_hours} hours")
        logger.warning("=" * 60)
        
        if self.alerter:
            try:
                self.alerter.send_message(msg)
            except Exception as e:
                logger.error(f"Failed to send bypass mode notification: {e}")
    
    def disable(self):
        """Disable bypass mode"""
        if not self.enabled:
            logger.info("Bypass mode already disabled")
            return
        
        self.enabled = False
        duration = None
        if self.enabled_at:
            duration = datetime.now() - self.enabled_at
        self.enabled_at = None
        
        msg = "✅ <b>BYPASS MODE DISABLED</b>\n\nQuality filters re-enabled."
        if duration:
            hours = duration.total_seconds() / 3600
            msg += f"\n\nBypass mode was active for {hours:.1f} hours."
        
        logger.info("=" * 60)
        logger.info("BYPASS MODE DISABLED - Quality filters re-enabled")
        if duration:
            logger.info(f"Was active for {duration}")
        logger.info("=" * 60)
        
        if self.alerter:
            try:
                self.alerter.send_message(msg)
            except Exception as e:
                logger.error(f"Failed to send bypass mode notification: {e}")
    
    def check_auto_disable(self):
        """Check if bypass mode should auto-disable"""
        if not self.enabled or not self.enabled_at:
            return
        
        elapsed = (datetime.now() - self.enabled_at).total_seconds() / 3600
        
        if elapsed >= self.auto_disable_hours:
            logger.warning(
                f"Auto-disabling bypass mode after {elapsed:.1f} hours "
                f"(threshold: {self.auto_disable_hours}h)"
            )
            self.disable()
    
    def should_bypass_filters(self) -> bool:
        """
        Check if filters should be bypassed
        
        Returns:
            True if bypass mode is active
        """
        # Check for auto-disable
        self.check_auto_disable()
        
        return self.enabled
    
    def get_status(self) -> dict:
        """
        Get bypass mode status
        
        Returns:
            Dictionary with status information
        """
        status = {
            'enabled': self.enabled,
            'auto_disable_hours': self.auto_disable_hours
        }
        
        if self.enabled and self.enabled_at:
            elapsed = (datetime.now() - self.enabled_at).total_seconds() / 3600
            remaining = max(0, self.auto_disable_hours - elapsed)
            status['enabled_at'] = self.enabled_at
            status['elapsed_hours'] = elapsed
            status['remaining_hours'] = remaining
        
        return status
    
    def format_signal_prefix(self) -> str:
        """
        Get signal prefix for bypass mode
        
        Returns:
            Prefix string to add to signals in bypass mode
        """
        if not self.enabled:
            return ""
        
        return "⚠️ BYPASS MODE ⚠️\n"
    
    def get_time_remaining(self) -> Optional[timedelta]:
        """
        Get time remaining before auto-disable
        
        Returns:
            timedelta remaining, or None if not enabled
        """
        if not self.enabled or not self.enabled_at:
            return None
        
        elapsed = datetime.now() - self.enabled_at
        total_duration = timedelta(hours=self.auto_disable_hours)
        remaining = total_duration - elapsed
        
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def extend_duration(self, additional_hours: float):
        """
        Extend bypass mode duration
        
        Args:
            additional_hours: Additional hours to add to auto-disable timer
        """
        if not self.enabled:
            logger.warning("Cannot extend duration - bypass mode not enabled")
            return
        
        self.auto_disable_hours += additional_hours
        
        remaining = self.get_time_remaining()
        logger.info(
            f"Bypass mode duration extended by {additional_hours}h. "
            f"New remaining time: {remaining}"
        )
        
        if self.alerter:
            msg = (
                f"⏰ <b>Bypass Mode Extended</b>\n\n"
                f"Added {additional_hours}h to duration.\n"
                f"Remaining time: {remaining}"
            )
            try:
                self.alerter.send_message(msg)
            except Exception as e:
                logger.error(f"Failed to send extension notification: {e}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration
    test_config = {
        'bypass_mode': {
            'enabled': False,
            'auto_disable_after_hours': 2
        }
    }
    
    # Create bypass mode instance
    bypass = BypassMode(test_config)
    
    # Test enable
    print("\n=== Testing Enable ===")
    bypass.enable()
    print(f"Status: {bypass.get_status()}")
    print(f"Should bypass: {bypass.should_bypass_filters()}")
    print(f"Signal prefix: '{bypass.format_signal_prefix()}'")
    
    # Test time remaining
    print(f"\nTime remaining: {bypass.get_time_remaining()}")
    
    # Test disable
    print("\n=== Testing Disable ===")
    bypass.disable()
    print(f"Status: {bypass.get_status()}")
    print(f"Should bypass: {bypass.should_bypass_filters()}")
