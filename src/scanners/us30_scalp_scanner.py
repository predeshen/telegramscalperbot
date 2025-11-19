"""US30 (Dow Jones) Scalping Scanner - 1m and 5m timeframes"""
from src.base_scanner import BaseScanner


class US30ScalpScanner(BaseScanner):
    """US30 scalping scanner for 1m and 5m timeframes"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize US30 scalp scanner"""
        asset_config = {
            'min_confluence_factors': 4,
            'min_confidence_score': 3,
            'volume_thresholds': {
                'momentum': 1.5,
                'trend_alignment': 1.0,
                'breakout': 1.5,
                'mean_reversion': 1.6,
                'momentum_shift': 1.5
            }
        }
        
        super().__init__(
            scanner_name="US30 Scalp Scanner",
            symbol="US30",
            timeframes=["1m", "5m"],
            config_path=config_path,
            asset_config=asset_config
        )

