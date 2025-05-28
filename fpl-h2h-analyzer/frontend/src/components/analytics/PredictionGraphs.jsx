import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  Slider,
  ToggleButton,
  ToggleButtonGroup,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Avatar
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  Legend,
  RadialBarChart,
  RadialBar,
  AreaChart,
  Area
} from 'recharts';
import { TrendingUp, Psychology, Speed, EmojiEvents } from '@mui/icons-material';

function PredictionGraphs({ data }) {
  const [predictionType, setPredictionType] = useState('outcome');
  const [confidenceThreshold, setConfidenceThreshold] = useState(70);

  if (!data?.prediction) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="textSecondary">
          No prediction data available
        </Typography>
      </Box>
    );
  }

  const { prediction } = data;

  // Outcome probabilities for pie chart
  const outcomeData = [
    { 
      name: 'Manager 1 Win', 
      value: (prediction.manager1_win_prob || 0) * 100, 
      fill: '#1976d2' 
    },
    { 
      name: 'Draw', 
      value: (prediction.draw_prob || 0) * 100, 
      fill: '#757575' 
    },
    { 
      name: 'Manager 2 Win', 
      value: (prediction.manager2_win_prob || 0) * 100, 
      fill: '#d32f2f' 
    }
  ];

  // Score distribution data
  const scoreRanges = prediction.score_ranges || {};
  const scoreDistribution = Object.entries(scoreRanges).map(([range, prob]) => ({
    range,
    probability: prob * 100,
    manager1: range.includes('Manager 1') ? prob * 100 : 0,
    manager2: range.includes('Manager 2') ? prob * 100 : 0
  }));

  // Confidence breakdown
  const confidenceFactors = [
    { factor: 'Form Analysis', value: (prediction.form_confidence || 0) * 100, color: '#4caf50' },
    { factor: 'Historical Data', value: (prediction.historical_confidence || 0) * 100, color: '#2196f3' },
    { factor: 'Player Quality', value: (prediction.player_confidence || 0) * 100, color: '#ff9800' },
    { factor: 'Fixture Difficulty', value: (prediction.fixture_confidence || 0) * 100, color: '#9c27b0' },
    { factor: 'Recent Transfers', value: (prediction.transfer_confidence || 0) * 100, color: '#f44336' }
  ];

  // Expected points timeline
  const pointsTimeline = prediction.points_timeline || [];

  // Key factors affecting prediction
  const keyFactors = prediction.key_factors || [];

  const getConfidenceColor = (confidence) => {
    if (confidence > 80) return 'success';
    if (confidence > 60) return 'warning';
    return 'error';
  };

  const getWinnerName = () => {
    if (prediction.manager1_win_prob > prediction.manager2_win_prob) {
      return prediction.manager1_win_prob > (prediction.draw_prob || 0) ? 'Manager 1' : 'Draw';
    } else {
      return prediction.manager2_win_prob > (prediction.draw_prob || 0) ? 'Manager 2' : 'Draw';
    }
  };

  return (
    <Grid container spacing={3}>
      {/* Prediction Summary */}
      <Grid item xs={12}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Predicted Winner
                </Typography>
                <Typography variant="h4">
                  {getWinnerName()}
                </Typography>
                <Chip 
                  label={`${Math.max(
                    prediction.manager1_win_prob || 0,
                    prediction.manager2_win_prob || 0,
                    prediction.draw_prob || 0
                  ).toFixed(1)}% chance`}
                  color="primary"
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Overall Confidence
                </Typography>
                <Typography variant="h4" color={getConfidenceColor((prediction.confidence || 0) * 100)}>
                  {Math.round((prediction.confidence || 0) * 100)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(prediction.confidence || 0) * 100} 
                  color={getConfidenceColor((prediction.confidence || 0) * 100)}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Expected Score
                </Typography>
                <Typography variant="h4">
                  {prediction.manager1_expected?.toFixed(1) || '0.0'} - {prediction.manager2_expected?.toFixed(1) || '0.0'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  M1 vs M2
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography color="textSecondary" gutterBottom>
                  Expected Margin
                </Typography>
                <Typography variant="h4">
                  {Math.abs((prediction.manager1_expected || 0) - (prediction.manager2_expected || 0)).toFixed(1)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  points
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Grid>

      {/* Outcome Probabilities */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Match Outcome Probabilities
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={outcomeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {outcomeData.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
            </PieChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Confidence Breakdown */}
      <Grid item xs={12} lg={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Prediction Confidence Breakdown
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={confidenceFactors} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis dataKey="factor" type="category" width={120} />
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
              <Bar dataKey="value" name="Confidence">
                {confidenceFactors.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      {/* Score Distribution */}
      {scoreDistribution.length > 0 && (
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Score Range Probabilities
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                <Bar dataKey="probability" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      )}

      {/* Confidence Controls */}
      <Grid item xs={12} lg={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Prediction Settings
          </Typography>
          <Box sx={{ mb: 3 }}>
            <Typography gutterBottom>
              Confidence Threshold: {confidenceThreshold}%
            </Typography>
            <Slider
              value={confidenceThreshold}
              onChange={(e, value) => setConfidenceThreshold(value)}
              min={0}
              max={100}
              marks={[
                { value: 50, label: '50%' },
                { value: 75, label: '75%' },
                { value: 90, label: '90%' }
              ]}
            />
          </Box>
          <Box sx={{ mb: 3 }}>
            <Typography gutterBottom>
              Prediction Type
            </Typography>
            <ToggleButtonGroup
              value={predictionType}
              exclusive
              onChange={(e, value) => value && setPredictionType(value)}
              size="small"
              fullWidth
            >
              <ToggleButton value="outcome">Outcome</ToggleButton>
              <ToggleButton value="score">Score</ToggleButton>
              <ToggleButton value="margin">Margin</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </Paper>
      </Grid>

      {/* Expected Points Timeline */}
      {pointsTimeline.length > 0 && (
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Expected Points Timeline
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={pointsTimeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="gameweek" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="manager1_expected" 
                  stackId="1" 
                  stroke="#1976d2" 
                  fill="#1976d2" 
                  fillOpacity={0.6}
                  name="Manager 1"
                />
                <Area 
                  type="monotone" 
                  dataKey="manager2_expected" 
                  stackId="2" 
                  stroke="#d32f2f" 
                  fill="#d32f2f" 
                  fillOpacity={0.6}
                  name="Manager 2"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      )}

      {/* Key Prediction Factors */}
      <Grid item xs={12} lg={4}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Key Prediction Factors
          </Typography>
          <List>
            {keyFactors.slice(0, 6).map((factor, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <Avatar sx={{ 
                  mr: 2,
                  bgcolor: factor.impact > 0 ? '#4caf50' : factor.impact < 0 ? '#f44336' : '#757575',
                  width: 32,
                  height: 32
                }}>
                  {factor.impact > 0 ? '+' : factor.impact < 0 ? '-' : '='}
                </Avatar>
                <ListItemText
                  primary={factor.description || factor.factor}
                  secondary={`Impact: ${factor.impact?.toFixed(2) || 'N/A'} | Weight: ${factor.weight?.toFixed(2) || 'N/A'}`}
                />
              </ListItem>
            ))}
            {keyFactors.length === 0 && (
              <ListItem>
                <ListItemText primary="No key factors available" />
              </ListItem>
            )}
          </List>
        </Paper>
      </Grid>

      {/* Model Performance Metrics */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Model Performance & Reliability
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {(prediction.model_accuracy || 0.75).toFixed(2)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Model Accuracy
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="secondary">
                  {(prediction.prediction_variance || 0.15).toFixed(2)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Prediction Variance
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="info.main">
                  {Math.round((prediction.data_quality || 0.85) * 100)}%
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Data Quality
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {prediction.sample_size || 'N/A'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Sample Size
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* Prediction Insights */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            AI Prediction Insights
          </Typography>
          <Grid container spacing={2}>
            {prediction.insights?.map((insight, index) => (
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
                  No prediction insights available
                </Typography>
              </Grid>
            )}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

export default PredictionGraphs;