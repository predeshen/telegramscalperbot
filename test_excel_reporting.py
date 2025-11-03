"""Quick test script for Excel reporting feature."""
import json
from datetime import datetime
from src.excel_reporter import ExcelReporter

def test_excel_reporter():
    """Test the Excel reporter with sample data."""
    print("=" * 60)
    print("Testing Excel Reporter")
    print("=" * 60)
    
    # Load config
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    # Get SMTP config
    smtp_config = config['excel_reporting'].get('smtp', config['smtp'])
    
    print(f"\n✓ SMTP Server: {smtp_config['server']}")
    print(f"✓ SMTP User: {smtp_config['user']}")
    print(f"✓ To Email: {smtp_config['to_email']}")
    print(f"✓ Password Set: {'Yes' if smtp_config['password'] != 'DISABLED' else 'No'}")
    
    # Create reporter
    print("\n📊 Creating Excel Reporter...")
    reporter = ExcelReporter(
        excel_file_path="logs/test_scans.xlsx",
        smtp_config=smtp_config,
        report_interval_seconds=3600,
        initial_report_delay_seconds=10,  # 10 seconds for testing
        scanner_name="Test Scanner"
    )
    
    print("✓ Excel Reporter created successfully")
    print(f"✓ Excel file will be created at: logs/test_scans.xlsx")
    
    # Log some test scan results
    print("\n📝 Logging test scan results...")
    for i in range(5):
        scan_data = {
            'timestamp': datetime.now(),
            'scanner': 'Test-Scanner',
            'symbol': 'BTC/USDT',
            'timeframe': '1m',
            'price': 50000.0 + (i * 100),
            'volume': 1000.0 + (i * 50),
            'indicators': {
                'ema_9': 49900.0,
                'ema_21': 49800.0,
                'ema_50': 49700.0,
                'rsi': 55.0 + i,
                'atr': 150.0,
                'volume_ma': 1000.0
            },
            'signal_detected': i == 2,  # Signal on 3rd scan
            'signal_type': 'LONG' if i == 2 else None,
            'signal_details': {
                'entry_price': 50200.0,
                'stop_loss': 50000.0,
                'take_profit': 50600.0,
                'risk_reward': 2.0,
                'strategy': 'Test Strategy'
            } if i == 2 else {}
        }
        
        success = reporter.log_scan_result(scan_data)
        if success:
            print(f"  ✓ Scan {i+1} logged")
        else:
            print(f"  ✗ Scan {i+1} failed")
    
    print("\n✓ Test scans logged to Excel file")
    print(f"✓ Check logs/test_scans.xlsx to view the data")
    
    # Start reporter (will send initial email in 10 seconds)
    print("\n📧 Starting email reporter...")
    print("⏰ Initial email will be sent in 10 seconds...")
    print("   (Check your inbox at predeshen@gmail.com)")
    
    reporter.start()
    
    print("\n✓ Reporter started successfully!")
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check logs/test_scans.xlsx - should have 5 rows of data")
    print("2. Wait 10 seconds and check your email")
    print("3. If email arrives, Excel reporting is working!")
    print("\nPress Ctrl+C to stop the test...")
    
    # Keep running for 30 seconds to allow email to send
    import time
    try:
        time.sleep(30)
        print("\n✓ Test email should have been sent!")
        reporter.stop()
        print("✓ Reporter stopped")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        reporter.stop()
        print("✓ Reporter stopped")

if __name__ == "__main__":
    test_excel_reporter()
