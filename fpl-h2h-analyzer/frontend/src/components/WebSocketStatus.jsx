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
import { motion, AnimatePresence } from 'framer-motion';
import websocketService from '../services/websocket';
import { GlassCard, GlassStatus } from './modern/';

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
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Box
            onClick={() => setDetailsOpen(true)}
            sx={{
              background: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '12px',
              padding: '8px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              cursor: 'pointer',
              transition: 'all 0.3s ease-out',
              '&:hover': {
                background: 'rgba(255, 255, 255, 0.15)',
                transform: 'translateY(-1px)',
                boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)',
              }
            }}
          >
            <motion.div
              animate={connectionState === 'connecting' ? {
                scale: [1, 1.2, 1],
                transition: { duration: 1, repeat: Infinity }
              } : {}}
            >
              <Circle 
                sx={{ 
                  fontSize: 8, 
                  color: isConnected ? '#00ff88' : connectionState === 'connecting' ? '#ffd93d' : '#ff4757',
                  filter: isConnected ? 'drop-shadow(0 0 4px #00ff88)' : undefined
                }} 
              />
            </motion.div>
            
            <Typography 
              variant="caption" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.9)',
                fontWeight: 500,
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}
            >
              {isConnected ? 'Live' : connectionState === 'connecting' ? 'Connecting' : 'Offline'}
            </Typography>
            
            {isConnected && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                <Typography 
                  variant="caption" 
                  sx={{ 
                    color: 'rgba(0, 255, 136, 0.8)',
                    fontSize: '0.65rem',
                    fontWeight: 400
                  }}
                >
                  {messageCount > 0 && `${messageCount} msgs`}
                </Typography>
              </motion.div>
            )}
          </Box>
        </motion.div>
      </Tooltip>
      
      <Dialog 
        open={detailsOpen} 
        onClose={() => setDetailsOpen(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: {
            background: 'rgba(26, 26, 46, 0.9)',
            backdropFilter: 'blur(30px)',
            WebkitBackdropFilter: 'blur(30px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '20px',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
          }
        }}
        BackdropProps={{
          sx: {
            backdropFilter: 'blur(8px)',
            background: 'rgba(0, 0, 0, 0.5)',
          }
        }}
      >
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