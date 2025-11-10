"""Test unified strategies with live market data across all 6 scanners."""

import sys
import logging
from datetime import datetime
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import required modules
from src.signal_detector import SignalDetector
from src.indicator_calculator import IndicatorCalculator
from src.yfinance_client import YFinanceClient
from src.strategy_registry import StrategyRegistry
from src.strategy_orchestrator import StrategyOrchestrator

# Define all 6 scanners with their configurations
SCANNERS = {
    'btc_scalp': {
        'symbol': 'BTC-USD',
        'display_name': 'BTC Scalp',
        'timeframe': '5m',
        'config_path': 'config/config.json'
    },
    'btc_swing': {
        'symbol': 'BTC-USD',
        'display_name': 'BTC Swing',
        'timeframe': '4h',
        'config_path': 'config/config.json'
    },
    'us30_scalp': {
        'symbol': '^DJI',
        'display_name': 'US30 Scalp',
        'timeframe': '5m',
        'config_path': 'us30_scanner/config_us30_scalp.json'
    },
    'us30_swing': {
        'symbol': '^DJI',
        'display_name': 'US30 Swing',
        'timeframe': '4h',
        'config_path': 'us30_scanner/config_us30_scalp.json'
    },
    'gold_scalp': {
        'symbol': 'GC=F',
        'display_name': 'Gold Scalp',
        'timeframe': '5m',
        'config_path': 'xauusd_scanner/config_gold.json'
    },
    'gold_swing': {
        'symbol': 'GC=F',
        'display_name': 'Gold Swing',
        'timeframe': '4h',
        'config_path': 'xauusd_scanner/config_gold.json'
    }
}

# Define all 4 unified strategies
STRATEGIES = [
    ('fibonacci_retracement', 'Fibonacci Retracement'),
    ('support_resistance_bounce', 'Support/Resistance Bounce'),
    ('key_level_break_retest', 'Key Level Break & Retest'),
    ('adx_rsi_momentum', 'ADX+RSI+Momentum')
]

def load_scanner_config(config_path: str) -> dict:
    """Load scanner configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}


def test_scanner_strategies(scanner_id: str, scanner_config: dict):
    """Test all 4 unified strategies on a specific scanner."""
    logger.info("\n" + "=" * 80)
    logger.info(f"Testing {scanner_config['display_name']} Scanner")
    logger.info("=" * 80)
    
    results = {
        'scanner': scanner_id,
        'display_name': scanner_config['display_name'],
        'symbol': scanner_config['symbol'],
        'timeframe': scanner_config['timeframe'],
        'strategies_tested': 0,
        'strategies_passed': 0,
        'signals_found': 0,
        'errors': []
    }
    
    try:
        # Load configuration
        config = load_scanner_config(scanner_config['config_path'])
        if not config:
            results['errors'].append("Failed to load config")
            return results
        
        # Initialize components
        logger.info(f"Initializing components for {scanner_config['display_name']}...")
        
        # Create YFinance client with proper parameters
        timeframes = [scanner_config['timeframe']]
        price_offset = config.get('exchange', {}).get('price_offset', 0.0)
        
        client = YFinanceClient(
            symbol=scanner_config['symbol'],
            timeframes=timeframes,
            buffer_size=200,
            price_offset=price_offset
        )
        
        # Connect and fetch data
        if not client.connect():
            results['errors'].append("Failed to connect to data source")
            return results
        
        logger.info(f"Fetching {scanner_config['timeframe']} data for {scanner_config['symbol']}...")
        raw_data = client.get_latest_candles(scanner_config['timeframe'], count=200)
        
        if raw_data.empty:
            results['errors'].append("No data fetched")
            return results
        
        logger.info(f"✓ Fetched {len(raw_data)} candles")
        
        # Calculate indicators - this should expose any data issues
        calculator = IndicatorCalculator()
        data = calculator.calculate_all_indicators(raw_data)
        logger.info(f"✓ Calculated indicators")
        
        # Initialize signal detector
        detector = SignalDetector()
        
        # Test each strategy
        logger.info("\n" + "-" * 80)
        logger.info("Testing Strategies:")
        logger.info("-" * 80)
        
        for strategy_id, strategy_name in STRATEGIES:
            results['strategies_tested'] += 1
            
            logger.info(f"\n🔍 {strategy_name}")
            
            try:
                # Check if strategy is enabled for this scanner
                strategy_config = config.get('strategies', {}).get(strategy_id, {})
                if not strategy_config.get('enabled', False):
                    logger.info(f"   ⚠️  Strategy disabled in config")
                    continue
                
                # Check if this scanner is in the allowed list
                allowed_scanners = strategy_config.get('scanners', [])
                if scanner_id not in allowed_scanners:
                    logger.info(f"   ⚠️  Scanner not in allowed list: {allowed_scanners}")
                    continue
                
                # Get the strategy method
                method_map = {
                    'fibonacci_retracement': detector._detect_fibonacci_retracement,
                    'support_resistance_bounce': detector._detect_support_resistance_bounce,
                    'key_level_break_retest': detector._detect_key_level_break_retest,
                    'adx_rsi_momentum': detector._detect_adx_rsi_momentum_confluence
                }
                
                strategy_method = method_map.get(strategy_id)
                if not strategy_method:
                    logger.error(f"   ❌ Strategy method not found")
                    results['errors'].append(f"{strategy_name}: method not found")
                    continue
                
                # Execute strategy
                signal = strategy_method(
                    data, 
                    timeframe=scanner_config['timeframe'],
                    symbol=scanner_config['symbol']
                )
                
                if signal:
                    results['signals_found'] += 1
                    results['strategies_passed'] += 1
                    logger.info(f"   ✅ SIGNAL DETECTED")
                    logger.info(f"      Type: {signal.signal_type}")
                    logger.info(f"      Entry: ${signal.entry_price:,.2f}")
                    logger.info(f"      Stop Loss: ${signal.stop_loss:,.2f}")
                    logger.info(f"      Take Profit: ${signal.take_profit:,.2f}")
                    logger.info(f"      Risk/Reward: {signal.risk_reward:.2f}")
                    logger.info(f"      Confidence: {signal.confidence}/5")
                else:
                    results['strategies_passed'] += 1
                    logger.info(f"   ✓ No signal (strategy executed successfully)")
                    
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
                results['errors'].append(f"{strategy_name}: {str(e)}")
        
        # Cleanup
        client.close()
        
        logger.info("\n" + "-" * 80)
        logger.info(f"Scanner Test Complete:")
        logger.info(f"  Strategies Tested: {results['strategies_tested']}")
        logger.info(f"  Strategies Passed: {results['strategies_passed']}")
        logger.info(f"  Signals Found: {results['signals_found']}")
        if results['errors']:
            logger.info(f"  Errors: {len(results['errors'])}")
        logger.info("-" * 80)
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing {scanner_config['display_name']}: {e}", exc_info=True)
        results['errors'].append(f"Fatal error: {str(e)}")
        return results


def test_all_scanners():
    """Test all 4 strategies on all 6 scanners."""
    logger.info("\n" + "=" * 80)
    logger.info("UNIFIED STRATEGY VALIDATION")
    logger.info("Testing 4 strategies across 6 scanners with live data")
    logger.info("=" * 80)
    
    all_results = []
    
    for scanner_id, scanner_config in SCANNERS.items():
        result = test_scanner_strategies(scanner_id, scanner_config)
        all_results.append(result)
    
    return all_results


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("UNIFIED STRATEGY LIVE DATA TEST")
    logger.info("=" * 80)
    logger.info("Testing: 4 strategies × 6 scanners = 24 test cases")
    logger.info("Strategies: Fibonacci, Support/Resistance, Key Level, ADX+RSI")
    logger.info("Scanners: BTC Scalp/Swing, US30 Scalp/Swing, Gold Scalp/Swing")
    logger.info("=" * 80)
    
    # Run all tests
    all_results = test_all_scanners()
    
    # Generate summary report
    logger.info("\n" + "=" * 80)
    logger.info("FINAL TEST SUMMARY")
    logger.info("=" * 80)
    
    total_scanners = len(all_results)
    total_strategies_tested = sum(r['strategies_tested'] for r in all_results)
    total_strategies_passed = sum(r['strategies_passed'] for r in all_results)
    total_signals_found = sum(r['signals_found'] for r in all_results)
    total_errors = sum(len(r['errors']) for r in all_results)
    
    logger.info(f"\nScanners Tested: {total_scanners}")
    logger.info(f"Total Strategy Tests: {total_strategies_tested}")
    logger.info(f"Tests Passed: {total_strategies_passed}")
    logger.info(f"Tests Failed: {total_strategies_tested - total_strategies_passed}")
    logger.info(f"Signals Found: {total_signals_found}")
    logger.info(f"Total Errors: {total_errors}")
    
    logger.info("\n" + "-" * 80)
    logger.info("Per-Scanner Results:")
    logger.info("-" * 80)
    
    for result in all_results:
        status = "✅" if result['strategies_passed'] == result['strategies_tested'] and not result['errors'] else "⚠️"
        logger.info(f"{status} {result['display_name']:20s} | Tested: {result['strategies_tested']} | Passed: {result['strategies_passed']} | Signals: {result['signals_found']}")
        
        if result['errors']:
            for error in result['errors']:
                logger.info(f"     ❌ {error}")
    
    # Determine overall success
    all_passed = (total_strategies_passed == total_strategies_tested) and (total_errors == 0)
    
    logger.info("\n" + "=" * 80)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("All 4 unified strategies are working correctly on all 6 scanners.")
        logger.info("The system is ready for live trading.")
        sys.exit(0)
    else:
        logger.warning("⚠️  SOME TESTS HAD ISSUES")
        logger.warning("Review the errors above. Strategies may still work but need attention.")
        sys.exit(1)
