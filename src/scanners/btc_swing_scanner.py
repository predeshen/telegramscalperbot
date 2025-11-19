"""BTC Swing Scanner - 15m and 1h timeframes"""
from src.base_scanner import BaseScanner


class BTCSwingScanner(BaseScanner):
    """BTC swing scanner for 15m and 1h timeframes"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize BTC swing scanner"""
        asset_config = {
            'min_confluence_factors': 4,
            'min_confidence_score': 3,
            'volume_thresholds': {
                'scalp': 1.3,
                'swing': 1.2,
                'trend_alignment': 0.8,
                'breakout': 1.3,
                'mean_reversion': 1.5,
                'momentum_shift': 1.3
            }
        }
        
        super().__init__(
            scanner_name="BTC Swing Scanner",
            symbol="BTC",
            timeframes=["15m", "1h"],
            config_path=config_path,
            asset_config=asset_config
        )

