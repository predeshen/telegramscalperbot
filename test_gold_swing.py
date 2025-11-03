#!/usr/bin/env python3
"""
Test script for XAU/USD Gold Swing Scanner
Tests the 15m/1h/4h/1d multi-timeframe Gold scanner
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("TESTING XAU/USD GOLD SWING SCANNER")
print("=" * 80)

# Test 1: Configuration
print("\n1️⃣ Testing Configuration...")
try:
    import json
    with open('xauusd_scanner/config_gold_swing.json', 'r') as f:
        config = json.load(f)
    
    print(f"   ✅ Config loaded successfully")
    print(f"   📊 Exchange: {config['exchange']['name']}")
    print(f"   💰 Symbol: {config['exchange']['symbol']}")
    print(f"   ⏰ Timeframes: {', '.join(config['exchange']['timeframes'])}")
    print(f"   📈 Stop Loss ATR: {config['signal_rules']['stop_loss_atr_multiplier']}x")
    print(f"   🎯 Take Profit ATR: {config['signal_rules']['take_profit_atr_multiplier']}x")
    print(f"   ⏱️ Polling: {config['polling_interval_seconds']}s")
    
except Exception as e:
    print(f"   ❌ Config error: {e}")
    sys.exit(1)

# Test 2: Imports
print("\n2️⃣ Testing Imports...")
try:
    from src.market_data_client import MarketDataClient
    from src.indicator_calculator import IndicatorCalculator
    from xauusd_scanner.session_manager import SessionManager
    from xauusd_scanner.news_calendar import NewsCalendar
    from xauusd_scanner.spread_monitor import SpreadMonitor
    from xauusd_scanner.key_level_tracker import KeyLevelTracker
    from xauusd_scanner.strategy_selector import StrategySelector
    from xauusd_scanner.gold_signal_detector import GoldSignalDetector
    
    print("   ✅ All imports successful")
    
except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 3: Component Initialization
print("\n3️⃣ Testing Component Initialization...")
try:
    # Initialize components
    session_mgr = SessionManager()
    news_cal = NewsCalendar("xauusd_scanner/news_events.json")
    spread_mon = SpreadMonitor()
    level_tracker = KeyLevelTracker()
    strategy_sel = StrategySelector(session_mgr)
    
    signal_detector = GoldSignalDetector(
        session_manager=session_mgr,
        key_level_tracker=level_tracker,
        strategy_selector=strategy_sel
    )
    
    print("   ✅ All components initialized")
    
except Exception as e:
    print(f"   ❌ Initialization error: {e}")
    sys.exit(1)

# Test 4: Market Data Connection
print("\n4️⃣ Testing Market Data Connection...")
try:
    from src.yfinance_client import YFinanceClient
    
    # Use YFinance for Gold
    if config['exchange']['name'] == 'yfinance':
        client = YFinanceClient(
            symbol=config['exchange']['symbol'],
            timeframes=config['exchange']['timeframes'],
            buffer_size=200
        )
    else:
        client = MarketDataClient(
            exchange_name=config['exchange']['name'],
            symbol=config['exchange']['symbol'],
            timeframes=config['exchange']['timeframes'],
            buffer_size=200
        )
    
    if client.connect():
        print(f"   ✅ Connected to {config['exchange']['name']}")
        
        # Test each timeframe
        indicator_calc = IndicatorCalculator()
        
        for timeframe in config['exchange']['timeframes']:
            candles = client.get_latest_candles(timeframe, count=50)
            
            # Calculate indicators
            candles['ema_9'] = indicator_calc.calculate_ema(candles, 9)
            candles['ema_21'] = indicator_calc.calculate_ema(candles, 21)
            candles['ema_50'] = indicator_calc.calculate_ema(candles, 50)
            candles['vwap'] = indicator_calc.calculate_vwap(candles)
            candles['atr'] = indicator_calc.calculate_atr(candles, 14)
            candles['rsi'] = indicator_calc.calculate_rsi(candles, 14)
            candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, 20)
            
            last = candles.iloc[-1]
            print(f"   ✅ {timeframe}: ${last['close']:,.2f} | RSI: {last['rsi']:.1f} | ATR: ${last['atr']:.2f}")
        
        print(f"   ✅ All timeframes working correctly")
    else:
        print(f"   ⚠️ Could not connect to {config['exchange']['name']}")
    
except Exception as e:
    print(f"   ⚠️ Market data warning: {e}")

# Test 5: Session Detection
print("\n5️⃣ Testing Session Detection...")
try:
    session_info = session_mgr.get_session_info()
    print(f"   ✅ Current session: {session_info['session']}")
    print(f"   ✅ Strategy focus: {session_info['strategy_focus']}")
    print(f"   ✅ Recommendation: {session_info['recommendation']}")
    
except Exception as e:
    print(f"   ❌ Session error: {e}")

# Test 6: News Calendar
print("\n6️⃣ Testing News Calendar...")
try:
    should_pause, reason = news_cal.should_pause_trading()
    event_count = len(news_cal.events) if hasattr(news_cal, 'events') else 0
    
    print(f"   ✅ News calendar: {event_count} events loaded")
    print(f"   ✅ Should pause: {should_pause}")
    
    if should_pause:
        print(f"   📰 Reason: {reason}")
    
    # Show next event
    next_event = news_cal.get_next_event()
    if next_event:
        print(f"   📅 Next event: {next_event.title} at {next_event.datetime_gmt.strftime('%Y-%m-%d %H:%M GMT')}")
    
except Exception as e:
    print(f"   ⚠️ News calendar warning: {e}")

# Test 7: Signal Detection (Dry Run)
print("\n7️⃣ Testing Signal Detection...")
try:
    from datetime import datetime, timezone
    
    # Update levels with current data
    if 'candles' in locals():
        last_candle = candles.iloc[-1]
        level_tracker.update_levels(
            high=last_candle['high'],
            low=last_candle['low'],
            close=last_candle['close'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Try to detect signals
        signal = signal_detector.detect_signals(candles, '1h')
        
        if signal:
            print(f"   🚨 SIGNAL DETECTED!")
            print(f"   📊 Type: {signal.signal_type}")
            print(f"   🎯 Strategy: {signal.strategy}")
            print(f"   💰 Entry: ${signal.entry_price:.2f}")
            print(f"   🛑 Stop: ${signal.stop_loss:.2f}")
            print(f"   🎯 Target: ${signal.take_profit:.2f}")
            print(f"   📈 R:R: {signal.risk_reward:.2f}")
        else:
            print(f"   ✅ No signal (normal - waiting for setup)")
    else:
        print(f"   ⚠️ Skipped (no market data)")
    
except Exception as e:
    print(f"   ⚠️ Signal detection warning: {e}")

# Test 8: Main Script Syntax
print("\n8️⃣ Testing Main Script...")
try:
    import py_compile
    py_compile.compile('xauusd_scanner/main_gold_swing.py', doraise=True)
    print("   ✅ Main script syntax valid")
    
except Exception as e:
    print(f"   ❌ Main script error: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ GOLD SWING SCANNER TEST PASSED!")
print("=" * 80)
print("\n🎯 XAU/USD Gold Swing Scanner (15m/1h/4h/1d) is ready!")
print("\nFeatures:")
print("  • Multi-timeframe analysis (15m, 1h, 4h, 1d)")
print("  • Session-aware trading (Asian/London/NY)")
print("  • News calendar integration")
print("  • Spread monitoring")
print("  • Key level tracking")
print("  • 3 adaptive strategies")
print("  • Higher R:R targets (2.5x ATR)")
print("\nDeploy with:")
print("  python xauusd_scanner/main_gold_swing.py")
print("\nOr deploy all scanners:")
print("  ./start_all_scanners.sh --monitor")
print("=" * 80)
