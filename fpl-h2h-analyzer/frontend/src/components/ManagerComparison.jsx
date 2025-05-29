import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  EmojiEvents,
  SwapHoriz,
  TrendingUp,
  SportsSoccer,
  Timeline
} from '@mui/icons-material';
import { fplApi } from '../services/api';
import { H2HComparisonSkeleton } from './Skeletons';
import { useOptimizedAPI } from '../hooks/useOptimizedAPI';
import cacheService from '../services/cache';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`comparison-tabpanel-${index}`}
      aria-labelledby={`comparison-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

function ManagerComparison({ manager1, manager2, leagueId }) {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [battleData, setBattleData] = useState(null);
  const [manager1Info, setManager1Info] = useState(null);
  const [manager2Info, setManager2Info] = useState(null);

  useEffect(() => {
    fetchComparisonData();
  }, [manager1, manager2]);

  const fetchComparisonData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check cache first
      const cacheKey = `h2h_comparison_${manager1.entry}_${manager2.entry}`;
      const cached = cacheService.get(cacheKey);
      
      if (cached) {
        setBattleData(cached.battle);
        setManager1Info(cached.m1Info);
        setManager2Info(cached.m2Info);
        setLoading(false);
        return;
      }

      // Fetch battle analysis and manager details in parallel
      const [battle, m1Info, m2Info] = await Promise.all([
        fplApi.getBattleDetails(manager1.entry, manager2.entry),
        fplApi.getManagerInfo(manager1.entry),
        fplApi.getManagerInfo(manager2.entry)
      ]);
      
      setBattleData(battle);
      setManager1Info(m1Info);
      setManager2Info(m2Info);
      
      // Cache the results
      cacheService.set(cacheKey, {
        battle,
        m1Info,
        m2Info
      }, 'h2h_analytics');

    } catch (err) {
      console.error('Error fetching comparison data:', err);
      setError(err.message || 'Failed to load comparison data');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  if (loading) {
    return <H2HComparisonSkeleton />;
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!battleData) {
    return (
      <Alert severity="warning">
        No comparison data available.
      </Alert>
    );
  }

  const manager1Score = battleData.manager1?.score?.total || 0;
  const manager2Score = battleData.manager2?.score?.total || 0;
  const scoreDiff = Math.abs(manager1Score - manager2Score);
  const manager1Winning = manager1Score > manager2Score;
  const isDraw = manager1Score === manager2Score;

  return (
    <Box>
      {/* Current Battle Summary */}
      <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #1a1e3a 0%, #0a0e27 100%)' }}>
        <Typography variant="h6" gutterBottom textAlign="center" color="primary">
          Gameweek {battleData.gameweek} Battle
        </Typography>
        
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={5}>
            <Box textAlign="center">
              <Avatar sx={{ width: 60, height: 60, mx: 'auto', mb: 1, bgcolor: 'primary.main' }}>
                {manager1.player_name.charAt(0)}
              </Avatar>
              <Typography variant="h6">{manager1.player_name}</Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {manager1.entry_name}
              </Typography>
              <Typography 
                variant="h3" 
                sx={{ 
                  color: isDraw ? 'warning.main' : (manager1Winning ? 'success.main' : 'error.main'),
                  fontWeight: 'bold'
                }}
              >
                {manager1Score}
              </Typography>
              {battleData.manager1?.score?.chip && (
                <Chip 
                  label={battleData.manager1.score.chip.toUpperCase()} 
                  size="small" 
                  color="secondary" 
                  sx={{ mt: 1 }}
                />
              )}
            </Box>
          </Grid>
          
          <Grid item xs={2}>
            <Box textAlign="center">
              <Typography variant="h5" color="text.secondary">VS</Typography>
              {!isDraw && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  +{scoreDiff}
                </Typography>
              )}
            </Box>
          </Grid>
          
          <Grid item xs={5}>
            <Box textAlign="center">
              <Avatar sx={{ width: 60, height: 60, mx: 'auto', mb: 1, bgcolor: 'primary.main' }}>
                {manager2.player_name.charAt(0)}
              </Avatar>
              <Typography variant="h6">{manager2.player_name}</Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {manager2.entry_name}
              </Typography>
              <Typography 
                variant="h3" 
                sx={{ 
                  color: isDraw ? 'warning.main' : (!manager1Winning ? 'success.main' : 'error.main'),
                  fontWeight: 'bold'
                }}
              >
                {manager2Score}
              </Typography>
              {battleData.manager2?.score?.chip && (
                <Chip 
                  label={battleData.manager2.score.chip.toUpperCase()} 
                  size="small" 
                  color="secondary" 
                  sx={{ mt: 1 }}
                />
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Detailed Comparison Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} variant="fullWidth">
          <Tab icon={<EmojiEvents />} label="Head to Head" />
          <Tab icon={<SportsSoccer />} label="Squad Comparison" />
          <Tab icon={<SwapHoriz />} label="Transfer Analysis" />
          <Tab icon={<Timeline />} label="Performance Trends" />
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Overall H2H Record
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Box display="flex" justifyContent="space-around">
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {manager1.matches_won}
                      </Typography>
                      <Typography variant="body2">{manager1.player_name} Wins</Typography>
                    </Box>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {manager1.matches_drawn}
                      </Typography>
                      <Typography variant="body2">Draws</Typography>
                    </Box>
                    <Box textAlign="center">
                      <Typography variant="h4" color="error.main">
                        {manager1.matches_lost}
                      </Typography>
                      <Typography variant="body2">{manager2.player_name} Wins</Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Season Performance
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="League Position"
                        secondary={`${manager1.player_name}: #${manager1.rank} | ${manager2.player_name}: #${manager2.rank}`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Total Points (H2H)"
                        secondary={`${manager1.player_name}: ${manager1.total} | ${manager2.player_name}: ${manager2.total}`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Points For"
                        secondary={`${manager1.player_name}: ${manager1.points_for} | ${manager2.player_name}: ${manager2.points_for}`}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Differential Players
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          {battleData.differentials && battleData.differentials.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Player</TableCell>
                    <TableCell>Team</TableCell>
                    <TableCell>Owned By</TableCell>
                    <TableCell align="right">Points</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {battleData.differentials.map((diff, index) => (
                    <TableRow key={index}>
                      <TableCell>{diff.name || `Player ${diff.player_id}`}</TableCell>
                      <TableCell>{diff.team || 'Unknown'}</TableCell>
                      <TableCell>
                        <Chip 
                          label={diff.owner === manager1.entry ? manager1.player_name : manager2.player_name}
                          size="small"
                          color={diff.owner === manager1.entry ? 'primary' : 'secondary'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="bold">
                          {diff.points}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No differential players in current gameweek
            </Typography>
          )}
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Recent Transfers
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {manager1.player_name}
                  </Typography>
                  {battleData.manager1?.transfers ? (
                    <List dense>
                      {battleData.manager1.transfers.slice(0, 5).map((transfer, idx) => (
                        <ListItem key={idx}>
                          <ListItemText
                            primary={`GW${transfer.gameweek}: ${transfer.player_out_name} → ${transfer.player_in_name}`}
                            secondary={`Cost: ${transfer.cost || 0}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No recent transfers
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {manager2.player_name}
                  </Typography>
                  {battleData.manager2?.transfers ? (
                    <List dense>
                      {battleData.manager2.transfers.slice(0, 5).map((transfer, idx) => (
                        <ListItem key={idx}>
                          <ListItemText
                            primary={`GW${transfer.gameweek}: ${transfer.player_out_name} → ${transfer.player_in_name}`}
                            secondary={`Cost: ${transfer.cost || 0}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No recent transfers
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Season Performance Metrics
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={2}>
            {[
              { label: 'Average Points', m1: manager1.points_for ? (manager1.points_for / manager1.matches_played).toFixed(1) : 'N/A', m2: manager2.points_for ? (manager2.points_for / manager2.matches_played).toFixed(1) : 'N/A' },
              { label: 'Win Rate', m1: manager1.matches_played ? `${((manager1.matches_won / manager1.matches_played) * 100).toFixed(0)}%` : 'N/A', m2: manager2.matches_played ? `${((manager2.matches_won / manager2.matches_played) * 100).toFixed(0)}%` : 'N/A' },
              { label: 'Total Matches', m1: manager1.matches_played, m2: manager2.matches_played },
            ].map((metric, idx) => (
              <Grid item xs={12} key={idx}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {metric.label}
                  </Typography>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="h6">{manager1.player_name}: {metric.m1}</Typography>
                    <Typography variant="h6">{manager2.player_name}: {metric.m2}</Typography>
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
}

export default ManagerComparison;