"""Gold (XAU/USD) Scalping Scanner - 1m and 5m timeframes"""
from src.base_scanner import BaseScanner


class GoldScalpScanner(BaseScanner):
    """Gold scalping scanner for 1m and 5m timeframes"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize Gold scalp scanner"""
        asset_config = {
            'min_confluence_factors': 4,
            'min_confidence_score': 3,
            'volume_thresholds': {
                'scalp': 1.4,
                'swing': 1.3,
                'trend_alignment': 0.9,
                'breakout': 1.4,
                'mean_reversion': 1.6,
                'momentum_shift': 1.4
            }
        }
        
        super().__init__(
            scanner_name="Gold Scalp Scanner",
            symbol="XAUUSD",
            timeframes=["1m", "5m"],
            config_path=config_path,
            asset_config=asset_config
        )

