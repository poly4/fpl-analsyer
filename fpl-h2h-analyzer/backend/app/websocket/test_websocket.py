"""
Test suite for enhanced WebSocket functionality
"""
import asyncio
import json
import pytest
import time
from unittest.mock import Mock, MagicMock, AsyncMock
from fastapi import WebSocket
from fastapi.testclient import TestClient

from .live_updates import (
    WebSocketManager, MessageType, WebSocketMessage, ClientConnection,
    ConnectionState, generate_h2h_room_id, generate_league_room_id,
    generate_live_room_id, generate_manager_room_id, generate_global_room_id
)

@pytest.fixture
async def websocket_manager():
    """Create a WebSocket manager instance for testing"""
    manager = WebSocketManager(
        max_connections=10,
        heartbeat_interval=5,
        ping_interval=2,
        reconnection_window=60
    )
    await manager.start_background_tasks()
    yield manager
    await manager.stop_background_tasks()

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket instance"""
    websocket = AsyncMock(spec=WebSocket)
    websocket.client_state = 1  # CONNECTED state
    websocket.headers = {"user-agent": "test-client"}
    websocket.client = Mock(host="127.0.0.1")
    return websocket

class TestWebSocketManager:
    """Test WebSocket manager functionality"""
    
    @pytest.mark.asyncio
    async def test_connect_client(self, websocket_manager, mock_websocket):
        """Test client connection"""
        client_id = "test-client-1"
        
        # Connect client
        connected = await websocket_manager.connect(mock_websocket, client_id)
        
        assert connected is True
        assert client_id in websocket_manager.active_connections
        assert websocket_manager.connection_count == 1
        
        # Verify connection acknowledgment was sent
        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message_data = json.loads(call_args)
        assert message_data["type"] == "connection_ack"
        assert message_data["data"]["client_id"] == client_id
        assert "reconnection_token" in message_data["data"]
    
    @pytest.mark.asyncio
    async def test_reconnect_client(self, websocket_manager, mock_websocket):
        """Test client reconnection"""
        client_id = "test-client-2"
        
        # Initial connection
        await websocket_manager.connect(mock_websocket, client_id)
        connection = websocket_manager.active_connections[client_id]
        reconnection_token = connection.reconnection_token
        
        # Subscribe to rooms
        await websocket_manager.subscribe_to_room(client_id, "test-room-1")
        await websocket_manager.subscribe_to_room(client_id, "test-room-2")
        
        # Disconnect with state saved
        await websocket_manager.disconnect(client_id, save_state=True)
        assert client_id not in websocket_manager.active_connections
        assert client_id in websocket_manager.disconnected_clients
        
        # Reconnect with token
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket2.client_state = 1
        mock_websocket2.headers = {"user-agent": "test-client"}
        mock_websocket2.client = Mock(host="127.0.0.1")
        
        connected = await websocket_manager.connect(
            mock_websocket2, "new-client-id", reconnection_token
        )
        
        assert connected is True
        # Verify reconnection message
        call_args = mock_websocket2.send_text.call_args[0][0]
        message_data = json.loads(call_args)
        assert message_data["type"] == "reconnect"
        assert message_data["data"]["is_reconnection"] is True
        assert set(message_data["data"]["subscribed_rooms"]) == {"test-room-1", "test-room-2"}
    
    @pytest.mark.asyncio
    async def test_max_connections_limit(self, websocket_manager, mock_websocket):
        """Test connection limit enforcement"""
        # Fill up to max connections
        for i in range(websocket_manager.max_connections):
            ws = AsyncMock(spec=WebSocket)
            ws.client_state = 1
            ws.headers = {}
            ws.client = None
            await websocket_manager.connect(ws, f"client-{i}")
        
        # Try to connect one more
        connected = await websocket_manager.connect(mock_websocket, "overflow-client")
        
        assert connected is False
        mock_websocket.close.assert_called_with(code=1013, reason="Server overloaded")
    
    @pytest.mark.asyncio
    async def test_room_subscription(self, websocket_manager, mock_websocket):
        """Test room subscription and broadcasting"""
        # Connect multiple clients
        clients = []
        for i in range(3):
            ws = AsyncMock(spec=WebSocket)
            ws.client_state = 1
            ws.headers = {}
            ws.client = None
            client_id = f"client-{i}"
            await websocket_manager.connect(ws, client_id)
            clients.append((client_id, ws))
        
        # Subscribe clients to rooms
        room_id = "test-room"
        await websocket_manager.subscribe_to_room("client-0", room_id)
        await websocket_manager.subscribe_to_room("client-1", room_id)
        # client-2 not subscribed
        
        # Broadcast to room
        message = WebSocketMessage(
            type=MessageType.LEAGUE_UPDATE,
            data={"test": "data"}
        )
        sent_count = await websocket_manager.broadcast_to_room(room_id, message)
        
        assert sent_count == 2
        # Verify only subscribed clients received the message
        assert clients[0][1].send_text.call_count == 2  # connection_ack + broadcast
        assert clients[1][1].send_text.call_count == 2  # connection_ack + broadcast
        assert clients[2][1].send_text.call_count == 1  # only connection_ack
    
    @pytest.mark.asyncio
    async def test_ping_pong_handling(self, websocket_manager, mock_websocket):
        """Test ping-pong message handling"""
        client_id = "ping-test-client"
        await websocket_manager.connect(mock_websocket, client_id)
        
        # Send ping message
        ping_message = json.dumps({
            "type": "ping",
            "data": {"timestamp": str(time.time())},
            "timestamp": "2025-01-01T00:00:00"
        })
        
        handled = await websocket_manager.handle_client_message(client_id, ping_message)
        assert handled is True
        
        # Verify pong response
        assert mock_websocket.send_text.call_count >= 2  # connection_ack + pong
        last_call = mock_websocket.send_text.call_args_list[-1][0][0]
        response_data = json.loads(last_call)
        assert response_data["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, websocket_manager, mock_websocket):
        """Test rate limiting functionality"""
        client_id = "rate-limit-test"
        await websocket_manager.connect(mock_websocket, client_id)
        
        # Send messages up to rate limit
        message = WebSocketMessage(type=MessageType.HEARTBEAT, data={})
        
        # Simulate sending many messages quickly
        connection = websocket_manager.active_connections[client_id]
        connection.message_count = websocket_manager.rate_limit_messages - 1
        
        # This should succeed
        success = await websocket_manager._send_to_client(client_id, message)
        assert success is True
        
        # This should be rate limited
        success = await websocket_manager._send_to_client(client_id, message)
        assert success is False
        
        # Verify rate limit message was sent
        rate_limit_call = None
        for call in mock_websocket.send_text.call_args_list:
            msg = json.loads(call[0][0])
            if msg["type"] == "rate_limit":
                rate_limit_call = msg
                break
        
        assert rate_limit_call is not None
        assert "retry_after" in rate_limit_call["data"]
    
    @pytest.mark.asyncio
    async def test_message_queuing(self, websocket_manager):
        """Test message queuing for offline clients"""
        client_id = "offline-client"
        
        # Queue messages for offline client
        for i in range(5):
            message = WebSocketMessage(
                type=MessageType.H2H_UPDATE,
                data={"update": i}
            )
            await websocket_manager._queue_message(client_id, message)
        
        assert len(websocket_manager.message_queues[client_id]) == 5
        
        # Connect client and verify queued messages are sent
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.client_state = 1
        mock_websocket.headers = {}
        mock_websocket.client = None
        
        await websocket_manager.connect(mock_websocket, client_id)
        
        # Should have received connection_ack + 5 queued messages
        assert mock_websocket.send_text.call_count >= 6
    
    @pytest.mark.asyncio
    async def test_connection_state_tracking(self, websocket_manager, mock_websocket):
        """Test connection state transitions"""
        client_id = "state-test-client"
        
        # Connect
        await websocket_manager.connect(mock_websocket, client_id)
        connection = websocket_manager.active_connections[client_id]
        assert connection.state == ConnectionState.CONNECTED
        
        # Request connection state
        state_request = json.dumps({
            "type": "connection_state",
            "data": {},
            "timestamp": "2025-01-01T00:00:00"
        })
        
        await websocket_manager.handle_client_message(client_id, state_request)
        
        # Verify state response
        state_response = None
        for call in mock_websocket.send_text.call_args_list:
            msg = json.loads(call[0][0])
            if msg["type"] == "connection_state":
                state_response = msg
                break
        
        assert state_response is not None
        assert state_response["data"]["state"] == "connected"
        assert "connected_at" in state_response["data"]
        assert "subscribed_rooms" in state_response["data"]

class TestRoomGeneration:
    """Test room ID generation functions"""
    
    def test_h2h_room_generation(self):
        """Test H2H room ID generation"""
        # Should be consistent regardless of order
        room1 = generate_h2h_room_id("123", "456")
        room2 = generate_h2h_room_id("456", "123")
        assert room1 == room2
        assert room1 == "h2h_123_456"
    
    def test_league_room_generation(self):
        """Test league room ID generation"""
        room = generate_league_room_id("620117")
        assert room == "league_620117"
    
    def test_live_room_generation(self):
        """Test live gameweek room ID generation"""
        room = generate_live_room_id(38)
        assert room == "live_gw_38"
    
    def test_manager_room_generation(self):
        """Test manager-specific room ID generation"""
        room = generate_manager_room_id("3356830")
        assert room == "manager_3356830"
    
    def test_global_room_generation(self):
        """Test global room ID generation"""
        room = generate_global_room_id()
        assert room == "global_updates"

class TestWebSocketMessage:
    """Test WebSocket message handling"""
    
    def test_message_serialization(self):
        """Test message to/from JSON"""
        message = WebSocketMessage(
            type=MessageType.H2H_UPDATE,
            data={"score1": 50, "score2": 45},
            room="h2h_123_456",
            client_id="test-client"
        )
        
        # Serialize
        json_str = message.to_json()
        
        # Deserialize
        parsed = WebSocketMessage.from_json(json_str)
        
        assert parsed.type == message.type
        assert parsed.data == message.data
        assert parsed.room == message.room
        assert parsed.client_id == message.client_id
        assert parsed.timestamp is not None

@pytest.mark.asyncio
async def test_concurrent_connections():
    """Test handling many concurrent connections"""
    manager = WebSocketManager(max_connections=100)
    await manager.start_background_tasks()
    
    try:
        # Create many concurrent connections
        tasks = []
        for i in range(50):
            mock_ws = AsyncMock(spec=WebSocket)
            mock_ws.client_state = 1
            mock_ws.headers = {}
            mock_ws.client = None
            task = manager.connect(mock_ws, f"concurrent-{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        assert all(results)  # All connections should succeed
        assert manager.connection_count == 50
        
        # Test concurrent broadcasting
        message = WebSocketMessage(
            type=MessageType.LIVE_SCORES,
            data={"test": "concurrent"}
        )
        sent_count = await manager.broadcast_to_all(message)
        assert sent_count == 50
        
    finally:
        await manager.stop_background_tasks()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])