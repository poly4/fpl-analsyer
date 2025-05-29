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
  Button,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent
} from '@mui/lab';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  LineChart,
  Line,
  Legend
} from 'recharts';
import { 
  EmojiEvents, 
  Star, 
  Speed, 
  Shield, 
  Refresh,
  CalendarToday,
  TrendingUp,
  Warning
} from '@mui/icons-material';

function ChipStrategy({ data, manager1Id, manager2Id }) {
  const [selectedChip, setSelectedChip] = useState('all');
  const [viewMode, setViewMode] = useState('calendar');
  const [chipData, setChipData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch chip strategy data
  useEffect(() => {
    const fetchChipData = async () => {
      if (!manager1Id) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/analytics/chip-strategy/${manager1Id}`);
        if (!response.ok) {
          throw new Error('Failed to fetch chip strategy');
        }
        const result = await response.json();
        setChipData(result);
      } catch (err) {
        console.error('Error fetching chip data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchChipData();
  }, [manager1Id]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="error">
          Error: {error}
        </Typography>
      </Box>
    );
  }

  // Try to use chip data from comprehensive analytics or dedicated endpoint
  const chip_strategy = data?.chip_strategy || chipData;
  
  if (!chip_strategy) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="textSecondary">
          No chip strategy data available
        </Typography>
      </Box>
    );
  }

  // Chip usage data
  const chipUsage = [
    { 
      chip: 'Wildcard', 
      manager1: chip_strategy.manager1_chips?.wildcard_used ? 1 : 0,
      manager2: chip_strategy.manager2_chips?.wildcard_used ? 1 : 0,
      manager1_gw: chip_strategy.manager1_chips?.wildcard_gw || 'Not used',
      manager2_gw: chip_strategy.manager2_chips?.wildcard_gw || 'Not used',
      icon: <Refresh />,
      color: '#4caf50'
    },
    { 
      chip: 'Triple Captain', 
      manager1: chip_strategy.manager1_chips?.triple_captain_used ? 1 : 0,
      manager2: chip_strategy.manager2_chips?.triple_captain_used ? 1 : 0,
      manager1_gw: chip_strategy.manager1_chips?.triple_captain_gw || 'Not used',
      manager2_gw: chip_strategy.manager2_chips?.triple_captain_gw || 'Not used',
      icon: <Star />,
      color: '#ff9800'
    },
    { 
      chip: 'Bench Boost', 
      manager1: chip_strategy.manager1_chips?.bench_boost_used ? 1 : 0,
      manager2: chip_strategy.manager2_chips?.bench_boost_used ? 1 : 0,
      manager1_gw: chip_strategy.manager1_chips?.bench_boost_gw || 'Not used',
      manager2_gw: chip_strategy.manager2_chips?.bench_boost_gw || 'Not used',
      icon: <TrendingUp />,
      color: '#2196f3'
    },
    { 
      chip: 'Free Hit', 
      manager1: chip_strategy.manager1_chips?.free_hit_used ? 1 : 0,
      manager2: chip_strategy.manager2_chips?.free_hit_used ? 1 : 0,
      manager1_gw: chip_strategy.manager1_chips?.free_hit_gw || 'Not used',
      manager2_gw: chip_strategy.manager2_chips?.free_hit_gw || 'Not used',
      icon: <Speed />,
      color: '#9c27b0'
    }
  ];

  // Chip recommendations
  const recommendations = chip_strategy.recommendations || [];

  // Chip effectiveness radar
  const chipEffectiveness = chip_strategy.chip_effectiveness ? [
    { chip: 'Wildcard', manager1: chip_strategy.chip_effectiveness.manager1_wildcard_roi * 100, manager2: chip_strategy.chip_effectiveness.manager2_wildcard_roi * 100 },
    { chip: 'Triple Captain', manager1: chip_strategy.chip_effectiveness.manager1_tc_roi * 100, manager2: chip_strategy.chip_effectiveness.manager2_tc_roi * 100 },
    { chip: 'Bench Boost', manager1: chip_strategy.chip_effectiveness.manager1_bb_roi * 100, manager2: chip_strategy.chip_effectiveness.manager2_bb_roi * 100 },
    { chip: 'Free Hit', manager1: chip_strategy.chip_effectiveness.manager1_fh_roi * 100, manager2: chip_strategy.chip_effectiveness.manager2_fh_roi * 100 }
  ] : [];

  // Optimal timing analysis
  const optimalTiming = chip_strategy.optimal_timing || [];

  // Chip timeline
  const chipTimeline = [];
  for (let gw = 1; gw <= 38; gw++) {
    const gwData = {
      gameweek: gw,
      manager1_chip: null,
      manager2_chip: null,
      difficulty: chip_strategy.gameweek_difficulty?.[gw] || 'Medium'
    };

    // Check for chip usage in this gameweek
    chipUsage.forEach(chip => {
      if (chip.manager1_gw === gw) gwData.manager1_chip = chip.chip;
      if (chip.manager2_gw === gw) gwData.manager2_chip = chip.chip;
    });

    chipTimeline.push(gwData);
  }

  const getChipColor = (chip) => {
    const chipData = chipUsage.find(c => c.chip === chip);
    return chipData?.color || '#757575';
  };

  const getROIColor = (roi) => {
    if (roi > 50) return '#4caf50';
    if (roi > 0) return '#ff9800';
    return '#f44336';
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'Easy': return '#4caf50';
      case 'Medium': return '#ff9800';
      case 'Hard': return '#f44336';
      default: return '#757575';
    }
  };

  return (
    <Grid container spacing={3}>
      {/* View Controls */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item>
              <Typography variant="body1">View Mode:</Typography>
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(e, value) => value && setViewMode(value)}
                size="small"
              >
                <ToggleButton value="calendar">Calendar</ToggleButton>
                <ToggleButton value="timeline">Timeline</ToggleButton>
                <ToggleButton value="analysis">Analysis</ToggleButton>
              </ToggleButtonGroup>
            </Grid>
            <Grid item>
              <Typography variant="body1">Chip Filter:</Typography>
              <ToggleButtonGroup
                value={selectedChip}
                exclusive
                onChange={(e, value) => value && setSelectedChip(value)}
                size="small"
              >
                <ToggleButton value="all">All</ToggleButton>
                <ToggleButton value="wildcard">Wildcard</ToggleButton>
                <ToggleButton value="triple_captain">Triple Captain</ToggleButton>
                <ToggleButton value="bench_boost">Bench Boost</ToggleButton>
                <ToggleButton value="free_hit">Free Hit</ToggleButton>
              </ToggleButtonGroup>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Chip Usage Summary */}
      <Grid item xs={12}>
        <Grid container spacing={2}>
          {chipUsage.map((chip, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: chip.color, mr: 2 }}>
                      {chip.icon}
                    </Avatar>
                    <Typography variant="h6">
                      {chip.chip}
                    </Typography>
                  </Box>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Manager 1
                      </Typography>
                      <Typography variant="body1">
                        {chip.manager1 ? `GW${chip.manager1_gw}` : 'Not used'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Manager 2
                      </Typography>
                      <Typography variant="body1">
                        {chip.manager2 ? `GW${chip.manager2_gw}` : 'Not used'}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Grid>

      {/* Calendar View */}
      {viewMode === 'calendar' && (
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Chip Usage Calendar
            </Typography>
            <Grid container spacing={1}>
              {chipTimeline.map((gw, index) => (
                <Grid item xs={2} sm={1} key={index}>
                  <Box 
                    sx={{ 
                      p: 1, 
                      textAlign: 'center', 
                      border: 1, 
                      borderColor: 'divider',
                      borderRadius: 1,
                      bgcolor: getDifficultyColor(gw.difficulty) + '20'
                    }}
                  >
                    <Typography variant="caption" fontWeight="bold">
                      GW{gw.gameweek}
                    </Typography>
                    {gw.manager1_chip && (
                      <Chip 
                        label="M1" 
                        size="small" 
                        sx={{ 
                          bgcolor: getChipColor(gw.manager1_chip), 
                          color: 'white', 
                          fontSize: '0.6rem',
                          height: 16,
                          mt: 0.5
                        }} 
                      />
                    )}
                    {gw.manager2_chip && (
                      <Chip 
                        label="M2" 
                        size="small" 
                        sx={{ 
                          bgcolor: getChipColor(gw.manager2_chip), 
                          color: 'white', 
                          fontSize: '0.6rem',
                          height: 16,
                          mt: 0.5
                        }} 
                      />
                    )}
                  </Box>
                </Grid>
              ))}
            </Grid>
            <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip label="Easy Gameweek" sx={{ bgcolor: '#4caf5020' }} size="small" />
              <Chip label="Medium Gameweek" sx={{ bgcolor: '#ff980020' }} size="small" />
              <Chip label="Hard Gameweek" sx={{ bgcolor: '#f4433620' }} size="small" />
            </Box>
          </Paper>
        </Grid>
      )}

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Chip Usage Timeline
            </Typography>
            <Timeline>
              {chipTimeline
                .filter(gw => gw.manager1_chip || gw.manager2_chip)
                .map((gw, index) => (
                <TimelineItem key={index}>
                  <TimelineOppositeContent color="text.secondary">
                    GW{gw.gameweek}
                  </TimelineOppositeContent>
                  <TimelineSeparator>
                    <TimelineDot color="primary">
                      <EmojiEvents />
                    </TimelineDot>
                    {index < chipTimeline.length - 1 && <TimelineConnector />}
                  </TimelineSeparator>
                  <TimelineContent>
                    {gw.manager1_chip && (
                      <Typography variant="body1">
                        Manager 1: {gw.manager1_chip}
                      </Typography>
                    )}
                    {gw.manager2_chip && (
                      <Typography variant="body1">
                        Manager 2: {gw.manager2_chip}
                      </Typography>
                    )}
                  </TimelineContent>
                </TimelineItem>
              ))}
            </Timeline>
          </Paper>
        </Grid>
      )}

      {/* Analysis View */}
      {viewMode === 'analysis' && (
        <>
          {/* Chip Effectiveness Radar */}
          <Grid item xs={12} lg={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Chip Effectiveness (ROI %)
              </Typography>
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={chipEffectiveness}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="chip" />
                  <PolarRadiusAxis 
                    angle={30} 
                    domain={[-50, 100]} 
                  />
                  <Radar 
                    name="Manager 1" 
                    dataKey="manager1" 
                    stroke="#1976d2" 
                    fill="#1976d2" 
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Radar 
                    name="Manager 2" 
                    dataKey="manager2" 
                    stroke="#d32f2f" 
                    fill="#d32f2f" 
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Optimal Timing */}
          <Grid item xs={12} lg={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Optimal Chip Timing
              </Typography>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={optimalTiming}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="gameweek" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="optimal_score" name="Optimal Score">
                    {optimalTiming.map((entry, index) => (
                      <Cell key={index} fill={getDifficultyColor(entry.difficulty)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </>
      )}

      {/* Recommendations */}
      <Grid item xs={12} lg={8}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Chip Strategy Recommendations
          </Typography>
          <List>
            {recommendations.map((rec, index) => (
              <ListItem key={index} divider>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: rec.priority === 'High' ? '#f44336' : rec.priority === 'Medium' ? '#ff9800' : '#4caf50' }}>
                    {rec.priority === 'High' ? <Warning /> : <EmojiEvents />}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        {rec.chip} - Gameweek {rec.gameweek}
                      </Typography>
                      <Chip 
                        label={rec.priority} 
                        size="small"
                        color={rec.priority === 'High' ? 'error' : rec.priority === 'Medium' ? 'warning' : 'success'}
                      />
                      <Chip 
                        label={rec.manager || 'Both'} 
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        {rec.reason}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Expected ROI: {rec.expected_roi?.toFixed(1) || 'N/A'}% | 
                        Confidence: {Math.round((rec.confidence || 0) * 100)}%
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={(rec.confidence || 0) * 100} 
                        sx={{ mt: 1 }}
                        color={rec.confidence > 0.7 ? 'success' : rec.confidence > 0.4 ? 'warning' : 'error'}
                      />
                    </Box>
                  }
                />
              </ListItem>
            ))}
            {recommendations.length === 0 && (
              <ListItem>
                <ListItemText primary="No chip recommendations available" />
              </ListItem>
            )}
          </List>
        </Paper>
      </Grid>

      {/* Chip Statistics */}
      <Grid item xs={12} lg={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Chip Statistics
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Metric</TableCell>
                  <TableCell align="center">M1</TableCell>
                  <TableCell align="center">M2</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Chips Used</TableCell>
                  <TableCell align="center">
                    {chipUsage.reduce((sum, chip) => sum + chip.manager1, 0)}/4
                  </TableCell>
                  <TableCell align="center">
                    {chipUsage.reduce((sum, chip) => sum + chip.manager2, 0)}/4
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Avg ROI</TableCell>
                  <TableCell align="center">
                    {chip_strategy.manager1_avg_roi?.toFixed(1) || 'N/A'}%
                  </TableCell>
                  <TableCell align="center">
                    {chip_strategy.manager2_avg_roi?.toFixed(1) || 'N/A'}%
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Best Chip</TableCell>
                  <TableCell align="center">
                    {chip_strategy.manager1_best_chip || 'N/A'}
                  </TableCell>
                  <TableCell align="center">
                    {chip_strategy.manager2_best_chip || 'N/A'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Total Points</TableCell>
                  <TableCell align="center">
                    {chip_strategy.manager1_chip_points || 0}
                  </TableCell>
                  <TableCell align="center">
                    {chip_strategy.manager2_chip_points || 0}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Grid>

      {/* Strategy Insights */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Strategic Insights
          </Typography>
          <Grid container spacing={2}>
            {chip_strategy.insights?.map((insight, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Alert 
                  severity={insight.type || 'info'}
                  sx={{ height: '100%' }}
                >
                  <Typography variant="body2">
                    {insight.message}
                  </Typography>
                </Alert>
              </Grid>
            )) || (
              <Grid item xs={12}>
                <Typography variant="body2" color="textSecondary">
                  No strategic insights available
                </Typography>
              </Grid>
            )}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

export default ChipStrategy;