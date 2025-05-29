import React, { useState, useEffect } from 'react';
import { 
  Card, CardContent, Typography, Box, Chip, Divider, IconButton, Badge, 
  LinearProgress, Tooltip, Grid, Collapse, Button, Avatar, Stack, Alert
} from '@mui/material';
import { 
  SportsSoccer, Timer, CheckCircle, OpenInNew, TrendingUp, Wifi,
  ExpandMore, ExpandLess, Analytics, Casino, History, Lightbulb,
  Stars, Person, EmojiEvents, Warning, Circle
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useH2HBattle } from '../hooks/useWebSocket';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function LiveBattleCard({ battle, gameweek = 38 }) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const [liveData, setLiveData] = useState(null);
  const [loadingLive, setLoadingLive] = useState(false);
  const [captainData, setCaptainData] = useState({ manager1: null, manager2: null });
  const [bonusPoints, setBonusPoints] = useState({ manager1: 0, manager2: 0 });
  const [scoringPlayers, setScoringPlayers] = useState({ manager1: [], manager2: [] });
  
  // Use WebSocket hook for real-time updates
  const { battleData, lastUpdate, updateCount, isConnected } = useH2HBattle(
    battle.manager1_id, 
    battle.manager2_id
  );
  
  // Determine colors based on scores
  const scoreColor1 = battle.score1 > battle.score2 ? 'success.main' : battle.score1 < battle.score2 ? 'error.main' : 'warning.main';
  const scoreColor2 = battle.score2 > battle.score1 ? 'success.main' : battle.score2 < battle.score1 ? 'error.main' : 'warning.main';

  // Fetch live match data including BPS, captains, and scoring players
  const fetchLiveData = async () => {
    if (loadingLive || !battle.manager1_id || !battle.manager2_id) return;
    
    setLoadingLive(true);
    try {
      // Fetch live match data
      const response = await axios.get(
        `${API_BASE_URL}/api/analytics/v2/live-match/${battle.manager1_id}/${battle.manager2_id}`,
        { params: { gameweek } }
      );
      
      if (response.data) {
        setLiveData(response.data);
        
        // Extract captain data
        if (response.data.manager1_data?.picks) {
          const captain1 = response.data.manager1_data.picks.find(p => p.is_captain);
          setCaptainData(prev => ({ ...prev, manager1: captain1 }));
        }
        if (response.data.manager2_data?.picks) {
          const captain2 = response.data.manager2_data.picks.find(p => p.is_captain);
          setCaptainData(prev => ({ ...prev, manager2: captain2 }));
        }
        
        // Extract bonus points and scoring players
        processScoringPlayers(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch live data:', error);
    } finally {
      setLoadingLive(false);
    }
  };
  
  // Process scoring players and bonus points
  const processScoringPlayers = (data) => {
    const m1Scorers = [];
    const m2Scorers = [];
    let m1Bonus = 0;
    let m2Bonus = 0;
    
    // Process manager 1 players
    if (data.manager1_data?.picks) {
      data.manager1_data.picks.forEach(pick => {
        const player = data.live_elements?.find(el => el.id === pick.element);
        if (player && player.stats) {
          const points = player.stats.total_points || 0;
          const bps = player.stats.bonus || 0;
          
          if (points > 0 || bps > 0) {
            m1Scorers.push({
              name: player.web_name,
              points: points * (pick.is_captain ? (pick.is_triple_captain ? 3 : 2) : 1),
              bonus: bps,
              goals: player.stats.goals_scored || 0,
              assists: player.stats.assists || 0,
              is_captain: pick.is_captain,
              position: pick.position
            });
          }
          
          if (bps > 0 && pick.position <= 11) {
            m1Bonus += bps * (pick.is_captain ? (pick.is_triple_captain ? 3 : 2) : 1);
          }
        }
      });
    }
    
    // Process manager 2 players
    if (data.manager2_data?.picks) {
      data.manager2_data.picks.forEach(pick => {
        const player = data.live_elements?.find(el => el.id === pick.element);
        if (player && player.stats) {
          const points = player.stats.total_points || 0;
          const bps = player.stats.bonus || 0;
          
          if (points > 0 || bps > 0) {
            m2Scorers.push({
              name: player.web_name,
              points: points * (pick.is_captain ? (pick.is_triple_captain ? 3 : 2) : 1),
              bonus: bps,
              goals: player.stats.goals_scored || 0,
              assists: player.stats.assists || 0,
              is_captain: pick.is_captain,
              position: pick.position
            });
          }
          
          if (bps > 0 && pick.position <= 11) {
            m2Bonus += bps * (pick.is_captain ? (pick.is_triple_captain ? 3 : 2) : 1);
          }
        }
      });
    }
    
    // Sort by points
    m1Scorers.sort((a, b) => b.points - a.points);
    m2Scorers.sort((a, b) => b.points - a.points);
    
    setScoringPlayers({ manager1: m1Scorers.slice(0, 5), manager2: m2Scorers.slice(0, 5) });
    setBonusPoints({ manager1: m1Bonus, manager2: m2Bonus });
  };
  
  useEffect(() => {
    if (expanded && !liveData) {
      fetchLiveData();
    }
  }, [expanded]);
  
  // Update live data from WebSocket
  useEffect(() => {
    if (battleData && battleData.live_data) {
      processScoringPlayers(battleData.live_data);
    }
  }, [battleData]);
  
  const handleViewDetails = () => {
    try {
      if (battle.manager1_id && battle.manager2_id) {
        navigate(`/battle/${battle.manager1_id}/${battle.manager2_id}`);
      }
    } catch (error) {
      console.error('Navigation error:', error);
    }
  };
  
  const renderLiveIndicator = () => {
    if (gameweek === 38) {
      return (
        <Chip 
          icon={<CheckCircle />} 
          label="Season Complete" 
          size="small" 
          color="default"
        />
      );
    }
    
    if (!battle.completed) {
      return (
        <Chip 
          icon={<Timer />} 
          label="Live" 
          size="small" 
          color="success"
          sx={{ 
            animation: 'pulse 2s infinite',
            '@keyframes pulse': {
              '0%': { opacity: 1 },
              '50%': { opacity: 0.6 },
              '100%': { opacity: 1 },
            }
          }}
        />
      );
    }
    
    return (
      <Chip 
        icon={<CheckCircle />} 
        label="FT" 
        size="small" 
        color="default"
      />
    );
  };
  
  const renderScoringPlayer = (player) => (
    <Box 
      key={player.name} 
      sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1, 
        py: 0.5,
        color: player.points > 10 ? 'success.main' : 'text.primary'
      }}
    >
      {player.is_captain && <Stars sx={{ fontSize: 16, color: 'warning.main' }} />}
      <Typography variant="caption" sx={{ flex: 1 }}>
        {player.name}
      </Typography>
      {player.goals > 0 && (
        <Chip 
          label={`${player.goals}G`} 
          size="small" 
          sx={{ height: 18, fontSize: '0.7rem', bgcolor: 'success.light' }} 
        />
      )}
      {player.assists > 0 && (
        <Chip 
          label={`${player.assists}A`} 
          size="small" 
          sx={{ height: 18, fontSize: '0.7rem', bgcolor: 'info.light' }} 
        />
      )}
      {player.bonus > 0 && (
        <Chip 
          label={`+${player.bonus}`} 
          size="small" 
          sx={{ height: 18, fontSize: '0.7rem', bgcolor: 'warning.light' }} 
        />
      )}
      <Typography variant="caption" fontWeight="bold">
        {player.points}pts
      </Typography>
    </Box>
  );
  
  return (
    <Card 
      sx={{ 
        height: '100%',
        position: 'relative',
        transition: 'all 0.3s ease-in-out',
        '&:hover': {
          boxShadow: 3,
        }
      }}
    >
      <CardContent>
        {/* Header with status */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" gap={0.5}>
            {renderLiveIndicator()}
            {isConnected && !battle.completed && gameweek !== 38 && (
              <Chip 
                icon={<Wifi />} 
                label="Connected" 
                size="small" 
                color="info"
              />
            )}
          </Box>
          <Box display="flex" gap={0.5}>
            <IconButton size="small" onClick={handleViewDetails}>
              <OpenInNew fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => setExpanded(!expanded)}>
              {expanded ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          </Box>
        </Box>
        
        {/* Main battle display */}
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={5}>
            <Box textAlign="center">
              <Typography variant="subtitle2" noWrap>
                {battle.team1}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {battle.manager1}
              </Typography>
              <Typography variant="h3" sx={{ color: scoreColor1, my: 1 }}>
                {battle.score1}
              </Typography>
              {bonusPoints.manager1 > 0 && (
                <Chip 
                  label={`+${bonusPoints.manager1} BPS`}
                  size="small"
                  color="warning"
                  sx={{ mb: 1 }}
                />
              )}
              {captainData.manager1 && (
                <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                  <Stars sx={{ fontSize: 16, color: 'warning.main' }} />
                  <Typography variant="caption" color="text.secondary">
                    {captainData.manager1.player_name}
                  </Typography>
                </Box>
              )}
              {battle.chip1 && (
                <Chip 
                  label={battle.chip1} 
                  size="small" 
                  color="secondary" 
                  sx={{ mt: 1 }}
                />
              )}
            </Box>
          </Grid>
          
          <Grid item xs={2}>
            <Typography variant="h6" textAlign="center" color="text.secondary">
              VS
            </Typography>
          </Grid>
          
          <Grid item xs={5}>
            <Box textAlign="center">
              <Typography variant="subtitle2" noWrap>
                {battle.team2}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {battle.manager2}
              </Typography>
              <Typography variant="h3" sx={{ color: scoreColor2, my: 1 }}>
                {battle.score2}
              </Typography>
              {bonusPoints.manager2 > 0 && (
                <Chip 
                  label={`+${bonusPoints.manager2} BPS`}
                  size="small"
                  color="warning"
                  sx={{ mb: 1 }}
                />
              )}
              {captainData.manager2 && (
                <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                  <Stars sx={{ fontSize: 16, color: 'warning.main' }} />
                  <Typography variant="caption" color="text.secondary">
                    {captainData.manager2.player_name}
                  </Typography>
                </Box>
              )}
              {battle.chip2 && (
                <Chip 
                  label={battle.chip2} 
                  size="small" 
                  color="secondary" 
                  sx={{ mt: 1 }}
                />
              )}
            </Box>
          </Grid>
        </Grid>
        
        {/* Live scoring players section */}
        <Collapse in={expanded}>
          <Box mt={3}>
            <Divider sx={{ mb: 2 }} />
            
            {loadingLive ? (
              <LinearProgress />
            ) : (
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    <TrendingUp fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                    Top Scorers - {battle.manager1.split(' ')[0]}
                  </Typography>
                  <Box sx={{ pl: 1 }}>
                    {scoringPlayers.manager1.length > 0 ? (
                      scoringPlayers.manager1.map(renderScoringPlayer)
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        No scoring players yet
                      </Typography>
                    )}
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    <TrendingUp fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                    Top Scorers - {battle.manager2.split(' ')[0]}
                  </Typography>
                  <Box sx={{ pl: 1 }}>
                    {scoringPlayers.manager2.length > 0 ? (
                      scoringPlayers.manager2.map(renderScoringPlayer)
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        No scoring players yet
                      </Typography>
                    )}
                  </Box>
                </Grid>
              </Grid>
            )}
            
            {gameweek === 38 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="caption">
                  Season complete - showing final GW38 data
                </Typography>
              </Alert>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
}

export default LiveBattleCard;