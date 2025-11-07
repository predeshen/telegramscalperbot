#!/usr/bin/env python3
"""Test configuration loading for all scanners."""

import sys

def test_btc_scalp():
    """Test BTC scalp config."""
    try:
        from src.config_loader import ConfigLoader
        config = ConfigLoader.load('config/config.json')
        print("✓ BTC Scalp config loaded successfully")
        return True
    except Exception as e:
        print(f"✗ BTC Scalp config failed: {e}")
        return False

def test_gold_scalp():
    """Test Gold scalp config."""
    try:
        from xauusd_scanner.gold_config_loader import GoldConfigLoader
        config = GoldConfigLoader.load('xauusd_scanner/config_gold.json')
        print("✓ Gold Scalp config loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Gold Scalp config failed: {e}")
        return False

def test_us30_scalp():
    """Test US30 scalp config."""
    try:
        from us30_scanner.us30_config_loader import US30ConfigLoader
        config = US30ConfigLoader.load('us30_scanner/config_us30_scalp.json')
        print("✓ US30 Scalp config loaded successfully")
        return True
    except Exception as e:
        print(f"✗ US30 Scalp config failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing configuration loading...\n")
    
    results = []
    results.append(test_btc_scalp())
    results.append(test_gold_scalp())
    results.append(test_us30_scalp())
    
    print(f"\n{sum(results)}/{len(results)} configs loaded successfully")
    
    if not all(results):
        sys.exit(1)
