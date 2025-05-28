"""
Example WebSocket client demonstrating enhanced features:
- Connection with reconnection support
- Heartbeat/ping-pong
- Room subscriptions
- Connection state tracking
"""
import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any
import websockets
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedWebSocketClient:
    """Enhanced WebSocket client with reconnection and heartbeat support"""
    
    def __init__(self, url: str):
        self.url = url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.client_id: Optional[str] = None
        self.reconnection_token: Optional[str] = None
        self.connected = False
        self.reconnection_attempts = 0
        self.max_reconnection_attempts = 5
        self.reconnection_delay = 1  # Start with 1 second
        self.subscribed_rooms = set()
        self.ping_interval = 10
        self.last_pong_time = time.time()
        self.tasks = []
        
    async def connect(self, reconnection_token: Optional[str] = None) -> bool:
        """Connect to WebSocket server with optional reconnection token"""
        try:
            # Build connection URL with parameters
            connect_url = self.url
            params = []
            if reconnection_token:
                params.append(f"reconnection_token={reconnection_token}")
            if self.client_id:
                params.append(f"client_id={self.client_id}")
            
            if params:
                connect_url += "?" + "&".join(params)
            
            logger.info(f"Connecting to {connect_url}")
            self.websocket = await websockets.connect(connect_url)
            self.connected = True
            self.reconnection_attempts = 0
            self.reconnection_delay = 1
            
            # Start background tasks
            self.tasks = [
                asyncio.create_task(self._receive_messages()),
                asyncio.create_task(self._ping_loop()),
                asyncio.create_task(self._monitor_connection())
            ]
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self.connected = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def send_message(self, message_type: str, data: Dict[str, Any]):
        """Send a message to the server"""
        if not self.websocket or not self.connected:
            logger.warning("Not connected, cannot send message")
            return False
        
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def subscribe_to_room(self, room_id: str):
        """Subscribe to a room for targeted updates"""
        success = await self.send_message("subscribe", {"room_id": room_id})
        if success:
            self.subscribed_rooms.add(room_id)
        return success
    
    async def unsubscribe_from_room(self, room_id: str):
        """Unsubscribe from a room"""
        success = await self.send_message("unsubscribe", {"room_id": room_id})
        if success:
            self.subscribed_rooms.discard(room_id)
        return success
    
    async def _receive_messages(self):
        """Background task to receive messages"""
        while self.connected:
            try:
                if not self.websocket:
                    await asyncio.sleep(1)
                    continue
                
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Handle different message types
                message_type = data.get("type")
                
                if message_type == "connection_ack":
                    self.client_id = data["data"]["client_id"]
                    self.reconnection_token = data["data"]["reconnection_token"]
                    logger.info(f"Connected with client_id: {self.client_id}")
                    logger.info(f"Reconnection token: {self.reconnection_token}")
                    
                elif message_type == "reconnect":
                    logger.info("Reconnection successful!")
                    # Re-subscribe to previous rooms
                    for room_id in data["data"].get("subscribed_rooms", []):
                        self.subscribed_rooms.add(room_id)
                    
                elif message_type == "pong":
                    self.last_pong_time = time.time()
                    if "timestamp" in data.get("data", {}):
                        latency = (time.time() - float(data["data"]["timestamp"])) * 1000
                        logger.debug(f"Latency: {latency:.2f}ms")
                
                elif message_type == "heartbeat":
                    logger.debug(f"Heartbeat received: {data['data']}")
                
                elif message_type == "h2h_update":
                    logger.info(f"H2H Update: {data['data']}")
                
                elif message_type == "league_update":
                    logger.info(f"League Update: {data['data']}")
                
                elif message_type == "error":
                    logger.error(f"Server error: {data['data']}")
                
                elif message_type == "rate_limit":
                    logger.warning(f"Rate limited! Retry after: {data['data']['retry_after']}s")
                
                else:
                    logger.info(f"Received message: {message_type} - {data.get('data')}")
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed by server")
                self.connected = False
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                await asyncio.sleep(1)
    
    async def _ping_loop(self):
        """Send periodic ping messages"""
        while self.connected:
            try:
                await asyncio.sleep(self.ping_interval)
                await self.send_message("ping", {"timestamp": str(time.time())})
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
    
    async def _monitor_connection(self):
        """Monitor connection health and trigger reconnection if needed"""
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if not self.connected and self.reconnection_token:
                    if self.reconnection_attempts < self.max_reconnection_attempts:
                        logger.info(f"Attempting reconnection #{self.reconnection_attempts + 1}")
                        
                        # Exponential backoff
                        await asyncio.sleep(self.reconnection_delay)
                        
                        if await self.connect(self.reconnection_token):
                            logger.info("Reconnection successful!")
                        else:
                            self.reconnection_attempts += 1
                            self.reconnection_delay = min(self.reconnection_delay * 2, 30)
                    else:
                        logger.error("Max reconnection attempts reached")
                        break
                
                # Check for stale connection (no pong in 3x ping interval)
                if self.connected and time.time() - self.last_pong_time > self.ping_interval * 3:
                    logger.warning("Connection appears stale, disconnecting...")
                    await self.disconnect()
                    
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")

async def main():
    """Example usage of the enhanced WebSocket client"""
    # Initialize client
    client = EnhancedWebSocketClient("ws://localhost:8000/ws/connect")
    
    try:
        # Connect to server
        if await client.connect():
            logger.info("Successfully connected!")
            
            # Subscribe to some rooms
            await client.subscribe_to_room("league_620117")
            await client.subscribe_to_room("h2h_3356830_3531308")
            await client.subscribe_to_room("live_gw_38")
            
            # Send a test message
            await client.send_message("connection_state", {})
            
            # Keep the connection alive
            await asyncio.sleep(300)  # Run for 5 minutes
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())