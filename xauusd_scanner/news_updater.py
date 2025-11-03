"""
News Events Auto-Updater for Gold Trading
Provides utilities to update economic calendar events
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class NewsUpdater:
    """
    Utilities for updating and managing news events.
    
    Note: This provides a template system. For production, integrate with:
    - ForexFactory API
    - Investing.com Economic Calendar
    - Trading Economics API
    - Or manual updates via add_event()
    """
    
    def __init__(self, events_file: str = "xauusd_scanner/news_events.json"):
        """Initialize News Updater."""
        self.events_file = Path(events_file)
        logger.info(f"NewsUpdater initialized for {events_file}")
    
    def create_sample_events(self, days_ahead: int = 7) -> list:
        """
        Create sample high-impact events for testing.
        
        Args:
            days_ahead: Number of days to generate events for
            
        Returns:
            List of event dictionaries
        """
        now = datetime.now(timezone.utc)
        events = []
        
        # Common high-impact events for Gold
        event_templates = [
            {"title": "US Non-Farm Payrolls", "time": "13:30", "impact": "high", "currency": "USD"},
            {"title": "FOMC Interest Rate Decision", "time": "19:00", "impact": "high", "currency": "USD"},
            {"title": "US CPI (Inflation)", "time": "13:30", "impact": "high", "currency": "USD"},
            {"title": "US GDP", "time": "13:30", "impact": "high", "currency": "USD"},
            {"title": "FOMC Press Conference", "time": "19:30", "impact": "high", "currency": "USD"},
            {"title": "US Retail Sales", "time": "13:30", "impact": "high", "currency": "USD"},
            {"title": "ECB Interest Rate Decision", "time": "12:45", "impact": "high", "currency": "EUR"},
            {"title": "UK CPI", "time": "07:00", "impact": "high", "currency": "GBP"},
        ]
        
        # Generate events for next N days
        for day in range(days_ahead):
            event_date = now + timedelta(days=day)
            
            # Add 1-2 events per week
            if day % 3 == 0:  # Every 3 days
                template = event_templates[day % len(event_templates)]
                
                # Parse time
                hour, minute = map(int, template["time"].split(":"))
                event_datetime = event_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                events.append({
                    "title": template["title"],
                    "datetime_gmt": event_datetime.isoformat(),
                    "impact": template["impact"],
                    "currency": template["currency"],
                    "description": f"High-impact {template['currency']} economic data release"
                })
        
        return events
    
    def add_manual_event(self, title: str, date_str: str, time_str: str,
                        impact: str = "high", currency: str = "USD",
                        description: str = "") -> None:
        """
        Add a manual event to the calendar.
        
        Args:
            title: Event title
            date_str: Date in YYYY-MM-DD format
            time_str: Time in HH:MM format (GMT)
            impact: Impact level ('low', 'medium', 'high')
            currency: Currency affected
            description: Event description
            
        Example:
            updater.add_manual_event(
                "FOMC Meeting",
                "2025-11-06",
                "19:00",
                impact="high",
                currency="USD"
            )
        """
        # Parse datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        time_obj = datetime.strptime(time_str, "%H:%M")
        
        event_datetime = datetime(
            date_obj.year, date_obj.month, date_obj.day,
            time_obj.hour, time_obj.minute,
            tzinfo=timezone.utc
        )
        
        # Load existing events
        events = self._load_events()
        
        # Add new event
        events.append({
            "title": title,
            "datetime_gmt": event_datetime.isoformat(),
            "impact": impact,
            "currency": currency,
            "description": description
        })
        
        # Save
        self._save_events(events)
        logger.info(f"Added manual event: {title} at {event_datetime.strftime('%Y-%m-%d %H:%M GMT')}")
    
    def add_weekly_events(self) -> None:
        """
        Add common weekly recurring events.
        Useful for setting up regular economic releases.
        """
        now = datetime.now(timezone.utc)
        events = self._load_events()
        
        # Find next Friday (NFP day)
        days_until_friday = (4 - now.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7  # Next week
        
        next_friday = now + timedelta(days=days_until_friday)
        nfp_datetime = next_friday.replace(hour=13, minute=30, second=0, microsecond=0)
        
        # Add NFP (first Friday of month)
        if next_friday.day <= 7:
            events.append({
                "title": "US Non-Farm Payrolls (NFP)",
                "datetime_gmt": nfp_datetime.isoformat(),
                "impact": "high",
                "currency": "USD",
                "description": "Monthly employment report - major Gold mover"
            })
            logger.info(f"Added NFP event for {nfp_datetime.strftime('%Y-%m-%d %H:%M GMT')}")
        
        self._save_events(events)
    
    def initialize_calendar(self, use_samples: bool = True) -> None:
        """
        Initialize the news calendar with events.
        
        Args:
            use_samples: If True, populate with sample events for testing
        """
        if self.events_file.exists():
            logger.info("Events file already exists. Use add_manual_event() to add more.")
            return
        
        if use_samples:
            events = self.create_sample_events(days_ahead=14)
            self._save_events(events)
            logger.info(f"Initialized calendar with {len(events)} sample events")
        else:
            self._save_events([])
            logger.info("Initialized empty calendar. Add events manually.")
    
    def cleanup_old_events(self, days_old: int = 7) -> int:
        """
        Remove events older than specified days.
        
        Args:
            days_old: Remove events older than this many days
            
        Returns:
            Number of events removed
        """
        events = self._load_events()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        original_count = len(events)
        
        # Filter out old events
        events = [
            event for event in events
            if datetime.fromisoformat(event['datetime_gmt']) >= cutoff
        ]
        
        removed_count = original_count - len(events)
        
        if removed_count > 0:
            self._save_events(events)
            logger.info(f"Removed {removed_count} old events")
        
        return removed_count
    
    def list_upcoming_events(self, days: int = 7) -> None:
        """
        Print upcoming events.
        
        Args:
            days: Number of days to look ahead
        """
        events = self._load_events()
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days)
        
        upcoming = [
            event for event in events
            if now <= datetime.fromisoformat(event['datetime_gmt']) <= cutoff
        ]
        
        # Sort by datetime
        upcoming.sort(key=lambda e: e['datetime_gmt'])
        
        print(f"\n📅 Upcoming Events (next {days} days):")
        print("=" * 80)
        
        if not upcoming:
            print("No events scheduled")
        else:
            for event in upcoming:
                dt = datetime.fromisoformat(event['datetime_gmt'])
                impact_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(event['impact'], "⚪")
                print(f"{impact_emoji} {dt.strftime('%Y-%m-%d %H:%M GMT')} - {event['title']} ({event['currency']})")
        
        print("=" * 80)
    
    def _load_events(self) -> list:
        """Load events from JSON file."""
        if not self.events_file.exists():
            return []
        
        try:
            with open(self.events_file, 'r') as f:
                data = json.load(f)
            return data.get('events', [])
        except Exception as e:
            logger.error(f"Error loading events: {e}")
            return []
    
    def _save_events(self, events: list) -> None:
        """Save events to JSON file."""
        try:
            # Ensure directory exists
            self.events_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {'events': events}
            
            with open(self.events_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(events)} events to {self.events_file}")
        except Exception as e:
            logger.error(f"Error saving events: {e}")


def main():
    """CLI for managing news events."""
    import sys
    
    updater = NewsUpdater()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m xauusd_scanner.news_updater init       # Initialize with sample events")
        print("  python -m xauusd_scanner.news_updater list       # List upcoming events")
        print("  python -m xauusd_scanner.news_updater cleanup    # Remove old events")
        print("  python -m xauusd_scanner.news_updater weekly     # Add weekly recurring events")
        return
    
    command = sys.argv[1]
    
    if command == "init":
        updater.initialize_calendar(use_samples=True)
        print("✅ Calendar initialized with sample events")
        updater.list_upcoming_events(14)
    
    elif command == "list":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        updater.list_upcoming_events(days)
    
    elif command == "cleanup":
        count = updater.cleanup_old_events()
        print(f"✅ Removed {count} old events")
    
    elif command == "weekly":
        updater.add_weekly_events()
        print("✅ Added weekly recurring events")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
