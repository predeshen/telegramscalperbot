"""WebSocket streamer for real-time market data."""
import json
import threading
import time
import websocket
from datetime import datetime
from typing import Callable, Dict, List
import logging


logger = logging.getLogger(__name__)


class BinanceWebSocketStreamer:
    """
    WebSocket client for Binance real-time kline (candlestick) streams.
    
    Connects to Binance WebSocket API and streams real-time candlestick updates.
    Note: This is disabled by default. Use polling mode instead for better compatibility.
    """
    
    def __init__(self, symbol: str, timeframes: List[str], on_candle_callback: Callable):
        """
        Initialize WebSocket streamer.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT' - note: no slash for Binance WS)
            timeframes: List of timeframes (e.g., ['1m', '5m'])
            on_candle_callback: Callback function(timeframe, candle_dict) called on new data
        """
        self.symbol = symbol.replace('/', '').lower()  # Convert BTC/USDT -> btcusdt
        self.timeframes = timeframes
        self.on_candle_callback = on_candle_callback
        
        self.ws = None
        self.ws_thread = None
        self._running = False
        self._connected = False
        
        # Build WebSocket URL for multiple streams
        streams = [f"{self.symbol}@kline_{tf}" for tf in timeframes]
        self.ws_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        
        logger.info(f"Initialized WebSocket streamer for {symbol} on timeframes {timeframes}")
    
    def start(self) -> None:
        """Start WebSocket connection in background thread."""
        if self._running:
            logger.warning("WebSocket streamer already running")
            return
        
        self._running = True
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()
        logger.info("WebSocket streamer started")
    
    def stop(self) -> None:
        """Stop WebSocket connection and cleanup."""
        self._running = False
        if self.ws:
            self.ws.close()
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
        logger.info("WebSocket streamer stopped")
    
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected."""
        return self._connected
    
    def _run_websocket(self) -> None:
        """Main WebSocket loop (runs in background thread)."""
        while self._running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_open=self._on_open
                )
                
                # Run WebSocket (blocking call)
                self.ws.run_forever()
                
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self._connected = False
            
            # Wait before reconnecting
            if self._running:
                logger.info("WebSocket disconnected, reconnecting in 5s...")
                time.sleep(5)
    
    def _on_open(self, ws) -> None:
        """Called when WebSocket connection is established."""
        self._connected = True
        logger.info("WebSocket connection established")
    
    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """Called when WebSocket connection is closed."""
        self._connected = False
        logger.warning(f"WebSocket connection closed: {close_status_code} - {close_msg}")
    
    def _on_error(self, ws, error) -> None:
        """Called when WebSocket encounters an error."""
        logger.error(f"WebSocket error: {error}")
        self._connected = False
    
    def _on_message(self, ws, message: str) -> None:
        """
        Called when WebSocket receives a message.
        
        Args:
            ws: WebSocket instance
            message: JSON message string
        """
        try:
            data = json.loads(message)
            
            # Binance sends data in 'data' field for combined streams
            if 'data' not in data:
                return
            
            kline_data = data['data']
            
            # Extract kline information
            if kline_data.get('e') != 'kline':
                return
            
            kline = kline_data['k']
            
            # Extract timeframe (e.g., '1m', '5m')
            timeframe = kline['i']
            
            # Parse candle data
            candle = {
                'timestamp': pd.to_datetime(kline['t'], unit='ms'),
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v']),
                'is_closed': kline['x']  # True if candle is closed
            }
            
            # Calculate latency
            current_time = datetime.now()
            candle_time = candle['timestamp']
            latency = (current_time - candle_time).total_seconds()
            
            if latency > 2.0:
                logger.warning(f"High latency detected: {latency:.2f}s for {timeframe}")
            
            # Call callback with parsed candle
            self.on_candle_callback(timeframe, candle)
            
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")


# Import pandas here to avoid circular import
import pandas as pd
