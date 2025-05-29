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
  ToggleButton,
  ToggleButtonGroup,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress
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
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  ComposedChart,
  Legend
} from 'recharts';
import { TrendingUp, TrendingDown, SwapHoriz, Money, AttachMoney } from '@mui/icons-material';

function TransferROI({ data, manager1Id, manager2Id }) {
  const [timeframe, setTimeframe] = useState('recent');
  const [metricType, setMetricType] = useState('roi');
  const [transferData, setTransferData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch transfer ROI data
  useEffect(() => {
    const fetchTransferData = async () => {
      if (!manager1Id) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/analytics/v2/transfer-roi/${manager1Id}`);
        if (!response.ok) {
          throw new Error('Failed to fetch transfer ROI data');
        }
        const result = await response.json();
        setTransferData(result);
      } catch (err) {
        console.error('Error fetching transfer data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTransferData();
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

  // Try to use transfer data from comprehensive analytics or dedicated endpoint
  const transfers = data?.transfers || transferData;
  
  if (!transfers || (!transfers.transfer_timeline && !transfers.recent_transfers)) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="textSecondary">
          No transfer ROI data available
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          Transfer data will appear once managers make transfers
        </Typography>
      </Box>
    );
  }

  // Prepare transfer timeline data
  const transferTimeline = transfers.transfer_timeline?.map(transfer => ({
    gameweek: transfer.gameweek,
    manager1_roi: transfer.manager1_roi,
    manager2_roi: transfer.manager2_roi,
    manager1_cost: transfer.manager1_cost,
    manager2_cost: transfer.manager2_cost,
    manager1_points: transfer.manager1_points_gained,
    manager2_points: transfer.manager2_points_gained
  })) || [];

  // Best and worst transfers
  const bestTransfers = transfers.best_transfers || [];
  const worstTransfers = transfers.worst_transfers || [];

  // Transfer patterns
  const transferPatterns = [
    { 
      pattern: 'Early Transfers', 
      manager1: transfers.manager1_early_transfers || 0, 
      manager2: transfers.manager2_early_transfers || 0 
    },
    { 
      pattern: 'Late Transfers', 
      manager1: transfers.manager1_late_transfers || 0, 
      manager2: transfers.manager2_late_transfers || 0 
    },
    { 
      pattern: 'Injury Reactions', 
      manager1: transfers.manager1_injury_transfers || 0, 
      manager2: transfers.manager2_injury_transfers || 0 
    },
    { 
      pattern: 'Form Chasing', 
      manager1: transfers.manager1_form_transfers || 0, 
      manager2: transfers.manager2_form_transfers || 0 
    }
  ];

  // Cost vs Points scatter data
  const costVsPoints = transfers.cost_vs_points?.map(transfer => ({
    cost: transfer.cost,
    points: transfer.points_gained,
    roi: transfer.roi,
    player: transfer.player_name,
    manager: transfer.manager === 'manager1' ? 'Manager 1' : 'Manager 2'
  })) || [];

  const getROIColor = (roi) => {
    if (roi > 0.5) return '#4caf50';
    if (roi > 0) return '#8bc34a';
    if (roi > -0.2) return '#ff9800';
    return '#f44336';
  };

  const getTransferIcon = (roi) => {
    if (roi > 0.3) return <TrendingUp color="success" />;
    if (roi > 0) return <TrendingUp color="warning" />;
    if (roi < -0.2) return <TrendingDown color="error" />;
    return <SwapHoriz color="disabled" />;
  };

  const formatCurrency = (value) => {
    return `£${value?.toFixed(1)}M` || '£0.0M';
  };

  return (
    <Grid container spacing={3}>
      {/* Summary Cards */}
      <Grid item xs={12}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Manager 1 Total ROI
                </Typography>
                <Typography variant="h4" sx={{ color: getROIColor(transfers.manager1_total_roi) }}>
                  {(transfers.manager1_total_roi || 0).toFixed(2)}
                </Typography>
                <Typography variant="body2">
                  {transfers.manager1_total_transfers || 0} transfers
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Manager 2 Total ROI
                </Typography>
                <Typography variant="h4" sx={{ color: getROIColor(transfers.manager2_total_roi) }}>
                  {(transfers.manager2_total_roi || 0).toFixed(2)}
                </Typography>
                <Typography variant="body2">
                  {transfers.manager2_total_transfers || 0} transfers
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Best Single Transfer
                </Typography>
                <Typography variant="h4" color="success.main">
                  {(transfers.best_single_roi || 0).toFixed(2)}
                </Typography>
                <Typography variant="body2">
                  {transfers.best_transfer_player || 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Transfer Efficiency
                </Typography>
                <Typography variant="h4" color="info.main">
                  {Math.round((transfers.transfer_efficiency || 0) * 100)}%
                </Typography>
                <Typography variant="body2">
                  Success Rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Grid>

      {/* Controls */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item>
              <Typography variant="body1">Timeframe:</Typography>
              <ToggleButtonGroup
                value={timeframe}
                exclusive
                onChange={(e, value) => value && setTimeframe(value)}
                size="small"
              >
                <ToggleButton value="recent">Recent 5 GWs</ToggleButton>
                <ToggleButton value="season">Full Season</ToggleButton>
                <ToggleButton value="comparison">H2H Period</ToggleButton>
              </ToggleButtonGroup>
            </Grid>
            <Grid item>
              <Typography variant="body1">Metric:</Typography>
              <ToggleButtonGroup
                value={metricType}
                exclusive
                onChange={(e, value) => value && setMetricType(value)}
                size="small"
              >
                <ToggleButton value="roi">ROI</ToggleButton>
                <ToggleButton value="points">Points</ToggleButton>
                <ToggleButton value="cost">Cost</ToggleButton>
              </ToggleButtonGroup>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* ROI Timeline */}
      <Grid item xs={12} lg={8}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Transfer ROI Timeline
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={transferTimeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="gameweek" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip 
                formatter={(value, name) => [
                  typeof value === 'number' ? value.toFixed(2) : value,
                  name.includes('roi') ? 'ROI' : 
                  name.includes('cost') ? 'Cost (£M)' : 'Points'
                ]}
              />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="manager1_roi" 
                stroke="#1976d2" 
                strokeWidth={2}
                name="Manager 1 ROI"
                dot={{ fill: '#1976d2' }}
              />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="manager2_roi" 
                stroke="#d32f2f" 
                strokeWidth={2}
                name="Manager 2 ROI"
                dot={{ fill: '#d32f2f' }}
              />
              {metricType === 'cost' && (
                <>
                  <Bar yAxisId="right" dataKey="manager1_cost" fill="#1976d280" name="Manager 1 Cost" />
                  <Bar yAxisId="right" dataKey="manager2_cost" fill="#d32f2f80" name="Manager 2 Cost" />
                </>
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Transfer Patterns */}
      <Grid item xs={12} lg={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Transfer Patterns
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={transferPatterns} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="pattern" type="category" width={120} />
              <Tooltip />
              <Legend />
              <Bar dataKey="manager1" fill="#1976d2" name="Manager 1" />
              <Bar dataKey="manager2" fill="#d32f2f" name="Manager 2" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Best Transfers */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Best Transfers (Highest ROI)
          </Typography>
          <List>
            {bestTransfers.slice(0, 6).map((transfer, index) => (
              <ListItem key={index} divider>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: getROIColor(transfer.roi) }}>
                    {getTransferIcon(transfer.roi)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        {transfer.player_name}
                      </Typography>
                      <Chip 
                        label={transfer.manager === 'manager1' ? 'M1' : 'M2'} 
                        size="small"
                        color={transfer.manager === 'manager1' ? 'primary' : 'secondary'}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        ROI: {transfer.roi.toFixed(2)} | 
                        Cost: {formatCurrency(transfer.cost)} | 
                        Points: {transfer.points_gained} | 
                        GW{transfer.gameweek}
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={Math.min(100, transfer.roi * 50)} 
                        sx={{ mt: 1 }}
                        color="success"
                      />
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      {/* Worst Transfers */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Worst Transfers (Lowest ROI)
          </Typography>
          <List>
            {worstTransfers.slice(0, 6).map((transfer, index) => (
              <ListItem key={index} divider>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: getROIColor(transfer.roi) }}>
                    {getTransferIcon(transfer.roi)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        {transfer.player_name}
                      </Typography>
                      <Chip 
                        label={transfer.manager === 'manager1' ? 'M1' : 'M2'} 
                        size="small"
                        color={transfer.manager === 'manager1' ? 'primary' : 'secondary'}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        ROI: {transfer.roi.toFixed(2)} | 
                        Cost: {formatCurrency(transfer.cost)} | 
                        Points: {transfer.points_gained} | 
                        GW{transfer.gameweek}
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={Math.max(0, 100 + transfer.roi * 50)} 
                        sx={{ mt: 1 }}
                        color="error"
                      />
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      {/* Cost vs Points Scatter */}
      <Grid item xs={12} lg={8}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Transfer Cost vs Points Gained
          </Typography>
          <ResponsiveContainer width="100%" height={350}>
            <ScatterChart data={costVsPoints}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="cost" 
                name="Cost" 
                unit="M" 
                domain={['dataMin - 0.5', 'dataMax + 0.5']}
              />
              <YAxis 
                dataKey="points" 
                name="Points" 
                domain={['dataMin - 5', 'dataMax + 5']}
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }}
                formatter={(value, name) => [
                  typeof value === 'number' ? value.toFixed(1) : value,
                  name === 'points' ? 'Points Gained' : 'Cost (£M)'
                ]}
                labelFormatter={(label) => `Player: ${label}`}
              />
              <Scatter name="Transfers" dataKey="points" fill="#8884d8">
                {costVsPoints.map((entry, index) => (
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

      {/* Transfer Statistics Table */}
      <Grid item xs={12} lg={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Transfer Statistics
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
                  <TableCell>Total Transfers</TableCell>
                  <TableCell align="center">{transfers.manager1_total_transfers || 0}</TableCell>
                  <TableCell align="center">{transfers.manager2_total_transfers || 0}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Avg ROI</TableCell>
                  <TableCell align="center">{(transfers.manager1_avg_roi || 0).toFixed(2)}</TableCell>
                  <TableCell align="center">{(transfers.manager2_avg_roi || 0).toFixed(2)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Success Rate</TableCell>
                  <TableCell align="center">{Math.round((transfers.manager1_success_rate || 0) * 100)}%</TableCell>
                  <TableCell align="center">{Math.round((transfers.manager2_success_rate || 0) * 100)}%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Avg Cost</TableCell>
                  <TableCell align="center">{formatCurrency(transfers.manager1_avg_cost)}</TableCell>
                  <TableCell align="center">{formatCurrency(transfers.manager2_avg_cost)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Points Gained</TableCell>
                  <TableCell align="center">{transfers.manager1_total_points || 0}</TableCell>
                  <TableCell align="center">{transfers.manager2_total_points || 0}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Grid>

      {/* Transfer Strategy Insights */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Transfer Strategy Insights
          </Typography>
          <Grid container spacing={2}>
            {transfers.strategy_insights?.map((insight, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Box sx={{ 
                  p: 2, 
                  bgcolor: 'background.default', 
                  borderRadius: 1,
                  borderLeft: 4,
                  borderLeftColor: index % 3 === 0 ? 'primary.main' : index % 3 === 1 ? 'secondary.main' : 'success.main'
                }}>
                  <Typography variant="body1">
                    {insight}
                  </Typography>
                </Box>
              </Grid>
            )) || (
              <Grid item xs={12}>
                <Typography variant="body2" color="textSecondary">
                  No transfer strategy insights available
                </Typography>
              </Grid>
            )}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

export default TransferROI;