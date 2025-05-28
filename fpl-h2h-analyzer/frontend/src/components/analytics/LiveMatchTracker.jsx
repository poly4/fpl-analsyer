import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  Badge,
  LinearProgress,
  IconButton,
  Divider,
  Alert
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { 
  PlayArrow, 
  Pause, 
  SportsSoccer, 
  Timer, 
  Refresh,
  TrendingUp,
  Person,
  Star
} from '@mui/icons-material';
import io from 'socket.io-client';

function LiveMatchTracker({ data, manager1Id, manager2Id, gameweek }) {
  const [liveData, setLiveData] = useState(null);
  const [isLive, setIsLive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [socket, setSocket] = useState(null);

  // Initialize WebSocket connection for live updates
  useEffect(() => {
    if (isLive) {
      const newSocket = io('ws://localhost:8000', {
        transports: ['websocket']
      });

      newSocket.on('connect', () => {
        console.log('Connected to live updates');
        newSocket.emit('join_room', { manager1_id: manager1Id, manager2_id: manager2Id });
      });

      newSocket.on('live_update', (update) => {
        setLiveData(prev => ({ ...prev, ...update }));
        setLastUpdate(new Date());
      });

      setSocket(newSocket);

      return () => {
        newSocket.disconnect();
      };
    }
  }, [isLive, manager1Id, manager2Id]);

  const liveTracking = data?.live_tracking || liveData;

  if (!liveTracking) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="textSecondary">
          No live tracking data available
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          Live tracking is only available during active gameweeks
        </Typography>
      </Box>
    );
  }

  // Current scores and projections
  const currentScores = {
    manager1: liveTracking.current_scores?.manager1 || 0,
    manager2: liveTracking.current_scores?.manager2 || 0,
    manager1_projected: liveTracking.projected_scores?.manager1 || 0,
    manager2_projected: liveTracking.projected_scores?.manager2 || 0
  };

  // Active players data
  const activePlayers = liveTracking.active_players || [];
  const completedMatches = liveTracking.completed_matches || [];
  const upcomingMatches = liveTracking.upcoming_matches || [];

  // Live events
  const liveEvents = liveTracking.live_events || [];

  // Performance by position
  const positionPerformance = [
    { position: 'GKP', manager1: liveTracking.position_scores?.manager1?.GKP || 0, manager2: liveTracking.position_scores?.manager2?.GKP || 0 },
    { position: 'DEF', manager1: liveTracking.position_scores?.manager1?.DEF || 0, manager2: liveTracking.position_scores?.manager2?.DEF || 0 },
    { position: 'MID', manager1: liveTracking.position_scores?.manager1?.MID || 0, manager2: liveTracking.position_scores?.manager2?.MID || 0 },
    { position: 'FWD', manager1: liveTracking.position_scores?.manager1?.FWD || 0, manager2: liveTracking.position_scores?.manager2?.FWD || 0 }
  ];

  // Captaincy performance
  const captaincyData = [
    { name: 'Manager 1 Captain', value: liveTracking.captaincy?.manager1_captain_points || 0, fill: '#1976d2' },
    { name: 'Manager 2 Captain', value: liveTracking.captaincy?.manager2_captain_points || 0, fill: '#d32f2f' }
  ];

  const getScoreColor = (current, projected) => {
    const performance = current / Math.max(1, projected);
    if (performance > 1.1) return 'success.main';
    if (performance > 0.9) return 'warning.main';
    return 'error.main';
  };

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'goal': return '⚽';
      case 'assist': return '🅰️';
      case 'yellow_card': return '🟨';
      case 'red_card': return '🟥';
      case 'clean_sheet': return '🛡️';
      case 'penalty_miss': return '❌';
      case 'save': return '🧤';
      default: return '📊';
    }
  };

  const toggleLiveTracking = () => {
    setIsLive(!isLive);
  };

  return (
    <Grid container spacing={3}>
      {/* Live Control Header */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconButton 
                onClick={toggleLiveTracking}
                color={isLive ? 'error' : 'success'}
                size="large"
              >
                {isLive ? <Pause /> : <PlayArrow />}
              </IconButton>
              <Box>
                <Typography variant="h6">
                  Live Match Tracker
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {isLive ? 'Live tracking active' : 'Click play to start live tracking'}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="body2" color="textSecondary">
                Last updated: {lastUpdate.toLocaleTimeString()}
              </Typography>
              <Chip 
                label={liveTracking.gameweek_status || 'Unknown'}
                color={liveTracking.gameweek_status === 'Live' ? 'success' : 'default'}
                icon={<SportsSoccer />}
              />
            </Box>
          </Box>
        </Paper>
      </Grid>

      {/* Current Scores */}
      <Grid item xs={12}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Manager 1 Score
                </Typography>
                <Typography variant="h3" color="primary">
                  {currentScores.manager1}
                </Typography>
                <Typography variant="body2">
                  Projected: {currentScores.manager1_projected}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(currentScores.manager1 / Math.max(1, currentScores.manager1_projected)) * 100} 
                  sx={{ mt: 1 }}
                  color={currentScores.manager1 >= currentScores.manager1_projected ? 'success' : 'warning'}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Manager 2 Score
                </Typography>
                <Typography variant="h3" color="secondary">
                  {currentScores.manager2}
                </Typography>
                <Typography variant="body2">
                  Projected: {currentScores.manager2_projected}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(currentScores.manager2 / Math.max(1, currentScores.manager2_projected)) * 100} 
                  sx={{ mt: 1 }}
                  color={currentScores.manager2 >= currentScores.manager2_projected ? 'success' : 'warning'}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Current Lead
                </Typography>
                <Typography variant="h3" sx={{ color: getScoreColor(Math.abs(currentScores.manager1 - currentScores.manager2), 10) }}>
                  {Math.abs(currentScores.manager1 - currentScores.manager2)}
                </Typography>
                <Typography variant="body2">
                  {currentScores.manager1 > currentScores.manager2 ? 'Manager 1' : 
                   currentScores.manager2 > currentScores.manager1 ? 'Manager 2' : 'Tied'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Matches Progress
                </Typography>
                <Typography variant="h3" color="info.main">
                  {completedMatches.length}/{completedMatches.length + upcomingMatches.length}
                </Typography>
                <Typography variant="body2">
                  {upcomingMatches.length} remaining
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Grid>

      {/* Position Performance */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Performance by Position
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={positionPerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="position" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="manager1" fill="#1976d2" name="Manager 1" />
              <Bar dataKey="manager2" fill="#d32f2f" name="Manager 2" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Captaincy Performance */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Captaincy Performance
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={captaincyData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value} pts`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {captaincyData.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2">
              Manager 1 Captain: {liveTracking.captaincy?.manager1_captain || 'Unknown'}
            </Typography>
            <Typography variant="body2">
              Manager 2 Captain: {liveTracking.captaincy?.manager2_captain || 'Unknown'}
            </Typography>
          </Box>
        </Paper>
      </Grid>

      {/* Active Players */}
      <Grid item xs={12} lg={8}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Active Players Performance
          </Typography>
          <List sx={{ maxHeight: 400, overflow: 'auto' }}>
            {activePlayers.map((player, index) => (
              <ListItem key={index} divider>
                <ListItemAvatar>
                  <Badge 
                    badgeContent={player.live_points || 0} 
                    color={player.live_points > 0 ? 'success' : 'default'}
                  >
                    <Avatar sx={{ 
                      bgcolor: player.manager === 'manager1' ? '#1976d2' : '#d32f2f'
                    }}>
                      <Person />
                    </Avatar>
                  </Badge>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        {player.web_name}
                      </Typography>
                      {player.is_captain && <Star color="warning" fontSize="small" />}
                      <Chip 
                        label={player.position} 
                        size="small" 
                        variant="outlined"
                      />
                      <Chip 
                        label={player.team} 
                        size="small" 
                        color="primary"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        Minutes: {player.minutes || 0} | 
                        Live Points: {player.live_points || 0} | 
                        BPS: {player.bps || 0}
                      </Typography>
                      {player.fixture_status && (
                        <Chip 
                          label={player.fixture_status} 
                          size="small"
                          color={player.fixture_status === 'Live' ? 'success' : 'default'}
                          sx={{ mt: 0.5 }}
                        />
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      {/* Live Events Feed */}
      <Grid item xs={12} lg={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Live Events
          </Typography>
          <List sx={{ maxHeight: 400, overflow: 'auto' }}>
            {liveEvents.slice(0, 10).map((event, index) => (
              <ListItem key={index}>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    {getEventIcon(event.type)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={event.description}
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        {event.player_name} - {event.time}'
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
            {liveEvents.length === 0 && (
              <ListItem>
                <ListItemText 
                  primary="No live events yet" 
                  secondary="Events will appear here during live matches"
                />
              </ListItem>
            )}
          </List>
        </Paper>
      </Grid>

      {/* Match Status */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Match Status
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Completed Matches ({completedMatches.length})
              </Typography>
              {completedMatches.map((match, index) => (
                <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'success.light', borderRadius: 1 }}>
                  <Typography variant="body2">
                    {match.home_team} {match.home_score} - {match.away_score} {match.away_team}
                  </Typography>
                </Box>
              ))}
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                Upcoming Matches ({upcomingMatches.length})
              </Typography>
              {upcomingMatches.map((match, index) => (
                <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'warning.light', borderRadius: 1 }}>
                  <Typography variant="body2">
                    {match.home_team} vs {match.away_team}
                  </Typography>
                  <Typography variant="caption">
                    {new Date(match.kickoff_time).toLocaleString()}
                  </Typography>
                </Box>
              ))}
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Alerts and Notifications */}
      {liveTracking.alerts && liveTracking.alerts.length > 0 && (
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Live Alerts
            </Typography>
            {liveTracking.alerts.map((alert, index) => (
              <Alert 
                key={index} 
                severity={alert.type || 'info'} 
                sx={{ mb: 1 }}
              >
                {alert.message}
              </Alert>
            ))}
          </Paper>
        </Grid>
      )}
    </Grid>
  );
}

export default LiveMatchTracker;