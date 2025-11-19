"""
Scanner Orchestrator
Manages all 8 scanner instances with unified control and monitoring.
"""
import logging
import threading
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ScannerOrchestrator:
    """
    Orchestrates all 8 trading scanners.
    
    Provides:
    - Unified start/stop/restart for all scanners
    - Individual scanner status monitoring
    - Health checking and error recovery
    - Centralized logging and reporting
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialize scanner orchestrator.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.scanners: Dict[str, any] = {}
        self.scanner_threads: Dict[str, threading.Thread] = {}
        self.running = False
        
        logger.info("Scanner Orchestrator initialized")
    
    def initialize_all_scanners(self) -> bool:
        """
        Initialize all 8 scanners.
        
        Returns:
            True if all scanners initialized successfully
        """
        try:
            from src.scanners import (
                BTCScalpScanner,
                BTCSwingScanner,
                GoldScalpScanner,
                GoldSwingScanner,
                US30ScalpScanner,
                US30SwingScanner,
                US100Scanner,
                MultiCryptoScanner
            )
            
            scanner_classes = [
                ('btc_scalp', BTCScalpScanner),
                ('btc_swing', BTCSwingScanner),
                ('gold_scalp', GoldScalpScanner),
                ('gold_swing', GoldSwingScanner),
                ('us30_scalp', US30ScalpScanner),
                ('us30_swing', US30SwingScanner),
                ('us100', US100Scanner),
                ('multi_crypto', MultiCryptoScanner)
            ]
            
            for scanner_id, scanner_class in scanner_classes:
                try:
                    logger.info(f"Initializing {scanner_id} scanner...")
                    scanner = scanner_class(self.config_path)
                    self.scanners[scanner_id] = scanner
                    logger.info(f"✓ {scanner_id} scanner initialized")
                except Exception as e:
                    logger.error(f"✗ Failed to initialize {scanner_id} scanner: {e}")
                    return False
            
            logger.info(f"✓ All {len(self.scanners)} scanners initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing scanners: {e}", exc_info=True)
            return False
    
    def start_all_scanners(self) -> bool:
        """
        Start all scanners.
        
        Returns:
            True if all scanners started successfully
        """
        try:
            logger.info("Starting all scanners...")
            
            if not self.scanners:
                logger.error("No scanners initialized. Call initialize_all_scanners() first.")
                return False
            
            # Start each scanner
            for scanner_id, scanner in self.scanners.items():
                try:
                    logger.info(f"Starting {scanner_id} scanner...")
                    
                    if not scanner.start():
                        logger.error(f"Failed to start {scanner_id} scanner")
                        return False
                    
                    # Start polling thread
                    thread = threading.Thread(
                        target=scanner.run_polling_loop,
                        args=(10,),  # 10-second polling interval
                        daemon=True,
                        name=f"{scanner_id}_thread"
                    )
                    thread.start()
                    self.scanner_threads[scanner_id] = thread
                    
                    logger.info(f"✓ {scanner_id} scanner started")
                    
                except Exception as e:
                    logger.error(f"Error starting {scanner_id} scanner: {e}")
                    return False
            
            self.running = True
            logger.info(f"✓ All {len(self.scanners)} scanners started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting scanners: {e}", exc_info=True)
            return False
    
    def stop_all_scanners(self) -> bool:
        """
        Stop all scanners.
        
        Returns:
            True if all scanners stopped successfully
        """
        try:
            logger.info("Stopping all scanners...")
            
            # Stop each scanner
            for scanner_id, scanner in self.scanners.items():
                try:
                    logger.info(f"Stopping {scanner_id} scanner...")
                    scanner.stop()
                    logger.info(f"✓ {scanner_id} scanner stopped")
                except Exception as e:
                    logger.error(f"Error stopping {scanner_id} scanner: {e}")
            
            # Wait for threads to finish
            for scanner_id, thread in self.scanner_threads.items():
                if thread.is_alive():
                    logger.info(f"Waiting for {scanner_id} thread to finish...")
                    thread.join(timeout=5)
            
            self.running = False
            logger.info("✓ All scanners stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping scanners: {e}", exc_info=True)
            return False
    
    def restart_all_scanners(self) -> bool:
        """
        Restart all scanners.
        
        Returns:
            True if all scanners restarted successfully
        """
        logger.info("Restarting all scanners...")
        
        if not self.stop_all_scanners():
            logger.error("Failed to stop scanners during restart")
            return False
        
        import time
        time.sleep(2)  # Wait before restarting
        
        if not self.start_all_scanners():
            logger.error("Failed to start scanners during restart")
            return False
        
        logger.info("✓ All scanners restarted successfully")
        return True
    
    def get_scanner_status(self, scanner_id: str) -> Optional[Dict]:
        """
        Get status of a specific scanner.
        
        Args:
            scanner_id: Scanner identifier
            
        Returns:
            Dictionary with scanner status, or None if not found
        """
        if scanner_id not in self.scanners:
            logger.warning(f"Scanner not found: {scanner_id}")
            return None
        
        try:
            scanner = self.scanners[scanner_id]
            status = scanner.get_status()
            
            # Add thread status
            if scanner_id in self.scanner_threads:
                thread = self.scanner_threads[scanner_id]
                status['thread_alive'] = thread.is_alive()
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting status for {scanner_id}: {e}")
            return None
    
    def get_all_scanner_status(self) -> Dict[str, Dict]:
        """
        Get status of all scanners.
        
        Returns:
            Dictionary with status for each scanner
        """
        status = {
            'orchestrator_running': self.running,
            'timestamp': datetime.now().isoformat(),
            'scanners': {}
        }
        
        for scanner_id in self.scanners.keys():
            scanner_status = self.get_scanner_status(scanner_id)
            if scanner_status:
                status['scanners'][scanner_id] = scanner_status
        
        return status
    
    def get_health_report(self) -> Dict:
        """
        Get comprehensive health report for all scanners.
        
        Returns:
            Dictionary with health information
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'orchestrator_running': self.running,
            'total_scanners': len(self.scanners),
            'active_scanners': sum(1 for s in self.scanners.values() if s.running),
            'scanners': {}
        }
        
        for scanner_id, scanner in self.scanners.items():
            try:
                status = scanner.get_status()
                report['scanners'][scanner_id] = {
                    'running': scanner.running,
                    'symbol': scanner.symbol,
                    'timeframes': scanner.timeframes,
                    'data_sources': status.get('data_source_status', {}),
                    'stale_data_count': status.get('stale_data_count', {})
                }
            except Exception as e:
                logger.error(f"Error getting health for {scanner_id}: {e}")
                report['scanners'][scanner_id] = {'error': str(e)}
        
        return report
    
    def print_status(self):
        """Print status of all scanners to console"""
        status = self.get_all_scanner_status()
        
        print("\n" + "="*80)
        print("SCANNER ORCHESTRATOR STATUS")
        print("="*80)
        print(f"Timestamp: {status['timestamp']}")
        print(f"Orchestrator Running: {status['orchestrator_running']}")
        print(f"Total Scanners: {len(status['scanners'])}")
        print()
        
        for scanner_id, scanner_status in status['scanners'].items():
            print(f"  {scanner_id.upper()}")
            print(f"    Running: {scanner_status.get('running', False)}")
            print(f"    Symbol: {scanner_status.get('symbol', 'N/A')}")
            print(f"    Timeframes: {', '.join(scanner_status.get('timeframes', []))}")
            print()
        
        print("="*80 + "\n")

