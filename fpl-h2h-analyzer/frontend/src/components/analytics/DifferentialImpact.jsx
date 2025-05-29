import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

function DifferentialImpact({ data }) {
  // Check for both v1 and v2 API formats
  const differentialData = data?.differential || data?.differential_analysis;
  
  if (!differentialData) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="textSecondary">
          No differential impact data available
        </Typography>
      </Box>
    );
  }

  const differential = differentialData;
  
  // Prepare data for visualizations - handle v2 API structure
  let impactData = [];
  
  if (differential.manager1_differentials && differential.manager2_differentials) {
    // V2 API structure
    const m1Diffs = differential.manager1_differentials.map(player => ({
      name: player.name,
      impact: player.impact_scores?.differential_impact || 0,
      ownership: player.ownership?.overall || 0,
      manager: 'Manager 1',
      position: player.position,
      form: player.performance?.form || 0
    }));
    
    const m2Diffs = differential.manager2_differentials.map(player => ({
      name: player.name,
      impact: player.impact_scores?.differential_impact || 0,
      ownership: player.ownership?.overall || 0,
      manager: 'Manager 2',
      position: player.position,
      form: player.performance?.form || 0
    }));
    
    impactData = [...m1Diffs, ...m2Diffs].sort((a, b) => b.impact - a.impact).slice(0, 10);
  } else if (differential.top_differentials) {
    // V1 API structure
    impactData = differential.top_differentials.map(player => ({
      name: player.web_name,
      impact: player.differential_impact,
      ownership: player.ownership_diff,
      manager: player.owned_by === 'manager1' ? 'Manager 1' : 'Manager 2',
      position: player.position,
      form: player.form
    }));
  }

  const positionBreakdown = [
    { name: 'GKP', value: differential.position_breakdown?.GKP || 0, fill: '#8884d8' },
    { name: 'DEF', value: differential.position_breakdown?.DEF || 0, fill: '#82ca9d' },
    { name: 'MID', value: differential.position_breakdown?.MID || 0, fill: '#ffc658' },
    { name: 'FWD', value: differential.position_breakdown?.FWD || 0, fill: '#ff7300' }
  ];

  const getImpactColor = (impact) => {
    if (impact > 5) return '#4caf50';
    if (impact > 2) return '#ff9800';
    return '#f44336';
  };

  const getImpactIcon = (impact) => {
    if (impact > 2) return <TrendingUp color="success" />;
    if (impact > 0) return <TrendingUp color="warning" />;
    if (impact < -2) return <TrendingDown color="error" />;
    return <Remove color="disabled" />;
  };

  return (
    <Grid container spacing={3}>
      {/* Summary Cards */}
      <Grid item xs={12}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {differential.high_impact_count || impactData.filter(p => p.impact > 3).length || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                High Impact Differentials
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="secondary">
                {differential.total_differential_impact?.manager1 || differential.total_differential_value?.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Total Expected Impact
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {differential.avg_ownership_diff?.toFixed(1) || '0.0'}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Avg Ownership Difference
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main">
                {differential.risk_score?.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Risk Score
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Grid>

      {/* Impact Bar Chart */}
      <Grid item xs={12} lg={8}>
        <Paper sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography variant="h6" gutterBottom>
            Differential Impact by Player
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={impactData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45}
                textAnchor="end"
                height={100}
                fontSize={10}
                interval={0}
              />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [value.toFixed(2), 'Impact Score']}
                labelFormatter={(label) => `Player: ${label}`}
              />
              <Bar dataKey="impact" name="Impact">
                {impactData.map((entry, index) => (
                  <Cell key={index} fill={getImpactColor(entry.impact)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Position Breakdown */}
      <Grid item xs={12} lg={4}>
        <Paper sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography variant="h6" gutterBottom>
            Differential by Position
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={positionBreakdown}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {positionBreakdown.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Top Differentials List */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography variant="h6" gutterBottom>
            Top Differential Players
          </Typography>
          <List>
            {differential.top_differentials?.slice(0, 8).map((player, index) => (
              <ListItem key={index} divider>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: getImpactColor(player.differential_impact) }}>
                    {getImpactIcon(player.differential_impact)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        {player.web_name}
                      </Typography>
                      <Chip 
                        label={player.position} 
                        size="small" 
                        variant="outlined"
                      />
                      <Chip 
                        label={player.owned_by === 'manager1' ? 'M1' : 'M2'} 
                        size="small"
                        color={player.owned_by === 'manager1' ? 'primary' : 'secondary'}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        Impact: {player.differential_impact.toFixed(2)} | 
                        Form: {player.form} | 
                        Ownership: {player.ownership_diff.toFixed(1)}%
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={Math.min(100, (player.differential_impact / 10) * 100)} 
                        sx={{ mt: 1 }}
                        color={player.differential_impact > 3 ? 'success' : player.differential_impact > 1 ? 'warning' : 'error'}
                      />
                    </Box>
                  }
                />
              </ListItem>
            )) || (
              <ListItem>
                <ListItemText primary="No differential data available" />
              </ListItem>
            )}
          </List>
        </Paper>
      </Grid>

      {/* Risk vs Reward Scatter */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography variant="h6" gutterBottom>
            Risk vs Reward Analysis
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart data={impactData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="ownership" 
                name="Ownership Diff" 
                unit="%" 
                domain={['dataMin - 5', 'dataMax + 5']}
              />
              <YAxis 
                dataKey="impact" 
                name="Impact" 
                domain={['dataMin - 1', 'dataMax + 1']}
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }}
                formatter={(value, name) => [
                  typeof value === 'number' ? value.toFixed(2) : value,
                  name === 'impact' ? 'Impact Score' : 'Ownership Diff (%)'
                ]}
                labelFormatter={(label) => `Player: ${label}`}
              />
              <Scatter name="Players" dataKey="impact" fill="#8884d8">
                {impactData.map((entry, index) => (
                  <Cell key={index} fill={entry.manager === 'Manager 1' ? '#1976d2' : '#d32f2f'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Chip label="Manager 1" sx={{ bgcolor: '#1976d2', color: 'white' }} size="small" />
            <Chip label="Manager 2" sx={{ bgcolor: '#d32f2f', color: 'white' }} size="small" />
          </Box>
        </Paper>
      </Grid>

      {/* Key Insights */}
      <Grid item xs={12}>
        <Paper sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography variant="h6" gutterBottom>
            Key Insights
          </Typography>
          <Grid container spacing={2}>
            {differential.insights?.map((insight, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="body1" fontWeight="medium">
                    {insight}
                  </Typography>
                </Box>
              </Grid>
            )) || (
              <Grid item xs={12}>
                <Typography variant="body2" color="textSecondary">
                  No insights available
                </Typography>
              </Grid>
            )}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

export default DifferentialImpact;