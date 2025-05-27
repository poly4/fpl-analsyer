import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastapi import WebSocket
from fastapi.testclient import TestClient

from app.websocket.live_updates import (
    WebSocketManager, 
    MessageType, 
    WebSocketMessage, 
    ClientConnection,
    generate_h2h_room_id,
    generate_league_room_id,
    generate_live_room_id
)


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self.sent_messages = []
        self.client = Mock()
        self.client.host = "127.0.0.1"
        self.headers = {"user-agent": "test-client"}
        
    async def accept(self):
        self.accepted = True
        
    async def close(self, code=1000, reason=""):
        self.closed = True
        self.close_code = code
        self.close_reason = reason
        
    async def send_text(self, data):
        if self.closed:
            raise Exception("WebSocket is closed")
        self.sent_messages.append(data)
        
    async def receive_text(self):
        # For testing purposes, return a test message
        return json.dumps({
            "type": "heartbeat",
            "data": {"client_time": datetime.utcnow().isoformat()}
        })


@pytest.fixture
def websocket_manager():
    """Create WebSocket manager for testing"""
    return WebSocketManager(max_connections=10, heartbeat_interval=5)


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket for testing"""
    return MockWebSocket()


class TestWebSocketManager:
    """Test WebSocket manager functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_manager_initialization(self, websocket_manager):
        """Test WebSocket manager initialization"""
        assert websocket_manager.max_connections == 10
        assert websocket_manager.heartbeat_interval == 5
        assert len(websocket_manager.active_connections) == 0
        assert len(websocket_manager.rooms) == 0
        assert websocket_manager.connection_count == 0
        
    @pytest.mark.asyncio
    async def test_client_connection(self, websocket_manager, mock_websocket):
        """Test client connection and disconnection"""
        client_id = "test_client_1"
        
        # Test connection
        success = await websocket_manager.connect(mock_websocket, client_id)
        assert success is True
        assert mock_websocket.accepted is True
        assert client_id in websocket_manager.active_connections
        assert websocket_manager.connection_count == 1
        assert websocket_manager.total_connections == 1
        
        # Verify connection acknowledgment was sent
        assert len(mock_websocket.sent_messages) == 1
        ack_message = json.loads(mock_websocket.sent_messages[0])
        assert ack_message["type"] == "connection_ack"
        assert ack_message["data"]["client_id"] == client_id
        
        # Test disconnection
        await websocket_manager.disconnect(client_id)
        assert client_id not in websocket_manager.active_connections
        assert websocket_manager.connection_count == 0
        
    @pytest.mark.asyncio
    async def test_connection_limit(self, websocket_manager):
        """Test connection limit enforcement"""
        # Fill up to max connections
        for i in range(websocket_manager.max_connections):
            mock_ws = MockWebSocket()
            success = await websocket_manager.connect(mock_ws, f"client_{i}")
            assert success is True
            
        # Try to exceed limit
        mock_ws_exceed = MockWebSocket()
        success = await websocket_manager.connect(mock_ws_exceed, "exceed_client")
        assert success is False
        assert mock_ws_exceed.closed is True
        assert mock_ws_exceed.close_code == 1013
        
    @pytest.mark.asyncio
    async def test_room_subscription(self, websocket_manager, mock_websocket):
        """Test room subscription and unsubscription"""
        client_id = "test_client"
        room_id = "test_room"
        
        # Connect client
        await websocket_manager.connect(mock_websocket, client_id)
        
        # Subscribe to room
        success = await websocket_manager.subscribe_to_room(client_id, room_id)
        assert success is True
        assert room_id in websocket_manager.rooms
        assert client_id in websocket_manager.rooms[room_id]
        assert room_id in websocket_manager.client_rooms[client_id]
        
        # Unsubscribe from room
        success = await websocket_manager.unsubscribe_from_room(client_id, room_id)
        assert success is True
        assert room_id not in websocket_manager.rooms  # Room should be cleaned up
        assert client_id not in websocket_manager.client_rooms or room_id not in websocket_manager.client_rooms[client_id]
        
    @pytest.mark.asyncio
    async def test_message_sending(self, websocket_manager, mock_websocket):
        """Test sending messages to clients"""
        client_id = "test_client"
        
        # Connect client
        await websocket_manager.connect(mock_websocket, client_id)
        
        # Send message to client
        message = WebSocketMessage(
            type=MessageType.H2H_UPDATE,
            data={"test": "data"},
            client_id=client_id
        )
        
        success = await websocket_manager.send_to_client(client_id, message)
        assert success is True
        assert len(mock_websocket.sent_messages) == 2  # ack + test message
        
        # Verify message content
        sent_message = json.loads(mock_websocket.sent_messages[-1])
        assert sent_message["type"] == "h2h_update"
        assert sent_message["data"]["test"] == "data"
        
    @pytest.mark.asyncio
    async def test_room_broadcasting(self, websocket_manager):
        """Test broadcasting messages to rooms"""
        room_id = "test_room"
        
        # Connect multiple clients
        clients = []
        for i in range(3):
            mock_ws = MockWebSocket()
            client_id = f"client_{i}"
            clients.append((client_id, mock_ws))
            
            await websocket_manager.connect(mock_ws, client_id)
            await websocket_manager.subscribe_to_room(client_id, room_id)
        
        # Broadcast message to room
        message = WebSocketMessage(
            type=MessageType.LEAGUE_UPDATE,
            data={"broadcast": "test"},
            room=room_id
        )
        
        sent_count = await websocket_manager.broadcast_to_room(room_id, message)
        assert sent_count == 3
        
        # Verify all clients received the message
        for client_id, mock_ws in clients:
            assert len(mock_ws.sent_messages) == 2  # ack + broadcast
            broadcast_msg = json.loads(mock_ws.sent_messages[-1])
            assert broadcast_msg["type"] == "league_update"
            assert broadcast_msg["data"]["broadcast"] == "test"
            assert broadcast_msg["room"] == room_id
            
    @pytest.mark.asyncio
    async def test_message_handling(self, websocket_manager, mock_websocket):
        """Test incoming message handling"""
        client_id = "test_client"
        
        # Connect client
        await websocket_manager.connect(mock_websocket, client_id)
        
        # Test subscription message
        subscribe_msg = json.dumps({
            "type": "subscribe",
            "data": {"room_id": "test_room"},
            "timestamp": datetime.utcnow().isoformat()
        })
        
        success = await websocket_manager.handle_client_message(client_id, subscribe_msg)
        assert success is True
        assert "test_room" in websocket_manager.rooms
        assert client_id in websocket_manager.rooms["test_room"]
        
        # Test heartbeat message
        heartbeat_msg = json.dumps({
            "type": "heartbeat",
            "data": {"client_time": datetime.utcnow().isoformat()},
            "timestamp": datetime.utcnow().isoformat()
        })
        
        success = await websocket_manager.handle_client_message(client_id, heartbeat_msg)
        assert success is True
        
        # Verify heartbeat response was sent
        heartbeat_response = json.loads(mock_websocket.sent_messages[-1])
        assert heartbeat_response["type"] == "heartbeat"
        
    @pytest.mark.asyncio
    async def test_invalid_message_handling(self, websocket_manager, mock_websocket):
        """Test handling of invalid messages"""
        client_id = "test_client"
        
        # Connect client
        await websocket_manager.connect(mock_websocket, client_id)
        
        # Test invalid JSON
        success = await websocket_manager.handle_client_message(client_id, "invalid json")
        assert success is False
        
        # Verify error message was sent
        error_response = json.loads(mock_websocket.sent_messages[-1])
        assert error_response["type"] == "error"
        assert "Invalid JSON format" in error_response["data"]["error"]
        
    @pytest.mark.asyncio
    async def test_message_queuing(self, websocket_manager):
        """Test message queuing for offline clients"""
        client_id = "offline_client"
        
        # Send message to non-connected client (should be queued)
        message = WebSocketMessage(
            type=MessageType.H2H_UPDATE,
            data={"queued": "message"},
            client_id=client_id
        )
        
        success = await websocket_manager.send_to_client(client_id, message)
        assert success is False  # Client not connected
        assert client_id in websocket_manager.message_queues
        assert len(websocket_manager.message_queues[client_id]) == 1
        
        # Connect client and verify queued message is delivered
        mock_ws = MockWebSocket()
        await websocket_manager.connect(mock_ws, client_id)
        
        # Check that queued message was processed
        assert len(mock_ws.sent_messages) >= 2  # ack + queued message
        queued_message = json.loads(mock_ws.sent_messages[-1])
        assert queued_message["data"]["queued"] == "message"
        
    @pytest.mark.asyncio
    async def test_statistics_and_health(self, websocket_manager, mock_websocket):
        \"\"\"Test statistics and health status reporting\"\"\"
        client_id = \"test_client\"
        
        # Connect client and subscribe to room\n        await websocket_manager.connect(mock_websocket, client_id)\n        await websocket_manager.subscribe_to_room(client_id, \"test_room\")\n        \n        # Send a message to increment counters\n        message = WebSocketMessage(\n            type=MessageType.H2H_UPDATE,\n            data={\"test\": \"data\"}\n        )\n        await websocket_manager.send_to_client(client_id, message)\n        \n        # Test statistics\n        stats = websocket_manager.get_statistics()\n        assert stats[\"active_connections\"] == 1\n        assert stats[\"total_connections\"] == 1\n        assert stats[\"total_rooms\"] == 1\n        assert stats[\"total_messages_sent\"] >= 2  # ack + test message\n        assert \"test_room\" in stats[\"room_details\"]\n        assert stats[\"room_details\"][\"test_room\"] == 1\n        \n        # Test health status\n        health = websocket_manager.get_health_status()\n        assert health[\"status\"] == \"healthy\"\n        assert health[\"active_connections\"] == 1\n        assert health[\"max_connections\"] == 10\n        assert health[\"utilization_percent\"] == 10.0\n        \n    @pytest.mark.asyncio\n    async def test_background_tasks(self, websocket_manager):\n        \"\"\"Test background task management\"\"\"\n        # Start background tasks\n        await websocket_manager.start_background_tasks()\n        \n        assert websocket_manager._heartbeat_task is not None\n        assert websocket_manager._cleanup_task is not None\n        assert not websocket_manager._heartbeat_task.done()\n        assert not websocket_manager._cleanup_task.done()\n        \n        # Stop background tasks\n        await websocket_manager.stop_background_tasks()\n        \n        assert websocket_manager._heartbeat_task is None\n        assert websocket_manager._cleanup_task is None\n        \n\nclass TestWebSocketMessage:\n    \"\"\"Test WebSocket message functionality\"\"\"\n    \n    def test_message_creation(self):\n        \"\"\"Test WebSocket message creation\"\"\"\n        message = WebSocketMessage(\n            type=MessageType.H2H_UPDATE,\n            data={\"test\": \"data\"},\n            client_id=\"test_client\"\n        )\n        \n        assert message.type == MessageType.H2H_UPDATE\n        assert message.data[\"test\"] == \"data\"\n        assert message.client_id == \"test_client\"\n        assert message.timestamp is not None\n        \n    def test_message_serialization(self):\n        \"\"\"Test message JSON serialization\"\"\"\n        message = WebSocketMessage(\n            type=MessageType.LIVE_SCORES,\n            data={\"gameweek\": 38, \"changes\": []},\n            room=\"live_gw_38\"\n        )\n        \n        json_str = message.to_json()\n        assert isinstance(json_str, str)\n        \n        # Verify JSON can be parsed\n        parsed = json.loads(json_str)\n        assert parsed[\"type\"] == \"live_scores\"\n        assert parsed[\"data\"][\"gameweek\"] == 38\n        assert parsed[\"room\"] == \"live_gw_38\"\n        \n    def test_message_deserialization(self):\n        \"\"\"Test message JSON deserialization\"\"\"\n        json_data = {\n            \"type\": \"league_update\",\n            \"data\": {\"league_id\": 123, \"update_type\": \"standings_change\"},\n            \"timestamp\": \"2024-01-01T12:00:00.000000\",\n            \"room\": \"league_123\"\n        }\n        \n        message = WebSocketMessage.from_json(json.dumps(json_data))\n        \n        assert message.type == MessageType.LEAGUE_UPDATE\n        assert message.data[\"league_id\"] == 123\n        assert message.room == \"league_123\"\n        assert message.timestamp == \"2024-01-01T12:00:00.000000\"\n        \n\nclass TestUtilityFunctions:\n    \"\"\"Test utility functions for room management\"\"\"\n    \n    def test_h2h_room_id_generation(self):\n        \"\"\"Test H2H room ID generation\"\"\"\n        # Test consistent room ID regardless of order\n        room_id_1 = generate_h2h_room_id(\"123\", \"456\")\n        room_id_2 = generate_h2h_room_id(\"456\", \"123\")\n        \n        assert room_id_1 == room_id_2\n        assert room_id_1 == \"h2h_123_456\"\n        \n    def test_league_room_id_generation(self):\n        \"\"\"Test league room ID generation\"\"\"\n        room_id = generate_league_room_id(\"789\")\n        assert room_id == \"league_789\"\n        \n    def test_live_room_id_generation(self):\n        \"\"\"Test live gameweek room ID generation\"\"\"\n        room_id = generate_live_room_id(38)\n        assert room_id == \"live_gw_38\"\n        \n\nclass TestWebSocketIntegration:\n    \"\"\"Integration tests for WebSocket functionality\"\"\"\n    \n    @pytest.mark.asyncio\n    async def test_full_h2h_battle_flow(self, websocket_manager):\n        \"\"\"Test complete H2H battle WebSocket flow\"\"\"\n        manager1_id = \"123\"\n        manager2_id = \"456\"\n        room_id = generate_h2h_room_id(manager1_id, manager2_id)\n        \n        # Connect two clients\n        client1_ws = MockWebSocket()\n        client2_ws = MockWebSocket()\n        \n        await websocket_manager.connect(client1_ws, \"client1\")\n        await websocket_manager.connect(client2_ws, \"client2\")\n        \n        # Subscribe both clients to H2H room\n        await websocket_manager.subscribe_to_room(\"client1\", room_id)\n        await websocket_manager.subscribe_to_room(\"client2\", room_id)\n        \n        # Simulate H2H update\n        h2h_update = WebSocketMessage(\n            type=MessageType.H2H_UPDATE,\n            data={\n                \"manager_id\": manager1_id,\n                \"update_type\": \"live_points\",\n                \"gameweek\": 38,\n                \"points\": 85,\n                \"previous_points\": 80,\n                \"change\": 5\n            },\n            room=room_id\n        )\n        \n        # Broadcast update\n        sent_count = await websocket_manager.broadcast_to_room(room_id, h2h_update)\n        assert sent_count == 2\n        \n        # Verify both clients received the update\n        for client_ws in [client1_ws, client2_ws]:\n            h2h_msg = json.loads(client_ws.sent_messages[-1])\n            assert h2h_msg[\"type\"] == \"h2h_update\"\n            assert h2h_msg[\"data\"][\"manager_id\"] == manager1_id\n            assert h2h_msg[\"data\"][\"change\"] == 5\n            assert h2h_msg[\"room\"] == room_id\n            \n    @pytest.mark.asyncio\n    async def test_live_scores_broadcast(self, websocket_manager):\n        \"\"\"Test live scores broadcasting to multiple subscribers\"\"\"\n        gameweek = 38\n        room_id = generate_live_room_id(gameweek)\n        \n        # Connect multiple clients interested in live scores\n        clients = []\n        for i in range(5):\n            mock_ws = MockWebSocket()\n            client_id = f\"live_client_{i}\"\n            clients.append((client_id, mock_ws))\n            \n            await websocket_manager.connect(mock_ws, client_id)\n            await websocket_manager.subscribe_to_room(client_id, room_id)\n        \n        # Simulate live score update\n        live_update = WebSocketMessage(\n            type=MessageType.LIVE_SCORES,\n            data={\n                \"gameweek\": gameweek,\n                \"changes\": [\n                    {\n                        \"type\": \"score_change\",\n                        \"player_id\": 302,\n                        \"player_name\": \"Salah\",\n                        \"previous_points\": 8,\n                        \"new_points\": 14,\n                        \"change\": 6\n                    }\n                ]\n            },\n            room=room_id\n        )\n        \n        # Broadcast to all live score subscribers\n        sent_count = await websocket_manager.broadcast_to_room(room_id, live_update)\n        assert sent_count == 5\n        \n        # Verify all clients received the live update\n        for client_id, mock_ws in clients:\n            live_msg = json.loads(mock_ws.sent_messages[-1])\n            assert live_msg[\"type\"] == \"live_scores\"\n            assert live_msg[\"data\"][\"gameweek\"] == gameweek\n            assert len(live_msg[\"data\"][\"changes\"]) == 1\n            assert live_msg[\"data\"][\"changes\"][0][\"player_name\"] == \"Salah\"\n            \n    @pytest.mark.asyncio\n    async def test_performance_under_load(self, websocket_manager):\n        \"\"\"Test WebSocket manager performance under load\"\"\"\n        num_clients = 50\n        num_rooms = 10\n        \n        # Connect many clients\n        clients = []\n        for i in range(num_clients):\n            mock_ws = MockWebSocket()\n            client_id = f\"load_client_{i}\"\n            clients.append((client_id, mock_ws))\n            \n            await websocket_manager.connect(mock_ws, client_id)\n            \n            # Subscribe to random rooms\n            room_id = f\"load_room_{i % num_rooms}\"\n            await websocket_manager.subscribe_to_room(client_id, room_id)\n        \n        # Broadcast to all rooms\n        start_time = time.time()\n        \n        for room_num in range(num_rooms):\n            room_id = f\"load_room_{room_num}\"\n            message = WebSocketMessage(\n                type=MessageType.LEAGUE_UPDATE,\n                data={\"room_num\": room_num, \"load_test\": True},\n                room=room_id\n            )\n            \n            await websocket_manager.broadcast_to_room(room_id, message)\n        \n        broadcast_time = time.time() - start_time\n        \n        # Verify performance (should complete quickly)\n        assert broadcast_time < 1.0  # Should complete within 1 second\n        \n        # Verify statistics\n        stats = websocket_manager.get_statistics()\n        assert stats[\"active_connections\"] == num_clients\n        assert stats[\"total_rooms\"] == num_rooms\n        assert stats[\"total_messages_sent\"] >= num_clients  # At least one message per client\n        \n        # Clean up\n        for client_id, _ in clients:\n            await websocket_manager.disconnect(client_id)\n        \n        assert websocket_manager.connection_count == 0\n        assert len(websocket_manager.rooms) == 0  # Rooms should be cleaned up"