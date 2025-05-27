/**
 * WebSocket service for real-time FPL updates
 */

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectInterval = 1000; // Start with 1 second
    this.maxReconnectInterval = 30000; // Max 30 seconds
    this.heartbeatInterval = null;
    this.messageHandlers = new Map();
    this.roomSubscriptions = new Set();
    this.clientId = null;
    
    // Auto-reconnect settings
    this.shouldReconnect = true;
    
    // Connection state callbacks
    this.onConnectionChange = null;
    this.onError = null;
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        // Determine WebSocket URL based on environment
        let wsUrl;
        
        if (process.env.NODE_ENV === 'development' && window.location.port === '5173') {
          // Vite dev server - connect directly to backend
          wsUrl = 'ws://localhost:8000/ws/connect';
        } else if (window.location.hostname === 'localhost' && window.location.port === '3000') {
          // Docker development - connect through Nginx proxy
          wsUrl = `ws://localhost:3000/ws/connect`;
        } else {
          // Production - use relative path with appropriate protocol
          const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
          const host = window.location.host; // includes port if non-standard
          wsUrl = `${protocol}//${host}/ws/connect`;
        }

        console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);
        
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = (event) => {
          console.log('✅ WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.reconnectInterval = 1000;
          
          // Start heartbeat
          this.startHeartbeat();
          
          // Re-subscribe to rooms
          this.resubscribeToRooms();
          
          if (this.onConnectionChange) {
            this.onConnectionChange(true);
          }
          
          resolve();
        };

        this.socket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('❌ Error parsing WebSocket message:', error);
          }
        };

        this.socket.onclose = (event) => {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          this.clientId = null;
          
          // Stop heartbeat
          this.stopHeartbeat();
          
          if (this.onConnectionChange) {
            this.onConnectionChange(false);
          }
          
          // Attempt reconnection if appropriate
          if (this.shouldReconnect && event.code !== 1000) {
            this.scheduleReconnect();
          }
        };

        this.socket.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          if (this.onError) {
            this.onError(error);
          }
          reject(error);
        };

      } catch (error) {
        console.error('❌ Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    this.shouldReconnect = false;
    this.stopHeartbeat();
    
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    
    this.isConnected = false;
    this.clientId = null;
    this.roomSubscriptions.clear();
  }

  /**
   * Send message to server
   */
  send(message) {
    if (!this.isConnected || !this.socket) {
      console.warn('⚠️ Cannot send message: WebSocket not connected');
      return false;
    }

    try {
      this.socket.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('❌ Error sending WebSocket message:', error);
      return false;
    }
  }

  /**
   * Subscribe to a room for targeted updates
   */
  subscribeToRoom(roomId) {
    if (!roomId) return false;
    
    const message = {
      type: 'subscribe',
      data: {
        room_id: roomId
      },
      timestamp: new Date().toISOString()
    };
    
    const sent = this.send(message);
    if (sent) {
      this.roomSubscriptions.add(roomId);
      console.log(`📢 Subscribed to room: ${roomId}`);
    }
    
    return sent;
  }

  /**
   * Unsubscribe from a room
   */
  unsubscribeFromRoom(roomId) {
    if (!roomId) return false;
    
    const message = {
      type: 'unsubscribe',
      data: {
        room_id: roomId
      },
      timestamp: new Date().toISOString()
    };
    
    const sent = this.send(message);
    if (sent) {
      this.roomSubscriptions.delete(roomId);
      console.log(`📢 Unsubscribed from room: ${roomId}`);
    }
    
    return sent;
  }

  /**
   * Subscribe to H2H battle updates
   */
  subscribeToH2HBattle(manager1Id, manager2Id) {
    // Generate consistent room ID
    const ids = [manager1Id, manager2Id].sort();
    const roomId = `h2h_${ids[0]}_${ids[1]}`;
    return this.subscribeToRoom(roomId);
  }

  /**
   * Subscribe to league updates
   */
  subscribeToLeague(leagueId) {
    const roomId = `league_${leagueId}`;
    return this.subscribeToRoom(roomId);
  }

  /**
   * Subscribe to live gameweek updates
   */
  subscribeToLiveGameweek(gameweek) {
    const roomId = `live_gw_${gameweek}`;
    return this.subscribeToRoom(roomId);
  }

  /**
   * Add message handler for specific message types
   */
  addMessageHandler(messageType, handler) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }
    this.messageHandlers.get(messageType).add(handler);
    
    console.log(`📝 Added handler for message type: ${messageType}`);
  }

  /**
   * Remove message handler
   */
  removeMessageHandler(messageType, handler) {
    if (this.messageHandlers.has(messageType)) {
      this.messageHandlers.get(messageType).delete(handler);
      
      // Clean up empty handler sets
      if (this.messageHandlers.get(messageType).size === 0) {
        this.messageHandlers.delete(messageType);
      }
    }
  }

  /**
   * Handle incoming messages
   */
  handleMessage(message) {
    const { type, data, timestamp, room, client_id } = message;
    
    // Store client ID from connection acknowledgment
    if (type === 'connection_ack' && data.client_id) {
      this.clientId = data.client_id;
      console.log(`🆔 Client ID assigned: ${this.clientId}`);
    }
    
    // Update last message timestamp for heartbeat
    this.lastMessageTime = Date.now();
    
    // Dispatch to registered handlers
    if (this.messageHandlers.has(type)) {
      const handlers = this.messageHandlers.get(type);
      handlers.forEach(handler => {
        try {
          handler(data, { type, timestamp, room, client_id });
        } catch (error) {
          console.error(`❌ Error in message handler for ${type}:`, error);
        }
      });
    }
    
    console.log(`📨 Received ${type} message:`, { room, dataKeys: Object.keys(data || {}) });
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.stopHeartbeat(); // Clear any existing heartbeat
    
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({
          type: 'heartbeat',
          data: {
            client_time: new Date().toISOString()
          }
        });
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    
    console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectInterval}ms`);
    
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect().catch(error => {
          console.error('❌ Reconnection failed:', error);
          
          // Exponential backoff with jitter
          this.reconnectInterval = Math.min(
            this.reconnectInterval * 2 + Math.random() * 1000,
            this.maxReconnectInterval
          );
        });
      }
    }, this.reconnectInterval);
  }

  /**
   * Re-subscribe to all rooms after reconnection
   */
  resubscribeToRooms() {
    this.roomSubscriptions.forEach(roomId => {
      this.subscribeToRoom(roomId);
    });
  }

  /**
   * Get connection status
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      clientId: this.clientId,
      reconnectAttempts: this.reconnectAttempts,
      subscribedRooms: Array.from(this.roomSubscriptions),
      readyState: this.socket ? this.socket.readyState : WebSocket.CLOSED
    };
  }

  /**
   * Set connection change callback
   */
  setConnectionChangeCallback(callback) {
    this.onConnectionChange = callback;
  }

  /**
   * Set error callback
   */
  setErrorCallback(callback) {
    this.onError = callback;
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

// Auto-connect when service is imported
if (typeof window !== 'undefined') {
  websocketService.connect().catch(error => {
    console.error('❌ Initial WebSocket connection failed:', error);
  });
}

export default websocketService;

// Export message types for convenience
export const MessageTypes = {
  H2H_UPDATE: 'h2h_update',
  LEAGUE_UPDATE: 'league_update',
  PLAYER_EVENT: 'player_event',
  LIVE_SCORES: 'live_scores',
  CONNECTION_ACK: 'connection_ack',
  ERROR: 'error',
  HEARTBEAT: 'heartbeat'
};