import React, { useState, useEffect } from 'react';
import { 
  Card, CardContent, Typography, Box, Chip, Divider, IconButton, Badge, 
  LinearProgress, Tooltip, Grid, Collapse, Button
} from '@mui/material';
import { 
  SportsSoccer, Timer, CheckCircle, OpenInNew, TrendingUp, Wifi,
  ExpandMore, ExpandLess, Analytics, Casino, History, Lightbulb
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useH2HBattle } from '../hooks/useWebSocket';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function EnhancedBattleCard({ battle }) {
  const navigate = useNavigate();
  const [recentUpdate, setRecentUpdate] = useState(false);
  const [scoreChange1, setScoreChange1] = useState(null);
  const [scoreChange2, setScoreChange2] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  
  // Use WebSocket hook for real-time updates
  const { battleData, lastUpdate, updateCount, isConnected } = useH2HBattle(
    battle.manager1_id, 
    battle.manager2_id
  );
  
  const scoreColor1 = battle.score1 > battle.score2 ? 'success.main' : battle.score1 < battle.score2 ? 'error.main' : 'warning.main';
  const scoreColor2 = battle.score2 > battle.score1 ? 'success.main' : battle.score2 < battle.score1 ? 'error.main' : 'warning.main';

  const handleViewDetails = () => {
    try {
      if (battle.manager1_id && battle.manager2_id) {
        navigate(`/battle/${battle.manager1_id}/${battle.manager2_id}`);
      } else {
        console.error('Cannot navigate: missing manager IDs');
      }
    } catch (error) {
      console.error('Navigation error:', error);
    }
  };
  
  const fetchAnalytics = async () => {
    if (analytics || loadingAnalytics) return;
    
    if (!battle.manager1_id || !battle.manager2_id) {
      console.error('Missing manager IDs for analytics');
      return;
    }
    
    setLoadingAnalytics(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/analytics/h2h/comprehensive/${battle.manager1_id}/${battle.manager2_id}`
      );
      
      if (response.data) {
        setAnalytics(response.data);
      } else {
        console.warn('No analytics data received');
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      // Don't crash - just show no analytics
      setAnalytics(null);
    } finally {
      setLoadingAnalytics(false);
    }
  };
  
  const handleToggleExpand = () => {
    if (!expanded && !analytics) {
      fetchAnalytics();
    }
    setExpanded(!expanded);
  };
  
  // Show visual feedback for recent updates
  useEffect(() => {
    if (lastUpdate) {
      setRecentUpdate(true);
      const timer = setTimeout(() => setRecentUpdate(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [lastUpdate]);
  
  // Track score changes
  useEffect(() => {
    if (battleData && battleData.points !== undefined) {
      const managerId = battleData.manager_id;
      const newPoints = battleData.points;
      const previousPoints = battleData.previous_points;
      
      if (previousPoints !== undefined && newPoints !== previousPoints) {
        const change = newPoints - previousPoints;
        
        if (managerId == battle.manager1_id) {
          setScoreChange1(change);
          setTimeout(() => setScoreChange1(null), 5000);
        } else if (managerId == battle.manager2_id) {
          setScoreChange2(change);
          setTimeout(() => setScoreChange2(null), 5000);
        }
      }
    }
  }, [battleData, battle.manager1_id, battle.manager2_id]);

  const renderAnalyticsInsight = () => {
    if (!analytics) return null;
    
    try {
      const { differential_analysis, prediction, chip_strategies } = analytics;
      const winProb1 = prediction?.manager1_win_probability ? Math.round(prediction.manager1_win_probability * 100) : 50;
      const winProb2 = prediction?.manager2_win_probability ? Math.round(prediction.manager2_win_probability * 100) : 50;
    
    return (
      <Box mt={2}>
        <Divider sx={{ mb: 2 }} />
        
        {/* Win Probability */}
        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom>
            <Analytics fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
            Win Probability
          </Typography>
          <Grid container spacing={1} alignItems="center">
            <Grid item xs={5}>
              <Box textAlign="center">
                <Typography variant="h5" color={winProb1 > winProb2 ? 'success.main' : 'text.secondary'}>
                  {winProb1}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={winProb1} 
                  color={winProb1 > winProb2 ? 'success' : 'inherit'}
                  sx={{ height: 8, borderRadius: 1 }}
                />
              </Box>
            </Grid>
            <Grid item xs={2}>
              <Typography variant="caption" color="text.secondary" textAlign="center" display="block">
                vs
              </Typography>
            </Grid>
            <Grid item xs={5}>
              <Box textAlign="center">
                <Typography variant="h5" color={winProb2 > winProb1 ? 'success.main' : 'text.secondary'}>
                  {winProb2}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={winProb2} 
                  color={winProb2 > winProb1 ? 'success' : 'inherit'}
                  sx={{ height: 8, borderRadius: 1 }}
                />
              </Box>
            </Grid>
          </Grid>
        </Box>
        
        {/* Key Differentials */}
        {differential_analysis.key_differentials.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              <TrendingUp fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
              Key Differentials
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={0.5}>
              {differential_analysis.key_differentials.slice(0, 3).map((player, idx) => (
                <Tooltip 
                  key={idx} 
                  title={`PSC: ${player.point_swing_contribution.toFixed(1)} | Own: ${player.effective_ownership_diff.toFixed(1)}%`}
                >
                  <Chip 
                    label={player.player_name} 
                    size="small" 
                    color={player.owned_by === 'manager1' ? 'primary' : 'secondary'}
                    icon={<SportsSoccer fontSize="small" />}
                  />
                </Tooltip>
              ))}
            </Box>
          </Box>
        )}
        
        {/* Chip Recommendations */}
        {(chip_strategies.manager1_chips.length > 0 || chip_strategies.manager2_chips.length > 0) && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              <Casino fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
              Chip Strategy
            </Typography>
            <Grid container spacing={1}>
              {chip_strategies.manager1_chips.length > 0 && (
                <Grid item xs={6}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {battle.manager1.split(' ')[0]}
                    </Typography>
                    {chip_strategies.manager1_chips.map((chip, idx) => (
                      <Chip 
                        key={idx}
                        label={`${chip.chip_type} GW${chip.recommended_gw}`} 
                        size="small" 
                        color="default"
                        sx={{ display: 'block', mb: 0.5 }}
                      />
                    ))}
                  </Box>
                </Grid>
              )}
              {chip_strategies.manager2_chips.length > 0 && (
                <Grid item xs={6}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {battle.manager2.split(' ')[0]}
                    </Typography>
                    {chip_strategies.manager2_chips.map((chip, idx) => (
                      <Chip 
                        key={idx}
                        label={`${chip.chip_type} GW${chip.recommended_gw}`} 
                        size="small" 
                        color="default"
                        sx={{ display: 'block', mb: 0.5 }}
                      />
                    ))}
                  </Box>
                </Grid>
              )}
            </Grid>
          </Box>
        )}
        
        {/* Insights */}
        {differential_analysis.recommendations.length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              <Lightbulb fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
              Strategic Insights
            </Typography>
            <Typography variant="caption" color="text.secondary">
              • {differential_analysis.recommendations[0]}
            </Typography>
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Card 
      sx={{ 
        height: '100%',
        position: 'relative',
        border: recentUpdate ? '2px solid' : '1px solid',
        borderColor: recentUpdate ? 'primary.main' : 'divider',
        transition: 'all 0.3s ease-in-out',
        transform: recentUpdate ? 'scale(1.02)' : 'scale(1)',
        '&:hover': {
          boxShadow: 3,
        }
      }}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Box display="flex" gap={0.5}>
            {battle.completed ? (
              <Chip 
                icon={<CheckCircle />} 
                label="Completed" 
                size="small" 
                color="default"
              />
            ) : (
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
            )}
            {isConnected && !battle.completed && (
              <Chip 
                icon={<Wifi />} 
                label="RT" 
                size="small" 
                color="info"
                sx={{ minWidth: '40px' }}
                title="Real-time updates enabled"
              />
            )}
            {updateCount > 0 && (
              <Badge 
                badgeContent={updateCount} 
                color="primary" 
                max={99}
                sx={{
                  '& .MuiBadge-badge': {
                    right: -3,
                    top: 3,
                  }
                }}
              >
                <Chip 
                  icon={<TrendingUp />} 
                  label="" 
                  size="small" 
                  color="secondary"
                  sx={{ minWidth: '30px' }}
                  title={`${updateCount} real-time updates received`}
                />
              </Badge>
            )}
          </Box>
          <Box display="flex" gap={0.5}>
            <IconButton size="small" onClick={handleToggleExpand}>
              {expanded ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
            <IconButton size="small" onClick={handleViewDetails}>
              <OpenInNew fontSize="small" />
            </IconButton>
          </Box>
        </Box>
        
        <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
          <Box flex={1} textAlign="center">
            <Typography variant="subtitle2" noWrap title={battle.manager1}>
              {battle.manager1}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap title={battle.team1}>
              {battle.team1}
            </Typography>
            <Box display="flex" alignItems="center" justifyContent="center" mt={1}>
              <Typography variant="h4" sx={{ color: scoreColor1 }}>
                {battle.score1}
              </Typography>
              {scoreChange1 && (
                <Typography 
                  variant="caption" 
                  sx={{ 
                    ml: 0.5,
                    color: scoreChange1 > 0 ? 'success.main' : 'error.main',
                    fontWeight: 'bold',
                    animation: 'bounce 0.5s ease-in-out',
                    '@keyframes bounce': {
                      '0%, 20%, 50%, 80%, 100%': { transform: 'translateY(0)' },
                      '40%': { transform: 'translateY(-5px)' },
                      '60%': { transform: 'translateY(-3px)' },
                    }
                  }}
                >
                  {scoreChange1 > 0 ? '+' : ''}{scoreChange1}
                </Typography>
              )}
            </Box>
            {battle.chip1 && (
              <Chip 
                label={battle.chip1.toUpperCase()} 
                size="small" 
                color="primary" 
                sx={{ mt: 0.5 }}
              />
            )}
          </Box>
          
          <Divider orientation="vertical" flexItem />
          
          <Box flex={1} textAlign="center">
            <Typography variant="subtitle2" noWrap title={battle.manager2}>
              {battle.manager2}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap title={battle.team2}>
              {battle.team2}
            </Typography>
            <Box display="flex" alignItems="center" justifyContent="center" mt={1}>
              <Typography variant="h4" sx={{ color: scoreColor2 }}>
                {battle.score2}
              </Typography>
              {scoreChange2 && (
                <Typography 
                  variant="caption" 
                  sx={{ 
                    ml: 0.5,
                    color: scoreChange2 > 0 ? 'success.main' : 'error.main',
                    fontWeight: 'bold',
                    animation: 'bounce 0.5s ease-in-out',
                    '@keyframes bounce': {
                      '0%, 20%, 50%, 80%, 100%': { transform: 'translateY(0)' },
                      '40%': { transform: 'translateY(-5px)' },
                      '60%': { transform: 'translateY(-3px)' },
                    }
                  }}
                >
                  {scoreChange2 > 0 ? '+' : ''}{scoreChange2}
                </Typography>
              )}
            </Box>
            {battle.chip2 && (
              <Chip 
                label={battle.chip2.toUpperCase()} 
                size="small" 
                color="primary" 
                sx={{ mt: 0.5 }}
              />
            )}
          </Box>
        </Box>
        
        {battle.error && (
          <Typography 
            variant="caption" 
            color="error" 
            display="block" 
            textAlign="center" 
            mt={1}
          >
            ⚠️ {battle.error}
          </Typography>
        )}
        
        {lastUpdate && (
          <Typography 
            variant="caption" 
            color="text.secondary" 
            display="block" 
            textAlign="center" 
            mt={0.5}
            sx={{ fontSize: '0.7rem' }}
          >
            🔄 Updated {lastUpdate.toLocaleTimeString()}
          </Typography>
        )}
        
        {/* Analytics Section */}
        <Collapse in={expanded}>
          {loadingAnalytics ? (
            <Box mt={2}>
              <LinearProgress />
              <Typography variant="caption" color="text.secondary" textAlign="center" display="block" mt={1}>
                Loading analytics...
              </Typography>
            </Box>
          ) : (
            renderAnalyticsInsight()
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
}

export default EnhancedBattleCard;