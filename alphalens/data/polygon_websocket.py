"""
Polygon.io WebSocket client for real-time market data.

Supports streaming:
- Stock trades
- Stock quotes (bid/ask)
- Stock aggregates (bars)
- Options trades and quotes
- Crypto trades
"""

from typing import Dict, Any, List, Callable, Optional
import json
import time
from threading import Thread
from loguru import logger

try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logger.warning("websocket-client not installed. Run: pip install websocket-client")


class PolygonWebSocketClient:
    """
    WebSocket client for Polygon.io real-time data.

    Subscription Channels:
    - T.*: Trades
    - Q.*: Quotes (bid/ask)
    - A.*: Aggregates (minute bars)
    - AM.*: Aggregates (minute bars)
    """

    def __init__(
        self,
        api_key: str,
        cluster: str = "stocks"  # stocks, options, forex, crypto
    ):
        """
        Initialize WebSocket client.

        Args:
            api_key: Polygon API key
            cluster: Data cluster (stocks, options, forex, crypto)
        """
        if not WEBSOCKET_AVAILABLE:
            raise ImportError("websocket-client required. Run: pip install websocket-client")

        self.api_key = api_key
        self.cluster = cluster
        self.ws_url = f"wss://socket.polygon.io/{cluster}"

        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.authenticated = False
        self.thread: Optional[Thread] = None

        # Subscriptions and callbacks
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}

        # Statistics
        self.messages_received = 0
        self.last_message_time = None

    def connect(self) -> bool:
        """
        Connect to WebSocket.

        Returns:
            True if connected successfully
        """
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            # Run in background thread
            self.thread = Thread(target=self._run_forever, daemon=True)
            self.thread.start()

            # Wait for connection
            timeout = 10
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.1)

            if self.connected:
                logger.info(f"Connected to Polygon WebSocket ({self.cluster})")
                return True
            else:
                logger.error("Connection timeout")
                return False

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        if self.ws:
            self.ws.close()
            self.connected = False
            self.authenticated = False
            logger.info("Disconnected from Polygon WebSocket")

    def _run_forever(self) -> None:
        """Run WebSocket in background thread."""
        try:
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.connected = False

    def _on_open(self, ws) -> None:
        """Handle connection opened."""
        self.connected = True
        logger.debug("WebSocket connection opened")

        # Authenticate
        auth_message = {
            "action": "auth",
            "params": self.api_key
        }
        ws.send(json.dumps(auth_message))

    def _on_message(self, ws, message: str) -> None:
        """Handle incoming message."""
        self.messages_received += 1
        self.last_message_time = time.time()

        try:
            data = json.loads(message)

            # Handle array of messages
            if isinstance(data, list):
                for msg in data:
                    self._process_message(msg)
            else:
                self._process_message(data)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _process_message(self, msg: Dict[str, Any]) -> None:
        """Process individual message."""
        msg_type = msg.get("ev")  # Event type

        # Authentication response
        if msg_type == "status":
            if msg.get("status") == "auth_success":
                self.authenticated = True
                logger.info("WebSocket authenticated")
            elif msg.get("status") == "auth_failed":
                logger.error("WebSocket authentication failed")
                self.disconnect()
            return

        # Data messages
        if msg_type:
            # Call type-specific handlers
            if msg_type in self.message_handlers:
                for handler in self.message_handlers[msg_type]:
                    try:
                        handler(msg)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")

            # Call symbol-specific handlers
            symbol = msg.get("sym")
            if symbol:
                key = f"{msg_type}:{symbol}"
                if key in self.subscriptions:
                    for callback in self.subscriptions[key]:
                        try:
                            callback(msg)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")

    def _on_error(self, ws, error) -> None:
        """Handle WebSocket error."""
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """Handle connection closed."""
        self.connected = False
        self.authenticated = False
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")

    def subscribe(
        self,
        channel: str,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to channel for symbols.

        Args:
            channel: Channel type (T=trades, Q=quotes, A=aggregates)
            symbols: List of symbols
            callback: Callback function for messages

        Example:
            client.subscribe("T", ["AAPL", "MSFT"], my_callback)
            # Subscribes to trades for AAPL and MSFT
        """
        if not self.authenticated:
            logger.warning("Not authenticated yet, waiting...")
            timeout = 5
            start = time.time()
            while not self.authenticated and (time.time() - start) < timeout:
                time.sleep(0.1)

            if not self.authenticated:
                raise RuntimeError("Not authenticated")

        # Register callbacks
        for symbol in symbols:
            key = f"{channel}:{symbol}"
            if key not in self.subscriptions:
                self.subscriptions[key] = []
            self.subscriptions[key].append(callback)

        # Send subscription message
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join([f"{channel}.{symbol}" for symbol in symbols])
        }

        self.ws.send(json.dumps(subscribe_message))
        logger.info(f"Subscribed to {channel} for {len(symbols)} symbols")

    def unsubscribe(self, channel: str, symbols: List[str]) -> None:
        """
        Unsubscribe from channel for symbols.

        Args:
            channel: Channel type
            symbols: List of symbols
        """
        if not self.connected:
            return

        # Remove callbacks
        for symbol in symbols:
            key = f"{channel}:{symbol}"
            if key in self.subscriptions:
                del self.subscriptions[key]

        # Send unsubscribe message
        unsubscribe_message = {
            "action": "unsubscribe",
            "params": ",".join([f"{channel}.{symbol}" for symbol in symbols])
        }

        self.ws.send(json.dumps(unsubscribe_message))
        logger.info(f"Unsubscribed from {channel} for {len(symbols)} symbols")

    def subscribe_trades(
        self,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to trades.

        Message format:
        {
            "ev": "T",
            "sym": "AAPL",
            "p": 150.25,  # Price
            "s": 100,      # Size
            "t": 1234567890000,  # Timestamp
            ...
        }
        """
        self.subscribe("T", symbols, callback)

    def subscribe_quotes(
        self,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to quotes (bid/ask).

        Message format:
        {
            "ev": "Q",
            "sym": "AAPL",
            "bp": 150.24,  # Bid price
            "bs": 100,     # Bid size
            "ap": 150.26,  # Ask price
            "as": 200,     # Ask size
            "t": 1234567890000,
            ...
        }
        """
        self.subscribe("Q", symbols, callback)

    def subscribe_aggregates(
        self,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to aggregates (minute bars).

        Message format:
        {
            "ev": "AM",
            "sym": "AAPL",
            "o": 150.00,  # Open
            "h": 150.50,  # High
            "l": 149.90,  # Low
            "c": 150.25,  # Close
            "v": 10000,   # Volume
            "s": 1234567890000,  # Start timestamp
            ...
        }
        """
        self.subscribe("AM", symbols, callback)

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register handler for all messages of a type.

        Args:
            event_type: Event type (T, Q, AM, etc.)
            handler: Handler function
        """
        if event_type not in self.message_handlers:
            self.message_handlers[event_type] = []
        self.message_handlers[event_type].append(handler)

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "connected": self.connected,
            "authenticated": self.authenticated,
            "messages_received": self.messages_received,
            "last_message_time": self.last_message_time,
            "active_subscriptions": len(self.subscriptions)
        }


# Example usage
if __name__ == "__main__":
    import os

    # Get API key
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        logger.error("Set POLYGON_API_KEY environment variable")
        exit(1)

    # Create client
    client = PolygonWebSocketClient(api_key, cluster="stocks")

    # Connect
    if not client.connect():
        logger.error("Failed to connect")
        exit(1)

    # Define callbacks
    def on_trade(msg):
        logger.info(f"TRADE: {msg['sym']} @ ${msg['p']:.2f} x{msg['s']}")

    def on_quote(msg):
        logger.info(f"QUOTE: {msg['sym']} BID ${msg['bp']:.2f} x{msg['bs']} ASK ${msg['ap']:.2f} x{msg['as']}")

    # Subscribe to trades and quotes
    symbols = ["AAPL", "MSFT"]
    client.subscribe_trades(symbols, on_trade)
    client.subscribe_quotes(symbols, on_quote)

    # Run for 30 seconds
    logger.info("Streaming data for 30 seconds...")
    time.sleep(30)

    # Stats
    stats = client.get_stats()
    logger.info(f"Received {stats['messages_received']} messages")

    # Disconnect
    client.disconnect()
