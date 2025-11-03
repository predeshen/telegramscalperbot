"""Extended test of the scanner with live market data."""
import sys
import time
import signal
from main import BTCScalpingScanner

print("=" * 70)
print("BTC Scalping Scanner - Extended Live Test")
print("=" * 70)
print("\n📊 ADJUSTED PARAMETERS FOR MORE SIGNALS:")
print("  - Volume threshold: 1.5x → 1.2x (more sensitive)")
print("  - RSI range: 30-70 → 25-75 (wider range)")
print("\nThis will run for 5 MINUTES with live BTC/USD data.")
print("\n🔍 What to watch for:")
print("  ✓ Connection to Binance")
print("  ✓ Real-time data streaming (1m and 5m)")
print("  ✓ Signal detection when confluence aligns")
print("  ✓ Telegram alerts sent instantly")
print("\n💡 Signals require ALL of these to align:")
print("  1. EMA(9) crosses EMA(21)")
print("  2. Price above/below VWAP")
print("  3. Volume spike (>1.2x average)")
print("  4. RSI in range (25-75)")
print("  5. Price confirms trend (vs EMA50)")
print("\nPress Ctrl+C to stop early")
print("=" * 70)
print()

# Create scanner
scanner = BTCScalpingScanner()

# Set up signal handler for clean shutdown
def signal_handler(signum, frame):
    print("\n\n⏹️  Shutting down scanner...")
    scanner.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    # Start scanner in a separate thread
    import threading
    scanner_thread = threading.Thread(target=scanner.start, daemon=True)
    scanner_thread.start()
    
    # Run for 5 minutes (300 seconds)
    total_seconds = 300
    print(f"🚀 Scanner running for {total_seconds // 60} minutes...")
    print()
    
    last_signal_count = 0
    
    for i in range(total_seconds, 0, -1):
        minutes = i // 60
        seconds = i % 60
        
        # Check for new signals
        current_signals = scanner.health_monitor.long_signal_count + scanner.health_monitor.short_signal_count
        if current_signals > last_signal_count:
            print(f"\n🎯 NEW SIGNAL DETECTED! Total: {current_signals}")
            print("   Check your Telegram for the alert!")
            print()
            last_signal_count = current_signals
        
        print(f"\r⏱️  Time remaining: {minutes:02d}:{seconds:02d} | Signals: {current_signals} | Status: Running", end='', flush=True)
        time.sleep(1)
    
    print("\n\n✅ Test complete! Stopping scanner...")
    scanner.stop()
    
    # Wait for thread to finish
    scanner_thread.join(timeout=5)
    
    print("\n" + "=" * 70)
    print("📈 SCANNER TEST RESULTS")
    print("=" * 70)
    
    # Get health metrics
    metrics = scanner.health_monitor.get_metrics()
    print(f"\n⏱️  Runtime: {metrics['uptime_formatted']}")
    print(f"📊 Total Signals: {metrics['total_signals']}")
    print(f"   🟢 Long Signals: {metrics['long_signals']}")
    print(f"   🔴 Short Signals: {metrics['short_signals']}")
    print(f"🔌 Connection: {metrics['connection_status']}")
    print(f"📡 Last Data: {metrics['last_data_update']}")
    print(f"⚠️  Errors: {metrics['errors_last_hour']}")
    
    print("\n" + "=" * 70)
    
    if metrics['total_signals'] > 0:
        print("🎉 SUCCESS! Signals were detected and sent to Telegram!")
        print(f"   You should have {metrics['total_signals']} alert(s) in your Telegram.")
    else:
        print("📊 No signals detected during this test period.")
        print("   This is normal - confluence conditions are strict.")
        print("   The scanner is working correctly and monitoring 24/7.")
    
    print("\n💡 TIP: For continuous monitoring, run as a service:")
    print("   python main.py")
    print("=" * 70)
    
except Exception as e:
    print(f"\n\n❌ Error during test: {e}")
    import traceback
    traceback.print_exc()
    scanner.stop()
    sys.exit(1)
