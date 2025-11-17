#!/usr/bin/env python3
"""Quick test to verify US30 scanner fix"""

import sys
from src.us30_strategy import US30Strategy

try:
    # Try to initialize the strategy
    config = {
        'us30_strategy': {
            'min_fvg_percent': 0.05,
            'swing_lookback': 5,
            'min_break_percent': 0.1,
            'min_adx': 25,
            'min_volume_ratio': 1.2,
            'min_candle_body_percent': 60,
            'initial_tp_atr': 2.5,
            'stop_loss_atr': 1.5,
            'trail_after_atr': 1.5
        }
    }
    
    strategy = US30Strategy(config=config)
    print("✅ US30Strategy initialized successfully!")
    print(f"   - FVG Detector: {strategy.fvg_detector}")
    print(f"   - Structure Analyzer: {strategy.structure_analyzer}")
    print(f"   - Min ADX: {strategy.min_adx}")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Error initializing US30Strategy: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
