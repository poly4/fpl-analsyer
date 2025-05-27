import React, { useState, useEffect, useCallback } from 'react';
import { Box, Typography, Grid, CircularProgress, Alert, Button, Chip } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import EnhancedBattleCard from './EnhancedBattleCard';
import { fplApi } from '../services/api';
import websocketService, { MessageTypes } from '../services/websocket';

// Default league ID from config
const DEFAULT_LEAGUE_ID = 620117; // Top Dog Premier League

function LiveBattles() {
  const [battles, setBattles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentGameweek, setCurrentGameweek] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [realtimeUpdates, setRealtimeUpdates] = useState(0);

  const fetchBattles = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get current gameweek
      const gwData = await fplApi.getCurrentGameweek();
      setCurrentGameweek(gwData.gameweek);

      // Get live battles
      const battlesData = await fplApi.getLiveBattles(DEFAULT_LEAGUE_ID);
      
      // Transform data for BattleCard component
      const transformedBattles = battlesData.battles.map(battle => ({
        id: battle.match_id,
        manager1: battle.manager1.player_name,
        team1: battle.manager1.name,
        score1: battle.manager1.score,
        chip1: battle.manager1.chip,
        manager2: battle.manager2.player_name,
        team2: battle.manager2.name,
        score2: battle.manager2.score,
        chip2: battle.manager2.chip,
        completed: battle.completed,
        error: battle.error,
        manager1_id: battle.manager1.id,
        manager2_id: battle.manager2.id
      }));

      setBattles(transformedBattles);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching battles:', err);
      setError(err.message || 'Failed to load battles');
    } finally {
      setLoading(false);
    }
  };

  // Handle real-time H2H updates
  const handleH2HUpdate = useCallback((data, meta) => {
    console.log('📊 H2H Update received:', data);
    
    setBattles(prevBattles => {
      const updatedBattles = prevBattles.map(battle => {
        // Find matching battle based on manager IDs
        const isMatch = (
          (battle.manager1_id === data.manager_id && data.update_type === 'live_points') ||
          (battle.manager2_id === data.manager_id && data.update_type === 'live_points')
        );
        
        if (isMatch) {
          const updatedBattle = { ...battle };
          
          // Update the relevant manager's score
          if (battle.manager1_id === data.manager_id) {
            updatedBattle.score1 = data.points || battle.score1;
          } else if (battle.manager2_id === data.manager_id) {
            updatedBattle.score2 = data.points || battle.score2;
          }
          
          return updatedBattle;
        }
        
        return battle;
      });
      
      return updatedBattles;
    });
    
    setRealtimeUpdates(prev => prev + 1);
    setLastUpdate(new Date());
  }, []);

  // Handle live score updates
  const handleLiveScoreUpdate = useCallback((data, meta) => {
    console.log('⚽ Live Score Update received:', data);
    
    if (data.changes && data.changes.length > 0) {
      // Update battles with new scores from live data
      setBattles(prevBattles => {
        return prevBattles.map(battle => {
          // This is a simplified update - in a real implementation,
          // you'd need to recalculate scores based on player changes
          return { ...battle };
        });
      });
      
      setRealtimeUpdates(prev => prev + 1);
      setLastUpdate(new Date());
    }
  }, []);

  // Handle league updates
  const handleLeagueUpdate = useCallback((data, meta) => {
    console.log('🏆 League Update received:', data);
    
    if (data.update_type === 'new_matches') {
      // Refresh battles when new matches are available
      fetchBattles();
    }
    
    setRealtimeUpdates(prev => prev + 1);
  }, []);

  useEffect(() => {
    fetchBattles();

    // Set up WebSocket connection handlers
    websocketService.setConnectionChangeCallback(setIsConnected);
    
    // Add message handlers for real-time updates
    websocketService.addMessageHandler(MessageTypes.H2H_UPDATE, handleH2HUpdate);
    websocketService.addMessageHandler(MessageTypes.LIVE_SCORES, handleLiveScoreUpdate);
    websocketService.addMessageHandler(MessageTypes.LEAGUE_UPDATE, handleLeagueUpdate);
    
    return () => {
      // Clean up message handlers
      websocketService.removeMessageHandler(MessageTypes.H2H_UPDATE, handleH2HUpdate);
      websocketService.removeMessageHandler(MessageTypes.LIVE_SCORES, handleLiveScoreUpdate);
      websocketService.removeMessageHandler(MessageTypes.LEAGUE_UPDATE, handleLeagueUpdate);
    };
  }, [handleH2HUpdate, handleLiveScoreUpdate, handleLeagueUpdate]);

  // Subscribe to real-time updates when gameweek is available
  useEffect(() => {
    if (currentGameweek && isConnected) {
      // Subscribe to league updates
      websocketService.subscribeToLeague(DEFAULT_LEAGUE_ID);
      
      // Subscribe to live gameweek updates
      websocketService.subscribeToLiveGameweek(currentGameweek);
      
      // Subscribe to H2H battles for each battle
      battles.forEach(battle => {
        if (battle.manager1_id && battle.manager2_id) {
          websocketService.subscribeToH2HBattle(battle.manager1_id, battle.manager2_id);
        }
      });
      
      console.log(`🔔 Subscribed to real-time updates for GW${currentGameweek} and league ${DEFAULT_LEAGUE_ID}`);
    }
  }, [currentGameweek, isConnected, battles]);

  const handleRefresh = () => {
    fetchBattles();
  };

  if (loading && !battles.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <div>
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <Typography variant="h5">
              Live H2H Battles - Gameweek {currentGameweek}
            </Typography>
            <Chip
              icon={isConnected ? <WifiIcon /> : <WifiOffIcon />}
              label={isConnected ? 'Live' : 'Offline'}
              color={isConnected ? 'success' : 'error'}
              size="small"
              variant="outlined"
            />
          </Box>
          <Box display="flex" gap={2}>
            {lastUpdate && (
              <Typography variant="caption" color="text.secondary">
                Last updated: {lastUpdate.toLocaleTimeString()}
              </Typography>
            )}
            {realtimeUpdates > 0 && (
              <Typography variant="caption" color="primary">
                Real-time updates: {realtimeUpdates}
              </Typography>
            )}
          </Box>
        </div>
        <Button
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
          variant="outlined"
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {!isConnected && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Real-time updates are currently unavailable. Scores may be outdated.
        </Alert>
      )}

      <Grid container spacing={2}>
        {battles.map(battle => (
          <Grid item xs={12} sm={6} md={4} key={battle.id}>
            <EnhancedBattleCard battle={battle} />
          </Grid>
        ))}
      </Grid>

      {!loading && battles.length === 0 && (
        <Typography variant="body1" color="text.secondary" textAlign="center">
          No battles found for the current gameweek.
        </Typography>
      )}
    </Box>
  );
}

export default LiveBattles;