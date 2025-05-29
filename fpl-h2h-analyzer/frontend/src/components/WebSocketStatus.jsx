import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Chip, 
  Tooltip, 
  Typography, 
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert
} from '@mui/material';
import { 
  Wifi, 
  WifiOff, 
  Refresh, 
  CheckCircle, 
  Error,
  Info,
  Circle
} from '@mui/icons-material';
import websocketService from '../services/websocket';

function WebSocketStatus() {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('disconnected');
  const [lastHeartbeat, setLastHeartbeat] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [messageCount, setMessageCount] = useState(0);
  const [subscriptions, setSubscriptions] = useState([]);
  
  useEffect(() => {
    // Monitor WebSocket connection status
    const statusInterval = setInterval(() => {
      const wsState = websocketService.getConnectionState?.() || 'disconnected';
      setConnectionState(wsState);
      setIsConnected(wsState === 'connected');
      
      if (websocketService.getSubscriptions) {
        setSubscriptions(websocketService.getSubscriptions());
      }
      
      if (websocketService.getMessageCount) {
        setMessageCount(websocketService.getMessageCount());
      }
    }, 1000);
    
    // Set up connection change callback
    if (websocketService.setConnectionChangeCallback) {
      websocketService.setConnectionChangeCallback((connected) => {
        setIsConnected(connected);
        if (connected) {
          setReconnectAttempts(0);
        }
      });
    }
    
    // Monitor heartbeat
    if (websocketService.onHeartbeat) {
      websocketService.onHeartbeat(() => {
        setLastHeartbeat(new Date());
      });
    }
    
    return () => {
      clearInterval(statusInterval);
    };
  }, []);
  
  const getStatusColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'success';
      case 'connecting':
        return 'warning';
      case 'disconnected':
        return 'error';
      default:
        return 'default';
    }
  };
  
  const getStatusIcon = () => {
    switch (connectionState) {
      case 'connected':
        return <Wifi />;
      case 'connecting':
        return <Circle sx={{ animation: 'pulse 1s infinite' }} />;
      case 'disconnected':
        return <WifiOff />;
      default:
        return <Info />;
    }
  };
  
  const handleReconnect = () => {
    if (websocketService.reconnect) {
      setReconnectAttempts(prev => prev + 1);
      websocketService.reconnect();
    }
  };
  
  const formatLastHeartbeat = () => {
    if (!lastHeartbeat) return 'Never';
    
    const seconds = Math.floor((new Date() - lastHeartbeat) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  };
  
  return (
    <>
      <Tooltip title={`WebSocket: ${connectionState}`}>
        <Chip
          icon={getStatusIcon()}
          label={isConnected ? 'Live' : 'Offline'}
          color={getStatusColor()}
          size="small"
          onClick={() => setDetailsOpen(true)}
          sx={{ cursor: 'pointer' }}
        />
      </Tooltip>
      
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          WebSocket Connection Details
        </DialogTitle>
        <DialogContent>
          <List>
            <ListItem>
              <ListItemIcon>
                {getStatusIcon()}
              </ListItemIcon>
              <ListItemText 
                primary="Connection Status"
                secondary={connectionState.charAt(0).toUpperCase() + connectionState.slice(1)}
              />
            </ListItem>
            
            <ListItem>
              <ListItemIcon>
                <CheckCircle color={lastHeartbeat && (new Date() - lastHeartbeat) < 30000 ? 'success' : 'error'} />
              </ListItemIcon>
              <ListItemText 
                primary="Last Heartbeat"
                secondary={formatLastHeartbeat()}
              />
            </ListItem>
            
            <ListItem>
              <ListItemIcon>
                <Info />
              </ListItemIcon>
              <ListItemText 
                primary="Messages Received"
                secondary={messageCount}
              />
            </ListItem>
            
            <ListItem>
              <ListItemIcon>
                <Refresh />
              </ListItemIcon>
              <ListItemText 
                primary="Reconnect Attempts"
                secondary={reconnectAttempts}
              />
            </ListItem>
          </List>
          
          {subscriptions.length > 0 && (
            <>
              <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                Active Subscriptions
              </Typography>
              <List dense>
                {subscriptions.map((sub, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={sub} />
                  </ListItem>
                ))}
              </List>
            </>
          )}
          
          {!isConnected && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              WebSocket is disconnected. Real-time updates are unavailable.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          {!isConnected && (
            <Button onClick={handleReconnect} startIcon={<Refresh />}>
              Reconnect
            </Button>
          )}
          <Button onClick={() => setDetailsOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default WebSocketStatus;