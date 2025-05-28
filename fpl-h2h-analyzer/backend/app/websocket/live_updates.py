import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict, field

from fastapi import WebSocket, WebSocketDisconnect, status
import uvloop
from starlette.websockets import WebSocketState

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
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    RECONNECT = "reconnect"
    CONNECTION_STATE = "connection_state"
    RATE_LIMIT = "rate_limit"

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
class ConnectionState(str, Enum):
    """Connection states for tracking"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"

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
    state: ConnectionState = ConnectionState.CONNECTING
    reconnection_token: Optional[str] = None
    reconnection_count: int = 0
    last_ping_sent: Optional[float] = None
    ping_latency: Optional[float] = None
    message_count: int = 0
    rate_limit_reset: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if not self.subscribed_rooms:
            self.subscribed_rooms = set()
        if not self.reconnection_token:
            self.reconnection_token = str(uuid.uuid4())

class WebSocketManager:
    """Production-ready WebSocket manager with connection pooling and room support"""
    
    def __init__(self, 
                 max_connections: int = 1000, 
                 heartbeat_interval: int = 30,
                 ping_interval: int = 10,
                 ping_timeout: int = 5,
                 reconnection_window: int = 300,  # 5 minutes
                 rate_limit_messages: int = 100,
                 rate_limit_window: int = 60):  # per minute
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.reconnection_window = reconnection_window
        self.rate_limit_messages = rate_limit_messages
        self.rate_limit_window = rate_limit_window
        
        # Connection management
        self.active_connections: Dict[str, ClientConnection] = {}
        self.rooms: Dict[str, Set[str]] = defaultdict(set)  # room_id -> set of client_ids
        self.client_rooms: Dict[str, Set[str]] = defaultdict(set)  # client_id -> set of room_ids
        
        # Reconnection support
        self.reconnection_tokens: Dict[str, str] = {}  # token -> client_id
        self.disconnected_clients: Dict[str, Dict[str, Any]] = {}  # client_id -> connection info
        
        # Connection state callbacks
        self.on_connect_callbacks: List[Callable] = []
        self.on_disconnect_callbacks: List[Callable] = []
        self.on_reconnect_callbacks: List[Callable] = []
        
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
        self._ping_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.connection_latencies: List[float] = []
        self.max_concurrent_connections = 0
        
    async def start_background_tasks(self):
        """Start background tasks for heartbeat, ping, cleanup, and metrics"""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_worker())
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
        if self._ping_task is None:
            self._ping_task = asyncio.create_task(self._ping_worker())
        if self._metrics_task is None:
            self._metrics_task = asyncio.create_task(self._metrics_worker())
    
    async def stop_background_tasks(self):
        """Stop background tasks gracefully"""
        tasks = [
            ('heartbeat', self._heartbeat_task),
            ('cleanup', self._cleanup_task),
            ('ping', self._ping_task),
            ('metrics', self._metrics_task)
        ]
        
        for task_name, task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                setattr(self, f'_{task_name}_task', None)
    
    async def connect(self, websocket: WebSocket, client_id: str, reconnection_token: Optional[str] = None) -> bool:
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
            
            # Handle reconnection
            is_reconnection = False
            previous_rooms = set()
            
            if reconnection_token and reconnection_token in self.reconnection_tokens:
                old_client_id = self.reconnection_tokens[reconnection_token]
                if old_client_id in self.disconnected_clients:
                    disconnected_info = self.disconnected_clients[old_client_id]
                    if time.time() - disconnected_info['disconnected_at'] <= self.reconnection_window:
                        is_reconnection = True
                        previous_rooms = disconnected_info['rooms']
                        # Clean up old data
                        del self.disconnected_clients[old_client_id]
                        del self.reconnection_tokens[reconnection_token]
            
            # Create client connection
            connection = ClientConnection(
                websocket=websocket,
                client_id=client_id,
                connected_at=time.time(),
                last_heartbeat=time.time(),
                subscribed_rooms=previous_rooms,
                user_agent=user_agent,
                ip_address=ip_address,
                state=ConnectionState.CONNECTED,
                reconnection_count=1 if is_reconnection else 0
            )
            
            self.active_connections[client_id] = connection
            self.connection_count += 1
            self.total_connections += 1
            self.reconnection_tokens[connection.reconnection_token] = client_id
            
            # Update max concurrent connections
            self.max_concurrent_connections = max(self.max_concurrent_connections, self.connection_count)
            
            # Re-subscribe to previous rooms if reconnecting
            if is_reconnection:
                for room_id in previous_rooms:
                    self.rooms[room_id].add(client_id)
                    self.client_rooms[client_id].add(room_id)
            
            # Send connection acknowledgment
            ack_message = WebSocketMessage(
                type=MessageType.CONNECTION_ACK if not is_reconnection else MessageType.RECONNECT,
                data={
                    "client_id": client_id,
                    "reconnection_token": connection.reconnection_token,
                    "server_time": datetime.utcnow().isoformat(),
                    "heartbeat_interval": self.heartbeat_interval,
                    "ping_interval": self.ping_interval,
                    "is_reconnection": is_reconnection,
                    "subscribed_rooms": list(connection.subscribed_rooms)
                },
                client_id=client_id
            )
            await self._send_to_client(client_id, ack_message)
            
            # Process any queued messages
            await self._process_queued_messages(client_id)
            
            # Send connection state update
            await self._broadcast_connection_state(client_id, ConnectionState.CONNECTED)
            
            # Execute callbacks
            callback_type = self.on_reconnect_callbacks if is_reconnection else self.on_connect_callbacks
            for callback in callback_type:
                asyncio.create_task(callback(client_id, connection))
            
            logger.info(f"Client {client_id} {'reconnected' if is_reconnection else 'connected'}. Total connections: {self.connection_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting client {client_id}: {e}")
            return False
    
    async def disconnect(self, client_id: str, save_state: bool = True):
        """Disconnect a WebSocket client and cleanup"""
        if client_id not in self.active_connections:
            return
        
        connection = self.active_connections[client_id]
        connection.state = ConnectionState.DISCONNECTED
        
        # Save state for reconnection if requested
        if save_state and connection.reconnection_token:
            self.disconnected_clients[client_id] = {
                'disconnected_at': time.time(),
                'rooms': connection.subscribed_rooms.copy(),
                'reconnection_token': connection.reconnection_token
            }
        
        # Remove from all rooms
        for room_id in list(connection.subscribed_rooms):
            await self._remove_from_room(client_id, room_id)
        
        # Clean up connection
        if connection.reconnection_token in self.reconnection_tokens:
            if not save_state:
                del self.reconnection_tokens[connection.reconnection_token]
        
        del self.active_connections[client_id]
        self.connection_count -= 1
        
        # Clear message queue if not saving state
        if not save_state and client_id in self.message_queues:
            del self.message_queues[client_id]
        
        # Send connection state update
        await self._broadcast_connection_state(client_id, ConnectionState.DISCONNECTED)
        
        # Execute callbacks
        for callback in self.on_disconnect_callbacks:
            asyncio.create_task(callback(client_id, connection))
        
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
        
        connection = self.active_connections[client_id]
        
        # Check rate limit
        if not await self._check_rate_limit(client_id):
            rate_limit_msg = WebSocketMessage(
                type=MessageType.RATE_LIMIT,
                data={"retry_after": self.rate_limit_window},
                client_id=client_id
            )
            try:
                await connection.websocket.send_text(rate_limit_msg.to_json())
            except:
                pass
            return False
        
        try:
            # Check if websocket is still open
            if connection.websocket.client_state != WebSocketState.CONNECTED:
                await self.disconnect(client_id, save_state=True)
                return False
            
            await connection.websocket.send_text(message.to_json())
            self.total_messages_sent += 1
            connection.message_count += 1
            return True
            
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected during send")
            await self.disconnect(client_id, save_state=True)
            return False
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            await self.disconnect(client_id, save_state=True)
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
                connection = self.active_connections[client_id]
                connection.last_heartbeat = time.time()
                connection.message_count += 1
            
            # Handle different message types
            if message.type == MessageType.PING:
                # Respond to ping immediately
                pong_message = WebSocketMessage(
                    type=MessageType.PONG,
                    data={"timestamp": message.data.get("timestamp")},
                    client_id=client_id
                )
                await self._send_to_client(client_id, pong_message)
                
                # Calculate latency
                if "timestamp" in message.data:
                    try:
                        ping_time = float(message.data["timestamp"])
                        latency = time.time() - ping_time
                        connection.ping_latency = latency * 1000  # Convert to milliseconds
                        self.connection_latencies.append(connection.ping_latency)
                    except:
                        pass
            
            elif message.type == MessageType.PONG:
                # Handle pong response
                if connection.last_ping_sent:
                    latency = time.time() - connection.last_ping_sent
                    connection.ping_latency = latency * 1000  # Convert to milliseconds
                    self.connection_latencies.append(connection.ping_latency)
            
            elif message.type == MessageType.SUBSCRIBE:
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
                    data={
                        "server_time": datetime.utcnow().isoformat(),
                        "latency": connection.ping_latency
                    },
                    client_id=client_id
                )
                await self._send_to_client(client_id, response)
            
            elif message.type == MessageType.CONNECTION_STATE:
                # Client requesting connection state
                state_message = WebSocketMessage(
                    type=MessageType.CONNECTION_STATE,
                    data={
                        "state": connection.state.value,
                        "connected_at": connection.connected_at,
                        "reconnection_count": connection.reconnection_count,
                        "subscribed_rooms": list(connection.subscribed_rooms),
                        "latency": connection.ping_latency
                    },
                    client_id=client_id
                )
                await self._send_to_client(client_id, state_message)
            
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
    
    async def _ping_worker(self):
        """Background worker to send ping messages and measure latency"""
        while True:
            try:
                ping_tasks = []
                current_time = time.time()
                
                for client_id, connection in self.active_connections.items():
                    # Send ping
                    ping_message = WebSocketMessage(
                        type=MessageType.PING,
                        data={"timestamp": current_time}
                    )
                    connection.last_ping_sent = current_time
                    task = self._send_to_client(client_id, ping_message)
                    ping_tasks.append(task)
                
                # Wait for all pings to be sent
                if ping_tasks:
                    await asyncio.gather(*ping_tasks, return_exceptions=True)
                
                await asyncio.sleep(self.ping_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping worker: {e}")
                await asyncio.sleep(5)
    
    async def _metrics_worker(self):
        """Background worker to collect and log metrics"""
        while True:
            try:
                # Log metrics every minute
                stats = self.get_statistics()
                logger.info(f"WebSocket metrics: {stats}")
                
                # Clean up old latency measurements (keep last 1000)
                if len(self.connection_latencies) > 1000:
                    self.connection_latencies = self.connection_latencies[-1000:]
                
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics worker: {e}")
                await asyncio.sleep(60)
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        if client_id not in self.active_connections:
            return False
        
        connection = self.active_connections[client_id]
        current_time = time.time()
        
        # Reset rate limit window if expired
        if current_time - connection.rate_limit_reset >= self.rate_limit_window:
            connection.message_count = 0
            connection.rate_limit_reset = current_time
        
        return connection.message_count < self.rate_limit_messages
    
    async def _broadcast_connection_state(self, client_id: str, state: ConnectionState):
        """Broadcast connection state change to relevant rooms"""
        # This can be used to notify other clients about connection state changes
        # For example, in a game or collaborative environment
        pass
    
    def add_connect_callback(self, callback: Callable):
        """Add callback to be executed when client connects"""
        self.on_connect_callbacks.append(callback)
    
    def add_disconnect_callback(self, callback: Callable):
        """Add callback to be executed when client disconnects"""
        self.on_disconnect_callbacks.append(callback)
    
    def add_reconnect_callback(self, callback: Callable):
        """Add callback to be executed when client reconnects"""
        self.on_reconnect_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        uptime = time.time() - self.start_time
        
        # Calculate average latency
        avg_latency = None
        if self.connection_latencies:
            avg_latency = sum(self.connection_latencies) / len(self.connection_latencies)
        
        return {
            "active_connections": self.connection_count,
            "total_connections": self.total_connections,
            "max_concurrent_connections": self.max_concurrent_connections,
            "total_rooms": len(self.rooms),
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received,
            "uptime_seconds": uptime,
            "queued_messages": sum(len(queue) for queue in self.message_queues.values()),
            "disconnected_clients_tracked": len(self.disconnected_clients),
            "average_latency_ms": avg_latency,
            "room_details": {room_id: len(clients) for room_id, clients in self.rooms.items()},
            "connection_states": self._get_connection_states()
        }
    
    def _get_connection_states(self) -> Dict[str, int]:
        """Get count of connections by state"""
        states = defaultdict(int)
        for connection in self.active_connections.values():
            states[connection.state.value] += 1
        return dict(states)
    
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

def generate_manager_room_id(manager_id: str) -> str:
    """Generate room ID for manager-specific updates"""
    return f"manager_{manager_id}"

def generate_global_room_id() -> str:
    """Generate room ID for global updates"""
    return "global_updates"