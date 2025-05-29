import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Avatar
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend
} from 'recharts';
import { EmojiEvents, TrendingUp, Psychology, Timeline } from '@mui/icons-material';

function HistoricalPatterns({ data }) {
  // The comprehensive analytics endpoint returns historical_patterns, not historical
  const historical = data?.historical_patterns || data?.historical;
  
  if (!historical) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="textSecondary">
          No historical pattern data available
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          Make sure to analyze two managers with H2H history
        </Typography>
      </Box>
    );
  }
  
  // Prepare historical performance data
  const performanceData = historical.h2h_history?.map((match, index) => ({
    gameweek: match.gameweek || `GW${index + 1}`,
    manager1_score: match.manager1_score,
    manager2_score: match.manager2_score,
    margin: match.manager1_score - match.manager2_score,
    winner: match.manager1_score > match.manager2_score ? 'Manager 1' : 
            match.manager2_score > match.manager1_score ? 'Manager 2' : 'Draw'
  })) || [];

  // Performance trends data
  const trendsData = historical.performance_trends ? [
    { metric: 'Recent Form', manager1: historical.performance_trends.manager1_recent_form, manager2: historical.performance_trends.manager2_recent_form },
    { metric: 'Avg Score', manager1: historical.performance_trends.manager1_avg_score, manager2: historical.performance_trends.manager2_avg_score },
    { metric: 'Consistency', manager1: historical.performance_trends.manager1_consistency, manager2: historical.performance_trends.manager2_consistency },
    { metric: 'Peak Performance', manager1: historical.performance_trends.manager1_peak, manager2: historical.performance_trends.manager2_peak }
  ] : [];

  // Psychological factors radar data
  const psychFactors = historical.psychological_factors ? [
    { factor: 'Pressure Handling', manager1: historical.psychological_factors.pressure_handling_m1 * 100, manager2: historical.psychological_factors.pressure_handling_m2 * 100 },
    { factor: 'Momentum', manager1: historical.psychological_factors.momentum_m1 * 100, manager2: historical.psychological_factors.momentum_m2 * 100 },
    { factor: 'Confidence', manager1: historical.psychological_factors.confidence_m1 * 100, manager2: historical.psychological_factors.confidence_m2 * 100 },
    { factor: 'Experience', manager1: historical.psychological_factors.experience_m1 * 100, manager2: historical.psychological_factors.experience_m2 * 100 }
  ] : [];

  const getWinRateColor = (rate) => {
    if (rate > 60) return 'success';
    if (rate > 40) return 'warning';
    return 'error';
  };

  const getPsychEdgeColor = (edge) => {
    if (edge > 0.3) return '#4caf50';
    if (edge > 0) return '#ff9800';
    if (edge < -0.3) return '#f44336';
    return '#757575';
  };

  return (
    <Grid container spacing={3}>
      {/* Summary Stats */}
      <Grid item xs={12}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Total Matches
                </Typography>
                <Typography variant="h4">
                  {historical.total_matches || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Manager 1 Wins
                </Typography>
                <Typography variant="h4" color="primary">
                  {historical.manager1_wins || 0}
                </Typography>
                <Typography variant="body2">
                  ({((historical.manager1_wins || 0) / Math.max(1, historical.total_matches || 1) * 100).toFixed(1)}%)
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Manager 2 Wins
                </Typography>
                <Typography variant="h4" color="secondary">
                  {historical.manager2_wins || 0}
                </Typography>
                <Typography variant="body2">
                  ({((historical.manager2_wins || 0) / Math.max(1, historical.total_matches || 1) * 100).toFixed(1)}%)
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Psychological Edge
                </Typography>
                <Typography 
                  variant="h4" 
                  sx={{ color: getPsychEdgeColor(historical.psychological_edge) }}
                >
                  {historical.psychological_edge?.toFixed(2) || '0.00'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Grid>

      {/* Historical Performance Chart */}
      <Grid item xs={12} lg={8}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Historical Head-to-Head Performance
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="gameweek" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  value, 
                  name === 'manager1_score' ? 'Manager 1' : 'Manager 2'
                ]}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="manager1_score" 
                stroke="#1976d2" 
                strokeWidth={2}
                name="Manager 1"
                dot={{ fill: '#1976d2' }}
              />
              <Line 
                type="monotone" 
                dataKey="manager2_score" 
                stroke="#d32f2f" 
                strokeWidth={2}
                name="Manager 2"
                dot={{ fill: '#d32f2f' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Recent Form */}
      <Grid item xs={12} lg={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Recent Form (Last 5 Matches)
          </Typography>
          <List>
            {performanceData.slice(-5).reverse().map((match, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <Avatar sx={{ 
                  mr: 2,
                  bgcolor: match.winner === 'Manager 1' ? '#1976d2' : 
                           match.winner === 'Manager 2' ? '#d32f2f' : '#757575'
                }}>
                  {match.winner === 'Draw' ? 'D' : match.winner.split(' ')[1]}
                </Avatar>
                <ListItemText
                  primary={`${match.gameweek}: ${match.manager1_score} - ${match.manager2_score}`}
                  secondary={`Margin: ${Math.abs(match.margin)} points`}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      {/* Performance Trends Comparison */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Performance Trends Comparison
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trendsData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 'dataMax + 10']} />
              <YAxis dataKey="metric" type="category" width={100} />
              <Tooltip />
              <Legend />
              <Bar dataKey="manager1" fill="#1976d2" name="Manager 1" />
              <Bar dataKey="manager2" fill="#d32f2f" name="Manager 2" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Psychological Factors Radar */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Psychological Profile
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={psychFactors}>
              <PolarGrid />
              <PolarAngleAxis dataKey="factor" />
              <PolarRadiusAxis 
                angle={30} 
                domain={[0, 100]} 
                tick={false}
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

      {/* Streak Analysis */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Streak Analysis
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" gutterBottom>
              Manager 1 Current Streak
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={Math.min(100, (historical.manager1_current_streak || 0) * 20)} 
              color={historical.manager1_current_streak > 0 ? 'success' : 'error'}
              sx={{ height: 10, borderRadius: 5 }}
            />
            <Typography variant="caption">
              {historical.manager1_current_streak > 0 ? '+' : ''}{historical.manager1_current_streak || 0} matches
            </Typography>
          </Box>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" gutterBottom>
              Manager 2 Current Streak
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={Math.min(100, (historical.manager2_current_streak || 0) * 20)} 
              color={historical.manager2_current_streak > 0 ? 'success' : 'error'}
              sx={{ height: 10, borderRadius: 5 }}
            />
            <Typography variant="caption">
              {historical.manager2_current_streak > 0 ? '+' : ''}{historical.manager2_current_streak || 0} matches
            </Typography>
          </Box>
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" color="textSecondary">
              Longest Winning Streaks:
            </Typography>
            <Typography variant="body1">
              Manager 1: {historical.manager1_longest_streak || 0} matches
            </Typography>
            <Typography variant="body1">
              Manager 2: {historical.manager2_longest_streak || 0} matches
            </Typography>
          </Box>
        </Paper>
      </Grid>

      {/* Key Historical Insights */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Historical Insights
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {historical.key_insights?.map((insight, index) => (
              <Box key={index} sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="body1">
                  {insight}
                </Typography>
              </Box>
            )) || (
              <Typography variant="body2" color="textSecondary">
                No historical insights available
              </Typography>
            )}
          </Box>
        </Paper>
      </Grid>

      {/* Momentum Indicators */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Current Momentum
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h3" color="primary">
                  {historical.manager1_momentum?.toFixed(1) || '0.0'}
                </Typography>
                <Typography variant="body1">Manager 1 Momentum</Typography>
                <Chip 
                  label={historical.manager1_momentum > 0 ? 'Rising' : historical.manager1_momentum < 0 ? 'Falling' : 'Stable'}
                  color={historical.manager1_momentum > 0 ? 'success' : historical.manager1_momentum < 0 ? 'error' : 'default'}
                  icon={<TrendingUp />}
                />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h3" color="secondary">
                  {historical.manager2_momentum?.toFixed(1) || '0.0'}
                </Typography>
                <Typography variant="body1">Manager 2 Momentum</Typography>
                <Chip 
                  label={historical.manager2_momentum > 0 ? 'Rising' : historical.manager2_momentum < 0 ? 'Falling' : 'Stable'}
                  color={historical.manager2_momentum > 0 ? 'success' : historical.manager2_momentum < 0 ? 'error' : 'default'}
                  icon={<TrendingUp />}
                />
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

export default HistoricalPatterns;