#!/usr/bin/env python3
"""Check if all dependencies are installed."""
import sys

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("=" * 60)
    print("Checking Dependencies")
    print("=" * 60)
    
    missing = []
    
    # Check core dependencies
    dependencies = [
        ('ccxt', 'Exchange connectivity'),
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical operations'),
        ('openpyxl', 'Excel reporting'),
        ('telegram', 'Telegram bot (python-telegram-bot)'),
    ]
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✓ {module:20s} - {description}")
        except ImportError:
            print(f"✗ {module:20s} - {description} - MISSING!")
            missing.append(module)
    
    print("=" * 60)
    
    if missing:
        print("\n❌ Missing dependencies detected!")
        print("\nInstall missing packages:")
        print(f"pip install {' '.join(missing)}")
        print("\nOr install all requirements:")
        print("pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True

if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
