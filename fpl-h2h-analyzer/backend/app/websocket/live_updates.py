import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict

from fastapi import WebSocket, WebSocketDisconnect
import uvloop

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    """WebSocket message types for FPL real-time updates"""
    H2H_UPDATE = "h2h_update"
    LEAGUE_UPDATE = "league_update"
    PLAYER_EVENT = "player_event"
    LIVE_SCORES = "live_scores"
    CONNECTION_ACK = "connection_ack"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

@dataclass
class WebSocketMessage:
    """Standard message format for WebSocket communication"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = None
    room: Optional[str] = None
    client_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> 'WebSocketMessage':
        parsed = json.loads(data)
        return cls(**parsed)

@dataclass
class ClientConnection:
    """Represents a connected WebSocket client"""
    websocket: WebSocket
    client_id: str
    connected_at: float
    last_heartbeat: float
    subscribed_rooms: Set[str]
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    def __post_init__(self):
        if not self.subscribed_rooms:
            self.subscribed_rooms = set()

class WebSocketManager:
    """Production-ready WebSocket manager with connection pooling and room support"""
    
    def __init__(self, max_connections: int = 1000, heartbeat_interval: int = 30):
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        
        # Connection management
        self.active_connections: Dict[str, ClientConnection] = {}
        self.rooms: Dict[str, Set[str]] = defaultdict(set)  # room_id -> set of client_ids
        self.client_rooms: Dict[str, Set[str]] = defaultdict(set)  # client_id -> set of room_ids
        
        # Statistics and monitoring
        self.connection_count = 0
        self.total_connections = 0
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.start_time = time.time()
        
        # Message queues for offline delivery
        self.message_queues: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self.max_queue_size = 100
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start_background_tasks(self):
        """Start background tasks for heartbeat and cleanup"""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_worker())
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
    
    async def stop_background_tasks(self):
        """Stop background tasks gracefully"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """Connect a new WebSocket client with rate limiting"""
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"Connection limit reached. Rejecting client {client_id}")
            await websocket.close(code=1013, reason="Server overloaded")
            return False
        
        try:
            await websocket.accept()
            
            # Extract client info
            headers = dict(websocket.headers)
            user_agent = headers.get("user-agent")
            ip_address = getattr(websocket.client, 'host', None) if websocket.client else None
            
            # Create client connection
            connection = ClientConnection(
                websocket=websocket,
                client_id=client_id,
                connected_at=time.time(),
                last_heartbeat=time.time(),
                subscribed_rooms=set(),
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            self.active_connections[client_id] = connection
            self.connection_count += 1
            self.total_connections += 1
            
            # Send connection acknowledgment
            ack_message = WebSocketMessage(
                type=MessageType.CONNECTION_ACK,
                data={
                    "client_id": client_id,
                    "server_time": datetime.utcnow().isoformat(),
                    "heartbeat_interval": self.heartbeat_interval
                },
                client_id=client_id
            )
            await self._send_to_client(client_id, ack_message)
            
            # Process any queued messages
            await self._process_queued_messages(client_id)
            
            logger.info(f"Client {client_id} connected. Total connections: {self.connection_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting client {client_id}: {e}")
            return False
    
    async def disconnect(self, client_id: str):
        """Disconnect a WebSocket client and cleanup"""
        if client_id not in self.active_connections:
            return
        
        connection = self.active_connections[client_id]
        
        # Remove from all rooms
        for room_id in list(connection.subscribed_rooms):
            await self._remove_from_room(client_id, room_id)
        
        # Clean up connection
        del self.active_connections[client_id]
        self.connection_count -= 1
        
        # Clear message queue to prevent memory leaks
        if client_id in self.message_queues:
            del self.message_queues[client_id]
        
        logger.info(f"Client {client_id} disconnected. Total connections: {self.connection_count}")
    
    async def subscribe_to_room(self, client_id: str, room_id: str) -> bool:
        """Subscribe a client to a room for targeted broadcasts"""
        if client_id not in self.active_connections:
            logger.warning(f"Cannot subscribe {client_id} to room {room_id}: client not connected")
            return False
        
        connection = self.active_connections[client_id]
        connection.subscribed_rooms.add(room_id)
        self.rooms[room_id].add(client_id)
        self.client_rooms[client_id].add(room_id)
        
        logger.debug(f"Client {client_id} subscribed to room {room_id}")
        return True
    
    async def unsubscribe_from_room(self, client_id: str, room_id: str) -> bool:
        """Unsubscribe a client from a room"""
        return await self._remove_from_room(client_id, room_id)
    
    async def _remove_from_room(self, client_id: str, room_id: str) -> bool:
        """Internal method to remove client from room"""
        removed = False
        
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            if room_id in connection.subscribed_rooms:
                connection.subscribed_rooms.remove(room_id)
                removed = True
        
        if room_id in self.rooms and client_id in self.rooms[room_id]:
            self.rooms[room_id].remove(client_id)
            if not self.rooms[room_id]:  # Clean up empty rooms
                del self.rooms[room_id]
            removed = True
        
        if client_id in self.client_rooms and room_id in self.client_rooms[client_id]:
            self.client_rooms[client_id].remove(room_id)
            if not self.client_rooms[client_id]:  # Clean up empty client room sets
                del self.client_rooms[client_id]
            removed = True
        
        if removed:
            logger.debug(f"Client {client_id} unsubscribed from room {room_id}")
        
        return removed
    
    async def send_to_client(self, client_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific client"""
        return await self._send_to_client(client_id, message)
    
    async def _send_to_client(self, client_id: str, message: WebSocketMessage) -> bool:
        """Internal method to send message to client with error handling"""
        if client_id not in self.active_connections:
            # Queue message for offline delivery
            await self._queue_message(client_id, message)
            return False
        
        try:
            connection = self.active_connections[client_id]
            await connection.websocket.send_text(message.to_json())
            self.total_messages_sent += 1
            return True
            
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected during send")
            await self.disconnect(client_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    async def broadcast_to_room(self, room_id: str, message: WebSocketMessage, exclude_client: Optional[str] = None) -> int:
        """Broadcast message to all clients in a room"""
        if room_id not in self.rooms:
            logger.debug(f"Room {room_id} has no subscribers")
            return 0
        
        message.room = room_id
        clients = self.rooms[room_id].copy()
        if exclude_client:
            clients.discard(exclude_client)
        
        successful_sends = 0
        failed_clients = []
        
        # Send to all clients in parallel
        send_tasks = []
        for client_id in clients:
            task = self._send_to_client(client_id, message)
            send_tasks.append((client_id, task))
        
        results = await asyncio.gather(*[task for _, task in send_tasks], return_exceptions=True)
        
        for (client_id, _), result in zip(send_tasks, results):
            if isinstance(result, Exception):
                failed_clients.append(client_id)
                logger.error(f"Failed to send to client {client_id}: {result}")
            elif result:
                successful_sends += 1
            else:
                failed_clients.append(client_id)
        
        # Clean up failed connections
        for client_id in failed_clients:
            await self.disconnect(client_id)
        
        logger.debug(f"Broadcast to room {room_id}: {successful_sends}/{len(clients)} successful")
        return successful_sends
    
    async def broadcast_to_all(self, message: WebSocketMessage, exclude_client: Optional[str] = None) -> int:
        """Broadcast message to all connected clients"""
        clients = set(self.active_connections.keys())
        if exclude_client:
            clients.discard(exclude_client)
        
        successful_sends = 0
        for client_id in clients:
            if await self._send_to_client(client_id, message):
                successful_sends += 1
        
        logger.debug(f"Broadcast to all: {successful_sends}/{len(clients)} successful")
        return successful_sends
    
    async def handle_client_message(self, client_id: str, data: str) -> bool:
        """Handle incoming message from client"""
        try:
            message = WebSocketMessage.from_json(data)
            self.total_messages_received += 1
            
            # Update heartbeat timestamp
            if client_id in self.active_connections:
                self.active_connections[client_id].last_heartbeat = time.time()
            
            # Handle different message types
            if message.type == MessageType.SUBSCRIBE:
                room_id = message.data.get("room_id")
                if room_id:
                    await self.subscribe_to_room(client_id, room_id)
                    response = WebSocketMessage(
                        type=MessageType.CONNECTION_ACK,
                        data={"subscribed_to": room_id},
                        client_id=client_id
                    )
                    await self._send_to_client(client_id, response)
            
            elif message.type == MessageType.UNSUBSCRIBE:
                room_id = message.data.get("room_id")
                if room_id:
                    await self.unsubscribe_from_room(client_id, room_id)
                    response = WebSocketMessage(
                        type=MessageType.CONNECTION_ACK,
                        data={"unsubscribed_from": room_id},
                        client_id=client_id
                    )
                    await self._send_to_client(client_id, response)
            
            elif message.type == MessageType.HEARTBEAT:
                # Respond to heartbeat
                response = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    data={"server_time": datetime.utcnow().isoformat()},
                    client_id=client_id
                )
                await self._send_to_client(client_id, response)
            
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from client {client_id}: {e}")
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Invalid JSON format"},
                client_id=client_id
            )
            await self._send_to_client(client_id, error_message)
            return False
        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            return False
    
    async def _queue_message(self, client_id: str, message: WebSocketMessage):
        """Queue message for offline client delivery"""
        queue = self.message_queues[client_id]
        
        # Maintain queue size limit
        if len(queue) >= self.max_queue_size:
            queue.pop(0)  # Remove oldest message
        
        queue.append(message)
        logger.debug(f"Queued message for offline client {client_id}")
    
    async def _process_queued_messages(self, client_id: str):
        """Process queued messages when client reconnects"""
        if client_id not in self.message_queues:
            return
        
        queue = self.message_queues[client_id]
        processed = 0
        
        for message in queue:
            if await self._send_to_client(client_id, message):
                processed += 1
            else:
                break  # Stop if send fails
        
        # Clear processed messages
        del self.message_queues[client_id]
        
        if processed > 0:
            logger.info(f"Processed {processed} queued messages for client {client_id}")
    
    async def _heartbeat_worker(self):
        """Background worker to send heartbeats and detect dead connections"""
        while True:
            try:
                current_time = time.time()
                dead_clients = []
                
                for client_id, connection in self.active_connections.items():
                    time_since_heartbeat = current_time - connection.last_heartbeat
                    
                    if time_since_heartbeat > self.heartbeat_interval * 3:  # 3x heartbeat interval timeout
                        dead_clients.append(client_id)
                    elif time_since_heartbeat > self.heartbeat_interval:
                        # Send heartbeat
                        heartbeat = WebSocketMessage(
                            type=MessageType.HEARTBEAT,
                            data={"server_time": datetime.utcnow().isoformat()}
                        )
                        await self._send_to_client(client_id, heartbeat)
                
                # Clean up dead connections
                for client_id in dead_clients:
                    logger.info(f"Removing dead connection: {client_id}")
                    await self.disconnect(client_id)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat worker: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _cleanup_worker(self):
        """Background worker for periodic cleanup tasks"""
        while True:
            try:
                # Clean up empty rooms
                empty_rooms = [room_id for room_id, clients in self.rooms.items() if not clients]
                for room_id in empty_rooms:
                    del self.rooms[room_id]
                
                # Clean up old message queues (older than 1 hour)
                current_time = time.time()
                old_queues = []
                for client_id, queue in self.message_queues.items():
                    if queue and len(queue) > 0:
                        # Check if oldest message is too old
                        oldest_timestamp = datetime.fromisoformat(queue[0].timestamp.replace('Z', '+00:00'))
                        age = current_time - oldest_timestamp.timestamp()
                        if age > 3600:  # 1 hour
                            old_queues.append(client_id)
                
                for client_id in old_queues:
                    del self.message_queues[client_id]
                
                if empty_rooms or old_queues:
                    logger.debug(f"Cleanup: removed {len(empty_rooms)} empty rooms, {len(old_queues)} old queues")
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        uptime = time.time() - self.start_time
        return {
            "active_connections": self.connection_count,
            "total_connections": self.total_connections,
            "total_rooms": len(self.rooms),
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received,
            "uptime_seconds": uptime,
            "queued_messages": sum(len(queue) for queue in self.message_queues.values()),
            "room_details": {room_id: len(clients) for room_id, clients in self.rooms.items()}
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for monitoring"""
        return {
            "status": "healthy" if self.connection_count < self.max_connections * 0.9 else "warning",
            "active_connections": self.connection_count,
            "max_connections": self.max_connections,
            "utilization_percent": (self.connection_count / self.max_connections) * 100,
            "background_tasks_running": {
                "heartbeat": self._heartbeat_task is not None and not self._heartbeat_task.done(),
                "cleanup": self._cleanup_task is not None and not self._cleanup_task.done()
            }
        }

# Utility functions for room management
def generate_h2h_room_id(manager1_id: str, manager2_id: str) -> str:
    """Generate consistent room ID for H2H battles"""
    # Sort IDs to ensure consistency regardless of order
    ids = sorted([str(manager1_id), str(manager2_id)])
    return f"h2h_{ids[0]}_{ids[1]}"

def generate_league_room_id(league_id: str) -> str:
    """Generate room ID for league updates"""
    return f"league_{league_id}"

def generate_live_room_id(gameweek: int) -> str:
    """Generate room ID for live gameweek updates"""
    return f"live_gw_{gameweek}"