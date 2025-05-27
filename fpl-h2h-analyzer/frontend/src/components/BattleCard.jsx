import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Box, Chip, Divider, IconButton, Badge } from '@mui/material';
import { SportsSoccer, Timer, CheckCircle, OpenInNew, TrendingUp, Wifi } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useH2HBattle } from '../hooks/useWebSocket';

function BattleCard({ battle }) {
  const navigate = useNavigate();
  const [recentUpdate, setRecentUpdate] = useState(false);
  const [scoreChange1, setScoreChange1] = useState(null);
  const [scoreChange2, setScoreChange2] = useState(null);
  
  // Use WebSocket hook for real-time updates
  const { battleData, lastUpdate, updateCount, isConnected } = useH2HBattle(
    battle.manager1_id, 
    battle.manager2_id
  );
  
  const scoreColor1 = battle.score1 > battle.score2 ? 'success.main' : battle.score1 < battle.score2 ? 'error.main' : 'warning.main';
  const scoreColor2 = battle.score2 > battle.score1 ? 'success.main' : battle.score2 < battle.score1 ? 'error.main' : 'warning.main';

  const handleViewDetails = () => {
    navigate(`/battle/${battle.manager1_id}/${battle.manager2_id}`);
  };
  
  // Show visual feedback for recent updates
  useEffect(() => {
    if (lastUpdate) {
      setRecentUpdate(true);
      const timer = setTimeout(() => setRecentUpdate(false), 3000); // Show for 3 seconds
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
          <IconButton size="small" onClick={handleViewDetails}>
            <OpenInNew fontSize="small" />
          </IconButton>
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
      </CardContent>
    </Card>
  );
}

export default BattleCard;