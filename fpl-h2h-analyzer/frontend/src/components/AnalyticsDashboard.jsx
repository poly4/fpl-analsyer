import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Button,
  TextField,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Analytics,
  TrendingUp,
  Timeline,
  SwapHoriz,
  SportsSoccer,
  EmojiEvents,
  Refresh
} from '@mui/icons-material';
import axios from 'axios';

// Import all visualization components
import DifferentialImpact from './analytics/DifferentialImpact';
import HistoricalPatterns from './analytics/HistoricalPatterns';
import PredictionGraphs from './analytics/PredictionGraphs';
import TransferROI from './analytics/TransferROI';
import LiveMatchTracker from './analytics/LiveMatchTracker';
import ChipStrategy from './analytics/ChipStrategy';
import AnalyticsManagerSelector from './AnalyticsManagerSelector';
import { GlassCard } from './modern';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function AnalyticsDashboard() {
  const [tabValue, setTabValue] = useState(0);
  const [manager1Id, setManager1Id] = useState('');
  const [manager2Id, setManager2Id] = useState('');
  const [gameweek, setGameweek] = useState(38);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const fetchAnalyticsData = async (m1Id = manager1Id, m2Id = manager2Id) => {
    if (!m1Id || !m2Id) {
      setError('Please select both managers');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(
        `/api/analytics/v2/h2h/comprehensive/${m1Id}/${m2Id}`,
        { params: { gameweek } }
      );
      setAnalyticsData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch analytics data');
      console.error('Analytics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh for live data
  useEffect(() => {
    let interval;
    if (autoRefresh && analyticsData) {
      interval = setInterval(fetchAnalyticsData, 30000); // Refresh every 30 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, analyticsData, manager1Id, manager2Id, gameweek]);

  const tabsData = [
    {
      label: 'Differential Impact',
      icon: <TrendingUp />,
      component: DifferentialImpact,
      description: 'Analyze unique players and their potential impact'
    },
    {
      label: 'Historical Patterns',
      icon: <Timeline />,
      component: HistoricalPatterns,
      description: 'Head-to-head history and psychological edge'
    },
    {
      label: 'Match Predictions',
      icon: <Analytics />,
      component: PredictionGraphs,
      description: 'AI-powered score predictions with confidence'
    },
    {
      label: 'Transfer ROI',
      icon: <SwapHoriz />,
      component: TransferROI,
      description: 'Transfer strategy and return on investment'
    },
    {
      label: 'Live Tracker',
      icon: <SportsSoccer />,
      component: LiveMatchTracker,
      description: 'Real-time match tracking and updates'
    },
    {
      label: 'Chip Strategy',
      icon: <EmojiEvents />,
      component: ChipStrategy,
      description: 'Optimal chip timing and recommendations'
    }
  ];

  const handleManagerSelection = (m1Id, m2Id) => {
    setManager1Id(m1Id);
    setManager2Id(m2Id);
    fetchAnalyticsData(m1Id, m2Id);
  };

  return (
    <Box sx={{ width: '100%', p: { xs: 1, sm: 2, md: 3 } }}>
      {/* Manager Selector */}
      <AnalyticsManagerSelector onSelectionChange={handleManagerSelection} />
      
      {/* Header */}
      <GlassCard sx={{ p: { xs: 2, sm: 3 }, mb: { xs: 2, sm: 3 } }}>
        <Typography 
          variant="h4" 
          gutterBottom 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 2,
            fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' },
            flexWrap: 'wrap'
          }}
        >
          <Analytics fontSize="large" />
          Advanced H2H Analytics Dashboard
        </Typography>
        
        {/* Input Controls */}
        <Grid container spacing={2} alignItems="center" sx={{ mt: 2 }}>
          <Grid item xs={6} sm={4} md={2}>
            <TextField
              label="Gameweek"
              type="number"
              value={gameweek}
              onChange={(e) => setGameweek(parseInt(e.target.value))}
              fullWidth
              variant="outlined"
              size="small"
              inputProps={{ min: 1, max: 38 }}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <Button
              variant="contained"
              onClick={fetchAnalyticsData}
              disabled={loading || !manager1Id || !manager2Id}
              fullWidth
              sx={{ height: '40px' }}
            >
              {loading ? <CircularProgress size={20} /> : 'Analyze'}
            </Button>
          </Grid>
          <Grid item xs={12} sm={4} md={2} sx={{ display: 'flex', justifyContent: 'center' }}>
            <Tooltip title={autoRefresh ? "Disable auto-refresh" : "Enable auto-refresh"}>
              <IconButton
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? "primary" : "default"}
                disabled={!analyticsData}
                size="large"
              >
                <Refresh />
              </IconButton>
            </Tooltip>
          </Grid>
        </Grid>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {/* Analytics Summary Cards */}
        {analyticsData && (
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Predicted Winner
                  </Typography>
                  <Typography variant="h5">
                    {(analyticsData.prediction?.win_probabilities?.manager1 > analyticsData.prediction?.win_probabilities?.manager2)
                      ? 'Manager 1' 
                      : (analyticsData.prediction?.win_probabilities?.manager2 > analyticsData.prediction?.win_probabilities?.manager1)
                      ? 'Manager 2' 
                      : 'Draw'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Confidence
                  </Typography>
                  <Typography variant="h5">
                    {Math.round((analyticsData.prediction?.confidence_level || 0) * 100)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Psychological Edge
                  </Typography>
                  <Typography variant="h5">
                    {analyticsData.historical?.psychological_edge?.toFixed(1) || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Key Differentials
                  </Typography>
                  <Typography variant="h5">
                    {analyticsData.differential?.high_impact_count || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Enhanced Prediction Scores */}
          {analyticsData.prediction?.expected_scores && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Manager 1 Expected Points
                    </Typography>
                    <Typography variant="h4" color="primary">
                      {analyticsData.prediction.expected_scores.manager1?.toFixed(1) || '0.0'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Win Probability: {(analyticsData.prediction.win_probabilities?.manager1 * 100)?.toFixed(1) || '0'}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Manager 2 Expected Points
                    </Typography>
                    <Typography variant="h4" color="secondary">
                      {analyticsData.prediction.expected_scores.manager2?.toFixed(1) || '0.0'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Win Probability: {(analyticsData.prediction.win_probabilities?.manager2 * 100)?.toFixed(1) || '0'}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        )}
      </Paper>

      {/* Analytics Tabs */}
      {analyticsData && (
        <Paper elevation={3}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
            sx={{ 
              borderBottom: 1, 
              borderColor: 'divider',
              '& .MuiTab-root': {
                minWidth: { xs: 120, sm: 140 },
                fontSize: { xs: '0.8rem', sm: '0.875rem' }
              }
            }}
          >
            {tabsData.map((tab, index) => (
              <Tab
                key={index}
                icon={tab.icon}
                label={tab.label}
                id={`analytics-tab-${index}`}
                aria-controls={`analytics-tabpanel-${index}`}
                sx={{ 
                  minHeight: { xs: 64, sm: 72 },
                  flexDirection: { xs: 'column', sm: 'row' }
                }}
              />
            ))}
          </Tabs>

          {tabsData.map((tab, index) => {
            const Component = tab.component;
            return (
              <TabPanel key={index} value={tabValue} index={index}>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  {tab.description}
                </Typography>
                <Component 
                  data={analyticsData} 
                  manager1Id={manager1Id}
                  manager2Id={manager2Id}
                  gameweek={gameweek}
                />
              </TabPanel>
            );
          })}
        </Paper>
      )}

      {/* Loading State */}
      {loading && !analyticsData && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress size={60} />
        </Box>
      )}

      {/* No Data State */}
      {!analyticsData && !loading && !error && (
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center', mt: 3 }}>
          <Analytics fontSize="large" color="disabled" />
          <Typography variant="h6" color="textSecondary" sx={{ mt: 2 }}>
            Enter manager IDs above to start analyzing
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Get comprehensive head-to-head analytics with AI-powered insights
          </Typography>
        </Paper>
      )}
    </Box>
  );
}

export default AnalyticsDashboard;