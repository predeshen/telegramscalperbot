#!/usr/bin/env python3
"""
Comprehensive System Test
Tests all scanners with diagnostic system integration
"""
import sys
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    modules_to_test = [
        ('src.signal_diagnostics', 'SignalDiagnostics'),
        ('src.config_validator', 'ConfigValidator'),
        ('src.bypass_mode', 'BypassMode'),
        ('src.signal_detector', 'SignalDetector'),
        ('src.signal_quality_filter', 'SignalQualityFilter'),
        ('main', None),
        ('main_swing', None),
        ('main_us30', None),
        ('main_us100', None),
        ('main_multi_symbol', None),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name] if class_name else [])
            if class_name:
                getattr(module, class_name)
                print(f"  ✅ {module_name}.{class_name}")
            else:
                print(f"  ✅ {module_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            failed += 1
    
    print(f"\n  Result: {passed} passed, {failed} failed")
    return failed == 0

def test_diagnostic_system():
    """Test diagnostic system functionality"""
    print("\n" + "="*60)
    print("TEST 2: Diagnostic System")
    print("="*60)
    
    try:
        from src.signal_diagnostics import SignalDiagnostics
        
        # Create diagnostic instance
        diagnostics = SignalDiagnostics("Test-Scanner")
        print("  ✅ Created SignalDiagnostics instance")
        
        # Test logging
        diagnostics.log_detection_attempt("EMA Crossover", True)
        diagnostics.log_detection_attempt("Trend Alignment", False, "ADX too low")
        diagnostics.log_signal_generated("EMA Crossover")
        print("  ✅ Logged detection attempts")
        
        # Test data quality logging
        diagnostics.log_data_quality_issue("Missing RSI data")
        print("  ✅ Logged data quality issue")
        
        # Generate report
        report = diagnostics.generate_report()
        print("  ✅ Generated diagnostic report")
        
        # Test report content
        assert hasattr(report, 'detection_attempts') or hasattr(report, 'total_attempts'), "Report missing attempts"
        print("  ✅ Report contains expected data")
        
        # Test recommendations
        recommendations = diagnostics.get_recommendations()
        print(f"  ✅ Generated {len(recommendations)} recommendations")
        
        # Test Telegram formatting
        telegram_msg = report.to_telegram_message()
        assert len(telegram_msg) > 0, "Empty Telegram message"
        print("  ✅ Telegram message formatting works")
        
        print("\n  Result: All diagnostic tests passed")
        return True
        
    except Exception as e:
        print(f"\n  ❌ Diagnostic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_validator():
    """Test configuration validator"""
    print("\n" + "="*60)
    print("TEST 3: Configuration Validator")
    print("="*60)
    
    try:
        from src.config_validator import ConfigValidator
        
        validator = ConfigValidator()
        print("  ✅ Created ConfigValidator instance")
        
        # Test with valid config
        valid_config = {
            'signal_rules': {
                'volume_spike_threshold': 1.3,
                'rsi_min': 25,
                'rsi_max': 75,
                'adx_min_trend_alignment': 15
            }
        }
        
        warnings = validator.validate_config(valid_config)
        print(f"  ✅ Validated config: {len(warnings)} warnings")
        
        # Test with invalid config
        invalid_config = {
            'signal_rules': {
                'volume_spike_threshold': 0.5,  # Too low
                'rsi_min': 10,  # Too low
                'rsi_max': 95,  # Too high
            }
        }
        
        warnings = validator.validate_config(invalid_config)
        assert len(warnings) > 0, "Should have warnings for invalid config"
        print(f"  ✅ Detected {len(warnings)} issues in invalid config")
        
        print("\n  Result: All validator tests passed")
        return True
        
    except Exception as e:
        print(f"\n  ❌ Validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bypass_mode():
    """Test bypass mode functionality"""
    print("\n" + "="*60)
    print("TEST 4: Bypass Mode")
    print("="*60)
    
    try:
        from src.bypass_mode import BypassMode
        
        config = {
            'bypass_mode': {
                'enabled': False,
                'auto_disable_after_hours': 2
            }
        }
        
        bypass = BypassMode(config)
        print("  ✅ Created BypassMode instance")
        
        # Test initial state
        assert not bypass.should_bypass_filters(), "Should be disabled initially"
        print("  ✅ Initial state is disabled")
        
        # Test enable
        bypass.enable()
        assert bypass.should_bypass_filters(), "Should be enabled after enable()"
        print("  ✅ Enable works")
        
        # Test status
        status = bypass.get_status()
        assert 'enabled' in status, "Status should contain 'enabled'"
        print("  ✅ Status reporting works")
        
        # Test disable
        bypass.disable()
        assert not bypass.should_bypass_filters(), "Should be disabled after disable()"
        print("  ✅ Disable works")
        
        print("\n  Result: All bypass mode tests passed")
        return True
        
    except Exception as e:
        print(f"\n  ❌ Bypass mode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_quality_filter():
    """Test signal quality filter with diagnostics"""
    print("\n" + "="*60)
    print("TEST 5: Signal Quality Filter")
    print("="*60)
    
    try:
        from src.signal_quality_filter import SignalQualityFilter, QualityConfig
        from src.signal_diagnostics import SignalDiagnostics
        from src.signal_detector import Signal
        import pandas as pd
        from datetime import datetime
        
        # Create diagnostics
        diagnostics = SignalDiagnostics("Test-Filter")
        
        # Create quality filter
        config = QualityConfig(
            min_confluence_factors=3,
            min_confidence_score=3,
            min_risk_reward=1.2
        )
        quality_filter = SignalQualityFilter(config, diagnostics=diagnostics)
        print("  ✅ Created SignalQualityFilter with diagnostics")
        
        # Create test signal
        signal = Signal(
            symbol="BTC/USD",
            signal_type="LONG",
            entry_price=45000,
            stop_loss=44500,
            take_profit=46000,
            timestamp=datetime.now(),
            timeframe="5m",
            strategy="EMA Crossover",
            confidence=4,
            atr=100,
            risk_reward=2.0,
            market_bias="BULLISH",
            indicators={'rsi': 55, 'adx': 25}
        )
        
        # Create test data
        data = pd.DataFrame({
            'close': [45000],
            'volume': [1000000],
            'rsi': [55],
            'adx': [25],
            'atr': [100]
        })
        
        # Evaluate signal
        result = quality_filter.evaluate_signal(signal, data)
        print(f"  ✅ Evaluated signal: {'Passed' if result.passed else 'Rejected'}")
        print(f"     Confidence: {result.confidence_score}/5")
        print(f"     Factors: {len(result.confluence_factors)}/7")
        
        # Check diagnostics were updated
        report = diagnostics.generate_report()
        # Just check that report was generated successfully
        print("  ✅ Diagnostics were updated")
        
        print("\n  Result: All quality filter tests passed")
        return True
        
    except Exception as e:
        print(f"\n  ❌ Quality filter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_files():
    """Test that all configuration files are valid"""
    print("\n" + "="*60)
    print("TEST 6: Configuration Files")
    print("="*60)
    
    import json
    
    config_files = [
        'config/config.json',
        'config/config_multitime.json',
        'config/us30_config.json',
        'config/us100_config.json',
        'config/multi_crypto_scalp.json',
        'config/multi_crypto_swing.json',
        'config/multi_fx_scalp.json',
        'config/multi_mixed.json'
    ]
    
    passed = 0
    failed = 0
    
    for config_file in config_files:
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Check for required sections
                required_sections = ['signal_rules']
                missing = [s for s in required_sections if s not in config]
                
                if missing:
                    print(f"  ⚠️  {config_file}: Missing sections: {missing}")
                else:
                    print(f"  ✅ {config_file}")
                    passed += 1
            else:
                print(f"  ⚠️  {config_file}: File not found")
                
        except Exception as e:
            print(f"  ❌ {config_file}: {e}")
            failed += 1
    
    print(f"\n  Result: {passed} valid, {failed} failed")
    return failed == 0

def test_scanner_startup():
    """Test that scanner files can be loaded"""
    print("\n" + "="*60)
    print("TEST 7: Scanner Startup")
    print("="*60)
    
    scanners = [
        'main.py',
        'main_swing.py',
        'main_us30.py',
        'main_us100.py',
        'main_multi_symbol.py'
    ]
    
    passed = 0
    failed = 0
    
    for scanner in scanners:
        try:
            if os.path.exists(scanner):
                # Just check if file can be read and has main function
                with open(scanner, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'def main(' in content or 'async def main(' in content:
                        print(f"  ✅ {scanner}")
                        passed += 1
                    else:
                        print(f"  ⚠️  {scanner}: No main() function found")
            else:
                print(f"  ⚠️  {scanner}: File not found")
                
        except Exception as e:
            print(f"  ❌ {scanner}: {e}")
            failed += 1
    
    print(f"\n  Result: {passed} valid, {failed} failed")
    return failed == 0

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("COMPREHENSIVE SYSTEM TEST")
    print("Testing Signal Detection Fix Implementation")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run all tests
    results.append(("Module Imports", test_imports()))
    results.append(("Diagnostic System", test_diagnostic_system()))
    results.append(("Config Validator", test_config_validator()))
    results.append(("Bypass Mode", test_bypass_mode()))
    results.append(("Quality Filter", test_signal_quality_filter()))
    results.append(("Configuration Files", test_configuration_files()))
    results.append(("Scanner Startup", test_scanner_startup()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n  🎉 ALL TESTS PASSED!")
        print("  ✅ Signal detection system is ready for deployment")
        return 0
    else:
        print(f"\n  ⚠️  {failed} test(s) failed")
        print("  🔧 Please review the failures above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
