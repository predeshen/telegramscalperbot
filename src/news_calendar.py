"""
News Calendar for Gold Trading
Manages economic events and trading pauses around high-impact news
"""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class NewsEvent:
    """Represents a single news event."""
    
    def __init__(self, event_dict: Dict):
        """
        Initialize news event from dictionary.
        
        Args:
            event_dict: Dictionary with event details
        """
        self.title = event_dict['title']
        self.datetime_gmt = datetime.fromisoformat(event_dict['datetime_gmt'])
        self.impact = event_dict.get('impact', 'medium')  # low, medium, high
        self.currency = event_dict.get('currency', 'USD')
        self.description = event_dict.get('description', '')
        
        # Ensure timezone aware
        if self.datetime_gmt.tzinfo is None:
            self.datetime_gmt = self.datetime_gmt.replace(tzinfo=timezone.utc)
    
    def __repr__(self) -> str:
        return f"NewsEvent({self.title} at {self.datetime_gmt.strftime('%Y-%m-%d %H:%M GMT')})"


class NewsCalendar:
    """
    Manages economic calendar and trading pauses around news events.
    
    Pauses trading 30 minutes before high-impact news.
    """
    
    def __init__(self, events_file: str = "config/news_events.json"):
        """
        Initialize News Calendar.
        
        Args:
            events_file: Path to JSON file with news events
        """
        self.events_file = Path(events_file)
        self.events: List[NewsEvent] = []
        self.pause_window_minutes = 30  # Pause 30 min before news
        self.resume_delay_minutes = 5   # Resume 5 min after news
        
        self.load_events()
        logger.info(f"NewsCalendar initialized with {len(self.events)} events")
    
    def load_events(self) -> None:
        """Load news events from JSON file."""
        if not self.events_file.exists():
            logger.warning(f"News events file not found: {self.events_file}")
            self.events = []
            return
        
        try:
            with open(self.events_file, 'r') as f:
                data = json.load(f)
            
            self.events = [NewsEvent(event) for event in data.get('events', [])]
            logger.info(f"Loaded {len(self.events)} news events from {self.events_file}")
            
            # Log upcoming events
            upcoming = self.get_upcoming_events(hours=24)
            if upcoming:
                logger.info(f"Next {len(upcoming)} events in 24h:")
                for event in upcoming[:5]:  # Show first 5
                    logger.info(f"  - {event.title} at {event.datetime_gmt.strftime('%H:%M GMT')}")
        
        except Exception as e:
            logger.error(f"Error loading news events: {e}")
            self.events = []
    
    def add_event(self, title: str, datetime_gmt: datetime, impact: str = 'medium',
                  currency: str = 'USD', description: str = '') -> None:
        """
        Add a news event manually.
        
        Args:
            title: Event title
            datetime_gmt: Event datetime in GMT
            impact: Impact level ('low', 'medium', 'high')
            currency: Currency affected
            description: Event description
        """
        event_dict = {
            'title': title,
            'datetime_gmt': datetime_gmt.isoformat(),
            'impact': impact,
            'currency': currency,
            'description': description
        }
        
        event = NewsEvent(event_dict)
        self.events.append(event)
        logger.info(f"Added news event: {event}")
    
    def get_upcoming_events(self, hours: int = 24) -> List[NewsEvent]:
        """
        Get upcoming news events within specified hours.
        
        Args:
            hours: Number of hours to look ahead
            
        Returns:
            List of upcoming NewsEvent objects
        """
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours)
        
        upcoming = [
            event for event in self.events
            if now <= event.datetime_gmt <= cutoff
        ]
        
        # Sort by datetime
        upcoming.sort(key=lambda e: e.datetime_gmt)
        
        return upcoming
    
    def get_next_event(self) -> Optional[NewsEvent]:
        """
        Get the next upcoming news event.
        
        Returns:
            Next NewsEvent or None if no upcoming events
        """
        upcoming = self.get_upcoming_events(hours=168)  # Next week
        return upcoming[0] if upcoming else None
    
    def is_news_imminent(self, current_time: Optional[datetime] = None,
                        impact_filter: Optional[List[str]] = None) -> tuple[bool, Optional[NewsEvent]]:
        """
        Check if high-impact news is imminent (within pause window).
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            impact_filter: List of impact levels to check (defaults to ['high'])
            
        Returns:
            Tuple of (is_imminent, event) where event is the imminent NewsEvent or None
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        if impact_filter is None:
            impact_filter = ['high']  # Only pause for high-impact by default
        
        # Check events within pause window
        pause_start = current_time
        pause_end = current_time + timedelta(minutes=self.pause_window_minutes)
        
        for event in self.events:
            if event.impact not in impact_filter:
                continue
            
            # Check if event is within pause window
            if pause_start <= event.datetime_gmt <= pause_end:
                minutes_until = (event.datetime_gmt - current_time).total_seconds() / 60
                logger.info(f"News imminent: {event.title} in {minutes_until:.1f} minutes")
                return True, event
        
        return False, None
    
    def should_pause_trading(self, current_time: Optional[datetime] = None) -> tuple[bool, Optional[str]]:
        """
        Determine if trading should be paused due to news.
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            
        Returns:
            Tuple of (should_pause, reason) where reason explains why
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Check for imminent high-impact news
        is_imminent, event = self.is_news_imminent(current_time, impact_filter=['high'])
        
        if is_imminent and event:
            minutes_until = (event.datetime_gmt - current_time).total_seconds() / 60
            reason = f"High-impact news in {minutes_until:.0f} min: {event.title}"
            return True, reason
        
        # Check if we're in post-news resume delay
        for event in self.events:
            if event.impact != 'high':
                continue
            
            time_since_event = (current_time - event.datetime_gmt).total_seconds() / 60
            
            # If event just passed and we're in resume delay
            if 0 <= time_since_event <= self.resume_delay_minutes:
                reason = f"Waiting {self.resume_delay_minutes - time_since_event:.0f} min after: {event.title}"
                return True, reason
        
        return False, None
    
    def get_news_status(self, current_time: Optional[datetime] = None) -> Dict[str, any]:
        """
        Get comprehensive news status.
        
        Args:
            current_time: Optional datetime to check (defaults to now in GMT)
            
        Returns:
            Dictionary with news status details
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        should_pause, reason = self.should_pause_trading(current_time)
        next_event = self.get_next_event()
        upcoming_24h = self.get_upcoming_events(hours=24)
        
        status = {
            'should_pause': should_pause,
            'pause_reason': reason,
            'next_event': {
                'title': next_event.title,
                'time_gmt': next_event.datetime_gmt.strftime('%Y-%m-%d %H:%M GMT'),
                'impact': next_event.impact,
                'minutes_until': (next_event.datetime_gmt - current_time).total_seconds() / 60
            } if next_event else None,
            'upcoming_24h_count': len(upcoming_24h),
            'high_impact_24h': len([e for e in upcoming_24h if e.impact == 'high'])
        }
        
        return status
    
    def save_events(self) -> None:
        """Save current events to JSON file."""
        try:
            events_data = {
                'events': [
                    {
                        'title': event.title,
                        'datetime_gmt': event.datetime_gmt.isoformat(),
                        'impact': event.impact,
                        'currency': event.currency,
                        'description': event.description
                    }
                    for event in self.events
                ]
            }
            
            with open(self.events_file, 'w') as f:
                json.dump(events_data, f, indent=2)
            
            logger.info(f"Saved {len(self.events)} events to {self.events_file}")
        
        except Exception as e:
            logger.error(f"Error saving news events: {e}")
    
    def cleanup_past_events(self, days_old: int = 7) -> int:
        """
        Remove events older than specified days.
        
        Args:
            days_old: Remove events older than this many days
            
        Returns:
            Number of events removed
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        original_count = len(self.events)
        self.events = [event for event in self.events if event.datetime_gmt >= cutoff]
        removed_count = original_count - len(self.events)
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} past events older than {days_old} days")
            self.save_events()
        
        return removed_count
