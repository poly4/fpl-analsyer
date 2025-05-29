import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  CircularProgress, 
  Alert, 
  Button, 
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import LiveBattleCard from './LiveBattleCard';
import { fplApi } from '../services/api';
import websocketService, { MessageTypes } from '../services/websocket';

function LiveBattles({ leagueId }) {
  const [battles, setBattles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentGameweek, setCurrentGameweek] = useState(null);
  const [selectedGameweek, setSelectedGameweek] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [realtimeUpdates, setRealtimeUpdates] = useState(0);

  const fetchBattles = async (gameweek = null) => {
    if (!leagueId) {
      setError('No league selected');
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);

      // Get current gameweek if not already set
      if (!currentGameweek) {
        try {
          const gwData = await fplApi.getCurrentGameweek();
          setCurrentGameweek(gwData.gameweek);
          if (!selectedGameweek) {
            setSelectedGameweek(gwData.gameweek);
          }
        } catch (gwError) {
          console.error('Failed to get current gameweek:', gwError);
          // Default to GW38 if current gameweek fails
          setCurrentGameweek(38);
          setSelectedGameweek(38);
        }
      }

      // Get live battles for specific gameweek
      const targetGameweek = gameweek || selectedGameweek || currentGameweek || 38;
      const url = `http://localhost:8000/api/h2h/live-battles/${leagueId}?gameweek=${targetGameweek}`;
      
      const response = await fetch(url);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`No battles found for gameweek ${targetGameweek}`);
        } else if (response.status === 500) {
          throw new Error('Server error. Please try again later.');
        }
        throw new Error(`Failed to fetch battles: ${response.status}`);
      }
      const battlesData = await response.json();
      
      // Validate and transform data safely
      if (!battlesData || !battlesData.battles || !Array.isArray(battlesData.battles)) {
        console.warn('Invalid battles data received:', battlesData);
        setBattles([]);
        return;
      }
      
      const transformedBattles = battlesData.battles.map(battle => {
        try {
          return {
            id: battle.match_id || `${battle.manager1?.id}-${battle.manager2?.id}`,
            manager1: battle.manager1?.player_name || 'Unknown',
            team1: battle.manager1?.name || 'Unknown Team',
            score1: battle.manager1?.score || 0,
            chip1: battle.manager1?.chip || null,
            manager2: battle.manager2?.player_name || 'Unknown',
            team2: battle.manager2?.name || 'Unknown Team',
            score2: battle.manager2?.score || 0,
            chip2: battle.manager2?.chip || null,
            completed: battle.completed || false,
            error: battle.error || null,
            manager1_id: battle.manager1?.id,
            manager2_id: battle.manager2?.id
          };
        } catch (transformError) {
          console.error('Error transforming battle:', transformError, battle);
          return null;
        }
      }).filter(Boolean); // Remove any null entries

      setBattles(transformedBattles);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching battles:', err);
      setError(err.message || 'Failed to load battles');
      setBattles([]); // Set empty battles to prevent undefined errors
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

  // Handle gameweek change
  const handleGameweekChange = (event) => {
    const newGameweek = event.target.value;
    setSelectedGameweek(newGameweek);
    fetchBattles(newGameweek);
  };

  useEffect(() => {
    fetchBattles();

    try {
      // Set up WebSocket connection handlers with error handling
      if (websocketService && websocketService.setConnectionChangeCallback) {
        websocketService.setConnectionChangeCallback(setIsConnected);
      }
      
      // Add message handlers for real-time updates
      if (websocketService && MessageTypes) {
        websocketService.addMessageHandler(MessageTypes.H2H_UPDATE, handleH2HUpdate);
        websocketService.addMessageHandler(MessageTypes.LIVE_SCORES, handleLiveScoreUpdate);
        websocketService.addMessageHandler(MessageTypes.LEAGUE_UPDATE, handleLeagueUpdate);
      }
    } catch (wsError) {
      console.error('WebSocket setup error:', wsError);
      // Continue without WebSocket - app should still work
    }
    
    return () => {
      try {
        // Clean up message handlers
        if (websocketService && MessageTypes) {
          websocketService.removeMessageHandler(MessageTypes.H2H_UPDATE, handleH2HUpdate);
          websocketService.removeMessageHandler(MessageTypes.LIVE_SCORES, handleLiveScoreUpdate);
          websocketService.removeMessageHandler(MessageTypes.LEAGUE_UPDATE, handleLeagueUpdate);
        }
      } catch (cleanupError) {
        console.error('WebSocket cleanup error:', cleanupError);
      }
    };
  }, [handleH2HUpdate, handleLiveScoreUpdate, handleLeagueUpdate]);

  // Subscribe to real-time updates when gameweek is available
  useEffect(() => {
    if (currentGameweek && isConnected) {
      // Subscribe to league updates
      websocketService.subscribeToLeague(leagueId);
      
      // Subscribe to live gameweek updates
      websocketService.subscribeToLiveGameweek(currentGameweek);
      
      // Subscribe to H2H battles for each battle
      battles.forEach(battle => {
        if (battle.manager1_id && battle.manager2_id) {
          websocketService.subscribeToH2HBattle(battle.manager1_id, battle.manager2_id);
        }
      });
      
      console.log(`🔔 Subscribed to real-time updates for GW${currentGameweek} and league ${leagueId}`);
    }
  }, [currentGameweek, isConnected, battles, leagueId]);

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
          <Box display="flex" alignItems="center" gap={2} mb={1}>
            <Typography variant="h5">
              H2H Battles
            </Typography>
            {currentGameweek && (
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Gameweek</InputLabel>
                <Select
                  value={selectedGameweek || currentGameweek}
                  label="Gameweek"
                  onChange={handleGameweekChange}
                >
                  {Array.from({ length: 38 }, (_, i) => i + 1).map(gw => (
                    <MenuItem key={gw} value={gw}>
                      GW {gw}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
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
            <LiveBattleCard 
              battle={battle}
              gameweek={selectedGameweek || currentGameweek || 38}
            />
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