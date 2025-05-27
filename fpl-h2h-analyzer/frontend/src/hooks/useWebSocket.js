import { useState, useEffect, useCallback, useRef } from 'react';
import websocketService, { MessageTypes } from '../services/websocket';

/**
 * Custom hook for WebSocket connection management
 */
export function useWebSocketConnection() {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [error, setError] = useState(null);

  useEffect(() => {
    // Set up connection change callback
    websocketService.setConnectionChangeCallback((connected) => {
      setIsConnected(connected);
      setConnectionStatus(connected ? 'connected' : 'disconnected');
      if (connected) {
        setError(null);
      }
    });

    // Set up error callback
    websocketService.setErrorCallback((error) => {
      setError(error);
      setConnectionStatus('error');
    });

    // Get initial status
    const status = websocketService.getStatus();
    setIsConnected(status.isConnected);
    setConnectionStatus(status.isConnected ? 'connected' : 'disconnected');

    return () => {
      // Clean up callbacks
      websocketService.setConnectionChangeCallback(null);
      websocketService.setErrorCallback(null);
    };
  }, []);

  const reconnect = useCallback(() => {
    setConnectionStatus('connecting');
    setError(null);
    websocketService.connect().catch((error) => {
      setError(error);
      setConnectionStatus('error');
    });
  }, []);

  return {
    isConnected,
    connectionStatus,
    error,
    reconnect,
    status: websocketService.getStatus()
  };
}

/**
 * Custom hook for subscribing to WebSocket messages
 */
export function useWebSocketSubscription(messageType, handler, dependencies = []) {
  const handlerRef = useRef(handler);
  
  // Update the ref when handler changes
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    const wrappedHandler = (data, meta) => {
      if (handlerRef.current) {
        handlerRef.current(data, meta);
      }
    };

    websocketService.addMessageHandler(messageType, wrappedHandler);

    return () => {
      websocketService.removeMessageHandler(messageType, wrappedHandler);
    };
  }, [messageType, ...dependencies]);
}

/**
 * Custom hook for H2H battle real-time updates
 */
export function useH2HBattle(manager1Id, manager2Id) {
  const [battleData, setBattleData] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [updateCount, setUpdateCount] = useState(0);
  const { isConnected } = useWebSocketConnection();

  // Handle H2H updates
  const handleH2HUpdate = useCallback((data, meta) => {
    // Filter updates for this specific battle
    if (data.manager_id && (data.manager_id == manager1Id || data.manager_id == manager2Id)) {
      setBattleData(prevData => ({
        ...prevData,
        ...data,
        meta
      }));
      setLastUpdate(new Date());
      setUpdateCount(prev => prev + 1);
    }
  }, [manager1Id, manager2Id]);

  // Subscribe to H2H updates
  useWebSocketSubscription(MessageTypes.H2H_UPDATE, handleH2HUpdate, [manager1Id, manager2Id]);

  // Subscribe to room when connected
  useEffect(() => {
    if (isConnected && manager1Id && manager2Id) {
      websocketService.subscribeToH2HBattle(manager1Id, manager2Id);
      
      return () => {
        // Optionally unsubscribe when component unmounts
        // websocketService.unsubscribeFromH2HBattle(manager1Id, manager2Id);
      };
    }
  }, [isConnected, manager1Id, manager2Id]);

  return {
    battleData,
    lastUpdate,
    updateCount,
    isConnected
  };
}

/**
 * Custom hook for live score updates
 */
export function useLiveScores(gameweek) {
  const [liveScores, setLiveScores] = useState({});
  const [lastUpdate, setLastUpdate] = useState(null);
  const [updateCount, setUpdateCount] = useState(0);
  const { isConnected } = useWebSocketConnection();

  // Handle live score updates
  const handleLiveUpdate = useCallback((data, meta) => {
    if (data.gameweek === gameweek && data.changes) {
      setLiveScores(prevScores => {
        const newScores = { ...prevScores };
        
        // Process each change
        data.changes.forEach(change => {
          const playerId = change.player_id;
          if (playerId) {
            newScores[playerId] = {
              ...newScores[playerId],
              ...change,
              timestamp: data.timestamp
            };
          }
        });
        
        return newScores;
      });
      
      setLastUpdate(new Date());
      setUpdateCount(prev => prev + 1);
    }
  }, [gameweek]);

  // Subscribe to live score updates
  useWebSocketSubscription(MessageTypes.LIVE_SCORES, handleLiveUpdate, [gameweek]);

  // Subscribe to live gameweek room when connected
  useEffect(() => {
    if (isConnected && gameweek) {
      websocketService.subscribeToLiveGameweek(gameweek);
    }
  }, [isConnected, gameweek]);

  return {
    liveScores,
    lastUpdate,
    updateCount,
    isConnected
  };
}

/**
 * Custom hook for league updates
 */
export function useLeagueUpdates(leagueId) {
  const [leagueUpdates, setLeagueUpdates] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [updateCount, setUpdateCount] = useState(0);
  const { isConnected } = useWebSocketConnection();

  // Handle league updates
  const handleLeagueUpdate = useCallback((data, meta) => {
    if (data.league_id == leagueId) {
      setLeagueUpdates(prevUpdates => [
        {
          ...data,
          meta,
          id: `${data.update_type}_${Date.now()}`
        },
        ...prevUpdates.slice(0, 49) // Keep last 50 updates
      ]);
      
      setLastUpdate(new Date());
      setUpdateCount(prev => prev + 1);
    }
  }, [leagueId]);

  // Subscribe to league updates
  useWebSocketSubscription(MessageTypes.LEAGUE_UPDATE, handleLeagueUpdate, [leagueId]);

  // Subscribe to league room when connected
  useEffect(() => {
    if (isConnected && leagueId) {
      websocketService.subscribeToLeague(leagueId);
    }
  }, [isConnected, leagueId]);

  return {
    leagueUpdates,
    lastUpdate,
    updateCount,
    isConnected,
    clearUpdates: () => setLeagueUpdates([])
  };
}

/**
 * Custom hook for player events
 */
export function usePlayerEvents() {
  const [playerEvents, setPlayerEvents] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);
  const { isConnected } = useWebSocketConnection();

  // Handle player events
  const handlePlayerEvent = useCallback((data, meta) => {
    setPlayerEvents(prevEvents => [
      {
        ...data,
        meta,
        id: `${data.type}_${data.player_id}_${Date.now()}`
      },
      ...prevEvents.slice(0, 99) // Keep last 100 events
    ]);
    
    setLastUpdate(new Date());
  }, []);

  // Subscribe to player events
  useWebSocketSubscription(MessageTypes.PLAYER_EVENT, handlePlayerEvent);

  return {
    playerEvents,
    lastUpdate,
    isConnected,
    clearEvents: () => setPlayerEvents([])
  };
}

/**
 * Utility hook for sending WebSocket messages
 */
export function useWebSocketSender() {
  const { isConnected } = useWebSocketConnection();

  const sendMessage = useCallback((type, data) => {
    if (!isConnected) {
      console.warn('Cannot send message: WebSocket not connected');
      return false;
    }

    return websocketService.send({
      type,
      data,
      timestamp: new Date().toISOString()
    });
  }, [isConnected]);

  const subscribeToRoom = useCallback((roomId) => {
    return websocketService.subscribeToRoom(roomId);
  }, []);

  const unsubscribeFromRoom = useCallback((roomId) => {
    return websocketService.unsubscribeFromRoom(roomId);
  }, []);

  return {
    sendMessage,
    subscribeToRoom,
    unsubscribeFromRoom,
    isConnected
  };
}