"""BTC Scalping Scanner - 1m and 5m timeframes"""
from src.base_scanner import BaseScanner


class BTCScalpScanner(BaseScanner):
    """BTC scalping scanner for 1m and 5m timeframes"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialize BTC scalp scanner.
        
        Args:
            config_path: Path to configuration file
        """
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
            scanner_name="BTC Scalp Scanner",
            symbol="BTC",
            timeframes=["1m", "5m"],
            config_path=config_path,
            asset_config=asset_config
        )

