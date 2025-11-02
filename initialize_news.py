#!/usr/bin/env python3
"""
News Events Initializer
Sets up the Gold scanner news calendar with sample events
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def initialize_news_calendar():
    """Initialize news calendar with sample events."""
    print("📰 INITIALIZING NEWS CALENDAR")
    print("=" * 50)
    
    try:
        from xauusd_scanner.news_updater import NewsUpdater
        
        updater = NewsUpdater()
        
        # Initialize with sample events
        print("\n📝 Creating sample news events...")
        updater.initialize_calendar(use_samples=True)
        
        # Add weekly recurring events
        print("\n📅 Adding weekly recurring events...")
        updater.add_weekly_events()
        
        # Show upcoming events
        print("\n📋 Upcoming events (next 14 days):")
        updater.list_upcoming_events(14)
        
        print("\n" + "=" * 50)
        print("✅ NEWS CALENDAR INITIALIZED!")
        print("\n💡 To manage events:")
        print("   python -m xauusd_scanner.news_updater list     # List events")
        print("   python -m xauusd_scanner.news_updater weekly   # Add weekly events")
        print("   python -m xauusd_scanner.news_updater cleanup  # Remove old events")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ INITIALIZATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = initialize_news_calendar()
    sys.exit(0 if success else 1)
