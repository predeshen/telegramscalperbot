"""Test the scanner with live market data for a short period."""
import sys
import time
import signal
from main import BTCScalpingScanner

print("=" * 70)
print("BTC Scalping Scanner - Live Test")
print("=" * 70)
print("\nThis will run the scanner for 60 seconds with live market data.")
print("Watch for:")
print("  - Connection to Binance")
print("  - Data loading (1m and 5m)")
print("  - WebSocket connection")
print("  - Signal detection (if market conditions align)")
print("  - Telegram alerts (if signals detected)")
print("\nPress Ctrl+C to stop early")
print("=" * 70)
print()

# Create scanner
scanner = BTCScalpingScanner()

# Set up signal handler for clean shutdown
def signal_handler(signum, frame):
    print("\n\nShutting down scanner...")
    scanner.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    # Start scanner in a separate thread
    import threading
    scanner_thread = threading.Thread(target=scanner.start, daemon=True)
    scanner_thread.start()
    
    # Run for 60 seconds
    print("Scanner running... (60 seconds)")
    for i in range(60, 0, -1):
        print(f"\rTime remaining: {i}s ", end='', flush=True)
        time.sleep(1)
    
    print("\n\nTest complete! Stopping scanner...")
    scanner.stop()
    
    # Wait for thread to finish
    scanner_thread.join(timeout=5)
    
    print("\n" + "=" * 70)
    print("Scanner Test Summary")
    print("=" * 70)
    
    # Get health metrics
    metrics = scanner.health_monitor.get_metrics()
    print(f"Uptime: {metrics['uptime_formatted']}")
    print(f"Total Signals: {metrics['total_signals']}")
    print(f"  - Long: {metrics['long_signals']}")
    print(f"  - Short: {metrics['short_signals']}")
    print(f"Connection: {metrics['connection_status']}")
    print(f"Last Data Update: {metrics['last_data_update']}")
    print(f"Errors (1h): {metrics['errors_last_hour']}")
    
    print("\n" + "=" * 70)
    print("✅ Scanner test completed successfully!")
    print("=" * 70)
    
    if metrics['total_signals'] > 0:
        print("\n🎯 Signals were detected! Check your Telegram for alerts.")
    else:
        print("\n📊 No signals detected (market conditions didn't align).")
        print("   This is normal - signals require specific confluence conditions.")
    
except Exception as e:
    print(f"\n\n❌ Error during test: {e}")
    import traceback
    traceback.print_exc()
    scanner.stop()
    sys.exit(1)
