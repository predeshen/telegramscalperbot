"""Quick diagnostic to check scanner status and recent errors"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

def check_log_file(log_path, scanner_name):
    """Check a log file for recent activity and errors"""
    if not os.path.exists(log_path):
        print(f"  ✗ {scanner_name}: Log file not found")
        return
    
    # Get file modification time
    mod_time = datetime.fromtimestamp(os.path.getmtime(log_path))
    age = datetime.now() - mod_time
    
    # Read last 50 lines
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines
        
        # Count errors in last 50 lines
        errors = [line for line in last_lines if '[ERROR]' in line or '[CRITICAL]' in line]
        warnings = [line for line in last_lines if '[WARNING]' in line]
        
        # Check if running (recent activity)
        is_running = age < timedelta(minutes=5)
        
        status = "🟢 RUNNING" if is_running else "🔴 STOPPED"
        print(f"  {status} {scanner_name}")
        print(f"    Last activity: {mod_time.strftime('%Y-%m-%d %H:%M:%S')} ({age.total_seconds():.0f}s ago)")
        print(f"    Recent errors: {len(errors)}")
        print(f"    Recent warnings: {len(warnings)}")
        
        # Show last few errors
        if errors:
            print(f"    Last error:")
            for line in errors[-2:]:
                print(f"      {line.strip()}")
        
        print()
        
    except Exception as e:
        print(f"  ✗ {scanner_name}: Error reading log - {e}")
        print()

def main():
    print("=" * 70)
    print("Scanner Status Check")
    print("=" * 70)
    print()
    
    # Check each scanner
    scanners = [
        ("logs/scanner.log", "BTC Scalp Scanner"),
        ("logs/scanner_swing.log", "BTC Swing Scanner"),
        ("logs/us30_scanner.log", "US30 Scalp Scanner"),
        ("logs/us30_swing_scanner.log", "US30 Swing Scanner"),
        ("xauusd_scanner/logs/gold_scalp_scanner.log", "Gold Scalp Scanner"),
        ("xauusd_scanner/logs/gold_swing_scanner.log", "Gold Swing Scanner"),
    ]
    
    for log_path, scanner_name in scanners:
        check_log_file(log_path, scanner_name)
    
    print("=" * 70)
    print("Tip: If a scanner shows 'Failed to connect to exchange' errors,")
    print("     run: python test_hybrid_fix.py")
    print("=" * 70)

if __name__ == "__main__":
    main()
